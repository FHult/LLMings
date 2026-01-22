"""Session database model."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, Boolean
from sqlalchemy.orm import relationship

from app.core.database import Base


class Session(Base):
    """Session model representing a council conversation."""

    __tablename__ = "sessions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Original prompt
    prompt = Column(Text, nullable=False)

    # Current iteration prompt (changes each iteration)
    current_prompt = Column(Text, nullable=True)

    # Configuration
    chair_provider = Column(String, nullable=False)  # e.g., 'anthropic'
    total_iterations = Column(Integer, default=1, nullable=False)
    current_iteration = Column(Integer, default=0, nullable=False)
    merge_template = Column(String, default="balanced", nullable=False)
    preset = Column(String, default="balanced", nullable=False)

    # User inputs
    system_prompt = Column(Text, nullable=True)
    user_guidance = Column(Text, nullable=True)

    # Status: 'pending', 'running', 'paused', 'completed', 'failed'
    status = Column(String, default="pending", nullable=False)

    # Provider selection (JSON arrays)
    # Note: selected_providers is deprecated - use council_members instead
    selected_providers = Column(Text, nullable=True)  # [DEPRECATED] JSON serialized list
    excluded_providers = Column(Text, nullable=True)  # JSON serialized list (for iterations)

    # Council members configuration
    council_members = Column(Text, nullable=True)  # JSON serialized list of council member configs

    # Autopilot mode
    autopilot = Column(Boolean, default=False, nullable=False)

    # Relationships
    responses = relationship("Response", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Session(id={self.id}, prompt={self.prompt[:50]}..., status={self.status})>"
