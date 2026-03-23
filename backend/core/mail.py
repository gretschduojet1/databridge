import smtplib
from email.message import EmailMessage

from core.config import settings


def send_email(to: str, subject: str, body: str, attachment: bytes | None = None, filename: str | None = None) -> None:
    msg = EmailMessage()
    msg["From"] = settings.mail_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)

    if attachment and filename:
        msg.add_attachment(
            attachment,
            maintype="application",
            subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=filename,
        )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
        server.send_message(msg)
