"""Session schemas."""
from datetime import datetime
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    """Model configuration for each provider."""

    provider: str = Field(..., description="Provider name")
    model: str = Field(..., description="Model name for this provider")


class FileAttachment(BaseModel):
    """File attachment for a session."""

    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type of the file")
    size: int = Field(..., description="File size in bytes")
    extracted_text: str | None = Field(default=None, description="Extracted text content")
    base64_data: str | None = Field(default=None, description="Base64 encoded image data for vision models")


class SessionCreate(BaseModel):
    """Schema for creating a new session."""

    prompt: str = Field(..., min_length=1, description="The user's prompt")
    chair: str = Field(..., description="Provider to act as chair (e.g., 'anthropic')")
    iterations: int = Field(default=1, ge=1, le=10, description="Number of iterations")
    template: str = Field(default="balanced", description="Merge template style")
    preset: str = Field(default="balanced", description="Response preset (creative/balanced/precise)")
    system_prompt: str | None = Field(default=None, description="Global system prompt")
    autopilot: bool = Field(default=False, description="Enable autopilot mode")
    selected_providers: list[str] | None = Field(
        default=None,
        description="Optional list of providers to include. If not provided, uses all configured providers."
    )
    model_configs: list[ModelConfig] | None = Field(
        default=None,
        description="Optional model configuration per provider. If not provided, uses defaults."
    )
    files: list[FileAttachment] | None = Field(
        default=None,
        description="Optional file attachments to include with the prompt"
    )


class SessionResponse(BaseModel):
    """Schema for session creation response."""

    session_id: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SessionSummary(BaseModel):
    """Schema for session summary in list view."""

    id: str
    created_at: datetime
    prompt: str
    status: str
    total_iterations: int
    current_iteration: int
    chair_provider: str

    model_config = {"from_attributes": True}


class SessionList(BaseModel):
    """Schema for paginated session list."""

    sessions: list[SessionSummary]
    total: int


class SessionDetail(BaseModel):
    """Schema for detailed session view."""

    id: str
    created_at: datetime
    updated_at: datetime
    prompt: str
    current_prompt: str | None
    chair_provider: str
    total_iterations: int
    current_iteration: int
    merge_template: str
    preset: str
    status: str
    autopilot: bool
    system_prompt: str | None
    user_guidance: str | None

    model_config = {"from_attributes": True}


class IterationRequest(BaseModel):
    """Schema for triggering next iteration."""

    guidance: str | None = Field(default=None, description="User guidance for iteration")
    excluded_providers: list[str] | None = Field(default=None, description="Providers to exclude")
