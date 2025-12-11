# Logo Editing Rules & Flow

Based on the analysis of `workflow.json`, `src/controller/logo_controller.py`, and `src/service/logo_service.py`, here is the documented flow and rules for logo editing.

## 1. High-Level Flow (N8N Workflow)

The logo processing happens in the "Process Video" branch of the N8N workflow:

1.  **Extract Frame**: `ffmpeg` extracts the first frame of the video.
2.  **Detect Logo**: `logo_controller.py` (YOLOv8) analyzes the frame to find existing logos.
3.  **Process Video** (`ffmpeg` script):
    *   **Case A: Logo Detected**
        *   Calculate coordinates: `X`, `Y`, `WIDTH`, `HEIGHT`.
        *   **Rule**: Expand the box by `EXPAND=15` pixels on all sides for removal.
        *   **Action**: Apply `delogo` filter (blur) to the expanded area.
        *   **Action**: Draw a black box with 0.98 opacity (`drawbox`) over the exact detected area.
        *   **Action**: Overlay the new logo on top, scaled to fit the original logo's dimensions (with specific aspect ratio scaling).
    *   **Case B: No Logo Detected**
        *   **Rule**: Use default dimensions `220x110`.
        *   **Rule**: Position at Top-Right with padding `10px` (`W-w-10:10`).
        *   **Action**: Overlay the new logo.

## 2. Python Implementation (`logo_service.py`)

The Python service provides the underlying logic for detection and image manipulation (used by the workflow and test scripts).

*   **Detection**:
    *   Uses YOLO model (`best.pt`) with a confidence threshold (default 0.25).
    *   Returns list of bounding boxes `{x, y, width, height, confidence}`.

*   **Overlay Logic (`process_logo` / `overlay_logo`)**:
    *   **Blurring**: Applies `cv2.GaussianBlur` to the region defined by the bounding box (plus `MARGIN`).
    *   **Resizing**: Resizes the new logo to fit the target box using `cv2.INTER_LANCZOS4`. It attempts to fit inside while preserving aspect ratio logic.
    *   **Blending**: If the logo has an alpha channel, it performs alpha blending with the background. Otherwise, it simply copies the pixels.
    *   **Overrides**: Supports global `SCALE_W`, `SCALE_H`, `MARGIN`, `OFFSET_Y` to adjust the placement/sizing.

## 3. Key Rules Summary

| Feature | Rule | Source |
| :--- | :--- | :--- |
| **Detection Threshold** | Default `0.25` | `logo_controller.py` / `workflow.json` |
| **Removal Method** | `delogo` (blur) + `drawbox` (black fill) | `workflow.json` (ffmpeg) |
| **Removal Margin** | `15px` expansion for delogo | `workflow.json` |
| **Replacement Sizing** | Scaled to match original (Case A) or 220x110 (Case B) | `workflow.json` |
| **Process Fallback** | Top-Right overlay if detection fails | `workflow.json` |
