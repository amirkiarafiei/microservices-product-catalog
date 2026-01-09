from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from uuid import UUID
from datetime import datetime
from ..domain.models import UnitOfMeasure


class CharacteristicBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    value: str = Field(..., min_length=1, max_length=100)
    unit_of_measure: UnitOfMeasure


class CharacteristicCreate(CharacteristicBase):
    pass


class CharacteristicUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    value: Optional[str] = Field(None, min_length=1, max_length=100)
    unit_of_measure: Optional[UnitOfMeasure] = None


class CharacteristicRead(CharacteristicBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime
