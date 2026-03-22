from typing import Protocol


class WriterProtocol(Protocol):
    """
    Contract for any format writer. Implementations receive column headers
    and rows, and return the serialized file as bytes.

    Adding a new format (e.g. PDF, JSON) means creating a new class that
    satisfies this interface — nothing else needs to change.
    """

    @property
    def extension(self) -> str:
        """File extension, e.g. 'xlsx' or 'txt'"""
        ...

    @property
    def content_type(self) -> str:
        """MIME type for email attachment or HTTP response"""
        ...

    def write(self, columns: list[str], rows: list) -> bytes:
        """Serialize columns + rows to bytes in the target format."""
        ...
