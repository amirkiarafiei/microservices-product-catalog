from typing import Optional

from common.config import BaseServiceSettings


class CharacteristicSettings(BaseServiceSettings):
    """
    Settings for the Characteristic Service.
    """
    SERVICE_NAME: str = "characteristic-service"
    # The public key used for JWT verification.
    # In production, this would be fetched from Identity Service or shared via a secret.
    JWT_PUBLIC_KEY: Optional[str] = None

settings = CharacteristicSettings()
