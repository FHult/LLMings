"""API routes for personality archetypes."""
from fastapi import APIRouter
from app.core.personality_archetypes import get_archetype_list, PERSONALITY_ARCHETYPES
from app.services.ai_providers.ollama_provider import OllamaProvider

router = APIRouter()


@router.get("/archetypes")
async def list_archetypes():
    """
    Get list of available personality archetypes for council members.

    Returns dynamic model recommendations based on installed Ollama models
    and their suitability scores.

    Returns:
        List of archetype definitions with id, name, description, emoji, and recommended_models
    """
    installed_models = []
    model_suitability = {}

    # Try to get installed Ollama models and suitability data
    try:
        async with OllamaProvider() as provider:
            # Get installed models
            models = await provider.list_available_models()
            installed_models = models

            # Build suitability map from installed models
            for model_name in models:
                info = provider.get_model_info(model_name)
                if "suitability" in info:
                    model_suitability[model_name] = info["suitability"]
                    # Also map by base model name for matching
                    base_model = model_name.split(":")[0] if ":" in model_name else model_name
                    if base_model not in model_suitability:
                        model_suitability[base_model] = info["suitability"]
    except Exception:
        # If Ollama is not running, fall back to static recommendations
        pass

    return {
        "archetypes": get_archetype_list(installed_models, model_suitability),
        "count": len(PERSONALITY_ARCHETYPES)
    }


@router.get("/archetypes/{archetype_id}")
async def get_archetype(archetype_id: str):
    """
    Get detailed information about a specific archetype.

    Args:
        archetype_id: The archetype identifier

    Returns:
        Archetype details including system prompt
    """
    if archetype_id not in PERSONALITY_ARCHETYPES:
        return {"error": "Archetype not found"}, 404

    archetype = PERSONALITY_ARCHETYPES[archetype_id]
    return {
        "id": archetype_id,
        "name": archetype["name"],
        "description": archetype["description"],
        "emoji": archetype["emoji"],
        "system_prompt": archetype["system_prompt"],
    }
