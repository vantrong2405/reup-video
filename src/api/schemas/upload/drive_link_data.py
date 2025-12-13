from pydantic import BaseModel
from typing import Optional

class DriveLinkData(BaseModel):
    link: Optional[str]
