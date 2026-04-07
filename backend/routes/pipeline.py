from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from core.database import get_db
from core.dependencies import get_current_user
from models.user import User

router = APIRouter()


class IngestionRun(BaseModel):
    id: int
    source: str
    status: str        # "running" | "complete" | "failed"
    message: str | None  # error detail when status == "failed"
    total: int
    processed: int
    skipped: int
    remaining: int
    pct_complete: float
    started_at: str
    finished_at: str | None
    resumed_from_id: int | None


@router.get("/runs", response_model=list[IngestionRun])
def list_runs(
    limit: int = 20,
    _: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[IngestionRun]:
    rows = db.execute(
        text("""
            SELECT id, source, status, message, total, processed, skipped,
                   total - processed                                  AS remaining,
                   CASE WHEN total > 0
                        THEN ROUND(processed::numeric / total * 100, 1)
                        ELSE 0
                   END                                                AS pct_complete,
                   started_at,
                   finished_at,
                   resumed_from_id
            FROM workers.ingestion_runs
            ORDER BY started_at DESC
            LIMIT :limit
        """),
        {"limit": limit},
    ).fetchall()

    return [
        IngestionRun(
            id=r.id,
            source=r.source,
            status=r.status,
            message=r.message,
            total=r.total,
            processed=r.processed,
            skipped=r.skipped,
            remaining=r.remaining,
            pct_complete=float(r.pct_complete),
            started_at=r.started_at.isoformat(),
            finished_at=r.finished_at.isoformat() if r.finished_at else None,
            resumed_from_id=r.resumed_from_id,
        )
        for r in rows
    ]
