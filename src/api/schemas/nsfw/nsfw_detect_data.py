from pydantic import BaseModel
from typing import List
from api.schemas.nsfw.nsfw_segment import NSFWSegment

class NSFWDetectData(BaseModel):
    segments: List[NSFWSegment]
    count: int
