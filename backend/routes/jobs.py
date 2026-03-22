import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from core.database import get_db
from core.dependencies import get_current_user
from core.events import dispatch
from models.user import User
from repositories.postgres.job import PostgresJobRepository
from schemas.job import JobOut, DispatchResponse

router = APIRouter()


def get_repo(db: Session = Depends(get_db)) -> PostgresJobRepository:
    return PostgresJobRepository(db)


@router.post("/dispatch/report", response_model=DispatchResponse)
def dispatch_report(
    _: User = Depends(get_current_user),
    repo: PostgresJobRepository = Depends(get_repo),
):
    """Enqueue a full summary report regeneration."""
    job_id = str(uuid.uuid4())
    job = repo.create(job_id, "generate_summary_report", {})
    dispatch("report.generate", {"job_id": job_id})
    return DispatchResponse(job_id=job.id, status=job.status)



@router.post("/dispatch/export", response_model=DispatchResponse)
def dispatch_export(
    resource: str,
    current_user: User = Depends(get_current_user),
    repo: PostgresJobRepository = Depends(get_repo),
):
    """Enqueue a full dataset export. Result is emailed to the requesting user."""
    if resource not in ("customers", "products", "orders"):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Unknown resource: {resource}")
    job_id = str(uuid.uuid4())
    payload = {"resource": resource, "email": current_user.email}
    job = repo.create(job_id, "export_resource", payload)
    dispatch("export.requested", {"job_id": job_id, **payload})
    return DispatchResponse(job_id=job.id, status=job.status)


@router.get("/{job_id}", response_model=JobOut)
def get_job(
    job_id: str,
    _: User = Depends(get_current_user),
    repo: PostgresJobRepository = Depends(get_repo),
):
    """Poll job status. Returns current state including result or error once complete."""
    job = repo.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/", response_model=list[JobOut])
def list_jobs(
    skip: int = 0,
    limit: int = 25,
    _: User = Depends(get_current_user),
    repo: PostgresJobRepository = Depends(get_repo),
):
    return repo.list(skip=skip, limit=limit)
