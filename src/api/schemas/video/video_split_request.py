from pydantic import BaseModel

class VideoSplitRequest(BaseModel):
    input_path: str
    output_dir: str
    mode: str = "manual"
    start_time: str = "00:00:00"
    duration: float = 10.0
    min_duration: float = 5.0
    limit: int = 5
    base_name: str = "video"
