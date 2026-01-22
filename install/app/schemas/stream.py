"""Streaming event schemas."""
from pydantic import BaseModel
from typing import Any


class StreamEvent(BaseModel):
    """Schema for Server-Sent Events."""

    type: str
    provider: str | None = None
    model: str | None = None
    content: str | None = None
    iteration: int | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    estimated_cost: float | None = None
    error: str | None = None
    error_code: str | None = None
    data: dict[str, Any] | None = None

    def to_sse(self) -> str:
        """Convert to SSE format."""
        return f"data: {self.model_dump_json()}\n\n"
