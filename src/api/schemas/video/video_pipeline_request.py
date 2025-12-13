from pydantic import BaseModel
from typing import Optional, List

class VideoPipelineRequest(BaseModel):
    video_input: str
    logo_input: str
    detect_json: str = "{}"
    output_path: str
    new_logo_url: Optional[str] = None
    intro_url: Optional[str] = None
    work_dir: str = "/tmp"
    flip: bool = False
    zoom: float = 1.0
    speed: float = 1.0
    brightness: float = 0.0
    saturation: float = 1.0
    hue: float = 0.0
    background_music: Optional[str] = None
    bg_music_volume: float = 0.3
    remove_text: bool = False
    ocr_languages: List[str] = ["en"]
    gemini_key: Optional[str] = None
    filter_nsfw: bool = False
    ffmpeg_preset: str = "veryfast"
    split_mode: str = "none"
    split_start: str = "00:00:00"
    split_duration: float = 10.0
    split_limit: int = 5
    unique_mode: bool = False
    watermark_text: Optional[str] = None
    watermark_opacity: float = 0.15
    watermark_size: int = 18
    watermark_speed: int = 50
    watermark_position: str = "bottom"
