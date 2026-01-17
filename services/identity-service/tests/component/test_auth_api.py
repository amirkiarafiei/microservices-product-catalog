from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(set_jwt_env) -> TestClient:
    from src.database import get_db
    from src.main import app

    def _override_get_db():
        yield MagicMock()

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_public_key_endpoint(client: TestClient, jwt_keys):
    resp = client.get("/api/v1/auth/public-key")
    assert resp.status_code == 200
    body = resp.json()
    assert "public_key" in body
    assert body["public_key"].strip() == jwt_keys.public_key_pem.strip()


def test_login_invalid_credentials_returns_401(set_jwt_env):
    from src.database import get_db
    from src.main import app

    # Mock DB to return no user
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None

    def _override_get_db():
        yield db

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as client:
        resp = client.post(
            "/api/v1/auth/login",
            data={"username": "nope", "password": "nope"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert resp.status_code == 401
    app.dependency_overrides.clear()

