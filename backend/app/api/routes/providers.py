"""Provider API routes."""
import asyncio
import logging
from fastapi import APIRouter, HTTPException

from app.services.ai_providers import ProviderFactory
from app.core.constants import PROVIDER_CONFIGS

logger = logging.getLogger(__name__)
router = APIRouter()

# Module-level cache: avoid reconstructing ProviderFactory (which loads API keys
# and initialises SDK clients) on every GET /providers request.
_factory_cache: ProviderFactory | None = None
_factory_lock = asyncio.Lock()


async def _get_factory() -> ProviderFactory:
    global _factory_cache
    async with _factory_lock:
        if _factory_cache is None:
            _factory_cache = ProviderFactory()
    return _factory_cache


@router.get("/providers")
async def get_providers():
    """
    Get list of configured providers and their available models.

    Returns:
        dict: Provider configuration information
    """
    factory = await _get_factory()

    providers_info = {}
    for provider_name in factory.get_provider_names():
        provider = factory.get_provider(provider_name)
        available_models = PROVIDER_CONFIGS[provider_name].get("available_models", [])
        default_model = PROVIDER_CONFIGS[provider_name].get("default_model")

        # For Ollama, get actually installed models
        if provider_name == "ollama" and hasattr(provider, 'list_available_models'):
            try:
                available_models = await provider.list_available_models()
            except Exception as e:
                logger.warning(f"Error getting Ollama models: {e}")
                available_models = []

        providers_info[provider_name] = {
            "name": provider_name,
            "current_model": provider.get_model_name(),
            "default_model": default_model,
            "available_models": available_models,
            "configured": True,
        }

    # Add unconfigured providers
    for provider_name, config in PROVIDER_CONFIGS.items():
        if provider_name not in providers_info:
            providers_info[provider_name] = {
                "name": provider_name,
                "current_model": None,
                "default_model": config.get("default_model"),
                "available_models": config.get("available_models", []),
                "configured": False,
            }

    return {
        "providers": providers_info,
        "configured_count": len(factory.get_provider_names()),
    }


async def invalidate_provider_cache() -> None:
    """Invalidate the provider factory cache (call after API key changes)."""
    global _factory_cache
    async with _factory_lock:
        _factory_cache = None


@router.get("/providers/{provider_name}/models")
async def get_provider_models(provider_name: str):
    """
    Get available models for a specific provider.

    Args:
        provider_name: Name of the provider (openai, anthropic, google, grok)

    Returns:
        dict: Available models for the provider
    """
    if provider_name not in PROVIDER_CONFIGS:
        raise HTTPException(status_code=404, detail=f"Provider '{provider_name}' not found")

    config = PROVIDER_CONFIGS[provider_name]

    return {
        "provider": provider_name,
        "default_model": config.get("default_model"),
        "available_models": config.get("available_models", []),
    }
