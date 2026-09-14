import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.core.validators import normalize_email, validate_password_policy


# ── Request schemas ─────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    """Payload for registering a new user."""

    email: EmailStr
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_field(cls, v: Any) -> str:
        if isinstance(v, str):
            return normalize_email(v)
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        validate_password_policy(v)
        return v


class UserLogin(BaseModel):
    """Payload for logging in (email + password)."""

    email: EmailStr
    password: str

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email_field(cls, v: Any) -> str:
        if isinstance(v, str):
            return normalize_email(v)
        return v


class RefreshTokenRequest(BaseModel):
    """Payload for requesting a new access token via refresh token."""

    refresh_token: str


# ── Response schemas ─────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    """Public representation of a user (sensitive fields strictly omitted)."""

    id: uuid.UUID
    email: str
    username: str
    is_active: bool
    is_superuser: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class Token(BaseModel):
    """JWT token pair returned after login/register."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class AccessToken(BaseModel):
    """Single access token (returned after refresh)."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data extracted from a decoded JWT payload."""

    sub: str | None = None
    type: str | None = None


# ── Standardized Error Response Schemas ─────────────────────────────────────

class ErrorResponse(BaseModel):
    """Standard error envelope returned by the API."""

    success: bool = False
    code: str
    message: str
    details: dict[str, Any] | None = None
