import os
import sys
from unittest.mock import MagicMock

import pytest
from common.security import UserContext
from fastapi.testclient import TestClient

# Add src to path so we can import it
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
sys.path.insert(0, BASE_DIR)

import offering.main as main_module  # noqa: E402
from offering.infrastructure.database import get_db  # noqa: E402
from offering.main import admin_required, any_user_required, app  # noqa: E402


@pytest.fixture
def mock_admin():
    return UserContext(user_id="admin-id", username="admin", role="ADMIN")


@pytest.fixture
def db_session_mock():
    return MagicMock()


@pytest.fixture
def client(db_session_mock, mock_admin):
    # Prevent background outbox listener in component tests
    main_module.settings.DATABASE_URL = None

    def _override_get_db():
        yield db_session_mock

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[admin_required] = lambda: mock_admin
    app.dependency_overrides[any_user_required] = lambda: mock_admin

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
