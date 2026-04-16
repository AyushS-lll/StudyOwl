"""
Attempt model — represents a single student answer attempt.
"""

from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from db import Base
from datetime import datetime, timezone


class Attempt(Base):
    __tablename__ = "attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False)
    attempt_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    hint_shown = Column(Text, nullable=True)  # The hint that was shown before this attempt
    hint_level = Column(Integer, nullable=False)  # The level at which this attempt was made
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    session = relationship("Session", back_populates="attempts")

    def __repr__(self) -> str:
        return f"<Attempt {self.id} (level {self.hint_level}) - {'✓' if self.is_correct else '✗'}>"
