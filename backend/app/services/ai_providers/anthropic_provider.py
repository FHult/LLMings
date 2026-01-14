"""Anthropic (Claude) provider implementation."""
from anthropic import AsyncAnthropic, APIError, RateLimitError as AnthropicRateLimitError, AuthenticationError as AnthropicAuthError
from typing import AsyncGenerator

from .base import AIProvider
from app.core.constants import PRICING, PROVIDER_CONFIGS
from app.core.exceptions import (
    AIProviderError,
    RateLimitError,
    AuthenticationError,
    ModelNotFoundError,
    ContextLengthError,
    ContentFilterError,
    TimeoutError,
    ServiceUnavailableError,
)


class AnthropicProvider(AIProvider):
    """Anthropic Claude API provider."""

    def __init__(self, api_key: str, model: str | None = None):
        """Initialize Anthropic provider."""
        super().__init__(api_key, model)
        self.client = AsyncAnthropic(api_key=api_key)
        self.name = "anthropic"

    async def stream_completion(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        image_data: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream completion from Anthropic."""
        try:
            async with self.client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt if system_prompt else "",
                messages=[
                    {"role": "user", "content": prompt}
                ],
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except AnthropicRateLimitError as e:
            raise RateLimitError(str(e), provider="anthropic")
        except AnthropicAuthError as e:
            raise AuthenticationError(str(e), provider="anthropic")
        except APIError as e:
            error_message = str(e).lower()
            if "model" in error_message and "not found" in error_message:
                raise ModelNotFoundError(self.model, provider="anthropic")
            elif "context" in error_message or "too long" in error_message:
                raise ContextLengthError(str(e), provider="anthropic")
            elif "content" in error_message and ("blocked" in error_message or "filter" in error_message):
                raise ContentFilterError(str(e), provider="anthropic")
            elif "timeout" in error_message:
                raise TimeoutError(str(e), provider="anthropic")
            elif "overloaded" in error_message or "unavailable" in error_message:
                raise ServiceUnavailableError(str(e), provider="anthropic")
            else:
                raise AIProviderError(f"Anthropic API error: {str(e)}", provider="anthropic")
        except Exception as e:
            raise AIProviderError(f"Anthropic error: {str(e)}", provider="anthropic")

    def count_tokens(self, text: str) -> int:
        """
        Count tokens using Claude's tokenizer.
        Note: This is an approximation. For exact counts, use Anthropic's count_tokens API.
        """
        try:
            # Rough estimate: Claude uses ~4 characters per token on average
            return len(text) // 4
        except Exception:
            return len(text) // 4

    def get_default_model(self) -> str:
        """Get default Anthropic model."""
        return PROVIDER_CONFIGS["anthropic"]["default_model"]

    def get_pricing(self) -> tuple[float, float]:
        """Get Anthropic pricing."""
        key = f"anthropic:{self.model}"
        # Default to Sonnet 4 pricing if model not found
        return PRICING.get(key, (3.0, 15.0))
