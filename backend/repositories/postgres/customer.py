from sqlalchemy.orm import Session
from sqlalchemy import asc, desc
from models.customer import Customer
from schemas.customer import CustomerCreate

SORTABLE_FIELDS = {"name", "email", "region", "created_at"}


class PostgresCustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 25, region: str | None = None, sort_by: str | None = None, sort_order: str = "asc") -> list[Customer]:
        q = self.db.query(Customer)
        if region:
            q = q.filter(Customer.region == region)
        if sort_by and sort_by in SORTABLE_FIELDS:
            col = getattr(Customer, sort_by)
            q = q.order_by(asc(col) if sort_order == "asc" else desc(col))
        return q.offset(skip).limit(limit).all()

    def count(self, region: str | None = None) -> int:
        q = self.db.query(Customer)
        if region:
            q = q.filter(Customer.region == region)
        return q.count()

    def get_by_id(self, id: int) -> Customer | None:
        return self.db.query(Customer).filter(Customer.id == id).first()

    def create(self, data: CustomerCreate) -> Customer:
        customer = Customer(**data.model_dump())
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer

    def export_all(self) -> tuple[list[str], list]:
        columns = ["ID", "Name", "Email", "Region", "Joined"]
        rows = (
            self.db.query(Customer.id, Customer.name, Customer.email, Customer.region, Customer.created_at)
            .order_by(Customer.name)
            .all()
        )
        return columns, rows
