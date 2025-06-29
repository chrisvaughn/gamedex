import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import create_session_token
from app.database import get_db
from app.main import app
from app.models import Base

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override the database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test"""
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Create session
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop tables
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden database dependency"""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def authenticated_client(db_session):
    """Create an authenticated test client"""
    app.dependency_overrides[get_db] = lambda: db_session

    with TestClient(app) as test_client:
        # Create a session token
        session_token = create_session_token()

        # Set the session cookie
        test_client.cookies.set("session", session_token)

        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def sample_game_data():
    """Sample game data for testing"""
    return {
        "title": "Test Game",
        "player_count": "2-4 players",
        "game_type": "Strategy",
        "playtime": "30-60 minutes",
        "complexity": "Medium",
    }


@pytest.fixture
def sample_games_data():
    """Multiple sample games for testing"""
    return [
        {
            "title": "Catan",
            "player_count": "3-4 players",
            "game_type": "Strategy",
            "playtime": "60-90 minutes",
            "complexity": "Medium",
        },
        {
            "title": "Ticket to Ride",
            "player_count": "2-5 players",
            "game_type": "Family",
            "playtime": "30-60 minutes",
            "complexity": "Easy",
        },
        {
            "title": "Pandemic",
            "player_count": "2-4 players",
            "game_type": "Cooperative",
            "playtime": "45 minutes",
            "complexity": "Medium",
        },
    ]
