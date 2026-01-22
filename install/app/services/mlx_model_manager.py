"""MLX model manager for downloading and converting HuggingFace models."""
import logging
import os
import subprocess
from pathlib import Path
from typing import AsyncGenerator
import httpx

logger = logging.getLogger(__name__)


class MLXModelManager:
    """Manage MLX models from HuggingFace for local inference."""

    def __init__(self, models_dir: str = None):
        """Initialize MLX model manager.

        Args:
            models_dir: Directory to store downloaded models
        """
        if models_dir is None:
            # Default to ~/.hivecouncil/models
            models_dir = os.path.expanduser("~/.hivecouncil/models")

        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)
        self.client = httpx.AsyncClient(timeout=300.0)

    # Popular MLX-compatible models on HuggingFace
    POPULAR_MLX_MODELS = {
        "llama-3.1-8b": {
            "repo": "mlx-community/Meta-Llama-3.1-8B-Instruct-4bit",
            "description": "Llama 3.1 8B - Fast, high quality",
            "size": "4.9GB",
            "quantization": "4-bit",
        },
        "llama-3-8b": {
            "repo": "mlx-community/Meta-Llama-3-8B-Instruct-4bit",
            "description": "Llama 3 8B - Reliable, well-tested",
            "size": "4.9GB",
            "quantization": "4-bit",
        },
        "mistral-7b": {
            "repo": "mlx-community/Mistral-7B-Instruct-v0.3-4bit",
            "description": "Mistral 7B - Excellent reasoning",
            "size": "4.1GB",
            "quantization": "4-bit",
        },
        "phi-3-mini": {
            "repo": "mlx-community/Phi-3-mini-4k-instruct-4bit",
            "description": "Phi-3 Mini - Compact, efficient",
            "size": "2.4GB",
            "quantization": "4-bit",
        },
        "gemma-2-9b": {
            "repo": "mlx-community/gemma-2-9b-it-4bit",
            "description": "Gemma 2 9B - Google's latest",
            "size": "5.4GB",
            "quantization": "4-bit",
        },
        "qwen-2-7b": {
            "repo": "mlx-community/Qwen2-7B-Instruct-4bit",
            "description": "Qwen 2 7B - Excellent multilingual",
            "size": "4.4GB",
            "quantization": "4-bit",
        },
    }

    async def download_mlx_model(
        self,
        model_key: str,
        custom_repo: str = None
    ) -> AsyncGenerator[dict, None]:
        """
        Download an MLX model from HuggingFace.

        Args:
            model_key: Key from POPULAR_MLX_MODELS or "custom"
            custom_repo: Custom HuggingFace repo (if model_key is "custom")

        Yields:
            Status updates during download
        """
        # Get repo info
        if custom_repo:
            repo = custom_repo
            model_name = repo.split("/")[-1]
        elif model_key in self.POPULAR_MLX_MODELS:
            repo = self.POPULAR_MLX_MODELS[model_key]["repo"]
            model_name = model_key
        else:
            yield {"error": f"Unknown model: {model_key}"}
            return

        model_path = self.models_dir / model_name

        # Check if already downloaded
        if model_path.exists():
            yield {
                "status": "complete",
                "message": f"Model already exists at {model_path}",
                "path": str(model_path)
            }
            return

        yield {"status": "starting", "message": f"Downloading {repo}..."}

        try:
            # Use huggingface-cli to download
            # Note: Requires huggingface-hub installed
            process = await self._run_hf_download(repo, str(model_path))

            async for update in process:
                yield update

            # Verify download
            if model_path.exists():
                yield {
                    "status": "complete",
                    "message": f"Model downloaded successfully",
                    "path": str(model_path)
                }

                # Convert to Ollama Modelfile format
                yield {"status": "converting", "message": "Creating Ollama model..."}
                await self._create_ollama_model(model_name, model_path)

                yield {
                    "status": "ready",
                    "message": f"Model '{model_name}' ready to use in Ollama"
                }
            else:
                yield {"error": "Download completed but model files not found"}

        except Exception as e:
            yield {"error": f"Download failed: {str(e)}"}

    async def _run_hf_download(self, repo: str, output_path: str) -> AsyncGenerator[dict, None]:
        """Run huggingface-cli download command."""
        try:
            # Use git clone for simplicity (could use huggingface_hub library for better progress)
            cmd = [
                "git", "clone",
                f"https://huggingface.co/{repo}",
                output_path
            ]

            yield {"status": "downloading", "message": "Cloning repository..."}

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            # Read output
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    yield {
                        "status": "downloading",
                        "message": line.strip()
                    }

            # Check return code
            if process.returncode != 0:
                stderr = process.stderr.read()
                raise Exception(f"Git clone failed: {stderr}")

        except FileNotFoundError:
            yield {
                "error": "git not found. Please install git or use: brew install git"
            }
        except Exception as e:
            yield {"error": str(e)}

    async def _create_ollama_model(self, model_name: str, model_path: Path):
        """Create an Ollama model from downloaded MLX weights."""
        # Create Modelfile
        modelfile_content = f"""FROM {model_path}
TEMPLATE \"\"\"{{{{ if .System }}}}{{{{ .System }}}}{{{{ end }}}}{{{{ if .Prompt }}}}{{{{ .Prompt }}}}{{{{ end }}}}\"\"\"
PARAMETER temperature 0.7
PARAMETER top_p 0.9
"""

        modelfile_path = model_path / "Modelfile"
        modelfile_path.write_text(modelfile_content)

        # Import into Ollama
        try:
            subprocess.run(
                ["ollama", "create", model_name, "-f", str(modelfile_path)],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create Ollama model: {e.stderr}")
        except FileNotFoundError:
            logger.warning("Ollama CLI not found. Model downloaded but not imported to Ollama.")

    async def list_downloaded_models(self) -> list[dict]:
        """List models downloaded to local storage."""
        models = []

        if not self.models_dir.exists():
            return models

        for model_dir in self.models_dir.iterdir():
            if model_dir.is_dir():
                # Get model info
                size = sum(f.stat().st_size for f in model_dir.rglob('*') if f.is_file())
                models.append({
                    "name": model_dir.name,
                    "path": str(model_dir),
                    "size_gb": round(size / (1024**3), 2),
                })

        return models

    async def delete_model(self, model_name: str) -> bool:
        """Delete a downloaded model."""
        model_path = self.models_dir / model_name

        if not model_path.exists():
            return False

        try:
            import shutil
            shutil.rmtree(model_path)
            return True
        except Exception as e:
            logger.error(f"Failed to delete model: {e}")
            return False

    def list_popular_models(self) -> dict:
        """Get list of popular MLX models available for download."""
        return self.POPULAR_MLX_MODELS

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
