from typing import Optional

from common.config import BaseServiceSettings


class StoreSettings(BaseServiceSettings):
    """
    Settings for the Store Query Service.
    """
    SERVICE_NAME: str = "store-service"

    # MongoDB Settings
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "store_db"

    # Elasticsearch Settings
    ELASTICSEARCH_URL: str = "http://localhost:9200"
    ELASTICSEARCH_INDEX: str = "offerings"

    # External Service URLs
    CHARACTERISTIC_SERVICE_URL: str = "http://localhost:8002"
    SPECIFICATION_SERVICE_URL: str = "http://localhost:8003"
    PRICING_SERVICE_URL: str = "http://localhost:8004"
    OFFERING_SERVICE_URL: str = "http://localhost:8005"

    # Camunda Settings
    CAMUNDA_URL: str = "http://localhost:8085/engine-rest"

    # JWT Public Key for verification
    JWT_PUBLIC_KEY: Optional[str] = None


settings = StoreSettings()
