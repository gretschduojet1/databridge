"""
DAG: ingest_products
Source:  raw.wms_inventory        (unnormalized WMS export)
Target:  inventory.products       (normalized inventory table)

Transform steps:
  - item_code          → sku  (rename)
  - item_name          → name (rename + strip)
  - department         → category (rename)
  - quantity_on_hand   → stock_qty (rename)
  - reorder_point      → reorder_level (rename)
  - cost_price         dropped (WMS-internal)
  - warehouse_bin      dropped (WMS-internal)
  - last_sync          dropped

Idempotency: uses workers.ingestion_watermarks to track the last processed
raw.wms_inventory.id. Only rows with id > last_id are fetched each run.
"""

from __future__ import annotations

from datetime import datetime, timezone

from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook

SOURCE = "wms_inventory"


@dag(
    dag_id="ingest_products",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ingestion", "products"],
)
def ingest_products_dag() -> None:
    @task
    def extract() -> dict:
        hook = PostgresHook(postgres_conn_id="databridge_postgres")

        watermark = hook.get_first(
            "SELECT last_id FROM workers.ingestion_watermarks WHERE source = %s",
            parameters=(SOURCE,),
        )
        last_id = watermark[0] if watermark else 0

        rows = hook.get_records(
            """
            SELECT id, item_code, item_name, department, quantity_on_hand, reorder_point
            FROM raw.wms_inventory
            WHERE id > %s
            ORDER BY id
            """,
            parameters=(last_id,),
        )
        return {
            "last_id": last_id,
            "records": [
                {
                    "raw_id": row[0],
                    "item_code": row[1],
                    "item_name": row[2],
                    "department": row[3],
                    "quantity_on_hand": row[4],
                    "reorder_point": row[5],
                }
                for row in rows
            ],
        }

    @task
    def transform(payload: dict) -> dict:
        return {
            "last_id": payload["last_id"],
            "records": [
                {
                    "raw_id": r["raw_id"],
                    "sku": r["item_code"].strip().upper(),
                    "name": r["item_name"].strip(),
                    "category": r["department"].strip(),
                    "stock_qty": max(0, r["quantity_on_hand"]),
                    "reorder_level": r["reorder_point"],
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
                for r in payload["records"]
            ],
        }

    @task
    def load(payload: dict) -> None:
        records = payload["records"]
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

        max_id = max(r["raw_id"] for r in records)
        cursor.execute(
            """
            INSERT INTO workers.ingestion_watermarks (source, last_id, rows_processed, updated_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (source) DO UPDATE
                SET last_id        = EXCLUDED.last_id,
                    rows_processed = ingestion_watermarks.rows_processed + EXCLUDED.rows_processed,
                    updated_at     = NOW()
            """,
            (SOURCE, max_id, len(records)),
        )

        conn.commit()
        cursor.close()
        print(f"Loaded {len(records)} products. Watermark advanced to id={max_id}")

    raw = extract()
    normalized = transform(raw)
    load(normalized)


ingest_products_dag()
