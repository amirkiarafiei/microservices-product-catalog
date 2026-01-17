"""
Identity Service - Authentication and Token Management.

Provides JWT token issuance and public key distribution for other services.
"""


from common.logging import setup_logging
from common.tracing import instrument_fastapi, setup_tracing
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db
from .models import User
from .security import create_access_token, verify_password
from .seed import seed_users

# Setup logging first
logger = setup_logging(settings.SERVICE_NAME, settings.LOG_LEVEL)

# Setup tracing
setup_tracing(
    service_name=settings.SERVICE_NAME,
    zipkin_endpoint=settings.ZIPKIN_ENDPOINT,
    enabled=settings.TRACING_ENABLED,
)

app = FastAPI(
    title="Identity Service",
    description="Identity & Authentication service for TMF Product Catalog",
    version="0.1.0",
)

# Instrument FastAPI for tracing
instrument_fastapi(app, excluded_urls="health")


@app.on_event("startup")
async def startup_event():
    logger.info("Starting up identity-service")
    # In a real app, you might run migrations here or via a sidecar
    seed_users()


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.SERVICE_NAME}


@app.post("/api/v1/auth/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if user:
        logger.info(f"DEBUG: Found user {user.username} with hash {user.password_hash}")
        is_valid = verify_password(form_data.password, user.password_hash)
        logger.info(f"DEBUG: Password check result: {is_valid} for input '{form_data.password}'")
    else:
        logger.info(f"DEBUG: User not found: {form_data.username}")

    if not user or not verify_password(form_data.password, user.password_hash):
        logger.warning(f"Failed login attempt for user: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username, "role": user.role}
    )

    logger.info(f"Successful login for user: {user.username} (Role: {user.role})")
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/v1/auth/public-key")
async def get_public_key():
    """
    Returns the RSA public key used for JWT verification.
    Other services use this to verify tokens without calling this service for every request.
    """
    # Fix newline escaping from env vars
    public_key = settings.JWT_PUBLIC_KEY.replace("\\n", "\n")
    return {"public_key": public_key, "algorithm": settings.JWT_ALGORITHM}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
