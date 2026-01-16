import uuid
from typing import List

import httpx
from common.exceptions import AppException, NotFoundError
from sqlalchemy.orm import Session

from ..config import settings
from ..domain.models import LifecycleStatus, ProductOffering
from ..infrastructure.models import OutboxORM, ProductOfferingORM
from ..infrastructure.repository import OfferingRepository
from .events import (
    OfferingCreated,
    OfferingPublicationInitiated,
    OfferingPublished,
    OfferingRetired,
    OfferingUpdated,
)
from .schemas import OfferingCreate, OfferingUpdate


class OfferingService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = OfferingRepository(db)

    def _add_to_outbox(self, topic: str, event: OfferingCreated | OfferingUpdated | OfferingPublicationInitiated | OfferingPublished | OfferingRetired):
        outbox_entry = OutboxORM(topic=topic, payload=event.model_dump(mode="json"))
        self.db.add(outbox_entry)

    async def _validate_external_ids(self, spec_ids: List[uuid.UUID], price_ids: List[uuid.UUID]):
        """
        Cross-service validation: Synchronous HTTP calls to Specification and Pricing services.
        """
        async with httpx.AsyncClient() as client:
            # Validate Specification IDs
            for spec_id in spec_ids:
                try:
                    resp = await client.get(f"{settings.SPECIFICATION_SERVICE_URL}/api/v1/specifications/{spec_id}", timeout=5.0)
                    if resp.status_code != 200:
                        raise AppException(f"Specification ID {spec_id} not found or invalid", code="BAD_REQUEST")
                except httpx.RequestError as e:
                    raise AppException(f"Could not connect to Specification Service: {str(e)}", code="SERVICE_UNAVAILABLE")

            # Validate Pricing IDs
            for price_id in price_ids:
                try:
                    resp = await client.get(f"{settings.PRICING_SERVICE_URL}/api/v1/prices/{price_id}", timeout=5.0)
                    if resp.status_code != 200:
                        raise AppException(f"Price ID {price_id} not found or invalid", code="BAD_REQUEST")
                except httpx.RequestError as e:
                    raise AppException(f"Could not connect to Pricing Service: {str(e)}", code="SERVICE_UNAVAILABLE")

    async def create_offering(self, offering_in: OfferingCreate) -> ProductOfferingORM:
        # Validate IDs if provided
        if offering_in.specification_ids or offering_in.pricing_ids:
            await self._validate_external_ids(offering_in.specification_ids, offering_in.pricing_ids)

        offering_domain = ProductOffering(**offering_in.model_dump())
        offering_orm = ProductOfferingORM.from_domain(offering_domain)

        self.repository.create(offering_orm)
        self.db.flush()

        event = OfferingCreated(payload=offering_orm.to_domain().model_dump(mode="json"))
        self._add_to_outbox("product.offering.events", event)

        self.db.commit()
        return offering_orm

    def get_offering(self, offering_id: uuid.UUID) -> ProductOfferingORM:
        offering = self.repository.get_by_id(offering_id)
        if not offering:
            raise NotFoundError(f"Offering with ID {offering_id} not found")
        return offering

    def list_offerings(self, skip: int = 0, limit: int = 100) -> List[ProductOfferingORM]:
        return self.repository.list(skip, limit)

    async def update_offering(self, offering_id: uuid.UUID, offering_in: OfferingUpdate) -> ProductOfferingORM:
        offering_orm = self.get_offering(offering_id)

        if offering_orm.lifecycle_status != LifecycleStatus.DRAFT.value:
            raise AppException(f"Cannot update offering in {offering_orm.lifecycle_status} state", code="BAD_REQUEST")

        # Validate IDs
        if offering_in.specification_ids or offering_in.pricing_ids:
            await self._validate_external_ids(offering_in.specification_ids, offering_in.pricing_ids)

        offering_orm.name = offering_in.name
        offering_orm.description = offering_in.description
        offering_orm.specification_ids = offering_in.specification_ids
        offering_orm.pricing_ids = offering_in.pricing_ids
        offering_orm.sales_channels = offering_in.sales_channels

        self.db.flush()

        event = OfferingUpdated(payload=offering_orm.to_domain().model_dump(mode="json"))
        self._add_to_outbox("product.offering.events", event)

        self.db.commit()
        return offering_orm

    def delete_offering(self, offering_id: uuid.UUID):
        offering_orm = self.get_offering(offering_id)

        if offering_orm.lifecycle_status != LifecycleStatus.DRAFT.value:
            raise AppException(f"Cannot delete offering in {offering_orm.lifecycle_status} state", code="BAD_REQUEST")

        self.repository.delete(offering_orm)
        self.db.flush()

        # No specific event for delete in the plan, but good practice
        # self._add_to_outbox("product.offering.events", OfferingDeleted(...))

        self.db.commit()

    async def initiate_publication(self, offering_id: uuid.UUID) -> ProductOfferingORM:
        offering_orm = self.get_offering(offering_id)
        offering_domain = offering_orm.to_domain()

        try:
            offering_domain.publish() # Transitions DRAFT -> PUBLISHING
        except ValueError as e:
            raise AppException(str(e), code="BAD_REQUEST")

        # Sync back to ORM
        offering_orm.lifecycle_status = offering_domain.lifecycle_status.value
        offering_orm.updated_at = offering_domain.updated_at

        self.db.flush()

        event = OfferingPublicationInitiated(payload=offering_domain.model_dump(mode="json"))
        self._add_to_outbox("product.offering.events", event)

        # Mocked part: immediately confirm publication for now as per Phase 9 notes
        # "Mock the publish() to simply change state for now (no Camunda yet)"
        # "State changes to PUBLISHING -> PUBLISHED (mocked)"

        offering_domain.confirm_publication()
        offering_orm.lifecycle_status = offering_domain.lifecycle_status.value
        offering_orm.published_at = offering_domain.published_at
        offering_orm.updated_at = offering_domain.updated_at

        pub_event = OfferingPublished(payload=offering_domain.model_dump(mode="json"))
        self._add_to_outbox("product.offering.events", pub_event)

        self.db.commit()
        return offering_orm

    def retire_offering(self, offering_id: uuid.UUID) -> ProductOfferingORM:
        offering_orm = self.get_offering(offering_id)
        offering_domain = offering_orm.to_domain()

        try:
            offering_domain.retire()
        except ValueError as e:
            raise AppException(str(e), code="BAD_REQUEST")

        offering_orm.lifecycle_status = offering_domain.lifecycle_status.value
        offering_orm.retired_at = offering_domain.retired_at
        offering_orm.updated_at = offering_domain.updated_at

        self.db.flush()

        event = OfferingRetired(payload=offering_domain.model_dump(mode="json"))
        self._add_to_outbox("product.offering.events", event)

        self.db.commit()
        return offering_orm
