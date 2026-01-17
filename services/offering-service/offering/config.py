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
    SPECIFICATION_SERVICE_URL: str = "http://localhost:8003"
    PRICING_SERVICE_URL: str = "http://localhost:8004"
    OFFERING_SERVICE_URL: str = "http://localhost:8005"
    STORE_SERVICE_URL: str = "http://localhost:8006"

    # Camunda Settings
    CAMUNDA_URL: str = "http://localhost:8085/engine-rest"


settings = OfferingSettings()
