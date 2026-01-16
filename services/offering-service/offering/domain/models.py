import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class LifecycleStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHING = "PUBLISHING"
    PUBLISHED = "PUBLISHED"
    RETIRED = "RETIRED"


class ProductOffering(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    name: str
    description: Optional[str] = None
    specification_ids: List[uuid.UUID] = Field(default_factory=list)
    pricing_ids: List[uuid.UUID] = Field(default_factory=list)
    sales_channels: List[str] = Field(default_factory=list)
    lifecycle_status: LifecycleStatus = LifecycleStatus.DRAFT
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    published_at: Optional[datetime] = None
    retired_at: Optional[datetime] = None

    def can_publish(self) -> bool:
        """
        Validation result: needs 1+ spec, 1+ price, 1+ channel.
        """
        return (
            len(self.specification_ids) > 0
            and len(self.pricing_ids) > 0
            and len(self.sales_channels) > 0
        )

    def publish(self):
        """
        Transitions DRAFT -> PUBLISHING.
        """
        if self.lifecycle_status != LifecycleStatus.DRAFT:
            raise ValueError(f"Cannot publish from {self.lifecycle_status} state")
        if not self.can_publish():
            raise ValueError("Offering must have at least one specification, one price, and one channel to be published")

        self.lifecycle_status = LifecycleStatus.PUBLISHING
        self.updated_at = datetime.now(timezone.utc)

    def confirm_publication(self):
        """
        Transitions PUBLISHING -> PUBLISHED.
        """
        if self.lifecycle_status != LifecycleStatus.PUBLISHING:
            raise ValueError(f"Cannot confirm publication from {self.lifecycle_status} state")

        self.lifecycle_status = LifecycleStatus.PUBLISHED
        self.published_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def fail_publication(self):
        """
        Transitions PUBLISHING -> DRAFT.
        """
        if self.lifecycle_status != LifecycleStatus.PUBLISHING:
            raise ValueError(f"Cannot fail publication from {self.lifecycle_status} state")

        self.lifecycle_status = LifecycleStatus.DRAFT
        self.updated_at = datetime.now(timezone.utc)

    def retire(self):
        """
        Transitions PUBLISHED -> RETIRED.
        """
        if self.lifecycle_status != LifecycleStatus.PUBLISHED:
            raise ValueError(f"Cannot retire from {self.lifecycle_status} state")

        self.lifecycle_status = LifecycleStatus.RETIRED
        self.retired_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
