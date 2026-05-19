"""
Alert model — one row per teacher alert event.

Replaces the boolean `Session.teacher_alerted` flag with a real audit trail:
when an alert fired, why (kind + severity), whether the email/SMS went out,
and whether a teacher has acknowledged or resolved it.

A single session can have multiple alerts of different kinds (e.g. distress
followed by repeated_failure). Same-kind dedup is enforced at insert time by
the service layer (see session_manager._trigger_alert).
"""

from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID

from db import Base
from datetime import datetime, timezone


# Reason kinds — keep in code, not config, so adding one is a deliberate change.
REASON_DISTRESS = "distress"
REASON_REPEATED_FAILURE = "repeated_failure"
REASON_INACTIVITY = "inactivity"
REASON_LEGACY = "legacy"  # used only for the one-shot backfill

SEVERITY_LOW = "low"
SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"


# Default severity for each reason kind. Kept in code so changes are reviewable.
SEVERITY_FOR_REASON = {
    REASON_DISTRESS: SEVERITY_HIGH,
    REASON_REPEATED_FAILURE: SEVERITY_MEDIUM,
    REASON_INACTIVITY: SEVERITY_LOW,
    REASON_LEGACY: SEVERITY_MEDIUM,
}


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False, index=True)
    student_id = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=False, index=True)

    severity = Column(String(16), nullable=False)
    reason_kind = Column(String(32), nullable=False)
    reason_text = Column(Text, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    notification_status = Column(String(16), nullable=False, default="pending")
    notification_error = Column(Text, nullable=True)

    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    acknowledged_by = Column(UUID(as_uuid=True), ForeignKey("students.id"), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships — explicit foreign_keys because acknowledged_by also points at students.
    session = relationship("Session")
    student = relationship("Student", foreign_keys=[student_id])
    acknowledger = relationship("Student", foreign_keys=[acknowledged_by])

    # The unresolved-alerts query is the dashboard's hot path; index it.
    __table_args__ = (
        Index("ix_alerts_resolved_at_created_at", "resolved_at", "created_at"),
    )

    def __repr__(self) -> str:
        state = "resolved" if self.resolved_at else (
            "acked" if self.acknowledged_at else "open"
        )
        return f"<Alert {self.id} ({self.reason_kind}/{self.severity}) — {state}>"
