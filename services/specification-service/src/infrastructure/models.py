import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from .database import Base
from common.database.outbox import OutboxMixin

class SpecificationORM(Base):
    __tablename__ = "specifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), unique=True, nullable=False, index=True)
    characteristic_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_domain(self):
        from ..domain.models import Specification
        return Specification(
            id=self.id,
            name=self.name,
            characteristic_ids=self.characteristic_ids,
            created_at=self.created_at,
            updated_at=self.updated_at
        )

    @staticmethod
    def from_domain(spec):
        return SpecificationORM(
            id=spec.id,
            name=spec.name,
            characteristic_ids=spec.characteristic_ids,
            created_at=spec.created_at,
            updated_at=spec.updated_at
        )

class CachedCharacteristicORM(Base):
    """
    Local read-only cache of valid characteristic IDs.
    """
    __tablename__ = "cached_characteristics"

    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String(200), nullable=True) # Optional: cache name too for display
    last_updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class OutboxORM(Base, OutboxMixin):
    __tablename__ = "outbox"
