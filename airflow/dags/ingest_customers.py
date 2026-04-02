"""
DAG: ingest_customers
Source:  raw.crm_customers       (unnormalized CRM export)
Target:  customers.customers     (normalized CRM table)

Transform steps:
  - Strip whitespace from full_name
  - Lowercase email_address → email
  - Expand territory short-codes (NE → Northeast, etc.) → region
  - Parse join_date text → TIMESTAMPTZ → created_at
  - Drop phone and account_tier (not part of our data model)

Idempotency: uses workers.ingestion_watermarks to track the last processed
raw.crm_customers.id. Only rows with id > last_id are fetched each run,
simulating reading from a source system we don't own (no ingested_at column
on their tables).
"""

from __future__ import annotations

from datetime import datetime

from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook

SOURCE = "crm_customers"

TERRITORY_MAP = {
    "NE": "Northeast",
    "SE": "Southeast",
    "MW": "Midwest",
    "W": "West",
}


@dag(
    dag_id="ingest_customers",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ingestion", "customers"],
)
def ingest_customers_dag() -> None:
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
            SELECT id, full_name, email_address, territory, join_date
            FROM raw.crm_customers
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
                    "full_name": row[1],
                    "email_address": row[2],
                    "territory": row[3],
                    "join_date": row[4],
                }
                for row in rows
            ],
        }

    @task
    def transform(payload: dict) -> dict:
        records = payload["records"]
        normalized = []
        for r in records:
            normalized.append(
                {
                    "raw_id": r["raw_id"],
                    "name": r["full_name"].strip(),
                    "email": r["email_address"].lower().strip(),
                    "region": TERRITORY_MAP.get(r["territory"].strip().upper(), r["territory"]),
                    "created_at": r["join_date"].strip()[:19],
                }
            )
        return {"last_id": payload["last_id"], "records": normalized}

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
                INSERT INTO customers.customers (name, email, region, created_at)
                VALUES (%(name)s, %(email)s, %(region)s, %(created_at)s)
                ON CONFLICT (email) DO UPDATE
                    SET name   = EXCLUDED.name,
                        region = EXCLUDED.region
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
        print(f"Loaded {len(records)} customers. Watermark advanced to id={max_id}")

    raw = extract()
    normalized = transform(raw)
    load(normalized)


ingest_customers_dag()
