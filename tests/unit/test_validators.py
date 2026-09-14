import pytest

from app.core.exceptions import InvalidEmailException, WeakPasswordException
from app.core.logging import mask_sensitive_data
from app.core.security import hash_password, verify_password
from app.core.validators import normalize_email, validate_email, validate_password_policy


# ── 1. Email Normalization & Validation Unit Tests ─────────────────────────

def test_normalize_email_trim_and_lowercase():
    """Verify email is trimmed of whitespace and lowercased."""
    raw_emails = [
        ("  User@Example.COM  ", "user@example.com"),
        ("TEST.USER@GMAIL.COM\n", "test.user@gmail.com"),
        ("\tAdmin@Hotmail.Com ", "admin@hotmail.com"),
    ]
    for raw, expected in raw_emails:
        assert normalize_email(raw) == expected


def test_validate_email_standard_domains():
    """Verify standard valid email formats and domains are accepted."""
    valid_emails = [
        "john.doe@gmail.com",
        "alice@hotmail.com",
        "bob@outlook.com",
        "user@icloud.com",
        "dev@company.co.uk",
    ]
    for email in valid_emails:
        assert validate_email(email) == email.lower()


def test_validate_email_invalid_formats():
    """Verify invalid format, empty, and overly long emails raise InvalidEmailException."""
    invalid_emails = [
        "",
        "   ",
        "plainaddress",
        "@missingusername.com",
        "username@.com",
        "user@domain..com",
        "a" * 250 + "@example.com",  # Exceeds max length
    ]
    for email in invalid_emails:
        with pytest.raises(InvalidEmailException):
            validate_email(email)


# ── 2. Password Policy Unit Tests ─────────────────────────────────────────

def test_password_policy_all_rules_pass():
    """Valid password passing all policy criteria."""
    valid_passwords = [
        "StrongP@ss123",
        "C0mplex#Pass2026",
        "Valid!99Secure",
    ]
    for pwd in valid_passwords:
        # Should not raise exception
        validate_password_policy(pwd)


def test_password_policy_each_rule_fail():
    """Verify failure of each individual password rule produces expected details."""
    scenarios = [
        # (Password, expected_details)
        ("Short1!", {"minLength": False, "uppercase": True, "lowercase": True, "number": True, "specialCharacter": True}),
        ("lowercase1!", {"minLength": True, "uppercase": False, "lowercase": True, "number": True, "specialCharacter": True}),
        ("UPPERCASE1!", {"minLength": True, "uppercase": True, "lowercase": False, "number": True, "specialCharacter": True}),
        ("NoNumber!!", {"minLength": True, "uppercase": True, "lowercase": True, "number": False, "specialCharacter": True}),
        ("NoSpecial123", {"minLength": True, "uppercase": True, "lowercase": True, "number": True, "specialCharacter": False}),
    ]
    for pwd, expected_details in scenarios:
        with pytest.raises(WeakPasswordException) as exc_info:
            validate_password_policy(pwd)
        assert exc_info.value.details == expected_details


# ── 3. Password Hashing & Verification Unit Tests ─────────────────────────

def test_password_hashing_not_plaintext():
    """Verify hashed password is not stored as plain text."""
    plain = "SuperSecret123!"
    hashed = hash_password(plain)

    assert hashed != plain
    assert not hashed.startswith(plain)
    assert len(hashed) > 30


def test_password_verification():
    """Verify password verification succeeds for correct password and fails for incorrect."""
    plain = "SecureP@ss2026"
    hashed = hash_password(plain)

    assert verify_password(plain, hashed) is True
    assert verify_password("WrongP@ss2026", hashed) is False
    assert verify_password("", hashed) is False


# ── 4. Log Masking Unit Test ───────────────────────────────────────────────

def test_sensitive_data_log_masking():
    """Verify passwords, hashes, and authorization tokens are masked in log messages."""
    log_messages = [
        ('User login attempt with password: "SuperSecret123!"', '***MASKED***'),
        ('hashed_password="hashed_val_xyz_123"', '***MASKED***'),
        ('Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0In0.xyz', '***MASKED***'),
    ]
    for raw_msg, expected_substring in log_messages:
        masked = mask_sensitive_data(raw_msg)
        assert "SuperSecret123!" not in masked
        assert "hashed_val_xyz_123" not in masked
        assert expected_substring in masked
