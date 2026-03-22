from core.celery_app import celery_app
from core.database import SessionLocal
from core.events import on
from core.container import get_customer_repo, get_product_repo, get_order_repo, get_mailer
from repositories.postgres.job import PostgresJobRepository
from writers.factory import get_writer

_REPO_FACTORY = {
    "customers": get_customer_repo,
    "products":  get_product_repo,
    "orders":    get_order_repo,
}


@on("export.requested")
@celery_app.task
def export_resource(payload: dict) -> dict:
    job_id   = payload["job_id"]
    resource = payload["resource"]
    email_to = payload["email"]
    fmt      = payload.get("format", "xlsx")

    db   = SessionLocal()
    repo = PostgresJobRepository(db)

    try:
        repo.set_running(job_id)

        resource_repo      = _REPO_FACTORY[resource](db)
        columns, rows      = resource_repo.export_all()
        writer             = get_writer(fmt)
        data               = writer.write(columns, rows)

        filename = f"{resource}_export.{writer.extension}"
        get_mailer().send(
            to=email_to,
            subject=f"Databridge — {resource.capitalize()} Export",
            body=f"Your {resource} export is attached ({len(rows)} records).",
            attachment=data,
            filename=filename,
            content_type=writer.content_type,
        )

        result = {"resource": resource, "rows": len(rows), "emailed_to": email_to}
        repo.set_success(job_id, result)
        return result

    except Exception as e:
        repo.set_failed(job_id, str(e))
        raise
    finally:
        db.close()
