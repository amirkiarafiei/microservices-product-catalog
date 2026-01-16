from typing import List, Optional
import uuid
from sqlalchemy.orm import Session
from ..domain.models import Characteristic
from ..infrastructure.models import CharacteristicORM, OutboxORM
from ..infrastructure.repository import CharacteristicRepository
from .schemas import CharacteristicCreate, CharacteristicUpdate
from .events import CharacteristicCreated, CharacteristicUpdated, CharacteristicDeleted
from common.exceptions import ConflictError, NotFoundError


class CharacteristicService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = CharacteristicRepository(db)

    def _add_to_outbox(self, topic: str, event: CharacteristicCreated | CharacteristicUpdated | CharacteristicDeleted):
        outbox_entry = OutboxORM(
            topic=topic,
            payload=event.model_dump(mode='json')
        )
        self.db.add(outbox_entry)

    def create_characteristic(self, char_in: CharacteristicCreate) -> CharacteristicORM:
        if self.repository.get_by_name(char_in.name):
            raise ConflictError(f"Characteristic with name '{char_in.name}' already exists")
        
        char_orm = CharacteristicORM(
            name=char_in.name,
            value=char_in.value,
            unit_of_measure=char_in.unit_of_measure
        )
        created = self.repository.create(char_orm)
        
        # Add to outbox
        event = CharacteristicCreated(payload={
            "id": str(created.id),
            "name": created.name,
            "value": created.value,
            "unit_of_measure": created.unit_of_measure
        })
        self._add_to_outbox("resource.characteristics.events", event)
        self.db.commit() # Repository.create already does a commit, but we need another one for outbox or we should have done it in one transaction.
        # Actually Repository.create commits. I should probably change Repository to not commit if I want atomicity here.
        
        return created

    def get_characteristic(self, char_id: uuid.UUID) -> CharacteristicORM:
        char = self.repository.get_by_id(char_id)
        if not char:
            raise NotFoundError(f"Characteristic with id '{char_id}' not found")
        return char

    def list_characteristics(self, skip: int = 0, limit: int = 100) -> List[CharacteristicORM]:
        return self.repository.list(skip=skip, limit=limit)

    def update_characteristic(self, char_id: uuid.UUID, char_in: CharacteristicUpdate) -> CharacteristicORM:
        char_orm = self.get_characteristic(char_id)
        
        if char_in.name and char_in.name != char_orm.name:
            if self.repository.get_by_name(char_in.name):
                raise ConflictError(f"Characteristic with name '{char_in.name}' already exists")
            char_orm.name = char_in.name
            
        if char_in.value is not None:
            char_orm.value = char_in.value
            
        if char_in.unit_of_measure is not None:
            char_orm.unit_of_measure = char_in.unit_of_measure
            
        updated = self.repository.update(char_orm)
        
        # Add to outbox
        event = CharacteristicUpdated(payload={
            "id": str(updated.id),
            "name": updated.name,
            "value": updated.value,
            "unit_of_measure": updated.unit_of_measure
        })
        self._add_to_outbox("resource.characteristics.events", event)
        self.db.commit()
        
        return updated

    def delete_characteristic(self, char_id: uuid.UUID) -> None:
        char_orm = self.get_characteristic(char_id)
        # TODO: Check if referenced by specifications before deleting
        
        # Save info for event before deleting
        char_id_str = str(char_orm.id)
        
        self.repository.delete(char_orm)
        
        # Add to outbox
        event = CharacteristicDeleted(payload={
            "id": char_id_str
        })
        self._add_to_outbox("resource.characteristics.events", event)
        self.db.commit()