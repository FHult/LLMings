"""Application configuration."""
import logging
import warnings
from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow"
    )

    # API Keys
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_api_key: str | None = None
    grok_api_key: str | None = None

    # Model Selection (optional - will use defaults if not specified)
    openai_model: str | None = None
    anthropic_model: str | None = None
    google_model: str | None = None
    grok_model: str | None = None

    # Database
    database_url: str = "sqlite+aiosqlite:///./hivecouncil.db"

    # Default Settings
    default_chair: str = "anthropic"
    default_iterations: int = 3
    default_template: str = "balanced"
    default_preset: str = "balanced"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]

    @property
    def configured_providers(self) -> list[str]:
        """Return list of providers with valid API keys or local providers."""
        providers = []
        if self.openai_api_key:
            providers.append("openai")
        if self.anthropic_api_key:
            providers.append("anthropic")
        if self.google_api_key:
            providers.append("google")
        if self.grok_api_key:
            providers.append("grok")

        # Always include Ollama (local, no API key needed)
        providers.append("ollama")

        return providers

    def validate_environment(self) -> list[str]:
        """
        Validate environment configuration and return list of warnings.

        Returns:
            List of warning messages (empty if all is well)
        """
        issues: list[str] = []

        # Check if at least one cloud provider is configured
        cloud_providers = [
            self.openai_api_key,
            self.anthropic_api_key,
            self.google_api_key,
            self.grok_api_key,
        ]

        if not any(cloud_providers):
            issues.append(
                "No cloud AI providers configured. Only Ollama (local) will be available. "
                "Set OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY, or GROK_API_KEY to enable cloud providers."
            )

        # Validate API key formats (basic checks)
        if self.openai_api_key and not self.openai_api_key.startswith("sk-"):
            issues.append("OPENAI_API_KEY doesn't appear to be in the expected format (should start with 'sk-')")

        if self.anthropic_api_key and not self.anthropic_api_key.startswith("sk-ant-"):
            issues.append("ANTHROPIC_API_KEY doesn't appear to be in the expected format (should start with 'sk-ant-')")

        # Check database URL
        if not self.database_url:
            issues.append("DATABASE_URL is not set. Using default SQLite database.")

        # Check CORS origins for production
        localhost_origins = [o for o in self.cors_origins if "localhost" in o or "127.0.0.1" in o]
        if len(localhost_origins) == len(self.cors_origins):
            issues.append(
                "CORS_ORIGINS only contains localhost addresses. "
                "Update this for production deployments."
            )

        return issues

    def log_configuration_status(self) -> None:
        """Log the current configuration status."""
        logger.info("=" * 50)
        logger.info("LLMings Configuration Status")
        logger.info("=" * 50)

        # Log configured providers
        providers = self.configured_providers
        logger.info(f"Configured providers: {', '.join(providers)}")

        # Log any validation issues
        issues = self.validate_environment()
        if issues:
            logger.warning("Configuration warnings:")
            for issue in issues:
                logger.warning(f"  - {issue}")
        else:
            logger.info("All configuration checks passed!")

        logger.info("=" * 50)


settings = Settings()
