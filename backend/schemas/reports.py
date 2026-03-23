from pydantic import BaseModel


class SalesByRegionRow(BaseModel):
    region: str
    revenue: float


class MonthlyRevenueRow(BaseModel):
    month: str
    order_count: int
    revenue: float


class LowStockRow(BaseModel):
    id: int
    sku: str
    name: str
    stock_qty: int
    reorder_level: int


class StockHealthRow(BaseModel):
    id: int
    sku: str
    name: str
    stock_qty: int
    reorder_level: int
    is_low_stock: bool


class StockProjectionRow(BaseModel):
    product_id: int
    sku: str
    name: str
    stock_qty: int
    reorder_level: int
    avg_daily_sales: float
    days_until_stockout: int | None
    projected_stockout_date: str | None  # ISO date string
    velocity_trend: str  # 'accelerating' | 'steady' | 'slowing'
    is_low_stock: bool
    computed_at: str


class StockAlertRow(BaseModel):
    id: int
    sku: str
    name: str
    stock_qty: int
    reorder_level: int
    is_low_stock: bool
    total_sold: int
    is_popular: bool  # top half of products by units sold


class SummaryRow(BaseModel):
    total_revenue: float
    total_orders: int
    total_customers: int
    total_products: int
    low_stock_count: int
