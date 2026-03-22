from typing import Protocol

from models.user import User


class UserRepositoryProtocol(Protocol):
    def get_by_email(self, email: str) -> User | None: ...
    def get_by_id(self, id: int) -> User | None: ...
