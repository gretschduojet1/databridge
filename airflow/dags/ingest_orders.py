"""
DAG: ingest_orders
Source:  raw.oms_transactions     (unnormalized OMS export)
Target:  sales.orders             (normalized orders table)

This DAG runs after ingest_customers and ingest_products because orders
reference customers and products by FK. Rows whose customer_email or item_code
can't be resolved are skipped — the watermark still advances past them since
the source system won't resend rows it already exported.

Transform steps:
  - customer_email    resolved to customers.customers.id via subquery
  - item_code         resolved to inventory.products.id via subquery
  - quantity_ordered  → quantity (rename)
  - sale_price        → unit_price (rename)
  - transaction_date  → ordered_at (text → timestamp parse)
  - payment_method    dropped
  - source_channel    dropped

Idempotency: uses workers.ingestion_watermarks to track the last processed
raw.oms_transactions.id. Only rows with id > last_id are fetched each run.
"""

from __future__ import annotations

from datetime import datetime

from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook

SOURCE = "oms_transactions"


@dag(
    dag_id="ingest_orders",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ingestion", "orders"],
)
def ingest_orders_dag() -> None:
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
            SELECT id, transaction_id, customer_email, item_code,
                   quantity_ordered, sale_price, transaction_date
            FROM raw.oms_transactions
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
                    "transaction_id": row[1],
                    "customer_email": row[2],
                    "item_code": row[3],
                    "quantity_ordered": row[4],
                    "sale_price": float(row[5]),
                    "transaction_date": row[6],
                }
                for row in rows
            ],
        }

    @task
    def transform(payload: dict) -> dict:
        records = payload["records"]
        if not records:
            return {"last_id": payload["last_id"], "records": [], "max_raw_id": payload["last_id"]}

        hook = PostgresHook(postgres_conn_id="databridge_postgres")

        emails = list({r["customer_email"].lower().strip() for r in records})
        customer_rows = hook.get_records(
            "SELECT email, id FROM customers.customers WHERE email = ANY(%s)",
            parameters=(emails,),
        )
        customer_map = {row[0]: row[1] for row in customer_rows}

        skus = list({r["item_code"].strip().upper() for r in records})
        product_rows = hook.get_records(
            "SELECT sku, id FROM inventory.products WHERE sku = ANY(%s)",
            parameters=(skus,),
        )
        product_map = {row[0]: row[1] for row in product_rows}

        normalized = []
        skipped = 0
        for r in records:
            customer_id = customer_map.get(r["customer_email"].lower().strip())
            product_id = product_map.get(r["item_code"].strip().upper())

            if customer_id is None or product_id is None:
                # Unresolvable FK — source system won't resend this row, so we
                # advance the watermark past it rather than retrying forever.
                skipped += 1
                continue

            normalized.append(
                {
                    "raw_id": r["raw_id"],
                    "customer_id": customer_id,
                    "product_id": product_id,
                    "quantity": r["quantity_ordered"],
                    "unit_price": r["sale_price"],
                    "ordered_at": r["transaction_date"].strip()[:19],
                }
            )

        if skipped:
            print(f"Skipped {skipped} rows with unresolvable customer_email or item_code")

        # Always advance to the max ID seen in this batch, including skipped rows.
        max_raw_id = max(r["raw_id"] for r in records)
        return {"last_id": payload["last_id"], "records": normalized, "max_raw_id": max_raw_id}

    @task
    def load(payload: dict) -> None:
        records = payload["records"]
        max_raw_id = payload["max_raw_id"]

        if not records and max_raw_id == payload["last_id"]:
            return

        hook = PostgresHook(postgres_conn_id="databridge_postgres")
        conn = hook.get_conn()
        cursor = conn.cursor()

        for r in records:
            cursor.execute(
                """
                INSERT INTO sales.orders
                    (customer_id, product_id, quantity, unit_price, ordered_at)
                VALUES
                    (%(customer_id)s, %(product_id)s, %(quantity)s, %(unit_price)s, %(ordered_at)s)
                """,
                r,
            )

        cursor.execute(
            """
            INSERT INTO workers.ingestion_watermarks (source, last_id, rows_processed, updated_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (source) DO UPDATE
                SET last_id        = EXCLUDED.last_id,
                    rows_processed = ingestion_watermarks.rows_processed + EXCLUDED.rows_processed,
                    updated_at     = NOW()
            """,
            (SOURCE, max_raw_id, len(records)),
        )

        conn.commit()
        cursor.close()
        print(f"Loaded {len(records)} orders. Watermark advanced to id={max_raw_id}")

    raw = extract()
    normalized = transform(raw)
    load(normalized)


ingest_orders_dag()
