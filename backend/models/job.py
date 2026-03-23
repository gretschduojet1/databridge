from datetime import datetime
from enum import Enum
from typing import ClassVar

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column

from core.database import Base


class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    success = "success"
    failed = "failed"


class Job(Base):
    __tablename__ = "jobs"
    __table_args__: ClassVar[dict] = {"schema": "workers"}  # type: ignore[misc]

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=JobStatus.pending)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    result: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
