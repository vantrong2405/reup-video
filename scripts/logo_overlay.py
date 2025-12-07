#!/usr/bin/env python3

import sys
import json
import cv2
import numpy as np
from pathlib import Path


def overlay_logo(origin_path, logo_path, boxes, output_path, debug_path=None):
    origin_img = cv2.imread(str(origin_path))
    logo_img = cv2.imread(str(logo_path), cv2.IMREAD_UNCHANGED)

    if origin_img is None:
        raise ValueError(f"Failed to read origin image: {origin_path}")
    if logo_img is None:
        raise ValueError(f"Failed to read logo image: {logo_path}")

    origin_h, origin_w = origin_img.shape[:2]

    if debug_path:
        debug_img = origin_img.copy()
        for i, box in enumerate(boxes):
            x, y, w, h = box['x'], box['y'], box['width'], box['height']
            color = (255, 0, 0) if i == 0 else (0, 0, 255)
            cv2.rectangle(debug_img, (x, y), (x + w, y + h), color, 2)
            cv2.putText(debug_img, f"#{i+1} {x},{y} {w}x{h}", (x, max(20, y-10)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        debug_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(debug_path), debug_img)

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

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), origin_img)
    return output_path


def main():
    if len(sys.argv) < 4:
        print(f"Usage: {sys.argv[0]} <origin_image> <new_logo> <boxes_json> <output_image> [debug_image]", file=sys.stderr)
        sys.exit(1)

    origin_path = Path(sys.argv[1])
    logo_path = Path(sys.argv[2])
    boxes_json = sys.argv[3]
    output_path = Path(sys.argv[4])
    debug_path = Path(sys.argv[5]) if len(sys.argv) > 5 else None

    if not output_path.is_absolute():
        output_path = Path("output") / output_path.name

    try:
        boxes = json.loads(boxes_json)
        if not isinstance(boxes, list):
            boxes = [boxes]
        overlay_logo(origin_path, logo_path, boxes, output_path, debug_path)
        print(str(output_path))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
