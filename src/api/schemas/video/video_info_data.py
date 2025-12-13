from pydantic import BaseModel

class VideoInfoData(BaseModel):
    width: int
    height: int
    fps: str
    duration: float
    has_audio: bool
