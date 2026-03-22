from datetime import datetime
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import mapped_column, Mapped
from core.database import Base


class Customer(Base):
    """
    Maps to the `customers.customers` table.

    The __table_args__ schema matches the Postgres schema defined in db/init.sql.
    SQLAlchemy will generate queries like: SELECT * FROM customers.customers
    """

    __tablename__ = "customers"
    __table_args__ = {"schema": "customers"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    region: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
