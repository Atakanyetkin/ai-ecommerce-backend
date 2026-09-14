import re
import string
from email_validator import EmailNotValidError, validate_email as validate_email_format

from app.core.exceptions import InvalidEmailException, WeakPasswordException

SPECIAL_CHARACTERS = set(string.punctuation)


def normalize_email(email: str) -> str:
    """Trim leading/trailing whitespace and convert email to lowercase."""
    if not email:
        return ""
    return email.strip().lower()


def validate_email(email: str) -> str:
    """Normalize and validate email format and length.

    Raises InvalidEmailException on validation failure.
    Returns normalized email string.
    """
    if not email or not email.strip():
        raise InvalidEmailException("Email address cannot be empty.")

    normalized = normalize_email(email)

    if len(normalized) > 254:
        raise InvalidEmailException("Email address exceeds maximum length of 254 characters.")

    try:
        # validate_email checks standard RFC format without restricting standard domains
        valid = validate_email_format(normalized, check_deliverability=False)
        return valid.normalized.lower()
    except EmailNotValidError as e:
        raise InvalidEmailException(f"Invalid email format: {str(e)}")


def validate_password_policy(password: str) -> None:
    """Enforce strict password strength requirements.

    Requirements:
    - At least 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    - At least 1 special character
    - Maximum length 128 characters

    Raises WeakPasswordException with structured details if policy is violated.
    """
    if not password:
        details = {
            "minLength": False,
            "uppercase": False,
            "lowercase": False,
            "number": False,
            "specialCharacter": False,
        }
        raise WeakPasswordException(details=details)

    if len(password) > 128:
        details = {
            "minLength": len(password) >= 8,
            "uppercase": any(c.isupper() for c in password),
            "lowercase": any(c.islower() for c in password),
            "number": any(c.isdigit() for c in password),
            "specialCharacter": any(c in SPECIAL_CHARACTERS for c in password),
        }
        raise WeakPasswordException(details=details)

    has_min_length = len(password) >= 8
    has_uppercase = any(c.isupper() for c in password)
    has_lowercase = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(c in SPECIAL_CHARACTERS for c in password)

    details = {
        "minLength": has_min_length,
        "uppercase": has_uppercase,
        "lowercase": has_lowercase,
        "number": has_digit,
        "specialCharacter": has_special,
    }

    if not all(details.values()):
        raise WeakPasswordException(details=details)
