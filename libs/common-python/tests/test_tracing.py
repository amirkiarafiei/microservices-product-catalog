"""
Unit tests for the tracing module.
"""

from unittest.mock import MagicMock, patch

from common.tracing import (
    add_span_attributes,
    create_span,
    get_current_trace_context,
    mark_span_error,
    setup_tracing,
    span_name_db,
    span_name_http,
    span_name_messaging,
    span_name_saga,
)


class TestSpanNamingHelpers:
    """Tests for span naming convention helpers."""

    def test_span_name_http(self):
        """HTTP span names follow {method} {path} convention."""
        assert span_name_http("GET", "/api/v1/offerings") == "GET /api/v1/offerings"
        assert span_name_http("POST", "/api/v1/prices") == "POST /api/v1/prices"
        assert span_name_http("DELETE", "/health") == "DELETE /health"

    def test_span_name_db(self):
        """Database span names follow {operation} {table} convention."""
        assert span_name_db("SELECT", "offerings") == "SELECT offerings"
        assert span_name_db("INSERT", "characteristics") == "INSERT characteristics"
        assert span_name_db("UPDATE", "prices") == "UPDATE prices"

    def test_span_name_messaging(self):
        """Messaging span names follow {action} {topic/queue} convention."""
        assert span_name_messaging("PUBLISH", "offering.created") == "PUBLISH offering.created"
        assert span_name_messaging("CONSUME", "store-updates") == "CONSUME store-updates"

    def test_span_name_saga(self):
        """Saga span names follow SAGA {process} {task} convention."""
        assert (
            span_name_saga("offering-publication-saga", "lock-prices")
            == "SAGA offering-publication-saga lock-prices"
        )
        assert (
            span_name_saga("offering-publication-saga", "confirm-publication")
            == "SAGA offering-publication-saga confirm-publication"
        )


class TestTracingSetup:
    """Tests for tracing initialization."""

    def test_setup_tracing_disabled(self):
        """When tracing is disabled, returns a noop tracer."""
        tracer = setup_tracing(
            service_name="test-service",
            zipkin_endpoint="http://localhost:9411/api/v2/spans",
            enabled=False,
        )
        assert tracer is not None

    @patch("common.tracing.ZipkinExporter")
    @patch("common.tracing.TracerProvider")
    @patch("common.tracing.trace.set_tracer_provider")
    @patch("common.tracing.set_global_textmap")
    def test_setup_tracing_enabled(
        self, mock_textmap, mock_set_provider, mock_provider_class, mock_exporter_class
    ):
        """When tracing is enabled, configures provider with Zipkin exporter."""
        mock_provider = MagicMock()
        mock_provider_class.return_value = mock_provider

        tracer = setup_tracing(
            service_name="test-service",
            zipkin_endpoint="http://zipkin:9411/api/v2/spans",
            enabled=True,
        )

        # Verify Zipkin exporter was created
        mock_exporter_class.assert_called_once_with(
            endpoint="http://zipkin:9411/api/v2/spans"
        )

        # Verify provider was set
        mock_set_provider.assert_called_once()

        # Verify B3 propagator was set
        mock_textmap.assert_called_once()

        assert tracer is not None


class TestTraceContext:
    """Tests for trace context extraction."""

    def test_get_current_trace_context_no_span(self):
        """When no span is active, returns None values."""
        ctx = get_current_trace_context()
        # Without an active span, context may be invalid
        assert "trace_id" in ctx
        assert "span_id" in ctx
        assert "trace_flags" in ctx

    @patch("common.tracing.get_current_span")
    def test_get_current_trace_context_with_valid_span(self, mock_get_span):
        """When a span is active, returns formatted trace context."""
        mock_span = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.is_valid = True
        mock_ctx.trace_id = 0x1234567890ABCDEF1234567890ABCDEF
        mock_ctx.span_id = 0xFEDCBA0987654321
        mock_ctx.trace_flags = 1
        mock_span.get_span_context.return_value = mock_ctx
        mock_get_span.return_value = mock_span

        ctx = get_current_trace_context()

        assert ctx["trace_id"] == "1234567890abcdef1234567890abcdef"
        assert ctx["span_id"] == "fedcba0987654321"
        assert ctx["trace_flags"] == 1


class TestSpanOperations:
    """Tests for span creation and manipulation."""

    @patch("common.tracing.get_tracer")
    def test_create_span_context_manager(self, mock_get_tracer):
        """create_span returns a context manager for span creation."""
        mock_tracer = MagicMock()
        mock_span_cm = MagicMock()
        mock_tracer.start_as_current_span.return_value = mock_span_cm
        mock_get_tracer.return_value = mock_tracer

        result = create_span("test-span", attributes={"key": "value"})

        mock_tracer.start_as_current_span.assert_called_once()
        assert result == mock_span_cm

    @patch("common.tracing.get_current_span")
    def test_mark_span_error(self, mock_get_span):
        """mark_span_error sets error status on current span."""
        mock_span = MagicMock()
        mock_span.is_recording.return_value = True
        mock_get_span.return_value = mock_span

        error = ValueError("Test error")
        mark_span_error(error, message="Custom message")

        mock_span.set_status.assert_called_once()
        mock_span.record_exception.assert_called_once_with(error)

    @patch("common.tracing.get_current_span")
    def test_add_span_attributes(self, mock_get_span):
        """add_span_attributes adds key-value pairs to current span."""
        mock_span = MagicMock()
        mock_span.is_recording.return_value = True
        mock_get_span.return_value = mock_span

        add_span_attributes({"user_id": "123", "offering_id": "456"})

        assert mock_span.set_attribute.call_count == 2
        mock_span.set_attribute.assert_any_call("user_id", "123")
        mock_span.set_attribute.assert_any_call("offering_id", "456")

    @patch("common.tracing.get_current_span")
    def test_add_span_attributes_not_recording(self, mock_get_span):
        """add_span_attributes does nothing if span is not recording."""
        mock_span = MagicMock()
        mock_span.is_recording.return_value = False
        mock_get_span.return_value = mock_span

        add_span_attributes({"key": "value"})

        mock_span.set_attribute.assert_not_called()
