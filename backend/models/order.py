from datetime import datetime
from sqlalchemy import Integer, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from core.database import Base


class Order(Base):
    """
    Maps to the `sales.orders` table.

    The ForeignKey references use the full schema.table.column path because
    customers and products live in different schemas.
    """

    __tablename__ = "orders"
    __table_args__ = {"schema": "sales"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("customers.customers.id"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("inventory.products.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    ordered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    # SQLAlchemy relationships let you traverse associations in Python:
    # order.customer.name, order.product.sku — no manual joins needed
    customer: Mapped["Customer"] = relationship("Customer")  # noqa: F821
    product: Mapped["Product"] = relationship("Product")  # noqa: F821
