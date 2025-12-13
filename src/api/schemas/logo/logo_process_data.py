from pydantic import BaseModel

class LogoProcessData(BaseModel):
    output: str
    detected_logos: int = 0
