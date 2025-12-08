#!/usr/bin/env python3

import sys
import json
import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO


def detect_logo(image_path, model_path, conf_threshold=0.25):
    if not Path(image_path).exists():
        print(json.dumps({"logos": [], "count": 0, "error": f"Image not found: {image_path}"}), file=sys.stderr)
        sys.exit(1)

    if not Path(model_path).exists():
        print(json.dumps({"logos": [], "count": 0, "error": f"Model not found: {model_path}"}), file=sys.stderr)
        sys.exit(1)

    try:
        model = YOLO(model_path)
        results = model(image_path, conf=conf_threshold, verbose=False)

        if not results or len(results) == 0:
            print(json.dumps({"logos": [], "count": 0}))
            return

        result = results[0]

        if result.boxes is None or len(result.boxes) == 0:
            print(json.dumps({"logos": [], "count": 0}))
            return

        boxes = result.boxes.xyxy.cpu().numpy()
        confidences = result.boxes.conf.cpu().numpy()

        img = cv2.imread(image_path)
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

        if len(detections) == 0:
            print(json.dumps({"logos": [], "count": 0}))
        else:
            print(json.dumps({"logos": detections, "count": len(detections)}))

    except Exception as e:
        print(json.dumps({"logos": [], "count": 0, "error": str(e)}), file=sys.stderr)
        sys.exit(1)


def overlay_logo_single(origin_img, logo_img, x, y, width, height):
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


def overlay_logo_boxes(origin_img, logo_img, boxes, debug_img=None):
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

        margin = 8
        remove_x = max(0, x - margin)
        remove_y = max(0, y - margin)
        remove_w = min(origin_w - remove_x, width + margin * 2)
        remove_h = min(origin_h - remove_y, height + margin * 2)

        roi = origin_img[remove_y:remove_y+remove_h, remove_x:remove_x+remove_w]
        blurred_roi = cv2.GaussianBlur(roi, (21, 21), 0)
        origin_img[remove_y:remove_y+remove_h, remove_x:remove_x+remove_w] = blurred_roi

        scale_factor = 1.15
        new_width = int(width * scale_factor)
        new_height = int(height * scale_factor)
        logo_resized = cv2.resize(logo_img, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)

        offset_x = (new_width - width) // 2
        offset_y = (new_height - height) // 2
        overlay_x = max(0, x - offset_x)
        overlay_y = max(0, y - offset_y)

        if overlay_x + new_width > origin_w:
            overlay_x = origin_w - new_width
        if overlay_y + new_height > origin_h:
            overlay_y = origin_h - new_height

        roi_h = min(new_height, origin_h - overlay_y)
        roi_w = min(new_width, origin_w - overlay_x)

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


def main():
    if len(sys.argv) < 2:
        print("Usage:", file=sys.stderr)
        print("  Detect only: logo_detect_overlay.py detect <image_path> [model_path] [conf_threshold]", file=sys.stderr)
        print("  Overlay only: logo_detect_overlay.py overlay <origin> <logo> <x> <y> <width> <height> <output>", file=sys.stderr)
        print("  Detect + Overlay: logo_detect_overlay.py process <origin> <logo> <model_path> [conf_threshold] <output>", file=sys.stderr)
        sys.exit(1)

    mode = sys.argv[1]

    if mode == "detect":
        if len(sys.argv) < 3:
            print("Usage: logo_detect_overlay.py detect <image_path> [model_path] [conf_threshold]", file=sys.stderr)
            sys.exit(1)
        image_path = sys.argv[2]
        model_path = sys.argv[3] if len(sys.argv) > 3 else "best.pt"
        conf_threshold = float(sys.argv[4]) if len(sys.argv) > 4 else 0.25
        detect_logo(image_path, model_path, conf_threshold)

    elif mode == "overlay":
        if len(sys.argv) < 9:
            print("Usage: logo_detect_overlay.py overlay <origin> <logo> <x> <y> <width> <height> <output>", file=sys.stderr)
            sys.exit(1)
        origin_path = Path(sys.argv[2])
        logo_path = Path(sys.argv[3])
        x, y = int(sys.argv[4]), int(sys.argv[5])
        width, height = int(sys.argv[6]), int(sys.argv[7])
        output_path = Path(sys.argv[8])

        if not origin_path.exists():
            print(json.dumps({"output": "", "error": f"Origin image not found: {origin_path}"}), file=sys.stderr)
            sys.exit(1)

        if not logo_path.exists():
            print(json.dumps({"output": "", "error": f"Logo image not found: {logo_path}"}), file=sys.stderr)
            sys.exit(1)

        origin_img = cv2.imread(str(origin_path))
        logo_img = cv2.imread(str(logo_path), cv2.IMREAD_UNCHANGED)

        if origin_img is None:
            print(json.dumps({"output": "", "error": f"Failed to read origin image: {origin_path}"}), file=sys.stderr)
            sys.exit(1)

        if logo_img is None:
            print(json.dumps({"output": "", "error": f"Failed to read logo image: {logo_path}"}), file=sys.stderr)
            sys.exit(1)

        try:
            overlay_logo_single(origin_img, logo_img, x, y, width, height)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_path), origin_img)
            print(json.dumps({"output": str(output_path)}))
        except Exception as e:
            print(json.dumps({"output": "", "error": str(e)}), file=sys.stderr)
            sys.exit(1)

    elif mode == "process":
        if len(sys.argv) < 6:
            print("Usage: logo_detect_overlay.py process <origin> <logo> <model_path> [conf_threshold] <output>", file=sys.stderr)
            sys.exit(1)
        origin_path = Path(sys.argv[2])
        logo_path = Path(sys.argv[3])
        model_path = sys.argv[4]
        if len(sys.argv) >= 7:
            try:
                conf_threshold = float(sys.argv[5])
                output_path = Path(sys.argv[6])
            except ValueError:
                conf_threshold = 0.25
                output_path = Path(sys.argv[5])
        else:
            conf_threshold = 0.25
            output_path = Path(sys.argv[5])

        if not origin_path.exists():
            print(json.dumps({"output": "", "error": f"Origin image not found: {origin_path}"}), file=sys.stderr)
            sys.exit(1)

        if not logo_path.exists():
            print(json.dumps({"output": "", "error": f"Logo image not found: {logo_path}"}), file=sys.stderr)
            sys.exit(1)

        if not Path(model_path).exists():
            print(json.dumps({"output": "", "error": f"Model not found: {model_path}"}), file=sys.stderr)
            sys.exit(1)

        try:
            model = YOLO(model_path)
            results = model(str(origin_path), conf=conf_threshold, verbose=False)

            if not results or len(results) == 0 or results[0].boxes is None or len(results[0].boxes) == 0:
                print(json.dumps({"output": "", "error": "No logos detected"}), file=sys.stderr)
                sys.exit(1)

            boxes = results[0].boxes.xyxy.cpu().numpy()
            confidences = results[0].boxes.conf.cpu().numpy()

            origin_img = cv2.imread(str(origin_path))
            logo_img = cv2.imread(str(logo_path), cv2.IMREAD_UNCHANGED)

            if origin_img is None:
                print(json.dumps({"output": "", "error": f"Failed to read origin image"}), file=sys.stderr)
                sys.exit(1)

            if logo_img is None:
                print(json.dumps({"output": "", "error": f"Failed to read logo image"}), file=sys.stderr)
                sys.exit(1)

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
                overlay_logo_single(origin_img, logo_img, box['x'], box['y'], box['width'], box['height'])
            else:
                overlay_logo_boxes(origin_img, logo_img, boxes_list)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_path), origin_img)
            print(json.dumps({"output": str(output_path), "detected": len(boxes_list)}))

        except Exception as e:
            print(json.dumps({"output": "", "error": str(e)}), file=sys.stderr)
            sys.exit(1)

    else:
        print(f"Unknown mode: {mode}", file=sys.stderr)
        print("Modes: detect, overlay, process", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
