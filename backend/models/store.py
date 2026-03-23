from datetime import UTC, datetime
from typing import ClassVar

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base


class StoreLocation(Base):
    __tablename__ = "locations"
    __table_args__: ClassVar[dict] = {"schema": "stores"}  # type: ignore[misc]

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str] = mapped_column(String(50), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    stock: Mapped[list["StoreStock"]] = relationship("StoreStock", back_populates="store")


class StoreStock(Base):
    __tablename__ = "stock"
    __table_args__: ClassVar[tuple] = (  # type: ignore[misc]
        UniqueConstraint("store_id", "product_id", name="uq_store_product"),
        {"schema": "stores"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    store_id: Mapped[int] = mapped_column(Integer, ForeignKey("stores.locations.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("inventory.products.id"), nullable=False)
    qty_on_hand: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    reorder_level: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    store: Mapped["StoreLocation"] = relationship("StoreLocation", back_populates="stock")
