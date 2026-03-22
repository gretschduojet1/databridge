from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class OrderBase(BaseModel):
    customer_id: int
    product_id: int
    quantity: int
    unit_price: Decimal


class OrderCreate(OrderBase):
    pass


class OrderRead(OrderBase):
    id: int
    ordered_at: datetime

    model_config = {"from_attributes": True}
