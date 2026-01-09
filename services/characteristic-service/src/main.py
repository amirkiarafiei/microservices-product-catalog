from fastapi import FastAPI, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List
import uuid

from common.logging import setup_logging
from common.exceptions import AppException
from common.schemas import ErrorResponse, ErrorDetail
from common.security import get_current_user, RoleChecker, UserContext, security

from .config import settings
from .infrastructure.database import get_db
from .application.schemas import CharacteristicCreate, CharacteristicUpdate, CharacteristicRead
from .application.service import CharacteristicService

# Setup logging
logger = setup_logging(settings.SERVICE_NAME, settings.LOG_LEVEL)

app = FastAPI(
    title="Characteristic Service",
    description="Service for managing product characteristics",
    version="0.1.0"
)

# Exception handler for standardized error responses
from fastapi.responses import JSONResponse

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

# Security dependency override to inject public key
def get_current_user_with_key(token=Depends(security)):
    public_key = settings.JWT_PUBLIC_KEY.replace("\\n", "\n") if settings.JWT_PUBLIC_KEY else None
    return get_current_user(token=token, public_key=public_key, algorithm=settings.JWT_ALGORITHM)

app.dependency_overrides[get_current_user] = get_current_user_with_key

# Role checkers
admin_required = RoleChecker(allowed_roles=["ADMIN"])
any_user_required = RoleChecker(allowed_roles=["ADMIN", "USER"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.SERVICE_NAME}

@app.post("/api/v1/characteristics", 
          response_model=CharacteristicRead, 
          status_code=status.HTTP_201_CREATED,
          dependencies=[Depends(admin_required)])
def create_characteristic(
    char_in: CharacteristicCreate,
    db: Session = Depends(get_db)
):
    service = CharacteristicService(db)
    return service.create_characteristic(char_in)

@app.get("/api/v1/characteristics/{char_id}", 
         response_model=CharacteristicRead,
         dependencies=[Depends(any_user_required)])
def get_characteristic(
    char_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    service = CharacteristicService(db)
    return service.get_characteristic(char_id)

@app.get("/api/v1/characteristics", 
         response_model=List[CharacteristicRead],
         dependencies=[Depends(any_user_required)])
def list_characteristics(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    service = CharacteristicService(db)
    return service.list_characteristics(skip=skip, limit=limit)

@app.put("/api/v1/characteristics/{char_id}", 
         response_model=CharacteristicRead,
         dependencies=[Depends(admin_required)])
def update_characteristic(
    char_id: uuid.UUID,
    char_in: CharacteristicUpdate,
    db: Session = Depends(get_db)
):
    service = CharacteristicService(db)
    return service.update_characteristic(char_id, char_in)

@app.delete("/api/v1/characteristics/{char_id}", 
            status_code=status.HTTP_204_NO_CONTENT,
            dependencies=[Depends(admin_required)])
def delete_characteristic(
    char_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    service = CharacteristicService(db)
    service.delete_characteristic(char_id)
    return None

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
