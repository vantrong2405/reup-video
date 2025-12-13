from pydantic import BaseModel

class LogoBox(BaseModel):
    x: int
    y: int
    width: int
    height: int
    confidence: float
