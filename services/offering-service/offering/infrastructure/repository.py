import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from .models import ProductOfferingORM


class OfferingRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, offering_orm: ProductOfferingORM) -> ProductOfferingORM:
        self.db.add(offering_orm)
        self.db.commit()
        self.db.refresh(offering_orm)
        return offering_orm

    def get_by_id(self, offering_id: uuid.UUID) -> Optional[ProductOfferingORM]:
        return self.db.query(ProductOfferingORM).filter(ProductOfferingORM.id == offering_id).first()

    def list(self, skip: int = 0, limit: int = 100) -> List[ProductOfferingORM]:
        return self.db.query(ProductOfferingORM).offset(skip).limit(limit).all()

    def update(self, offering_orm: ProductOfferingORM) -> ProductOfferingORM:
        self.db.commit()
        self.db.refresh(offering_orm)
        return offering_orm

    def delete(self, offering_orm: ProductOfferingORM):
        self.db.delete(offering_orm)
        self.db.commit()
