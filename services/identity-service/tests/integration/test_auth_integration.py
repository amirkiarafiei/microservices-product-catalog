from __future__ import annotations

from jose import jwt


def test_login_admin_success_and_token_decodes(client, jwt_keys):
    # OAuth2PasswordRequestForm expects x-www-form-urlencoded
    resp = client.post(
        "/api/v1/auth/login",
        data={"username": "admin", "password": "admin"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "access_token" in body

    from src.config import settings

    decoded = jwt.decode(body["access_token"], jwt_keys.public_key_pem, algorithms=[settings.JWT_ALGORITHM])
    assert decoded["username"] == "admin"
    assert decoded["role"] == "ADMIN"


def test_public_key_matches_env(client, jwt_keys):
    resp = client.get("/api/v1/auth/public-key")
    assert resp.status_code == 200
    assert resp.json()["public_key"].strip() == jwt_keys.public_key_pem.strip()

