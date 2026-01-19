import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from .models import CharacteristicORM


class CharacteristicRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, char_orm: CharacteristicORM) -> CharacteristicORM:
        self.db.add(char_orm)
        self.db.commit()
        self.db.refresh(char_orm)
        return char_orm

    def get_by_id(self, char_id: uuid.UUID) -> Optional[CharacteristicORM]:
        return self.db.query(CharacteristicORM).filter(CharacteristicORM.id == char_id).first()

    def get_by_name(self, name: str) -> Optional[CharacteristicORM]:
        return self.db.query(CharacteristicORM).filter(CharacteristicORM.name == name).first()

    def list(self, skip: int = 0, limit: int = 100) -> List[CharacteristicORM]:
        return self.db.query(CharacteristicORM).offset(skip).limit(limit).all()

    def update(self, char_orm: CharacteristicORM) -> CharacteristicORM:
        self.db.commit()
        self.db.refresh(char_orm)
        return char_orm

    def delete(self, char_orm: CharacteristicORM) -> None:
        self.db.delete(char_orm)
        self.db.commit()
