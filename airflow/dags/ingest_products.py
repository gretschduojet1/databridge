"""
DAG: ingest_products
Source:  raw.wms_inventory        (unnormalized WMS export)
Target:  inventory.products       (normalized inventory table)

Transform steps:
  - item_code          → sku  (rename)
  - item_name          → name (rename + strip)
  - department         → category (rename — values may differ; no mapping needed here
                          as the WMS happens to use the same category names)
  - quantity_on_hand   → stock_qty (rename)
  - reorder_point      → reorder_level (rename)
  - cost_price         dropped (WMS-internal, not part of our model)
  - warehouse_bin      dropped (WMS-internal)
  - last_sync          dropped (not needed)

Runs daily. Only processes rows where ingested_at IS NULL.
"""

from __future__ import annotations

from datetime import datetime, timezone

from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook


@dag(
    dag_id="ingest_products",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ingestion", "products"],
)
def ingest_products_dag() -> None:
    @task
    def extract() -> list[dict]:
        hook = PostgresHook(postgres_conn_id="databridge_postgres")
        rows = hook.get_records(
            """
            SELECT id, item_code, item_name, department, quantity_on_hand, reorder_point
            FROM raw.wms_inventory
            WHERE ingested_at IS NULL
            ORDER BY id
            """
        )
        return [
            {
                "raw_id": row[0],
                "item_code": row[1],
                "item_name": row[2],
                "department": row[3],
                "quantity_on_hand": row[4],
                "reorder_point": row[5],
            }
            for row in rows
        ]

    @task
    def transform(records: list[dict]) -> list[dict]:
        return [
            {
                "raw_id": r["raw_id"],
                "sku": r["item_code"].strip().upper(),
                "name": r["item_name"].strip(),
                "category": r["department"].strip(),
                "stock_qty": max(0, r["quantity_on_hand"]),  # guard against negative WMS values
                "reorder_level": r["reorder_point"],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            for r in records
        ]

    @task
    def load(records: list[dict]) -> None:
        if not records:
            return

        hook = PostgresHook(postgres_conn_id="databridge_postgres")
        conn = hook.get_conn()
        cursor = conn.cursor()

        for r in records:
            cursor.execute(
                """
                INSERT INTO inventory.products (sku, name, category, stock_qty, reorder_level, updated_at)
                VALUES (%(sku)s, %(name)s, %(category)s, %(stock_qty)s, %(reorder_level)s, %(updated_at)s)
                ON CONFLICT (sku) DO UPDATE
                    SET name          = EXCLUDED.name,
                        category      = EXCLUDED.category,
                        stock_qty     = EXCLUDED.stock_qty,
                        reorder_level = EXCLUDED.reorder_level,
                        updated_at    = NOW()
                """,
                r,
            )
            cursor.execute(
                "UPDATE raw.wms_inventory SET ingested_at = NOW() WHERE id = %s",
                (r["raw_id"],),
            )

        conn.commit()
        cursor.close()

    raw = extract()
    normalized = transform(raw)
    load(normalized)


ingest_products_dag()
