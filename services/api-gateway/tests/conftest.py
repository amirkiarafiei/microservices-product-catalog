import os
import sys
import pytest
from fastapi.testclient import TestClient

# Add src to path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
sys.path.insert(0, BASE_DIR)

from gateway.main import app, breakers  # noqa: E402
from gateway.resilience import CircuitState  # noqa: E402

@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(autouse=True)
def reset_breakers():
    """Reset all circuit breakers between tests."""
    for breaker in breakers.values():
        breaker.state = CircuitState.CLOSED
        breaker.fail_count = 0
    yield
