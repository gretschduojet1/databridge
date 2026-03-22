from datetime import datetime

from pydantic import BaseModel, EmailStr

from schemas.enums import Region


class CustomerBase(BaseModel):
    name: str
    email: EmailStr
    region: Region


class CustomerCreate(CustomerBase):
    pass


class CustomerRead(CustomerBase):
    id: int
    created_at: datetime

    # Required to read from SQLAlchemy ORM objects, not just plain dicts
    model_config = {"from_attributes": True}
