import os
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import text

from app.database import get_db


class TestHealthCheck:
    def test_health_check_healthy(self, db_session):
        from fastapi.testclient import TestClient

        from app.main import app

        app.dependency_overrides[get_db] = lambda: db_session
        client = TestClient(app)
        response = client.get("/healthz")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert data["environment"] == "development"

    def test_health_check_healthy_production(self, db_session):
        with patch.dict(os.environ, {"IS_PRODUCTION": "true"}):
            from fastapi.testclient import TestClient

            from app.main import app

            app.dependency_overrides[get_db] = lambda: db_session
            client = TestClient(app)
            response = client.get("/healthz")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert data["database"] == "connected"
            assert data["environment"] == "production"

    def test_health_check_unhealthy(self, db_session):
        from fastapi.testclient import TestClient

        from app.main import app

        app.dependency_overrides[get_db] = lambda: db_session

        # Mock the database to raise an exception
        with patch.object(db_session, "execute", side_effect=Exception("DB Error")):
            client = TestClient(app)
            response = client.get("/healthz")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "unhealthy"
            assert data["database"] == "disconnected"

    def test_health_check_head(self, db_session):
        from fastapi.testclient import TestClient

        from app.main import app

        app.dependency_overrides[get_db] = lambda: db_session
        client = TestClient(app)
        response = client.head("/healthz")
        assert response.status_code == 200


class TestLoginLogout:
    def test_login_page_get(self):
        with patch.dict(
            os.environ,
            {"FAMILY_PASSWORD": "test_password", "SESSION_SECRET_KEY": "test_secret"},
        ):
            from fastapi.testclient import TestClient

            from app.main import app

            client = TestClient(app)
            response = client.get("/login")
            assert response.status_code == 200
            assert "Family Password" in response.text
            assert "Login to GameDex" in response.text

    def test_login_success(self):
        with patch.dict(
            os.environ,
            {"FAMILY_PASSWORD": "test_password", "SESSION_SECRET_KEY": "test_secret"},
        ):
            import importlib

            import app.auth

            importlib.reload(app.auth)
            from fastapi.testclient import TestClient

            from app.main import app

            client = TestClient(app)
            client.cookies.clear()
            response = client.post(
                "/login", data={"password": "test_password"}, follow_redirects=False
            )
            if response.status_code != 303:
                print(
                    f"DEBUG: status={response.status_code}, headers={response.headers}, text={response.text[:200]}"
                )
            assert response.status_code == 303
            assert response.headers["location"] == "/"
            assert "session" in response.cookies
            assert response.cookies["session"] != ""

    def test_login_success_production(self):
        with patch.dict(
            os.environ,
            {
                "FAMILY_PASSWORD": "test_password",
                "SESSION_SECRET_KEY": "test_secret",
                "IS_PRODUCTION": "true",
            },
        ):
            import importlib

            import app.auth

            importlib.reload(app.auth)
            from fastapi.testclient import TestClient

            from app.main import app

            client = TestClient(app)
            client.cookies.clear()
            response = client.post(
                "/login", data={"password": "test_password"}, follow_redirects=False
            )
            if response.status_code != 303:
                print(
                    f"DEBUG: status={response.status_code}, headers={response.headers}, text={response.text[:200]}"
                )
            assert response.status_code == 303
            assert response.headers["location"] == "/"
            assert "session" in response.cookies
            session_cookie = response.cookies["session"]
            assert session_cookie != ""

    def test_login_failure(self):
        with patch.dict(
            os.environ,
            {"FAMILY_PASSWORD": "test_password", "SESSION_SECRET_KEY": "test_secret"},
        ):
            from fastapi.testclient import TestClient

            from app.main import app

            client = TestClient(app)
            response = client.post("/login", data={"password": "wrong_password"})
            assert response.status_code == 200
            assert "Invalid password" in response.text
            assert "Family Password" in response.text

    def test_login_empty_password(self):
        with patch.dict(
            os.environ,
            {"FAMILY_PASSWORD": "test_password", "SESSION_SECRET_KEY": "test_secret"},
        ):
            from fastapi.testclient import TestClient

            from app.main import app

            client = TestClient(app)
            response = client.post("/login", data={"password": ""})
            assert response.status_code == 200
            assert "Invalid password" in response.text
            assert "Family Password" in response.text

    def test_logout(self):
        with patch.dict(
            os.environ,
            {"FAMILY_PASSWORD": "test_password", "SESSION_SECRET_KEY": "test_secret"},
        ):
            from fastapi.testclient import TestClient

            from app.main import app

            client = TestClient(app)
            response = client.get("/logout", follow_redirects=False)
            assert response.status_code == 303
            assert response.headers["location"] == "/login"
            # Check for cookie deletion in headers
            set_cookie_header = response.headers.get("set-cookie", "")
            assert "session=" in set_cookie_header and "Max-Age=0" in set_cookie_header

    def test_login_missing_password(self):
        with patch.dict(
            os.environ,
            {"FAMILY_PASSWORD": "test_password", "SESSION_SECRET_KEY": "test_secret"},
        ):
            from fastapi.testclient import TestClient

            from app.main import app

            client = TestClient(app)
            response = client.post("/login", data={})
            assert response.status_code == 422  # Validation error

    def test_login_with_session_cookie(self):
        with patch.dict(
            os.environ,
            {"FAMILY_PASSWORD": "test_password", "SESSION_SECRET_KEY": "test_secret"},
        ):
            import importlib

            import app.auth

            importlib.reload(app.auth)
            from fastapi.testclient import TestClient

            from app.main import app

            client = TestClient(app)
            client.cookies.clear()
            login_response = client.post(
                "/login", data={"password": "test_password"}, follow_redirects=False
            )
            if login_response.status_code != 303:
                print(
                    f"DEBUG: status={login_response.status_code}, headers={login_response.headers}, text={login_response.text[:200]}"
                )
            assert login_response.status_code == 303
            session_cookie = login_response.cookies["session"]
            response = client.post(
                "/login", data={"password": "test_password"}, follow_redirects=False
            )
            if response.status_code != 303:
                print(
                    f"DEBUG: status={response.status_code}, headers={response.headers}, text={response.text[:200]}"
                )
            assert response.status_code == 303
            assert response.headers["location"] == "/"


class TestUIEndpoints:
    """Test cases for UI/UX endpoints (pages and forms)"""

    def test_new_game_form(self, authenticated_client):
        """Test the new game form page"""
        response = authenticated_client.get("/games/new")
        assert response.status_code == 200
        assert "Add New Game" in response.text

    def test_edit_game_form_success(self, authenticated_client, db_session):
        """Test the edit game form"""
        # Create a game first
        from app.models import Game

        game = Game(title="Test Game")
        db_session.add(game)
        db_session.commit()

        response = authenticated_client.get(f"/games/{game.id}/edit")
        assert response.status_code == 200
        assert "Test Game" in response.text

    def test_edit_game_form_not_found(self, authenticated_client):
        """Test edit form for non-existent game"""
        response = authenticated_client.get("/games/999/edit")
        assert response.status_code == 404

    def test_settings_page(self, authenticated_client, db_session):
        """Test the settings page"""
        response = authenticated_client.get("/settings")
        assert response.status_code == 200
        assert "Settings" in response.text

    def test_recommend_page(self, authenticated_client):
        """Test the recommendation page"""
        response = authenticated_client.get("/recommend")
        assert response.status_code == 200
        assert "Recommendations" in response.text


class TestAuthenticationRequired:
    """Test cases for endpoints that require authentication"""

    def test_index_requires_auth(self, db_session):
        """Test that index page requires authentication"""
        from fastapi.testclient import TestClient

        from app.main import app

        app.dependency_overrides[get_db] = lambda: db_session
        client = TestClient(app)

        # Don't set any session cookie
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/login"

    def test_games_requires_auth(self, db_session):
        """Test that games page requires authentication"""
        from fastapi.testclient import TestClient

        from app.main import app

        app.dependency_overrides[get_db] = lambda: db_session
        client = TestClient(app)

        # Don't set any session cookie
        response = client.get("/games", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/login"

    def test_settings_requires_auth(self, db_session):
        """Test that settings page requires authentication"""
        from fastapi.testclient import TestClient

        from app.main import app

        app.dependency_overrides[get_db] = lambda: db_session
        client = TestClient(app)

        # Don't set any session cookie
        response = client.get("/settings", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/login"
