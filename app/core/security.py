from datetime import datetime, timedelta, timezone
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Argon2id hasher
argon2_hasher = PasswordHasher(
    time_cost=settings.ARGON2_TIME_COST,
    memory_cost=settings.ARGON2_MEMORY_COST,
    parallelism=settings.ARGON2_PARALLELISM,
)

# Bcrypt context fallback
bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain-text password using Argon2id or Bcrypt based on configuration.

    The password is NEVER stored or logged in plain text.
    """
    if settings.HASH_ALGORITHM.lower() == "argon2":
        return argon2_hasher.hash(password)
    return bcrypt_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a hashed password using timing-safe comparison.

    Supports both Argon2id hashes and Bcrypt hashes for backward compatibility.
    """
    if not hashed_password:
        return False

    # Check if hash is Argon2
    if hashed_password.startswith("$argon2"):
        try:
            return argon2_hasher.verify(hashed_password, plain_password)
        except (VerifyMismatchError, VerificationError, InvalidHashError):
            return False
    else:
        try:
            return bcrypt_context.verify(plain_password, hashed_password)
        except Exception:
            return False


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Create a short-lived JWT access token without sensitive payload data."""
    to_encode = data.copy()
    # Strip any potential sensitive fields from payload
    to_encode.pop("password", None)
    to_encode.pop("hashed_password", None)
    to_encode.pop("passwordHash", None)

    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: dict[str, Any]) -> str:
    """Create a long-lived JWT refresh token without sensitive payload data."""
    to_encode = data.copy()
    to_encode.pop("password", None)
    to_encode.pop("hashed_password", None)
    to_encode.pop("passwordHash", None)

    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT token. Raises JWTError on failure."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
