from __future__ import annotations

from jose import jwt


def test_password_hash_and_verify(set_jwt_env):
    from src.security import get_password_hash, verify_password

    hashed = get_password_hash("secret")
    assert verify_password("secret", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_create_access_token_and_verify_signature(set_jwt_env, jwt_keys):
    from src.config import settings
    from src.security import create_access_token

    token = create_access_token({"sub": "user-id", "username": "admin", "role": "ADMIN"})
    decoded = jwt.decode(token, jwt_keys.public_key_pem, algorithms=[settings.JWT_ALGORITHM])
    assert decoded["sub"] == "user-id"
    assert decoded["username"] == "admin"
    assert decoded["role"] == "ADMIN"
    assert "exp" in decoded

