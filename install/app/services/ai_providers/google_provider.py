"""Google (Gemini) provider implementation."""
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
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
    ServiceUnavailableError,
)


class GoogleProvider(AIProvider):
    """Google Gemini API provider."""

    def __init__(self, api_key: str, model: str | None = None):
        """Initialize Google provider."""
        super().__init__(api_key, model)
        genai.configure(api_key=api_key)
        self.name = "google"

    async def stream_completion(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        image_data: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream completion from Google Gemini."""
        try:
            # Create model instance
            model = genai.GenerativeModel(
                model_name=self.model,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                }
            )

            # Combine system prompt and user prompt if system prompt provided
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\nUser: {prompt}"

            # Generate content with streaming
            response = await model.generate_content_async(
                full_prompt,
                stream=True
            )

            async for chunk in response:
                if chunk.text:
                    yield chunk.text

        except google_exceptions.ResourceExhausted as e:
            raise RateLimitError(str(e), provider="google")
        except google_exceptions.Unauthenticated as e:
            raise AuthenticationError(str(e), provider="google")
        except google_exceptions.PermissionDenied as e:
            raise AuthenticationError(str(e), provider="google")
        except google_exceptions.NotFound as e:
            raise ModelNotFoundError(self.model, provider="google")
        except google_exceptions.InvalidArgument as e:
            error_msg = str(e).lower()
            if "token" in error_msg or "length" in error_msg or "too long" in error_msg:
                raise ContextLengthError(str(e), provider="google")
            raise AIProviderError(f"Google API error: {str(e)}", provider="google")
        except google_exceptions.ServiceUnavailable as e:
            raise ServiceUnavailableError(str(e), provider="google")
        except Exception as e:
            error_msg = str(e).lower()
            if "safety" in error_msg or "blocked" in error_msg:
                raise ContentFilterError(str(e), provider="google")
            raise AIProviderError(f"Google API error: {str(e)}", provider="google")

    def count_tokens(self, text: str) -> int:
        """
        Count tokens for Google models.
        Note: This is an approximation. Google has a count_tokens API for exact counts.
        """
        try:
            # Rough estimate: ~4 characters per token
            return len(text) // 4
        except Exception:
            return len(text) // 4

    def get_default_model(self) -> str:
        """Get default Google model."""
        return PROVIDER_CONFIGS["google"]["default_model"]

    def get_pricing(self) -> tuple[float, float]:
        """Get Google pricing."""
        key = f"google:{self.model}"
        # Default to Gemini 1.5 Pro pricing if model not found
        return PRICING.get(key, (1.25, 5.0))
