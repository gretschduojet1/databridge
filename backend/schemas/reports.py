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


class SummaryRow(BaseModel):
    total_revenue: float
    total_orders: int
    total_customers: int
    low_stock_count: int
