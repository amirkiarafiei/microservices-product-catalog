from typing import Optional

from common.config import BaseServiceSettings


class OfferingSettings(BaseServiceSettings):
    """
    Settings for the Offering Service.
    """
    SERVICE_NAME: str = "offering-service"
    # The public key used for JWT verification.
    JWT_PUBLIC_KEY: Optional[str] = None

    # External Service URLs
    SPECIFICATION_SERVICE_URL: str = "http://specification-service:8003"
    PRICING_SERVICE_URL: str = "http://pricing-service:8004"
    OFFERING_SERVICE_URL: str = "http://offering-service:8005"
    STORE_SERVICE_URL: str = "http://store-service:8006"

    # Camunda Settings
    CAMUNDA_URL: str = "http://camunda:8080/engine-rest"


settings = OfferingSettings()
