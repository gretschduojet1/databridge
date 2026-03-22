import io
from core.celery_app import celery_app
from core.database import SessionLocal
from core.events import on
from core.mail import send_email
from repositories.postgres.job import PostgresJobRepository
from sqlalchemy import text


QUERIES = {
    "customers": {
        "sql": "SELECT id, name, email, region, created_at FROM customers.customers ORDER BY name",
        "columns": ["ID", "Name", "Email", "Region", "Joined"],
    },
    "products": {
        "sql": "SELECT id, sku, name, category, stock_qty, reorder_level, updated_at FROM inventory.products ORDER BY name",
        "columns": ["ID", "SKU", "Name", "Category", "Stock", "Reorder At", "Updated"],
    },
    "orders": {
        "sql": """
            SELECT id, customer_id, product_id, quantity, unit_price,
                   (quantity * unit_price) AS total, ordered_at
            FROM sales.orders ORDER BY ordered_at DESC
        """,
        "columns": ["ID", "Customer", "Product", "Qty", "Unit Price", "Total", "Date"],
    },
}


@on("export.requested")
@celery_app.task
def export_resource(payload: dict) -> dict:
    import openpyxl

    job_id   = payload["job_id"]
    resource = payload["resource"]
    email_to = payload["email"]

    db   = SessionLocal()
    repo = PostgresJobRepository(db)

    try:
        repo.set_running(job_id)

        cfg  = QUERIES[resource]
        rows = db.execute(text(cfg["sql"])).fetchall()

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = resource.capitalize()
        ws.append(cfg["columns"])
        for row in rows:
            ws.append(list(row))

        buf = io.BytesIO()
        wb.save(buf)
        excel_bytes = buf.getvalue()

        filename = f"{resource}_export.xlsx"
        send_email(
            to=email_to,
            subject=f"Databridge — {resource.capitalize()} Export",
            body=f"Your {resource} export is attached ({len(rows)} records).",
            attachment=excel_bytes,
            filename=filename,
        )

        result = {"resource": resource, "rows": len(rows), "emailed_to": email_to}
        repo.set_success(job_id, result)
        return result

    except Exception as e:
        repo.set_failed(job_id, str(e))
        raise
    finally:
        db.close()
