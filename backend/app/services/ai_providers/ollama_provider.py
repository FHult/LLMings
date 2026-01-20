"""Ollama provider implementation for local LLM support."""
import logging
import httpx
import psutil
from typing import AsyncGenerator
from .base import AIProvider
from app.core.config import settings
from app.core.constants import PRICING, PROVIDER_CONFIGS
from app.core.exceptions import (
    AIProviderError,
    ModelNotFoundError,
    ConnectionError as ProviderConnectionError,
    TimeoutError,
)

logger = logging.getLogger(__name__)


class OllamaProvider(AIProvider):
    """Ollama local LLM provider with RAM checks and model suitability."""

    # Model RAM requirements (in GB) - approximate minimums
    MODEL_RAM_REQUIREMENTS = {
        # Small models (good for 8GB RAM)
        "phi3": 4, "phi3:mini": 2, "phi4-mini": 4, "gemma": 4, "gemma3": 5,
        "qwen2": 4, "qwen2.5": 5, "qwen3": 5, "smollm2": 2,
        # Medium models (good for 16GB RAM)
        "llama3.1": 8, "llama3.2": 8, "llama3.3": 8, "llama3": 8,
        "mistral": 7, "mistral-nemo": 12, "mistral-small": 14,
        "gemma2": 9, "gemma2:9b": 9, "gemma3:12b": 12,
        "qwen2:7b": 7, "qwen2.5:7b": 7, "qwen3:8b": 8,
        "codellama": 7, "deepseek-coder": 8, "deepseek-coder-v2": 10,
        "starcoder2": 8, "codegemma": 9,
        # Coding-focused models
        "qwen3-coder": 10, "qwen2.5-coder": 8, "qwen2.5-coder:7b": 7,
        "devstral": 14,
        # Large models (need 32GB+ RAM)
        "llama3.1:70b": 48, "llama3.3:70b": 48,
        "phi3:medium": 16, "phi4": 16,
        "gemma2:27b": 24, "gemma3:27b": 24,
        "qwen2.5:32b": 24, "qwen3:32b": 24,
        "mistral-large": 48, "mixtral": 32,
        "deepseek-v3": 48, "deepseek-r1": 48,
        # Cloud/API models (minimal local RAM - inference via API)
        "glm-4.7:cloud": 2, "minimax-m2.1:cloud": 2,
        # Vision models
        "llava": 8, "llava-phi3": 6, "llava-llama3": 8,
        "llama3.2-vision": 12, "moondream": 4,
    }

    # Model suitability ratings (1-10 scale)
    MODEL_SUITABILITY = {
        # Latest flagship models
        "llama3.3": {"general": 9, "coding": 9, "reasoning": 9, "creative": 8},
        "llama3.2": {"general": 9, "coding": 8, "reasoning": 9, "creative": 8},
        "llama3.1": {"general": 9, "coding": 8, "reasoning": 9, "creative": 8},
        "gemma3": {"general": 9, "coding": 8, "reasoning": 9, "creative": 8},
        "gemma2": {"general": 8, "coding": 7, "reasoning": 8, "creative": 8},
        "qwen3": {"general": 9, "coding": 9, "reasoning": 9, "creative": 8},
        "qwen2.5": {"general": 8, "coding": 8, "reasoning": 8, "creative": 7},
        "phi4": {"general": 8, "coding": 9, "reasoning": 9, "creative": 7},
        "phi4-mini": {"general": 7, "coding": 8, "reasoning": 8, "creative": 6},
        # Coding specialists
        "qwen3-coder": {"general": 7, "coding": 10, "reasoning": 8, "creative": 5},
        "qwen2.5-coder": {"general": 7, "coding": 10, "reasoning": 8, "creative": 5},
        "deepseek-coder-v2": {"general": 7, "coding": 10, "reasoning": 8, "creative": 5},
        "deepseek-coder": {"general": 6, "coding": 9, "reasoning": 7, "creative": 4},
        "codellama": {"general": 6, "coding": 9, "reasoning": 7, "creative": 5},
        "starcoder2": {"general": 5, "coding": 9, "reasoning": 6, "creative": 4},
        "codegemma": {"general": 6, "coding": 9, "reasoning": 7, "creative": 5},
        "devstral": {"general": 7, "coding": 10, "reasoning": 8, "creative": 5},
        # Reasoning models
        "deepseek-r1": {"general": 9, "coding": 9, "reasoning": 10, "creative": 7},
        "deepseek-v3": {"general": 9, "coding": 9, "reasoning": 9, "creative": 8},
        # General models
        "mistral": {"general": 8, "coding": 8, "reasoning": 8, "creative": 7},
        "mistral-nemo": {"general": 8, "coding": 8, "reasoning": 8, "creative": 7},
        "mistral-small": {"general": 8, "coding": 8, "reasoning": 8, "creative": 7},
        "phi3": {"general": 7, "coding": 8, "reasoning": 7, "creative": 6},
        # Cloud models (via Ollama API compatibility)
        "glm-4.7:cloud": {"general": 9, "coding": 9, "reasoning": 9, "creative": 8},
        "minimax-m2.1:cloud": {"general": 9, "coding": 8, "reasoning": 9, "creative": 9},
        # Vision models
        "llava": {"general": 7, "coding": 5, "reasoning": 6, "creative": 6},
        "llama3.2-vision": {"general": 8, "coding": 6, "reasoning": 7, "creative": 7},
    }

    def __init__(self, api_key: str = "not-needed", model: str | None = None, base_url: str | None = None):
        """Initialize Ollama provider."""
        super().__init__(api_key, model)
        self.base_url = base_url or settings.ollama_base_url
        self.name = "ollama"
        self.client = httpx.AsyncClient(timeout=60.0)  # 60 second timeout for local models

    async def stream_completion(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        image_data: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """Stream completion from Ollama."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        # Build user message with optional image
        if image_data and self.supports_vision():
            messages.append({
                "role": "user",
                "content": prompt,
                "images": [image_data]  # Ollama accepts base64 images directly
            })
        else:
            messages.append({"role": "user", "content": prompt})

        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens,
                    }
                }
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            import json
                            chunk = json.loads(line)
                            if "message" in chunk and "content" in chunk["message"]:
                                content = chunk["message"]["content"]
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            continue

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise ModelNotFoundError(self.model, provider="ollama")
            raise AIProviderError(f"Ollama API error: {str(e)}", provider="ollama")
        except httpx.ConnectError:
            raise ProviderConnectionError("Cannot connect to Ollama. Make sure Ollama is running (ollama serve)", provider="ollama")
        except httpx.TimeoutException:
            raise TimeoutError("Ollama request timed out", provider="ollama")
        except (ModelNotFoundError, ProviderConnectionError, TimeoutError):
            raise  # Re-raise our custom exceptions
        except Exception as e:
            raise AIProviderError(f"Ollama error: {str(e)}", provider="ollama")

    def supports_vision(self) -> bool:
        """Check if model supports vision."""
        # Ollama vision models
        vision_models = {"llava", "bakllava", "llava-phi3", "llava-llama3"}
        return any(vm in self.model.lower() for vm in vision_models)

    def count_tokens(self, text: str) -> int:
        """Count tokens using rough estimation."""
        # Rough estimate: 4 chars per token for most models
        return len(text) // 4

    def get_default_model(self) -> str:
        """Get default Ollama model."""
        return PROVIDER_CONFIGS.get("ollama", {}).get("default_model", "llama3.1")

    def get_pricing(self) -> tuple[float, float]:
        """Get Ollama pricing (free for local)."""
        # Local models are free
        return (0.0, 0.0)

    async def list_available_models(self) -> list[str]:
        """List models available in local Ollama installation."""
        try:
            response = await self.client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            data = response.json()

            models = []
            if "models" in data:
                for model_info in data["models"]:
                    if "name" in model_info:
                        models.append(model_info["name"])

            return models
        except Exception as e:
            logger.warning(f"Error listing Ollama models: {e}")
            return []

    async def pull_model(self, model_name: str) -> AsyncGenerator[dict, None]:
        """
        Pull/download a model from Ollama library.

        Yields status updates during download.
        """
        try:
            async with self.client.stream(
                "POST",
                f"{self.base_url}/api/pull",
                json={"name": model_name, "stream": True}
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            import json
                            status = json.loads(line)
                            yield status
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            yield {"error": str(e)}

    async def check_ollama_status(self) -> dict:
        """Check if Ollama is running and get version info."""
        try:
            response = await self.client.get(f"{self.base_url}/api/version")
            response.raise_for_status()
            return {
                "running": True,
                "version": response.json().get("version", "unknown")
            }
        except Exception:
            return {
                "running": False,
                "error": "Ollama is not running. Start it with: ollama serve"
            }

    def check_system_ram(self) -> float:
        """Get available system RAM in GB."""
        memory = psutil.virtual_memory()
        return memory.available / (1024 ** 3)  # Convert bytes to GB

    def get_total_system_ram(self) -> float:
        """Get total system RAM in GB."""
        memory = psutil.virtual_memory()
        return memory.total / (1024 ** 3)

    def can_run_model(self, model_name: str) -> tuple[bool, str]:
        """
        Check if model can run on current system.

        Returns:
            (can_run, message): Boolean and explanatory message
        """
        # Extract base model name (handle tags like "llama3.1:70b")
        base_model = model_name.split(":")[0] if ":" in model_name else model_name
        full_model = model_name

        # Check if we have RAM requirements for this model
        required_ram = self.MODEL_RAM_REQUIREMENTS.get(full_model) or self.MODEL_RAM_REQUIREMENTS.get(base_model)

        if required_ram is None:
            return True, f"No RAM requirements defined for {model_name}, should be safe to try"

        available_ram = self.check_system_ram()
        total_ram = self.get_total_system_ram()

        # We want at least 2GB buffer for system
        safe_available = available_ram - 2.0

        if safe_available >= required_ram:
            return True, f"Model requires {required_ram}GB, you have {available_ram:.1f}GB available"
        else:
            return False, f"Model requires {required_ram}GB, but only {available_ram:.1f}GB available (total: {total_ram:.1f}GB)"

    def get_recommended_models(self) -> list[dict]:
        """
        Get models recommended for current system based on available RAM.

        Returns:
            List of model info dicts with name, ram_required, and suitability
        """
        available_ram = self.check_system_ram()
        recommended = []

        for model_name, required_ram in self.MODEL_RAM_REQUIREMENTS.items():
            can_run, message = self.can_run_model(model_name)

            if can_run:
                model_info = {
                    "name": model_name,
                    "ram_required": required_ram,
                    "can_run": True,
                    "message": message,
                }

                # Add suitability if available
                base_model = model_name.split(":")[0]
                if base_model in self.MODEL_SUITABILITY:
                    model_info["suitability"] = self.MODEL_SUITABILITY[base_model]

                recommended.append(model_info)

        # Sort by RAM requirement (smallest first)
        recommended.sort(key=lambda x: x["ram_required"])
        return recommended

    def get_model_info(self, model_name: str) -> dict:
        """
        Get detailed info about a specific model.

        Returns:
            Dict with RAM requirements, suitability ratings, and compatibility
        """
        base_model = model_name.split(":")[0] if ":" in model_name else model_name

        info = {
            "name": model_name,
            "base_model": base_model,
        }

        # Add RAM requirements
        required_ram = self.MODEL_RAM_REQUIREMENTS.get(model_name) or self.MODEL_RAM_REQUIREMENTS.get(base_model)
        if required_ram:
            info["ram_required"] = required_ram
            can_run, message = self.can_run_model(model_name)
            info["can_run"] = can_run
            info["message"] = message

        # Add suitability ratings
        if base_model in self.MODEL_SUITABILITY:
            info["suitability"] = self.MODEL_SUITABILITY[base_model]

        # Check if it's a vision model
        info["supports_vision"] = any(vm in model_name.lower() for vm in {"llava", "bakllava"})

        return info

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
