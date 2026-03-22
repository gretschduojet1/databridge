from sqlalchemy.orm import Session
from sqlalchemy import func
from models.order import Order
from models.customer import Customer
from models.product import Product
from schemas.reports import SalesByRegionRow, MonthlyRevenueRow, LowStockRow, SummaryRow


class PostgresReportsRepository:
    def __init__(self, db: Session):
        self.db = db

    def sales_by_region(self) -> list[SalesByRegionRow]:
        rows = (
            self.db.query(Customer.region, func.sum(Order.quantity * Order.unit_price).label("revenue"))
            .join(Order, Order.customer_id == Customer.id)
            .group_by(Customer.region)
            .order_by(func.sum(Order.quantity * Order.unit_price).desc())
            .all()
        )
        return [SalesByRegionRow(region=r.region, revenue=float(r.revenue)) for r in rows]

    def monthly_revenue(self, year: int | None = None) -> list[MonthlyRevenueRow]:
        q = self.db.query(
            func.date_trunc("month", Order.ordered_at).label("month"),
            func.count(Order.id).label("order_count"),
            func.sum(Order.quantity * Order.unit_price).label("revenue"),
        )
        if year:
            q = q.filter(func.extract("year", Order.ordered_at) == year)
        rows = q.group_by("month").order_by("month").all()
        return [
            MonthlyRevenueRow(month=r.month.isoformat(), order_count=r.order_count, revenue=float(r.revenue))
            for r in rows
        ]

    def low_stock(self) -> list[LowStockRow]:
        products = (
            self.db.query(Product)
            .filter(Product.stock_qty <= Product.reorder_level)
            .order_by(Product.stock_qty.asc())
            .all()
        )
        return [
            LowStockRow(id=p.id, sku=p.sku, name=p.name, stock_qty=p.stock_qty, reorder_level=p.reorder_level)
            for p in products
        ]

    def summary(self) -> SummaryRow:
        total_revenue = self.db.query(func.sum(Order.quantity * Order.unit_price)).scalar() or 0
        total_orders = self.db.query(func.count(Order.id)).scalar() or 0
        total_customers = self.db.query(func.count(Customer.id)).scalar() or 0
        low_stock_count = (
            self.db.query(func.count(Product.id))
            .filter(Product.stock_qty <= Product.reorder_level)
            .scalar() or 0
        )
        return SummaryRow(
            total_revenue=float(total_revenue),
            total_orders=total_orders,
            total_customers=total_customers,
            low_stock_count=low_stock_count,
        )
