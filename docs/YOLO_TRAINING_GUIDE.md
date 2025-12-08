# YOLO Logo Detection - Quick Guide

## Tổng quan

Project đã setup hoàn chỉnh:
- Docker container với ultralytics, YOLO, OpenCV
- Model đã train: `best.pt`
- Script chính: `logo_detect_overlay.py` (gộp detect + overlay)
- Test scripts: `test_scripts/` folder
- Dataset: `dataset_yolo/` với train/valid split

## Cấu trúc Project

```
n8n-install/
├── Dockerfile                    # Docker image với YOLO dependencies
├── docker-compose.yml            # Docker compose config
├── models/
│   └── best.pt                  # YOLO model đã train
├── dataset_yolo/
│   ├── train/
│   │   ├── images/              # Training images
│   │   └── labels/              # Training labels
│   ├── valid/
│   │   ├── images/              # Validation images
│   │   └── labels/              # Validation labels
│   └── data.yaml                # Dataset config
├── scripts/
│   └── logo_detect_overlay.py   # Script chính: detect + overlay
├── test_scripts/
│   ├── replace_all_logos.py     # Batch process tất cả ảnh
│   ├── test_yolo.py             # Test model
│   └── train_yolo.sh            # Training script
├── image_logo.png               # Logo mới để overlay
└── output/                      # Output images sau khi xử lý
```

## Script Chính: logo_detect_overlay.py

Script gộp detect và overlay thành 1 file, có 3 modes:

### Mode 1: detect
Chỉ detect logo, trả về JSON với bounding boxes.

**Usage:**
```bash
python3 /data/scripts/logo_detect_overlay.py detect <image_path> [model_path] [conf_threshold]
```

**Example:**
```bash
python3 /data/scripts/logo_detect_overlay.py detect \
    /data/dataset_yolo/valid/images/test.png \
    /data/models/best.pt \
    0.25
```

**Output:**
```json
{"logos": [{"x": 1083, "y": 11, "width": 242, "height": 54, "confidence": 0.98}], "count": 1}
```

### Mode 2: overlay
Chỉ overlay logo mới lên ảnh (đã có bbox).

**Usage:**
```bash
python3 /data/scripts/logo_detect_overlay.py overlay <origin> <logo> <x> <y> <width> <height> <output>
```

**Example:**
```bash
python3 /data/scripts/logo_detect_overlay.py overlay \
    /data/dataset_yolo/valid/images/test.png \
    /data/image_logo.png \
    1083 11 242 54 \
    /data/output/result.jpg
```

**Output:**
```json
{"output": "/data/output/result.jpg"}
```

### Mode 3: process
Detect + Overlay trong 1 lệnh (tiện nhất).

**Usage:**
```bash
python3 /data/scripts/logo_detect_overlay.py process <origin> <logo> <model_path> [conf_threshold] <output>
```

**Example:**
```bash
python3 /data/scripts/logo_detect_overlay.py process \
    /data/dataset_yolo/valid/images/test.png \
    /data/image_logo.png \
    /data/models/best.pt \
    0.25 \
    /data/output/result.jpg
```

**Output:**
```json
{"output": "/data/output/result.jpg", "detected": 1}
```

## Test Scripts

### replace_all_logos.py
Batch process tất cả ảnh trong dataset: detect và replace logo.

**Usage:**
```bash
python3 /data/test_scripts/replace_all_logos.py \
    <dataset_path> \
    <model_path> \
    <logo_path> \
    <output_dir> \
    [conf_threshold] \
    [scale_factor] \
    [min_width] \
    [min_height]
```

**Example:**
```bash
python3 /data/test_scripts/replace_all_logos.py \
    /data/dataset_yolo \
    /data/models/best.pt \
    /data/image_logo.png \
    /data/output \
    0.25 \
    1.0 \
    100 \
    100
```

**Output:** JSON với results và summary.

### test_yolo.py
Test model trên ảnh hoặc toàn bộ dataset.

**Test single image:**
```bash
python3 /data/test_scripts/test_yolo.py <image_path> <model_path> [conf_threshold] [output_path]
```

**Test all images:**
```bash
python3 /data/test_scripts/test_yolo.py --all <model_path> <dataset_path> [conf_threshold]
```

**Example:**
```bash
python3 /data/test_scripts/test_yolo.py \
    /data/dataset_yolo/valid/images/test.png \
    /data/models/best.pt \
    0.25 \
    /tmp/test_result.jpg
```

## Lệnh Test

### Test trong Docker Container

**1. Vào container:**
```bash
sudo docker compose exec n8n bash
```

**2. Test detect:**
```bash
python3 /data/scripts/logo_detect_overlay.py detect \
    /data/dataset_yolo/valid/images/test.png \
    /data/models/best.pt \
    0.25
```

**3. Test overlay:**
```bash
python3 /data/scripts/logo_detect_overlay.py overlay \
    /data/dataset_yolo/valid/images/test.png \
    /data/image_logo.png \
    1083 11 242 54 \
    /tmp/test_overlay.jpg
```

**4. Test process (detect + overlay):**
```bash
python3 /data/scripts/logo_detect_overlay.py process \
    /data/dataset_yolo/valid/images/test.png \
    /data/image_logo.png \
    /data/models/best.pt \
    0.25 \
    /tmp/test_result.jpg
```

**5. Test batch processing:**
```bash
python3 /data/test_scripts/replace_all_logos.py \
    /data/dataset_yolo \
    /data/models/best.pt \
    /data/image_logo.png \
    /data/output \
    0.25 \
    1.0 \
    100 \
    100
```

**6. Test model trên tất cả ảnh:**
```bash
python3 /data/test_scripts/test_yolo.py --all \
    /data/models/best.pt \
    /data/dataset_yolo \
    0.25
```

### Test từ Host

**1. Test detect:**
```bash
sudo docker compose exec n8n python3 /data/scripts/logo_detect_overlay.py detect \
    /data/dataset_yolo/valid/images/test.png \
    /data/models/best.pt \
    0.25
```

**2. Test process:**
```bash
sudo docker compose exec n8n python3 /data/scripts/logo_detect_overlay.py process \
    /data/dataset_yolo/valid/images/test.png \
    /data/image_logo.png \
    /data/models/best.pt \
    0.25 \
    /data/output/result.jpg
```

**3. Test batch processing:**
```bash
sudo docker compose exec n8n python3 /data/test_scripts/replace_all_logos.py \
    /data/dataset_yolo \
    /data/models/best.pt \
    /data/image_logo.png \
    /data/output \
    0.25 \
    1.0 \
    100 \
    100
```

## Training Model

### Train mới

**Trong Docker container:**
```bash
cd /home/node
yolo detect train \
    data=/data/dataset_yolo/data.yaml \
    model=yolov8s.pt \
    epochs=50 \
    imgsz=640 \
    batch=16
```

**Copy model sau khi train:**
```bash
cp /home/node/runs/detect/train*/weights/best.pt /data/models/best.pt
```

**Từ host:**
```bash
sudo docker compose exec n8n bash -c "cd /home/node && yolo detect train data=/data/dataset_yolo/data.yaml model=yolov8s.pt epochs=50 imgsz=640 batch=16"
```

### Resume training

```bash
yolo detect train \
    data=/data/dataset_yolo/data.yaml \
    model=/data/models/best.pt \
    epochs=100 \
    imgsz=640 \
    batch=16
```

## Dataset

### Cấu trúc dataset_yolo

```
dataset_yolo/
├── train/
│   ├── images/          # Training images
│   └── labels/          # Training labels (.txt)
├── valid/
│   ├── images/          # Validation images
│   └── labels/          # Validation labels (.txt)
└── data.yaml            # Dataset config
```

### File data.yaml

```yaml
path: /data/dataset_yolo
train: train/images
val: valid/images

nc: 1
names:
  0: logo
```

**Lưu ý:** Phải dùng `val:` không phải `valid:`.

## N8N Workflow Integration

### Cách 1: Dùng 2 nodes (detect riêng, overlay riêng)

**Node 1: Detect Logo**
- Command: `python3`
- Arguments:
  ```
  /data/scripts/logo_detect_overlay.py
  detect
  /data/input/image.jpg
  /data/models/best.pt
  0.25
  ```
- Working Directory: `/data`

**Node 2: Parse JSON**
- Code Node (JavaScript):
```javascript
const output = $input.item.json.stdout.trim();
const result = JSON.parse(output);
return result.logos[0] || {x: 0, y: 0, width: 0, height: 0};
```

**Node 3: Overlay Logo**
- Command: `python3`
- Arguments:
  ```
  /data/scripts/logo_detect_overlay.py
  overlay
  /data/input/image.jpg
  /data/image_logo.png
  {{ $json.x }}
  {{ $json.y }}
  {{ $json.width }}
  {{ $json.height }}
  /data/output/result.jpg
  ```
- Working Directory: `/data`

### Cách 2: Dùng 1 node (process mode - tiện nhất)

**Node 1: Detect + Overlay**
- Command: `python3`
- Arguments:
  ```
  /data/scripts/logo_detect_overlay.py
  process
  /data/input/image.jpg
  /data/image_logo.png
  /data/models/best.pt
  0.25
  /data/output/result.jpg
  ```
- Working Directory: `/data`

**Node 2: Parse Output**
- Code Node (JavaScript):
```javascript
const output = $input.item.json.stdout.trim();
const result = JSON.parse(output);
return {output_path: result.output, detected: result.detected};
```

## Troubleshooting

### Model không detect được logo

**Giảm confidence threshold:**
```bash
python3 /data/scripts/logo_detect_overlay.py detect image.jpg /data/models/best.pt 0.15
```

### Model detect quá nhiều false positive

**Tăng confidence threshold:**
```bash
python3 /data/scripts/logo_detect_overlay.py detect image.jpg /data/models/best.pt 0.4
```

### Model not found

**Kiểm tra file:**
```bash
sudo docker compose exec n8n ls -lh /data/models/best.pt
```

**Restart container:**
```bash
sudo docker compose restart n8n
```

### Update logo mới

**Copy logo vào project:**
```bash
cp new_logo.png ./image_logo.png
```

**Restart containers:**
```bash
sudo docker compose restart n8n worker
```

## Quick Reference

**Test detect:**
```bash
sudo docker compose exec n8n python3 /data/scripts/logo_detect_overlay.py detect \
    /data/dataset_yolo/valid/images/test.png \
    /data/models/best.pt \
    0.25
```

**Test process (detect + overlay):**
```bash
sudo docker compose exec n8n python3 /data/scripts/logo_detect_overlay.py process \
    /data/dataset_yolo/valid/images/test.png \
    /data/image_logo.png \
    /data/models/best.pt \
    0.25 \
    /data/output/result.jpg
```

**Batch process:**
```bash
sudo docker compose exec n8n python3 /data/test_scripts/replace_all_logos.py \
    /data/dataset_yolo \
    /data/models/best.pt \
    /data/image_logo.png \
    /data/output \
    0.25 1.0 100 100
```

**Test model:**
```bash
sudo docker compose exec n8n python3 /data/test_scripts/test_yolo.py --all \
    /data/models/best.pt \
    /data/dataset_yolo \
    0.25
```

**Train model:**
```bash
sudo docker compose exec n8n bash -c "cd /home/node && yolo detect train data=/data/dataset_yolo/data.yaml model=yolov8s.pt epochs=50 imgsz=640 batch=16"
```
