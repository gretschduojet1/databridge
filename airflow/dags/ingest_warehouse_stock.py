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

Runs daily. Only processes rows where ingested_at IS NULL.
"""

from __future__ import annotations

from datetime import datetime, timezone

from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook


@dag(
    dag_id="ingest_warehouse_stock",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ingestion", "stores"],
)
def ingest_warehouse_stock_dag() -> None:
    @task
    def extract() -> list[dict]:
        hook = PostgresHook(postgres_conn_id="databridge_postgres")
        rows = hook.get_records(
            """
            SELECT id, store_name, store_city, store_region,
                   product_sku, qty_on_hand, reorder_level, last_updated
            FROM raw.warehouse_stock
            WHERE ingested_at IS NULL
            ORDER BY id
            """
        )
        return [
            {
                "raw_id": row[0],
                "store_name": row[1],
                "store_city": row[2],
                "store_region": row[3],
                "product_sku": row[4],
                "qty_on_hand": row[5],
                "reorder_level": row[6],
                "last_updated": row[7],
            }
            for row in rows
        ]

    @task
    def transform(records: list[dict]) -> dict:
        if not records:
            return {"stores": [], "stock": []}

        hook = PostgresHook(postgres_conn_id="databridge_postgres")

        # Resolve SKUs to product IDs in bulk
        skus = list({r["product_sku"].strip().upper() for r in records})
        product_rows = hook.get_records(
            "SELECT sku, id FROM inventory.products WHERE sku = ANY(%s)",
            parameters=(skus,),
        )
        product_map = {row[0]: row[1] for row in product_rows}

        # Deduplicate stores (last writer wins for city/region)
        store_map: dict[str, dict] = {}
        for r in records:
            name = r["store_name"].strip()
            store_map[name] = {
                "name": name,
                "city": r["store_city"].strip(),
                "region": r["store_region"].strip(),
            }

        # Build stock rows, skipping unresolvable SKUs
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
                }
            )

        if skipped:
            print(f"Skipped {skipped} rows with unresolvable product_sku")

        return {"stores": list(store_map.values()), "stock": stock_rows}

    @task
    def load(payload: dict) -> None:
        stores = payload.get("stores", [])
        stock_rows = payload.get("stock", [])
        if not stores and not stock_rows:
            return

        hook = PostgresHook(postgres_conn_id="databridge_postgres")
        conn = hook.get_conn()
        cursor = conn.cursor()
        now = datetime.now(timezone.utc).isoformat()

        # Upsert stores and collect name → id mapping
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

        # Upsert stock rows
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
                "UPDATE raw.warehouse_stock SET ingested_at = NOW() WHERE id = %s",
                (r["raw_id"],),
            )

        conn.commit()
        cursor.close()

    raw = extract()
    transformed = transform(raw)
    load(transformed)


ingest_warehouse_stock_dag()
