import uuid
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime, timezone

from .database import Base
from ..domain.models import UnitOfMeasure
from common.database.outbox import OutboxMixin


class CharacteristicORM(Base):
    __tablename__ = "characteristics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), unique=True, nullable=False, index=True)
    value = Column(String(100), nullable=False)
    unit_of_measure = Column(SQLEnum(UnitOfMeasure), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_domain(self):
        from ..domain.models import Characteristic
        return Characteristic(
            id=self.id,
            name=self.name,
            value=self.value,
            unit_of_measure=self.unit_of_measure,
            created_at=self.created_at,
            updated_at=self.updated_at
        )

    @staticmethod
    def from_domain(char):
        return CharacteristicORM(
            id=char.id,
            name=char.name,
            value=char.value,
            unit_of_measure=char.unit_of_measure,
            created_at=char.created_at,
            updated_at=char.updated_at
        )


class OutboxORM(Base, OutboxMixin):
    __tablename__ = "outbox"
