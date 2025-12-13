from pydantic import BaseModel
from typing import List

class TextMaskFiltersRequest(BaseModel):
    video_path: str
    languages: List[str] = ["en"]
    expand: int = 10
    max_frames: int = 3
