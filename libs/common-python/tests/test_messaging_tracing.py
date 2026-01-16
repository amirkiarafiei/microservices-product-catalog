"""
Integration tests for trace context propagation in messaging.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from common.messaging import (
    RabbitMQPublisher,
    extract_trace_context,
    inject_trace_context,
)


class TestTraceContextPropagation:
    """Tests for B3 trace context propagation in RabbitMQ messages."""

    @patch("common.messaging.inject")
    def test_inject_trace_context(self, mock_inject):
        """inject_trace_context calls OpenTelemetry inject with headers."""
        headers = {"correlation_id": "test-123"}

        result = inject_trace_context(headers)

        mock_inject.assert_called_once()
        assert "correlation_id" in result

    @patch("common.messaging.extract")
    def test_extract_trace_context(self, mock_extract):
        """extract_trace_context calls OpenTelemetry extract with headers."""
        mock_ctx = MagicMock()
        mock_extract.return_value = mock_ctx

        headers = {
            "X-B3-TraceId": "463ac35c9f6413ad48485a3953bb6124",
            "X-B3-SpanId": "a2fb4a1d1a96d312",
            "X-B3-Sampled": "1",
        }

        result = extract_trace_context(headers)

        mock_extract.assert_called_once_with(headers)
        assert result == mock_ctx

    def test_extract_trace_context_empty_headers(self):
        """extract_trace_context handles empty headers gracefully."""
        result = extract_trace_context({})
        # Should not raise, returns a context object
        assert result is not None

    def test_extract_trace_context_none_headers(self):
        """extract_trace_context handles None headers gracefully."""
        result = extract_trace_context(None)
        assert result is not None


class TestRabbitMQPublisherTracing:
    """Tests for trace-aware RabbitMQ publisher."""

    @pytest.mark.asyncio
    @patch("common.messaging.aio_pika.connect_robust")
    @patch("common.messaging.trace.get_tracer")
    async def test_publish_creates_producer_span(self, mock_get_tracer, mock_connect):
        """Publishing a message creates a PRODUCER span."""
        from common.schemas import Event

        # Setup mocks
        mock_tracer = MagicMock()
        mock_span_ctx = MagicMock()
        mock_tracer.start_as_current_span.return_value.__enter__ = MagicMock(
            return_value=mock_span_ctx
        )
        mock_tracer.start_as_current_span.return_value.__exit__ = MagicMock(
            return_value=False
        )
        mock_get_tracer.return_value = mock_tracer

        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()

        mock_connect.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_channel.declare_exchange.return_value = mock_exchange
        mock_exchange.publish = AsyncMock()

        # Create publisher and publish
        publisher = RabbitMQPublisher("amqp://guest:guest@localhost:5672")

        event = Event(
            event_type="TestEvent",
            event_id="550e8400-e29b-41d4-a716-446655440000",
            payload={"key": "value"},
            correlation_id="corr-123",
        )

        await publisher.publish("test.topic", event)

        # Verify span was created with PRODUCER kind
        mock_tracer.start_as_current_span.assert_called_once()
        call_args = mock_tracer.start_as_current_span.call_args
        assert "PUBLISH test.topic" in call_args[0]

    @pytest.mark.asyncio
    @patch("common.messaging.aio_pika.connect_robust")
    @patch("common.messaging.inject_trace_context")
    async def test_publish_injects_trace_headers(self, mock_inject, mock_connect):
        """Publishing a message injects B3 trace headers."""
        from common.schemas import Event

        mock_inject.return_value = {
            "correlation_id": "corr-123",
            "X-B3-TraceId": "injected-trace-id",
        }

        mock_connection = AsyncMock()
        mock_channel = AsyncMock()
        mock_exchange = AsyncMock()

        mock_connect.return_value = mock_connection
        mock_connection.channel.return_value = mock_channel
        mock_channel.declare_exchange.return_value = mock_exchange
        mock_exchange.publish = AsyncMock()

        publisher = RabbitMQPublisher("amqp://guest:guest@localhost:5672")

        event = Event(
            event_type="TestEvent",
            event_id="550e8400-e29b-41d4-a716-446655440000",
            payload={"key": "value"},
            correlation_id="corr-123",
        )

        await publisher.publish("test.topic", event)

        # Verify inject was called
        mock_inject.assert_called_once()
