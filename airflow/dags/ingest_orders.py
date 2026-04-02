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

Idempotency: uses workers.ingestion_watermarks (last_seen_at) to fetch
only rows where created_at > last_seen_at each run.
"""

from __future__ import annotations

from datetime import datetime

from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook

from ingestion_utils import finish_run, start_run

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
            "SELECT last_seen_at FROM workers.ingestion_watermarks WHERE source = %s",
            parameters=(SOURCE,),
        )
        last_seen_at = watermark[0] if watermark else "1970-01-01T00:00:00+00:00"

        rows = hook.get_records(
            """
            SELECT id, transaction_id, customer_email, item_code,
                   quantity_ordered, sale_price, transaction_date, created_at
            FROM raw.oms_transactions
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
                    "transaction_id": row[1],
                    "customer_email": row[2],
                    "item_code": row[3],
                    "quantity_ordered": row[4],
                    "sale_price": float(row[5]),
                    "transaction_date": row[6],
                    "created_at": str(row[7]),
                }
                for row in rows
            ],
        }

    @task
    def transform(payload: dict) -> dict:
        records = payload["records"]
        if not records:
            return {"last_seen_at": payload["last_seen_at"], "records": [], "max_seen_at": payload["last_seen_at"]}

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
                    "source_created_at": r["created_at"],
                }
            )

        if skipped:
            print(f"Skipped {skipped} rows with unresolvable customer_email or item_code")

        max_seen_at = max(r["created_at"] for r in records)
        return {"last_seen_at": payload["last_seen_at"], "records": normalized, "max_seen_at": max_seen_at}

    @task
    def load(payload: dict) -> None:
        records = payload["records"]
        max_seen_at = payload["max_seen_at"]

        if not records and max_seen_at == payload["last_seen_at"]:
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
            INSERT INTO workers.ingestion_watermarks (source, last_seen_at, rows_processed, updated_at)
            VALUES (%s, %s, %s, NOW())
            ON CONFLICT (source) DO UPDATE
                SET last_seen_at   = EXCLUDED.last_seen_at,
                    rows_processed = ingestion_watermarks.rows_processed + EXCLUDED.rows_processed,
                    updated_at     = NOW()
            """,
            (SOURCE, max_seen_at, len(records)),
        )

        conn.commit()
        cursor.close()

        run_id = start_run(SOURCE, len(records))
        finish_run(run_id, len(records), max_seen_at)
        print(f"Loaded {len(records)} orders. Watermark advanced to {max_seen_at}")

    raw = extract()
    normalized = transform(raw)
    load(normalized)


ingest_orders_dag()
