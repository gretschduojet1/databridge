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

Runs daily. Only processes rows where ingested_at IS NULL so re-runs
are safe — already-loaded rows are skipped automatically.
"""

from __future__ import annotations

from datetime import datetime

from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook

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
    def extract() -> list[dict]:
        hook = PostgresHook(postgres_conn_id="databridge_postgres")
        rows = hook.get_records(
            """
            SELECT id, full_name, email_address, territory, join_date
            FROM raw.crm_customers
            WHERE ingested_at IS NULL
            ORDER BY id
            """
        )
        return [
            {
                "raw_id": row[0],
                "full_name": row[1],
                "email_address": row[2],
                "territory": row[3],
                "join_date": row[4],
            }
            for row in rows
        ]

    @task
    def transform(records: list[dict]) -> list[dict]:
        normalized = []
        for r in records:
            normalized.append(
                {
                    "raw_id": r["raw_id"],
                    "name": r["full_name"].strip(),
                    "email": r["email_address"].lower().strip(),
                    # Territory codes expand to the full region name.
                    # Unknown codes fall through unchanged so nothing is silently dropped.
                    "region": TERRITORY_MAP.get(r["territory"].strip().upper(), r["territory"]),
                    # join_date arrives as a text string — parse it to a timestamp.
                    # We accept both ISO format ("2023-04-12T09:15:00") and date-only ("2023-04-12").
                    "created_at": r["join_date"].strip()[:19],
                }
            )
        return normalized

    @task
    def load(records: list[dict]) -> None:
        if not records:
            return

        hook = PostgresHook(postgres_conn_id="databridge_postgres")
        conn = hook.get_conn()
        cursor = conn.cursor()

        for r in records:
            # ON CONFLICT updates name and region if the email already exists,
            # so re-seeding raw data or reprocessing is idempotent.
            cursor.execute(
                """
                INSERT INTO customers.customers (name, email, region, created_at)
                VALUES (%(name)s, %(email)s, %(region)s, %(created_at)s)
                ON CONFLICT (email) DO UPDATE
                    SET name       = EXCLUDED.name,
                        region     = EXCLUDED.region
                """,
                r,
            )
            cursor.execute(
                "UPDATE raw.crm_customers SET ingested_at = NOW() WHERE id = %s",
                (r["raw_id"],),
            )

        conn.commit()
        cursor.close()

    raw = extract()
    normalized = transform(raw)
    load(normalized)


ingest_customers_dag()
