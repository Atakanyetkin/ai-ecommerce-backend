from fastapi import APIRouter, Depends, Request, status
from jose import JWTError
from sqlalchemy.orm import Session

from app import crud
from app.api.v1.deps import get_current_active_user
from app.core.config import settings
from app.core.exceptions import (
    EmailAlreadyRegisteredException,
    InvalidCredentialsException,
)
from app.core.rate_limiter import limiter
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import AccessToken, RefreshTokenRequest, Token, UserCreate, UserLogin, UserResponse

router = APIRouter()


@router.post(
    "/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
def register(
    request: Request,
    user_in: UserCreate,
    db: Session = Depends(get_db),
) -> Token:
    """Create a new user account with normalized email and strong password validation.

    Returns a JWT token pair on successful creation.
    Raises 409 Conflict if email is already registered.
    """
    # Double check username conflict
    if crud.get_user_by_username(db, username=user_in.username):
        raise EmailAlreadyRegisteredException()

    user = crud.create_user(db, user_in)
    return Token(
        access_token=create_access_token({"sub": user.email}),
        refresh_token=create_refresh_token({"sub": user.email}),
    )


@router.post(
    "/login",
    response_model=Token,
    summary="Login with email and password",
)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
def login(
    request: Request,
    credentials: UserLogin,
    db: Session = Depends(get_db),
) -> Token:
    """Authenticate user with email and password.

    Returns generic 401 INVALID_CREDENTIALS for non-existent user or invalid password
    to prevent user enumeration.
    """
    user = crud.authenticate_user(db, email=credentials.email, password=credentials.password)
    if not user or not user.is_active:
        raise InvalidCredentialsException()

    return Token(
        access_token=create_access_token({"sub": user.email}),
        refresh_token=create_refresh_token({"sub": user.email}),
    )


@router.post(
    "/refresh",
    response_model=AccessToken,
    summary="Refresh access token",
)
def refresh_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)) -> AccessToken:
    """Exchange a valid refresh token for a new access token."""
    try:
        data = decode_token(payload.refresh_token)
        sub: str | None = data.get("sub")
        token_type: str | None = data.get("type")
        if sub is None or token_type != "refresh":
            raise InvalidCredentialsException()
    except JWTError:
        raise InvalidCredentialsException()

    user = crud.get_user_by_email(db, email=sub)
    if not user or not user.is_active:
        raise InvalidCredentialsException()

    return AccessToken(access_token=create_access_token({"sub": user.email}))


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
)
def get_me(current_user: User = Depends(get_current_active_user)) -> UserResponse:
    """Return the profile of the currently authenticated user."""
    return current_user
