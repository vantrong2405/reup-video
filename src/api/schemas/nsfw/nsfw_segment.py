from pydantic import BaseModel

class NSFWSegment(BaseModel):
    start: float
    end: float
