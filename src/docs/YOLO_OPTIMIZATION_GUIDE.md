# HƯỚNG DẪN TỐI ƯU HỆ THỐNG YOLO + FFMPEG (16GB RAM - CPU)

Tài liệu này hướng dẫn tối ưu hóa service xử lý video trên laptop 16GB RAM không GPU.
Mục tiêu: **Không OOM (Out Of Memory)**, **Không quá nhiệt**, bảo vệ SSD, và hỗ trợ **Re-up an toàn**.

---

## 1. Cấu hình Cốt lõi (Bắt buộc)

Dù chạy profile nào, các thiết lập hệ thống sau là **BẮT BUỘC** để tránh sập nguồn/treo máy:

### 1.1 Biến Môi trường (System Env)
Đặt trong `.env`, Dockerfile hoặc script khởi chạy:
```bash
# Ép chạy đơn luồng để RAM đi ngang (Flatline), không spike
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1
export OPENBLAS_NUM_THREADS=1
export VECLIB_MAXIMUM_THREADS=1
export NUMEXPR_NUM_THREADS=1

# Giới hạn RAM cứng cho process (3.5GB) để OS kill nếu leak thay vì treo máy
ulimit -v 3500000

# Chạy background priority
nice -n 10
```

### 1.2 Pipeline Logic (Code Level)
1.  **Split & Stream**: Không load cả video. Cắt từng chunk **30s** -> Xử lý xong -> Xóa ngay.
2.  **Singleton Model**: Load YOLO model đúng **1 lần** vào biến Global.
3.  **Inference**:
    -   `imgsz=640`, `device='cpu'`, `batch=1`, `workers=0`.
    -   Luôn dùng `with torch.no_grad():` để tiết kiệm 40% RAM.

---

## 2. Các Profile Cấu hình (Chọn 1)

Admin chọn 1 trong 2 profile dưới đây tùy mục đích. Config file nên hỗ trợ switch qua lại.

### PROFILE A: TỐC ĐỘ TỐI ĐA (Test / Raw Process)
*Dành cho debug hoặc video không cần né bản quyền.*
-   **FFmpeg**: `-preset ultrafast -crf 28` (Render cực nhanh, video hơi mờ, file nhẹ).
-   **Detect**: `N=3` (Mỗi 3 frame check 1 lần).
-   **Ưu điểm**: Nhanh, nhẹ nhất có thể.
-   **Nhược điểm**: Chất lượng thấp, dễ bị AI quét.

### PROFILE B: RE-UP AN TOÀN (Recommended for YouTube/TikTok)
*Dành cho môi trường Production Re-up. Cân bằng giữa chất lượng và safety.*
-   **FFmpeg**: `-preset veryfast -crf 24`
    -   *Lý do*: `veryfast` nén kỹ hơn `ultrafast` (không bị vỡ hạt). `crf 24` giữ chi tiết tốt để video nhìn "chuyên nghiệp".
-   **Detect**: `N=2` (Mỗi 2 frame check 1 lần) hoặc `N=3` kết hợp **Linear Interpolation**.
    -   *Lý do*: Giúp logo bám dính mượt mà, không bị trễ/giật khi vật thể di chuyển nhanh.
-   **Anti-AI Defenses (Lớp bảo vệ)**:
    -   **Flip**: `True` (Lật ngược video).
    -   **Zoom**: `1.1` (Zoom 110% để cắt viền).
    -   **Color**: `Brightness +5%`, `Saturation +10%`.
    -   **Speed**: `1.02x` (Tăng tốc nhẹ để lệch sóng âm thanh).

---

## 3. Config Block mẫu (Copy-Paste)

Dev copy đoạn này vào `config.ini` hoặc `.env`. Mặc định đang để **Profile B (Safe Re-up)**.

```ini
# --- SYSTEM RESOURCES ---
MEM_ULIMIT_KB=3500000
CPU_NICE_LEVEL=10
OMP_NUM_THREADS=1

# --- YOLO CORE ---
YOLO_MODEL_PATH="./models/yolov8n.pt"
YOLO_IMGSZ=640
YOLO_DEVICE="cpu"
YOLO_BATCH_SIZE=1

# --- SAFE RE-UP PROFILE (Recommended) ---
# 1. Chất lượng video (Nét, không mờ)
FFMPEG_PRESET="-preset veryfast"
FFMPEG_QUALITY="-crf 24"
FFMPEG_BUFFER="-probesize 32k -bufsize 500k"

# 2. Logic Detect (Mượt)
DETECT_INTERVAL_FRAMES=2   # Giảm N=2 để logo bám sát hơn
USE_INTERPOLATION=True     # Bật nội suy vị trí giữa các frame

# 3. Chống AI Quét (Anti-Content ID)
ENABLE_FLIP=True           # Lật gương
ZOOM_FACTOR=1.1            # Zoom 110%
SPEED_FACTOR=1.02          # Tốc độ 102%
COLOR_ADJUST="eq=brightness=0.05:saturation=1.1"
```

---

## 4. FAQ: Tại sao làm vậy?

**Q1: Tại sao không dùng `ultrafast` cho Re-up?**
> A: `ultrafast` làm vỡ hạt (pixelated). Video mờ -> AI Youtube đánh giá là "Spam/Low Quality" -> Bóp reach. Nên dùng `Veryfast` + `CRF 24` để video nét, nền tảng phân phối tốt hơn.

**Q2: Tại sao phải Zoom/Flip thay vì làm méo tiếng/mờ hình?**
> A: Làm mờ/méo tiếng là kỹ thuật cũ (2018), giờ AI phát hiện được hết và viewer sẽ bỏ xem. Zoom/Flip/Color/Speed thay đổi cấu trúc file (fingerprint) nhưng vẫn giữ trải nghiệm xem tốt -> Đây là cách Re-up bền vững (High Retention).

**Q3: Máy 16GB có chịu nổi Profile B không?**
> A: **Thoải mái**. Profile B chỉ tốn thêm CPU Time (thời gian render lâu hơn 20-30%) chứ **không tốn thêm RAM**. RAM đã bị khóa cứng bởi `OMP_NUM_THREADS` và logic Chunking rồi. Máy sẽ render lâu hơn xíu nhưng an toàn tuyệt đối.

---

## 5. Quy trình Deploy & Rollback

1.  **Deploy**:
    -   Check đúng model `yolov8n.pt`.
    -   Set Env Vars.
    -   Chạy thử 1 video với Profile B. So sánh input/output xem có bị vỡ hình không.
    -   Check `htop` xem RAM có < 4GB không.

2.  **Rollback**:
    -   Backup model cũ: `mv model.pt model.pt.bak`.
    -   Nếu deploy model mới bị sai lệch (detect trượt): Stop service -> Rename lại .bak -> Start lại.
