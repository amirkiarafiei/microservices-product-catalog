from typing import List, Optional
import uuid
from sqlalchemy.orm import Session
from ..domain.models import Characteristic
from ..infrastructure.models import CharacteristicORM
from ..infrastructure.repository import CharacteristicRepository
from .schemas import CharacteristicCreate, CharacteristicUpdate
from common.exceptions import ConflictError, NotFoundError


class CharacteristicService:
    def __init__(self, db: Session):
        self.repository = CharacteristicRepository(db)

    def create_characteristic(self, char_in: CharacteristicCreate) -> CharacteristicORM:
        if self.repository.get_by_name(char_in.name):
            raise ConflictError(f"Characteristic with name '{char_in.name}' already exists")
        
        char_orm = CharacteristicORM(
            name=char_in.name,
            value=char_in.value,
            unit_of_measure=char_in.unit_of_measure
        )
        return self.repository.create(char_orm)

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
            
        return self.repository.update(char_orm)

    def delete_characteristic(self, char_id: uuid.UUID) -> None:
        char_orm = self.get_characteristic(char_id)
        # TODO: Check if referenced by specifications before deleting
        # For now, as per Phase 5 goal, no outbox or cross-service checks yet.
        # But SRS mentions rejecting delete if referenced. 
        # Since we don't have specifications yet, this is okay for now.
        self.repository.delete(char_orm)
