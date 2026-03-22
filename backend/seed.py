"""
Seed the database with realistic sample data across all three source systems.
Run with: docker compose exec backend python seed.py

Safe to re-run — clears existing data before inserting.
"""

import random
from datetime import UTC, datetime

from faker import Faker
from sqlalchemy.orm import Session

from core.database import SessionLocal
from core.security import hash_password
from models.customer import Customer
from models.order import Order
from models.product import Product
from models.user import User
from schemas.enums import Role

fake = Faker()
random.seed(42)
Faker.seed(42)

REGIONS = ["Northeast", "Southeast", "Midwest", "West"]
CATEGORIES = ["Electronics", "Office", "Supplies"]

PRODUCTS = [
    ("Wireless Mouse", "Electronics"), ("USB-C Hub", "Electronics"),
    ("Mechanical Keyboard", "Electronics"), ("Monitor Stand", "Electronics"),
    ("Webcam HD", "Electronics"), ("Laptop Sleeve", "Supplies"),
    ("Desk Lamp", "Office"), ("Whiteboard", "Office"),
    ("Standing Desk Mat", "Office"), ("Cable Organizer", "Supplies"),
    ("Sticky Notes Pack", "Supplies"), ("Ballpoint Pens (12)", "Supplies"),
    ("Binder Clips", "Supplies"), ("Printer Paper (500)", "Supplies"),
    ("Label Maker", "Office"),
]


def seed(db: Session) -> None:
    print("Clearing existing data...")
    db.query(Order).delete()
    db.query(Customer).delete()
    db.query(Product).delete()
    db.query(User).delete()
    db.commit()

    print("Seeding demo users...")
    db.add(User(
        email="admin@databridge.io",
        hashed_password=hash_password("admin"),
        role=Role.ADMIN,
        created_at=datetime.now(UTC),
    ))
    db.add(User(
        email="demo@databridge.io",
        hashed_password=hash_password("demo"),
        role=Role.VIEWER,
        created_at=datetime.now(UTC),
    ))
    db.commit()

    print("Seeding customers...")
    customers = []
    for _ in range(200):
        c = Customer(
            name=fake.name(),
            email=fake.unique.email(),
            region=random.choice(REGIONS),
            created_at=fake.date_time_between(start_date="-2y", end_date="now", tzinfo=UTC),
        )
        db.add(c)
        customers.append(c)
    db.commit()

    print("Seeding products...")
    products = []
    for i, (name, category) in enumerate(PRODUCTS):
        p = Product(
            sku=f"SKU-{i+1:04d}",
            name=name,
            category=category,
            stock_qty=random.randint(0, 500),
            reorder_level=random.choice([5, 10, 25, 50]),
            updated_at=datetime.now(UTC),
        )
        db.add(p)
        products.append(p)
    db.commit()

    print("Seeding orders...")
    for _ in range(500):
        ordered_at = fake.date_time_between(start_date="-1y", end_date="now", tzinfo=UTC)
        o = Order(
            customer_id=random.choice(customers).id,
            product_id=random.choice(products).id,
            quantity=random.randint(1, 20),
            unit_price=round(random.uniform(4.99, 499.99), 2),
            ordered_at=ordered_at,
        )
        db.add(o)
    db.commit()

    print("Done. Users: 2 | Customers: 200 | Products: 15 | Orders: 500")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
