from pydantic import BaseModel

class VideoPipelineData(BaseModel):
    output: str
    success: bool = True
