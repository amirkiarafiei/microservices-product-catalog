import uuid
from datetime import datetime, timezone
from decimal import Decimal

from common.database.outbox import OutboxMixin
from sqlalchemy import Boolean, Column, DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import UUID

from ..domain.models import Price, CurrencyEnum
from .database import Base


class PriceORM(Base):
    __tablename__ = "prices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), unique=True, nullable=False, index=True)
    value = Column(Numeric(10, 2), nullable=False)
    unit = Column(String(50), nullable=False)
    currency = Column(String(3), nullable=False)
    locked = Column(Boolean, default=False)
    locked_by_saga_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )

    def to_domain(self) -> Price:
        return Price(
            id=self.id or uuid.uuid4(),
            name=self.name,
            value=self.value,
            unit=self.unit,
            currency=CurrencyEnum(self.currency),
            locked=self.locked or False,
            locked_by_saga_id=self.locked_by_saga_id,
            created_at=self.created_at or datetime.now(timezone.utc),
            updated_at=self.updated_at or datetime.now(timezone.utc),
        )

    @staticmethod
    def from_domain(price: Price) -> "PriceORM":
        return PriceORM(
            id=price.id,
            name=price.name,
            value=price.value,
            unit=price.unit,
            currency=price.currency.value,
            locked=price.locked,
            locked_by_saga_id=price.locked_by_saga_id,
            created_at=price.created_at,
            updated_at=price.updated_at,
        )


class OutboxORM(Base, OutboxMixin):
    __tablename__ = "outbox"
