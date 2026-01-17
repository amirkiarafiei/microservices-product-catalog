import os
import sys

import pytest
from common.security import UserContext
from common.testing.containers import start_postgres, start_rabbitmq
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src to path so we can import it
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))
sys.path.insert(0, BASE_DIR)

import src.infrastructure.database as db_module  # noqa: E402
import src.main as main_module  # noqa: E402
from src.config import settings  # noqa: E402
from src.infrastructure.database import Base, get_db  # noqa: E402
from src.main import admin_required, any_user_required, app  # noqa: E402


@pytest.fixture(scope="session")
def infra():
    pg_container, pg = start_postgres(dbname="characteristic_test_db")
    rmq_container, rmq = start_rabbitmq()
    try:
        yield {"pg_container": pg_container, "pg": pg, "rmq_container": rmq_container, "rmq": rmq}
    finally:
        rmq_container.stop()
        pg_container.stop()


@pytest.fixture(scope="session", autouse=True)
def configure_db(infra):
    # Point settings to containers
    settings.DATABASE_URL = infra["pg"].url
    settings.RABBITMQ_URL = infra["rmq"].amqp_url
    main_module.settings.DATABASE_URL = infra["pg"].url
    main_module.settings.RABBITMQ_URL = infra["rmq"].amqp_url

    # Re-init engine/session globals used by get_db()
    engine = create_engine(infra["pg"].url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_module.engine = engine
    db_module.SessionLocal = SessionLocal
    main_module.SessionLocal = SessionLocal

    # Create tables
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def db_session(infra):
    engine = create_engine(infra["pg"].url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Clean up data after each test to ensure isolation
        with engine.connect() as conn:
            for table in reversed(Base.metadata.sorted_tables):
                conn.execute(table.delete())
            conn.commit()


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

