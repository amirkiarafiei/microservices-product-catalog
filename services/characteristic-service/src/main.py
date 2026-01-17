"""
Characteristic Service - Manage Product Characteristics.

Provides CRUD operations for product characteristics with event sourcing via outbox pattern.
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
from common.tracing import instrument_fastapi, setup_tracing
from fastapi import Depends, FastAPI, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .application.schemas import CharacteristicCreate, CharacteristicRead, CharacteristicUpdate
from .application.service import CharacteristicService
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

# Global background task
outbox_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global outbox_task
    logger.info("Starting up characteristic-service")

    # Initialize RabbitMQ Publisher
    publisher = RabbitMQPublisher(settings.RABBITMQ_URL)

    # Initialize Outbox Listener
    # DSN for asyncpg (needs to be postgres:// instead of postgresql://)
    # Also handle postgresql+psycopg2:// which SQLAlchemy might use
    dsn = None
    if settings.DATABASE_URL:
        dsn = settings.DATABASE_URL.replace("postgresql+psycopg2://", "postgres://")
        dsn = dsn.replace("postgresql://", "postgres://")

    if dsn:
        listener = OutboxListener(
            dsn=dsn,
            publisher=publisher,
            outbox_model=OutboxORM,
            session_factory=SessionLocal,
        )

        # Start as background task
        outbox_task = asyncio.create_task(listener.run())
        logger.info("Outbox listener background task started")
    else:
        logger.warning("DATABASE_URL not set, outbox listener not started")

    yield

    if outbox_task:
        outbox_task.cancel()
        try:
            await outbox_task
        except asyncio.CancelledError:
            pass
    logger.info("Shutdown complete")


app = FastAPI(
    title="Characteristic Service",
    description="Service for managing product characteristics",
    version="0.1.0",
    lifespan=lifespan,
)

# Instrument FastAPI for tracing
instrument_fastapi(app, excluded_urls="health")


# Exception handler for standardized error responses
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
    "/api/v1/characteristics",
    response_model=CharacteristicRead,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(admin_required)],
)
def create_characteristic(char_in: CharacteristicCreate, db: Session = Depends(get_db)):
    service = CharacteristicService(db)
    return service.create_characteristic(char_in)


@app.get(
    "/api/v1/characteristics/{char_id}",
    response_model=CharacteristicRead,
    dependencies=[Depends(any_user_required)],
)
def get_characteristic(char_id: uuid.UUID, db: Session = Depends(get_db)):
    service = CharacteristicService(db)
    return service.get_characteristic(char_id)


@app.get(
    "/api/v1/characteristics",
    response_model=List[CharacteristicRead],
    dependencies=[Depends(any_user_required)],
)
def list_characteristics(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    service = CharacteristicService(db)
    return service.list_characteristics(skip=skip, limit=limit)


@app.put(
    "/api/v1/characteristics/{char_id}",
    response_model=CharacteristicRead,
    dependencies=[Depends(admin_required)],
)
def update_characteristic(
    char_id: uuid.UUID, char_in: CharacteristicUpdate, db: Session = Depends(get_db)
):
    service = CharacteristicService(db)
    return service.update_characteristic(char_id, char_in)


@app.delete(
    "/api/v1/characteristics/{char_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(admin_required)],
)
def delete_characteristic(char_id: uuid.UUID, db: Session = Depends(get_db)):
    service = CharacteristicService(db)
    service.delete_characteristic(char_id)
    return None


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)
