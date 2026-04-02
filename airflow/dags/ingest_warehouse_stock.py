"""
DAG: ingest_warehouse_stock
Source:  raw.warehouse_stock      (denormalized store+product dump)
Target:  stores.locations         (normalized store records)
         stores.stock             (store-level inventory per product)

The raw table has one flat row per store+product combination — store name,
city, region, and product details all embedded together. This DAG splits
that into two normalized tables and resolves product FKs by SKU.

Transform steps:
  - Deduplicate store_name → upsert into stores.locations
  - product_sku resolved to inventory.products.id
  - qty_on_hand + reorder_level kept per store (not global defaults)
  - last_updated (text) parsed to timestamp for updated_at

Idempotency: uses workers.ingestion_watermarks (last_seen_at) to fetch
only rows where created_at > last_seen_at each run.
"""

from __future__ import annotations

from datetime import datetime, timezone

from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook

from ingestion_utils import finish_run, start_run

SOURCE = "warehouse_stock"


@dag(
    dag_id="ingest_warehouse_stock",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ingestion", "stores"],
)
def ingest_warehouse_stock_dag() -> None:
    @task
    def extract() -> dict:
        hook = PostgresHook(postgres_conn_id="databridge_postgres")

        watermark = hook.get_first(
            "SELECT last_seen_at FROM workers.ingestion_watermarks WHERE source = %s",
            parameters=(SOURCE,),
        )
        last_seen_at = watermark[0] if watermark else "1970-01-01T00:00:00+00:00"

        rows = hook.get_records(
            """
            SELECT id, store_name, store_city, store_region,
                   product_sku, qty_on_hand, reorder_level, last_updated, created_at
            FROM raw.warehouse_stock
            WHERE created_at > %s
            ORDER BY created_at, id
            """,
            parameters=(last_seen_at,),
        )
        return {
            "last_seen_at": str(last_seen_at),
            "records": [
                {
                    "raw_id": row[0],
                    "store_name": row[1],
                    "store_city": row[2],
                    "store_region": row[3],
                    "product_sku": row[4],
                    "qty_on_hand": row[5],
                    "reorder_level": row[6],
                    "last_updated": row[7],
                    "created_at": str(row[8]),
                }
                for row in rows
            ],
        }

    @task
    def transform(payload: dict) -> dict:
        records = payload["records"]
        if not records:
            return {"last_seen_at": payload["last_seen_at"], "stores": [], "stock": [], "max_seen_at": payload["last_seen_at"]}

        hook = PostgresHook(postgres_conn_id="databridge_postgres")

        skus = list({r["product_sku"].strip().upper() for r in records})
        product_rows = hook.get_records(
            "SELECT sku, id FROM inventory.products WHERE sku = ANY(%s)",
            parameters=(skus,),
        )
        product_map = {row[0]: row[1] for row in product_rows}

        store_map: dict[str, dict] = {}
        for r in records:
            name = r["store_name"].strip()
            store_map[name] = {
                "name": name,
                "city": r["store_city"].strip(),
                "region": r["store_region"].strip(),
            }

        now = datetime.now(timezone.utc).isoformat()
        stock_rows = []
        skipped = 0
        for r in records:
            product_id = product_map.get(r["product_sku"].strip().upper())
            if product_id is None:
                skipped += 1
                continue
            stock_rows.append(
                {
                    "raw_id": r["raw_id"],
                    "store_name": r["store_name"].strip(),
                    "product_id": product_id,
                    "qty_on_hand": max(0, r["qty_on_hand"]),
                    "reorder_level": r["reorder_level"],
                    "updated_at": now,
                    "source_created_at": r["created_at"],
                }
            )

        if skipped:
            print(f"Skipped {skipped} rows with unresolvable product_sku")

        max_seen_at = max(r["created_at"] for r in records)
        return {
            "last_seen_at": payload["last_seen_at"],
            "stores": list(store_map.values()),
            "stock": stock_rows,
            "max_seen_at": max_seen_at,
        }

    @task
    def load(payload: dict) -> None:
        stores = payload.get("stores", [])
        stock_rows = payload.get("stock", [])
        max_seen_at = payload["max_seen_at"]

        if not stores and not stock_rows and max_seen_at == payload["last_seen_at"]:
            return

        hook = PostgresHook(postgres_conn_id="databridge_postgres")
        conn = hook.get_conn()
        cursor = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()

        store_id_map: dict[str, int] = {}
        for s in stores:
            cursor.execute(
                """
                INSERT INTO stores.locations (name, city, region, created_at)
                VALUES (%(name)s, %(city)s, %(region)s, %(now)s)
                ON CONFLICT (name) DO UPDATE
                    SET city   = EXCLUDED.city,
                        region = EXCLUDED.region
                RETURNING id
                """,
                {**s, "now": now},
            )
            store_id_map[s["name"]] = cursor.fetchone()[0]

        for r in stock_rows:
            store_id = store_id_map.get(r["store_name"])
            if store_id is None:
                continue
            cursor.execute(
                """
                INSERT INTO stores.stock
                    (store_id, product_id, qty_on_hand, reorder_level, updated_at)
                VALUES (%(store_id)s, %(product_id)s, %(qty_on_hand)s, %(reorder_level)s, %(updated_at)s)
                ON CONFLICT (store_id, product_id) DO UPDATE
                    SET qty_on_hand   = EXCLUDED.qty_on_hand,
                        reorder_level = EXCLUDED.reorder_level,
                        updated_at    = EXCLUDED.updated_at
                """,
                {**r, "store_id": store_id},
            )

        cursor.execute(
            """
            INSERT INTO workers.ingestion_watermarks (source, last_seen_at, rows_processed, updated_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (source) DO UPDATE
                SET last_seen_at   = EXCLUDED.last_seen_at,
                    rows_processed = ingestion_watermarks.rows_processed + EXCLUDED.rows_processed,
                    updated_at     = NOW()
            """,
            (SOURCE, max_seen_at, len(stock_rows)),
        )

        conn.commit()
        cursor.close()

        run_id = start_run(SOURCE, len(stock_rows))
        finish_run(run_id, len(stock_rows), max_seen_at)
        print(f"Loaded {len(stock_rows)} stock rows. Watermark advanced to {max_seen_at}")

    raw = extract()
    transformed = transform(raw)
    load(transformed)


ingest_warehouse_stock_dag()
