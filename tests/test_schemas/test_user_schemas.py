from builtins import str
import pytest
from pydantic import ValidationError
from datetime import datetime
from app.schemas.user_schemas import UserBase, UserCreate, UserUpdate, UserResponse, UserListResponse, LoginRequest

# Tests for UserBase
def test_user_base_valid(user_base_data):
    user = UserBase(**user_base_data)
    assert user.nickname == user_base_data["nickname"]
    assert user.email == user_base_data["email"]

# Tests for UserCreate
def test_user_create_valid(user_create_data):
    user = UserCreate(**user_create_data)
    assert user.nickname == user_create_data["nickname"]
    assert user.password == user_create_data["password"]

# Tests for UserUpdate
def test_user_update_valid(user_update_data):
    user_update = UserUpdate(**user_update_data)
    assert user_update.email == user_update_data["email"]
    assert user_update.first_name == user_update_data["first_name"]

# Tests for UserResponse
def test_user_response_valid(user_response_data):
    user = UserResponse(**user_response_data)
    assert str(user.id) == user_response_data["id"]
    #assert user.last_login_at == user_response_data["last_login_at"]

# Tests for LoginRequest
def test_login_request_valid(login_request_data):
    login = LoginRequest(**login_request_data)
    assert login.email == login_request_data["email"]
    assert login.password == login_request_data["password"]

# Parametrized tests for nickname and email validation
@pytest.mark.parametrize("nickname", ["test_user", "test-user", "testuser123", "123test"])
def test_user_base_nickname_valid(nickname, user_base_data):
    user_base_data["nickname"] = nickname
    user = UserBase(**user_base_data)
    assert user.nickname == nickname

@pytest.mark.parametrize("nickname", ["test user", "test?user", "", "us"])
def test_user_base_nickname_invalid(nickname, user_base_data):
    user_base_data["nickname"] = nickname
    with pytest.raises(ValidationError):
        UserBase(**user_base_data)

# Parametrized tests for URL validation
@pytest.mark.parametrize("url", ["http://valid.com/profile.jpg", "https://valid.com/profile.png", None])
def test_user_base_url_valid(url, user_base_data):
    user_base_data["profile_picture_url"] = url
    user = UserBase(**user_base_data)
    assert user.profile_picture_url == url

@pytest.mark.parametrize("url", ["ftp://invalid.com/profile.jpg", "http//invalid", "https//invalid"])
def test_user_base_url_invalid(url, user_base_data):
    user_base_data["profile_picture_url"] = url
    with pytest.raises(ValidationError):
        UserBase(**user_base_data)

# Tests for UserBase
def test_user_base_invalid_email(user_base_data_invalid):
    with pytest.raises(ValidationError) as exc_info:
        user = UserBase(**user_base_data_invalid)
    
    assert "value is not a valid email address" in str(exc_info.value)
    assert "john.doe.example.com" in str(exc_info.value)

#Test for Invalid nichname Characters
def test_invalid_nickname_characters():
    invalid_data = {
        "email": "test@example.com",
        "nickname": "john$doe",  # Contains an invalid character '$'
    }
    with pytest.raises(ValidationError) as exc_info:
        UserBase(**invalid_data)
    assert "Nickname must contain only alphanumeric characters" in str(exc_info.value)

def test_weak_password():
    # Test with a password that is too short and lacks complexity.
    invalid_payload = {
        "email": "test@example.com",
        "password": "pass"  # Too short, no digits, and no special character
    }
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(**invalid_payload)
    
    error_str = str(exc_info.value)
    assert "at least 8 characters" in error_str or "uppercase" in error_str

def test_password_without_special_character():
    invalid_payload = {
        "email": "test@example.com",
        "password": "Password1"  # No special character
    }
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(**invalid_payload)
    
    error_str = str(exc_info.value)
    assert "special character" in error_str

def test_password_too_short():
    invalid_data = {
        "email": "test@example.com",
        "password": "Short1!",
    }
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(**invalid_data)
    assert "at least 8 characters" in str(exc_info.value)

def test_password_without_uppercase():
    invalid_data = {
        "email": "test@example.com",
        "password": "secure*1234",  # no uppercase letters
    }
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(**invalid_data)
    assert "at least one uppercase" in str(exc_info.value)

def test_password_without_lowercase():
    invalid_data = {
        "email": "test@example.com",
        "password": "SECURE*1234",  # no lowercase letters
    }
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(**invalid_data)
    assert "at least one lowercase" in str(exc_info.value)

def test_password_without_digit():
    invalid_data = {
        "email": "test@example.com",
        "password": "Secure*Password",  # no digits
    }
    with pytest.raises(ValidationError) as exc_info:
        UserCreate(**invalid_data)
    assert "at least one digit" in str(exc_info.value)

@pytest.mark.asyncio
async def test_update_multiple_profile_fields(async_client, admin_token, verified_user):
    headers = {"Authorization": f"Bearer {admin_token}"}
    update_payload = {
        "bio": "Updated bio text that is valid.",
        "profile_picture_url": "https://example.com/new-profile.jpg"
    }
    response = await async_client.put(f"/users/{verified_user.id}", json=update_payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["bio"] == update_payload["bio"]
    assert data["profile_picture_url"] == update_payload["profile_picture_url"]

def test_invalid_profile_picture_url():
    invalid_update = {"profile_picture_url": "htt:/invalid"}
    with pytest.raises(ValidationError) as exc_info:
        UserUpdate(**invalid_update)
    assert "Invalid URL format" in str(exc_info.value)