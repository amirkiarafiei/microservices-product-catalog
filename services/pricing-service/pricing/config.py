from typing import Optional

from common.config import BaseServiceSettings


class PricingSettings(BaseServiceSettings):
    """
    Settings for the Pricing Service.
    """
    SERVICE_NAME: str = "pricing-service"
    # The public key used for JWT verification.
    JWT_PUBLIC_KEY: Optional[str] = None


settings = PricingSettings()
