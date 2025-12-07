# Hướng dẫn Setup YOLO Logo Detection

## I. Build Docker Image

### Bước 1: Build Image

```bash
docker-compose build
```

**Lưu ý:** Build lần đầu sẽ mất 10-20 phút vì phải download và compile torch (~2GB).

### Bước 2: Kiểm tra Image đã build

```bash
docker images | grep n8n_custom
```

---

## II. Chuẩn bị Model YOLO

### Bước 1: Train Model trên Roboflow

1. Upload ảnh có logo lên Roboflow
2. Annotate (vẽ bounding box) cho tất cả logo
3. Export dataset YOLOv8 format
4. Train model:

```bash
yolo detect train \
    data=/path/to/dataset/data.yaml \
    model=yolov8s.pt \
    epochs=50 \
    imgsz=640
```

### Bước 2: Copy Model vào Project

```bash
# Copy best.pt vào thư mục models
cp runs/detect/logo_detection/weights/best.pt ./models/best.pt
```

**Hoặc** nếu model ở nơi khác:

```bash
cp /path/to/best.pt ./models/best.pt
```

### Bước 3: Kiểm tra Model

```bash
ls -lh models/best.pt
```

---

## III. Test Scripts (Trong Container)

### Bước 1: Start Container

```bash
docker-compose up -d
```

### Bước 2: Test Detect Script

```bash
# Copy ảnh test vào input
cp /path/to/test_image.jpg ./input/

# Test detect
docker-compose exec n8n python3 /data/scripts/detect_yolo.py \
    /data/input/test_image.jpg \
    /data/models/best.pt \
    0.25
```

**Output mong đợi:**
```json
{"x":340,"y":120,"width":90,"height":40}
```

### Bước 3: Test Overlay Script

```bash
# Copy logo mới vào input
cp /path/to/new_logo.png ./input/

# Test overlay (dùng kết quả từ detect)
docker-compose exec n8n python3 /data/scripts/overlay_logo.py \
    /data/input/test_image.jpg \
    /data/input/new_logo.png \
    340 120 90 40 \
    /data/output/result.jpg
```

**Output mong đợi:**
```json
{"output":"/data/output/result.jpg"}
```

### Bước 4: Kiểm tra Output

```bash
ls -lh output/result.jpg
```

---

## IV. Setup N8N Workflow

### Node 1: Load Image

**HTTP Request Node** hoặc **Read Binary File Node**:
- Save image vào `/data/input/image.jpg`

### Node 2: Detect Logo (YOLO)

**Execute Command Node**:
- Command: `python3`
- Arguments:
  ```
  /data/scripts/detect_yolo.py
  /data/input/image.jpg
  /data/models/best.pt
  0.25
  ```
- Working Directory: `/data`

**Parse Output (Code Node)**:
```javascript
const output = $input.item.json.stdout;
const bbox = JSON.parse(output);
return {
  x: bbox.x,
  y: bbox.y,
  width: bbox.width,
  height: bbox.height
};
```

### Node 3: Overlay Logo

**Execute Command Node**:
- Command: `python3`
- Arguments:
  ```
  /data/scripts/overlay_logo.py
  /data/input/image.jpg
  /data/input/new_logo.png
  {{ $json.x }}
  {{ $json.y }}
  {{ $json.width }}
  {{ $json.height }}
  /data/output/result.jpg
  ```
- Working Directory: `/data`

**Parse Output (Code Node)**:
```javascript
const output = $input.item.json.stdout;
const result = JSON.parse(output);
return {
  output_path: result.output
};
```

### Node 4: Return/Upload Result

**HTTP Response Node** hoặc **Upload Node**:
- Read file từ `/data/output/result.jpg`

---

## V. Cấu trúc Thư mục

```
n8n-install/
├── Dockerfile
├── docker-compose.yml
├── models/
│   └── best.pt          # YOLO model (cần copy vào)
├── input/
│   └── (ảnh input sẽ được lưu ở đây)
├── output/
│   └── (ảnh output sẽ được lưu ở đây)
├── scripts/
│   ├── detect_yolo.py
│   └── overlay_logo.py
└── SETUP_YOLO.md
```

---

## VI. Troubleshooting

### Lỗi: Model not found
```bash
# Kiểm tra model có trong container không
docker-compose exec n8n ls -lh /data/models/best.pt

# Nếu không có, kiểm tra volume mount
docker-compose exec n8n ls -lh /data/models/
```

### Lỗi: No detections
- Giảm confidence threshold: `0.25` → `0.15`
- Kiểm tra model đã train đúng chưa
- Kiểm tra ảnh input có logo không

### Lỗi: Import ultralytics failed
```bash
# Rebuild image
docker-compose build --no-cache
docker-compose up -d
```

### Lỗi: Script not found
```bash
# Kiểm tra scripts có trong container không
docker-compose exec n8n ls -lh /data/scripts/

# Nếu không có, kiểm tra volume mount
docker-compose exec n8n ls -lh /data/scripts/
```

---

## VII. Quick Start

1. **Build Docker:**
   ```bash
   docker-compose build
   ```

2. **Copy Model:**
   ```bash
   cp /path/to/best.pt ./models/best.pt
   ```

3. **Start Services:**
   ```bash
   docker-compose up -d
   ```

4. **Test Scripts:**
   ```bash
   # Test detect
   docker-compose exec n8n python3 /data/scripts/detect_yolo.py \
       /data/input/test.jpg /data/models/best.pt 0.25

   # Test overlay
   docker-compose exec n8n python3 /data/scripts/overlay_logo.py \
       /data/input/test.jpg /data/input/logo.png 100 100 200 100 /data/output/result.jpg
   ```

5. **Setup N8N Workflow** theo hướng dẫn trên

---

**Lưu ý:** Tất cả scripts output JSON một dòng duy nhất để n8n dễ parse.
