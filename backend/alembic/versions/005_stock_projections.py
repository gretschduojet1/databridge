"""Add inventory.stock_projections table

Revision ID: 005
Revises: 004
Create Date: 2026-03-22
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "stock_projections",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("product_id", sa.Integer, sa.ForeignKey("inventory.products.id"), nullable=False, unique=True),
        sa.Column("avg_daily_sales", sa.Numeric(10, 2), nullable=False),
        sa.Column("days_until_stockout", sa.Integer, nullable=True),  # NULL = no sales velocity
        sa.Column("projected_stockout_date", sa.Date, nullable=True),
        sa.Column("velocity_trend", sa.String(20), nullable=False, server_default="steady"),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False),
        schema="inventory",
    )


def downgrade() -> None:
    op.drop_table("stock_projections", schema="inventory")
