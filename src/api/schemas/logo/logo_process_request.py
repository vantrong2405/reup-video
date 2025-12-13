from pydantic import BaseModel

class LogoProcessRequest(BaseModel):
    origin_path: str
    logo_path: str
    model_path: str = "/data/models/best.pt"
    conf_threshold: float = 0.25
    output_path: str
    scale_w: float = 1.0
    scale_h: float = 1.0
    margin: int = 0
    offset_y: int = 0
