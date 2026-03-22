from datetime import UTC, datetime

from sqlalchemy.orm import Session

from models.job import Job, JobStatus


class PostgresJobRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, job_id: str, name: str, payload: dict) -> Job:
        now = datetime.now(UTC)
        job = Job(
            id=job_id,
            name=name,
            status=JobStatus.pending,
            payload=payload,
            created_at=now,
            updated_at=now,
        )
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        return job

    def get(self, job_id: str) -> Job | None:
        return self.db.get(Job, job_id)

    def list(self, skip: int = 0, limit: int = 25) -> list[Job]:
        return (
            self.db.query(Job)
            .order_by(Job.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def set_running(self, job_id: str) -> None:
        self._update(job_id, {"status": JobStatus.running})

    def set_success(self, job_id: str, result: dict) -> None:
        self._update(job_id, {"status": JobStatus.success, "result": result})

    def set_failed(self, job_id: str, error: str) -> None:
        self._update(job_id, {"status": JobStatus.failed, "error": error})

    def _update(self, job_id: str, fields: dict) -> None:
        fields["updated_at"] = datetime.now(UTC)
        self.db.query(Job).filter(Job.id == job_id).update(fields)
        self.db.commit()
