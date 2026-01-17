import os
import sys
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

# Add src to path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
sys.path.insert(0, BASE_DIR)

from store.main import app  # noqa: E402


@pytest.fixture
def client():
    """
    Component-test client:
    - Mocks external deps (Mongo/ES init + consumer start/stop)
    - No Docker required
    """
    with (
        patch("store.infrastructure.elasticsearch.es_client.init_index", new_callable=AsyncMock),
        patch("store.infrastructure.elasticsearch.es_client.close", new_callable=AsyncMock),
        patch("store.infrastructure.mongodb.mongodb_client.close", new_callable=AsyncMock),
        patch("store.application.consumers.EventConsumerService.start", new_callable=AsyncMock),
        patch("store.application.consumers.EventConsumerService.stop", new_callable=AsyncMock),
    ):
        with TestClient(app) as test_client:
            yield test_client
