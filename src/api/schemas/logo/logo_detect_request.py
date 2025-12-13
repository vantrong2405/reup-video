from pydantic import BaseModel

class LogoDetectRequest(BaseModel):
    image_path: str
    model_path: str = "/data/models/best.pt"
    conf_threshold: float = 0.25
