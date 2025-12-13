from pydantic import BaseModel

class VideoInfoRequest(BaseModel):
    video_path: str
