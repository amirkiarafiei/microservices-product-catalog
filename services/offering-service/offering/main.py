"""
Offering Service - Manage Product Offerings and Lifecycle.

Provides CRUD operations for product offerings with saga orchestration for publication.
"""

import asyncio
import uuid
from contextlib import asynccontextmanager
from typing import List

from common.database.outbox import OutboxListener
from common.exceptions import AppException
from common.logging import setup_logging
from common.messaging import RabbitMQPublisher
from common.schemas import ErrorDetail, ErrorResponse
from common.security import RoleChecker, get_current_user, security
from common.tracing import instrument_fastapi, instrument_httpx, setup_tracing
from fastapi import Depends, FastAPI, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .application.schemas import OfferingCreate, OfferingRead, OfferingUpdate
from .application.service import OfferingService
from .config import settings
from .infrastructure.database import SessionLocal, get_db
from .infrastructure.models import OutboxORM

# Setup logging first
logger = setup_logging(settings.SERVICE_NAME, settings.LOG_LEVEL)

# Setup tracing
setup_tracing(
    service_name=settings.SERVICE_NAME,
    zipkin_endpoint=settings.ZIPKIN_ENDPOINT,
    enabled=settings.TRACING_ENABLED,
)

# Instrument HTTPX for outgoing requests (Camunda calls)
instrument_httpx()

# Global background tasks
outbox_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global outbox_task
    logger.info("Starting up offering-service")

    # Initialize RabbitMQ Publisher for Outbox
    publisher = RabbitMQPublisher(settings.RABBITMQ_URL)

    # Initialize Outbox Listener
    dsn = (
        settings.DATABASE_URL.replace("postgresql://", "postgres://")
        if settings.DATABASE_URL
        else None
    )

    if dsn:
        listener = OutboxListener(
            dsn=dsn,
            publisher=publisher,
            outbox_model=OutboxORM,
            session_factory=SessionLocal,
        )
        outbox_task = asyncio.create_task(listener.run())
        logger.info("Outbox listener background task started")
    else:
        logger.warning("DATABASE_URL not set, outbox listener not started")

    yield

    # Shutdown tasks
    if outbox_task:
        outbox_task.cancel()

    try:
        if outbox_task:
            await outbox_task
    except asyncio.CancelledError:
        pass
    logger.info("Shutdown complete")


app = FastAPI(
    title="Offering Service",
    description="Service for managing product offerings and their lifecycle",
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
    elif exc.code == "CONFLICT":
        status_code = status.HTTP_409_CONFLICT
    elif exc.code == "SERVICE_UNAVAILABLE":
        status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    elif exc.code == "UNAUTHORIZED":
        status_code = status.HTTP_401_UNAUTHORIZED
    elif exc.code == "FORBIDDEN":
        status_code = status.HTTP_403_FORBIDDEN
    elif exc.code == "INTERNAL_ERROR":
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return JSONResponse(
        status_code=status_code,
        content=ErrorResponse(
            error=ErrorDetail(code=exc.code, message=exc.message, details=exc.details)
        ).model_dump(),
    )


# Security dependency override to inject public key
def get_current_user_with_key(token=Depends(security)):
    public_key = (
        settings.JWT_PUBLIC_KEY.replace("\\n", "\n") if settings.JWT_PUBLIC_KEY else None
    )
    return get_current_user(token=token, public_key=public_key, algorithm=settings.JWT_ALGORITHM)


app.dependency_overrides[get_current_user] = get_current_user_with_key

# Role checkers
admin_required = RoleChecker(allowed_roles=["ADMIN"])
any_user_required = RoleChecker(allowed_roles=["ADMIN", "USER"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.SERVICE_NAME}


@app.post(
    "/api/v1/offerings",
    response_model=OfferingRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(admin_required)],
)
async def create_offering(offering_in: OfferingCreate, db: Session = Depends(get_db)):
    service = OfferingService(db)
    return await service.create_offering(offering_in)


@app.get(
    "/api/v1/offerings/{offering_id}",
    response_model=OfferingRead,
    dependencies=[Depends(any_user_required)],
)
def get_offering(offering_id: uuid.UUID, db: Session = Depends(get_db)):
    service = OfferingService(db)
    return service.get_offering(offering_id)


@app.get(
    "/api/v1/offerings",
    response_model=List[OfferingRead],
    dependencies=[Depends(any_user_required)],
)
def list_offerings(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    service = OfferingService(db)
    return service.list_offerings(skip=skip, limit=limit)


@app.put(
    "/api/v1/offerings/{offering_id}",
    response_model=OfferingRead,
    dependencies=[Depends(admin_required)],
)
async def update_offering(
    offering_id: uuid.UUID, offering_in: OfferingUpdate, db: Session = Depends(get_db)
):
    service = OfferingService(db)
    return await service.update_offering(offering_id, offering_in)


@app.delete(
    "/api/v1/offerings/{offering_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(admin_required)],
)
def delete_offering(offering_id: uuid.UUID, db: Session = Depends(get_db)):
    service = OfferingService(db)
    service.delete_offering(offering_id)
    return None


@app.post(
    "/api/v1/offerings/{offering_id}/publish",
    response_model=OfferingRead,
    dependencies=[Depends(admin_required)],
)
async def publish_offering(offering_id: uuid.UUID, db: Session = Depends(get_db)):
    service = OfferingService(db)
    return await service.initiate_publication(offering_id)


@app.post(
    "/api/v1/offerings/{offering_id}/retire",
    response_model=OfferingRead,
    dependencies=[Depends(admin_required)],
)
def retire_offering(offering_id: uuid.UUID, db: Session = Depends(get_db)):
    service = OfferingService(db)
    return service.retire_offering(offering_id)


@app.post(
    "/api/v1/offerings/{offering_id}/confirm",
    response_model=OfferingRead,
    dependencies=[Depends(admin_required)],
)
def confirm_offering(offering_id: uuid.UUID, db: Session = Depends(get_db)):
    service = OfferingService(db)
    return service.confirm_publication(offering_id)


@app.post(
    "/api/v1/offerings/{offering_id}/fail",
    response_model=OfferingRead,
    dependencies=[Depends(admin_required)],
)
def fail_offering(offering_id: uuid.UUID, db: Session = Depends(get_db)):
    service = OfferingService(db)
    return service.fail_publication(offering_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8005)
