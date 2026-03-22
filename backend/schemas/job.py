from datetime import datetime
from typing import Any
from pydantic import BaseModel
from models.job import JobStatus


class JobOut(BaseModel):
    id:         str
    name:       str
    status:     JobStatus
    payload:    dict[str, Any] | None
    result:     dict[str, Any] | None
    error:      str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DispatchResponse(BaseModel):
    job_id: str
    status: JobStatus
