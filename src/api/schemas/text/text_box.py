from pydantic import BaseModel

class TextBox(BaseModel):
    x: int
    y: int
    width: int
    height: int
    text: str
    prob: float
