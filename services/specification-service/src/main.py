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
from fastapi import Depends, FastAPI, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from .application.consumers import CharacteristicConsumer
from .application.schemas import SpecificationCreate, SpecificationRead, SpecificationUpdate
from .application.service import SpecificationService
from .config import settings
from .infrastructure.database import SessionLocal, get_db
from .infrastructure.models import OutboxORM

# Setup logging
logger = setup_logging(settings.SERVICE_NAME, settings.LOG_LEVEL)

# Global background tasks
outbox_task = None
consumer_task = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global outbox_task, consumer_task
    logger.info("Starting up specification-service")

    # Initialize RabbitMQ Publisher
    publisher = RabbitMQPublisher(settings.RABBITMQ_URL)

    # Initialize Outbox Listener
    dsn = settings.DATABASE_URL.replace("postgresql://", "postgres://") if settings.DATABASE_URL else None

    if dsn:
        # 1. Start Outbox Listener
        listener = OutboxListener(
            dsn=dsn,
            publisher=publisher,
            outbox_model=OutboxORM,
            session_factory=SessionLocal
        )
        outbox_task = asyncio.create_task(listener.run())
        logger.info("Outbox listener background task started")

        # 2. Start Characteristic Consumer
        consumer = CharacteristicConsumer()
        consumer_task = asyncio.create_task(consumer.run())
        logger.info("Characteristic event consumer background task started")
    else:
        logger.warning("DATABASE_URL not set, background tasks not started")

    yield

    # Shutdown
    if outbox_task:
        outbox_task.cancel()
    if consumer_task:
        consumer_task.cancel()

    try:
        if outbox_task:
            await outbox_task
        if consumer_task:
            await consumer_task
    except asyncio.CancelledError:
        pass

    logger.info("Shutdown complete")

app = FastAPI(
    title="Specification Service",
    description="Service for managing product technical specifications",
    version="0.1.0",
    lifespan=lifespan
)

# Exception handler
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
            error=ErrorDetail(
                code=exc.code,
                message=exc.message,
                details=exc.details
            )
        ).model_dump()
    )

# Security
def get_current_user_with_key(token=Depends(security)):
    public_key = settings.JWT_PUBLIC_KEY.replace("\\n", "\n") if settings.JWT_PUBLIC_KEY else None
    return get_current_user(token=token, public_key=public_key, algorithm=settings.JWT_ALGORITHM)

app.dependency_overrides[get_current_user] = get_current_user_with_key

admin_required = RoleChecker(allowed_roles=["ADMIN"])
any_user_required = RoleChecker(allowed_roles=["ADMIN", "USER"])

# Routes
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.SERVICE_NAME}

@app.post("/api/v1/specifications",
          response_model=SpecificationRead,
          status_code=status.HTTP_201_CREATED,
          dependencies=[Depends(admin_required)])
def create_specification(
    spec_in: SpecificationCreate,
    db: Session = Depends(get_db)
):
    service = SpecificationService(db)
    return service.create_specification(spec_in)

@app.get("/api/v1/specifications/{spec_id}",
         response_model=SpecificationRead,
         dependencies=[Depends(any_user_required)])
def get_specification(
    spec_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    service = SpecificationService(db)
    return service.get_specification(spec_id)

@app.get("/api/v1/specifications",
         response_model=List[SpecificationRead],
         dependencies=[Depends(any_user_required)])
def list_specifications(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    service = SpecificationService(db)
    return service.list_specifications(skip=skip, limit=limit)

@app.put("/api/v1/specifications/{spec_id}",
         response_model=SpecificationRead,
         dependencies=[Depends(admin_required)])
def update_specification(
    spec_id: uuid.UUID,
    spec_in: SpecificationUpdate,
    db: Session = Depends(get_db)
):
    service = SpecificationService(db)
    return service.update_specification(spec_id, spec_in)

@app.delete("/api/v1/specifications/{spec_id}",
            status_code=status.HTTP_204_NO_CONTENT,
            dependencies=[Depends(admin_required)])
def delete_specification(
    spec_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    service = SpecificationService(db)
    service.delete_specification(spec_id)
    return None

@app.post("/api/v1/specifications/validate",
          status_code=status.HTTP_204_NO_CONTENT,
          dependencies=[Depends(admin_required)])
def validate_specifications(
    spec_ids: List[uuid.UUID],
    db: Session = Depends(get_db)
):
    service = SpecificationService(db)
    service.validate_specifications(spec_ids)
    return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
