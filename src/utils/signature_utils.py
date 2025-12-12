import random
import uuid
from datetime import datetime

class SignatureUtils:
    
    @staticmethod
    def get_random_metadata():
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()
        return {
            "comment": f"N8N-{unique_id}",
            "creation_time": timestamp,
            "copyright": f"N8N-{unique_id}"
        }

    @staticmethod
    def get_visual_filters():
        br = random.uniform(-0.02, 0.02)
        sat = random.uniform(0.98, 1.02)
        contrast = random.uniform(0.98, 1.02)
        h = random.uniform(-0.02, 0.02)
        
        return [
            f"eq=brightness={br:.3f}:saturation={sat:.3f}:contrast={contrast:.3f}",
            f"hue=h={h:.3f}",
            "noise=c0s=2:allf=t"
        ]

    @staticmethod
    def get_audio_filters():
        pitch = random.uniform(0.99, 1.01)
        return [f"asetrate=44100*{pitch:.4f}", "aresample=44100"]

    @staticmethod
    def get_watermark_filter(text, opacity=0.3, size=24, speed=100, position="bottom", color="yellow"):
        if not text:
            return ""
        
        safe_text = text.replace("'", "").replace(":", "").replace('"', '').replace("\\", "")
        
        # Use single backslash for FFmpeg expression escaping
        # The comma in mod() needs to be escaped as \, for FFmpeg filter syntax
        if position == "bottom":
            x_expr = f"w-mod(t*{speed}\\,w+tw)"
            y_expr = "h-th-20"
        elif position == "top":
            x_expr = f"w-mod(t*{speed}\\,w+tw)"
            y_expr = "20"
        else:
            x_expr = f"w-mod(t*{speed}\\,w+tw)"
            y_expr = "h-th-20"
        
        return f"drawtext=text='{safe_text}':fontsize={size}:fontcolor={color}@{opacity}:x={x_expr}:y={y_expr}"

    @staticmethod
    def get_watermark_filter_static(text, opacity=0.3, size=24, position="bottom", color="yellow"):
        """Static watermark (no scrolling) for maximum compatibility."""
        if not text:
            return ""
        
        safe_text = text.replace("'", "").replace(":", "").replace('"', '').replace("\\", "")
        
        if position == "bottom":
            x_val = "10"
            y_val = "h-th-20"
        elif position == "top":
            x_val = "10"
            y_val = "20"
        else:
            x_val = "10"
            y_val = "h-th-20"
        
        return f"drawtext=text='{safe_text}':fontsize={size}:fontcolor={color}@{opacity}:x={x_val}:y={y_val}"
