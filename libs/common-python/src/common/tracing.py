"""
OpenTelemetry Tracing Configuration Module.

Provides distributed tracing with B3 propagation for cross-service trace context.
Supports auto-instrumentation for FastAPI, HTTPX, SQLAlchemy, and aio-pika.
"""

import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.zipkin.json import ZipkinExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import SpanKind, Status, StatusCode, get_current_span

logger = logging.getLogger(__name__)

# Global tracer instance
_tracer: Optional[trace.Tracer] = None


def setup_tracing(
    service_name: str,
    zipkin_endpoint: str = "http://localhost:9411/api/v2/spans",
    enabled: bool = True,
) -> trace.Tracer:
    """
    Initialize OpenTelemetry tracing with Zipkin exporter and B3 propagation.

    Args:
        service_name: Name of the service for span attribution.
        zipkin_endpoint: URL of the Zipkin collector endpoint.
        enabled: Whether tracing is enabled (useful for tests).

    Returns:
        Configured Tracer instance.
    """
    global _tracer

    if not enabled:
        logger.info("Tracing is disabled")
        _tracer = trace.get_tracer(service_name)
        return _tracer

    # Create resource with service name
    resource = Resource.create({SERVICE_NAME: service_name})

    # Create tracer provider
    provider = TracerProvider(resource=resource)

    # Configure Zipkin exporter
    zipkin_exporter = ZipkinExporter(endpoint=zipkin_endpoint)

    # Add span processor with batching for performance
    provider.add_span_processor(BatchSpanProcessor(zipkin_exporter))

    # Set as global tracer provider
    trace.set_tracer_provider(provider)

    # Set B3 propagator for trace context propagation
    set_global_textmap(B3MultiFormat())

    _tracer = trace.get_tracer(service_name)
    logger.info(f"Tracing initialized for {service_name}, exporting to {zipkin_endpoint}")

    return _tracer


def get_tracer() -> trace.Tracer:
    """Get the global tracer instance."""
    global _tracer
    if _tracer is None:
        _tracer = trace.get_tracer("uninitialized")
    return _tracer


def instrument_fastapi(app, excluded_urls: Optional[str] = None):
    """
    Instrument a FastAPI application for automatic tracing.

    Args:
        app: FastAPI application instance.
        excluded_urls: Comma-separated list of URL patterns to exclude (e.g., "/health,/metrics").
    """
    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls=excluded_urls or "health",
        server_request_hook=_server_request_hook,
        client_request_hook=_client_request_hook,
        client_response_hook=_client_response_hook,
    )
    logger.info("FastAPI instrumentation enabled")


def instrument_httpx():
    """
    Instrument HTTPX client for automatic tracing of outgoing HTTP requests.
    """
    HTTPXClientInstrumentor().instrument()
    logger.info("HTTPX instrumentation enabled")


def instrument_sqlalchemy(engine):
    """
    Instrument SQLAlchemy engine for automatic database tracing.

    Args:
        engine: SQLAlchemy engine instance.
    """
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

        SQLAlchemyInstrumentor().instrument(engine=engine, enable_commenter=True)
        logger.info("SQLAlchemy instrumentation enabled")
    except Exception as e:
        logger.warning(f"Failed to instrument SQLAlchemy: {e}")


def instrument_aio_pika():
    """
    Instrument aio-pika for automatic RabbitMQ tracing.
    """
    try:
        from opentelemetry.instrumentation.aio_pika import AioPikaInstrumentor

        AioPikaInstrumentor().instrument()
        logger.info("aio-pika instrumentation enabled")
    except Exception as e:
        logger.warning(f"Failed to instrument aio-pika: {e}")


def _server_request_hook(span, scope):
    """
    Hook called when a server request span is created.
    Customizes span name to follow convention: {method} {path}
    """
    if span and span.is_recording():
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "/")
        span.update_name(f"{method} {path}")


def _client_request_hook(span, request):
    """Hook called when a client request span is created."""
    pass


def _client_response_hook(span, request, response):
    """Hook called when a client response is received."""
    pass


def get_current_trace_context() -> dict:
    """
    Extract current trace context for logging or propagation.

    Returns:
        Dictionary with trace_id, span_id, and trace_flags.
    """
    span = get_current_span()
    ctx = span.get_span_context()

    if ctx.is_valid:
        return {
            "trace_id": format(ctx.trace_id, "032x"),
            "span_id": format(ctx.span_id, "016x"),
            "trace_flags": ctx.trace_flags,
        }
    return {"trace_id": None, "span_id": None, "trace_flags": None}


def create_span(
    name: str,
    kind: SpanKind = SpanKind.INTERNAL,
    attributes: Optional[dict] = None,
):
    """
    Context manager to create a new span.

    Args:
        name: Name of the span (e.g., "SAGA offering-publication lock-prices").
        kind: Type of span (INTERNAL, CLIENT, SERVER, PRODUCER, CONSUMER).
        attributes: Optional attributes to attach to the span.

    Usage:
        with create_span("process_data", attributes={"item_id": "123"}):
            do_work()
    """
    tracer = get_tracer()
    return tracer.start_as_current_span(name, kind=kind, attributes=attributes or {})


def mark_span_error(error: Exception, message: Optional[str] = None):
    """
    Mark the current span as errored.

    Args:
        error: The exception that occurred.
        message: Optional error message.
    """
    span = get_current_span()
    if span and span.is_recording():
        span.set_status(Status(StatusCode.ERROR, message or str(error)))
        span.record_exception(error)


def add_span_attributes(attributes: dict):
    """
    Add attributes to the current span.

    Args:
        attributes: Dictionary of key-value pairs to add.
    """
    span = get_current_span()
    if span and span.is_recording():
        for key, value in attributes.items():
            span.set_attribute(key, value)


# Span naming helpers following the convention
def span_name_http(method: str, path: str) -> str:
    """Generate span name for HTTP operations: {method} {path}"""
    return f"{method} {path}"


def span_name_db(operation: str, table: str) -> str:
    """Generate span name for database operations: {operation} {table}"""
    return f"{operation} {table}"


def span_name_messaging(action: str, topic_or_queue: str) -> str:
    """Generate span name for messaging: PUBLISH {topic} or CONSUME {queue}"""
    return f"{action} {topic_or_queue}"


def span_name_saga(process_name: str, task_name: str) -> str:
    """Generate span name for saga tasks: SAGA {process_name} {task_name}"""
    return f"SAGA {process_name} {task_name}"
