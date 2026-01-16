import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from ..infrastructure.models import SpecificationORM

class SpecificationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, spec_orm: SpecificationORM) -> SpecificationORM:
        self.db.add(spec_orm)
        # We don't commit here to allow service layer to manage transaction with outbox
        return spec_orm

    def get_by_id(self, spec_id: uuid.UUID) -> Optional[SpecificationORM]:
        return self.db.query(SpecificationORM).filter(SpecificationORM.id == spec_id).first()

    def get_by_name(self, name: str) -> Optional[SpecificationORM]:
        return self.db.query(SpecificationORM).filter(SpecificationORM.name == name).first()

    def list(self, skip: int = 0, limit: int = 100) -> List[SpecificationORM]:
        return self.db.query(SpecificationORM).offset(skip).limit(limit).all()

    def delete(self, spec_orm: SpecificationORM):
        self.db.delete(spec_orm)
