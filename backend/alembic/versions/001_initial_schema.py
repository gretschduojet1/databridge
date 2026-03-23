"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-22
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM as PGEnum

from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS customers")
    op.execute("CREATE SCHEMA IF NOT EXISTS sales")
    op.execute("CREATE SCHEMA IF NOT EXISTS inventory")
    op.execute("CREATE SCHEMA IF NOT EXISTS auth")

    op.execute("""
    DO $$ BEGIN
        CREATE TYPE auth.user_role AS ENUM ('admin', 'viewer');
    EXCEPTION WHEN duplicate_object THEN NULL;
    END $$;
    """)

    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("region", sa.String(50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        schema="customers",
    )

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sku", sa.String(50), unique=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("stock_qty", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reorder_level", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        schema="inventory",
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.customers.id"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("inventory.products.id"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("ordered_at", sa.DateTime(timezone=True), nullable=False),
        schema="sales",
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column(
            "role",
            PGEnum("admin", "viewer", name="user_role", schema="auth", create_type=False),
            nullable=False,
            server_default="viewer",
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        schema="auth",
    )

    # Indexes
    op.create_index("idx_customers_region", "customers", ["region"], schema="customers")
    op.create_index("idx_orders_customer", "orders", ["customer_id"], schema="sales")
    op.create_index("idx_orders_product", "orders", ["product_id"], schema="sales")
    op.create_index("idx_orders_ordered_at", "orders", ["ordered_at"], schema="sales")
    op.create_index("idx_products_category", "products", ["category"], schema="inventory")


def downgrade() -> None:
    op.drop_table("orders", schema="sales")
    op.drop_table("products", schema="inventory")
    op.drop_table("customers", schema="customers")
    op.drop_table("users", schema="auth")
    op.execute("DROP TYPE auth.user_role")
    op.execute("DROP SCHEMA auth")
    op.execute("DROP SCHEMA sales")
    op.execute("DROP SCHEMA inventory")
    op.execute("DROP SCHEMA customers")
