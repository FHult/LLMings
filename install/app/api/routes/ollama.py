"""API routes for Ollama provider management."""
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.ai_providers.ollama_provider import OllamaProvider
from app.services.mlx_model_manager import MLXModelManager
from app.core.config import settings

router = APIRouter()


class PullModelRequest(BaseModel):
    """Request to pull a model from Ollama library."""
    model_name: str


class DownloadMLXRequest(BaseModel):
    """Request to download MLX model from HuggingFace."""
    model_key: str
    custom_repo: str | None = None


@router.get("/ollama/status")
async def get_ollama_status():
    """Check if Ollama is running and get version info."""
    async with OllamaProvider() as provider:
        status = await provider.check_ollama_status()

        if status["running"]:
            # Add system RAM info
            status["system_ram"] = {
                "total_gb": provider.get_total_system_ram(),
                "available_gb": provider.check_system_ram(),
            }

        return status


@router.get("/ollama/models")
async def list_ollama_models():
    """List all models available in local Ollama installation."""
    async with OllamaProvider() as provider:
        models = await provider.list_available_models()

        # Add model info for each
        models_with_info = []
        for model_name in models:
            info = provider.get_model_info(model_name)
            models_with_info.append(info)

        return {
            "models": models_with_info,
            "count": len(models_with_info),
        }


@router.get("/ollama/recommended")
async def get_recommended_models():
    """Get models recommended for current system based on available RAM."""
    async with OllamaProvider() as provider:
        recommended = provider.get_recommended_models()

        return {
            "recommended": recommended,
            "system_ram": {
                "total_gb": provider.get_total_system_ram(),
                "available_gb": provider.check_system_ram(),
            },
        }


@router.get("/ollama/models/{model_name}/info")
async def get_model_info(model_name: str):
    """Get detailed info about a specific model."""
    async with OllamaProvider() as provider:
        info = provider.get_model_info(model_name)

        # Check if model is installed
        installed_models = await provider.list_available_models()
        info["installed"] = model_name in installed_models

        return info


@router.post("/ollama/models/pull")
async def pull_model(request: PullModelRequest):
    """
    Pull/download a model from Ollama library.

    Returns a streaming response with download progress.
    """
    async def stream_pull():
        """Stream pull progress."""
        async with OllamaProvider() as provider:
            # Check if model can run first
            can_run, message = provider.can_run_model(request.model_name)

            if not can_run:
                yield f'data: {{"error": "{message}"}}\n\n'
                return

            async for status in provider.pull_model(request.model_name):
                import json
                yield f"data: {json.dumps(status)}\n\n"

                if "error" in status:
                    break

                # Check if download is complete
                if status.get("status") == "success":
                    break

    return StreamingResponse(
        stream_pull(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.get("/ollama/mlx/available")
async def list_available_mlx_models():
    """List popular MLX models available for download."""
    manager = MLXModelManager()
    models = manager.list_popular_models()

    return {
        "models": models,
        "count": len(models),
    }


@router.post("/ollama/mlx/download")
async def download_mlx_model(request: DownloadMLXRequest):
    """
    Download MLX model from HuggingFace and import to Ollama.

    Returns a streaming response with download progress.
    """
    async def stream_download():
        """Stream download progress."""
        manager = MLXModelManager()

        async for status in manager.download_mlx_model(
            request.model_key,
            request.custom_repo
        ):
            import json
            yield f"data: {json.dumps(status)}\n\n"

            if "error" in status:
                break

            if status.get("status") == "complete":
                break

    return StreamingResponse(
        stream_download(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.delete("/ollama/models/{model_name}")
async def delete_model(model_name: str):
    """Delete a model from Ollama."""
    import httpx

    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                f"{settings.ollama_base_url}/api/delete",
                json={"name": model_name}
            )
            response.raise_for_status()

            return {"success": True, "message": f"Model {model_name} deleted"}
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Failed to delete model: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error deleting model: {str(e)}"
            )
