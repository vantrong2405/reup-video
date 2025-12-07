#!/usr/bin/env python3

import sys
import json
from pathlib import Path
import cv2
import numpy as np
from ultralytics import YOLO


def calculate_iou(box1, box2):
    x1_1, y1_1, w1, h1 = box1['x'], box1['y'], box1['width'], box1['height']
    x2_1, y2_1 = x1_1 + w1, y1_1 + h1

    x1_2, y1_2, w2, h2 = box2['x'], box2['y'], box2['width'], box2['height']
    x2_2, y2_2 = x1_2 + w2, y1_2 + h2

    xi1 = max(x1_1, x1_2)
    yi1 = max(y1_1, y1_2)
    xi2 = min(x2_1, x2_2)
    yi2 = min(y2_1, y2_2)

    inter_area = max(0, xi2 - xi1) * max(0, yi2 - yi1)

    box1_area = w1 * h1
    box2_area = w2 * h2
    union_area = box1_area + box2_area - inter_area

    if union_area == 0:
        return 0

    return inter_area / union_area


def calculate_center_distance(box1, box2):
    center1_x = box1['x'] + box1['width'] // 2
    center1_y = box1['y'] + box1['height'] // 2
    center2_x = box2['x'] + box2['width'] // 2
    center2_y = box2['y'] + box2['height'] // 2

    distance = ((center2_x - center1_x) ** 2 + (center2_y - center1_y) ** 2) ** 0.5
    avg_size = ((box1['width'] + box1['height'] + box2['width'] + box2['height']) / 4)

    return distance / max(avg_size, 1)


def filter_overlapping_boxes(boxes, iou_threshold=0.1, distance_threshold=1.5):
    if len(boxes) <= 1:
        return boxes

    boxes_sorted = sorted(boxes, key=lambda x: x['confidence'], reverse=True)
    filtered = []
    used = [False] * len(boxes_sorted)

    for i, box1 in enumerate(boxes_sorted):
        if used[i]:
            continue

        filtered.append(box1)
        used[i] = True

        for j, box2 in enumerate(boxes_sorted[i+1:], start=i+1):
            if used[j]:
                continue

            iou = calculate_iou(box1, box2)
            distance_ratio = calculate_center_distance(box1, box2)

            if iou > iou_threshold or distance_ratio < distance_threshold:
                used[j] = True

    if len(filtered) > 1:
        boxes_sorted_again = sorted(filtered, key=lambda x: x['confidence'], reverse=True)
        final_filtered = [boxes_sorted_again[0]]

        for box in boxes_sorted_again[1:]:
            iou_with_best = calculate_iou(boxes_sorted_again[0], box)
            distance_with_best = calculate_center_distance(boxes_sorted_again[0], box)

            if iou_with_best <= 0.05 and distance_with_best >= 2.0:
                final_filtered.append(box)

        return final_filtered

    return filtered


def detect_logos(image_path, model_path, conf_threshold=0.25):
    try:
        model = YOLO(model_path)
        results = model(str(image_path), conf=conf_threshold, verbose=False)

        if not results or len(results) == 0:
            return [], 0

        result = results[0]
        if result.boxes is None or len(result.boxes) == 0:
            return [], 0

        boxes = result.boxes.xyxy.cpu().numpy()
        confidences = result.boxes.conf.cpu().numpy()

        img = cv2.imread(str(image_path))
        img_h, img_w = img.shape[:2] if img is not None else (0, 0)

        logos = []
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

            logos.append({
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "confidence": float(conf)
            })

        return logos, len(logos)
    except Exception as e:
        print(f"Error detecting logos: {e}", file=sys.stderr)
        return [], 0


def overlay_logo_multiple(origin_path, logo_path, boxes, output_path, scale_factor=1.5, min_width=100, min_height=100):
    origin_img = cv2.imread(str(origin_path))
    logo_img = cv2.imread(str(logo_path), cv2.IMREAD_UNCHANGED)

    if origin_img is None:
        raise ValueError(f"Failed to read origin image: {origin_path}")
    if logo_img is None:
        raise ValueError(f"Failed to read logo image: {logo_path}")

    origin_h, origin_w = origin_img.shape[:2]

    for box in boxes:
        box_x = max(0, min(box['x'], origin_w - 1))
        box_y = max(0, min(box['y'], origin_h - 1))
        box_width = max(1, min(box['width'], origin_w - box_x))
        box_height = max(1, min(box['height'], origin_h - box_y))

        box_center_x = box_x + box_width // 2
        box_center_y = box_y + box_height // 2

        padding_x = int(box_width * 0.1)
        padding_y = int(box_height * 0.1)

        expanded_width = box_width + padding_x * 2
        expanded_height = box_height + padding_y * 2

        new_width = int(expanded_width * scale_factor)
        new_height = int(expanded_height * scale_factor)

        new_width = max(new_width, min_width)
        new_height = max(new_height, min_height)

        overlay_x = box_center_x - new_width // 2
        overlay_y = box_center_y - new_height // 2

        if overlay_x < 0:
            overlay_x = 0
        if overlay_y < 0:
            overlay_y = 0
        if overlay_x + new_width > origin_w:
            overlay_x = origin_w - new_width
        if overlay_y + new_height > origin_h:
            overlay_y = origin_h - new_height

        overlay_x = max(0, overlay_x)
        overlay_y = max(0, overlay_y)

        final_width = min(new_width, origin_w - overlay_x)
        final_height = min(new_height, origin_h - overlay_y)

        if final_width <= 0 or final_height <= 0:
            continue

        logo_resized = cv2.resize(logo_img, (final_width, final_height), interpolation=cv2.INTER_LANCZOS4)

        if logo_resized.shape[2] == 4:
            alpha = logo_resized[:, :, 3] / 255.0
            alpha = np.stack([alpha, alpha, alpha], axis=2)
            logo_rgb = logo_resized[:, :, :3]
            roi = origin_img[overlay_y:overlay_y+final_height, overlay_x:overlay_x+final_width]
            blended = (logo_rgb * alpha + roi * (1 - alpha)).astype(np.uint8)
            origin_img[overlay_y:overlay_y+final_height, overlay_x:overlay_x+final_width] = blended
        else:
            origin_img[overlay_y:overlay_y+final_height, overlay_x:overlay_x+final_width] = logo_resized

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), origin_img)

    return str(output_path)


def process_all_images(dataset_path, model_path, logo_path, output_dir, conf_threshold=0.25, scale_factor=1.5, min_width=100, min_height=100):
    dataset_path = Path(dataset_path)
    logo_path = Path(logo_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    results = []

    train_images_dir = dataset_path / "train" / "images"
    valid_images_dir = dataset_path / "valid" / "images"

    all_images = []
    if train_images_dir.exists():
        all_images.extend(train_images_dir.glob("*.png"))
    if valid_images_dir.exists():
        all_images.extend(valid_images_dir.glob("*.png"))

    print(f"=== PROCESSING {len(all_images)} IMAGES ===")
    print(f"Model: {model_path}")
    print(f"Logo: {logo_path}")
    print(f"Output: {output_dir}")
    print()

    for img_path in sorted(all_images):
        try:
            print(f"Processing: {img_path.name}...", end=" ")

            logos, count = detect_logos(img_path, model_path, conf_threshold)

            if count == 0:
                print(f"❌ No logos detected")
                results.append({
                    "image": img_path.name,
                    "status": "no_detection",
                    "output": None,
                    "logos_count": 0
                })
                continue

            filtered_logos = filter_overlapping_boxes(logos, iou_threshold=0.2, distance_threshold=0.8)
            filtered_count = len(filtered_logos)

            if filtered_count != count:
                print(f" (filtered: {count} → {filtered_count})", end="")

            if filtered_count == 0:
                print(f"❌ No logos after filtering")
                results.append({
                    "image": img_path.name,
                    "status": "no_detection",
                    "output": None,
                    "logos_count": 0
                })
                continue

            output_path = output_dir / img_path.name
            overlay_logo_multiple(img_path, logo_path, filtered_logos, output_path, scale_factor, min_width, min_height)

            print(f"✅ Replaced {filtered_count} logo(s) (filtered from {count})")
            results.append({
                "image": img_path.name,
                "status": "success",
                "output": str(output_path),
                "logos_count": filtered_count
            })

        except Exception as e:
            print(f"❌ Error: {e}")
            results.append({
                "image": img_path.name,
                "status": "error",
                "error": str(e),
                "logos_count": 0
            })

    print()
    print("=== SUMMARY ===")
    success = sum(1 for r in results if r.get("status") == "success")
    no_detection = sum(1 for r in results if r.get("status") == "no_detection")
    errors = sum(1 for r in results if r.get("status") == "error")
    total_logos = sum(r.get("logos_count", 0) for r in results)

    print(f"Total images: {len(results)}")
    print(f"Success: {success}")
    print(f"No detection: {no_detection}")
    print(f"Errors: {errors}")
    print(f"Total logos replaced: {total_logos}")
    print(f"Output directory: {output_dir}")

    print(json.dumps({
        "results": results,
        "summary": {
            "total": len(results),
            "success": success,
            "no_detection": no_detection,
            "errors": errors,
            "total_logos_replaced": total_logos,
            "output_dir": str(output_dir)
        }
    }, indent=2))


def main():
    if len(sys.argv) < 5:
        print("Usage: replace_all_logos.py <dataset_path> <model_path> <logo_path> <output_dir> [conf_threshold] [scale_factor] [min_width] [min_height]")
        print("Example: replace_all_logos.py /data/dataset_yolo /data/models/best.pt /data/image_logo.png /data/output 0.25 1.5 100 100")
        sys.exit(1)

    dataset_path = sys.argv[1]
    model_path = sys.argv[2]
    logo_path = sys.argv[3]
    output_dir = sys.argv[4]
    conf_threshold = float(sys.argv[5]) if len(sys.argv) > 5 else 0.25
    scale_factor = float(sys.argv[6]) if len(sys.argv) > 6 else 1.5
    min_width = int(sys.argv[7]) if len(sys.argv) > 7 else 100
    min_height = int(sys.argv[8]) if len(sys.argv) > 8 else 100

    process_all_images(dataset_path, model_path, logo_path, output_dir, conf_threshold, scale_factor, min_width, min_height)


if __name__ == "__main__":
    main()
