from typing import Optional

from common.config import BaseServiceSettings


class SpecificationSettings(BaseServiceSettings):
    """
    Settings for the Specification Service.
    """
    SERVICE_NAME: str = "specification-service"
    # The public key used for JWT verification.
    JWT_PUBLIC_KEY: Optional[str] = None

    # Camunda Settings
    CAMUNDA_URL: str = "http://localhost:8085/engine-rest"
    SPECIFICATION_SERVICE_URL: str = "http://localhost:8003"


settings = SpecificationSettings()
