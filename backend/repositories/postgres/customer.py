from sqlalchemy.orm import Session
from models.customer import Customer
from schemas.customer import CustomerCreate


class PostgresCustomerRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_all(self, skip: int = 0, limit: int = 100, region: str | None = None) -> list[Customer]:
        q = self.db.query(Customer)
        if region:
            q = q.filter(Customer.region == region)
        return q.offset(skip).limit(limit).all()

    def get_by_id(self, id: int) -> Customer | None:
        return self.db.query(Customer).filter(Customer.id == id).first()

    def create(self, data: CustomerCreate) -> Customer:
        customer = Customer(**data.model_dump())
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
        return customer
