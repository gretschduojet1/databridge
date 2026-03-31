"""Add workers.ingestion_runs for batch ingestion progress tracking

Revision ID: 006
Revises: 005
Create Date: 2026-03-26
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "006"
down_revision: str | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("total", sa.Integer, nullable=False),
        sa.Column("processed", sa.Integer, nullable=False, server_default="0"),
        sa.Column("last_id", sa.BigInteger, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        schema="workers",
    )
    op.create_index(
        "idx_ingestion_runs_source_status",
        "ingestion_runs",
        ["source", "status"],
        schema="workers",
    )


def downgrade() -> None:
    op.drop_index("idx_ingestion_runs_source_status", table_name="ingestion_runs", schema="workers")
    op.drop_table("ingestion_runs", schema="workers")
