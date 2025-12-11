import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO

class LogoService:
    MARGIN = 0
    SCALE_W = 1.0
    SCALE_H = 1.0
    OFFSET_Y = 0

    @staticmethod
    def _validate_exists(path: Path, message: str):
        if not path.exists():
            raise FileNotFoundError(message)

    @staticmethod
    def detect_logo(image_path: str, model_path: str, conf_threshold: float = 0.25):
        image_path = Path(image_path)
        model_path = Path(model_path)
        LogoService._validate_exists(image_path, f"Image not found: {image_path}")
        LogoService._validate_exists(model_path, f"Model not found: {model_path}")

        model = YOLO(str(model_path))
        results = model(str(image_path), conf=conf_threshold, verbose=False)
        if not results or len(results) == 0:
            return {"logos": [], "count": 0}

        result = results[0]
        if result.boxes is None or len(result.boxes) == 0:
            return {"logos": [], "count": 0}

        boxes = result.boxes.xyxy.cpu().numpy()
        confidences = result.boxes.conf.cpu().numpy()

        img = cv2.imread(str(image_path))
        img_h, img_w = img.shape[:2] if img is not None else (0, 0)

        detections = []
        for box, conf in zip(boxes, confidences):
            x1, y1, x2, y2 = box
            x = int(x1)
            y = int(y1)
            width = int(x2 - x1)
            height = int(y2 - y1)

            if img is not None:
                x = max(0, min(x, img_w - 1))
                y = max(0, min(y, img_h - 1))
                width = max(1, min(width, img_w - x))
                height = max(1, min(height, img_h - y))

            detections.append({
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "confidence": float(conf)
            })

        return {"logos": detections, "count": len(detections)}

    @staticmethod
    def _apply_overlay(origin_img, logo_img, boxes, debug_img=None):
        origin_h, origin_w = origin_img.shape[:2]

        if debug_img is not None:
            for i, box in enumerate(boxes):
                x, y, w, h = box['x'], box['y'], box['width'], box['height']
                color = (255, 0, 0) if i == 0 else (0, 0, 255)
                cv2.rectangle(debug_img, (x, y), (x + w, y + h), color, 2)
                cv2.putText(debug_img, f"#{i+1} {x},{y} {w}x{h}", (x, max(20, y-10)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        for box in boxes:
            x = max(0, min(box['x'], origin_w - 1))
            y = max(0, min(box['y'], origin_h - 1))
            width = max(1, min(box['width'], origin_w - x))
            height = max(1, min(box['height'], origin_h - y))

            # 1. Blur the area (Delogo)
            margin = LogoService.MARGIN
            remove_x = max(0, x - margin)
            remove_y = max(0, y - margin)
            remove_w = min(origin_w - remove_x, width + margin * 2)
            remove_h = min(origin_h - remove_y, height + margin * 2)

            roi = origin_img[remove_y:remove_y+remove_h, remove_x:remove_x+remove_w]
            blurred_roi = cv2.GaussianBlur(roi, (21, 21), 0)
            origin_img[remove_y:remove_y+remove_h, remove_x:remove_x+remove_w] = blurred_roi

            # 2. Calculate new size with Scale (Smart Cover Logic)
            logo_h, logo_w = logo_img.shape[:2]
            if logo_h > 0:
                logo_aspect = logo_w / logo_h
            else:
                logo_aspect = 1.0

            # Desired minimum coverage box (what we want to cover)
            req_w = width * LogoService.SCALE_W
            req_h = height * LogoService.SCALE_H

            # Option A: Anchor to Height
            calc_w_by_h = req_h * logo_aspect
            
            # Check if this covers the width
            if calc_w_by_h < req_w:
                # Width is insufficient, so we must anchor to Width (Option B)
                new_width = int(req_w)
                new_height = int(req_w / logo_aspect)
            else:
                # Width is sufficient (or surplus), anchor to Height (Option A)
                new_width = int(calc_w_by_h)
                new_height = int(req_h)

            # Fit inside frame (optional, but good safety)
            if new_width <= 0 or new_height <= 0:
                continue

            # 3. Calculate Position (Center aligned + Offset)
            center_x = x + width // 2
            center_y = y + height // 2
            
            # Ideally where we want to place the top-left of the NEW logo
            overlay_x = int(center_x - new_width / 2)
            overlay_y = int(center_y - new_height / 2)

            overlay_y += LogoService.OFFSET_Y

            # 4. Handle boundary checks -> CROP instead of SHIFT
            # Define the box of the overlay in absolute image coordinates
            x1 = overlay_x
            y1 = overlay_y
            x2 = x1 + new_width
            y2 = y1 + new_height

            # Image bounds
            img_x1, img_y1 = 0, 0
            img_x2, img_y2 = origin_w, origin_h

            # Calculate intersection (The part of the logo that is actually visible)
            xx1 = max(x1, img_x1)
            yy1 = max(y1, img_y1)
            xx2 = min(x2, img_x2)
            yy2 = min(y2, img_y2)

            # Check if there is any intersection
            if xx1 >= xx2 or yy1 >= yy2:
                continue

            # Calculate relative coordinates for cropping the LOGO source
            logo_crop_x1 = xx1 - x1
            logo_crop_y1 = yy1 - y1
            logo_crop_x2 = logo_crop_x1 + (xx2 - xx1)
            logo_crop_y2 = logo_crop_y1 + (yy2 - yy1)

            # 5. Resize logo
            logo_resized = cv2.resize(logo_img, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
            
            # Crop the logo to match the intersection area
            logo_cropped = logo_resized[logo_crop_y1:logo_crop_y2, logo_crop_x1:logo_crop_x2]
            
            # Dimensions of the destination area
            roi_h = yy2 - yy1
            roi_w = xx2 - xx1

            # 6. Blend/Overlay
            if logo_cropped.shape[2] == 4:
                alpha = logo_cropped[:, :, 3] / 255.0
                alpha = np.stack([alpha, alpha, alpha], axis=2)
                logo_rgb = logo_cropped[:, :, :3]
                
                # Destination slice
                roi_bg = origin_img[yy1:yy2, xx1:xx2]
                
                blended = (logo_rgb * alpha + roi_bg * (1 - alpha)).astype(np.uint8)
                origin_img[yy1:yy2, xx1:xx2] = blended
            else:
                origin_img[yy1:yy2, xx1:xx2] = logo_cropped

    @staticmethod
    def overlay_logo(origin_path: str, logo_path: str, x: int, y: int, width: int, height: int, output_path: str):
        origin_path = Path(origin_path)
        logo_path = Path(logo_path)
        output_path = Path(output_path)

        LogoService._validate_exists(origin_path, f"Origin image not found: {origin_path}")
        LogoService._validate_exists(logo_path, f"Logo image not found: {logo_path}")

        origin_img = cv2.imread(str(origin_path))
        logo_img = cv2.imread(str(logo_path), cv2.IMREAD_UNCHANGED)

        if origin_img is None:
            raise ValueError(f"Failed to read origin image: {origin_path}")
        if logo_img is None:
            raise ValueError(f"Failed to read logo image: {logo_path}")

        # Construct a box dict to use the unified logic
        box = {"x": x, "y": y, "width": width, "height": height}
        LogoService._apply_overlay(origin_img, logo_img, [box])
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), origin_img)
        return {"output": str(output_path)}

    @staticmethod
    def process_logo(origin_path: str, logo_path: str, model_path: str, conf_threshold: float, output_path: str):
        origin_path = Path(origin_path)
        logo_path = Path(logo_path)
        model_path = Path(model_path)
        output_path = Path(output_path)

        LogoService._validate_exists(origin_path, f"Origin image not found: {origin_path}")
        LogoService._validate_exists(logo_path, f"Logo image not found: {logo_path}")
        LogoService._validate_exists(model_path, f"Model not found: {model_path}")

        model = YOLO(str(model_path))
        results = model(str(origin_path), conf=conf_threshold, verbose=False)

        if not results or len(results) == 0 or results[0].boxes is None or len(results[0].boxes) == 0:
            raise ValueError("No logos detected")

        boxes = results[0].boxes.xyxy.cpu().numpy()
        confidences = results[0].boxes.conf.cpu().numpy()

        origin_img = cv2.imread(str(origin_path))
        logo_img = cv2.imread(str(logo_path), cv2.IMREAD_UNCHANGED)

        if origin_img is None:
            raise ValueError("Failed to read origin image")
        if logo_img is None:
            raise ValueError("Failed to read logo image")

        img_h, img_w = origin_img.shape[:2]

        boxes_list = []
        for box, conf in zip(boxes, confidences):
            x1, y1, x2, y2 = box
            
            # Use original float coordinates for more precision if needed, but rounding to int for safe indexing is fine
            # Ensure coordinates are within image bounds
            x = max(0, min(int(x1), img_w - 1))
            y = max(0, min(int(y1), img_h - 1))
            width = max(1, min(int(x2 - x1), img_w - x))
            height = max(1, min(int(y2 - y1), img_h - y))
            
            boxes_list.append({"x": x, "y": y, "width": width, "height": height, "confidence": float(conf)})

        # Use unified logic for ALL boxes (singular or multiple)
        LogoService._apply_overlay(origin_img, logo_img, boxes_list)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), origin_img)
        return {"output": str(output_path), "detected": len(boxes_list)}
