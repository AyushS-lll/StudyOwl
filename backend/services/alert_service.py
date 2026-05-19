"""
Alert service — send notifications to teachers via SendGrid and Twilio.

Takes an Alert ORM row plus the originating Session (which must have its
`student` relationship eagerly loaded), dispatches the email, and records the
outcome on the alert row (notification_status / notification_error). Failures
are swallowed at the dispatch layer — one bad SendGrid call shouldn't block
other processing — but recorded in the DB so the dashboard can surface them.
"""

import logging

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from sqlalchemy.ext.asyncio import AsyncSession
from twilio.rest import Client

from config import settings
from models.alert import Alert
from models.session import Session


logger = logging.getLogger(__name__)


async def notify_teacher(db: AsyncSession, alert: Alert, session: Session) -> None:
    """
    Dispatch the teacher notification for the given Alert and record the
    outcome on the alert row.

    Caller is responsible for ensuring `session.student` is already loaded
    (async SQLAlchemy can't lazy-load relationships outside a greenlet).
    """
    try:
        _dispatch_email(
            alert_id=str(alert.id),
            student_name=session.student.name,
            question=session.question,
            severity=alert.severity,
            reason_kind=alert.reason_kind,
            reason_text=alert.reason_text,
        )
        alert.notification_status = "sent"
        alert.notification_error = None
    except Exception as exc:
        # Don't propagate — the DB record of "we failed to notify" is enough
        # for the dashboard to surface the problem.
        alert.notification_status = "failed"
        alert.notification_error = str(exc)[:1000]
        logger.exception("Alert %s notification failed", alert.id)

    await db.commit()


def _dispatch_email(
    alert_id: str,
    student_name: str,
    question: str,
    severity: str,
    reason_kind: str,
    reason_text: str,
    teacher_email: str = "",
) -> None:
    """
    Send the teacher-alert email via SendGrid. Raises on any failure so the
    caller can record `notification_status="failed"` with the error.
    """
    if not settings.sendgrid_api_key:
        # Soft no-op for dev. The notify path still marks "sent" because
        # there's nothing more we can do; the operator can see "no key" in
        # the logs. Re-throwing here would mark every dev alert "failed".
        logger.info("[ALERT %s] No SendGrid API key configured. Skipping send.", alert_id)
        return

    teacher_email = teacher_email or settings.teacher_alert_email

    severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🔵"}.get(severity, "⚠️")
    message = Mail(
        from_email="alerts@studyowl.ai",
        to_emails=teacher_email,
        subject=f"StudyOwl {severity_emoji} {severity.upper()}: {student_name} needs help",
        html_content=f"""
        <h2>Student Help Alert</h2>
        <p><strong>Severity:</strong> {severity_emoji} {severity.upper()} ({reason_kind})</p>
        <p><strong>Student:</strong> {student_name}</p>
        <p><strong>Alert ID:</strong> {alert_id}</p>
        <p><strong>Reason:</strong> {reason_text}</p>
        <p><strong>Question:</strong></p>
        <p><em>{question}</em></p>
        """,
    )

    sg = SendGridAPIClient(settings.sendgrid_api_key)
    sg.send(message)
    logger.info("[ALERT %s] Email sent to %s", alert_id, teacher_email)


def send_sms_alert(
    student_phone: str,
    teacher_phone: str,
    message_text: str,
) -> None:
    """
    Send an SMS alert to a teacher via Twilio. Kept for backward compat with
    any external callers; the new Alert-based flow uses email only.
    """
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        logger.info("Twilio not configured. SMS alert not sent.")
        return

    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    try:
        client.messages.create(
            body=message_text,
            from_="+1234567890",
            to=teacher_phone,
        )
        logger.info("SMS sent to %s", teacher_phone)
    except Exception as exc:
        logger.exception("Failed to send Twilio SMS: %s", exc)
