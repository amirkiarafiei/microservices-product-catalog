import os
import sys

import pytest
from common.security import UserContext
from common.testing.containers import start_postgres
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src to path so we can import it, and ensure we get the right 'src'
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
COMMON_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../libs/common-python/src"))
sys.path = [p for p in sys.path if not p.endswith("/src")]
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, COMMON_DIR)

import pricing.infrastructure.database as db_module  # noqa: E402
import pricing.main as main_module  # noqa: E402
from pricing.config import settings  # noqa: E402
from pricing.infrastructure.database import Base, get_db  # noqa: E402
from pricing.main import admin_required, any_user_required, app  # noqa: E402


@pytest.fixture(scope="session")
def infra():
    pg_container, pg = start_postgres(dbname="pricing_test_db")
    try:
        yield {"pg_container": pg_container, "pg": pg}
    finally:
        pg_container.stop()


@pytest.fixture(scope="session", autouse=True)
def configure_db(infra):
    settings.DATABASE_URL = infra["pg"].url
    main_module.settings.DATABASE_URL = infra["pg"].url

    db_module.engine = create_engine(infra["pg"].url)
    db_module.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_module.engine)
    db_module.DATABASE_URL = infra["pg"].url

    Base.metadata.create_all(bind=db_module.engine)
    yield


@pytest.fixture
def db_session():
    connection = db_module.engine.connect()
    transaction = connection.begin()
    session = db_module.SessionLocal(bind=connection)
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def override_get_db(db_session):
    def _override_get_db():
        yield db_session

    return _override_get_db


@pytest.fixture
def mock_admin():
    return UserContext(user_id="admin-id", username="admin", role="ADMIN")


@pytest.fixture
def client(override_get_db, mock_admin):
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[admin_required] = lambda: mock_admin
    app.dependency_overrides[any_user_required] = lambda: mock_admin
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

