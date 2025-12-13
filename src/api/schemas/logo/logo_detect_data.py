from pydantic import BaseModel
from typing import List
from api.schemas.logo.logo_box import LogoBox

class LogoDetectData(BaseModel):
    logos: List[LogoBox]
    count: int
