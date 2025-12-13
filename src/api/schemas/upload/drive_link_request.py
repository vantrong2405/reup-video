from pydantic import BaseModel

class DriveLinkRequest(BaseModel):
    drive_path: str
