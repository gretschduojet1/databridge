from datetime import datetime
from sqlalchemy import Integer, String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import mapped_column, Mapped
from core.database import Base
from schemas.enums import Role


class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(SAEnum(Role, schema="auth", name="user_role"), nullable=False, default=Role.VIEWER)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
