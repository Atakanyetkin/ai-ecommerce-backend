from typing import Any


class BaseAuthException(Exception):
    """Base exception class for authentication and authorization errors."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
    ):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        super().__init__(message)


class WeakPasswordException(BaseAuthException):
    """Raised when password policy validation fails."""

    def __init__(self, details: dict[str, bool]):
        super().__init__(
            status_code=400,
            code="WEAK_PASSWORD",
            message="Password does not meet security requirements.",
            details=details,
        )


class EmailAlreadyRegisteredException(BaseAuthException):
    """Raised when signup is attempted with an existing email (409 Conflict)."""

    def __init__(self):
        super().__init__(
            status_code=409,
            code="EMAIL_ALREADY_REGISTERED",
            message="An account with this email already exists.",
        )


class InvalidCredentialsException(BaseAuthException):
    """Raised when email is not found or password is incorrect (401 Unauthorized)."""

    def __init__(self):
        super().__init__(
            status_code=401,
            code="INVALID_CREDENTIALS",
            message="Invalid email or password.",
        )


class InvalidEmailException(BaseAuthException):
    """Raised when email format validation fails (400 Bad Request)."""

    def __init__(self, message: str = "Invalid email address format."):
        super().__init__(
            status_code=400,
            code="INVALID_EMAIL",
            message=message,
        )
