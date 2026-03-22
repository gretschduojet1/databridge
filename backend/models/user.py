from datetime import datetime
from typing import ClassVar

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base
from schemas.enums import Role


class User(Base):
    __tablename__ = "users"
    __table_args__: ClassVar[dict] = {"schema": "auth"}

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[Role] = mapped_column(
        SAEnum(Role, schema="auth", name="user_role", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=Role.VIEWER,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
