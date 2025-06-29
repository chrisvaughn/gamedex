import os
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from itsdangerous import URLSafeTimedSerializer
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Session management
SESSION_SECRET_KEY = os.getenv("SESSION_SECRET_KEY")
serializer = URLSafeTimedSerializer(SESSION_SECRET_KEY)

# Family password (you can change this)
FAMILY_PASSWORD = os.getenv("FAMILY_PASSWORD")

if not SESSION_SECRET_KEY:
    raise RuntimeError(
        "SESSION_SECRET_KEY environment variable must be set and non-empty."
    )
if not FAMILY_PASSWORD:
    raise RuntimeError(
        "FAMILY_PASSWORD environment variable must be set and non-empty."
    )


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_session_token() -> str:
    """Create a session token"""
    return serializer.dumps({"authenticated": True})


def verify_session_token(token: str) -> bool:
    """Verify a session token"""
    try:
        data = serializer.loads(token, max_age=86400)  # 24 hours
        return data.get("authenticated", False)
    except:
        return False


def get_current_user(request: Request) -> Optional[dict]:
    """Get current user from session"""
    session_token = request.cookies.get("session")
    if session_token and verify_session_token(session_token):
        return {"authenticated": True}
    return None


def require_auth(request: Request) -> dict:
    """Require authentication - redirect to login if not authenticated"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Authentication required",
            headers={"Location": "/login"},
        )
    return user


def check_family_password(password: str) -> bool:
    """Check if the provided password matches the family password"""
    return password == FAMILY_PASSWORD
