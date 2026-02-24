"""Unit tests for secret sanitizer."""

from wfc.shared.logging.sanitizer import sanitize_message


class TestSecretSanitizer:
    """Test secret sanitization."""

    def test_sanitize_wfc_api_key(self):
        """Test sanitization of wfc_ prefixed API keys."""
        message = "API key is wfc_1234567890abcdef"
        result = sanitize_message(message)
        assert result == "API key is [REDACTED]"

    def test_sanitize_sk_api_key(self):
        """Test sanitization of sk_ prefixed API keys."""
        message = "Using key sk_test_1234567890"
        result = sanitize_message(message)
        assert result == "Using key [REDACTED]"

    def test_sanitize_bearer_token(self):
        """Test sanitization of Bearer tokens."""
        message = "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        result = sanitize_message(message)
        assert result == "Authorization: [REDACTED]"

    def test_sanitize_wfc_directory_path(self):
        """Test sanitization of .wfc/ directory paths."""
        message = "Config at /home/user/.wfc/config.json"
        result = sanitize_message(message)
        assert result == "Config at [REDACTED_PATH]"

    def test_sanitize_jwt_token(self):
        """Test sanitization of JWT tokens."""
        message = "Token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"  # pragma: allowlist secret
        result = sanitize_message(message)
        assert result == "Token: [REDACTED]"

    def test_sanitize_newline_injection(self):
        """Test escaping of newline characters to prevent log injection."""
        message = "User input: line1\nline2"
        result = sanitize_message(message)
        assert result == "User input: line1\\nline2"

    def test_sanitize_carriage_return(self):
        """Test escaping of carriage return characters."""
        message = "Input: data\rmalicious"
        result = sanitize_message(message)
        assert result == "Input: data\\rmalicious"

    def test_sanitize_multiple_secrets(self):
        """Test sanitization of multiple secrets in one message."""
        message = "Keys: wfc_abc123 and sk_xyz789"
        result = sanitize_message(message)
        assert result == "Keys: [REDACTED] and [REDACTED]"

    def test_sanitize_mixed_secrets_and_injection(self):
        """Test sanitization of both secrets and injection attempts."""
        message = "API key wfc_secret\nBearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
        result = sanitize_message(message)
        assert result == "API key [REDACTED]\\n[REDACTED]"

    def test_sanitize_control_characters(self):
        """Test escaping of control characters."""
        message = "Data: \x00\x01\x02"
        result = sanitize_message(message)
        assert "\x00" not in result
        assert "\x01" not in result
        assert "\x02" not in result

    def test_no_secrets_unchanged(self):
        """Test that messages without secrets are unchanged."""
        message = "This is a normal log message"
        result = sanitize_message(message)
        assert result == message

    def test_sanitize_windows_path_with_wfc(self):
        """Test sanitization of Windows-style paths containing .wfc."""
        message = "Config at C:\\Users\\user\\.wfc\\config.json"
        result = sanitize_message(message)
        assert result == "Config at [REDACTED_PATH]"

    def test_sanitize_partial_jwt(self):
        """Test that partial JWT tokens are not redacted (only complete JWTs)."""
        message = "Partial: eyJhbGciOiJIUzI1NiIsInR5cCI.incomplete"
        result = sanitize_message(message)
        assert result == message

    def test_sanitize_empty_string(self):
        """Test sanitization of empty string."""
        message = ""
        result = sanitize_message(message)
        assert result == ""

    def test_sanitize_none_value(self):
        """Test sanitization of None value."""
        message = None
        result = sanitize_message(message)
        assert result == ""
