from datetime import datetime

from pydantic import BaseModel, EmailStr

from schemas.enums import Role


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRead(BaseModel):
    id: int
    email: EmailStr
    role: Role
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}
