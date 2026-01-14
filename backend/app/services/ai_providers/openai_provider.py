"""OpenAI provider implementation."""
# import tiktoken  # Temporarily disabled - use fallback token counting
from openai import AsyncOpenAI, APIError, RateLimitError as OpenAIRateLimitError, AuthenticationError as OpenAIAuthError
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


class OpenAIProvider(AIProvider):
    """OpenAI API provider."""

    def __init__(self, api_key: str, model: str | None = None):
        """Initialize OpenAI provider."""
        super().__init__(api_key, model)
        self.client = AsyncOpenAI(api_key=api_key)
        self.name = "openai"

        # Tokenizer temporarily disabled - using fallback estimation
        # TODO: Re-enable tiktoken once Python 3.13 support is stable

    async def stream_completion(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        image_data: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream completion from OpenAI."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Build user message with optional image
        if image_data:
            messages.append({
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_data}"
                        }
                    }
                ]
            })
        else:
            messages.append({"role": "user", "content": prompt})

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except OpenAIRateLimitError as e:
            raise RateLimitError(str(e), provider="openai")
        except OpenAIAuthError as e:
            raise AuthenticationError(str(e), provider="openai")
        except APIError as e:
            # Parse specific error types from the API error
            error_message = str(e).lower()
            if "model" in error_message and ("not found" in error_message or "does not exist" in error_message):
                raise ModelNotFoundError(self.model, provider="openai")
            elif "context_length" in error_message or "maximum context" in error_message:
                raise ContextLengthError(str(e), provider="openai")
            elif "content_filter" in error_message or "content_policy" in error_message:
                raise ContentFilterError(str(e), provider="openai")
            elif "timeout" in error_message:
                raise TimeoutError(str(e), provider="openai")
            elif "service" in error_message and "unavailable" in error_message:
                raise ServiceUnavailableError(str(e), provider="openai")
            else:
                raise AIProviderError(f"OpenAI API error: {str(e)}", provider="openai")
        except Exception as e:
            raise AIProviderError(f"OpenAI error: {str(e)}", provider="openai")

    def supports_vision(self) -> bool:
        """Check if model supports vision."""
        # GPT-4o and GPT-4 Turbo support vision
        vision_models = {"gpt-4o", "gpt-4o-mini", "gpt-4-turbo"}
        return self.model in vision_models

    def count_tokens(self, text: str) -> int:
        """Count tokens using fallback estimation."""
        # Fallback: rough estimate (4 chars per token)
        # TODO: Re-enable tiktoken for accurate counting
        return len(text) // 4

    def get_default_model(self) -> str:
        """Get default OpenAI model."""
        return PROVIDER_CONFIGS["openai"]["default_model"]

    def get_pricing(self) -> tuple[float, float]:
        """Get OpenAI pricing."""
        key = f"openai:{self.model}"
        return PRICING.get(key, (5.0, 15.0))  # Default to gpt-4o pricing
