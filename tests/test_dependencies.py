import pytest
import asyncio
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient

# Import dependency functions from your module.
from app.dependencies import (
    get_settings,
    get_email_service,
    get_db,
    get_current_user,
    require_role,
    oauth2_scheme
)
from settings.config import Settings
from app.services.jwt_service import decode_token

# --------------------------------------------------------------------
# Test for get_settings()
# --------------------------------------------------------------------
def test_get_settings_returns_instance():
    settings_instance = get_settings()
    assert isinstance(settings_instance, Settings), "get_settings() should return an instance of Settings"

# --------------------------------------------------------------------
# Test for get_email_service()
# --------------------------------------------------------------------
def test_get_email_service_returns_instance():
    email_service = get_email_service()
    from app.services.email_service import EmailService  # Import here to check type.
    assert isinstance(email_service, EmailService), "get_email_service() should return an instance of EmailService"

# --------------------------------------------------------------------
# Test for get_db()
# --------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_db_yields_session(monkeypatch):
    # get_db() is an async generator. We'll iterate to retrieve one session.
    sessions = []
    async for session in get_db():
        sessions.append(session)
        await session.close()  # Close the session after use.
        break  # Only need one session for the test.
    from sqlalchemy.ext.asyncio import AsyncSession
    assert len(sessions) == 1, "get_db() should yield one session"
    assert isinstance(sessions[0], AsyncSession), "The yielded object should be an AsyncSession"

# --------------------------------------------------------------------
# Tests for get_current_user()
# --------------------------------------------------------------------
def test_get_current_user_valid_token(monkeypatch):
    # Simulate a valid payload with both 'sub' and 'role'.
    def fake_decode_token(token: str):
        return {"sub": "test@example.com", "role": "ADMIN"}
    monkeypatch.setattr("app.dependencies.decode_token", fake_decode_token)
    
    result = get_current_user(token="fake_token")
    assert result == {"user_id": "test@example.com", "role": "ADMIN"}, "get_current_user should return a dict with user_id and role"

def test_get_current_user_invalid_token(monkeypatch):
    # Simulate an invalid token (decode returns None).
    def fake_decode_token(token: str):
        return None
    monkeypatch.setattr("app.dependencies.decode_token", fake_decode_token)
    
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token="fake_token")
    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Could not validate credentials"

def test_get_current_user_missing_sub(monkeypatch):
    # Simulate a payload that is missing 'sub'.
    def fake_decode_token(token: str):
        return {"role": "ADMIN"}
    monkeypatch.setattr("app.dependencies.decode_token", fake_decode_token)
    
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token="fake_token")
    assert exc_info.value.status_code == 401

def test_get_current_user_missing_role(monkeypatch):
    # Simulate a payload that is missing 'role'.
    def fake_decode_token(token: str):
        return {"sub": "test@example.com"}
    monkeypatch.setattr("app.dependencies.decode_token", fake_decode_token)
    
    with pytest.raises(HTTPException) as exc_info:
        get_current_user(token="fake_token")
    assert exc_info.value.status_code == 401

# --------------------------------------------------------------------
# Tests for require_role()
# --------------------------------------------------------------------
