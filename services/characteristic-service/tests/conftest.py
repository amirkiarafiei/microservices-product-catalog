import os
import sys
from unittest.mock import MagicMock

import pytest
from common.security import UserContext
from fastapi.testclient import TestClient

# Add src to path so we can import it
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

import characteristic.main as main_module  # noqa: E402
from characteristic.infrastructure.database import get_db  # noqa: E402
from characteristic.main import admin_required, any_user_required, app  # noqa: E402


@pytest.fixture
def mock_admin():
    return UserContext(user_id="admin-id", username="admin", role="ADMIN")


@pytest.fixture
def db_session_mock():
    # Component tests should not require a real DB.
    return MagicMock()


@pytest.fixture
def client(db_session_mock, mock_admin):
    """
    Component-test client:
    - No Postgres/Rabbit required.
    - DB dependency overridden with a MagicMock session.
    - Auth dependencies overridden to ADMIN.
    """

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
