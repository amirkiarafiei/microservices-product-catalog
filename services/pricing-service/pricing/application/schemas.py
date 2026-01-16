import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from ..domain.models import CurrencyEnum


class PriceBase(BaseModel):
    name: str
    value: Decimal
    unit: str
    currency: CurrencyEnum

    @field_validator("value")
    @classmethod
    def value_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Price value must be positive")
        return v.quantize(Decimal("0.01"))


class PriceCreate(PriceBase):
    pass


class PriceUpdate(PriceBase):
    pass


class PriceRead(PriceBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    locked: bool
    locked_by_saga_id: Optional[uuid.UUID]
    created_at: datetime
    updated_at: datetime


class PriceLock(BaseModel):
    saga_id: uuid.UUID
