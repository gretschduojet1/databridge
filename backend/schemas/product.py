from datetime import datetime

from pydantic import BaseModel

from schemas.enums import Category


class ProductBase(BaseModel):
    sku: str
    name: str
    category: Category
    stock_qty: int
    reorder_level: int


class ProductCreate(ProductBase):
    pass


class ProductRead(ProductBase):
    id: int
    updated_at: datetime

    model_config = {"from_attributes": True}
