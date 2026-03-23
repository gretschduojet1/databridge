from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from core.database import get_db
from core.dependencies import get_current_user
from models.user import User
from models.order import Order
from models.customer import Customer
from models.product import Product

router = APIRouter()


@router.get("/sales/by-region")
def sales_by_region(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    rows = (
        db.query(Customer.region, func.sum(Order.quantity * Order.unit_price).label("revenue"))
        .join(Order, Order.customer_id == Customer.id)
        .group_by(Customer.region)
        .order_by(func.sum(Order.quantity * Order.unit_price).desc())
        .all()
    )
    return [{"region": r.region, "revenue": float(r.revenue)} for r in rows]


@router.get("/sales/monthly")
def sales_monthly(
    year: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    q = db.query(
        func.date_trunc("month", Order.ordered_at).label("month"),
        func.count(Order.id).label("order_count"),
        func.sum(Order.quantity * Order.unit_price).label("revenue"),
    )
    if year:
        q = q.filter(func.extract("year", Order.ordered_at) == year)
    rows = q.group_by("month").order_by("month").all()
    return [
        {"month": r.month.isoformat(), "order_count": r.order_count, "revenue": float(r.revenue)}
        for r in rows
    ]


@router.get("/inventory/low-stock")
def low_stock(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    products = (
        db.query(Product)
        .filter(Product.stock_qty <= Product.reorder_level)
        .order_by(Product.stock_qty.asc())
        .all()
    )
    return [
        {"id": p.id, "sku": p.sku, "name": p.name, "stock_qty": p.stock_qty, "reorder_level": p.reorder_level}
        for p in products
    ]


@router.get("/summary")
def summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    total_revenue = db.query(func.sum(Order.quantity * Order.unit_price)).scalar() or 0
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    total_customers = db.query(func.count(Customer.id)).scalar() or 0
    low_stock_count = db.query(func.count(Product.id)).filter(Product.stock_qty <= Product.reorder_level).scalar() or 0

    return {
        "total_revenue": float(total_revenue),
        "total_orders": total_orders,
        "total_customers": total_customers,
        "low_stock_count": low_stock_count,
    }
