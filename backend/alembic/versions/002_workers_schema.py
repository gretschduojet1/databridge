"""Add workers schema and jobs table

Revision ID: 002
Revises: 001
Create Date: 2026-03-22
"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS workers")

    op.create_table(
        "jobs",
        sa.Column("id",         sa.String(36),                      primary_key=True),
        sa.Column("name",       sa.String(100),  nullable=False),
        sa.Column("status",     sa.String(20),   nullable=False, server_default="pending"),
        sa.Column("payload",    sa.JSON,         nullable=True),
        sa.Column("result",     sa.JSON,         nullable=True),
        sa.Column("error",      sa.Text,         nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        schema="workers",
    )

    op.create_index("idx_jobs_status",     "jobs", ["status"],     schema="workers")
    op.create_index("idx_jobs_created_at", "jobs", ["created_at"], schema="workers")


def downgrade() -> None:
    op.drop_table("jobs", schema="workers")
    op.execute("DROP SCHEMA workers")
