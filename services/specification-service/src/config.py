from typing import Optional

from common.config import BaseServiceSettings


class SpecificationSettings(BaseServiceSettings):
    """
    Settings for the Specification Service.
    """
    SERVICE_NAME: str = "specification-service"
    # The public key used for JWT verification.
    # In production, this would be fetched from Identity Service or shared via a secret.
    JWT_PUBLIC_KEY: Optional[str] = None

settings = SpecificationSettings()
