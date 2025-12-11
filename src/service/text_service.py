import easyocr
import cv2
from pathlib import Path

class TextService:
    def __init__(self, languages=['en']):
        self.reader = easyocr.Reader(languages)

    def detect_text(self, image_path):
        """
        Detects text in the given image path.
        Returns a list of bounding boxes (x, y, w, h).
        """
        img = cv2.imread(str(image_path))
        if img is None:
            raise FileNotFoundError(f"Image not found: {image_path}")

        results = self.reader.readtext(str(image_path))
        boxes = []
        for (bbox, text, prob) in results:
            # bbox is [[x1, y1], [x2, y1], [x2, y2], [x1, y2]]
            (tl, tr, br, bl) = bbox
            x = int(tl[0])
            y = int(tl[1])
            w = int(br[0] - tl[0])
            h = int(br[1] - tl[1])
            boxes.append({"x": x, "y": y, "width": w, "height": h, "text": text, "prob": prob})
        
        return boxes

    @staticmethod
    def generate_mask_filters(video_path, service=None):
        """
        Extracts a sample frame, detects text, and returns FFmpeg filter string to mask it.
        Using a simplified strategy: Check frame at 10% duration.
        """
        import subprocess
        
        video_path = Path(video_path)
        temp_frame = video_path.parent / f"temp_ocr_frame_{video_path.stem}.jpg"
        
        # 1. Extract Sample Frame (at 5 seconds or start)
        # Using ffmpeg to extract one frame
        cmd = f"ffmpeg -y -i \"{video_path}\" -ss 00:00:05 -vframes 1 \"{temp_frame}\""
        subprocess.run(cmd, shell=True, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        if not temp_frame.exists():
            # Fallback to start if video is short
            cmd = f"ffmpeg -y -i \"{video_path}\" -vframes 1 \"{temp_frame}\""
            subprocess.run(cmd, shell=True, check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
        if not temp_frame.exists():
             return "", [] # Cannot process
             
        # 2. Detect Text
        if service is None:
            service = TextService()
            
        boxes = service.detect_text(temp_frame)
        
        # Cleanup
        temp_frame.unlink()
        
        if not boxes:
            return "", []

        # 3. Generate Filters
        filter_parts = []
        # We will use 'drawbox' to paint black box over text
        # Or 'delogo' for blurring. User asked to "remove" text.
        # Drawbox with color logic or delogo?
        # User complained about "reversed text". If we just blur it, it's fine.
        # But "drawbox=color=black@1.0:t=fill" is stronger masking (like censorship).
        # Let's use delogo for a cleaner look if possible, or blur.
        # Actually, drawbox with a "background color" might be better if we know the background.
        # For REUP, simpler is better. Let's use `delogo` (blur) for a "soft content removal" look.
        
        for box in boxes:
            x, y, w, h = box['x'], box['y'], box['width'], box['height']
            # Padding
            pad = 5
            x = max(0, x - pad)
            y = max(0, y - pad)
            w += pad * 2
            h += pad * 2
            
            # Use gblur (Gaussian Blur) with sigma calculation or simple boxblur
            # Or delogo which is smart blur.
            # Delogo is good.
            filter_parts.append(f"delogo=x={x}:y={y}:w={w}:h={h}")
            
        return ",".join(filter_parts), boxes
