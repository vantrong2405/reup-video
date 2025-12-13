from pydantic import BaseModel

class UploadDriveRequest(BaseModel):
    local_path: str
    drive_destination: str
