from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, ClassVar

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

if TYPE_CHECKING:
    from models.product import Product
    from repositories.postgres.customer_table import CustomerRow


class Order(Base):
    """
    Maps to the `sales.orders` table.

    The ForeignKey references use the full schema.table.column path because
    customers and products live in different schemas.
    """

    __tablename__ = "orders"
    __table_args__: ClassVar[dict] = {"schema": "sales"}  # type: ignore[misc]

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(Integer, ForeignKey("customers.customers.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("inventory.products.id"), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    ordered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    # SQLAlchemy relationships let you traverse associations in Python:
    # order.customer.name, order.product.sku — no manual joins needed
    customer: Mapped[CustomerRow] = relationship("CustomerRow")
    product: Mapped[Product] = relationship("Product")
