import os
import sys

import pytest
from common.security import UserContext
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src to path so we can import it
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))
sys.path.insert(0, BASE_DIR)

import offering.infrastructure.database as db_module  # noqa: E402
import offering.main as main_module  # noqa: E402
from offering.config import settings  # noqa: E402
from offering.infrastructure.database import Base, get_db  # noqa: E402
from offering.main import admin_required, any_user_required, app  # noqa: E402

# Test database URL
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql://user:password@localhost:5432/offering_test_db"
)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """
    Creates and migrates the test database at the beginning of the test session.
    """
    # Ensure the engine is created with the test URL
    db_module.engine = create_engine(TEST_DATABASE_URL)
    db_module.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_module.engine)
    db_module.DATABASE_URL = TEST_DATABASE_URL  # Ensure settings use test DB

    # Create tables
    Base.metadata.create_all(bind=db_module.engine)

    yield

    # Clean up (optional: drop tables)
    # Base.metadata.drop_all(bind=db_module.engine)


@pytest.fixture
def db_session():
    """
    Provides a clean database session for each test.
    """
    connection = db_module.engine.connect()
    transaction = connection.begin()
    session = db_module.SessionLocal(bind=connection)

    # Ensure settings use test DB
    settings.DATABASE_URL = TEST_DATABASE_URL
    main_module.settings.DATABASE_URL = TEST_DATABASE_URL

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def override_get_db(db_session):
    """
    Overrides the get_db dependency for FastAPI routes.
    """

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    return _override_get_db


@pytest.fixture
def mock_admin():
    return UserContext(user_id="admin-id", username="admin", role="ADMIN")


@pytest.fixture
def client(override_get_db, mock_admin):
    """
    Provides a FastAPI test client with database and auth dependencies overridden.
    Default role is ADMIN.
    """
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[admin_required] = lambda: mock_admin
    app.dependency_overrides[any_user_required] = lambda: mock_admin

    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
