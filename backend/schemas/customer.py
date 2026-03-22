from datetime import datetime
from pydantic import BaseModel, EmailStr


class CustomerBase(BaseModel):
    name: str
    email: EmailStr
    region: str


class CustomerCreate(CustomerBase):
    pass


class CustomerRead(CustomerBase):
    id: int
    created_at: datetime

    # Required to read from SQLAlchemy ORM objects, not just plain dicts
    model_config = {"from_attributes": True}
