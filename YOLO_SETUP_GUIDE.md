# Hướng dẫn Setup YOLO Logo Detection System

## I. Tổng quan Flow

```
Input Image → YOLO Detect → Bounding Box → Overlay Logo → Output Image
```

1. **Detect**: `detect_yolo.py` nhận ảnh → YOLO detect → trả JSON `{x, y, width, height}`
2. **Overlay**: `overlay_logo.py` nhận bounding box → overlay logo mới → trả JSON `{output: path}`

---

## II. Tạo Dataset bằng Roboflow

### Bước 1: Tạo Project trên Roboflow

1. Truy cập: https://roboflow.com
2. Đăng ký/Đăng nhập (miễn phí)
3. Click **"Create New Project"**
4. Đặt tên: `logo-detection`
5. Chọn **"Object Detection"**
6. Chọn **"YOLOv8"** format

### Bước 2: Upload Ảnh

1. Click **"Upload"** hoặc kéo thả ảnh
2. Upload tất cả ảnh có logo cần detect
3. Khuyến nghị: **ít nhất 50-100 ảnh** để train tốt

### Bước 3: Annotate (Vẽ Bounding Box)

1. Click vào từng ảnh
2. Dùng chuột **vẽ box** quanh logo
3. Đặt tên class: `logo` (hoặc tên bạn muốn)
4. Lặp lại cho tất cả ảnh

**Lưu ý:**
- Vẽ box chính xác, không quá rộng hoặc quá hẹp
- Nếu có nhiều logo trong 1 ảnh, vẽ tất cả
- Nếu logo bị che khuất, chỉ vẽ phần nhìn thấy

### Bước 4: Export Dataset

1. Click **"Generate"** → **"Export Dataset"**
2. Chọn **"YOLOv8"** format
3. Chọn **"Download ZIP"**
4. Giải nén file ZIP

**Cấu trúc dataset sau khi giải nén:**
```
dataset/
├── train/
│   ├── images/
│   └── labels/
├── valid/
│   ├── images/
│   └── labels/
├── test/
│   ├── images/
│   └── labels/
└── data.yaml
```

### Bước 5: Kiểm tra data.yaml

File `data.yaml` mẫu:
```yaml
path: /path/to/dataset
train: train/images
val: valid/images
test: test/images

nc: 1
names:
  0: logo
```

---

## III. Train YOLO Model

### Bước 1: Cài đặt Ultralytics

```bash
pip install ultralytics
```

### Bước 2: Chuẩn bị Dataset

1. Copy dataset vào thư mục project
2. Đảm bảo `data.yaml` đúng đường dẫn

### Bước 3: Train Model

```bash
yolo detect train \
    data=/path/to/dataset/data.yaml \
    model=yolov8s.pt \
    epochs=50 \
    imgsz=640 \
    batch=16 \
    project=runs/detect \
    name=logo_detection
```

**Giải thích tham số:**
- `data`: đường dẫn đến `data.yaml`
- `model`: model pretrained (yolov8s.pt, yolov8n.pt, yolov8m.pt, yolov8l.pt, yolov8x.pt)
- `epochs`: số lần train (50-100)
- `imgsz`: kích thước ảnh input (640, 1280)
- `batch`: batch size (tùy GPU/RAM)

### Bước 4: Lấy Model đã Train

Sau khi train xong, model sẽ ở:
```
runs/detect/logo_detection/weights/best.pt
```

**Copy `best.pt` vào thư mục project:**
```bash
cp runs/detect/logo_detection/weights/best.pt ./best.pt
```

---

## IV. Setup Docker

### Bước 1: Build Docker Image

```bash
docker build -f Dockerfile.yolo -t n8n-yolo:latest .
```

### Bước 2: Copy Model vào Container

Có 2 cách:

**Cách 1: Mount volume**
```yaml
# docker-compose.yml
volumes:
  - ./best.pt:/data/models/best.pt
  - ./scripts:/data/scripts
  - ./input:/data/input
  - ./output:/data/output
```

**Cách 2: Copy vào image**
```dockerfile
COPY best.pt /data/models/best.pt
```

### Bước 3: Chạy Container

```bash
docker-compose up -d
```

---

## V. N8N Workflow Setup

### Node 1: HTTP Request / Load Image

**HTTP Request Node:**
- Method: GET
- URL: `https://example.com/image.jpg`
- Response: Binary Data
- Save to: `/data/input/image.jpg`

**Hoặc Read Binary File Node:**
- File Path: `/data/input/image.jpg`

### Node 2: Execute Command - Detect Logo

**Execute Command Node:**
- Command: `python3`
- Arguments:
  ```
  /data/scripts/detect_yolo.py
  /data/input/image.jpg
  /data/models/best.pt
  0.25
  ```
- Working Directory: `/data`

**Parse Output:**
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

### Node 3: Execute Command - Overlay Logo

**Execute Command Node:**
- Command: `python3`
- Arguments:
  ```
  /data/scripts/overlay_logo.py
  /data/input/image.jpg
  /data/new_logo.png
  {{ $json.x }}
  {{ $json.y }}
  {{ $json.width }}
  {{ $json.height }}
  /data/output/result.jpg
  ```
- Working Directory: `/data`

**Parse Output:**
```javascript
const output = $input.item.json.stdout;
const result = JSON.parse(output);
return {
  output_path: result.output
};
```

### Node 4: Upload / Save / Return

**HTTP Response Node:**
- Return binary file từ `/data/output/result.jpg`

**Hoặc Save File Node:**
- Save to local/cloud storage

---

## VI. Test Scripts

### Test Detect

```bash
python3 /data/scripts/detect_yolo.py /data/input/test.jpg /data/models/best.pt 0.25
```

**Output mong đợi:**
```json
{"x":340,"y":120,"width":90,"height":40}
```

### Test Overlay

```bash
python3 /data/scripts/overlay_logo.py \
  /data/input/test.jpg \
  /data/new_logo.png \
  340 120 90 40 \
  /data/output/result.jpg
```

**Output mong đợi:**
```json
{"output":"/data/output/result.jpg"}
```

---

## VII. Troubleshooting

### Lỗi: Model not found
- Kiểm tra đường dẫn `best.pt` trong container
- Đảm bảo volume mount đúng

### Lỗi: No detections
- Giảm `conf_threshold` (mặc định 0.25)
- Kiểm tra model đã train đúng chưa
- Kiểm tra ảnh input có logo không

### Lỗi: Import ultralytics failed
- Kiểm tra Dockerfile đã install ultralytics chưa
- Rebuild image: `docker build -f Dockerfile.yolo -t n8n-yolo:latest .`

### Lỗi: Multiple detections
- Script tự động chọn box có confidence cao nhất
- Nếu cần tất cả boxes, sửa `detect_yolo.py` để trả array

---

## VIII. Production Tips

1. **Model Size**: Dùng `yolov8n.pt` (nano) nếu cần tốc độ, `yolov8s.pt` (small) nếu cần độ chính xác
2. **Confidence Threshold**: Tùy chỉnh trong n8n (0.25-0.5)
3. **Image Size**: Resize ảnh input về 640x640 trước khi detect để tăng tốc
4. **Batch Processing**: Có thể xử lý nhiều ảnh cùng lúc nếu cần

---

## IX. File Structure

```
n8n-install/
├── Dockerfile.yolo
├── docker-compose.yml
├── best.pt (model đã train)
├── scripts/
│   ├── detect_yolo.py
│   └── overlay_logo.py
├── data/
│   ├── models/
│   │   └── best.pt
│   ├── input/
│   │   └── image.jpg
│   ├── output/
│   │   └── result.jpg
│   └── new_logo.png
└── YOLO_SETUP_GUIDE.md
```

---

## X. Quick Start

1. **Train model trên Roboflow** → export dataset → train YOLO → lấy `best.pt`
2. **Build Docker**: `docker build -f Dockerfile.yolo -t n8n-yolo:latest .`
3. **Copy model**: `cp best.pt ./data/models/`
4. **Setup n8n workflow** theo hướng dẫn trên
5. **Test**: Chạy workflow với ảnh test

---

**Lưu ý:** Tất cả script output JSON một dòng duy nhất để n8n dễ parse.

