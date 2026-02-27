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
            # Standard chat models
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            # Reasoning models (no temperature support, use max_completion_tokens)
            "o3",
            "o3-mini",
            "o1",
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
        "default_model": "gemini-2.5-flash",
        "env_key": "GOOGLE_API_KEY",
        "supports_streaming": True,
        "available_models": [
            "gemini-2.5-flash",      # Best price/performance, hybrid reasoning
            "gemini-2.5-pro",        # Most capable for complex tasks
            "gemini-2.5-flash-lite", # Fastest, most budget-friendly
            "gemini-2.0-flash",      # Previous generation, still available
            "gemini-1.5-pro",        # Legacy, broader availability
            "gemini-1.5-flash",      # Legacy, fast and cheap
        ],
    },
    "grok": {
        "default_model": "grok-3",
        "env_key": "GROK_API_KEY",
        "supports_streaming": True,
        "base_url": "https://api.x.ai/v1",
        "available_models": [
            "grok-4",              # Latest — advanced reasoning + vision
            "grok-3",              # Released June 2025, 131K context
            "grok-3-mini",         # Cost-effective, built-in reasoning
            "grok-2-1212",         # Previous generation
            "grok-2-vision-1212",  # Previous generation + vision
            "grok-beta",           # Legacy
        ],
    },
    "ollama": {
        "default_model": "llama3.2",
        "env_key": None,  # No API key needed for local
        "supports_streaming": True,
        "base_url": "http://localhost:11434",
        "available_models": [
            # General — small (≤8GB RAM)
            "llama3.2",
            "qwen3:8b",
            "gemma3",
            "phi4-mini",
            "mistral",
            "qwen2.5",
            "smollm2",
            # General — medium (≤16GB RAM)
            "llama3.3",
            "qwen3:14b",
            "mistral-nemo",
            "phi4",
            "gemma3:12b",
            # General — large (32GB+ RAM)
            "llama3.3:70b",
            "qwen3:32b",
            "gemma3:27b",
            "qwen2.5:32b",
            "mistral-large",
            "mixtral",
            # Coding specialists
            "qwen3-coder",
            "qwen2.5-coder",
            "devstral",
            "deepseek-coder-v2",
            "mimo-v2-flash",
            "codellama",
            # Reasoning
            "deepseek-r1",
            "deepseek-v3.2",
            "phi4-reasoning",
            "phi4-reasoning-plus",
            "kimi-k2.5",
            "glm-5",
            # Cloud-routed (via Ollama API compatibility)
            "glm-4.7:cloud",
            "minimax-m2.1:cloud",
            # Vision
            "llama3.2-vision",
            "qwen2.5vl",
            "llava",
            "llava-phi3",
            "moondream",
        ],
        "is_local": True,
    },
}

# Pricing per 1K tokens (input, output) in USD
# Note: These are estimates and should be updated regularly
PRICING = {
    # OpenAI ($ per 1M tokens)
    "openai:gpt-4o": (2.50, 10.00),
    "openai:gpt-4o-mini": (0.15, 0.60),
    "openai:gpt-4-turbo": (10.00, 30.00),
    "openai:gpt-3.5-turbo": (0.50, 1.50),
    "openai:o3": (10.00, 40.00),
    "openai:o3-mini": (1.10, 4.40),
    "openai:o1": (15.00, 60.00),
    # Anthropic
    "anthropic:claude-opus-4-20250514": (15.00, 75.00),
    "anthropic:claude-sonnet-4-20250514": (3.00, 15.00),
    "anthropic:claude-sonnet-3-5-20241022": (3.00, 15.00),
    "anthropic:claude-sonnet-3-5-20240620": (3.00, 15.00),
    "anthropic:claude-haiku-3-5-20241022": (0.80, 4.00),
    # Google ($ per 1M tokens — matches the per-1M convention used throughout this dict)
    "google:gemini-2.5-flash": (0.30, 2.50),
    "google:gemini-2.5-pro": (1.25, 10.00),
    "google:gemini-2.5-flash-lite": (0.10, 0.40),
    "google:gemini-2.0-flash": (0.10, 0.40),
    "google:gemini-1.5-pro": (1.25, 5.00),
    "google:gemini-1.5-flash": (0.075, 0.30),
    # Grok ($ per 1M tokens)
    "grok:grok-4": (10.00, 30.00),
    "grok:grok-3": (3.00, 15.00),
    "grok:grok-3-mini": (0.30, 0.50),
    "grok:grok-2-1212": (2.00, 10.00),
    "grok:grok-2-vision-1212": (2.00, 10.00),
    "grok:grok-beta": (5.00, 15.00),
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
