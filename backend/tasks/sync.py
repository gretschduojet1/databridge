import time
from datetime import datetime, timezone
from faker import Faker
from core.celery_app import celery_app
from core.database import SessionLocal
from core.events import on
from repositories.postgres.job import PostgresJobRepository
from models.customer import Customer
from schemas.enums import Region

fake = Faker()


@on("sync.customers")
@celery_app.task
def simulate_customer_sync(payload: dict) -> dict:
    """
    Simulates pulling a batch of new customers from an upstream CRM.
    In a real system this would call an external API or read from a
    message queue; here we generate realistic-looking Faker records.
    """
    job_id = payload["job_id"]
    batch_size = payload.get("batch_size", 10)

    db = SessionLocal()
    jobs = PostgresJobRepository(db)

    try:
        jobs.set_running(job_id)

        # Simulate network latency from the upstream source
        time.sleep(1)

        regions = list(Region)
        inserted = 0

        for _ in range(batch_size):
            customer = Customer(
                name=fake.name(),
                email=fake.unique.email(),
                region=fake.random_element(regions).value,
                created_at=datetime.now(timezone.utc),
            )
            db.add(customer)
            inserted += 1

        db.commit()

        result = {"synced": inserted, "source": "crm_simulation"}
        jobs.set_success(job_id, result)
        return result

    except Exception as e:
        db.rollback()
        jobs.set_failed(job_id, str(e))
        raise
    finally:
        db.close()
