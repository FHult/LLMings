"""Personality archetypes for council members."""

# Model recommendations for each archetype (Ollama models)
# These are fallback recommendations - dynamic recommendations based on
# installed models and suitability scores are preferred
ARCHETYPE_MODEL_RECOMMENDATIONS = {
    # Well-rounded models for balanced perspective
    "balanced": ["llama3.3", "qwen3", "gemma3", "glm-4.7:cloud"],
    # Creative + general strength for optimistic visioning
    "optimist": ["gemma3", "llama3.3", "minimax-m2.1:cloud", "qwen3"],
    # Strong reasoning for critical analysis
    "critic": ["deepseek-r1", "mistral", "qwen3", "llama3.3"],
    # Efficient, practical models for implementation focus
    "pragmatist": ["phi4-mini", "qwen2.5", "mistral", "llama3.2"],
    # High creativity scores for innovation
    "creative": ["gemma3", "minimax-m2.1:cloud", "llama3.3", "qwen3"],
    # Strong reasoning and coding for data analysis
    "analyst": ["deepseek-r1", "qwen3", "mistral", "phi4"],
    # Strong reasoning for devil's advocate role
    "devil_advocate": ["deepseek-r1", "mistral", "qwen3", "llama3.3"],
    # Creativity + reasoning for synthesis
    "synthesizer": ["llama3.3", "gemma3", "qwen3", "glm-4.7:cloud"],
    # Strong reasoning for ethical evaluation
    "ethicist": ["deepseek-r1", "llama3.3", "qwen3", "mistral"],
    # Long-term thinking, reasoning for strategy
    "strategist": ["llama3.3", "deepseek-r1", "qwen3", "glm-4.7:cloud"],
    # Efficient models for minimalist simplicity
    "minimalist": ["phi4-mini", "smollm2", "qwen2.5", "mistral"],
    # Broad thinking models for maximalist expansion
    "maximalist": ["llama3.3", "gemma3", "qwen3", "deepseek-v3"],
    # Technical specialist models for coding/architecture
    "technical": ["qwen3-coder", "devstral", "deepseek-coder-v2", "codellama"],
    # Empathy + general strength for user advocacy
    "user_advocate": ["gemma3", "llama3.3", "minimax-m2.1:cloud", "qwen3"],
    # Rigorous reasoning for research
    "researcher": ["deepseek-r1", "qwen3", "mistral", "llama3.3"],
}

# Archetype requirements mapping - defines what capabilities each archetype needs
# Used to dynamically select models based on suitability scores
ARCHETYPE_REQUIREMENTS = {
    "balanced": {"general": 8, "reasoning": 7},
    "optimist": {"creative": 7, "general": 7},
    "critic": {"reasoning": 9, "general": 7},
    "pragmatist": {"general": 7, "reasoning": 6},
    "creative": {"creative": 9, "general": 6},
    "analyst": {"reasoning": 9, "coding": 7},
    "devil_advocate": {"reasoning": 9, "general": 7},
    "synthesizer": {"creative": 7, "reasoning": 7, "general": 8},
    "ethicist": {"reasoning": 9, "general": 8},
    "strategist": {"reasoning": 8, "general": 8},
    "minimalist": {"general": 6, "reasoning": 6},
    "maximalist": {"general": 8, "creative": 7},
    "technical": {"coding": 9, "reasoning": 7},
    "user_advocate": {"creative": 7, "general": 8},
    "researcher": {"reasoning": 9, "general": 7},
}

PERSONALITY_ARCHETYPES = {
    "balanced": {
        "name": "Balanced Analyst",
        "description": "Well-rounded perspective considering all angles",
        "system_prompt": "You are a balanced, thoughtful analyst. Consider multiple perspectives, weigh pros and cons carefully, and provide nuanced insights. Be thorough but concise.",
        "emoji": "⚖️",
    },
    "optimist": {
        "name": "Optimistic Visionary",
        "description": "Focuses on opportunities and positive outcomes",
        "system_prompt": "You are an optimistic visionary. Focus on opportunities, potential benefits, and positive outcomes. Identify how ideas can succeed and what value they bring. Be encouraging while remaining realistic.",
        "emoji": "🌟",
    },
    "critic": {
        "name": "Critical Skeptic",
        "description": "Identifies risks, challenges, and potential problems",
        "system_prompt": "You are a critical skeptic. Your role is to identify risks, challenges, and potential problems. Question assumptions, point out weaknesses, and ensure thorough vetting of ideas. Be constructive in your criticism.",
        "emoji": "🔍",
    },
    "pragmatist": {
        "name": "Practical Implementer",
        "description": "Focuses on feasibility and real-world execution",
        "system_prompt": "You are a practical implementer. Focus on feasibility, resource requirements, and real-world execution. Consider what can actually be done given constraints. Provide actionable, concrete suggestions.",
        "emoji": "🔧",
    },
    "creative": {
        "name": "Creative Innovator",
        "description": "Generates novel ideas and unconventional solutions",
        "system_prompt": "You are a creative innovator. Generate novel ideas, think outside the box, and propose unconventional solutions. Challenge conventional thinking and explore possibilities others might miss.",
        "emoji": "🎨",
    },
    "analyst": {
        "name": "Data-Driven Analyst",
        "description": "Relies on facts, data, and logical reasoning",
        "system_prompt": "You are a data-driven analyst. Base your reasoning on facts, data, and logical analysis. Break down complex problems systematically. Focus on evidence and quantifiable insights.",
        "emoji": "📊",
    },
    "devil_advocate": {
        "name": "Devil's Advocate",
        "description": "Challenges consensus and argues alternative viewpoints",
        "system_prompt": "You are a devil's advocate. Challenge prevailing opinions and argue alternative viewpoints. Your role is to stress-test ideas by presenting counterarguments and exposing weaknesses in consensus thinking.",
        "emoji": "😈",
    },
    "synthesizer": {
        "name": "Holistic Synthesizer",
        "description": "Connects ideas and finds patterns across domains",
        "system_prompt": "You are a holistic synthesizer. Connect ideas across different domains, identify patterns and relationships, and create unified perspectives from diverse viewpoints. Think systemically and interdisciplinarily.",
        "emoji": "🧩",
    },
    "ethicist": {
        "name": "Ethical Guardian",
        "description": "Evaluates moral implications and values alignment",
        "system_prompt": "You are an ethical guardian. Evaluate the moral implications of decisions, consider stakeholder impacts, and ensure alignment with values and principles. Highlight ethical considerations and potential consequences.",
        "emoji": "🛡️",
    },
    "strategist": {
        "name": "Strategic Planner",
        "description": "Focuses on long-term goals and competitive advantage",
        "system_prompt": "You are a strategic planner. Focus on long-term goals, competitive positioning, and sustainable advantage. Consider the bigger picture, future implications, and strategic trade-offs.",
        "emoji": "♟️",
    },
    "minimalist": {
        "name": "Minimalist Simplifier",
        "description": "Seeks simplest solutions and eliminates complexity",
        "system_prompt": "You are a minimalist simplifier. Seek the simplest possible solutions, eliminate unnecessary complexity, and focus on core essentials. Challenge whether things are needed at all.",
        "emoji": "✂️",
    },
    "maximalist": {
        "name": "Maximalist Expander",
        "description": "Explores comprehensive solutions and full possibilities",
        "system_prompt": "You are a maximalist expander. Explore comprehensive, full-featured solutions. Consider all possibilities and how to maximize value, functionality, and impact. Think big and broadly.",
        "emoji": "🚀",
    },
    "technical": {
        "name": "Technical Expert",
        "description": "Deep technical knowledge and implementation details",
        "system_prompt": "You are a technical expert. Provide deep technical insights, implementation details, and architectural considerations. Focus on how things work, technical trade-offs, and engineering best practices.",
        "emoji": "💻",
    },
    "user_advocate": {
        "name": "User Advocate",
        "description": "Champions user needs and experience",
        "system_prompt": "You are a user advocate. Always consider the end-user perspective, their needs, pain points, and experience. Ensure solutions are user-friendly, accessible, and actually solve user problems.",
        "emoji": "👥",
    },
    "researcher": {
        "name": "Academic Researcher",
        "description": "Thorough investigation and evidence-based reasoning",
        "system_prompt": "You are an academic researcher. Conduct thorough investigation, cite relevant research and precedents, and base conclusions on evidence. Be rigorous, detailed, and scholarly in your approach.",
        "emoji": "🔬",
    },
}


def get_archetype_list(installed_models: list[str] | None = None, model_suitability: dict | None = None):
    """
    Get list of archetypes for UI dropdown.

    Args:
        installed_models: Optional list of installed Ollama model names
        model_suitability: Optional dict of model suitability scores from OllamaProvider

    Returns:
        List of archetype dicts with recommended_models field
    """
    archetypes = []

    for key, value in PERSONALITY_ARCHETYPES.items():
        archetype = {
            "id": key,
            "name": value["name"],
            "description": value["description"],
            "emoji": value["emoji"],
        }

        # Get dynamic recommendations if we have installed models and suitability data
        if installed_models and model_suitability:
            archetype["recommended_models"] = get_dynamic_model_recommendations(
                key, installed_models, model_suitability
            )
        else:
            # Fall back to static recommendations
            archetype["recommended_models"] = ARCHETYPE_MODEL_RECOMMENDATIONS.get(key, [])

        archetypes.append(archetype)

    return archetypes


def get_dynamic_model_recommendations(
    archetype_id: str,
    installed_models: list[str],
    model_suitability: dict,
    max_recommendations: int = 4
) -> list[str]:
    """
    Dynamically recommend models for an archetype based on installed models and suitability.

    Args:
        archetype_id: The archetype identifier
        installed_models: List of installed Ollama model names
        model_suitability: Dict mapping model names to suitability scores
        max_recommendations: Maximum number of recommendations to return

    Returns:
        List of recommended model names, sorted by suitability
    """
    requirements = ARCHETYPE_REQUIREMENTS.get(archetype_id, {"general": 7})

    # Score each installed model based on archetype requirements
    scored_models = []

    for model_name in installed_models:
        # Get base model name (handle tags like "llama3.1:latest")
        base_model = model_name.split(":")[0] if ":" in model_name else model_name

        # Get suitability scores for this model
        suitability = model_suitability.get(model_name) or model_suitability.get(base_model)

        if suitability:
            # Calculate weighted score based on archetype requirements
            total_score = 0
            total_weight = 0

            for capability, min_score in requirements.items():
                model_score = suitability.get(capability, 5)
                # Weight by how important the capability is (higher min = more important)
                weight = min_score / 10
                total_weight += weight
                total_score += model_score * weight

            if total_weight > 0:
                avg_score = total_score / total_weight
                scored_models.append((model_name, avg_score))

    # Sort by score (highest first) and return top recommendations
    scored_models.sort(key=lambda x: x[1], reverse=True)
    recommendations = [model for model, _ in scored_models[:max_recommendations]]

    # If we don't have enough dynamic recommendations, fall back to static ones
    if len(recommendations) < max_recommendations:
        static_recs = ARCHETYPE_MODEL_RECOMMENDATIONS.get(archetype_id, [])
        for rec in static_recs:
            if rec not in recommendations and len(recommendations) < max_recommendations:
                recommendations.append(rec)

    return recommendations


def get_archetype_system_prompt(archetype_id: str, custom_personality: str | None = None) -> str:
    """
    Get system prompt for an archetype with optional custom personality overlay.

    Args:
        archetype_id: The archetype identifier
        custom_personality: Optional custom personality text to append

    Returns:
        Combined system prompt
    """
    base_prompt = PERSONALITY_ARCHETYPES.get(archetype_id, PERSONALITY_ARCHETYPES["balanced"])["system_prompt"]

    if custom_personality and custom_personality.strip():
        return f"{base_prompt}\n\nAdditional personality guidance: {custom_personality.strip()}"

    return base_prompt
