from pydantic import BaseModel

class AIRewriteData(BaseModel):
    original: str
    rewritten: str
