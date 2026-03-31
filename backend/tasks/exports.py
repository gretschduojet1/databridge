from collections.abc import Callable

from sqlalchemy.orm import Session

from core import storage
from core.celery_app import celery_app
from core.container import get_mailer, get_order_repo, get_product_repo, make_customer_repo
from core.database import SessionLocal
from core.events import on
from repositories.interfaces.customer import CustomerRepositoryProtocol
from repositories.interfaces.order import OrderRepositoryProtocol
from repositories.interfaces.product import ProductRepositoryProtocol
from repositories.postgres.job import PostgresJobRepository
from writers.factory import get_writer

_ExportRepo = CustomerRepositoryProtocol | ProductRepositoryProtocol | OrderRepositoryProtocol
_REPO_FACTORY: dict[str, Callable[[Session], _ExportRepo]] = {
    "customers": make_customer_repo,
    "products": get_product_repo,
    "orders": get_order_repo,
}


@on("export.requested")
@celery_app.task
def export_resource(payload: dict) -> dict:
    job_id = payload["job_id"]
    resource = payload["resource"]
    email_to = payload["email"]
    fmt = payload.get("format", "xlsx")

    db = SessionLocal()
    repo = PostgresJobRepository(db)

    try:
        repo.set_running(job_id)

        resource_repo = _REPO_FACTORY[resource](db)
        columns, rows = resource_repo.export_all()
        writer = get_writer(fmt)
        data = writer.write(columns, rows)

        key = f"exports/{job_id}/{resource}_export.{writer.extension}"
        storage.upload(key, data, writer.content_type)
        download_url = storage.presign(key)

        get_mailer().send(
            to=email_to,
            subject=f"Databridge — {resource.capitalize()} Export Ready",
            body=(
                f"Your {resource} export ({len(rows)} records) is ready.\n\n"
                f"Download: {download_url}\n\n"
                "Link expires in 24 hours."
            ),
        )

        result = {"resource": resource, "rows": len(rows), "emailed_to": email_to, "s3_key": key}
        repo.set_success(job_id, result)
        return result

    except Exception as e:
        repo.set_failed(job_id, str(e))
        raise
    finally:
        db.close()
