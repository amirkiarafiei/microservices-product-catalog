import os
import sys
from dataclasses import dataclass
from typing import Generator

import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


@dataclass(frozen=True)
class JwtKeyPair:
    private_key_pem: str
    public_key_pem: str


def _generate_rsa_keypair() -> JwtKeyPair:
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return JwtKeyPair(private_key_pem=private_pem, public_key_pem=public_pem)


@pytest.fixture(scope="session")
def jwt_keys() -> JwtKeyPair:
    return _generate_rsa_keypair()


@pytest.fixture(scope="session", autouse=True)
def ensure_import_paths():
    # Add src to path so we can import identity service modules as `src.*`
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
    sys.path.insert(0, BASE_DIR)
    yield


@pytest.fixture
def set_jwt_env(jwt_keys: JwtKeyPair) -> Generator[None, None, None]:
    """
    Identity Settings require JWT keys at import time.
    """
    os.environ["JWT_PRIVATE_KEY"] = jwt_keys.private_key_pem
    os.environ["JWT_PUBLIC_KEY"] = jwt_keys.public_key_pem
    yield

