"""API routes for personality archetypes."""
from fastapi import APIRouter
from app.core.personality_archetypes import get_archetype_list, PERSONALITY_ARCHETYPES

router = APIRouter()


@router.get("/archetypes")
async def list_archetypes():
    """
    Get list of available personality archetypes for council members.

    Returns:
        List of archetype definitions with id, name, description, and emoji
    """
    return {
        "archetypes": get_archetype_list(),
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
