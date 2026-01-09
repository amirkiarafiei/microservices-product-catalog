import pytest
import uuid
from datetime import datetime, timezone
from src.domain.models import Characteristic, UnitOfMeasure

def test_characteristic_creation():
    char_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    char = Characteristic(
        id=char_id,
        name="Internet Speed",
        value="100",
        unit_of_measure=UnitOfMeasure.MBPS,
        created_at=now,
        updated_at=now
    )
    
    assert char.id == char_id
    assert char.name == "Internet Speed"
    assert char.value == "100"
    assert char.unit_of_measure == UnitOfMeasure.MBPS
