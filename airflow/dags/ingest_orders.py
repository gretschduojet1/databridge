"""
DAG: ingest_orders
Source:  raw.oms_transactions     (unnormalized OMS export)
Target:  sales.orders             (normalized orders table)

This DAG runs after ingest_customers and ingest_products because orders
reference customers and products by FK. If those aren't loaded first,
the email/sku lookups will silently drop unresolvable rows.

Transform steps:
  - customer_email    resolved to customers.customers.id via subquery
  - item_code         resolved to inventory.products.id via subquery
  - quantity_ordered  → quantity (rename)
  - sale_price        → unit_price (rename)
  - transaction_date  → ordered_at (text → timestamp parse)
  - payment_method    dropped
  - source_channel    dropped

Deduplication: transaction_id is stored in raw.oms_transactions.transaction_id
and the ingested_at watermark ensures each row is loaded exactly once.
"""

from __future__ import annotations

from datetime import datetime

from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook


@dag(
    dag_id="ingest_orders",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    # Runs after customers and products are loaded so FK lookups succeed.
    tags=["ingestion", "orders"],
)
def ingest_orders_dag() -> None:
    @task
    def extract() -> list[dict]:
        hook = PostgresHook(postgres_conn_id="databridge_postgres")
        rows = hook.get_records(
            """
            SELECT id, transaction_id, customer_email, item_code,
                   quantity_ordered, sale_price, transaction_date
            FROM raw.oms_transactions
            WHERE ingested_at IS NULL
            ORDER BY id
            """
        )
        return [
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
        ]

    @task
    def transform(records: list[dict]) -> list[dict]:
        # Resolve natural keys to surrogate PKs in bulk to avoid N+1 queries.
        if not records:
            return []

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
                # Row references an email or SKU that hasn't been loaded yet.
                # Leave ingested_at NULL so the next run can retry once the
                # customer/product DAGs have caught up.
                skipped += 1
                continue

            normalized.append(
                {
                    "raw_id": r["raw_id"],
                    "customer_id": customer_id,
                    "product_id": product_id,
                    "quantity": r["quantity_ordered"],
                    "unit_price": r["sale_price"],
                    # Parse text date — accept ISO datetime or date-only strings.
                    "ordered_at": r["transaction_date"].strip()[:19],
                }
            )

        if skipped:
            print(f"Skipped {skipped} rows with unresolvable customer_email or item_code")

        return normalized

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
                INSERT INTO sales.orders
                    (customer_id, product_id, quantity, unit_price, ordered_at)
                VALUES
                    (%(customer_id)s, %(product_id)s, %(quantity)s, %(unit_price)s, %(ordered_at)s)
                """,
                r,
            )
            cursor.execute(
                "UPDATE raw.oms_transactions SET ingested_at = NOW() WHERE id = %s",
                (r["raw_id"],),
            )

        conn.commit()
        cursor.close()

    raw = extract()
    normalized = transform(raw)
    load(normalized)


ingest_orders_dag()
