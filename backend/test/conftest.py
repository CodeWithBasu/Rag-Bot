"""
Pytest configuration and shared test fixtures for RAG Bot backend tests.

This module provides:
- An in-memory SQLite database (separate from production)
- A test FastAPI client
- Pre-created test user and JWT token helpers
"""
import sys
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ensure backend modules are importable
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from database import Base, get_db
from main import app
import auth


# ─── In-Memory Test Database ───────────────────────────────────────────
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_ragbot.db"

test_engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_database():
    """Create all tables before each test, drop them after."""
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session():
    """Get a test database session."""
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """FastAPI test client that uses the test database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# ─── Helper Fixtures ───────────────────────────────────────────────────
@pytest.fixture
def test_user(client):
    """Register a test user and return user data."""
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPassword123"
    }
    response = client.post("/auth/register", json=user_data)
    assert response.status_code == 200
    return user_data


@pytest.fixture 
def auth_token(client, test_user):
    """Login with the test user and return a valid JWT token."""
    response = client.post("/auth/login", data={
        "username": test_user["username"],
        "password": test_user["password"]
    })
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    """Return authorization headers with a valid JWT token."""
    return {"Authorization": f"Bearer {auth_token}"}
