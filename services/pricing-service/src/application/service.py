import uuid
from typing import List

from common.exceptions import AppException, ConflictError, NotFoundError
from sqlalchemy.orm import Session

from ..infrastructure.models import OutboxORM, PriceORM
from ..infrastructure.repository import PriceRepository
from .events import PriceCreated, PriceDeleted, PriceLocked, PriceUnlocked, PriceUpdated
from .schemas import PriceCreate, PriceUpdate


class PricingService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = PriceRepository(db)

    def _add_to_outbox(
        self, topic: str, event: PriceCreated | PriceUpdated | PriceDeleted | PriceLocked | PriceUnlocked
    ):
        outbox_entry = OutboxORM(topic=topic, payload=event.model_dump(mode="json"))
        self.db.add(outbox_entry)

    def create_price(self, price_in: PriceCreate) -> PriceORM:
        if self.repository.get_by_name(price_in.name):
            raise ConflictError(f"Price with name '{price_in.name}' already exists")

        price_orm = PriceORM(
            name=price_in.name,
            value=price_in.value,
            unit=price_in.unit,
            currency=price_in.currency.value,
        )

        self.repository.create(price_orm)
        self.db.flush()

        event = PriceCreated(payload=price_orm.to_domain().model_dump(mode="json"))
        self._add_to_outbox("commercial.pricing.events", event)

        self.db.commit()
        return price_orm

    def get_price(self, price_id: uuid.UUID) -> PriceORM:
        price = self.repository.get_by_id(price_id)
        if not price:
            raise NotFoundError(f"Price with ID {price_id} not found")
        return price

    def list_prices(self, skip: int = 0, limit: int = 100) -> List[PriceORM]:
        return self.repository.list(skip, limit)

    def update_price(self, price_id: uuid.UUID, price_in: PriceUpdate) -> PriceORM:
        price_orm = self.get_price(price_id)

        if price_orm.locked:
            raise AppException(
                code="LOCKED",
                message=f"Price {price_id} is locked by saga {price_orm.locked_by_saga_id} and cannot be modified",
            )

        if price_in.name != price_orm.name:
            if self.repository.get_by_name(price_in.name):
                raise ConflictError(f"Price with name '{price_in.name}' already exists")

        price_orm.name = price_in.name
        price_orm.value = price_in.value
        price_orm.unit = price_in.unit
        price_orm.currency = price_in.currency.value

        self.db.flush()

        event = PriceUpdated(payload=price_orm.to_domain().model_dump(mode="json"))
        self._add_to_outbox("commercial.pricing.events", event)

        self.db.commit()
        return price_orm

    def delete_price(self, price_id: uuid.UUID):
        price_orm = self.get_price(price_id)

        if price_orm.locked:
            raise AppException(
                code="LOCKED",
                message=f"Price {price_id} is locked by saga {price_orm.locked_by_saga_id} and cannot be deleted",
            )

        self.repository.delete(price_orm)

        event = PriceDeleted(payload={"id": str(price_id)})
        self._add_to_outbox("commercial.pricing.events", event)

        self.db.commit()

    def lock_price(self, price_id: uuid.UUID, saga_id: uuid.UUID) -> PriceORM:
        price_orm = self.get_price(price_id)

        # If already locked by the same saga, just return
        if price_orm.locked and price_orm.locked_by_saga_id == saga_id:
            return price_orm

        if price_orm.locked:
            raise AppException(
                code="LOCKED",
                message=f"Price {price_id} is already locked by another saga: {price_orm.locked_by_saga_id}",
            )

        price_orm.locked = True
        price_orm.locked_by_saga_id = saga_id

        self.db.flush()

        event = PriceLocked(payload={"id": str(price_id), "locked_by_saga_id": str(saga_id)})
        self._add_to_outbox("commercial.pricing.events", event)

        self.db.commit()
        return price_orm

    def unlock_price(self, price_id: uuid.UUID) -> PriceORM:
        price_orm = self.get_price(price_id)

        if not price_orm.locked:
            return price_orm

        saga_id = price_orm.locked_by_saga_id
        price_orm.locked = False
        price_orm.locked_by_saga_id = None

        self.db.flush()

        event = PriceUnlocked(payload={"id": str(price_id), "previously_locked_by": str(saga_id)})
        self._add_to_outbox("commercial.pricing.events", event)

        self.db.commit()
        return price_orm
