from pydantic import BaseModel

class HealthData(BaseModel):
    status: str = "healthy"
    version: str
    redis: str = "connected"
