#!/usr/bin/env python3

import sys
import json
from pathlib import Path
from ultralytics import YOLO
import cv2


def detect_logo(image_path, model_path="best.pt", conf_threshold=0.25):
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
        for i, (box, conf) in enumerate(zip(boxes, confidences)):
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


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"logos": [], "count": 0, "error": "Usage: detect_yolo.py <image_path> [model_path] [conf_threshold]"}), file=sys.stderr)
        sys.exit(1)

    image_path = sys.argv[1]
    model_path = sys.argv[2] if len(sys.argv) > 2 else "best.pt"
    conf_threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.25

    detect_logo(image_path, model_path, conf_threshold)


if __name__ == "__main__":
    main()
