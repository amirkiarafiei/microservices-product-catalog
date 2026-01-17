from typing import Optional

from common.config import BaseServiceSettings


class PricingSettings(BaseServiceSettings):
    """
    Settings for the Pricing Service.
    """
    SERVICE_NAME: str = "pricing-service"
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/pricing_db"
    # The public key used for JWT verification.
    JWT_PUBLIC_KEY: Optional[str] = None
    # Identity Service URL for fetching public key
    IDENTITY_SERVICE_URL: str = "http://localhost:8001"


settings = PricingSettings()
