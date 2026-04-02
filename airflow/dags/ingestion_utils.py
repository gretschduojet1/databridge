"""
Shared helpers for ingestion DAGs.

Writes run history to workers.ingestion_runs so there's a full audit log
of every DAG execution alongside the moving watermark in ingestion_watermarks.
"""

from __future__ import annotations

from airflow.providers.postgres.hooks.postgres import PostgresHook


def start_run(source: str, total: int) -> int:
    """Insert a new ingestion_runs row and return its id."""
    hook = PostgresHook(postgres_conn_id="databridge_postgres")
    conn = hook.get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO workers.ingestion_runs (source, total, processed, status, started_at)
        VALUES (%s, %s, 0, 'running', NOW())
        RETURNING id
        """,
        (source, total),
    )
    run_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    return run_id


def finish_run(run_id: int, processed: int, last_seen_at: str) -> None:
    """Mark a run as complete with final row count and watermark timestamp."""
    hook = PostgresHook(postgres_conn_id="databridge_postgres")
    conn = hook.get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE workers.ingestion_runs
        SET processed    = %s,
            last_seen_at = %s,
            status       = 'complete',
            finished_at  = NOW()
        WHERE id = %s
        """,
        (processed, last_seen_at, run_id),
    )
    conn.commit()
    cursor.close()


def fail_run(run_id: int, error: str) -> None:
    """Mark a run as failed."""
    hook = PostgresHook(postgres_conn_id="databridge_postgres")
    conn = hook.get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE workers.ingestion_runs
        SET status      = %s,
            finished_at = NOW()
        WHERE id = %s
        """,
        (f"failed: {error[:200]}", run_id),
    )
    conn.commit()
    cursor.close()
