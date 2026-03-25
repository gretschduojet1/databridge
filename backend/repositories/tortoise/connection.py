"""
Tortoise ORM implementation of DataConnectionProtocol.

Tortoise is async-native, so each method bridges to async via a fresh event loop.
This is safe for sync FastAPI routes because they run in a thread pool, not the
main event loop. For fully async FastAPI routes, remove the bridge and use
`await` directly.

To activate: change container.py get_connection() to return TortoiseConnection().
Tortoise must be initialized at app startup — see setup instructions below.

Setup (in main.py):
    from tortoise.contrib.fastapi import register_tortoise
    register_tortoise(app, db_url=settings.database_url, modules={})

Dependencies (add to requirements.txt):
    tortoise-orm==0.21.7
    asyncpg==0.30.0
"""

import asyncio
import re
from typing import Any

from tortoise import Tortoise


def _run(coro: Any) -> Any:
    """Run a coroutine synchronously from a thread-pool context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _convert_params(sql: str, params: dict[str, Any] | None) -> tuple[str, list[Any]]:
    """
    Convert SQLAlchemy-style named params (:name) to asyncpg positional ($1, $2).
    Preserves insertion order so values align with placeholders.
    """
    if not params:
        return sql, []
    values: list[Any] = []
    counter = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal counter
        counter += 1
        values.append(params[match.group(1)])
        return f"${counter}"

    return re.sub(r":(\w+)", replace, sql), values


class TortoiseConnection:
    def fetch_all(self, sql: str, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        async def _inner() -> list[dict[str, Any]]:
            converted_sql, values = _convert_params(sql, params)
            conn = Tortoise.get_connection("default")
            _, rows = await conn.execute_query_dict(converted_sql, values)
            return rows

        return _run(_inner())

    def fetch_one(self, sql: str, params: dict[str, Any] | None = None) -> dict[str, Any] | None:
        rows = self.fetch_all(sql, params)
        return rows[0] if rows else None

    def execute(self, sql: str, params: dict[str, Any] | None = None) -> None:
        async def _inner() -> None:
            converted_sql, values = _convert_params(sql, params)
            conn = Tortoise.get_connection("default")
            await conn.execute_query(converted_sql, values)

        _run(_inner())

    def commit(self) -> None:
        # Tortoise auto-commits by default on each execute_query call.
        # For explicit transaction control, wrap operations in
        # `async with in_transaction()` instead.
        pass

    def rollback(self) -> None:
        pass
