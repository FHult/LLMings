"""Settings database model."""
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime

from app.core.database import Base


class Settings(Base):
    """Settings model for storing user preferences."""

    __tablename__ = "settings"

    key = Column(String, primary_key=True)
    value = Column(Text, nullable=False)  # JSON serialized
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Settings(key={self.key}, value={self.value[:50]}...)>"
