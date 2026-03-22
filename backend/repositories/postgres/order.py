from sqlalchemy.orm import Session
from models.order import Order
from schemas.order import OrderCreate


class PostgresOrderRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100, customer_id: int | None = None) -> list[Order]:
        q = self.db.query(Order)
        if customer_id:
            q = q.filter(Order.customer_id == customer_id)
        return q.offset(skip).limit(limit).all()

    def get_by_id(self, id: int) -> Order | None:
        return self.db.query(Order).filter(Order.id == id).first()

    def create(self, data: OrderCreate) -> Order:
        order = Order(**data.model_dump())
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order
