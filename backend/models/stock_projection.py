from datetime import UTC, date, datetime
from typing import ClassVar

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class StockProjection(Base):
    """Pre-computed sales velocity and stockout projections, written by the
    compute_stock_projections Airflow DAG and read by the dashboard."""

    __tablename__ = "stock_projections"
    __table_args__: ClassVar[dict] = {"schema": "inventory"}  # type: ignore[misc]

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey("inventory.products.id"), nullable=False, unique=True)
    avg_daily_sales: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    days_until_stockout: Mapped[int | None] = mapped_column(Integer, nullable=True)
    projected_stockout_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # 'accelerating' | 'steady' | 'slowing' — based on last-15-days vs prior-15-days velocity
    velocity_trend: Mapped[str] = mapped_column(String(20), nullable=False, default="steady")
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
