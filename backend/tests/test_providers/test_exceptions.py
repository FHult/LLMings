"""Test custom exception classes."""
import pytest
from app.core.exceptions import (
    AIProviderError,
    RateLimitError,
    AuthenticationError,
    ModelNotFoundError,
    ContextLengthError,
    ContentFilterError,
    ConnectionError,
    TimeoutError,
    InsufficientQuotaError,
    ServiceUnavailableError,
)


class TestExceptionHierarchy:
    """Test exception class hierarchy and attributes."""

    def test_base_exception_attributes(self):
        """Test AIProviderError has correct attributes."""
        error = AIProviderError("Test error", provider="openai")
        assert str(error) == "Test error"
        assert error.provider == "openai"

    def test_rate_limit_error(self):
        """Test RateLimitError with retry_after."""
        error = RateLimitError("Rate limited", provider="anthropic", retry_after=60)
        assert error.retry_after == 60
        assert error.provider == "anthropic"
        assert isinstance(error, AIProviderError)

    def test_authentication_error(self):
        """Test AuthenticationError."""
        error = AuthenticationError(provider="google")
        assert "Authentication failed" in str(error)
        assert error.provider == "google"

    def test_model_not_found_error(self):
        """Test ModelNotFoundError with model name."""
        error = ModelNotFoundError("gpt-5", provider="openai")
        assert error.model == "gpt-5"
        assert "gpt-5" in str(error)
        assert "not found" in str(error).lower()

    def test_context_length_error(self):
        """Test ContextLengthError with max_tokens."""
        error = ContextLengthError("Too long", provider="anthropic", max_tokens=100000)
        assert error.max_tokens == 100000
        assert error.provider == "anthropic"

    def test_content_filter_error(self):
        """Test ContentFilterError."""
        error = ContentFilterError(provider="openai")
        assert "blocked" in str(error).lower() or "filter" in str(error).lower()

    def test_timeout_error(self):
        """Test TimeoutError with timeout_seconds."""
        error = TimeoutError("Request timed out", provider="ollama", timeout_seconds=30)
        assert error.timeout_seconds == 30
        assert error.provider == "ollama"

    def test_all_exceptions_inherit_from_base(self):
        """Test all exceptions inherit from AIProviderError."""
        exception_classes = [
            RateLimitError,
            AuthenticationError,
            ModelNotFoundError,
            ContextLengthError,
            ContentFilterError,
            ConnectionError,
            TimeoutError,
            InsufficientQuotaError,
            ServiceUnavailableError,
        ]
        for exc_class in exception_classes:
            assert issubclass(exc_class, AIProviderError), f"{exc_class} should inherit from AIProviderError"
