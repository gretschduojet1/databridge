from datetime import datetime

from pydantic import BaseModel


class StoreSummary(BaseModel):
    id: int
    name: str
    city: str
    region: str
    total_products: int
    low_stock_count: int


class StoreStockItem(BaseModel):
    product_id: int
    sku: str
    name: str
    category: str
    qty_on_hand: int
    reorder_level: int
    is_low_stock: bool
    updated_at: datetime

    model_config = {"from_attributes": True}


class StoreDetail(BaseModel):
    id: int
    name: str
    city: str
    region: str
    inventory: list[StoreStockItem]
