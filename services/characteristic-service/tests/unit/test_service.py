import pytest
from unittest.mock import MagicMock
import uuid
from src.application.service import CharacteristicService
from src.application.schemas import CharacteristicCreate, CharacteristicUpdate
from src.infrastructure.models import CharacteristicORM
from src.domain.models import UnitOfMeasure
from common.exceptions import ConflictError, NotFoundError

@pytest.fixture
def mock_db():
    return MagicMock()

@pytest.fixture
def char_service(mock_db):
    return CharacteristicService(mock_db)

def test_create_characteristic_success(char_service, mock_db):
    # Setup
    char_in = CharacteristicCreate(name="Speed", value="50", unit_of_measure=UnitOfMeasure.MBPS)
    char_service.repository.get_by_name = MagicMock(return_value=None)
    char_service.repository.create = MagicMock(side_effect=lambda x: x)
    
    # Execute
    result = char_service.create_characteristic(char_in)
    
    # Assert
    assert result.name == "Speed"
    assert result.value == "50"
    assert result.unit_of_measure == UnitOfMeasure.MBPS
    char_service.repository.get_by_name.assert_called_once_with("Speed")
    char_service.repository.create.assert_called_once()

def test_create_characteristic_conflict(char_service):
    # Setup
    char_in = CharacteristicCreate(name="Existing", value="10", unit_of_measure=UnitOfMeasure.GB)
    char_service.repository.get_by_name = MagicMock(return_value=MagicMock())
    
    # Execute & Assert
    with pytest.raises(ConflictError):
        char_service.create_characteristic(char_in)

def test_get_characteristic_success(char_service):
    # Setup
    char_id = uuid.uuid4()
    mock_char = MagicMock(spec=CharacteristicORM)
    char_service.repository.get_by_id = MagicMock(return_value=mock_char)
    
    # Execute
    result = char_service.get_characteristic(char_id)
    
    # Assert
    assert result == mock_char
    char_service.repository.get_by_id.assert_called_once_with(char_id)

def test_get_characteristic_not_found(char_service):
    # Setup
    char_id = uuid.uuid4()
    char_service.repository.get_by_id = MagicMock(return_value=None)
    
    # Execute & Assert
    with pytest.raises(NotFoundError):
        char_service.get_characteristic(char_id)

def test_update_characteristic_success(char_service):
    # Setup
    char_id = uuid.uuid4()
    mock_char = CharacteristicORM(id=char_id, name="Old", value="1", unit_of_measure=UnitOfMeasure.GB)
    char_service.repository.get_by_id = MagicMock(return_value=mock_char)
    char_service.repository.get_by_name = MagicMock(return_value=None)
    char_service.repository.update = MagicMock(side_effect=lambda x: x)
    
    char_update = CharacteristicUpdate(name="New", value="2")
    
    # Execute
    result = char_service.update_characteristic(char_id, char_update)
    
    # Assert
    assert result.name == "New"
    assert result.value == "2"
    assert result.unit_of_measure == UnitOfMeasure.GB
    char_service.repository.update.assert_called_once_with(mock_char)

def test_delete_characteristic_success(char_service):
    # Setup
    char_id = uuid.uuid4()
    mock_char = MagicMock(spec=CharacteristicORM)
    char_service.repository.get_by_id = MagicMock(return_value=mock_char)
    char_service.repository.delete = MagicMock()
    
    # Execute
    char_service.delete_characteristic(char_id)
    
    # Assert
    char_service.repository.delete.assert_called_once_with(mock_char)
