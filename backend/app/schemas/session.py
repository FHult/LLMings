"""Session schemas."""
from datetime import datetime
from pydantic import BaseModel, Field, model_validator

from app.core.validation import (
    MAX_PROMPT_LENGTH,
    MIN_PROMPT_LENGTH,
    MAX_ITERATIONS,
    MIN_ITERATIONS,
    MAX_COUNCIL_MEMBERS,
    MIN_COUNCIL_MEMBERS,
)


class ModelConfig(BaseModel):
    """Model configuration for each provider."""

    provider: str = Field(..., description="Provider name")
    model: str = Field(..., description="Model name for this provider")


class CouncilMember(BaseModel):
    """Council member configuration with personality."""

    id: str = Field(..., description="Unique identifier for this council member")
    provider: str = Field(..., description="Provider name (openai, anthropic, ollama, etc.)")
    model: str = Field(..., description="Model name to use")
    role: str = Field(..., description="Display name/role for this member")
    archetype: str = Field(default="balanced", description="Personality archetype ID")
    custom_personality: str | None = Field(default=None, description="Custom personality instructions")
    is_chair: bool = Field(default=False, description="Whether this member is the chair")


class FileAttachment(BaseModel):
    """File attachment for a session."""

    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME type of the file")
    size: int = Field(..., description="File size in bytes")
    extracted_text: str | None = Field(default=None, description="Extracted text content")
    base64_data: str | None = Field(default=None, description="Base64 encoded image data for vision models")


class SessionCreate(BaseModel):
    """Schema for creating a new session."""

    prompt: str = Field(..., min_length=MIN_PROMPT_LENGTH, max_length=MAX_PROMPT_LENGTH, description="The user's prompt")
    council_members: list[CouncilMember] = Field(..., min_length=MIN_COUNCIL_MEMBERS, max_length=MAX_COUNCIL_MEMBERS, description="Council members configuration")
    iterations: int = Field(default=1, ge=MIN_ITERATIONS, le=MAX_ITERATIONS, description="Number of iterations")
    template: str = Field(default="balanced", description="Merge template style")
    preset: str = Field(default="balanced", description="Response preset (creative/balanced/precise)")
    system_prompt: str | None = Field(default=None, max_length=MAX_PROMPT_LENGTH, description="Global system prompt (overrides member personalities if provided)")
    autopilot: bool = Field(default=False, description="Enable autopilot mode")
    files: list[FileAttachment] | None = Field(
        default=None,
        description="Optional file attachments to include with the prompt"
    )
    resume_state: dict | None = Field(
        default=None,
        description="State data for resuming a paused session"
    )

    @model_validator(mode="after")
    def validate_chair_member(self) -> "SessionCreate":
        """Validate that exactly one council member is marked as chair."""
        if self.council_members:
            chair_count = sum(1 for m in self.council_members if m.is_chair)
            if chair_count == 0:
                raise ValueError("At least one council member must be designated as chair (is_chair=True)")
            if chair_count > 1:
                raise ValueError(f"Only one council member can be chair, but {chair_count} are marked as chair")
        return self


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
