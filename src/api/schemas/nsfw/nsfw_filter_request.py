from pydantic import BaseModel

class NSFWFilterRequest(BaseModel):
    video_path: str
    output_path: str
    work_dir: str = "/tmp"
