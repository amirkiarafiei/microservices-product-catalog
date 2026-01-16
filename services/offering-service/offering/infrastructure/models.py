import uuid
from datetime import datetime, timezone

from common.database.outbox import OutboxMixin
from sqlalchemy import Column, DateTime, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID

from ..domain.models import LifecycleStatus, ProductOffering
from .database import Base


class ProductOfferingORM(Base):
    __tablename__ = "product_offerings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    specification_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False, default=list)
    pricing_ids = Column(ARRAY(UUID(as_uuid=True)), nullable=False, default=list)
    sales_channels = Column(ARRAY(String), nullable=False, default=list)
    lifecycle_status = Column(String(20), nullable=False, default=LifecycleStatus.DRAFT.value)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc)
    )
    published_at = Column(DateTime, nullable=True)
    retired_at = Column(DateTime, nullable=True)

    def to_domain(self) -> ProductOffering:
        return ProductOffering(
            id=self.id,
            name=self.name,
            description=self.description,
            specification_ids=self.specification_ids,
            pricing_ids=self.pricing_ids,
            sales_channels=self.sales_channels,
            lifecycle_status=LifecycleStatus(self.lifecycle_status),
            created_at=self.created_at,
            updated_at=self.updated_at,
            published_at=self.published_at,
            retired_at=self.retired_at,
        )

    @staticmethod
    def from_domain(offering: ProductOffering) -> "ProductOfferingORM":
        return ProductOfferingORM(
            id=offering.id,
            name=offering.name,
            description=offering.description,
            specification_ids=offering.specification_ids,
            pricing_ids=offering.pricing_ids,
            sales_channels=offering.sales_channels,
            lifecycle_status=offering.lifecycle_status.value,
            created_at=offering.created_at,
            updated_at=offering.updated_at,
            published_at=offering.published_at,
            retired_at=offering.retired_at,
        )


class OutboxORM(Base, OutboxMixin):
    __tablename__ = "outbox"
