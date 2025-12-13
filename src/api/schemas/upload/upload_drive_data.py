from pydantic import BaseModel

class UploadDriveData(BaseModel):
    success: bool
    destination: str
