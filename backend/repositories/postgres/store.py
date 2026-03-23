from typing import Any

from sqlalchemy import case, func
from sqlalchemy.orm import Session

from models.product import Product
from models.store import StoreLocation, StoreStock
from schemas.store import StoreDetail, StoreStockItem, StoreSummary


def _base_query(db: Session, region: str | None, search: str | None, low_stock_only: bool) -> Any:
    low_stock_flag = case((StoreStock.qty_on_hand <= StoreStock.reorder_level, 1), else_=0)

    q = (
        db.query(
            StoreLocation,
            func.count(StoreStock.id).label("total_products"),
            func.sum(low_stock_flag).label("low_stock_count"),
        )
        .outerjoin(StoreStock, StoreLocation.id == StoreStock.store_id)
        .group_by(StoreLocation.id)
    )

    if region:
        q = q.filter(StoreLocation.region == region)
    if search:
        term = f"%{search}%"
        q = q.filter(StoreLocation.name.ilike(term) | StoreLocation.city.ilike(term))
    if low_stock_only:
        q = q.having(func.sum(low_stock_flag) > 0)

    return q


class PostgresStoreRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(
        self,
        skip: int = 0,
        limit: int = 25,
        region: str | None = None,
        search: str | None = None,
        low_stock_only: bool = False,
    ) -> list[StoreSummary]:
        rows = (
            _base_query(self.db, region, search, low_stock_only)
            .order_by(StoreLocation.name)
            .offset(skip)
            .limit(limit)
            .all()
        )
        return [
            StoreSummary(
                id=store.id,
                name=store.name,
                city=store.city,
                region=store.region,
                total_products=total or 0,
                low_stock_count=low or 0,
            )
            for store, total, low in rows
        ]

    def count(
        self,
        region: str | None = None,
        search: str | None = None,
        low_stock_only: bool = False,
    ) -> int:
        return _base_query(self.db, region, search, low_stock_only).count()

    def get_by_id(self, id: int) -> StoreDetail | None:
        store = self.db.query(StoreLocation).filter(StoreLocation.id == id).first()
        if not store:
            return None

        rows = (
            self.db.query(StoreStock, Product)
            .join(Product, StoreStock.product_id == Product.id)
            .filter(StoreStock.store_id == id)
            .order_by(Product.name)
            .all()
        )

        return StoreDetail(
            id=store.id,
            name=store.name,
            city=store.city,
            region=store.region,
            inventory=[
                StoreStockItem(
                    product_id=product.id,
                    sku=product.sku,
                    name=product.name,
                    category=product.category,
                    qty_on_hand=stock.qty_on_hand,
                    reorder_level=stock.reorder_level,
                    is_low_stock=stock.qty_on_hand <= stock.reorder_level,
                    updated_at=stock.updated_at,
                )
                for stock, product in rows
            ],
        )
