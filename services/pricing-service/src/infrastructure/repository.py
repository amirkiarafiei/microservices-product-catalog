import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from .models import PriceORM


class PriceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, price_orm: PriceORM) -> PriceORM:
        self.db.add(price_orm)
        self.db.commit()
        self.db.refresh(price_orm)
        return price_orm

    def get_by_id(self, price_id: uuid.UUID) -> Optional[PriceORM]:
        return self.db.query(PriceORM).filter(PriceORM.id == price_id).first()

    def get_by_name(self, name: str) -> Optional[PriceORM]:
        return self.db.query(PriceORM).filter(PriceORM.name == name).first()

    def list(self, skip: int = 0, limit: int = 100) -> List[PriceORM]:
        return self.db.query(PriceORM).offset(skip).limit(limit).all()

    def update(self, price_orm: PriceORM) -> PriceORM:
        self.db.commit()
        self.db.refresh(price_orm)
        return price_orm

    def delete(self, price_orm: PriceORM):
        self.db.delete(price_orm)
        self.db.commit()
