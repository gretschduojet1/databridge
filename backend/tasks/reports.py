import time
from core.celery_app import celery_app
from core.database import SessionLocal
from core.events import on
from repositories.postgres.job import PostgresJobRepository


@on("report.generate")
@celery_app.task
def generate_summary_report(payload: dict) -> dict:
    job_id = payload["job_id"]

    db = SessionLocal()
    jobs = PostgresJobRepository(db)

    try:
        jobs.set_running(job_id)

        # Simulate report generation work
        time.sleep(2)

        from sqlalchemy import text
        result = db.execute(text("""
            SELECT
                COUNT(*)                                          AS total_orders,
                SUM(quantity * unit_price)                        AS total_revenue,
                AVG(quantity * unit_price)                        AS avg_order_value,
                (SELECT COUNT(*) FROM customers.customers)        AS total_customers,
                (SELECT COUNT(*) FROM inventory.products
                  WHERE stock_qty <= reorder_level)               AS low_stock_count
            FROM sales.orders
        """)).mappings().one()

        summary = {
            "total_orders":    int(result["total_orders"]),
            "total_revenue":   float(result["total_revenue"] or 0),
            "avg_order_value": float(result["avg_order_value"] or 0),
            "total_customers": int(result["total_customers"]),
            "low_stock_count": int(result["low_stock_count"]),
        }

        jobs.set_success(job_id, summary)
        return summary

    except Exception as e:
        jobs.set_failed(job_id, str(e))
        raise
    finally:
        db.close()
