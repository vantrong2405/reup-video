#!/usr/bin/env python3

import sys
import json
from pathlib import Path
from ultralytics import YOLO
import cv2


def test_single_image(image_path, model_path, conf_threshold=0.25, output_path=None):
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
            return

        result = results[0]

        if result.boxes is None or len(result.boxes) == 0:
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
                "image": Path(image_path).name,
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "confidence": round(float(conf), 3),
                "class": int(cls),
                "status": "detected"
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
        else:
            output_path = Path("test_result.jpg")
            cv2.imwrite(str(output_path), img)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def test_all_images(model_path, dataset_path, conf_threshold=0.25):
    model = YOLO(model_path)
    dataset_path = Path(dataset_path)

    results = []

    valid_images_dir = dataset_path / "valid" / "images"
    if valid_images_dir.exists():
        for img_path in sorted(valid_images_dir.glob("*.png")):
            try:
                predictions = model(str(img_path), conf=conf_threshold)
                if predictions and len(predictions) > 0:
                    boxes = predictions[0].boxes
                    if len(boxes) > 0:
                        box = boxes[0]
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        width = int(x2 - x1)
                        height = int(y2 - y1)
                        x = int(x1)
                        y = int(y1)
                        conf = float(box.conf[0].cpu().numpy())

                        result = {
                            "image": img_path.name,
                            "x": x,
                            "y": y,
                            "width": width,
                            "height": height,
                            "confidence": round(conf, 3),
                            "status": "detected"
                        }
                    else:
                        result = {
                            "image": img_path.name,
                            "x": 0,
                            "y": 0,
                            "width": 0,
                            "height": 0,
                            "confidence": 0.0,
                            "status": "no_detection"
                        }
                else:
                    result = {
                        "image": img_path.name,
                        "x": 0,
                        "y": 0,
                        "width": 0,
                        "height": 0,
                        "confidence": 0.0,
                        "status": "no_detection"
                    }
                results.append(result)
            except Exception as e:
                result = {
                    "image": img_path.name,
                    "error": str(e),
                    "status": "error"
                }
                results.append(result)

    train_images_dir = dataset_path / "train" / "images"
    if train_images_dir.exists():
        for img_path in sorted(train_images_dir.glob("*.png")):
            try:
                predictions = model(str(img_path), conf=conf_threshold)
                if predictions and len(predictions) > 0:
                    boxes = predictions[0].boxes
                    if len(boxes) > 0:
                        box = boxes[0]
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        width = int(x2 - x1)
                        height = int(y2 - y1)
                        x = int(x1)
                        y = int(y1)
                        conf = float(box.conf[0].cpu().numpy())

                        result = {
                            "image": img_path.name,
                            "x": x,
                            "y": y,
                            "width": width,
                            "height": height,
                            "confidence": round(conf, 3),
                            "status": "detected"
                        }
                    else:
                        result = {
                            "image": img_path.name,
                            "x": 0,
                            "y": 0,
                            "width": 0,
                            "height": 0,
                            "confidence": 0.0,
                            "status": "no_detection"
                        }
                else:
                    result = {
                        "image": img_path.name,
                        "x": 0,
                        "y": 0,
                        "width": 0,
                        "height": 0,
                        "confidence": 0.0,
                        "status": "no_detection"
                    }
                results.append(result)
            except Exception as e:
                result = {
                    "image": img_path.name,
                    "error": str(e),
                    "status": "error"
                }
                results.append(result)

    detected = sum(1 for r in results if r.get("status") == "detected")
    no_detection = sum(1 for r in results if r.get("status") == "no_detection")
    errors = sum(1 for r in results if r.get("status") == "error")
    total = len(results)

    print(json.dumps({"results": results, "summary": {
        "total": total,
        "detected": detected,
        "no_detection": no_detection,
        "errors": errors,
        "success_rate": round(detected/total*100, 1) if total > 0 else 0
    }}, indent=2))


def main():
    if len(sys.argv) < 3:
        print("Usage:", file=sys.stderr)
        print("  Test single image: test_yolo.py <image_path> <model_path> [conf_threshold] [output_path]", file=sys.stderr)
        print("  Test all images: test_yolo.py --all <model_path> <dataset_path> [conf_threshold]", file=sys.stderr)
        print("\nExamples:", file=sys.stderr)
        print("  test_yolo.py image.jpg best.pt 0.25 output.jpg", file=sys.stderr)
        print("  test_yolo.py --all best.pt dataset_yolo 0.25", file=sys.stderr)
        sys.exit(1)

    if sys.argv[1] == "--all":
        if len(sys.argv) < 4:
            print("Usage: test_yolo.py --all <model_path> <dataset_path> [conf_threshold]", file=sys.stderr)
            sys.exit(1)
        model_path = sys.argv[2]
        dataset_path = sys.argv[3]
        conf_threshold = float(sys.argv[4]) if len(sys.argv) > 4 else 0.25
        test_all_images(model_path, dataset_path, conf_threshold)
    else:
        image_path = sys.argv[1]
        model_path = sys.argv[2]
        conf_threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.25
        output_path = sys.argv[4] if len(sys.argv) > 4 else None
        test_single_image(image_path, model_path, conf_threshold, output_path)


if __name__ == "__main__":
    main()
