from datetime import datetime, timezone, timedelta
from core.celery_app import celery_app
from core.database import SessionLocal
from models.job import Job, JobStatus
from repositories.postgres.job import PostgresJobRepository

# Jobs in "running" longer than this are assumed to have died mid-task
STALE_RUNNING_MINUTES = 5


@celery_app.task
def sweep_stuck_jobs():
    """
    Finds jobs that never made it into the queue (pending) or whose worker
    died before finishing (running but stale), and re-enqueues them.
    """
    # Import here to avoid circular imports at module load time
    from tasks.reports import generate_summary_report
    from tasks.exports import export_resource

    task_map = {
        "generate_summary_report": generate_summary_report,
        "export_resource":         export_resource,
    }

    db = SessionLocal()
    repo = PostgresJobRepository(db)

    try:
        stale_cutoff = datetime.now(timezone.utc) - timedelta(minutes=STALE_RUNNING_MINUTES)

        stuck = (
            db.query(Job)
            .filter(
                (Job.status == JobStatus.pending) |
                (
                    (Job.status == JobStatus.running) &
                    (Job.updated_at < stale_cutoff)
                )
            )
            .all()
        )

        requeued = 0
        for job in stuck:
            task = task_map.get(job.name)
            if not task:
                continue
            repo._update(job.id, {"status": JobStatus.pending})
            task.delay({"job_id": job.id, **(job.payload or {})})
            requeued += 1

        return {"requeued": requeued}
    finally:
        db.close()
