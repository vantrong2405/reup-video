#!/usr/bin/env python3

import sys
import json
import cv2
import numpy as np
from pathlib import Path


def nms(boxes, scores, iou_threshold=0.3):
    if len(boxes) == 0:
        return []

    boxes = np.array(boxes)
    scores = np.array(scores)

    x1 = boxes[:, 0]
    y1 = boxes[:, 1]
    x2 = boxes[:, 0] + boxes[:, 2]
    y2 = boxes[:, 1] + boxes[:, 3]

    areas = boxes[:, 2] * boxes[:, 3]
    order = scores.argsort()[::-1]

    keep = []
    while len(order) > 0:
        i = order[0]
        keep.append(i)

        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        w = np.maximum(0, xx2 - xx1)
        h = np.maximum(0, yy2 - yy1)
        inter = w * h

        iou = inter / (areas[i] + areas[order[1:]] - inter)

        inds = np.where(iou <= iou_threshold)[0]
        order = order[inds + 1]

    return keep


def detect_logo_full_image(origin_img, sample_img):
    origin_gray = cv2.cvtColor(origin_img, cv2.COLOR_BGR2GRAY)
    sample_gray = cv2.cvtColor(sample_img, cv2.COLOR_BGR2GRAY)
    template_h, template_w = sample_gray.shape
    origin_h, origin_w = origin_gray.shape

    if template_h > origin_h or template_w > origin_w:
        return []

    scales = np.arange(0.6, 1.41, 0.05)
    method = cv2.TM_CCOEFF_NORMED
    all_matches = []

    for scale in scales:
        scaled_w = int(template_w * scale)
        scaled_h = int(template_h * scale)

        if scaled_w < 10 or scaled_h < 10 or scaled_w > origin_w or scaled_h > origin_h:
            continue

        if abs(scale - 1.0) > 0.01:
            scaled_template = cv2.resize(sample_gray, (scaled_w, scaled_h), interpolation=cv2.INTER_AREA)
        else:
            scaled_template = sample_gray

        result = cv2.matchTemplate(origin_gray, scaled_template, method)

        threshold = 0.5
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

        if max_val < threshold:
            continue

        locations = np.where(result >= threshold)

        for pt in zip(*locations[::-1]):
            x, y = pt
            score = float(result[y, x])

            if score < threshold:
                continue

            all_matches.append({
                'score': score,
                'x': x,
                'y': y,
                'width': scaled_w,
                'height': scaled_h,
                'scale': scale
            })

    if not all_matches:
        return []

    all_matches.sort(key=lambda m: -m['score'])

    boxes = [[m['x'], m['y'], m['width'], m['height']] for m in all_matches]
    scores = [m['score'] for m in all_matches]

    keep_indices = nms(boxes, scores, iou_threshold=0.2)

    results = []
    template_h, template_w = sample_gray.shape
    min_logo_size = min(template_w, template_h) * 0.5
    max_logo_size = max(template_w, template_h) * 2.0

    for idx in keep_indices:
        match = all_matches[idx]
        if match['score'] < 0.5:
            continue

        logo_size = max(match['width'], match['height'])
        if logo_size < min_logo_size or logo_size > max_logo_size:
            continue

        aspect_ratio = match['width'] / max(match['height'], 1)
        if aspect_ratio < 0.5 or aspect_ratio > 5.0:
            continue

        padding_w = int(match['width'] * 0.1)
        padding_h = int(match['height'] * 0.25)
        x = max(0, match['x'] - padding_w // 2)
        y = max(0, match['y'] - padding_h // 2)
        width = min(origin_w - x, match['width'] + padding_w)
        height = min(origin_h - y, match['height'] + padding_h)

        distance_from_top_right = ((origin_w - x) ** 2 + y ** 2) ** 0.5
        results.append({
            "x": int(x),
            "y": int(y),
            "width": int(width),
            "height": int(height),
            "score": match['score']
        })

    results.sort(key=lambda r: -r['score'])

    seen = set()
    final_results = []

    for r in results:
        if r['score'] >= 0.4:
            key = (r['x'], r['y'], r['width'], r['height'])
            if key not in seen:
                seen.add(key)
                final_results.append({"x": r['x'], "y": r['y'], "width": r['width'], "height": r['height']})

    return final_results


def detect_logo_multi_roi(origin_img, sample_img):
    origin_gray = cv2.cvtColor(origin_img, cv2.COLOR_BGR2GRAY)
    sample_gray = cv2.cvtColor(sample_img, cv2.COLOR_BGR2GRAY)
    template_h, template_w = sample_gray.shape
    origin_h, origin_w = origin_gray.shape

    if template_h > origin_h or template_w > origin_w:
        return []

    rois = [
        {"name": "top_left", "x": 0, "y": 0, "w": origin_w // 2, "h": origin_h // 2},
        {"name": "top_right", "x": origin_w // 2, "y": 0, "w": origin_w // 2, "h": origin_h // 2},
        {"name": "bottom_left", "x": 0, "y": origin_h // 2, "w": origin_w // 2, "h": origin_h // 2},
        {"name": "bottom_right", "x": origin_w // 2, "y": origin_h // 2, "w": origin_w // 2, "h": origin_h // 2}
    ]

    scales = np.arange(0.6, 1.41, 0.05)
    method = cv2.TM_CCOEFF_NORMED
    all_matches = []

    for roi in rois:
        roi_img = origin_gray[roi["y"]:roi["y"]+roi["h"], roi["x"]:roi["x"]+roi["w"]]

        if roi_img.shape[0] < template_h or roi_img.shape[1] < template_w:
            continue

        for scale in scales:
            scaled_w = int(template_w * scale)
            scaled_h = int(template_h * scale)

            if scaled_w < 10 or scaled_h < 10 or scaled_w > roi["w"] or scaled_h > roi["h"]:
                continue

            if abs(scale - 1.0) > 0.01:
                scaled_template = cv2.resize(sample_gray, (scaled_w, scaled_h), interpolation=cv2.INTER_AREA)
            else:
                scaled_template = sample_gray

            result = cv2.matchTemplate(roi_img, scaled_template, method)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            if max_val < 0.5:
                continue

            x = max_loc[0] + roi["x"]
            y = max_loc[1] + roi["y"]
            all_matches.append({
                'score': max_val,
                'x': x,
                'y': y,
                'width': scaled_w,
                'height': scaled_h,
                'scale': scale,
                'roi': roi["name"]
            })

    if not all_matches:
        return []

    all_matches.sort(key=lambda m: -m['score'])

    boxes = [[m['x'], m['y'], m['width'], m['height']] for m in all_matches]
    scores = [m['score'] for m in all_matches]

    keep_indices = nms(boxes, scores, iou_threshold=0.2)

    results = []
    template_h, template_w = sample_gray.shape
    min_logo_size = min(template_w, template_h) * 0.5
    max_logo_size = max(template_w, template_h) * 2.0

    for idx in keep_indices:
        match = all_matches[idx]
        if match['score'] < 0.5:
            continue

        logo_size = max(match['width'], match['height'])
        if logo_size < min_logo_size or logo_size > max_logo_size:
            continue

        aspect_ratio = match['width'] / max(match['height'], 1)
        if aspect_ratio < 0.5 or aspect_ratio > 5.0:
            continue

        padding_w = int(match['width'] * 0.1)
        padding_h = int(match['height'] * 0.25)
        x = max(0, match['x'] - padding_w // 2)
        y = max(0, match['y'] - padding_h // 2)
        width = min(origin_w - x, match['width'] + padding_w)
        height = min(origin_h - y, match['height'] + padding_h)

        results.append({
            "x": int(x),
            "y": int(y),
            "width": int(width),
            "height": int(height),
            "score": match['score']
        })

    results.sort(key=lambda r: -r['score'])

    seen = set()
    final_results = []

    for r in results:
        if r['score'] >= 0.4:
            key = (r['x'], r['y'], r['width'], r['height'])
            if key not in seen:
                seen.add(key)
                final_results.append({"x": r['x'], "y": r['y'], "width": r['width'], "height": r['height']})

    return final_results


def main():
    if len(sys.argv) < 2:
        print(json.dumps([]), file=sys.stderr)
        sys.exit(1)

    origin_path = Path(sys.argv[1])
    sample_path = Path(sys.argv[2]) if len(sys.argv) > 2 else None
    debug_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None

    if not origin_path.exists():
        print(json.dumps([]), file=sys.stderr)
        sys.exit(1)

    origin_img = cv2.imread(str(origin_path))
    if origin_img is None:
        print(json.dumps([]), file=sys.stderr)
        sys.exit(1)

    results = []

    if sample_path and sample_path.exists():
        sample_img = cv2.imread(str(sample_path))
        if sample_img is None:
            print(json.dumps([]), file=sys.stderr)
            sys.exit(1)

        results = detect_logo_full_image(origin_img, sample_img)

        if not results:
            results = detect_logo_multi_roi(origin_img, sample_img)

    if debug_path and results:
        debug_img = origin_img.copy()
        for i, result in enumerate(results):
            x, y, w, h = result['x'], result['y'], result['width'], result['height']
            color = (0, 255, 0) if i == 0 else (255, 0, 0)
            cv2.rectangle(debug_img, (x, y), (x + w, y + h), color, 3)
            cv2.putText(debug_img, f"#{i+1} x={x},y={y} {w}x{h}", (x, max(20, y-10)), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        debug_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(debug_path), debug_img)

    print(json.dumps(results))


if __name__ == "__main__":
    main()
