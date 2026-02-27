"""Pydantic models for structured consensus output from Ollama chair synthesis."""
from pydantic import BaseModel, Field


class ConsensusOutput(BaseModel):
    """Structured output produced by an Ollama chair when synthesizing council responses."""

    synthesis: str = Field(
        description="The complete, ready-to-use consensus output that directly addresses the original prompt"
    )
    key_agreements: list[str] = Field(
        description="Points where all or most council members converged",
        default_factory=list,
    )
    key_disagreements: list[str] = Field(
        description="Points where council members held meaningfully different views",
        default_factory=list,
    )
    confidence: float = Field(
        description="Chair's confidence in the synthesis quality, from 0.0 (low) to 1.0 (high)",
        ge=0.0,
        le=1.0,
        default=0.8,
    )
    reasoning: str = Field(
        description="Brief explanation of how the chair weighted and combined the council inputs",
        default="",
    )
