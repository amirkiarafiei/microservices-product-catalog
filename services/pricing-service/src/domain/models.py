import uuid
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CurrencyEnum(str, Enum):
    USD = "USD"
    EUR = "EUR"
    TRY = "TRY"


class Price(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    value: Decimal
    unit: str
    currency: CurrencyEnum
    locked: bool = False
    locked_by_saga_id: Optional[uuid.UUID] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def update(self, name: str, value: Decimal, unit: str, currency: CurrencyEnum):
        if self.locked:
            return False
        self.name = name
        self.value = value
        self.unit = unit
        self.currency = currency
        self.updated_at = datetime.now(timezone.utc)
        return True

    def lock(self, saga_id: uuid.UUID):
        self.locked = True
        self.locked_by_saga_id = saga_id
        self.updated_at = datetime.now(timezone.utc)

    def unlock(self):
        self.locked = False
        self.locked_by_saga_id = None
        self.updated_at = datetime.now(timezone.utc)
