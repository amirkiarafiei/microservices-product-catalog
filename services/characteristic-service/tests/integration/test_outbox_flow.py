import asyncio
import json
import uuid

import aio_pika
import pytest
from characteristic.application.schemas import CharacteristicCreate
from characteristic.config import settings
from characteristic.domain.models import UnitOfMeasure
from characteristic.infrastructure.models import OutboxORM


@pytest.mark.asyncio
async def test_outbox_flow_e2e(db_session, client):
    """
    Test the full outbox flow:
    1. Create a characteristic via service
    2. Verify it exists in DB
    3. Verify an outbox entry is created (PENDING)
    4. Since the background listener is running in the 'app' used by 'client',
       we should eventually see the status change to 'SENT'.
    """
    char_in = CharacteristicCreate(
        name=f"Outbox Test {uuid.uuid4()}",
        value="100",
        unit_of_measure=UnitOfMeasure.MBPS
    )

    # 1. Create via API
    response = client.post(
        "/api/v1/characteristics",
        json=char_in.model_dump(mode='json')
    )
    assert response.status_code == 201
    created_id = response.json()["id"]

    # 2. Verify outbox entry exists and is PENDING (or already SENT if listener is fast)
    # We query all and filter in Python to avoid SQLAlchemy JSON vs JSONB vs cast issues in tests
    all_outbox = db_session.query(OutboxORM).all()
    outbox_entry = next((r for r in all_outbox if str(r.payload['payload']['id']) == str(created_id)), None)

    assert outbox_entry is not None
    assert outbox_entry.topic == "resource.characteristics.events"

    # 3. Wait for the background listener to process it
    # We poll the DB for a few seconds
    max_retries = 20 # Increased retries
    processed = False
    for _ in range(max_retries):
        db_session.refresh(outbox_entry)
        if outbox_entry.status == "SENT":
            processed = True
            break
        await asyncio.sleep(0.5)

    assert processed, f"Outbox entry status was {outbox_entry.status}, expected SENT"
    assert outbox_entry.processed_at is not None

@pytest.mark.asyncio
async def test_rabbitmq_message_received(db_session, client):
    """
    Verify that the message actually reaches RabbitMQ.
    """
    # 1. Setup RabbitMQ consumer
    connection = await aio_pika.connect_robust(settings.RABBITMQ_URL)
    channel = await connection.channel()
    exchange = await channel.declare_exchange(
        "catalog.events", aio_pika.ExchangeType.TOPIC, durable=True
    )
    queue = await channel.declare_queue(exclusive=True)
    await queue.bind(exchange, routing_key="resource.characteristics.events")

    # 2. Create characteristic via API
    unique_name = f"MQ Test {uuid.uuid4()}"
    char_in = CharacteristicCreate(
        name=unique_name,
        value="50",
        unit_of_measure=UnitOfMeasure.GB
    )
    response = client.post(
        "/api/v1/characteristics",
        json=char_in.model_dump(mode='json')
    )
    assert response.status_code == 201

    # 3. Wait for message
    try:
        async with asyncio.timeout(10): # Add 10s timeout
            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        body = json.loads(message.body.decode())
                        if body["payload"]["name"] == unique_name:
                            assert body["event_type"] == "CharacteristicCreated"
                            return # Success
    except asyncio.TimeoutError:
        pytest.fail("Timed out waiting for RabbitMQ message")
    finally:
        await connection.close()
