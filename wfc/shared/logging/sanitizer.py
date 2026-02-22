"""Secret sanitizer for logging.

Detects and redacts sensitive information from log messages to prevent
accidental exposure of credentials, tokens, and other secrets.
"""

import re
from typing import Optional

PATTERNS = {
    "api_key": re.compile(r"\b(wfc|sk)_[a-zA-Z0-9_]+"),
    "bearer": re.compile(r"Bearer\s+[a-zA-Z0-9\-._~+/]+=*", re.IGNORECASE),
    "jwt": re.compile(r"\beyJ[a-zA-Z0-9\-_]+\.eyJ[a-zA-Z0-9\-_]+\.[a-zA-Z0-9\-_]+"),
    "wfc_path": re.compile(
        r"[a-zA-Z]:[\\\/](?:[^\\\/\s]+[\\\/])*\.wfc[\\\/][^\s]*|[\/](?:[^\/\s]+[\/])*\.wfc[\/][^\s]*"
    ),
}

CONTROL_CHARS = {
    "\n": "\\n",
    "\r": "\\r",
    "\t": "\\t",
}


def sanitize_message(message: Optional[str]) -> str:
    """Sanitize a log message by redacting secrets and escaping control characters.

    Args:
        message: The log message to sanitize. Can be None.

    Returns:
        Sanitized message with secrets redacted and control characters escaped.

    Examples:
        >>> sanitize_message("API key: wfc_abc123")
        'API key: [REDACTED]'

        >>> sanitize_message("Path: /home/user/.wfc/config.json")
        'Path: [REDACTED_PATH]'

        >>> sanitize_message("Log line 1\\nLog line 2")
        'Log line 1\\\\nLog line 2'
    """
    if message is None:
        return ""

    if not message:
        return message

    result = message

    result = PATTERNS["wfc_path"].sub("[REDACTED_PATH]", result)

    result = PATTERNS["api_key"].sub("[REDACTED]", result)

    result = PATTERNS["bearer"].sub("[REDACTED]", result)

    result = PATTERNS["jwt"].sub("[REDACTED]", result)

    for char, escaped in CONTROL_CHARS.items():
        result = result.replace(char, escaped)

    result = "".join(
        char if (ord(char) >= 32 or char in "\t\n\r") else f"\\x{ord(char):02x}" for char in result
    )

    return result
