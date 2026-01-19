"""
Structured JSON Logging with OpenTelemetry Trace Context.

Configures logging to output JSON to stdout with automatic injection of
trace_id, span_id, and correlation_id for distributed tracing correlation.
"""

import logging
import sys
from datetime import datetime, timezone

from pythonjsonlogger import json


def _get_trace_context():
    """
    Extract trace context from OpenTelemetry.

    Returns tuple of (trace_id, span_id) or (None, None) if not available.
    """
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx.is_valid:
            return format(ctx.trace_id, "032x"), format(ctx.span_id, "016x")
    except Exception:
        pass
    return None, None


class CustomJsonFormatter(json.JsonFormatter):
    """
    JSON formatter that enriches log records with trace context.
    """

    def add_fields(self, log_record, record, message_dict):
        super().add_fields(log_record, record, message_dict)

        # Timestamp in ISO format
        if not log_record.get("timestamp"):
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            log_record["timestamp"] = now

        # Normalize level to uppercase
        if log_record.get("level"):
            log_record["level"] = log_record["level"].upper()
        else:
            log_record["level"] = record.levelname

        # Service name
        log_record.setdefault("service_name", getattr(record, "service_name", "unknown"))

        # Correlation ID (from request context)
        log_record.setdefault("correlation_id", getattr(record, "correlation_id", None))

        # OpenTelemetry trace context - auto-inject from current span
        trace_id, span_id = _get_trace_context()

        # Prefer explicit trace_id from record, fallback to OTel context
        if not log_record.get("trace_id"):
            explicit_trace_id = getattr(record, "trace_id", None)
            log_record["trace_id"] = explicit_trace_id or trace_id

        # Add span_id from OTel context
        if not log_record.get("span_id"):
            explicit_span_id = getattr(record, "span_id", None)
            log_record["span_id"] = explicit_span_id or span_id


class TraceContextFilter(logging.Filter):
    """
    Logging filter that automatically adds trace context to all log records.
    """

    def filter(self, record):
        trace_id, span_id = _get_trace_context()
        if not hasattr(record, "trace_id") or record.trace_id is None:
            record.trace_id = trace_id
        if not hasattr(record, "span_id") or record.span_id is None:
            record.span_id = span_id
        return True


def setup_logging(service_name: str, log_level: str = "INFO"):
    """
    Configures structured JSON logging for the service.

    Features:
    - JSON output to stdout for ELK ingestion
    - Automatic trace_id and span_id injection from OpenTelemetry
    - Service name in every log record
    - Correlation ID propagation

    Args:
        service_name: Name of the service (e.g., "offering-service").
        log_level: Logging level (default: "INFO").

    Returns:
        Configured root logger.
    """
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # Clear existing handlers
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)

    # Create stdout handler
    handler = logging.StreamHandler(sys.stdout)

    # Format string (fields picked up by formatter)
    format_str = "%(timestamp)s %(level)s %(name)s %(message)s"

    formatter = CustomJsonFormatter(format_str)
    handler.setFormatter(formatter)

    # Add trace context filter
    handler.addFilter(TraceContextFilter())

    logger.addHandler(handler)

    # Inject service_name into every LogRecord via factory
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.service_name = service_name
        return record

    logging.setLogRecordFactory(record_factory)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a named logger.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Logger instance.
    """
    return logging.getLogger(name)
