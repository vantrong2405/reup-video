from pydantic import BaseModel

class LogoOverlayRequest(BaseModel):
    origin_path: str
    logo_path: str
    x: int
    y: int
    width: int
    height: int
    output_path: str
    scale_w: float = 1.0
    scale_h: float = 1.0
    margin: int = 0
    offset_y: int = 0
