from common.config import BaseServiceSettings
from pydantic import Field


class IdentitySettings(BaseServiceSettings):
    """
    Configuration settings for the Identity Service.
    """
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # These must be set in the .env file
    JWT_PRIVATE_KEY: str = Field(..., description="RSA Private Key for signing JWTs")
    JWT_PUBLIC_KEY: str = Field(..., description="RSA Public Key for sharing with other services")

settings = IdentitySettings()
