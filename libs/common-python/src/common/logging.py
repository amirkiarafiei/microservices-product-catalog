import logging
import sys
from datetime import datetime, timezone

from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        if not log_record.get('timestamp'):
            now = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.%fZ')
            log_record['timestamp'] = now
        if log_record.get('level'):
            log_record['level'] = log_record['level'].upper()
        else:
            log_record['level'] = record.levelname

        # Ensure these fields exist in the JSON output even if not provided
        log_record.setdefault('service_name', getattr(record, 'service_name', 'unknown'))
        log_record.setdefault('correlation_id', getattr(record, 'correlation_id', None))
        log_record.setdefault('trace_id', getattr(record, 'trace_id', None))

def setup_logging(service_name: str, log_level: str = "INFO"):
    """
    Configures structured JSON logging for the service.
    """
    logger = logging.getLogger()
    logger.setLevel(log_level)

    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)

    # These fields will be picked up by the formatter from the LogRecord or extra dict
    format_str = '%(timestamp)s %(level)s %(name)s %(message)s'

    formatter = CustomJsonFormatter(format_str)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Inject service_name into every LogRecord
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.service_name = service_name
        return record

    logging.setLogRecordFactory(record_factory)

    return logger
