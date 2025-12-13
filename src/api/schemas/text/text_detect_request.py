from pydantic import BaseModel
from typing import List

class TextDetectRequest(BaseModel):
    image_path: str
    languages: List[str] = ["en"]
