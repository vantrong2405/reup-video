from pydantic import BaseModel
from typing import Optional, Any
from datetime import datetime

class JobStatusData(BaseModel):
    job_id: str
    status: str
    progress: Optional[int] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
