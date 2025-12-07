#!/usr/bin/env python3

import sys
import json
from pathlib import Path
from ultralytics import YOLO

def test_all_images(model_path, dataset_path, conf_threshold=0.25):
    model = YOLO(model_path)
    dataset_path = Path(dataset_path)
    
    results = []
    
    # Test valid images
    valid_images_dir = dataset_path / "valid" / "images"
    if valid_images_dir.exists():
        print("=== TESTING VALID IMAGES ===")
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
                print(f"✅ {img_path.name}: {result['status']} (conf: {result['confidence']})")
            except Exception as e:
                result = {
                    "image": img_path.name,
                    "error": str(e),
                    "status": "error"
                }
                results.append(result)
                print(f"❌ {img_path.name}: ERROR - {e}")
    
    # Test train images
    train_images_dir = dataset_path / "train" / "images"
    if train_images_dir.exists():
        print("\n=== TESTING TRAIN IMAGES ===")
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
                print(f"✅ {img_path.name}: {result['status']} (conf: {result['confidence']})")
            except Exception as e:
                result = {
                    "image": img_path.name,
                    "error": str(e),
                    "status": "error"
                }
                results.append(result)
                print(f"❌ {img_path.name}: ERROR - {e}")
    
    # Summary
    print("\n=== SUMMARY ===")
    detected = sum(1 for r in results if r.get("status") == "detected")
    no_detection = sum(1 for r in results if r.get("status") == "no_detection")
    errors = sum(1 for r in results if r.get("status") == "error")
    total = len(results)
    
    print(f"Total images: {total}")
    print(f"Detected: {detected}")
    print(f"No detection: {no_detection}")
    print(f"Errors: {errors}")
    print(f"Success rate: {detected/total*100:.1f}%")
    
    print(json.dumps({"results": results, "summary": {
        "total": total,
        "detected": detected,
        "no_detection": no_detection,
        "errors": errors,
        "success_rate": round(detected/total*100, 1) if total > 0 else 0
    }}, indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: test_all_images.py <model_path> <dataset_path> [conf_threshold]")
        sys.exit(1)
    
    model_path = sys.argv[1]
    dataset_path = sys.argv[2]
    conf_threshold = float(sys.argv[3]) if len(sys.argv) > 3 else 0.25
    
    test_all_images(model_path, dataset_path, conf_threshold)
