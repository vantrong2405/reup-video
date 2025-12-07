# QUICK START - TRAIN YOLO MODEL DETECT LOGO

## Tóm Tắt Nhanh

File hướng dẫn chi tiết: [YOLO_TRAINING_GUIDE.md](./YOLO_TRAINING_GUIDE.md)

## Quy Trình 5 Bước

### 1. Chuẩn Bị Dataset (Roboflow)

1. Tạo tài khoản: https://roboflow.com
2. Tạo project mới: **Object Detection**
3. Upload ảnh có logo (50-500 ảnh)
4. Annotate: Vẽ bounding box, label **"logo"**
5. Generate dataset với augmentation (2x-3x)
6. Export: **YOLOv8 Ultralytics format**
7. Download và giải nén: `unzip logo-detection-1.zip -d dataset_yolo`

### 2. Validate Dataset

```bash
python3 scripts/validate_dataset.py dataset_yolo
```

### 3. Train Model

**Cách 1: Dùng script (khuyến nghị)**
```bash
./scripts/train_yolo.sh dataset_yolo yolov8s.pt 50 640 16
```

**Cách 2: Lệnh trực tiếp**
```bash
yolo detect train \
    data=dataset_yolo/data.yaml \
    model=yolov8s.pt \
    epochs=50 \
    imgsz=640 \
    batch=16
```

**Với GPU:**
```bash
./scripts/train_yolo.sh dataset_yolo yolov8s.pt 50 640 16 0
```

### 4. Copy Model Vào N8N

```bash
cp runs/detect/train/weights/best.pt ./models/best.pt
```

### 5. Test Model

```bash
# Test local
python3 scripts/test_yolo_model.py dataset_yolo/valid/images/frame_050.jpg ./models/best.pt 0.25

# Test trong Docker
docker exec -it n8n_main python3 /data/scripts/detect_yolo.py \
    /data/input/test.jpg \
    /data/models/best.pt \
    0.25
```

## N8N Workflow

### Node 1: Load Image
- HTTP Request hoặc Read Binary File
- Save to: `/data/input/image.jpg`

### Node 2: Detect Logo
**Execute Command:**
```bash
python3 /data/scripts/detect_yolo.py /data/input/image.jpg /data/models/best.pt 0.25
```

**Code Node (Parse JSON):**
```javascript
const output = $input.item.json.stdout.trim();
return JSON.parse(output);
```

### Node 3: Overlay Logo
**Execute Command:**
```bash
python3 /data/scripts/overlay_logo.py /data/input/image.jpg /data/input/new_logo.png {{ $json.x }} {{ $json.y }} {{ $json.width }} {{ $json.height }} /data/output/result.jpg
```

## Troubleshooting

- **Model không detect:** Giảm confidence (0.15) hoặc thêm ảnh training
- **Detect sai:** Tăng confidence (0.4) hoặc kiểm tra annotation
- **Lỗi "Model not found":** Kiểm tra `./models/best.pt` và docker-compose mount

## Tham Khảo

- [YOLO_TRAINING_GUIDE.md](./YOLO_TRAINING_GUIDE.md) - Hướng dẫn chi tiết đầy đủ
- [SETUP_YOLO.md](./SETUP_YOLO.md) - Setup ban đầu
