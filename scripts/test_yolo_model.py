#!/usr/bin/env python3

import sys
import json
from pathlib import Path
from ultralytics import YOLO
import cv2


def test_model(image_path, model_path="best.pt", conf_threshold=0.25, output_path=None):
    if not Path(image_path).exists():
        print(f"Error: Image not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    if not Path(model_path).exists():
        print(f"Error: Model not found: {model_path}", file=sys.stderr)
        sys.exit(1)

    try:
        model = YOLO(model_path)
        results = model(image_path, conf=conf_threshold, verbose=False)

        if not results or len(results) == 0:
            print("No detections found")
            return

        result = results[0]

        if result.boxes is None or len(result.boxes) == 0:
            print("No detections found")
            return

        boxes = result.boxes.xyxy.cpu().numpy()
        confidences = result.boxes.conf.cpu().numpy()
        classes = result.boxes.cls.cpu().numpy()

        img = cv2.imread(image_path)
        if img is None:
            print(f"Error: Failed to read image: {image_path}", file=sys.stderr)
            sys.exit(1)

        img_h, img_w = img.shape[:2]

        detections = []
        for i, (box, conf, cls) in enumerate(zip(boxes, confidences, classes)):
            x1, y1, x2, y2 = box
            x = int(x1)
            y = int(y1)
            width = int(x2 - x1)
            height = int(y2 - y1)

            x = max(0, min(x, img_w - 1))
            y = max(0, min(y, img_h - 1))
            width = max(1, min(width, img_w - x))
            height = max(1, min(height, img_h - y))

            detections.append({
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "confidence": float(conf),
                "class": int(cls)
            })

            color = (0, 255, 0) if i == 0 else (255, 0, 0)
            cv2.rectangle(img, (x, y), (x + width, y + height), color, 2)
            cv2.putText(img, f"logo {conf:.2f}", (x, max(20, y-10)),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        print(json.dumps(detections, indent=2))

        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            cv2.imwrite(str(output_path), img)
            print(f"\nVisualization saved to: {output_path}")
        else:
            cv2.imwrite("test_result.jpg", img)
            print(f"\nVisualization saved to: test_result.jpg")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print("Usage: test_yolo_model.py <image_path> [model_path] [conf_threshold] [output_path]", file=sys.stderr)
        sys.exit(1)

    image_path = sys.argv[1]
    model_path = sys.argv[2] if len(sys.argv) > 2 else "best.pt"
    conf_threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.25
    output_path = sys.argv[4] if len(sys.argv) > 4 else None

    test_model(image_path, model_path, conf_threshold, output_path)


if __name__ == "__main__":
    main()
