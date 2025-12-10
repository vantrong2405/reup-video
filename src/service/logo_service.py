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
    def _overlay_logo_single(origin_img, logo_img, x, y, width, height):
        origin_h, origin_w = origin_img.shape[:2]
        x = max(0, min(x, origin_w - 1))
        y = max(0, min(y, origin_h - 1))
        width = max(1, min(width, origin_w - x))
        height = max(1, min(height, origin_h - y))

        logo_resized = cv2.resize(logo_img, (width, height), interpolation=cv2.INTER_LANCZOS4)

        if logo_resized.shape[2] == 4:
            alpha = logo_resized[:, :, 3] / 255.0
            alpha = np.stack([alpha, alpha, alpha], axis=2)
            logo_rgb = logo_resized[:, :, :3]
            roi = origin_img[y:y+height, x:x+width]
            blended = (logo_rgb * alpha + roi * (1 - alpha)).astype(np.uint8)
            origin_img[y:y+height, x:x+width] = blended
        else:
            origin_img[y:y+height, x:x+width] = logo_resized

    @staticmethod
    def _overlay_logo_boxes(origin_img, logo_img, boxes, debug_img=None):
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

            margin = LogoService.MARGIN
            remove_x = max(0, x - margin)
            remove_y = max(0, y - margin)
            remove_w = min(origin_w - remove_x, width + margin * 2)
            remove_h = min(origin_h - remove_y, height + margin * 2)

            roi = origin_img[remove_y:remove_y+remove_h, remove_x:remove_x+remove_w]
            blurred_roi = cv2.GaussianBlur(roi, (21, 21), 0)
            origin_img[remove_y:remove_y+remove_h, remove_x:remove_x+remove_w] = blurred_roi

            scale_w = LogoService.SCALE_W
            scale_h = LogoService.SCALE_H
            new_width = int(width * scale_w)
            new_height = int(height * scale_h)

            # Fit inside frame while preserving requested scale center
            if new_width <= 0 or new_height <= 0:
                continue
            fit_ratio_w = (origin_w - 1) / new_width if new_width > 0 else 1.0
            fit_ratio_h = (origin_h - 1) / new_height if new_height > 0 else 1.0
            fit_ratio = min(fit_ratio_w, fit_ratio_h, 1.0)
            if fit_ratio < 1.0:
                new_width = max(1, int(new_width * fit_ratio))
                new_height = max(1, int(new_height * fit_ratio))

            logo_resized = cv2.resize(logo_img, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)

            center_x = x + width // 2
            center_y = y + height // 2
            overlay_x = int(center_x - new_width / 2)
            overlay_y = int(center_y - new_height / 2)

            overlay_y += LogoService.OFFSET_Y

            if overlay_x < 0:
                overlay_x = 0
            if overlay_y < 0:
                overlay_y = 0
            if overlay_x + new_width > origin_w:
                overlay_x = origin_w - new_width
            if overlay_y + new_height > origin_h:
                overlay_y = origin_h - new_height

            roi_h = min(new_height, max(0, origin_h - overlay_y))
            roi_w = min(new_width, max(0, origin_w - overlay_x))

            if roi_h < new_height or roi_w < new_width:
                logo_resized = cv2.resize(logo_resized, (roi_w, roi_h), interpolation=cv2.INTER_LANCZOS4)

            if logo_resized.shape[2] == 4:
                alpha = logo_resized[:, :, 3] / 255.0
                alpha = np.stack([alpha, alpha, alpha], axis=2)
                logo_rgb = logo_resized[:, :, :3]
                roi = origin_img[overlay_y:overlay_y+roi_h, overlay_x:overlay_x+roi_w]
                blended = (logo_rgb * alpha + roi * (1 - alpha)).astype(np.uint8)
                origin_img[overlay_y:overlay_y+roi_h, overlay_x:overlay_x+roi_w] = blended
            else:
                origin_img[overlay_y:overlay_y+roi_h, overlay_x:overlay_x+roi_w] = logo_resized

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

        LogoService._overlay_logo_single(origin_img, logo_img, x, y, width, height)
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
            x = max(0, min(int(x1), img_w - 1))
            y = max(0, min(int(y1), img_h - 1))
            width = max(1, min(int(x2 - x1), img_w - x))
            height = max(1, min(int(y2 - y1), img_h - y))
            boxes_list.append({"x": x, "y": y, "width": width, "height": height, "confidence": float(conf)})

        if len(boxes_list) == 1:
            box = boxes_list[0]
            LogoService._overlay_logo_single(origin_img, logo_img, box['x'], box['y'], box['width'], box['height'])
        else:
            LogoService._overlay_logo_boxes(origin_img, logo_img, boxes_list)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), origin_img)
        return {"output": str(output_path), "detected": len(boxes_list)}
