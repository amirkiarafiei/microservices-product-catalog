import pytest
import uuid
from unittest.mock import MagicMock
from src.application.service import SpecificationService
from src.application.schemas import SpecificationCreate, SpecificationUpdate
from src.infrastructure.models import CachedCharacteristicORM
from common.exceptions import AppException

def test_create_specification_no_characteristics(db_session):
    service = SpecificationService(db_session)
    spec_in = SpecificationCreate(name="Test Spec", characteristic_ids=[])
    
    with pytest.raises(AppException) as exc:
        service.create_specification(spec_in)
    assert exc.value.code == "VALIDATION_ERROR"

def test_create_specification_missing_characteristics(db_session):
    service = SpecificationService(db_session)
    missing_id = uuid.uuid4()
    spec_in = SpecificationCreate(name="Test Spec", characteristic_ids=[missing_id])
    
    with pytest.raises(AppException) as exc:
        service.create_specification(spec_in)
    assert exc.value.code == "VALIDATION_ERROR"
    assert str(missing_id) in exc.value.message

def test_create_specification_success(db_session):
    # Setup cache
    char_id = uuid.uuid4()
    db_session.add(CachedCharacteristicORM(id=char_id, name="Test Char"))
    db_session.commit()
    
    service = SpecificationService(db_session)
    spec_in = SpecificationCreate(name="Valid Spec", characteristic_ids=[char_id])
    
    spec = service.create_specification(spec_in)
    assert spec.name == "Valid Spec"
    assert spec.characteristic_ids == [char_id]
