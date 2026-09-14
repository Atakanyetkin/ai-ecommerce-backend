import logging
import re
from typing import Any

SENSITIVE_PATTERNS = [
    (r'(?i)("?password"?\s*[:=]\s*["\'])([^"\']+)(["\'])', r'\1***MASKED***\3'),
    (r'(?i)("?hashed_password"?\s*[:=]\s*["\'])([^"\']+)(["\'])', r'\1***MASKED***\3'),
    (r'(?i)("?passwordHash"?\s*[:=]\s*["\'])([^"\']+)(["\'])', r'\1***MASKED***\3'),
    (r'(?i)("?token"?\s*[:=]\s*["\'])([^"\']+)(["\'])', r'\1***MASKED***\3'),
    (r'(?i)(Bearer\s+)[A-Za-z0-9\-\._~\+\/]+=*', r'\1***MASKED***'),
    (r'(?i)("?authorization"?\s*[:=]\s*["\'])([^"\']+)(["\'])', r'\1***MASKED***\3'),
]


def mask_sensitive_data(message: str) -> str:
    """Mask passwords, hashes, tokens, and authorization headers in string logs."""
    if not isinstance(message, str):
        message = str(message)
    for pattern, replacement in SENSITIVE_PATTERNS:
        message = re.sub(pattern, replacement, message)
    return message


class SensitiveDataFilter(logging.Filter):
    """Logging filter that sanitizes sensitive data from log record messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = mask_sensitive_data(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: mask_sensitive_data(str(v)) if "pass" in k.lower() or "token" in k.lower() else v
                    for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    mask_sensitive_data(str(arg)) if isinstance(arg, str) else arg
                    for arg in record.args
                )
        return True
