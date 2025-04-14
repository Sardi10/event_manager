# ISSUES_RESOLVED.md

This document summarizes the issues that have been identified and resolved during the development of the Event Manager API project. Each entry includes a description of the problem, the steps taken to resolve it, the code modifications made, and the outcome. All issues have been reviewed, tested, and merged into the main branch.

---

## Issue #1: Invalid Characters in Username

**Description:**  
Users should only be allowed to register with usernames (stored as the `nickname` field) that contain only alphanumeric characters, underscores, and hyphens. Inputs containing spaces or special characters (e.g., "john$doe") must be rejected with a clear validation error.

**Steps Taken:**  
1. **Model Update:**  
   - In `app/schemas/user_shemas.py`, a custom validator was added to the `nickname` field in the `UserBase` model.
   - **Code Modification:**
     ```python
     class UserBase(BaseModel):
         email: EmailStr = Field(..., example="john.doe@example.com")
         nickname: Optional[str] = Field(
             None,
             min_length=3,
             max_length=50,
             example=generate_nickname()
         )
         # other fields...
     
         @validator('nickname')
         def validate_nickname(cls, v):
             if v is not None:
                 if not re.match(r'^[A-Za-z0-9_-]+$', v):
                     raise ValueError("Nickname must contain only alphanumeric characters, underscores, or hyphens")
             return v
     ```
2. **Testing:**  
   - Tests were added in `tests/test_models/test_user_schemas.py` to ensure that invalid usernames (e.g., "john$doe") raise the expected validation error.

**Outcome:**  
- Invalid usernames now trigger an HTTP 422 error with a descriptive message, and the issue was resolved and merged into the main branch.

---

## Issue #2: Password Validation Does Not Enforce Complexity Requirements

**Description:**  
The API must enforce strong password policies during registration. This includes enforcing a minimum length and requiring at least one uppercase letter, one lowercase letter, one digit, and one special character.

**Steps Taken:**  
1. **Model Update:**  
   - In the `UserCreate` model (in `app/schemas/user_shemas.py`), a validator was added to enforce the complexity requirements for the `password` field.
   - **Code Modification:**
     ```python
     class UserCreate(UserBase):
         email: EmailStr = Field(..., example="john.doe@example.com")
         password: str = Field(..., example="Secure*1234")
     
         @validator('password')
         def validate_password(cls, v):
             if len(v) < 8:
                 raise ValueError("Password must be at least 8 characters long")
             if not re.search(r'[A-Z]', v):
                 raise ValueError("Password must contain at least one uppercase letter")
             if not re.search(r'[a-z]', v):
                 raise ValueError("Password must contain at least one lowercase letter")
             if not re.search(r'\d', v):
                 raise ValueError("Password must contain at least one digit")
             if not re.search(r'[!@#$%^&*()\-_=+]', v):
                 raise ValueError("Password must contain at least one special character (e.g., !@#$%^&*()-_=+)")
             return v
     ```
2. **Testing:**  
   - Tests were created for various invalid password scenarios (e.g., too short, lacking required character types) to confirm the validator raised a ValidationError with the correct error message.

**Outcome:**  
- The API now rejects passwords that do not meet the complexity requirements with a clear error message (HTTP 422), and the changes have been merged into the main branch.

---

## Issue #3: Profile Field Edge Cases in User Updates

**Description:**  
The user profile update endpoint must handle various edge cases for optional profile fields. This includes:
- Validating that profile-related URLs (`profile_picture_url`, `linkedin_profile_url`, `github_profile_url`) are correctly formatted (i.e., valid HTTP/HTTPS URLs).
- Enforcing a maximum length constraint on the bio field (e.g., 500 characters) to prevent overly long inputs.
- Ensuring that both partial updates (updating one field) and simultaneous updates (updating multiple fields) operate correctly, without overwriting unrelated data.

**Steps Taken:**  
1. **Model Enhancements:**  
   - In `app/schemas/user_shemas.py`:
     - A shared URL validator was added for the URL fields:
       ```python
       def validate_url(url: Optional[str]) -> Optional[str]:
           if url is None:
               return url
           url_regex = r'^https?:\/\/[^\s/$.?#].[^\s]*$'
           if not re.match(url_regex, url):
               raise ValueError('Invalid URL format')
           return url
       
       _validate_urls = validator('profile_picture_url', 'linkedin_profile_url', 'github_profile_url', pre=True, allow_reuse=True)(validate_url)
       ```
     - The `bio` field was updated with a maximum length constraint:
       ```python
       bio: Optional[str] = Field(None, max_length=500, example="Experienced software developer specializing in web applications.")
       ```
2. **Endpoint Behavior:**  
   - The update operation in the service layer (using Pydantic’s `exclude_unset=True`) ensures that only the provided fields are updated.
3. **Testing:**  
   - New tests were added to verify that:
     - Invalid URLs trigger a validation error.
     - A bio field longer than 500 characters results in an error.
     - Simultaneous updates (updating multiple fields at once) are processed correctly.
   - **Example Test:**
     ```python
     import pytest
     from pydantic import ValidationError
     from app.schemas.user_shemas import UserUpdate
     
     def test_invalid_profile_picture_url():
         invalid_update = {"profile_picture_url": "htt:/invalid"}
         with pytest.raises(ValidationError) as exc_info:
             UserUpdate(**invalid_update)
         assert "Invalid URL format" in str(exc_info.value)
     
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
     ```

**Outcome:**  
- The API now properly validates profile field inputs. Invalid URLs and overly long bios are rejected with clear error messages, while valid partial and simultaneous updates are processed correctly. No changes to the core update logic were necessary. The resolution has been verified with tests and merged into the main branch.

---

## Issue #4: Account Lockout on Multiple Failed Login Attempts

**Description:**  
To mitigate brute-force attacks, the API should lock a user’s account after a specific number of consecutive failed login attempts (configured via `settings.max_login_attempts`). Once this threshold is reached, the account should be locked (i.e., `is_locked` set to `True`), preventing further login attempts.

**Steps Taken:**  
1. **Login Logic Update:**  
   - In `app/services/user_service.py`, the `login_user` method was updated to increment a user’s `failed_login_attempts` and, upon reaching the threshold, set `is_locked` to `True`:
     ```python
     @classmethod
     async def login_user(cls, session: AsyncSession, email: str, password: str) -> Optional[User]:
         user = await cls.get_by_email(session, email)
         if user:
             if user.email_verified is False:
                 logger.info(f"User {email} is not verified.")
                 return None
             if user.is_locked:
                 logger.info(f"User {email} is locked.")
                 return None
             if verify_password(password, user.hashed_password):
                 user.failed_login_attempts = 0
                 user.last_login_at = datetime.now(timezone.utc)
                 session.add(user)
                 await session.commit()
                 logger.info(f"User {email} logged in successfully.")
                 return user
             else:
                 user.failed_login_attempts += 1
                 logger.info(f"Failed login attempt {user.failed_login_attempts} for user {email}.")
                 if user.failed_login_attempts >= settings.max_login_attempts:
                     user.is_locked = True
                     logger.info(f"User {email} has been locked due to too many failed login attempts.")
                 session.add(user)
                 await session.commit()
         return None
     ```
2. **Testing:**  
   - A test was added in `tests/test_services/test_user_service.py` to simulate consecutive failed login attempts:
     ```python
     import pytest
     from app.services.user_service import UserService
     from settings.config import settings
     
     @pytest.mark.asyncio
     async def test_account_lockout_on_failed_logins(db_session, verified_user):
         for _ in range(settings.max_login_attempts):
             user = await UserService.login_user(db_session, verified_user.email, "WrongPassword")
             assert user is None
         locked_user = await UserService.get_by_email(db_session, verified_user.email)
         assert locked_user.is_locked is True, "The account should be locked after maximum failed login attempts."
     ```
   - If importing `settings` causes issues in the test, a local constant (e.g., `MAX_LOGIN_ATTEMPTS = 3`) can be used.

**Outcome:**  
- Upon reaching the maximum number of failed attempts, the user’s account is locked and further login attempts are rejected. The implementation has been verified via tests and merged into the main branch.

---

## Issue #5: JWT Token Expiry Handling

**Description:**  
For enhanced security, JWT tokens must expire after a predetermined duration (e.g., 15 minutes). The API must validate tokens upon authentication and reject expired tokens, returning an HTTP 401 error.

**Steps Taken:**  
1. **Token Generation and Decoding Update:**  
   - In `app/services/jwt_service.py`, the token creation function was verified to include an expiration claim, and the token decoding function was updated to handle expired tokens:
     ```python
     from datetime import datetime, timedelta
     import jwt
     from settings.config import settings
     
     def create_access_token(*, data: dict, expires_delta: timedelta = None):
         to_encode = data.copy()
         expire = datetime.utcnow() + (expires_delta if expires_delta else timedelta(minutes=settings.access_token_expire_minutes))
         to_encode.update({"exp": expire})
         encoded_jwt = jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
         return encoded_jwt
     
     def decode_token(token: str):
         try:
             decoded = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
             return decoded
         except jwt.ExpiredSignatureError:
             # Token has expired
             return None
         except jwt.PyJWTError:
             return None
     ```
2. **Token Validation on Protected Endpoints:**  
   - The dependency that retrieves the current user (e.g., `get_current_user` in `app/dependencies.py`) uses `decode_token` to verify the token. Expired tokens now result in an HTTP 401 error.
3. **Testing:**  
   - Automated tests were implemented to verify that a token, once expired, results in protected endpoints returning HTTP 401.
   - For instance, a test may generate a token with a very short expiration, wait for it to expire, and then attempt to access a protected resource.

**Outcome:**  
- Expired tokens are correctly rejected by the API, enforcing security best practices. The modifications have been tested and merged into the main branch.

---

# End of ISSUES_RESOLVED.md Entries
