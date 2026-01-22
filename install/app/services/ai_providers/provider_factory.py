"""Factory for creating AI provider instances."""
from .base import AIProvider
from .openai_provider import OpenAIProvider
from .anthropic_provider import AnthropicProvider
from .google_provider import GoogleProvider
from .grok_provider import GrokProvider
from .ollama_provider import OllamaProvider
from app.core.config import settings
from app.core.constants import PROVIDER_CONFIGS


class ProviderFactory:
    """Factory for creating and managing AI providers."""

    def __init__(self, model_configs: dict[str, str] | None = None):
        """
        Initialize provider factory.

        Args:
            model_configs: Optional dict mapping provider name to model name.
                          If not provided, uses defaults from settings or PROVIDER_CONFIGS.
        """
        self._providers: dict[str, AIProvider] = {}
        self._model_configs = model_configs or {}
        self._initialize_providers()

    def _get_model_for_provider(self, provider_name: str) -> str | None:
        """
        Get the model to use for a provider.

        Priority:
        1. Model from model_configs parameter (runtime)
        2. Model from settings (environment variable)
        3. Default model from PROVIDER_CONFIGS
        """
        # Check runtime config
        if provider_name in self._model_configs:
            return self._model_configs[provider_name]

        # Check settings
        model_attr = f"{provider_name}_model"
        if hasattr(settings, model_attr):
            model = getattr(settings, model_attr)
            if model:
                return model

        # Return None to use provider default
        return None

    def _initialize_providers(self):
        """Initialize all configured providers with their models."""
        if settings.openai_api_key:
            model = self._get_model_for_provider("openai")
            self._providers["openai"] = OpenAIProvider(settings.openai_api_key, model)

        if settings.anthropic_api_key:
            model = self._get_model_for_provider("anthropic")
            self._providers["anthropic"] = AnthropicProvider(settings.anthropic_api_key, model)

        if settings.google_api_key:
            model = self._get_model_for_provider("google")
            self._providers["google"] = GoogleProvider(settings.google_api_key, model)

        if settings.grok_api_key:
            model = self._get_model_for_provider("grok")
            self._providers["grok"] = GrokProvider(settings.grok_api_key, model)

        # Ollama is always available (local, no API key needed)
        model = self._get_model_for_provider("ollama")
        base_url = getattr(settings, "ollama_base_url", "http://localhost:11434")
        self._providers["ollama"] = OllamaProvider("not-needed", model, base_url)

    def get_provider(self, name: str) -> AIProvider:
        """
        Get a provider by name.

        Args:
            name: Provider name (e.g., 'openai')

        Returns:
            AIProvider: The provider instance

        Raises:
            ValueError: If provider not found or not configured
        """
        if name not in self._providers:
            raise ValueError(f"Provider '{name}' not found or not configured")
        return self._providers[name]

    def get_all_providers(self) -> list[AIProvider]:
        """
        Get all configured providers.

        Returns:
            list[AIProvider]: List of all providers
        """
        return list(self._providers.values())

    def get_provider_names(self) -> list[str]:
        """
        Get names of all configured providers.

        Returns:
            list[str]: List of provider names
        """
        return list(self._providers.keys())

    def is_provider_configured(self, name: str) -> bool:
        """
        Check if a provider is configured.

        Args:
            name: Provider name

        Returns:
            bool: True if provider is configured
        """
        return name in self._providers

    def get_available_models(self, provider_name: str) -> list[str]:
        """
        Get available models for a provider.

        Args:
            provider_name: Provider name

        Returns:
            list[str]: List of available model names
        """
        if provider_name in PROVIDER_CONFIGS:
            return PROVIDER_CONFIGS[provider_name].get("available_models", [])
        return []
