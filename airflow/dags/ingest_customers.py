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

Idempotency: uses workers.ingestion_watermarks to track last_seen_at —
the MAX(created_at) of the last processed batch. Each run fetches only
rows where created_at > last_seen_at, simulating a source system we
don't own and cannot write to.
"""

from __future__ import annotations

from datetime import datetime

from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook

from ingestion_utils import finish_run, start_run

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
            "SELECT last_seen_at FROM workers.ingestion_watermarks WHERE source = %s",
            parameters=(SOURCE,),
        )
        # Falls back to epoch if no watermark exists — first run fetches everything.
        last_seen_at = watermark[0] if watermark else "1970-01-01T00:00:00+00:00"

        rows = hook.get_records(
            """
            SELECT id, full_name, email_address, territory, join_date, created_at
            FROM raw.crm_customers
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
                    "full_name": row[1],
                    "email_address": row[2],
                    "territory": row[3],
                    "join_date": row[4],
                    "created_at": str(row[5]),
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
                    "source_created_at": r["created_at"],
                }
            )
        return {"last_seen_at": payload["last_seen_at"], "records": normalized}

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

        max_seen_at = max(r["source_created_at"] for r in records)
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
        print(f"Loaded {len(records)} customers. Watermark advanced to {max_seen_at}")

    raw = extract()
    normalized = transform(raw)
    load(normalized)


ingest_customers_dag()
