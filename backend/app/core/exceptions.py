"""Custom exception classes for AI provider errors."""


class AIProviderError(Exception):
    """Base exception for AI provider errors."""

    def __init__(self, message: str, provider: str | None = None):
        self.provider = provider
        super().__init__(message)


class RateLimitError(AIProviderError):
    """Raised when the API rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded", provider: str | None = None, retry_after: int | None = None):
        self.retry_after = retry_after
        super().__init__(message, provider)


class AuthenticationError(AIProviderError):
    """Raised when API authentication fails (invalid API key)."""

    def __init__(self, message: str = "Authentication failed - check your API key", provider: str | None = None):
        super().__init__(message, provider)


class ModelNotFoundError(AIProviderError):
    """Raised when the specified model is not available."""

    def __init__(self, model: str, provider: str | None = None):
        self.model = model
        super().__init__(f"Model '{model}' not found", provider)


class ContextLengthError(AIProviderError):
    """Raised when the input exceeds the model's context length."""

    def __init__(self, message: str = "Input exceeds model's context length", provider: str | None = None, max_tokens: int | None = None):
        self.max_tokens = max_tokens
        super().__init__(message, provider)


class ContentFilterError(AIProviderError):
    """Raised when content is blocked by the provider's content filter."""

    def __init__(self, message: str = "Content blocked by safety filter", provider: str | None = None):
        super().__init__(message, provider)


class ConnectionError(AIProviderError):
    """Raised when unable to connect to the provider's API."""

    def __init__(self, message: str = "Unable to connect to API", provider: str | None = None):
        super().__init__(message, provider)


class TimeoutError(AIProviderError):
    """Raised when the API request times out."""

    def __init__(self, message: str = "Request timed out", provider: str | None = None, timeout_seconds: int | None = None):
        self.timeout_seconds = timeout_seconds
        super().__init__(message, provider)


class InsufficientQuotaError(AIProviderError):
    """Raised when the account has insufficient quota/credits."""

    def __init__(self, message: str = "Insufficient quota or credits", provider: str | None = None):
        super().__init__(message, provider)


class ServiceUnavailableError(AIProviderError):
    """Raised when the provider's service is temporarily unavailable."""

    def __init__(self, message: str = "Service temporarily unavailable", provider: str | None = None):
        super().__init__(message, provider)
