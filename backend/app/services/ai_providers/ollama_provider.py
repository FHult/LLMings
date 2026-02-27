"""Ollama provider implementation — uses the official ollama Python SDK."""
import logging
import platform
import subprocess
import psutil
from typing import AsyncGenerator, TYPE_CHECKING
from ollama import AsyncClient, ResponseError
from .base import AIProvider
from app.core.config import settings
from app.core.constants import PRICING, PROVIDER_CONFIGS
from app.core.exceptions import (
    AIProviderError,
    ModelNotFoundError,
    ConnectionError as ProviderConnectionError,
    TimeoutError,
)

if TYPE_CHECKING:
    from pydantic import BaseModel

logger = logging.getLogger(__name__)


class OllamaProvider(AIProvider):
    """Ollama local LLM provider with RAM/GPU checks and model suitability."""

    # Model RAM requirements (in GB) — approximate minimums
    MODEL_RAM_REQUIREMENTS = {
        # Small models (good for 8GB RAM)
        "phi3": 4, "phi3:mini": 2, "phi4-mini": 4, "gemma": 4, "gemma3": 5,
        "qwen2": 4, "qwen2.5": 5, "qwen3": 5, "smollm2": 2,
        # Medium models (good for 16GB RAM)
        "llama3.1": 8, "llama3.2": 8, "llama3.3": 8, "llama3": 8,
        "mistral": 7, "mistral-nemo": 12, "mistral-small": 14,
        "gemma2": 9, "gemma2:9b": 9, "gemma3:12b": 12,
        "qwen2:7b": 7, "qwen2.5:7b": 7, "qwen3:8b": 8, "qwen3:14b": 14,
        "codellama": 7, "deepseek-coder": 8, "deepseek-coder-v2": 10,
        "starcoder2": 8, "codegemma": 9,
        # Coding-focused models
        "qwen3-coder": 10, "qwen2.5-coder": 8, "qwen2.5-coder:7b": 7,
        "devstral": 14, "mimo-v2-flash": 8,
        # Large models (need 32GB+ RAM)
        "llama3.1:70b": 48, "llama3.3:70b": 48,
        "phi3:medium": 16, "phi4": 16,
        "phi4-reasoning": 16, "phi4-reasoning-plus": 16,
        "gemma2:27b": 24, "gemma3:27b": 24,
        "qwen2.5:32b": 24, "qwen3:32b": 24,
        "mistral-large": 48, "mixtral": 32,
        "deepseek-v3": 48, "deepseek-v3.2": 48, "deepseek-r1": 48,
        "kimi-k2.5": 48, "glm-5": 32,
        # Cloud/API models (minimal local RAM — inference via API)
        "glm-4.7:cloud": 2, "minimax-m2.1:cloud": 2,
        # Vision models
        "llava": 8, "llava-phi3": 6, "llava-llama3": 8,
        "llama3.2-vision": 12, "moondream": 4, "qwen2.5vl": 8,
    }

    # Model suitability ratings (1–10 scale)
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
        "phi4-reasoning": {"general": 8, "coding": 9, "reasoning": 10, "creative": 6},
        "phi4-reasoning-plus": {"general": 8, "coding": 9, "reasoning": 10, "creative": 6},
        # Coding specialists
        "qwen3-coder": {"general": 7, "coding": 10, "reasoning": 8, "creative": 5},
        "qwen2.5-coder": {"general": 7, "coding": 10, "reasoning": 8, "creative": 5},
        "deepseek-coder-v2": {"general": 7, "coding": 10, "reasoning": 8, "creative": 5},
        "deepseek-coder": {"general": 6, "coding": 9, "reasoning": 7, "creative": 4},
        "codellama": {"general": 6, "coding": 9, "reasoning": 7, "creative": 5},
        "starcoder2": {"general": 5, "coding": 9, "reasoning": 6, "creative": 4},
        "codegemma": {"general": 6, "coding": 9, "reasoning": 7, "creative": 5},
        "devstral": {"general": 7, "coding": 10, "reasoning": 8, "creative": 5},
        "mimo-v2-flash": {"general": 6, "coding": 10, "reasoning": 7, "creative": 4},
        # Reasoning models
        "deepseek-r1": {"general": 9, "coding": 9, "reasoning": 10, "creative": 7},
        "deepseek-v3": {"general": 9, "coding": 9, "reasoning": 9, "creative": 8},
        "deepseek-v3.2": {"general": 9, "coding": 10, "reasoning": 9, "creative": 8},
        "kimi-k2.5": {"general": 9, "coding": 8, "reasoning": 9, "creative": 8},
        "glm-5": {"general": 9, "coding": 9, "reasoning": 10, "creative": 8},
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
        "qwen2.5vl": {"general": 8, "coding": 6, "reasoning": 7, "creative": 7},
    }

    def __init__(self, api_key: str = "not-needed", model: str | None = None, base_url: str | None = None):
        """Initialize Ollama provider using the official SDK."""
        super().__init__(api_key, model)
        self.base_url = base_url or settings.ollama_base_url
        self.name = "ollama"
        self._client = AsyncClient(host=self.base_url)

    async def stream_completion(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        image_data: str | None = None,
        think: bool = False,
    ) -> AsyncGenerator[str, None]:
        """Stream completion from Ollama via the SDK."""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        if image_data and self.supports_vision():
            messages.append({
                "role": "user",
                "content": prompt,
                "images": [image_data],
            })
        else:
            messages.append({"role": "user", "content": prompt})

        chat_kwargs: dict = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }
        if think:
            chat_kwargs["think"] = True

        try:
            async for chunk in await self._client.chat(**chat_kwargs):
                content = chunk.message.content
                if content:
                    yield content

        except ResponseError as e:
            if e.status_code == 404:
                raise ModelNotFoundError(self.model, provider="ollama")
            raise AIProviderError(f"Ollama API error: {e.error}", provider="ollama")
        except Exception as e:
            msg = str(e).lower()
            if "connect" in msg or "connection" in msg:
                raise ProviderConnectionError(
                    "Cannot connect to Ollama. Make sure Ollama is running (ollama serve)",
                    provider="ollama",
                )
            if "timeout" in msg:
                raise TimeoutError("Ollama request timed out", provider="ollama")
            raise AIProviderError(f"Ollama error: {str(e)}", provider="ollama")

    async def get_structured_completion(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        response_format: "type[BaseModel] | None" = None,
        think: bool = False,
    ) -> str:
        """
        Non-streaming completion with optional structured JSON output.

        When response_format is provided (a Pydantic model class), Ollama constrains
        its output to the model's JSON schema. Returns the raw JSON string.
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        kwargs: dict = {
            "model": self.model,
            "messages": messages,
            "options": {"temperature": temperature},
        }
        if response_format is not None:
            kwargs["format"] = response_format.model_json_schema()
        if think:
            kwargs["think"] = True

        try:
            response = await self._client.chat(**kwargs)
            return response.message.content
        except ResponseError as e:
            if e.status_code == 404:
                raise ModelNotFoundError(self.model, provider="ollama")
            raise AIProviderError(f"Ollama API error: {e.error}", provider="ollama")
        except Exception as e:
            raise AIProviderError(f"Ollama structured completion error: {str(e)}", provider="ollama")

    VISION_MODELS = {"llava", "bakllava", "llava-phi3", "llava-llama3", "vision", "moondream", "qwen2.5vl"}

    def supports_vision(self) -> bool:
        """Check if model supports vision."""
        return any(vm in self.model.lower() for vm in self.VISION_MODELS)

    def count_tokens(self, text: str) -> int:
        """Rough token estimate (4 chars per token)."""
        return len(text) // 4

    def get_default_model(self) -> str:
        """Get default Ollama model."""
        return PROVIDER_CONFIGS.get("ollama", {}).get("default_model", "llama3.2")

    def get_pricing(self) -> tuple[float, float]:
        """Local models are free."""
        return (0.0, 0.0)

    async def list_available_models(self) -> list[str]:
        """List models currently installed in Ollama."""
        try:
            response = await self._client.list()
            return [m.model for m in response.models]
        except Exception as e:
            logger.warning(f"Error listing Ollama models: {e}")
            return []

    async def pull_model(self, model_name: str) -> AsyncGenerator[dict, None]:
        """Pull/download a model; yields progress dicts."""
        try:
            async for progress in await self._client.pull(model_name, stream=True):
                yield {
                    "status": progress.status,
                    "digest": getattr(progress, "digest", None),
                    "total": getattr(progress, "total", None),
                    "completed": getattr(progress, "completed", None),
                }
        except Exception as e:
            yield {"error": str(e)}

    async def check_ollama_status(self) -> dict:
        """Check if Ollama is running, return version and GPU info."""
        try:
            # list() is lightweight and confirms Ollama is reachable
            await self._client.list()

            # Fetch version separately (SDK doesn't expose it directly)
            import httpx
            async with httpx.AsyncClient(timeout=5.0) as http:
                r = await http.get(f"{self.base_url}/api/version")
                version = r.json().get("version", "unknown") if r.is_success else "unknown"

            return {"running": True, "version": version}
        except Exception:
            return {
                "running": False,
                "error": "Ollama is not running. Start it with: ollama serve",
            }

    # ── System resource helpers ──────────────────────────────────────────────

    def check_system_ram(self) -> float:
        """Available system RAM in GB."""
        return psutil.virtual_memory().available / (1024 ** 3)

    def get_total_system_ram(self) -> float:
        """Total system RAM in GB."""
        return psutil.virtual_memory().total / (1024 ** 3)

    def get_gpu_info(self) -> dict:
        """
        Detect GPU/accelerator info for model-running guidance.

        Returns a dict with keys:
            type        – "apple_silicon" | "nvidia" | "none"
            name        – human-readable label
            vram_gb     – effective VRAM in GB (unified memory on Apple Silicon)
            shared      – True when RAM and VRAM are the same pool
            gpus        – list of per-GPU dicts (NVIDIA only)
            note        – optional guidance string
        """
        system = platform.system()
        machine = platform.machine()

        # Apple Silicon: RAM and VRAM are a unified pool
        if system == "Darwin" and machine == "arm64":
            total_ram = self.get_total_system_ram()
            return {
                "type": "apple_silicon",
                "name": "Apple Silicon (Unified Memory)",
                "vram_gb": round(total_ram, 1),
                "shared": True,
                "note": "Unified memory — RAM and VRAM share the same pool",
            }

        # Try NVIDIA via nvidia-smi
        try:
            result = subprocess.run(
                [
                    "nvidia-smi",
                    "--query-gpu=name,memory.total,memory.free",
                    "--format=csv,noheader,nounits",
                ],
                capture_output=True,
                text=True,
                timeout=3,
            )
            if result.returncode == 0 and result.stdout.strip():
                gpus = []
                for line in result.stdout.strip().splitlines():
                    parts = [p.strip() for p in line.split(",")]
                    if len(parts) == 3:
                        name, total_mb, free_mb = parts
                        gpus.append({
                            "name": name,
                            "vram_total_gb": round(int(total_mb) / 1024, 1),
                            "vram_free_gb": round(int(free_mb) / 1024, 1),
                        })
                if gpus:
                    return {
                        "type": "nvidia",
                        "name": gpus[0]["name"],
                        "vram_gb": gpus[0]["vram_total_gb"],
                        "vram_free_gb": gpus[0]["vram_free_gb"],
                        "shared": False,
                        "gpus": gpus,
                    }
        except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
            pass

        return {
            "type": "none",
            "name": "CPU only",
            "vram_gb": None,
            "shared": False,
            "note": "No dedicated GPU detected — models will run on CPU",
        }

    # ── Model suitability helpers ────────────────────────────────────────────

    def can_run_model(self, model_name: str) -> tuple[bool, str]:
        """
        Check if a model can run on the current system.

        For CPU/Apple Silicon systems, checks RAM.
        For NVIDIA GPU systems, checks VRAM if available.
        """
        base_model = model_name.split(":")[0] if ":" in model_name else model_name
        required_ram = (
            self.MODEL_RAM_REQUIREMENTS.get(model_name)
            or self.MODEL_RAM_REQUIREMENTS.get(base_model)
        )

        if required_ram is None:
            return True, f"No RAM requirements defined for {model_name}, should be safe to try"

        gpu = self.get_gpu_info()

        # NVIDIA: check free VRAM
        if gpu["type"] == "nvidia" and gpu.get("vram_free_gb") is not None:
            free_vram = gpu["vram_free_gb"]
            if free_vram >= required_ram:
                return True, f"Model requires {required_ram}GB VRAM, {free_vram:.1f}GB free"
            return False, (
                f"Model requires {required_ram}GB VRAM, only {free_vram:.1f}GB free "
                f"(total: {gpu['vram_gb']}GB)"
            )

        # Apple Silicon / CPU: check available RAM
        available_ram = self.check_system_ram()
        safe_available = available_ram - 2.0  # keep 2GB headroom for OS

        if safe_available >= required_ram:
            return True, f"Model requires {required_ram}GB, {available_ram:.1f}GB available"
        return False, (
            f"Model requires {required_ram}GB, only {available_ram:.1f}GB available "
            f"(total: {self.get_total_system_ram():.1f}GB)"
        )

    def get_recommended_models(self) -> list[dict]:
        """Get models that can run on the current system, sorted by RAM requirement."""
        recommended = []
        for model_name, required_ram in self.MODEL_RAM_REQUIREMENTS.items():
            can_run, message = self.can_run_model(model_name)
            if not can_run:
                continue

            model_info: dict = {
                "name": model_name,
                "ram_required": required_ram,
                "can_run": True,
                "message": message,
            }
            base_model = model_name.split(":")[0]
            if base_model in self.MODEL_SUITABILITY:
                model_info["suitability"] = self.MODEL_SUITABILITY[base_model]

            recommended.append(model_info)

        recommended.sort(key=lambda x: x["ram_required"])
        return recommended

    def get_model_info(self, model_name: str) -> dict:
        """Return RAM requirements, suitability ratings, and compatibility for a model."""
        base_model = model_name.split(":")[0] if ":" in model_name else model_name

        info: dict = {"name": model_name, "base_model": base_model}

        required_ram = (
            self.MODEL_RAM_REQUIREMENTS.get(model_name)
            or self.MODEL_RAM_REQUIREMENTS.get(base_model)
        )
        if required_ram:
            info["ram_required"] = required_ram
            can_run, message = self.can_run_model(model_name)
            info["can_run"] = can_run
            info["message"] = message

        if base_model in self.MODEL_SUITABILITY:
            info["suitability"] = self.MODEL_SUITABILITY[base_model]

        info["supports_vision"] = any(
            vm in model_name.lower() for vm in self.VISION_MODELS
        )

        return info

    # ── Async context manager ────────────────────────────────────────────────

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass  # AsyncClient manages its own connection lifecycle
