from contextlib import asynccontextmanager
from typing import Optional

from common.exceptions import AppException
from common.logging import setup_logging
from common.schemas import ErrorDetail, ErrorResponse
from common.security import RoleChecker
from fastapi import FastAPI, Query, status
from fastapi.responses import JSONResponse

from .application.consumers import EventConsumerService
from .config import settings
from .infrastructure.elasticsearch import es_client
from .infrastructure.mongodb import mongodb_client

# Setup logging
logger = setup_logging(settings.SERVICE_NAME, settings.LOG_LEVEL)

# Global background tasks
consumer_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global consumer_service
    logger.info("Starting up store-service")

    # Init ES index
    await es_client.init_index()

    # Start Consumers
    consumer_service = EventConsumerService()
    await consumer_service.start()
    logger.info("Event consumers started")

    yield

    # Shutdown tasks
    if consumer_service:
        await consumer_service.stop()

    await es_client.close()
    await mongodb_client.close()
    logger.info("Shutdown complete")


app = FastAPI(
    title="Store Query Service",
    description="Read Model (CQRS) for Product Catalog",
    version="0.1.0",
    lifespan=lifespan,
)


@app.exception_handler(AppException)
async def custom_app_exception_handler(request, exc: AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    if exc.code == "NOT_FOUND":
        status_code = status.HTTP_404_NOT_FOUND
    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=ErrorDetail(code=exc.code, message=exc.message, details=exc.details)
        ).model_dump(),
    )

# Role checkers
any_user_required = RoleChecker(allowed_roles=["ADMIN", "USER"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.SERVICE_NAME}

@app.get("/api/v1/store/offerings")
async def list_offerings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    cursor = mongodb_client.offerings.find({}, {"_id": 0}).skip(skip).limit(limit)
    items = []
    async for doc in cursor:
        items.append(doc)
    return {"total": await mongodb_client.offerings.count_documents({}), "items": items}

@app.get("/api/v1/store/offerings/{offering_id}")
async def get_offering(offering_id: str):
    doc = await mongodb_client.offerings.find_one({"id": offering_id}, {"_id": 0})
    if not doc:
        return JSONResponse(status_code=404, content={"error": "Offering not found"})
    return doc

@app.get("/api/v1/store/search")
async def search_offerings(
    q: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    channel: Optional[str] = None,
    skip: int = 0,
    limit: int = 10
):
    """
    Full-text search with filters (price range, characteristic facets) and full-text query.
    """
    must_queries = []
    filters = []

    if q:
        must_queries.append({
            "multi_match": {
                "query": q,
                "fields": ["name^3", "description", "specifications.name", "specifications.characteristics.value"]
            }
        })
    else:
        must_queries.append({"match_all": {}})

    if min_price is not None or max_price is not None:
        range_query = {"range": {"pricing.value": {}}}
        if min_price is not None:
            range_query["range"]["pricing.value"]["gte"] = min_price
        if max_price is not None:
            range_query["range"]["pricing.value"]["lte"] = max_price
        # Since pricing is nested, we need nested query
        filters.append({
            "nested": {
                "path": "pricing",
                "query": range_query
            }
        })

    if channel:
        filters.append({"term": {"sales_channels": channel}})

    query_body = {
        "from": skip,
        "size": limit,
        "query": {
            "bool": {
                "must": must_queries,
                "filter": filters
            }
        },
        "aggs": {
            "channels": {"terms": {"field": "sales_channels"}},
            "price_ranges": {
                "range": {
                    "field": "pricing.value",
                    "ranges": [
                        {"to": 50},
                        {"from": 50, "to": 100},
                        {"from": 100}
                    ]
                }
            }
        }
    }

    try:
        results = await es_client.search_offerings(query_body)
        hits = results["hits"]["hits"]
        items = [hit["_source"] for hit in hits]
        return {
            "total": results["hits"]["total"]["value"],
            "items": items,
            "facets": results.get("aggregations", {})
        }
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        return JSONResponse(status_code=500, content={"error": "Search failed", "details": str(e)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
