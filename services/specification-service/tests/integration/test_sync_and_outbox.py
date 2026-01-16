import pytest
import asyncio
import uuid
from src.application.consumers import CharacteristicConsumer
from src.infrastructure.models import CachedCharacteristicORM, OutboxORM, SpecificationORM
from src.application.service import SpecificationService
from src.application.schemas import SpecificationCreate

@pytest.mark.asyncio
async def test_characteristic_sync_consumer(db_session):
    """Tests that the consumer correctly syncs events to the local cache."""
    consumer = CharacteristicConsumer()
    char_id = uuid.uuid4()
    
    # 1. Test Created
    event = {
        "event_type": "CharacteristicCreated",
        "payload": {"id": str(char_id), "name": "Sync Test"}
    }
    await consumer._handle_event(event, {})
    
    cached = db_session.query(CachedCharacteristicORM).filter_by(id=char_id).first()
    assert cached is not None
    assert cached.name == "Sync Test"
    
    # 2. Test Updated
    event["event_type"] = "CharacteristicUpdated"
    event["payload"]["name"] = "Updated Name"
    await consumer._handle_event(event, {})
    
    db_session.refresh(cached)
    assert cached.name == "Updated Name"
    
    # 3. Test Deleted
    event["event_type"] = "CharacteristicDeleted"
    await consumer._handle_event(event, {})
    
    cached = db_session.query(CachedCharacteristicORM).filter_by(id=char_id).first()
    assert cached is None

@pytest.mark.asyncio
async def test_specification_outbox_flow(db_session):
    """Tests that creating a spec writes to the outbox."""
    # Setup cache
    char_id = uuid.uuid4()
    db_session.add(CachedCharacteristicORM(id=char_id, name="Test Char"))
    db_session.commit()
    
    service = SpecificationService(db_session)
    spec_in = SpecificationCreate(name="Outbox Spec", characteristic_ids=[char_id])
    
    spec = service.create_specification(spec_in)
    
    # Verify outbox
    outbox_entry = db_session.query(OutboxORM).first()
    assert outbox_entry is not None
    assert outbox_entry.topic == "resource.specifications.events"
    assert outbox_entry.payload["payload"]["id"] == str(spec.id)
    assert outbox_entry.status == "PENDING"
