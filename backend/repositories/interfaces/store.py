from typing import Protocol

from schemas.store import StoreDetail, StoreSummary


class StoreRepositoryProtocol(Protocol):
    def get_all(
        self,
        skip: int = 0,
        limit: int = 25,
        region: str | None = None,
        search: str | None = None,
        low_stock_only: bool = False,
    ) -> list[StoreSummary]: ...

    def count(
        self,
        region: str | None = None,
        search: str | None = None,
        low_stock_only: bool = False,
    ) -> int: ...

    def get_by_id(self, id: int) -> StoreDetail | None: ...
