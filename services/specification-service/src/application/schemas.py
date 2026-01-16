import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

class SpecificationBase(BaseModel):
    name: str
    characteristic_ids: List[uuid.UUID]

class SpecificationCreate(SpecificationBase):
    pass

class SpecificationUpdate(SpecificationBase):
    pass

class SpecificationRead(SpecificationBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
