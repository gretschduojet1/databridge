import smtplib
from email.message import EmailMessage

from core.config import settings


class SmtpMailer:
    def send(
        self,
        to: str,
        subject: str,
        body: str,
        attachment: bytes | None = None,
        filename: str | None = None,
        content_type: str | None = None,
    ) -> None:
        msg = EmailMessage()
        msg["From"]    = settings.mail_from
        msg["To"]      = to
        msg["Subject"] = subject
        msg.set_content(body)

        if attachment and filename:
            maintype, subtype = (content_type or "application/octet-stream").split("/", 1)
            msg.add_attachment(attachment, maintype=maintype, subtype=subtype, filename=filename)

        with smtplib.SMTP(settings.smtp_host, settings.smtp_port) as server:
            server.send_message(msg)
