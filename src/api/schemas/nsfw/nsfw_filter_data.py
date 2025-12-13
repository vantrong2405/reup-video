from pydantic import BaseModel

class NSFWFilterData(BaseModel):
    output: str
    segments_removed: int
