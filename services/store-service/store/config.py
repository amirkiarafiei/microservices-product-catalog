from typing import Optional

from common.config import BaseServiceSettings


class StoreSettings(BaseServiceSettings):
    """
    Settings for the Store Query Service.
    """
    SERVICE_NAME: str = "store-service"

    # MongoDB Settings
    MONGODB_URL: str = "mongodb://mongodb:27017"
    MONGODB_DB_NAME: str = "store_db"

    # Elasticsearch Settings
    ELASTICSEARCH_URL: str = "http://elasticsearch:9200"
    ELASTICSEARCH_INDEX: str = "offerings"

    # External Service URLs
    CHARACTERISTIC_SERVICE_URL: str = "http://characteristic-service:8002"
    SPECIFICATION_SERVICE_URL: str = "http://specification-service:8003"
    PRICING_SERVICE_URL: str = "http://pricing-service:8004"
    OFFERING_SERVICE_URL: str = "http://offering-service:8005"

    # Camunda Settings
    CAMUNDA_URL: str = "http://camunda:8080/engine-rest"

    # JWT Public Key for verification
    JWT_PUBLIC_KEY: Optional[str] = None


settings = StoreSettings()
