"""Response database model."""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship

from app.core.database import Base


class Response(Base):
    """Response model representing an AI's response in a session."""

    __tablename__ = "responses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Foreign key
    session_id = Column(String, ForeignKey("sessions.id"), nullable=False)

    # Provider info
    provider = Column(String, nullable=False)  # 'openai', 'anthropic', etc.
    model = Column(String, nullable=False)  # 'gpt-4o', 'claude-sonnet-3.5', etc.

    # Content
    content = Column(Text, nullable=False)

    # Iteration context
    iteration = Column(Integer, default=1, nullable=False)
    role = Column(String, nullable=False)  # 'council' or 'chair'

    # Metadata
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)
    response_time_ms = Column(Integer, default=0)

    # Error tracking
    error = Column(Text, nullable=True)

    # Relationship
    session = relationship("Session", back_populates="responses")

    def __repr__(self):
        return f"<Response(id={self.id}, provider={self.provider}, role={self.role}, iteration={self.iteration})>"
