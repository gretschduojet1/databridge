"""Add raw landing-zone schema for Airflow ingestion

Revision ID: 003
Revises: 002
Create Date: 2026-03-22
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS raw")

    # Raw CRM export — customer data as delivered by the CRM team.
    # territory uses short codes (NE/SE/MW/W); join_date is a text string.
    # phone and account_tier are CRM-only fields dropped during ingestion.
    op.create_table(
        "crm_customers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("email_address", sa.String(255), nullable=False),
        sa.Column("territory", sa.String(10), nullable=False),
        sa.Column("join_date", sa.Text(), nullable=False),
        sa.Column("phone", sa.String(30), nullable=True),
        sa.Column("account_tier", sa.String(20), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=True),
        schema="raw",
    )

    # Raw WMS export — inventory data from the warehouse management system.
    # item_code maps to sku; department maps to category; cost_price and
    # warehouse_bin are WMS-internal and dropped during ingestion.
    op.create_table(
        "wms_inventory",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("item_code", sa.String(50), nullable=False),
        sa.Column("item_name", sa.String(255), nullable=False),
        sa.Column("department", sa.String(100), nullable=False),
        sa.Column("quantity_on_hand", sa.Integer(), nullable=False),
        sa.Column("reorder_point", sa.Integer(), nullable=False),
        sa.Column("cost_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("warehouse_bin", sa.String(20), nullable=True),
        sa.Column("last_sync", sa.Text(), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=True),
        schema="raw",
    )

    # Raw OMS export — order transactions referencing customers and products
    # by natural keys (email, item_code) rather than integer FKs.
    # Airflow resolves these to real FKs during ingestion.
    op.create_table(
        "oms_transactions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("transaction_id", sa.String(50), nullable=False, unique=True),
        sa.Column("customer_email", sa.String(255), nullable=False),
        sa.Column("item_code", sa.String(50), nullable=False),
        sa.Column("quantity_ordered", sa.Integer(), nullable=False),
        sa.Column("sale_price", sa.Numeric(10, 2), nullable=False),
        sa.Column("transaction_date", sa.Text(), nullable=False),
        sa.Column("payment_method", sa.String(30), nullable=True),
        sa.Column("source_channel", sa.String(30), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=True),
        schema="raw",
    )

    op.create_index("idx_raw_crm_ingested", "crm_customers", ["ingested_at"], schema="raw")
    op.create_index("idx_raw_wms_ingested", "wms_inventory", ["ingested_at"], schema="raw")
    op.create_index("idx_raw_oms_ingested", "oms_transactions", ["ingested_at"], schema="raw")


def downgrade() -> None:
    op.drop_table("oms_transactions", schema="raw")
    op.drop_table("wms_inventory", schema="raw")
    op.drop_table("crm_customers", schema="raw")
    op.execute("DROP SCHEMA raw")
