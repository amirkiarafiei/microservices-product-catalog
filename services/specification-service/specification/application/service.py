import uuid
from typing import List

from common.exceptions import AppException
from sqlalchemy.orm import Session

from ..infrastructure.models import CachedCharacteristicORM, OutboxORM, SpecificationORM
from ..infrastructure.repository import SpecificationRepository
from .events import SpecificationCreated, SpecificationDeleted, SpecificationUpdated
from .schemas import SpecificationCreate, SpecificationUpdate


class SpecificationService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = SpecificationRepository(db)

    def _validate_characteristics(self, characteristic_ids: List[uuid.UUID]):
        """
        Validates that all characteristic IDs exist in the local cache.
        """
        if not characteristic_ids:
            raise AppException("A specification must have at least one characteristic", "VALIDATION_ERROR")

        # Query local cache
        existing = self.db.query(CachedCharacteristicORM.id).filter(
            CachedCharacteristicORM.id.in_(characteristic_ids)
        ).all()

        existing_ids = {row.id for row in existing}
        missing_ids = [str(cid) for cid in characteristic_ids if cid not in existing_ids]

        if missing_ids:
            raise AppException(
                f"Missing characteristic IDs in local cache: {', '.join(missing_ids)}. "
                "Ensure they exist in Characteristic Service.",
                "VALIDATION_ERROR"
            )

    def _add_to_outbox(self, topic: str, event: SpecificationCreated | SpecificationUpdated | SpecificationDeleted):
        outbox_entry = OutboxORM(
            topic=topic,
            payload=event.model_dump(mode='json')
        )
        self.db.add(outbox_entry)

    def create_specification(self, spec_in: SpecificationCreate) -> SpecificationORM:
        # Check uniqueness
        if self.repository.get_by_name(spec_in.name):
            raise AppException(f"Specification with name '{spec_in.name}' already exists", "CONFLICT")

        # Validate characteristics from local cache
        self._validate_characteristics(spec_in.characteristic_ids)

        spec_orm = SpecificationORM(
            name=spec_in.name,
            characteristic_ids=spec_in.characteristic_ids
        )

        self.repository.create(spec_orm)
        self.db.flush() # Get ID

        # Write to outbox
        event = SpecificationCreated(payload=spec_orm.to_domain().model_dump(mode='json'))
        self._add_to_outbox("resource.specifications.events", event)

        self.db.commit()
        return spec_orm

    def get_specification(self, spec_id: uuid.UUID) -> SpecificationORM:
        spec = self.repository.get_by_id(spec_id)
        if not spec:
            raise AppException(f"Specification with ID {spec_id} not found", "NOT_FOUND")
        return spec

    def list_specifications(self, skip: int = 0, limit: int = 100) -> List[SpecificationORM]:
        return self.repository.list(skip, limit)

    def update_specification(self, spec_id: uuid.UUID, spec_in: SpecificationUpdate) -> SpecificationORM:
        spec_orm = self.get_specification(spec_id)

        # Check name uniqueness if changed
        if spec_in.name != spec_orm.name:
            if self.repository.get_by_name(spec_in.name):
                raise AppException("CONFLICT", f"Specification with name '{spec_in.name}' already exists")

        # Validate characteristics from local cache
        self._validate_characteristics(spec_in.characteristic_ids)

        spec_orm.name = spec_in.name
        spec_orm.characteristic_ids = spec_in.characteristic_ids

        self.db.flush()

        # Write to outbox
        event = SpecificationUpdated(payload=spec_orm.to_domain().model_dump(mode='json'))
        self._add_to_outbox("resource.specifications.events", event)

        self.db.commit()
        return spec_orm

    def delete_specification(self, spec_id: uuid.UUID):
        spec_orm = self.get_specification(spec_id)

        # In a real system, we'd check if any Offerings use this Spec here.
        # For now, we just delete.

        self.repository.delete(spec_orm)

        # Write to outbox
        event = SpecificationDeleted(payload={"id": str(spec_id)})
        self._add_to_outbox("resource.specifications.events", event)

        self.db.commit()

    def validate_specifications(self, spec_ids: List[uuid.UUID]):
        """
        Validates a list of specification IDs.
        Raises AppException if any ID is missing.
        """
        for spec_id in spec_ids:
            # get_specification already raises AppException if not found
            self.get_specification(spec_id)
