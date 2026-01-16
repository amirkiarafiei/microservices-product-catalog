import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from ..domain.models import LifecycleStatus


class OfferingBase(BaseModel):
    name: str
    description: Optional[str] = None
    specification_ids: List[uuid.UUID] = Field(default_factory=list)
    pricing_ids: List[uuid.UUID] = Field(default_factory=list)
    sales_channels: List[str] = Field(default_factory=list)


class OfferingCreate(OfferingBase):
    pass


class OfferingUpdate(OfferingBase):
    pass


class OfferingRead(OfferingBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    lifecycle_status: LifecycleStatus
    created_at: datetime
    updated_at: datetime
    published_at: Optional[datetime] = None
    retired_at: Optional[datetime] = None
