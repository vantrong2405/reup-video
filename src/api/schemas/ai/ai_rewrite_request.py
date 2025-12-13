from pydantic import BaseModel

class AIRewriteRequest(BaseModel):
    text: str
    api_key: str
    target_language: str = "Vietnamese"
