import uuid
from unittest.mock import MagicMock

import pytest
from common.exceptions import AppException
from src.application.schemas import SpecificationCreate
from src.application.service import SpecificationService


def _db_with_cached_ids(existing_ids: list[uuid.UUID]) -> MagicMock:
    """
    Builds a MagicMock Session whose query(CachedCharacteristicORM.id).filter(...).all()
    returns rows with .id for the provided IDs.
    """
    db = MagicMock()
    query = db.query.return_value
    filt = query.filter.return_value
    filt.all.return_value = [MagicMock(id=i) for i in existing_ids]
    return db


def test_create_specification_no_characteristics():
    db = _db_with_cached_ids([])
    service = SpecificationService(db)
    service.repository = MagicMock()
    service.repository.get_by_name.return_value = None

    spec_in = SpecificationCreate(name="Test Spec", characteristic_ids=[])
    with pytest.raises(AppException) as exc:
        service.create_specification(spec_in)
    assert exc.value.code == "VALIDATION_ERROR"


def test_create_specification_missing_characteristics():
    missing_id = uuid.uuid4()
    db = _db_with_cached_ids([])
    service = SpecificationService(db)
    service.repository = MagicMock()
    service.repository.get_by_name.return_value = None

    spec_in = SpecificationCreate(name="Test Spec", characteristic_ids=[missing_id])
    with pytest.raises(AppException) as exc:
        service.create_specification(spec_in)
    assert exc.value.code == "VALIDATION_ERROR"
    assert str(missing_id) in exc.value.message


def test_create_specification_success():
    char_id = uuid.uuid4()
    db = _db_with_cached_ids([char_id])
    db.flush = MagicMock()
    db.commit = MagicMock()
    db.add = MagicMock()

    service = SpecificationService(db)
    service.repository = MagicMock()
    service.repository.get_by_name.return_value = None
    service.repository.create = MagicMock()

    spec_in = SpecificationCreate(name="Valid Spec", characteristic_ids=[char_id])
    spec = service.create_specification(spec_in)
    assert spec.name == "Valid Spec"
    assert spec.characteristic_ids == [char_id]
    db.commit.assert_called()