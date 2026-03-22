from datetime import datetime
from pydantic import BaseModel


class ProductBase(BaseModel):
    sku: str
    name: str
    category: str
    stock_qty: int
    reorder_level: int


class ProductCreate(ProductBase):
    pass


class ProductRead(ProductBase):
    id: int
    updated_at: datetime

    model_config = {"from_attributes": True}
