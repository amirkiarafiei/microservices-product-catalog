from unittest.mock import AsyncMock, patch

import pytest
from common.messaging import RabbitMQPublisher
from common.schemas import Event


@pytest.mark.asyncio
async def test_publisher_connect():
    publisher = RabbitMQPublisher("amqp://guest:guest@localhost:5672")

    with patch("aio_pika.connect_robust", new_callable=AsyncMock) as mock_connect:
        mock_connection = AsyncMock()
        mock_connect.return_value = mock_connection
        mock_channel = AsyncMock()
        mock_connection.channel.return_value = mock_channel

        await publisher.connect()

        mock_connect.assert_called_once_with("amqp://guest:guest@localhost:5672")
        mock_connection.channel.assert_called_once()

@pytest.mark.asyncio
async def test_publisher_publish():
    publisher = RabbitMQPublisher("amqp://guest:guest@localhost:5672")
    event = Event(event_type="TestEvent", payload={"foo": "bar"})

    with patch("aio_pika.connect_robust", new_callable=AsyncMock) as mock_connect:
        mock_connection = AsyncMock()
        mock_connect.return_value = mock_connection
        mock_channel = AsyncMock()
        mock_connection.channel.return_value = mock_channel
        mock_exchange = AsyncMock()
        mock_channel.declare_exchange.return_value = mock_exchange

        await publisher.publish("test.topic", event)

        mock_exchange.publish.assert_called_once()
        args, kwargs = mock_exchange.publish.call_args
        message = args[0]
        assert b"TestEvent" in message.body
        assert kwargs["routing_key"] == "test.topic"
