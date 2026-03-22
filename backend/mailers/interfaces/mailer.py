from typing import Protocol


class MailerProtocol(Protocol):
    def send(
        self,
        to: str,
        subject: str,
        body: str,
        attachment: bytes | None = None,
        filename: str | None = None,
        content_type: str | None = None,
    ) -> None: ...
