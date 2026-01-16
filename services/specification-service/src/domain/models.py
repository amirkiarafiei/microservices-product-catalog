import uuid
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class Specification(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    characteristic_ids: List[uuid.UUID]
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(from_attributes=True)
