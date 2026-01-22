"""Response schemas."""
from datetime import datetime
from pydantic import BaseModel


class ResponseSchema(BaseModel):
    """Schema for AI response."""

    id: str
    created_at: datetime
    session_id: str
    provider: str
    model: str
    content: str
    iteration: int
    role: str
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    response_time_ms: int
    error: str | None

    model_config = {"from_attributes": True}
