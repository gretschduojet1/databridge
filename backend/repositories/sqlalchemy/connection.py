from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


class SQLAlchemyConnection:
    def __init__(self, session: Session):
        self._session = session

    def fetch_all(self, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        result = self._session.execute(text(sql), params or {})
        return [dict(row._mapping) for row in result]

    def fetch_one(self, sql: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        result = self._session.execute(text(sql), params or {})
        row = result.fetchone()
        return dict(row._mapping) if row else None

    def execute(self, sql: str, params: dict[str, Any] | None = None) -> None:
        self._session.execute(text(sql), params or {})

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
