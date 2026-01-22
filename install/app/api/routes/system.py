"""System resource monitoring routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.ai_providers.ollama_provider import OllamaProvider
from app.core.config import settings

router = APIRouter()


class RAMStatus(BaseModel):
    """RAM status information."""
    total_gb: float
    available_gb: float
    used_gb: float
    used_percent: float
    status: str  # 'healthy', 'warning', 'critical'
    message: str
    recommended_models: list[dict]
    all_models: list[dict]  # All models with their RAM requirements


@router.get("/ram-status", response_model=RAMStatus)
async def get_ram_status():
    """
    Get current system RAM status and model recommendations.

    Returns:
        RAMStatus: Current RAM usage and recommended models
    """
    try:
        # Create Ollama provider instance to access RAM monitoring methods
        base_url = getattr(settings, "ollama_base_url", "http://localhost:11434")
        ollama = OllamaProvider("not-needed", None, base_url)

        # Get RAM stats
        total_ram = ollama.get_total_system_ram()
        available_ram = ollama.check_system_ram()
        used_ram = total_ram - available_ram
        used_percent = (used_ram / total_ram) * 100

        # Determine status and message
        if available_ram > 8.0:
            status = "healthy"
            message = f"System has plenty of RAM available ({available_ram:.1f}GB free)"
        elif available_ram > 4.0:
            status = "warning"
            message = f"RAM is getting limited ({available_ram:.1f}GB free). Consider using smaller models."
        else:
            status = "critical"
            message = f"RAM is very low ({available_ram:.1f}GB free). Large models may fail to load."

        # Get recommended models (models that can run)
        recommended_models = ollama.get_recommended_models()

        # Get ALL models with their RAM requirements
        all_models = []
        for model_name, required_ram in ollama.MODEL_RAM_REQUIREMENTS.items():
            can_run, msg = ollama.can_run_model(model_name)
            model_info = {
                "name": model_name,
                "ram_required": required_ram,
                "can_run": can_run,
                "message": msg,
            }

            # Add suitability if available
            base_model = model_name.split(":")[0]
            if base_model in ollama.MODEL_SUITABILITY:
                model_info["suitability"] = ollama.MODEL_SUITABILITY[base_model]

            all_models.append(model_info)

        return RAMStatus(
            total_gb=round(total_ram, 2),
            available_gb=round(available_ram, 2),
            used_gb=round(used_ram, 2),
            used_percent=round(used_percent, 1),
            status=status,
            message=message,
            recommended_models=recommended_models,
            all_models=all_models
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get RAM status: {str(e)}")
