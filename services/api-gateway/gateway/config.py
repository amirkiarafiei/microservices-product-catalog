from typing import List, Optional

from common.config import BaseServiceSettings


class GatewaySettings(BaseServiceSettings):
    """
    Settings for the API Gateway.
    """

    SERVICE_NAME: str = "api-gateway"
    PORT: int = 8000

    # Downstream Service URLs
    IDENTITY_SERVICE_URL: str = "http://identity-service:8001"
    CHARACTERISTIC_SERVICE_URL: str = "http://characteristic-service:8002"
    SPECIFICATION_SERVICE_URL: str = "http://specification-service:8003"
    PRICING_SERVICE_URL: str = "http://pricing-service:8004"
    OFFERING_SERVICE_URL: str = "http://offering-service:8005"
    STORE_SERVICE_URL: str = "http://store-service:8006"

    # Resilience Settings
    CONNECTION_TIMEOUT: float = 2.0
    READ_TIMEOUT: float = 4.0
    CB_FAILURE_THRESHOLD: int = 3
    CB_RESET_TIMEOUT: float = 20.0

    # CORS Settings
    ALLOWED_ORIGINS: List[str] = ["*"]

    # JWT Settings (Gateway trusts downstream validation but can also validate if needed)
    JWT_PUBLIC_KEY: Optional[str] = None

    # Observability Settings
    ZIPKIN_ENDPOINT: str = "http://localhost:9411/api/v2/spans"
    TRACING_ENABLED: bool = True


settings = GatewaySettings()
