"""
Store Query Service - Read Model (CQRS) for Product Catalog.

Provides search and query operations over denormalized product data in MongoDB/Elasticsearch.
"""

from contextlib import asynccontextmanager
from typing import List, Optional

from common.exceptions import AppException
from common.logging import setup_logging
from common.schemas import ErrorDetail, ErrorResponse
from common.security import RoleChecker
from common.tracing import instrument_fastapi, instrument_httpx, setup_tracing
from fastapi import FastAPI, Query, status
from fastapi.responses import JSONResponse

from .application.consumers import EventConsumerService
from .application.service import StoreService
from .config import settings
from .infrastructure.elasticsearch import es_client
from .infrastructure.mongodb import mongodb_client

# Setup logging first
logger = setup_logging(settings.SERVICE_NAME, settings.LOG_LEVEL)

# Setup tracing
setup_tracing(
    service_name=settings.SERVICE_NAME,
    zipkin_endpoint=settings.ZIPKIN_ENDPOINT,
    enabled=settings.TRACING_ENABLED,
)

# Instrument HTTPX for outgoing requests (fetching data from other services)
instrument_httpx()

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

# Instrument FastAPI for tracing
instrument_fastapi(app, excluded_urls="health")


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
async def list_offerings(skip: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000)):
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
    characteristic: Optional[List[str]] = Query(None),
    skip: int = 0,
    limit: int = 10,
):
    """
    Search offerings using Elasticsearch.

    Args:
        q: Full-text search query.
        min_price: Minimum price filter.
        max_price: Maximum price filter.
        channel: Sales channel filter.
        characteristic: List of characteristic filters in format "name:value".
        skip: Pagination offset.
        limit: Page size.
    """
    # Build Elasticsearch query
    must = []
    filter_clauses = []

    if q:
        must.append(
            {
                "multi_match": {
                    "query": q,
                    "fields": ["name^2", "description", "specifications.name"],
                }
            }
        )

    if min_price is not None or max_price is not None:
        range_clause = {"nested": {
            "path": "pricing",
            "query": {
                "range": {"pricing.value": {}}
            }
        }}
        if min_price is not None:
            range_clause["nested"]["query"]["range"]["pricing.value"]["gte"] = min_price
        if max_price is not None:
            range_clause["nested"]["query"]["range"]["pricing.value"]["lte"] = max_price
        filter_clauses.append(range_clause)

    if channel:
        filter_clauses.append({"term": {"sales_channels": channel}})

    if characteristic:
        for char_filter in characteristic:
            if ":" in char_filter:
                name, value = char_filter.split(":", 1)
                filter_clauses.append({
                    "nested": {
                        "path": "specifications.characteristics",
                        "query": {
                            "bool": {
                                "must": [
                                    {"term": {"specifications.characteristics.name": name}},
                                    {"term": {"specifications.characteristics.value": value}}
                                ]
                            }
                        }
                    }
                })

    query = {"query": {"bool": {"must": must or [{"match_all": {}}], "filter": filter_clauses}}}

    results = await es_client.search_offerings(query, from_=skip, size=limit)
    return results


@app.post("/api/v1/store/sync/{offering_id}", status_code=status.HTTP_204_NO_CONTENT)
async def sync_offering(offering_id: str):
    service = StoreService(mongodb_client, es_client)
    await service.sync_offering(offering_id)
    return None


@app.delete("/api/v1/store/offerings/{offering_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_offering_read(offering_id: str):
    service = StoreService(mongodb_client, es_client)
    await service.retire_offering(offering_id)
    return None


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8006)
