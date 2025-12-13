from pydantic import BaseModel
from typing import List

class VideoSplitData(BaseModel):
    output_files: List[str]
    count: int
