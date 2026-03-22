from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from models.order import Order
from schemas.order import OrderCreate

SORTABLE_FIELDS = {"ordered_at", "quantity", "unit_price"}


class PostgresOrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 25, customer_id: int | None = None, date_from: datetime | None = None, date_to: datetime | None = None, sort_by: str | None = None, sort_order: str = "asc") -> list[Order]:
        q = self.db.query(Order)
        if customer_id:
            q = q.filter(Order.customer_id == customer_id)
        if date_from:
            q = q.filter(Order.ordered_at >= date_from)
        if date_to:
            q = q.filter(Order.ordered_at <= date_to)
        if sort_by and sort_by in SORTABLE_FIELDS:
            col = getattr(Order, sort_by)
            q = q.order_by(asc(col) if sort_order == "asc" else desc(col))
        return q.offset(skip).limit(limit).all()

    def count(self, customer_id: int | None = None, date_from: datetime | None = None, date_to: datetime | None = None) -> int:
        q = self.db.query(Order)
        if customer_id:
            q = q.filter(Order.customer_id == customer_id)
        if date_from:
            q = q.filter(Order.ordered_at >= date_from)
        if date_to:
            q = q.filter(Order.ordered_at <= date_to)
        return q.count()

    def get_by_id(self, id: int) -> Order | None:
        return self.db.query(Order).filter(Order.id == id).first()

    def create(self, data: OrderCreate) -> Order:
        order = Order(**data.model_dump())
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order

    def export_all(self) -> tuple[list[str], list]:
        columns = ["ID", "Customer", "Product", "Qty", "Unit Price", "Total", "Date"]
        rows = (
            self.db.query(
                Order.id, Order.customer_id, Order.product_id,
                Order.quantity, Order.unit_price,
                (Order.quantity * Order.unit_price).label("total"),
                Order.ordered_at,
            )
            .order_by(Order.ordered_at.desc())
            .all()
        )
        return columns, rows
