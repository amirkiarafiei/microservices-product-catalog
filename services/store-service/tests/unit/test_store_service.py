from unittest.mock import AsyncMock, MagicMock

import pytest
from store.application.service import StoreService


@pytest.mark.asyncio
async def test_idempotency_check():
    mongodb = MagicMock()
    mongodb.events.find_one = AsyncMock(return_value=None)
    es = MagicMock()

    service = StoreService(mongodb, es)

    processed = await service.is_event_processed("evt-123")
    assert processed is False
    mongodb.events.find_one.assert_called_once_with({"event_id": "evt-123"})

@pytest.mark.asyncio
async def test_mark_event_processed():
    mongodb = MagicMock()
    mongodb.events.insert_one = AsyncMock()
    es = MagicMock()

    service = StoreService(mongodb, es)

    await service.mark_event_processed("evt-123")
    mongodb.events.insert_one.assert_called_once_with({"event_id": "evt-123"})

@pytest.mark.asyncio
async def test_retire_offering():
    mongodb = MagicMock()
    mongodb.offerings.delete_one = AsyncMock()
    es = MagicMock()
    es.delete_offering = AsyncMock()

    service = StoreService(mongodb, es)

    await service.retire_offering("off-123")
    mongodb.offerings.delete_one.assert_called_once_with({"id": "off-123"})
    es.delete_offering.assert_called_once_with("off-123")
