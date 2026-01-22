"""Abstract base class for AI providers."""
from abc import ABC, abstractmethod
from typing import AsyncGenerator


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    def __init__(self, api_key: str, model: str | None = None):
        """Initialize provider with API key and optional model."""
        self.api_key = api_key
        self.model = model or self.get_default_model()
        self.name = self.__class__.__name__.replace("Provider", "").lower()

    @abstractmethod
    async def stream_completion(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        image_data: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream completion tokens from the AI provider.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            temperature: Temperature for response randomness
            max_tokens: Maximum tokens in response
            image_data: Optional base64 encoded image data for vision models

        Yields:
            str: Token strings as they arrive
        """
        pass

    def supports_vision(self) -> bool:
        """
        Check if this provider supports vision/image inputs.

        Returns:
            bool: True if provider supports vision
        """
        return False

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """
        Count tokens in text.

        Args:
            text: Text to count tokens for

        Returns:
            int: Approximate token count
        """
        pass

    @abstractmethod
    def get_default_model(self) -> str:
        """
        Get the default model name for this provider.

        Returns:
            str: Model name
        """
        pass

    @abstractmethod
    def get_pricing(self) -> tuple[float, float]:
        """
        Get pricing for this provider/model.

        Returns:
            tuple[float, float]: (input_price_per_1k, output_price_per_1k)
        """
        pass

    def get_model_name(self) -> str:
        """
        Get the current model name.

        Returns:
            str: Model name
        """
        return self.model

    def estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Estimate cost for a completion.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            float: Estimated cost in USD
        """
        input_price, output_price = self.get_pricing()
        cost = (input_tokens / 1000 * input_price) + (output_tokens / 1000 * output_price)
        return round(cost, 6)
