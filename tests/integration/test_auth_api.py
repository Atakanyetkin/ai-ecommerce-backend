import pytest
from fastapi.testclient import TestClient

from app import crud
from app.core.rate_limiter import limiter
from app.schemas.user import UserCreate


def test_signup_success(client: TestClient):
    """Verify new user signup succeeds and returns access/refresh tokens without sensitive data."""
    payload = {
        "email": "  NewUser@Example.Com  ",
        "username": "newuser123",
        "password": "StrongPassword123!",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    # Ensure no password / passwordHash in response body
    assert "password" not in data
    assert "hashed_password" not in data


def test_signup_duplicate_email_conflict(client: TestClient):
    """Verify signup with an existing email returns 409 EMAIL_ALREADY_REGISTERED."""
    payload = {
        "email": "duplicate@example.com",
        "username": "user1",
        "password": "StrongPassword123!",
    }
    response1 = client.post("/api/v1/auth/register", json=payload)
    assert response1.status_code == 201

    # Second signup with same email
    payload2 = {
        "email": "duplicate@example.com",
        "username": "user2",
        "password": "StrongPassword123!",
    }
    response2 = client.post("/api/v1/auth/register", json=payload2)
    assert response2.status_code == 409
    data = response2.json()
    assert data["success"] is False
    assert data["code"] == "EMAIL_ALREADY_REGISTERED"
    assert data["message"] == "An account with this email already exists."


def test_signup_case_insensitive_duplicate(client: TestClient):
    """Verify case-insensitive duplicate email check (Test@Email.com vs test@email.com)."""
    payload1 = {
        "email": "Test@Email.com",
        "username": "caseduser1",
        "password": "StrongPassword123!",
    }
    response1 = client.post("/api/v1/auth/register", json=payload1)
    assert response1.status_code == 201

    payload2 = {
        "email": "test@email.com",
        "username": "caseduser2",
        "password": "StrongPassword123!",
    }
    response2 = client.post("/api/v1/auth/register", json=payload2)
    assert response2.status_code == 409
    assert response2.json()["code"] == "EMAIL_ALREADY_REGISTERED"


def test_login_success(client: TestClient):
    """Verify login with correct email and password returns JWT tokens."""
    signup_payload = {
        "email": "loginuser@example.com",
        "username": "loginuser",
        "password": "ValidPassword123!",
    }
    client.post("/api/v1/auth/register", json=signup_payload)

    login_payload = {
        "email": "  LOGINUSER@EXAMPLE.COM  ",
        "password": "ValidPassword123!",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


def test_login_invalid_credentials_identical_response(client: TestClient):
    """Verify non-existent user and wrong password return IDENTICAL 401 INVALID_CREDENTIALS responses."""
    # 1. Non-existent user
    resp_nonexistent = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "SomePassword123!"},
    )
    assert resp_nonexistent.status_code == 401
    data_nonexistent = resp_nonexistent.json()

    # 2. Existing user, wrong password
    client.post(
        "/api/v1/auth/register",
        json={"email": "realuser@example.com", "username": "realuser", "password": "CorrectPassword123!"},
    )
    resp_wrongpass = client.post(
        "/api/v1/auth/login",
        json={"email": "realuser@example.com", "password": "WrongPassword123!"},
    )
    assert resp_wrongpass.status_code == 401
    data_wrongpass = resp_wrongpass.json()

    # Verify contracts are strictly identical to prevent user enumeration
    expected_body = {
        "success": False,
        "code": "INVALID_CREDENTIALS",
        "message": "Invalid email or password.",
    }
    assert data_nonexistent == expected_body
    assert data_wrongpass == expected_body


def test_weak_password_returns_400_with_details(client: TestClient):
    """Verify weak password returns 400 Bad Request with rule validation details."""
    payload = {
        "email": "weakpwd@example.com",
        "username": "weakpwd",
        "password": "weak",  # missing minLength, uppercase, number, specialChar
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["success"] is False
    assert data["code"] == "WEAK_PASSWORD"
    assert data["message"] == "Password does not meet security requirements."
    assert "details" in data
    assert data["details"]["minLength"] is False
    assert data["details"]["uppercase"] is False
    assert data["details"]["specialCharacter"] is False


def test_rate_limiting_triggers_429(client: TestClient):
    """Verify exceeding rate limit triggers 429 Too Many Requests."""
    limiter.enabled = True
    try:
        # Send requests past rate limit threshold (5 per minute)
        responses = []
        for i in range(7):
            resp = client.post(
                "/api/v1/auth/login",
                json={"email": f"rate{i}@example.com", "password": "WrongPassword123!"},
            )
            responses.append(resp)

        rate_limited = [r for r in responses if r.status_code == 429]
        assert len(rate_limited) > 0
        data = rate_limited[0].json()
        assert data["code"] == "RATE_LIMIT_EXCEEDED"
    finally:
        limiter.enabled = False


def test_crud_race_condition_integrity_error(db_session):
    """Verify CRUD handles concurrent signup DB IntegrityError by raising EmailAlreadyRegisteredException."""
    from app.core.exceptions import EmailAlreadyRegisteredException

    user_in1 = UserCreate(email="race@example.com", username="race1", password="ValidPassword123!")
    user_in2 = UserCreate(email="RACE@example.com", username="race2", password="ValidPassword123!")

    crud.create_user(db_session, user_in1)

    with pytest.raises(EmailAlreadyRegisteredException):
        crud.create_user(db_session, user_in2)
