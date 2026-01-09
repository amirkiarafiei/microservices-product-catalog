import json

import pytest
from common.config import BaseServiceSettings
from common.exceptions import NotFoundError, ValidationError
from common.logging import setup_logging
from common.utils.idempotency import idempotency_key_required
from common.utils.versioning import check_version
from common.security import UserContext


def test_logging_output(capsys):
    # Setup logging
    logger = setup_logging("test-service")

    # Log something
    logger.info("test message", extra={"correlation_id": "123", "trace_id": "abc"})

    # Capture stdout
    captured = capsys.readouterr()
    log_output = captured.out.splitlines()

    # Parse the last log line as JSON
    # Find the first line that is a valid JSON
    log_entry = None
    for line in log_output:
        try:
            log_entry = json.loads(line)
            break
        except json.JSONDecodeError:
            continue

    assert log_entry is not None, "No JSON log entry found in stdout"
    assert log_entry["service_name"] == "test-service"
    assert log_entry["message"] == "test message"
    assert log_entry["correlation_id"] == "123"
    assert log_entry["trace_id"] == "abc"
    assert "timestamp" in log_entry

def test_base_config():
    class TestSettings(BaseServiceSettings):
        SERVICE_NAME: str = "test-service"
        CUSTOM_VAL: str = "default"

    settings = TestSettings()
    assert settings.SERVICE_NAME == "test-service"
    assert settings.LOG_LEVEL == "INFO"
    assert settings.CUSTOM_VAL == "default"

def test_exceptions():
    with pytest.raises(ValidationError) as excinfo:
        raise ValidationError("invalid data", details={"field": "name"})

    assert excinfo.value.code == "VALIDATION_ERROR"
    assert excinfo.value.message == "invalid data"
    assert excinfo.value.details == {"field": "name"}

    with pytest.raises(NotFoundError) as excinfo:
        raise NotFoundError("not found")
    assert excinfo.value.code == "NOT_FOUND"

def test_versioning_utility():
    assert check_version(2, 1) is True
    assert check_version(1, 1) is False
    assert check_version(1, 2) is False


@pytest.mark.asyncio
async def test_idempotency_skeleton():
    @idempotency_key_required
    async def my_handler(val: int):
        return val * 2

    result = await my_handler(10)
    assert result == 20


def test_user_context():
    user = UserContext(user_id="123", username="test", role="ADMIN")
    assert user.user_id == "123"
    assert user.role == "ADMIN"
