"""
Alert service — send notifications to teachers via SendGrid and Twilio.
"""

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from twilio.rest import Client

from config import settings


async def notify_teacher(session, reason: str) -> None:
    """
    Notify a teacher that a student needs help.

    Args:
        session: The Session ORM object.
        reason: Why the alert is being sent.
    """
    send_teacher_alert(
        session_id=str(session.id),
        student_name=session.student.name,
        question=session.question,
        reason=reason,
    )


def send_teacher_alert(
    session_id: str,
    student_name: str,
    question: str,
    reason: str,
    teacher_email: str = "",
) -> None:
    """
    Send a teacher alert via email (SendGrid) when a student is stuck.

    Args:
        session_id: The homework session ID.
        student_name: The student's name.
        question: The homework question.
        reason: Why the alert was triggered.
        teacher_email: The teacher's email (defaults to settings).
    """
    if not settings.sendgrid_api_key:
        print("[ALERT] No SendGrid API key configured. Alert not sent.")
        return

    teacher_email = teacher_email or settings.teacher_alert_email

    message = Mail(
        from_email="alerts@studyowl.ai",
        to_emails=teacher_email,
        subject=f"StudyOwl: {student_name} needs help",
        html_content=f"""
        <h2>Student Help Alert</h2>
        <p><strong>Student:</strong> {student_name}</p>
        <p><strong>Session ID:</strong> {session_id}</p>
        <p><strong>Reason:</strong> {reason}</p>
        <p><strong>Question:</strong></p>
        <p><em>{question}</em></p>
        <p><a href="https://studyowl.ai/teacher/session/{session_id}">View session →</a></p>
        """,
    )

    sg = SendGridAPIClient(settings.sendgrid_api_key)
    try:
        sg.send(message)
        print(f"[ALERT] Email sent to {teacher_email}")
    except Exception as e:
        print(f"[ERROR] Failed to send SendGrid alert: {e}")


def send_sms_alert(
    student_phone: str,
    teacher_phone: str,
    message_text: str,
) -> None:
    """
    Send an SMS alert to a teacher via Twilio.

    Args:
        student_phone: Student's phone number (for context).
        teacher_phone: Teacher's phone number (alert destination).
        message_text: The alert message.
    """
    if not settings.twilio_account_sid or not settings.twilio_auth_token:
        print("[ALERT] Twilio not configured. SMS alert not sent.")
        return

    client = Client(settings.twilio_account_sid, settings.twilio_auth_token)
    try:
        client.messages.create(
            body=message_text,
            from_="+1234567890",  # Replace with actual Twilio phone number
            to=teacher_phone,
        )
        print(f"[ALERT] SMS sent to {teacher_phone}")
    except Exception as e:
        print(f"[ERROR] Failed to send Twilio SMS: {e}")
