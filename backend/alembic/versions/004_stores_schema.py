"""Add stores schema and raw warehouse_stock landing table

Revision ID: 004
Revises: 003
Create Date: 2026-03-22
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # Raw landing table — denormalized warehouse dump
    # One row per store+product combination as delivered by the WMS.
    # Store and product details are embedded flat (no FKs) because the
    # source system doesn't know about our internal IDs.
    # ------------------------------------------------------------------
    op.execute("CREATE SCHEMA IF NOT EXISTS raw")  # idempotent if 003 already ran

    op.create_table(
        "warehouse_stock",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_name", sa.String(255), nullable=False),
        sa.Column("store_city", sa.String(100), nullable=False),
        sa.Column("store_region", sa.String(50), nullable=False),
        sa.Column("product_sku", sa.String(50), nullable=False),
        sa.Column("product_name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("qty_on_hand", sa.Integer(), nullable=False),
        sa.Column("reorder_level", sa.Integer(), nullable=False),
        sa.Column("last_updated", sa.Text(), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=True),
        schema="raw",
    )
    op.create_index("idx_raw_warehouse_ingested", "warehouse_stock", ["ingested_at"], schema="raw")

    # ------------------------------------------------------------------
    # Normalized stores schema
    # ------------------------------------------------------------------
    op.execute("CREATE SCHEMA IF NOT EXISTS stores")

    op.create_table(
        "locations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("city", sa.String(100), nullable=False),
        sa.Column("region", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        schema="stores",
    )
    op.create_index("idx_stores_region", "locations", ["region"], schema="stores")

    op.create_table(
        "stock",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.locations.id"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("inventory.products.id"), nullable=False),
        sa.Column("qty_on_hand", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reorder_level", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("store_id", "product_id", name="uq_store_product"),
        schema="stores",
    )
    op.create_index("idx_stock_store", "stock", ["store_id"], schema="stores")
    op.create_index("idx_stock_product", "stock", ["product_id"], schema="stores")


def downgrade() -> None:
    op.drop_table("stock", schema="stores")
    op.drop_table("locations", schema="stores")
    op.execute("DROP SCHEMA stores")
    op.drop_table("warehouse_stock", schema="raw")
