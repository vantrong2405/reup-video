#!/usr/bin/env python3

import sys
import json
import cv2
import numpy as np
from pathlib import Path


def overlay_logo(origin_path, logo_path, x, y, width, height, output_path):
    origin_img = cv2.imread(str(origin_path))
    logo_img = cv2.imread(str(logo_path), cv2.IMREAD_UNCHANGED)

    if origin_img is None:
        print(json.dumps({"output": "", "error": f"Failed to read origin image: {origin_path}"}), file=sys.stderr)
        sys.exit(1)
    
    if logo_img is None:
        print(json.dumps({"output": "", "error": f"Failed to read logo image: {logo_path}"}), file=sys.stderr)
        sys.exit(1)

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

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), origin_img)
    
    print(json.dumps({"output": str(output_path)}))


def main():
    if len(sys.argv) < 8:
        print(json.dumps({"output": "", "error": f"Usage: {sys.argv[0]} <origin_image> <new_logo> <x> <y> <width> <height> <output_image>"}), file=sys.stderr)
        sys.exit(1)

    origin_path = Path(sys.argv[1])
    logo_path = Path(sys.argv[2])
    x, y = int(sys.argv[3]), int(sys.argv[4])
    width, height = int(sys.argv[5]), int(sys.argv[6])
    output_path = Path(sys.argv[7])

    try:
        overlay_logo(origin_path, logo_path, x, y, width, height, output_path)
    except Exception as e:
        print(json.dumps({"output": "", "error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

