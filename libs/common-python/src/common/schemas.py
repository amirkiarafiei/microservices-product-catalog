from typing import Any, Dict, Optional
from datetime import datetime, timezone
import uuid
from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    correlation_id: Optional[str] = None

class ErrorResponse(BaseModel):
    error: ErrorDetail


class Event(BaseModel):
    """Base schema for all domain events."""
    event_id: uuid.UUID = Field(default_factory=uuid.uuid4)
    event_type: str
    schema_version: str = "1.0"
    entity_version: int = 1
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: Optional[str] = None
    payload: Dict[str, Any]
