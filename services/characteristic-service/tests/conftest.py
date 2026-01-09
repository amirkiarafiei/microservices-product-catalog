import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys

# Add src to path so we can import it
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from src.infrastructure.database import Base, get_db
from src.main import app, admin_required, any_user_required
from common.security import UserContext

# Test database URL
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "postgresql://user:password@localhost:5432/characteristic_test_db")

@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    """
    Creates and migrates the test database at the beginning of the test session.
    """
    engine = create_engine(TEST_DATABASE_URL)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    yield
    
    # Clean up (optional: drop tables)
    # Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    """
    Provides a clean database session for each test.
    """
    engine = create_engine(TEST_DATABASE_URL)
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
    from fastapi.testclient import TestClient
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[admin_required] = lambda: mock_admin
    app.dependency_overrides[any_user_required] = lambda: mock_admin
    
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
