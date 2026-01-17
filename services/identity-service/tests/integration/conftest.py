import os
import sys

import pytest
from common.testing.containers import start_postgres
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src to path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, BASE_DIR)


@pytest.fixture(scope="session")
def infra(jwt_keys):
    # Ensure required env is set BEFORE importing identity modules
    os.environ["JWT_PRIVATE_KEY"] = jwt_keys.private_key_pem
    os.environ["JWT_PUBLIC_KEY"] = jwt_keys.public_key_pem

    pg_container, pg = start_postgres(dbname="identity_test_db")
    os.environ["DATABASE_URL"] = pg.url

    try:
        yield {"pg_container": pg_container, "pg": pg}
    finally:
        pg_container.stop()


@pytest.fixture(scope="session", autouse=True)
def configure_db(infra):
    # Rebuild engine/session in identity database module to point at container
    import src.database as db_module  # noqa: E402
    import src.models  # noqa: E402  (register models)

    db_module.engine = create_engine(infra["pg"].url)
    db_module.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_module.engine)
    db_module.DATABASE_URL = infra["pg"].url

    db_module.Base.metadata.create_all(bind=db_module.engine)
    yield


@pytest.fixture
def client(infra):
    from src.main import app

    with TestClient(app) as c:
        yield c

