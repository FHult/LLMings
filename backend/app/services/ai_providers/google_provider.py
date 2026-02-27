"""Google (Gemini) provider — uses the google-genai SDK (replaces google-generativeai)."""
from google import genai
from google.genai import types, errors as genai_errors
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
    """Google Gemini API provider using the google-genai SDK."""

    def __init__(self, api_key: str, model: str | None = None):
        """Initialize Google provider."""
        super().__init__(api_key, model)
        self._client = genai.Client(api_key=api_key)
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
            config = types.GenerateContentConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )
            if system_prompt:
                config.system_instruction = system_prompt

            async for chunk in await self._client.aio.models.generate_content_stream(
                model=self.model,
                contents=prompt,
                config=config,
            ):
                if chunk.text:
                    yield chunk.text

        except genai_errors.APIError as e:
            code = e.code
            msg = e.message if hasattr(e, "message") else str(e)
            msg_lower = msg.lower()

            if code == 429:
                raise RateLimitError(msg, provider="google")
            elif code in (401, 403):
                raise AuthenticationError(msg, provider="google")
            elif code == 404:
                raise ModelNotFoundError(self.model, provider="google")
            elif code == 400:
                if any(kw in msg_lower for kw in ("token", "length", "too long", "context")):
                    raise ContextLengthError(msg, provider="google")
                if any(kw in msg_lower for kw in ("safety", "blocked", "filter")):
                    raise ContentFilterError(msg, provider="google")
                raise AIProviderError(f"Google API error: {msg}", provider="google")
            elif code == 503:
                raise ServiceUnavailableError(msg, provider="google")
            else:
                raise AIProviderError(f"Google API error ({code}): {msg}", provider="google")

        except Exception as e:
            error_msg = str(e).lower()
            if any(kw in error_msg for kw in ("safety", "blocked", "filter")):
                raise ContentFilterError(str(e), provider="google")
            raise AIProviderError(f"Google error: {str(e)}", provider="google")

    def supports_vision(self) -> bool:
        """All current Gemini models support vision."""
        return True

    def count_tokens(self, text: str) -> int:
        """Rough token estimate (4 chars per token)."""
        return len(text) // 4

    def get_default_model(self) -> str:
        """Get default Google model."""
        return PROVIDER_CONFIGS["google"]["default_model"]

    def get_pricing(self) -> tuple[float, float]:
        """Get Google pricing (stored as $ per 1M tokens, matching the rest of the codebase)."""
        key = f"google:{self.model}"
        return PRICING.get(key, (0.30, 2.50))  # default: gemini-2.5-flash rates
