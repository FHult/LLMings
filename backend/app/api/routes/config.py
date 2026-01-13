"""Configuration API endpoints for managing API keys and settings."""
import os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()


class APIKeyUpdate(BaseModel):
    """Schema for updating an API key."""

    provider: str = Field(..., description="Provider name (openai, anthropic, google, grok)")
    api_key: str = Field(..., min_length=1, description="API key value")


class APIKeyResponse(BaseModel):
    """Response after updating API key."""

    success: bool
    message: str
    provider: str
    configured: bool


def get_env_file_path() -> Path:
    """Get the path to the .env file."""
    # Go up from app/api/routes to backend/
    backend_dir = Path(__file__).parent.parent.parent.parent
    return backend_dir / ".env"


def read_env_file() -> dict[str, str]:
    """Read .env file and return as dict."""
    env_path = get_env_file_path()
    env_vars = {}

    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()

    return env_vars


def write_env_file(env_vars: dict[str, str]) -> None:
    """Write env vars back to .env file."""
    env_path = get_env_file_path()

    with open(env_path, 'w') as f:
        f.write("# HiveCouncil Environment Variables\n\n")

        # API Keys section
        f.write("# AI Provider API Keys\n")
        for key in ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY', 'GROK_API_KEY']:
            if key in env_vars:
                f.write(f"{key}={env_vars[key]}\n")

        f.write("\n# Database\n")
        if 'DATABASE_URL' in env_vars:
            f.write(f"DATABASE_URL={env_vars['DATABASE_URL']}\n")
        else:
            f.write("DATABASE_URL=sqlite+aiosqlite:///./hivecouncil.db\n")

        f.write("\n# CORS Origins\n")
        if 'CORS_ORIGINS' in env_vars:
            f.write(f"CORS_ORIGINS={env_vars['CORS_ORIGINS']}\n")
        else:
            f.write('CORS_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173"]\n')

        # Add any other custom vars
        other_vars = {k: v for k, v in env_vars.items()
                     if k not in ['OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'GOOGLE_API_KEY',
                                 'GROK_API_KEY', 'DATABASE_URL', 'CORS_ORIGINS']}
        if other_vars:
            f.write("\n# Other Settings\n")
            for key, value in other_vars.items():
                f.write(f"{key}={value}\n")


@router.post("/config/api-key", response_model=APIKeyResponse)
async def update_api_key(update: APIKeyUpdate):
    """
    Update an API key for a provider.

    This endpoint updates the .env file with the new API key and updates
    the environment variable for the current process.

    Note: The provider factory will need to be reinitialized after this,
    which currently requires a backend restart.
    """
    # Validate provider name
    valid_providers = ['openai', 'anthropic', 'google', 'grok']
    if update.provider not in valid_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider. Must be one of: {', '.join(valid_providers)}"
        )

    # Map provider name to env var name
    env_key_map = {
        'openai': 'OPENAI_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY',
        'google': 'GOOGLE_API_KEY',
        'grok': 'GROK_API_KEY',
    }

    env_key = env_key_map[update.provider]

    try:
        # Read current .env file
        env_vars = read_env_file()

        # Update the API key
        env_vars[env_key] = update.api_key

        # Write back to .env file
        write_env_file(env_vars)

        # Update the environment variable for current process
        os.environ[env_key] = update.api_key

        return APIKeyResponse(
            success=True,
            message=f"API key for {update.provider} has been saved. Please restart the backend to use the new key.",
            provider=update.provider,
            configured=True
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update API key: {str(e)}"
        )


@router.delete("/config/api-key/{provider}")
async def delete_api_key(provider: str):
    """
    Remove an API key for a provider.

    This removes the API key from the .env file and environment.
    """
    valid_providers = ['openai', 'anthropic', 'google', 'grok']
    if provider not in valid_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid provider. Must be one of: {', '.join(valid_providers)}"
        )

    env_key_map = {
        'openai': 'OPENAI_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY',
        'google': 'GOOGLE_API_KEY',
        'grok': 'GROK_API_KEY',
    }

    env_key = env_key_map[provider]

    try:
        # Read current .env file
        env_vars = read_env_file()

        # Remove the API key if it exists
        if env_key in env_vars:
            del env_vars[env_key]

        # Write back to .env file
        write_env_file(env_vars)

        # Remove from environment
        if env_key in os.environ:
            del os.environ[env_key]

        return {
            "success": True,
            "message": f"API key for {provider} has been removed.",
            "provider": provider,
            "configured": False
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to remove API key: {str(e)}"
        )
