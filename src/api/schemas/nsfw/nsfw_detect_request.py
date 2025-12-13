from pydantic import BaseModel

class NSFWDetectRequest(BaseModel):
    video_path: str
    threshold: float = 0.7
    frame_interval: float = 1.0
