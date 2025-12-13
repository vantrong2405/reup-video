from pydantic import BaseModel
from typing import List
from api.schemas.text.text_box import TextBox

class TextDetectData(BaseModel):
    boxes: List[TextBox]
    count: int
