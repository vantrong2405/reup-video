from pydantic import BaseModel
from typing import List
from api.schemas.text.text_box import TextBox

class TextMaskFiltersData(BaseModel):
    filter_string: str
    boxes: List[TextBox]
