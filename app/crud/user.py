from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import EmailAlreadyRegisteredException
from app.core.security import hash_password, verify_password
from app.core.validators import normalize_email
from app.models.user import User
from app.schemas.user import UserCreate

# Dummy hash for timing attack mitigation when user is not found
DUMMY_HASH = "$argon2id$v=19$m=65536,t=2,p=1$c29tZXNhbHQ$RkJkYXA4YnB2YU02bW5xU213YXRnZ3d6Z2tvdnN5Z2E"


def get_user_by_email(db: Session, email: str) -> User | None:
    """Fetch a user by email address after normalizing the input email."""
    normalized = normalize_email(email)
    if not normalized:
        return None
    return db.query(User).filter(User.email == normalized).first()


def get_user_by_username(db: Session, username: str) -> User | None:
    """Fetch a user by username."""
    if not username:
        return None
    return db.query(User).filter(User.username == username.strip()).first()


def get_user_by_id(db: Session, user_id: str) -> User | None:
    """Fetch a user by UUID."""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, user_in: UserCreate) -> User:
    """Create and persist a new user with normalized email and hashed password.

    Handles concurrent DB unique constraint violations gracefully by rolling back
    and raising EmailAlreadyRegisteredException.
    """
    normalized_email = normalize_email(user_in.email)

    # 1. Application-level check
    if get_user_by_email(db, normalized_email):
        raise EmailAlreadyRegisteredException()

    db_user = User(
        email=normalized_email,
        username=user_in.username.strip(),
        hashed_password=hash_password(user_in.password),
    )

    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        # Race condition: concurrent signup created user between check and commit
        raise EmailAlreadyRegisteredException()


def authenticate_user(db: Session, email: str, password: str) -> User | None:
    """Authenticate user with email and password.

    Mitigates timing attacks by executing password verification even if user does not exist.
    """
    normalized_email = normalize_email(email)
    user = get_user_by_email(db, normalized_email)

    if not user:
        # Perform dummy verification to maintain constant-time response characteristics
        verify_password(password, DUMMY_HASH)
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user
