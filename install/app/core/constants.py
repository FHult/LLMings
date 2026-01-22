"""Application constants including pricing and model configurations."""
from enum import Enum


class ProviderName(str, Enum):
    """Supported AI providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    GROK = "grok"
    OLLAMA = "ollama"


class SessionStatus(str, Enum):
    """Session status values."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"


class ResponseRole(str, Enum):
    """Response role types."""
    COUNCIL = "council"
    CHAIR = "chair"


class StreamEventType(str, Enum):
    """SSE stream event types."""
    ITERATION_START = "iteration_start"
    RESPONSE_START = "response_start"
    RESPONSE_CHUNK = "response_chunk"
    RESPONSE_END = "response_end"
    RESPONSE_ERROR = "response_error"
    CONSENSUS_START = "consensus_start"
    CONSENSUS_CHUNK = "consensus_chunk"
    CONSENSUS_END = "consensus_end"
    ITERATION_END = "iteration_end"
    SESSION_COMPLETE = "session_complete"


# AI Provider Configurations
PROVIDER_CONFIGS = {
    "openai": {
        "default_model": "gpt-4o",
        "env_key": "OPENAI_API_KEY",
        "supports_streaming": True,
        "available_models": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo",
        ],
    },
    "anthropic": {
        "default_model": "claude-sonnet-4-20250514",
        "env_key": "ANTHROPIC_API_KEY",
        "supports_streaming": True,
        "available_models": [
            "claude-opus-4-20250514",
            "claude-sonnet-4-20250514",
            "claude-sonnet-3-5-20241022",
            "claude-sonnet-3-5-20240620",
            "claude-haiku-3-5-20241022",
        ],
    },
    "google": {
        "default_model": "gemini-2.0-flash-exp",
        "env_key": "GOOGLE_API_KEY",
        "supports_streaming": True,
        "available_models": [
            "gemini-2.0-flash-exp",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
            "gemini-pro",
        ],
    },
    "grok": {
        "default_model": "grok-beta",
        "env_key": "GROK_API_KEY",
        "supports_streaming": True,
        "base_url": "https://api.x.ai/v1",
        "available_models": [
            "grok-beta",
            "grok-vision-beta",
        ],
    },
    "ollama": {
        "default_model": "phi3:mini",
        "env_key": None,  # No API key needed for local
        "supports_streaming": True,
        "base_url": "http://localhost:11434",
        "available_models": [
            "phi3:mini",
            "llama3.1",
            "llama3.1:70b",
            "llama3",
            "mistral",
            "mistral-nemo",
            "phi3",
            "phi3:medium",
            "gemma2",
            "gemma2:27b",
            "qwen2",
            "qwen2:7b",
            "codellama",
            "llava",  # Vision model
            "llava-phi3",  # Vision model
        ],
        "is_local": True,
    },
}

# Pricing per 1K tokens (input, output) in USD
# Note: These are estimates and should be updated regularly
PRICING = {
    # OpenAI
    "openai:gpt-4o": (2.50, 10.00),
    "openai:gpt-4o-mini": (0.15, 0.60),
    "openai:gpt-4-turbo": (10.00, 30.00),
    "openai:gpt-4": (30.00, 60.00),
    "openai:gpt-3.5-turbo": (0.50, 1.50),
    # Anthropic
    "anthropic:claude-opus-4-20250514": (15.00, 75.00),
    "anthropic:claude-sonnet-4-20250514": (3.00, 15.00),
    "anthropic:claude-sonnet-3-5-20241022": (3.00, 15.00),
    "anthropic:claude-sonnet-3-5-20240620": (3.00, 15.00),
    "anthropic:claude-haiku-3-5-20241022": (0.80, 4.00),
    # Google
    "google:gemini-2.0-flash-exp": (0.00, 0.00),  # Free during preview
    "google:gemini-1.5-pro": (1.25, 5.00),
    "google:gemini-1.5-flash": (0.075, 0.30),
    "google:gemini-pro": (0.50, 1.50),
    # Grok
    "grok:grok-beta": (5.00, 15.00),
    "grok:grok-vision-beta": (5.00, 15.00),
}

# Preset temperature mappings
PRESETS = {
    "creative": 0.9,
    "balanced": 0.7,
    "precise": 0.3,
}

# Preset configurations (full details)
PRESET_CONFIGS = {
    "creative": {
        "temperature": 0.9,
        "description": "More varied and creative responses",
    },
    "balanced": {
        "temperature": 0.7,
        "description": "Balanced between creativity and consistency",
    },
    "precise": {
        "temperature": 0.3,
        "description": "More focused and consistent responses",
    },
}

# Merge templates system prompts
MERGE_TEMPLATES = {
    "analytical": """You are an analytical synthesizer. Your task is to merge multiple AI responses into a single, cohesive answer.

Focus on:
- Logical synthesis of key points
- Evidence-based consolidation
- Clear reasoning and structure
- Identifying common themes and unique insights
- Maintaining factual accuracy

Create a well-structured response that represents the best thinking from all sources.""",
    "creative": """You are a creative synthesizer. Your task is to merge multiple AI responses into a single, innovative answer.

Focus on:
- Novel combinations of ideas
- Expansive and exploratory thinking
- Synthesizing unique perspectives
- Building on creative insights
- Encouraging bold connections

Create an imaginative response that expands beyond individual contributions.""",
    "technical": """You are a technical synthesizer. Your task is to merge multiple AI responses into a single, accurate answer.

Focus on:
- Technical precision and correctness
- Detailed accuracy
- Clear technical explanations
- Verification of claims
- Consistent terminology

Create a technically sound response that maintains high standards of accuracy.""",
    "balanced": """You are a balanced synthesizer. Your task is to merge multiple AI responses into a single, well-rounded answer.

Focus on:
- Integrating diverse perspectives
- Balanced representation of ideas
- Clear and accessible language
- Practical applicability
- Thoughtful synthesis

Create a comprehensive response that reflects the collective wisdom of all sources.""",
}

# Session statuses
SESSION_STATUS = {
    "PENDING": "pending",
    "RUNNING": "running",
    "PAUSED": "paused",
    "COMPLETED": "completed",
    "FAILED": "failed",
}

# Response roles
RESPONSE_ROLES = {
    "COUNCIL": "council",
    "CHAIR": "chair",
}

# Stream event types
STREAM_EVENTS = {
    "ITERATION_START": "iteration_start",
    "RESPONSE_START": "response_start",
    "RESPONSE_CHUNK": "response_chunk",
    "RESPONSE_END": "response_end",
    "RESPONSE_ERROR": "response_error",
    "CONSENSUS_START": "consensus_start",
    "CONSENSUS_CHUNK": "consensus_chunk",
    "CONSENSUS_END": "consensus_end",
    "ITERATION_END": "iteration_end",
    "SESSION_COMPLETE": "session_complete",
}
