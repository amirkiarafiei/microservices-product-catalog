from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceSettings(BaseSettings):
    """
    Common configuration settings for all microservices.
    Each service should extend this class.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    SERVICE_NAME: str
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: Optional[str] = None

    # Messaging
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672"

    # Observability / Tracing
    ZIPKIN_ENDPOINT: str = "http://zipkin:9411/api/v2/spans"
    TRACING_ENABLED: bool = True

    # Security
    JWT_PUBLIC_KEY_URL: Optional[str] = None
    JWT_ALGORITHM: str = "RS256"
