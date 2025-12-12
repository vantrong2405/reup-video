import easyocr
import cv2
import numpy as np
from pathlib import Path

from utils.command_utils import CommandUtils
from utils.video_utils import VideoUtils

DEFAULT_IOU_THRESHOLD = 0.1
DEFAULT_DIST_THRESHOLD = 20
DEFAULT_EXPAND = 10
DEFAULT_MAX_FRAMES = 3
SAFE_MARGIN = 2
DEFAULT_LANGUAGES = ['en']

class TextService:
    def __init__(self, languages=['en']):
        self.reader = easyocr.Reader(languages)

    def detect_text(self, image_path):
        img = cv2.imread(str(image_path))
        if img is None:
            raise FileNotFoundError(f"Image not found: {image_path}")

        results = self.reader.readtext(str(image_path))
        boxes = []
        for (bbox, text, prob) in results:
            (tl, tr, br, bl) = bbox
            x = int(tl[0])
            y = int(tl[1])
            w = int(br[0] - tl[0])
            h = int(br[1] - tl[1])
            boxes.append({"x": x, "y": y, "width": w, "height": h, "text": text, "prob": prob})
        
        return boxes

    @staticmethod
    def _merge_boxes(boxes, iou_threshold=DEFAULT_IOU_THRESHOLD, dist_threshold=DEFAULT_DIST_THRESHOLD):
        if not boxes:
            return []
            
        converted = []
        for b in boxes:
            converted.append([b['x'], b['y'], b['x'] + b['width'], b['y'] + b['height']])
        
        merged = []
        while converted:
            curr = converted.pop(0)
            merged_idx = -1
            
            for i, ex in enumerate(merged):
                x1 = max(curr[0], ex[0])
                y1 = max(curr[1], ex[1])
                x2 = min(curr[2], ex[2])
                y2 = min(curr[3], ex[3])
                
                inter_area = max(0, x2 - x1) * max(0, y2 - y1)
                x_dist = max(0, curr[0] - ex[2], ex[0] - curr[2])
                y_dist = max(0, curr[1] - ex[3], ex[1] - curr[3])
                
                should_merge = False
                if inter_area > 0:
                    area1 = (curr[2] - curr[0]) * (curr[3] - curr[1])
                    area2 = (ex[2] - ex[0]) * (ex[3] - ex[1])
                    if inter_area / (area1 + area2 - inter_area) > iou_threshold:
                        should_merge = True
                
                if not should_merge and x_dist < dist_threshold and y_dist < dist_threshold:
                     should_merge = True

                if should_merge:
                    merged_idx = i
                    break
            
            if merged_idx != -1:
                ex = merged[merged_idx]
                new_box = [
                    min(curr[0], ex[0]),
                    min(curr[1], ex[1]),
                    max(curr[2], ex[2]),
                    max(curr[3], ex[3])
                ]
                merged[merged_idx] = new_box
            else:
                merged.append(curr)

        final_boxes = []
        for b in merged:
            final_boxes.append({
                "x": b[0],
                "y": b[1],
                "width": b[2] - b[0],
                "height": b[3] - b[1]
            })
        return final_boxes

    @staticmethod
    def generate_mask_filters(video_path, languages=DEFAULT_LANGUAGES, expand=DEFAULT_EXPAND, max_frames=DEFAULT_MAX_FRAMES, vid_w=None, vid_h=None):
        video_path = Path(video_path)
        
        if vid_w is None or vid_h is None:
            try:
                info = VideoUtils.get_video_info(video_path)
                vid_w = info['width']
                vid_h = info['height']
            except:
                pass

        try:
             info = VideoUtils.get_video_info(video_path)
             duration = info['duration']
        except:
            duration = 10.0

        num_scans = max(1, max_frames)
        timestamps = [duration * (i + 1) / (num_scans + 1) for i in range(num_scans)]
        
        all_boxes = []
        service = TextService(languages=languages)

        for i, ts in enumerate(timestamps):
            temp_frame = video_path.parent / f"temp_ocr_{video_path.stem}_{i}.jpg"
            cmd = f"ffmpeg -y -i \"{video_path}\" -ss {ts} -vframes 1 \"{temp_frame}\""
            CommandUtils.run_command(cmd, check=False)
            
            if temp_frame.exists():
                try:
                    boxes = service.detect_text(temp_frame)
                    all_boxes.extend(boxes)
                except Exception as e:
                    print(f"OCR Error at {ts}s: {e}")
                finally:
                    temp_frame.unlink()

        unique_boxes = TextService._merge_boxes(all_boxes)
        
        if not unique_boxes:
            return "", []

        filter_parts = []
        for box in unique_boxes:
            x, y, w, h = box['x'], box['y'], box['width'], box['height']
            x = max(0, x - expand)
            y = max(0, y - expand)
            w += expand * 2
            h += expand * 2
            
            margin = SAFE_MARGIN
            
            x = (x // 2) * 2
            y = (y // 2) * 2
            w = ((w + 1) // 2) * 2
            h = ((h + 1) // 2) * 2

            if vid_w is not None and vid_h is not None:
                x = max(margin, min(x, vid_w - margin))
                y = max(margin, min(y, vid_h - margin))
                
                w = min(w, vid_w - margin - x)
                h = min(h, vid_h - margin - y)
                
                w = (w // 2) * 2
                h = (h // 2) * 2
            
            if w > 0 and h > 0:
                filter_parts.append(f"delogo=x={x}:y={y}:w={w}:h={h}")
            
        return ",".join(filter_parts), unique_boxes
