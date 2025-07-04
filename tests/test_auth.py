import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException, Request
from fastapi.responses import RedirectResponse

from app.auth import (
    check_family_password,
    create_session_token,
    get_current_user,
    get_serializer,
    require_auth,
    verify_session_token,
)


class TestAuthFunctions:
    """Test cases for authentication functions"""

    def test_create_session_token(self):
        """Test creating a session token"""
        token = create_session_token()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_verify_session_token_valid(self):
        """Test verifying a valid session token"""
        # Create a token
        token = create_session_token()

        # Verify it
        result = verify_session_token(token)
        assert result is True

    def test_verify_session_token_invalid(self):
        """Test verifying an invalid session token"""
        result = verify_session_token("invalid_token")
        assert result is False

    def test_verify_session_token_expired(self):
        """Test verifying an expired session token"""
        # Create a token with a very short expiration
        with patch("app.auth.get_serializer") as mock_get_serializer:
            mock_serializer = MagicMock()
            mock_serializer.loads.side_effect = Exception("Token expired")
            mock_get_serializer.return_value = mock_serializer

            result = verify_session_token("any_token")
            assert result is False

    def test_verify_session_token_malformed(self):
        """Test verifying a malformed session token"""
        with patch("app.auth.get_serializer") as mock_get_serializer:
            mock_serializer = MagicMock()
            mock_serializer.loads.side_effect = Exception("Invalid token")
            mock_get_serializer.return_value = mock_serializer

            result = verify_session_token("malformed_token")
            assert result is False

    def test_get_current_user_with_valid_session(self):
        """Test getting current user with valid session"""
        # Create a valid token
        token = create_session_token()

        # Mock request with valid session cookie
        mock_request = MagicMock(spec=Request)
        mock_request.cookies = {"session": token}

        user = get_current_user(mock_request)
        assert user is not None
        assert user["authenticated"] is True

    def test_get_current_user_with_invalid_session(self):
        """Test getting current user with invalid session"""
        # Mock request with invalid session cookie
        mock_request = MagicMock(spec=Request)
        mock_request.cookies = {"session": "invalid_token"}

        user = get_current_user(mock_request)
        assert user is None

    def test_get_current_user_without_session(self):
        """Test getting current user without session cookie"""
        # Mock request without session cookie
        mock_request = MagicMock(spec=Request)
        mock_request.cookies = {}

        user = get_current_user(mock_request)
        assert user is None

    def test_get_current_user_with_none_session(self):
        """Test getting current user with None session cookie"""
        # Mock request with None session cookie
        mock_request = MagicMock(spec=Request)
        mock_request.cookies = {"session": None}

        user = get_current_user(mock_request)
        assert user is None

    def test_require_auth_with_valid_user(self):
        """Test require_auth with valid user"""
        # Create a valid token
        token = create_session_token()

        # Mock request with valid session cookie
        mock_request = MagicMock(spec=Request)
        mock_request.cookies = {"session": token}

        user = require_auth(mock_request)
        assert user is not None
        assert user["authenticated"] is True

    def test_require_auth_without_user(self):
        """Test require_auth without valid user"""
        # Mock request without valid session
        mock_request = MagicMock(spec=Request)
        mock_request.cookies = {}

        with pytest.raises(HTTPException) as exc_info:
            require_auth(mock_request)

        assert exc_info.value.status_code == 303
        assert exc_info.value.detail == "Authentication required"
        assert exc_info.value.headers["Location"] == "/login"

    def test_check_family_password_correct(self):
        """Test checking family password with correct password"""
        with patch.dict(
            os.environ,
            {"FAMILY_PASSWORD": "test_password", "SESSION_SECRET_KEY": "test_secret"},
            clear=True,
        ):
            # Re-import to get fresh module with new environment
            import importlib

            import app.auth

            importlib.reload(app.auth)

            result = app.auth.check_family_password("test_password")
            assert result is True

    def test_check_family_password_incorrect(self):
        """Test checking family password with incorrect password"""
        with patch.dict(os.environ, {"FAMILY_PASSWORD": "test_password"}):
            result = check_family_password("wrong_password")
            assert result is False

    def test_check_family_password_empty(self):
        """Test checking family password with empty password"""
        with patch.dict(os.environ, {"FAMILY_PASSWORD": "test_password"}):
            result = check_family_password("")
            assert result is False

    def test_get_serializer(self):
        """Test getting serializer"""
        with patch.dict(
            os.environ,
            {"SESSION_SECRET_KEY": "test_secret", "FAMILY_PASSWORD": "test_password"},
            clear=True,
        ):
            # Re-import to get fresh module with new environment
            import importlib

            import app.auth

            importlib.reload(app.auth)

            serializer = app.auth.get_serializer()
            assert serializer is not None

    def test_verify_session_token_with_false_authenticated(self):
        """Test verifying token that returns authenticated=False"""
        with patch("app.auth.get_serializer") as mock_get_serializer:
            mock_serializer = MagicMock()
            mock_serializer.loads.return_value = {"authenticated": False}
            mock_get_serializer.return_value = mock_serializer

            result = verify_session_token("any_token")
            assert result is False

    def test_verify_session_token_without_authenticated_key(self):
        """Test verifying token that doesn't have authenticated key"""
        with patch("app.auth.get_serializer") as mock_get_serializer:
            mock_serializer = MagicMock()
            mock_serializer.loads.return_value = {"other_key": "value"}
            mock_get_serializer.return_value = mock_serializer

            result = verify_session_token("any_token")
            assert result is False


class TestAuthEnvironmentVariables:
    """Test cases for environment variable handling"""

    def test_missing_session_secret_key(self):
        """Test that missing SESSION_SECRET_KEY raises RuntimeError"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(
                RuntimeError,
                match="SESSION_SECRET_KEY environment variable must be set",
            ):
                # Re-import auth module to trigger the check
                import importlib

                import app.auth

                importlib.reload(app.auth)

    def test_empty_session_secret_key(self):
        """Test that empty SESSION_SECRET_KEY raises RuntimeError"""
        with patch.dict(os.environ, {"SESSION_SECRET_KEY": ""}):
            with pytest.raises(
                RuntimeError,
                match="SESSION_SECRET_KEY environment variable must be set",
            ):
                # Re-import auth module to trigger the check
                import importlib

                import app.auth

                importlib.reload(app.auth)

    def test_missing_family_password(self):
        """Test that missing FAMILY_PASSWORD raises RuntimeError"""
        with patch.dict(os.environ, {"SESSION_SECRET_KEY": "test"}, clear=True):
            with pytest.raises(
                RuntimeError, match="FAMILY_PASSWORD environment variable must be set"
            ):
                # Re-import auth module to trigger the check
                import importlib

                import app.auth

                importlib.reload(app.auth)

    def test_empty_family_password(self):
        """Test that empty FAMILY_PASSWORD raises RuntimeError"""
        with patch.dict(
            os.environ, {"SESSION_SECRET_KEY": "test", "FAMILY_PASSWORD": ""}
        ):
            with pytest.raises(
                RuntimeError, match="FAMILY_PASSWORD environment variable must be set"
            ):
                # Re-import auth module to trigger the check
                import importlib

                import app.auth

                importlib.reload(app.auth)
