from sqlalchemy import func
from sqlalchemy.orm import Session

from models.customer import Customer
from models.order import Order
from models.product import Product
from models.stock_projection import StockProjection
from schemas.reports import (
    LowStockRow,
    MonthlyRevenueRow,
    SalesByRegionRow,
    StockAlertRow,
    StockHealthRow,
    StockProjectionRow,
    SummaryRow,
)


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

    def stock_alerts(self, limit: int = 10) -> list[StockAlertRow]:
        sales_subq = (
            self.db.query(
                Order.product_id,
                func.sum(Order.quantity).label("total_sold"),
            )
            .group_by(Order.product_id)
            .subquery()
        )

        total_sold_col = func.coalesce(sales_subq.c.total_sold, 0)

        # Fetch all products with sales so we can compute the median in Python
        all_rows = (
            self.db.query(Product, total_sold_col).outerjoin(sales_subq, Product.id == sales_subq.c.product_id).all()
        )

        if not all_rows:
            return []

        sold_values = sorted(int(sold) for _, sold in all_rows)
        mid = len(sold_values) // 2
        median = sold_values[mid]

        # Sort: low stock first, then by units sold descending
        all_rows.sort(key=lambda r: (0 if r[0].stock_qty <= r[0].reorder_level else 1, -int(r[1])))

        return [
            StockAlertRow(
                id=p.id,
                sku=p.sku,
                name=p.name,
                stock_qty=p.stock_qty,
                reorder_level=p.reorder_level,
                is_low_stock=p.stock_qty <= p.reorder_level,
                total_sold=int(sold),
                is_popular=int(sold) >= median,
            )
            for p, sold in all_rows[:limit]
        ]

    def stock_health(self, limit: int = 10) -> list[StockHealthRow]:
        # Sort by stock_qty - reorder_level ascending so the most at-risk products come first.
        products = self.db.query(Product).order_by((Product.stock_qty - Product.reorder_level).asc()).limit(limit).all()
        return [
            StockHealthRow(
                id=p.id,
                sku=p.sku,
                name=p.name,
                stock_qty=p.stock_qty,
                reorder_level=p.reorder_level,
                is_low_stock=p.stock_qty <= p.reorder_level,
            )
            for p in products
        ]

    def stock_projections(self) -> list[StockProjectionRow]:
        rows = (
            self.db.query(StockProjection, Product)
            .join(Product, StockProjection.product_id == Product.id)
            .order_by(
                # NULL days_until_stockout (no sales) goes last
                StockProjection.days_until_stockout.is_(None),
                StockProjection.days_until_stockout.asc(),
            )
            .all()
        )
        return [
            StockProjectionRow(
                product_id=proj.product_id,
                sku=product.sku,
                name=product.name,
                stock_qty=product.stock_qty,
                reorder_level=product.reorder_level,
                avg_daily_sales=float(proj.avg_daily_sales),
                days_until_stockout=proj.days_until_stockout,
                projected_stockout_date=(
                    proj.projected_stockout_date.isoformat() if proj.projected_stockout_date else None
                ),
                velocity_trend=proj.velocity_trend,
                is_low_stock=product.stock_qty <= product.reorder_level,
                computed_at=proj.computed_at.isoformat(),
            )
            for proj, product in rows
        ]

    def summary(self) -> SummaryRow:
        total_revenue = self.db.query(func.sum(Order.quantity * Order.unit_price)).scalar() or 0
        total_orders = self.db.query(func.count(Order.id)).scalar() or 0
        total_customers = self.db.query(func.count(Customer.id)).scalar() or 0
        total_products = self.db.query(func.count(Product.id)).scalar() or 0
        low_stock_count = (
            self.db.query(func.count(Product.id)).filter(Product.stock_qty <= Product.reorder_level).scalar() or 0
        )
        return SummaryRow(
            total_revenue=float(total_revenue),
            total_orders=total_orders,
            total_customers=total_customers,
            total_products=total_products,
            low_stock_count=low_stock_count,
        )
