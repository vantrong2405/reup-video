from pydantic import BaseModel

class JobCreatedData(BaseModel):
    job_id: str
    status: str = "pending"
    message: str = "Job submitted successfully"
