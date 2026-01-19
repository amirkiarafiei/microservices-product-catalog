from typing import Optional

from common.config import BaseServiceSettings


class CharacteristicSettings(BaseServiceSettings):
    """
    Settings for the Characteristic Service.
    """
    SERVICE_NAME: str = "characteristic-service"
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/characteristic_db"
    # The public key used for JWT verification.
    # In production, this would be fetched from Identity Service or shared via a secret.
    JWT_PUBLIC_KEY: Optional[str] = None
    # Identity Service URL for fetching public key
    IDENTITY_SERVICE_URL: str = "http://localhost:8001"

settings = CharacteristicSettings()
