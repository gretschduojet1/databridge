"""
DAG: ingest_customers_batched
Source:  raw.crm_customers       (unnormalized CRM export)
Target:  customers.customers     (normalized CRM table)

Processes rows in batches of 1000. Tracks progress in workers.ingestion_runs
so that if the DAG fails mid-run, the next execution resumes from exactly
where it stopped rather than reprocessing from the beginning.

Retry behaviour:
  - run_batches retries up to 3 times (4 total attempts) with a 5-minute delay
  - On each retry, the cursor is re-read from the DB so it resumes correctly
  - If all retries are exhausted, on_ingestion_failure marks the run as failed
    and sends an alert email to the admin
  - The next scheduled run will start a new run from remaining unprocessed rows
    (ingested_at IS NULL ensures already-processed rows are never re-imported)
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

from airflow.decorators import dag, task
from airflow.providers.postgres.hooks.postgres import PostgresHook
from airflow.utils.email import send_email

BATCH_SIZE = 1000
SOURCE = "raw.crm_customers"
ALERT_EMAIL = os.environ["AIRFLOW_ALERT_EMAIL"]

TERRITORY_MAP = {
    "NE": "Northeast",
    "SE": "Southeast",
    "MW": "Midwest",
    "W": "West",
}


def on_ingestion_failure(context: dict) -> None:
    """
    Called after all retries are exhausted.
    Marks the run as failed and sends an alert email.
    """
    run_meta = context["task_instance"].xcom_pull(task_ids="start_or_resume")

    if run_meta and run_meta.get("run_id"):
        hook = PostgresHook(postgres_conn_id="databridge_postgres")
        conn = hook.get_conn()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE workers.ingestion_runs SET status = 'failed', finished_at = NOW() WHERE id = %s",
            (run_meta["run_id"],),
        )
        conn.commit()
        cursor.close()

    dag_id = context["dag"].dag_id
    execution_date = context["execution_date"]
    exception = context.get("exception", "Unknown error")

    send_email(
        to=[ALERT_EMAIL],
        subject=f"[Databridge] Ingestion failed after all retries: {dag_id}",
        html_content=f"""
            <h3>Ingestion DAG Failed</h3>
            <p><strong>DAG:</strong> {dag_id}</p>
            <p><strong>Execution date:</strong> {execution_date}</p>
            <p><strong>Error:</strong> {exception}</p>
            <p>
                The run has been marked as <strong>failed</strong> after exhausting all retries.
                The next scheduled run will resume from remaining unprocessed rows.
            </p>
        """,
    )


@dag(
    dag_id="ingest_customers_batched",
    schedule="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["ingestion", "customers"],
)
def ingest_customers_batched_dag() -> None:
    @task
    def start_or_resume() -> dict:
        hook = PostgresHook(postgres_conn_id="databridge_postgres")
        conn = hook.get_conn()
        cursor = conn.cursor()

        # Check for an incomplete run to resume
        cursor.execute("""
            SELECT id, last_id, processed, total
            FROM workers.ingestion_runs
            WHERE source = %s AND status = 'running'
            ORDER BY started_at DESC
            LIMIT 1
        """, (SOURCE,))
        existing = cursor.fetchone()

        if existing:
            run_id, last_id, processed, total = existing
            print(f"Resuming run {run_id}: {processed}/{total} processed, cursor at id {last_id}")
            cursor.close()
            return {"run_id": run_id, "last_id": last_id or 0, "processed": processed, "total": total}

        # Count how many rows are waiting
        cursor.execute("SELECT COUNT(*) FROM raw.crm_customers WHERE ingested_at IS NULL")
        total = cursor.fetchone()[0]

        if total == 0:
            print("No unprocessed rows found — nothing to do.")
            cursor.close()
            return {"run_id": None, "last_id": 0, "processed": 0, "total": 0}

        # Create a new run record
        cursor.execute("""
            INSERT INTO workers.ingestion_runs (source, total, started_at)
            VALUES (%s, %s, NOW())
            RETURNING id
        """, (SOURCE, total))
        run_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()

        print(f"Starting new run {run_id}: {total} rows to process in batches of {BATCH_SIZE}")
        return {"run_id": run_id, "last_id": 0, "processed": 0, "total": total}

    @task(
        retries=3,
        retry_delay=timedelta(minutes=5),
        retry_exponential_backoff=True,
        on_failure_callback=on_ingestion_failure,
    )
    def run_batches(run: dict) -> dict:
        if run["run_id"] is None:
            return run

        hook = PostgresHook(postgres_conn_id="databridge_postgres")
        conn = hook.get_conn()
        cursor = conn.cursor()

        # Always re-read the cursor from the DB — XCom holds the value from when
        # start_or_resume ran, but retries need the latest position from the DB.
        cursor.execute(
            "SELECT last_id, processed FROM workers.ingestion_runs WHERE id = %s",
            (run["run_id"],),
        )
        row = cursor.fetchone()
        last_id: int = row[0] or 0
        processed: int = row[1]

        while True:
            cursor.execute("""
                SELECT id, full_name, email_address, territory, join_date
                FROM raw.crm_customers
                WHERE ingested_at IS NULL AND id > %s
                ORDER BY id
                LIMIT %s
            """, (last_id, BATCH_SIZE))

            rows = cursor.fetchall()
            if not rows:
                break

            for raw_id, full_name, email_address, territory, join_date in rows:
                name = full_name.strip()
                email = email_address.lower().strip()
                region = TERRITORY_MAP.get(territory.strip().upper(), territory)
                created_at = join_date.strip()[:19]

                cursor.execute("""
                    INSERT INTO customers.customers (name, email, region, created_at)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (email) DO UPDATE
                        SET name   = EXCLUDED.name,
                            region = EXCLUDED.region
                """, (name, email, region, created_at))

                cursor.execute(
                    "UPDATE raw.crm_customers SET ingested_at = NOW() WHERE id = %s",
                    (raw_id,),
                )

            last_id = rows[-1][0]
            processed += len(rows)

            # Update cursor before committing — safe resume point if failure occurs
            cursor.execute("""
                UPDATE workers.ingestion_runs
                SET processed = %s, last_id = %s
                WHERE id = %s
            """, (processed, last_id, run["run_id"]))
            conn.commit()

            print(f"Batch complete — {processed}/{run['total']} rows processed (last_id={last_id})")

        cursor.close()
        return {**run, "last_id": last_id, "processed": processed}

    @task
    def finish(run: dict) -> None:
        if run["run_id"] is None:
            return

        hook = PostgresHook(postgres_conn_id="databridge_postgres")
        conn = hook.get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE workers.ingestion_runs
            SET status = 'complete', finished_at = NOW()
            WHERE id = %s
        """, (run["run_id"],))
        conn.commit()
        cursor.close()

        print(f"Run {run['run_id']} complete: {run['processed']}/{run['total']} records ingested")

    run = start_or_resume()
    result = run_batches(run)
    finish(result)


ingest_customers_batched_dag()
