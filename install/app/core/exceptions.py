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


# Application-level exceptions

class LLMingsError(Exception):
    """Base exception for LLMings application errors."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class ValidationError(LLMingsError):
    """Raised when input validation fails."""

    def __init__(self, message: str, field: str | None = None):
        self.field = field
        super().__init__(message, status_code=400)


class NotFoundError(LLMingsError):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str, identifier: str | None = None):
        self.resource = resource
        self.identifier = identifier
        message = f"{resource} not found" if not identifier else f"{resource} '{identifier}' not found"
        super().__init__(message, status_code=404)


class ConfigurationError(LLMingsError):
    """Raised when there's a configuration issue."""

    def __init__(self, message: str):
        super().__init__(message, status_code=500)


class SessionError(LLMingsError):
    """Raised when there's an error with a council session."""

    def __init__(self, message: str, session_id: str | None = None):
        self.session_id = session_id
        super().__init__(message, status_code=400)
