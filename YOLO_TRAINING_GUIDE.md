# HƯỚNG DẪN CHI TIẾT TRAIN YOLO MODEL DETECT LOGO VÀ TÍCH HỢP VÀO N8N

## MỤC LỤC

1. [Chuẩn bị Dataset](#1-chuẩn-bị-dataset)
2. [Tạo Dataset bằng MakeSense.ai](#2-tạo-dataset-bằng-makesenseai)
3. [Export Dataset YOLOv8](#3-export-dataset-yolov8)
4. [Chỉnh sửa File data.yaml](#4-chỉnh-sửa-file-datayaml)
5. [Train YOLO Model](#5-train-yolo-model)
6. [Test Model](#6-test-model)
7. [Chuyển Model vào N8N](#7-chuyển-model-vào-n8n)
8. [Tích hợp vào N8N Workflow](#8-tích-hợp-vào-n8n-workflow)
9. [Troubleshooting và Tips](#9-troubleshooting-và-tips)

---

## 1. CHUẨN BỊ DATASET

### 1.1. Cách Thu Thập Ảnh Có Logo

**Mục đích:** Thu thập ảnh thực tế từ video YouTube mà bạn sẽ xử lý, có chứa logo cần detect.

**Các nguồn ảnh phù hợp:**
- Extract frames từ video YouTube gốc (dùng ffmpeg hoặc yt-dlp)
- Ảnh từ các video khác nhau của cùng một kênh (logo giống nhau)
- Ảnh từ các thời điểm khác nhau trong video (logo có thể ở vị trí khác nhau)

**Lệnh extract frames từ video:**
```bash
# Extract 1 frame mỗi 5 giây
ffmpeg -i video.mp4 -vf "fps=1/5" frame_%04d.jpg

# Hoặc extract frame tại thời điểm cụ thể
ffmpeg -i video.mp4 -ss 00:00:10 -vframes 1 frame_001.jpg
```

### 1.2. Số Lượng Ảnh Phù Hợp

**Tối thiểu:**
- **50-100 ảnh** cho logo đơn giản, dễ nhận diện
- **100-200 ảnh** cho logo phức tạp, nhiều biến thể

**Lý tưởng:**
- **200-500 ảnh** để model có độ chính xác cao
- **500+ ảnh** cho production quality

**Lưu ý:** Chất lượng quan trọng hơn số lượng. 100 ảnh đa dạng tốt hơn 500 ảnh giống nhau.

### 1.3. Yêu Cầu Đa Dạng Ảnh

**Tại sao cần đa dạng:**
- Model cần học được logo trong nhiều điều kiện khác nhau
- Tránh overfitting (model chỉ nhớ ảnh training, không generalize được)

**Các yếu tố đa dạng cần có:**

1. **Vị trí logo:**
   - Top-left corner
   - Top-right corner
   - Bottom-left corner
   - Bottom-right corner
   - Giữa màn hình (ít gặp nhưng nên có)

2. **Kích thước logo:**
   - Logo nhỏ (chiếm < 5% diện tích ảnh)
   - Logo trung bình (5-15% diện tích)
   - Logo lớn (> 15% diện tích)

3. **Góc nhìn/Độ nghiêng:**
   - Logo thẳng đứng (normal)
   - Logo nghiêng nhẹ (nếu có trong video thực tế)
   - Logo bị méo do perspective (nếu có)

4. **Điều kiện ánh sáng:**
   - Ảnh sáng
   - Ảnh tối
   - Ảnh có độ tương phản cao/thấp

5. **Background:**
   - Background đơn giản (màu đồng nhất)
   - Background phức tạp (nhiều chi tiết)
   - Background có màu tương tự logo (khó detect)

6. **Độ phân giải:**
   - Ảnh HD (1280x720)
   - Ảnh Full HD (1920x1080)
   - Ảnh 4K (nếu có)

### 1.4. Ảnh Nên Loại Bỏ

**Loại bỏ các ảnh sau:**

1. **Logo quá mờ/không rõ:**
   - Logo bị blur quá nhiều
   - Logo bị che khuất > 50%
   - Logo quá nhỏ (< 20x20 pixels)

2. **Logo bị biến dạng:**
   - Logo bị méo quá nhiều do video effect
   - Logo bị cắt mất một phần quan trọng

3. **Ảnh trùng lặp:**
   - Ảnh giống hệt nhau (chỉ khác tên file)
   - Ảnh từ cùng một frame (không có giá trị)

4. **Ảnh không có logo:**
   - Ảnh không chứa logo cần detect
   - Ảnh chỉ có background

**Cách kiểm tra nhanh:**
```bash
# Xem tất cả ảnh trong thư mục
ls -lh dataset_raw/*.jpg | wc -l

# Xem preview ảnh (nếu có ImageMagick)
montage dataset_raw/*.jpg -tile 10x10 -geometry 200x200 preview.jpg
```

### 1.5. Cấu Trúc Thư Mục Ban Đầu

```
n8n-install/
├── dataset_raw/          # Ảnh gốc chưa annotate
│   ├── frame_001.jpg
│   ├── frame_002.jpg
│   ├── frame_003.jpg
│   └── ...
└── ...
```

**Lưu ý:** Giữ ảnh gốc ở `dataset_raw/` để backup, sau khi annotate trên Roboflow sẽ có dataset mới.

---

## 2. TẠO DATASET BẰNG MAKESENSE.AI

### 2.1. Tại Sao Chọn MakeSense.ai?

**Ưu điểm:**
- ✅ **Không cần tài khoản** - Chạy hoàn toàn trên trình duyệt
- ✅ **Không phụ thuộc CDN** - Ổn định hơn Roboflow
- ✅ **Miễn phí hoàn toàn** - Không giới hạn số lượng ảnh
- ✅ **Hỗ trợ YOLO format** - Export trực tiếp định dạng YOLO
- ✅ **Giao diện đơn giản** - Dễ sử dụng, không cần học nhiều

**Lưu ý:** MakeSense.ai không có tính năng augmentation tự động. Nếu cần augmentation, có thể dùng script Python sau khi export (sẽ nói ở phần sau).

### 2.2. Truy Cập MakeSense.ai

1. Truy cập: https://www.makesense.ai
2. **KHÔNG CẦN đăng ký** - Có thể dùng ngay
3. Trang chủ sẽ hiển thị các tùy chọn task

### 2.3. Chọn Task Type

1. Click vào **"Get Started"** hoặc **"Object Detection"**
2. Chọn task: **"Object Detection"** (QUAN TRỌNG!)
3. Trang annotation sẽ mở ra

**Lưu ý:** PHẢI chọn "Object Detection" vì chúng ta cần detect bounding box, không phải classification.

### 2.4. Upload Ảnh

1. Click nút **"Upload Images"** hoặc kéo thả ảnh vào browser
2. Chọn tất cả ảnh từ thư mục `dataset_raw/`
3. Chờ upload xong (có progress bar)

**Lưu ý:**
- Không giới hạn số lượng ảnh upload
- Format ảnh: JPG, PNG đều được
- Nếu có nhiều ảnh (> 500), có thể chia làm nhiều batch để tránh browser bị chậm

### 2.5. Tạo Label "logo"

1. Sau khi upload xong, ở sidebar bên trái sẽ có phần **"Labels"**
2. Click **"Add new label"** hoặc nhập trực tiếp vào ô text
3. Nhập tên label: **"logo"** (chữ thường, không dấu)
4. Nhấn `Enter` hoặc click **"Add"**

**Lưu ý:** Tên label phải là **"logo"** (chữ thường) để khớp với `data.yaml` sau này.

### 2.6. Annotate Logo (Vẽ Bounding Box)

**Bước quan trọng nhất!** Annotate đúng sẽ quyết định độ chính xác của model.

1. Click vào ảnh đầu tiên để bắt đầu annotate
2. Chọn label **"logo"** từ danh sách labels (hoặc nhấn phím số tương ứng)
3. Vẽ bounding box:
   - Click và kéo chuột để vẽ hình chữ nhật bao quanh logo
   - **QUAN TRỌNG:**
     - Bounding box phải bao phủ **TOÀN BỘ** logo
     - Bao gồm cả shadow, outline, glow nếu có
     - Không được cắt mất phần nào của logo
     - Không được bao quá nhiều background thừa

4. Điều chỉnh bounding box:
   - Click vào box để chọn
   - Kéo các góc để resize
   - Kéo box để di chuyển
   - Hoặc click vào box và dùng phím mũi tên để di chuyển

5. Lưu annotation:
   - Annotation tự động lưu khi bạn vẽ box
   - Click **"Next"** (mũi tên phải) hoặc nhấn `→` để chuyển ảnh tiếp theo
   - Click **"Previous"** (mũi tên trái) hoặc nhấn `←` để quay lại ảnh trước

**Tips annotate tốt:**
- ✅ Bounding box sát với logo (không thừa nhiều background)
- ✅ Bao gồm toàn bộ logo (không cắt mất phần nào)
- ✅ Nhất quán: tất cả ảnh cùng một logo phải annotate giống nhau
- ❌ Không annotate quá rộng (nhiều background thừa)
- ❌ Không annotate quá hẹp (cắt mất phần logo)

**Keyboard shortcuts:**
- `1`, `2`, `3`...: Chọn label tương ứng
- `W` hoặc click: Vẽ bounding box
- `←` / `→`: Previous/Next image
- `Delete` hoặc `Backspace`: Xóa bounding box đang chọn
- `Ctrl+Z`: Undo
- `Ctrl+S`: Save (tự động lưu)

**Lưu ý:** Nếu ảnh không có logo, bỏ qua ảnh đó (không vẽ box gì cả).

### 2.7. Kiểm Tra Annotation

1. Sau khi annotate xong, scroll qua tất cả ảnh để kiểm tra
2. Đảm bảo:
   - Tất cả ảnh có logo đều đã được annotate
   - Bounding box đúng vị trí và kích thước
   - Không có box nào bị thiếu hoặc sai

3. Sửa annotation nếu cần:
   - Click vào box để chọn và chỉnh sửa
   - Xóa box sai và vẽ lại

---

## 3. EXPORT DATASET YOLOV8

### 3.1. Export Annotations

**QUAN TRỌNG:** Đảm bảo đã annotate ít nhất 1 ảnh trước khi export!

1. Sau khi annotate xong tất cả ảnh, tìm nút **"Actions"** hoặc **"Export"** (thường ở góc trên bên phải hoặc menu)
2. Click vào **"Actions"** → **"Export Labels"** hoặc **"Export Annotations"**
3. Chọn format: **"YOLO"** hoặc **"YOLO txt"** (QUAN TRỌNG: phải chọn YOLO format!)
4. Click **"Export"** hoặc **"Download"**

**Lưu ý:**
- MakeSense.ai sẽ export tất cả ảnh và labels trong cùng một file zip
- Nếu file zip trống, có thể do:
  - Chưa annotate ảnh nào (chưa vẽ bounding box)
  - Export sai format (phải chọn YOLO, không phải Pascal VOC hay COCO)
  - Browser chặn download (kiểm tra thư mục Downloads)

### 3.2. Download Dataset

1. File zip sẽ được download tự động vào thư mục Downloads
2. Tên file có thể là: `annotations.zip`, `labels.zip`, `dataset_makesense.zip`, hoặc tên khác tùy MakeSense.ai

**Kiểm tra file đã download:**
```bash
# Xem file zip trong Downloads
ls -lh ~/Downloads/*.zip

# Kiểm tra file có rỗng không
unzip -l ~/Downloads/dataset_makesense.zip
```

**Lưu ý:** File zip này phải chứa:
- Tất cả ảnh gốc (`.jpg`, `.png`)
- File labels (`.txt`) tương ứng với mỗi ảnh đã annotate

**Nếu file zip trống hoặc không có file:**
- Quay lại MakeSense.ai và kiểm tra:
  1. Đã annotate ít nhất 1 ảnh chưa? (có bounding box chưa?)
  2. Đã chọn đúng format YOLO chưa?
  3. Thử export lại

### 3.3. Giải Nén và Kiểm Tra Cấu Trúc

1. Tìm file zip vừa download (thường trong `~/Downloads/`):
```bash
# Xem tất cả file zip trong Downloads
ls -lh ~/Downloads/*.zip

# Tìm file mới nhất (vừa download)
ls -t ~/Downloads/*.zip | head -1
```

2. Giải nén file zip (thay `dataset_makesense.zip` bằng tên file thực tế):
```bash
cd /home/vantrong/Documents/n8n-install

# Giải nén (thay tên file bằng tên file thực tế của bạn)
unzip ~/Downloads/dataset_makesense.zip -d dataset_makesense

# Hoặc nếu file tên khác:
# unzip ~/Downloads/annotations.zip -d dataset_makesense
# unzip ~/Downloads/labels.zip -d dataset_makesense
```

3. Kiểm tra cấu trúc thư mục:
```bash
# Xem tất cả file trong thư mục
ls -la dataset_makesense/

# Đếm số ảnh và labels
echo "Số ảnh: $(ls dataset_makesense/*.jpg dataset_makesense/*.png 2>/dev/null | wc -l)"
echo "Số labels: $(ls dataset_makesense/*.txt 2>/dev/null | wc -l)"
```

**Lưu ý:**
- Nếu giải nén báo lỗi "zipfile is empty", file zip bị rỗng → Quay lại MakeSense.ai export lại
- Số lượng file `.txt` phải bằng số lượng ảnh đã annotate (không nhất thiết bằng tổng số ảnh)

**Cấu trúc từ MakeSense.ai thường là:**
```
dataset_makesense/
├── frame_001.jpg
├── frame_001.txt
├── frame_002.jpg
├── frame_002.txt
├── frame_003.jpg
├── frame_003.txt
└── ...
```

**Lưu ý:** MakeSense.ai export tất cả ảnh và labels trong cùng một thư mục, chưa chia thành train/valid. Chúng ta sẽ tự chia ở bước tiếp theo.

### 3.4. Chia Dataset Thành Train/Valid

**Tại sao cần chia?**
- YOLO cần dataset được chia thành `train` và `valid`
- `train`: Dùng để train model (70-80% ảnh)
- `valid`: Dùng để validate model trong quá trình training (10-20% ảnh)

**Cách chia dataset:**

1. Tạo cấu trúc thư mục:
```bash
cd /home/vantrong/Documents/n8n-install
mkdir -p dataset_yolo/train/images dataset_yolo/train/labels
mkdir -p dataset_yolo/valid/images dataset_yolo/valid/labels
```

2. Chia ảnh và labels:
```bash
# Đếm tổng số ảnh
total=$(ls dataset_makesense/*.jpg | wc -l)
echo "Tổng số ảnh: $total"

# Tính số ảnh cho validation (20%)
valid_count=$((total * 20 / 100))
train_count=$((total - valid_count))
echo "Train: $train_count ảnh"
echo "Valid: $valid_count ảnh"

# Copy ảnh và labels vào train (80% đầu tiên)
counter=0
for img in dataset_makesense/*.jpg; do
    if [ $counter -lt $train_count ]; then
        filename=$(basename "$img")
        name="${filename%.*}"
        cp "$img" dataset_yolo/train/images/
        cp "dataset_makesense/${name}.txt" dataset_yolo/train/labels/ 2>/dev/null || echo "No label for $filename"
        counter=$((counter + 1))
    else
        break
    fi
done

# Copy ảnh và labels vào valid (20% còn lại)
for img in dataset_makesense/*.jpg; do
    if [ $counter -ge $train_count ]; then
        filename=$(basename "$img")
        name="${filename%.*}"
        cp "$img" dataset_yolo/valid/images/
        cp "dataset_makesense/${name}.txt" dataset_yolo/valid/labels/ 2>/dev/null || echo "No label for $filename"
        counter=$((counter + 1))
    fi
done
```

**Hoặc dùng script Python tự động:**

Tạo file `split_dataset.py`:
```python
import os
import shutil
import random

source_dir = "dataset_makesense"
train_images_dir = "dataset_yolo/train/images"
train_labels_dir = "dataset_yolo/train/labels"
valid_images_dir = "dataset_yolo/valid/images"
valid_labels_dir = "dataset_yolo/valid/labels"

# Tạo thư mục
os.makedirs(train_images_dir, exist_ok=True)
os.makedirs(train_labels_dir, exist_ok=True)
os.makedirs(valid_images_dir, exist_ok=True)
os.makedirs(valid_labels_dir, exist_ok=True)

# Lấy tất cả ảnh
images = [f for f in os.listdir(source_dir) if f.endswith(('.jpg', '.png', '.jpeg'))]
random.shuffle(images)  # Shuffle để đảm bảo đa dạng

# Chia 80% train, 20% valid
split_idx = int(len(images) * 0.8)
train_images = images[:split_idx]
valid_images = images[split_idx:]

print(f"Tổng số ảnh: {len(images)}")
print(f"Train: {len(train_images)} ảnh")
print(f"Valid: {len(valid_images)} ảnh")

# Copy ảnh và labels
for img in train_images:
    name = os.path.splitext(img)[0]
    shutil.copy(os.path.join(source_dir, img), os.path.join(train_images_dir, img))
    label_file = f"{name}.txt"
    if os.path.exists(os.path.join(source_dir, label_file)):
        shutil.copy(os.path.join(source_dir, label_file), os.path.join(train_labels_dir, label_file))

for img in valid_images:
    name = os.path.splitext(img)[0]
    shutil.copy(os.path.join(source_dir, img), os.path.join(valid_images_dir, img))
    label_file = f"{name}.txt"
    if os.path.exists(os.path.join(source_dir, label_file)):
        shutil.copy(os.path.join(source_dir, label_file), os.path.join(valid_labels_dir, label_file))

print("✅ Đã chia dataset thành công!")
```

Chạy script:
```bash
python3 split_dataset.py
```

### 3.5. Kiểm Tra Cấu Trúc Cuối Cùng

Sau khi chia xong, cấu trúc phải như sau:
```
dataset_yolo/
├── train/
│   ├── images/          # Ảnh training
│   │   ├── frame_001.jpg
│   │   ├── frame_002.jpg
│   │   └── ...
│   └── labels/           # File label (bounding box) cho mỗi ảnh
│       ├── frame_001.txt
│       ├── frame_002.txt
│       └── ...
├── valid/                # Validation set (dùng để đánh giá model)
│   ├── images/
│   │   ├── frame_050.jpg
│   │   └── ...
│   └── labels/
│       ├── frame_050.txt
│       └── ...
└── data.yaml             # File config (sẽ tạo ở phần tiếp theo)
```

### 3.6. Giải Thích Từng Thư Mục

**train/images:**
- Chứa ảnh dùng để train model
- Thường chiếm 70-80% tổng số ảnh
- Model sẽ học từ những ảnh này

**train/labels:**
- Chứa file `.txt` tương ứng với mỗi ảnh trong `train/images`
- Mỗi file `.txt` chứa annotation (bounding box) của logo trong ảnh
- Format: `class_id center_x center_y width height` (normalized 0-1)
- Ví dụ file `frame_001.txt`:
```
0 0.85 0.05 0.10 0.08
```
  - `0`: class_id của "logo" (class đầu tiên = 0)
  - `0.85`: center_x = 85% chiều rộng ảnh (logo ở bên phải)
  - `0.05`: center_y = 5% chiều cao ảnh (logo ở trên)
  - `0.10`: width = 10% chiều rộng ảnh
  - `0.08`: height = 8% chiều cao ảnh

**valid/images:**
- Chứa ảnh dùng để validate model trong quá trình training
- Thường chiếm 10-20% tổng số ảnh
- Model KHÔNG học từ ảnh này, chỉ dùng để đánh giá

**valid/labels:**
- Tương tự `train/labels`, nhưng cho validation set

**data.yaml:**
- File config quan trọng nhất!
- Chứa thông tin về dataset: số class, tên class, đường dẫn...
- Sẽ được tạo ở phần tiếp theo

### 3.7. Kiểm Tra Số Lượng Ảnh

```bash
# Đếm số ảnh training
ls dataset_yolo/train/images/*.jpg | wc -l

# Đếm số ảnh validation
ls dataset_yolo/valid/images/*.jpg | wc -l

# Đếm số label (phải bằng số ảnh)
ls dataset_yolo/train/labels/*.txt | wc -l
ls dataset_yolo/valid/labels/*.txt | wc -l
```

**Lưu ý:**
- Số lượng file trong `images/` phải bằng số lượng file trong `labels/` (mỗi ảnh phải có 1 file label tương ứng)
- Nếu ảnh không có logo (không có label), có thể bỏ qua ảnh đó hoặc tạo file `.txt` rỗng

### 3.8. Augmentation (Tùy Chọn)

**Lưu ý:** MakeSense.ai không có tính năng augmentation tự động. Nếu cần augmentation để tăng số lượng ảnh training, có thể:

1. **Dùng YOLO augmentation trong quá trình train:**
   - YOLO tự động áp dụng augmentation khi train (flip, rotation, brightness...)
   - Không cần chuẩn bị trước

2. **Dùng script Python để augment trước khi train:**
   - Có thể dùng thư viện `albumentations` hoặc `imgaug`
   - Tạo thêm ảnh từ ảnh gốc trước khi train
   - **Khuyến nghị:** Không cần thiết nếu đã có > 200 ảnh đa dạng

---

## 4. CHỈNH SỬA FILE data.yaml

### 4.1. Tạo File data.yaml

**Lưu ý:** MakeSense.ai không tự động tạo file `data.yaml`. Chúng ta cần tự tạo file này.

Tạo file `dataset_yolo/data.yaml`:
```bash
nano dataset_yolo/data.yaml
# Hoặc
vim dataset_yolo/data.yaml
```

**Nội dung file data.yaml:**
```yaml
path: /home/vantrong/Documents/n8n-install/dataset_yolo
train: train/images
valid: valid/images

nc: 1
names:
  0: logo
```

### 4.2. Giải Thích Từng Field

**path:**
- Đường dẫn gốc đến thư mục dataset
- Có thể là đường dẫn tuyệt đối hoặc tương đối
- **Lưu ý:** Khi train, YOLO sẽ dùng `path + train` để tìm ảnh

**train:**
- Đường dẫn đến thư mục ảnh training (tương đối so với `path`)
- Mặc định: `train/images`
- **Lưu ý:** YOLO tự động tìm file label trong `train/labels/` (cùng tên file, đổi extension .jpg → .txt)

**valid:**
- Đường dẫn đến thư mục ảnh validation (tương đối so với `path`)
- Mặc định: `valid/images`
- **Lưu ý:** Tương tự train, YOLO tự động tìm label trong `valid/labels/`

**test (optional):**
- Đường dẫn đến thư mục ảnh test
- Có thể bỏ qua nếu không có test set

**nc:**
- Số lượng class (number of classes)
- Với logo detection: `nc: 1` (chỉ có 1 class là "logo")
- **Lưu ý:** Nếu detect nhiều loại logo khác nhau, tăng số này (ví dụ: `nc: 3` cho 3 loại logo)

**names:**
- Dictionary mapping class_id → tên class
- **QUAN TRỌNG:** Phải có key `0: logo` (vì class_id của logo là 0)
- Format: `{class_id: "class_name"}`
- Ví dụ cho 1 class:
  ```yaml
  names:
    0: logo
  ```
- Ví dụ cho 3 class:
  ```yaml
  names:
    0: logo_old
    1: logo_new
    2: watermark
  ```

### 4.3. Chỉnh Sửa File data.yaml

**Cách 1: Dùng đường dẫn tuyệt đối (khuyến nghị)**

```yaml
path: /home/vantrong/Documents/n8n-install/dataset_yolo
train: train/images
valid: valid/images

nc: 1
names:
  0: logo
```

**Cách 2: Dùng đường dẫn tương đối (khi train từ thư mục dataset_yolo)**

```yaml
path: .
train: train/images
valid: valid/images

nc: 1
names:
  0: logo
```

**File data.yaml hoàn chỉnh (copy và paste):**
```yaml
path: /home/vantrong/Documents/n8n-install/dataset_yolo
train: train/images
valid: valid/images

nc: 1
names:
  0: logo
```

**Lưu ý:**
- Đảm bảo `names` có key `0: logo` (chữ thường, không dấu)
- Đảm bảo `nc: 1` (số class = 1)
- Đảm bảo đường dẫn `path` đúng với vị trí thực tế của dataset

### 4.4. Verify File data.yaml

```bash
# Kiểm tra syntax YAML
python3 -c "import yaml; yaml.safe_load(open('dataset_yolo/data.yaml'))"
```

Nếu không có lỗi, file đã đúng format.

---

## 5. TRAIN YOLO MODEL

### 5.1. Cài Đặt Ultralytics (Nếu Train Local)

**Nếu train trong Docker container n8n:**
- Đã có sẵn ultralytics trong Dockerfile, không cần cài thêm

**Nếu train trên máy local (không dùng Docker):**
```bash
pip3 install ultralytics
# Hoặc
pip3 install --upgrade ultralytics
```

**Kiểm tra đã cài chưa:**
```bash
python3 -c "from ultralytics import YOLO; print('OK')"
```

### 5.2. Chọn Model YOLO

**Các model YOLOv8 có sẵn:**
- `yolov8n.pt` - Nano (nhỏ nhất, nhanh nhất, ít chính xác nhất)
- `yolov8s.pt` - Small (cân bằng tốt, **KHUYẾN NGHỊ**)
- `yolov8m.pt` - Medium (lớn hơn, chính xác hơn, chậm hơn)
- `yolov8l.pt` - Large (rất chính xác, rất chậm)
- `yolov8x.pt` - XLarge (chính xác nhất, chậm nhất)

**Khuyến nghị:**
- **yolov8s.pt** - Cân bằng tốt giữa tốc độ và độ chính xác
- Phù hợp cho logo detection (logo thường không quá phức tạp)
- Model size ~22MB, đủ nhỏ để chạy trong Docker

**Khi nào dùng model khác:**
- `yolov8n.pt`: Nếu cần tốc độ cực nhanh, chấp nhận độ chính xác thấp hơn
- `yolov8m.pt`: Nếu logo rất nhỏ hoặc rất phức tạp, cần độ chính xác cao hơn

### 5.3. Lệnh Train Chính Xác

**Lệnh cơ bản:**
```bash
yolo detect train \
    data=/home/vantrong/Documents/n8n-install/dataset_yolo/data.yaml \
    model=yolov8s.pt \
    epochs=50 \
    imgsz=640
```

**Giải thích từng tham số:**
- `data=...`: Đường dẫn đến file `data.yaml`
- `model=yolov8s.pt`: Model pre-trained để fine-tune (YOLO tự động download nếu chưa có)
- `epochs=50`: Số lần train qua toàn bộ dataset (50-100 là hợp lý)
- `imgsz=640`: Kích thước ảnh input (640x640 pixels, chuẩn YOLO)

**Lệnh đầy đủ với các tham số tối ưu:**
```bash
yolo detect train \
    data=/home/vantrong/Documents/n8n-install/dataset_yolo/data.yaml \
    model=yolov8s.pt \
    epochs=100 \
    imgsz=640 \
    batch=16 \
    patience=20 \
    device=0
```

**Giải thích tham số bổ sung:**
- `batch=16`: Số ảnh xử lý cùng lúc (tăng nếu có nhiều RAM/GPU)
- `patience=20`: Dừng train sớm nếu validation loss không cải thiện sau 20 epochs
- `device=0`: Dùng GPU (0 = GPU đầu tiên), bỏ tham số này nếu train bằng CPU

**Lệnh train bằng CPU (không có GPU):**
```bash
yolo detect train \
    data=/home/vantrong/Documents/n8n-install/dataset_yolo/data.yaml \
    model=yolov8s.pt \
    epochs=50 \
    imgsz=640 \
    batch=8
```

**Lưu ý:** Train bằng CPU sẽ chậm hơn rất nhiều (có thể mất vài giờ đến vài ngày tùy số ảnh).

### 5.4. Nên Train Bao Nhiêu Epochs?

**Khuyến nghị:**
- **50-100 epochs** cho dataset nhỏ (< 200 ảnh)
- **100-200 epochs** cho dataset lớn (> 200 ảnh)
- **Dùng early stopping** (`patience=20`) để tự động dừng khi không cải thiện

**Cách xác định số epochs phù hợp:**
- Train với `epochs=200` và `patience=20`
- Model sẽ tự động dừng khi validation loss không cải thiện sau 20 epochs
- Thường sẽ dừng ở epoch 60-100

**Dấu hiệu model đã train đủ:**
- Validation loss không giảm nữa (plateau)
- Validation mAP (mean Average Precision) không tăng nữa
- Model bắt đầu overfit (train loss giảm nhưng validation loss tăng)

### 5.5. Yêu Cầu GPU Hay CPU?

**GPU (NVIDIA CUDA):**
- ✅ **Rất nhanh:** Train 100 epochs trong 10-30 phút (tùy GPU)
- ✅ **Khuyến nghị** cho dataset lớn (> 200 ảnh)
- ⚠️ Cần cài CUDA và cuDNN

**CPU:**
- ⚠️ **Chậm:** Train 100 epochs có thể mất 2-10 giờ (tùy CPU)
- ✅ **Đủ dùng** cho dataset nhỏ (< 200 ảnh)
- ✅ Không cần setup gì thêm

**Cách kiểm tra có GPU không:**
```bash
# Kiểm tra GPU NVIDIA
nvidia-smi

# Kiểm tra CUDA trong Python
python3 -c "import torch; print(torch.cuda.is_available())"
```

**Khuyến nghị:**
- Nếu có GPU: Dùng GPU (`device=0`)
- Nếu không có GPU: Train bằng CPU, nhưng giảm `batch` xuống 4-8 và tăng `patience`

### 5.6. Chạy Lệnh Train

**Cách 1: Train trong Docker container n8n**
```bash
# Vào container
docker exec -it n8n_main bash

# Chạy train (đảm bảo dataset_yolo đã được mount hoặc copy vào container)
cd /data
yolo detect train \
    data=/data/dataset_yolo/data.yaml \
    model=yolov8s.pt \
    epochs=50 \
    imgsz=640
```

**Cách 2: Train trên máy local**
```bash
cd /home/vantrong/Documents/n8n-install
yolo detect train \
    data=dataset_yolo/data.yaml \
    model=yolov8s.pt \
    epochs=50 \
    imgsz=640
```

**Output khi train:**
```
Ultralytics YOLOv8.0.xxx  Python-3.12.0  Linux-6.14.0
YOLOv8s summary: 225 layers, 11166560 parameters, 0 gradients, 28.6 GFLOPs

Dataset: /data/dataset_yolo
Train: 140 images
Valid: 30 images

Epoch    GPU_mem   box_loss   obj_loss   cls_loss   Instances       Size
  1/50      2.1G     0.12345    0.05678    0.00123        140        640
  2/50      2.1G     0.09876    0.04567    0.00098        140        640
  ...
```

**Theo dõi quá trình train:**
- `box_loss`: Loss của bounding box (càng thấp càng tốt)
- `obj_loss`: Loss của objectness (càng thấp càng tốt)
- `cls_loss`: Loss của classification (càng thấp càng tốt)
- `Instances`: Số lượng object detect được trong batch
- `Size`: Kích thước ảnh input

### 5.7. Giải Thích Output Folder `runs/detect/train/`

Sau khi train xong, YOLO tạo thư mục `runs/detect/train/` với cấu trúc:

```
runs/detect/train/
├── args.yaml              # Tất cả tham số train đã dùng
├── results.png            # Biểu đồ kết quả train (loss, mAP)
├── confusion_matrix.png   # Confusion matrix
├── F1_curve.png          # F1 score curve
├── PR_curve.png          # Precision-Recall curve
├── results.csv           # Kết quả train dạng CSV
├── train_batch0.jpg      # Ảnh training batch đầu tiên (có vẽ bounding box)
├── val_batch0.jpg        # Ảnh validation batch đầu tiên (có vẽ prediction)
└── weights/
    ├── best.pt           # Model tốt nhất (dựa trên validation mAP) ⭐
    └── last.pt           # Model ở epoch cuối cùng
```

**File quan trọng nhất: `weights/best.pt`**
- Đây là model tốt nhất trong quá trình train
- Được chọn dựa trên validation mAP (mean Average Precision) cao nhất
- **File này sẽ được dùng trong `detect_yolo.py`**

**File `last.pt`:**
- Model ở epoch cuối cùng
- Có thể không phải model tốt nhất (nếu overfit ở cuối)
- Thường dùng để tiếp tục train (resume training)

**Các file ảnh:**
- `results.png`: Biểu đồ tổng hợp (loss, mAP, precision, recall)
- `confusion_matrix.png`: Ma trận confusion (đánh giá độ chính xác)
- `train_batch0.jpg`: Xem model học như thế nào
- `val_batch0.jpg`: Xem model predict như thế nào trên validation set

**Cách xem kết quả:**
```bash
# Xem biểu đồ kết quả
xdg-open runs/detect/train/results.png

# Hoặc copy vào máy local để xem
scp runs/detect/train/results.png ~/Desktop/
```

---

## 6. TEST MODEL

### 6.1. Load Model và Test

**Tạo script test đơn giản:**

```python
# test_model.py
from ultralytics import YOLO
import cv2

# Load model
model = YOLO("runs/detect/train/weights/best.pt")

# Test trên ảnh
results = model("dataset_yolo/valid/images/frame_050.jpg", conf=0.25)

# Xem kết quả
result = results[0]
print(f"Detected {len(result.boxes)} logo(s)")

# Vẽ bounding box lên ảnh
img = cv2.imread("dataset_yolo/valid/images/frame_050.jpg")
for box in result.boxes:
    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
    conf = box.conf[0].cpu().numpy()
    cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
    cv2.putText(img, f"logo {conf:.2f}", (int(x1), int(y1)-10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

cv2.imwrite("test_result.jpg", img)
print("Saved test_result.jpg")
```

**Chạy test:**
```bash
python3 test_model.py
```

### 6.2. Đọc Bounding Box Kết Quả

**Format kết quả từ YOLO:**
```python
results = model("image.jpg", conf=0.25)
result = results[0]

# Lấy tất cả bounding boxes
boxes = result.boxes.xyxy.cpu().numpy()  # Format: [x1, y1, x2, y2]
confidences = result.boxes.conf.cpu().numpy()  # Confidence scores

# Lấy box có confidence cao nhất
best_idx = confidences.argmax()
best_box = boxes[best_idx]  # [x1, y1, x2, y2]

x1, y1, x2, y2 = best_box
x = int(x1)        # Tọa độ x góc trên trái
y = int(y1)        # Tọa độ y góc trên trái
width = int(x2 - x1)   # Chiều rộng
height = int(y2 - y1)  # Chiều cao
```

**Format này khớp với `detect_yolo.py`:**
- `detect_yolo.py` đã xử lý đúng format này
- Output JSON: `{"x": x, "y": y, "width": width, "height": height}`

### 6.3. Test Trên Nhiều Ảnh

**Test trên toàn bộ validation set:**
```bash
yolo detect val \
    model=runs/detect/train/weights/best.pt \
    data=dataset_yolo/data.yaml \
    imgsz=640
```

**Output:**
```
Ultralytics YOLOv8.0.xxx
Results saved to runs/detect/val

Speed: 2.3ms preprocess, 5.6ms inference, 0.1ms postprocess per image
Results:
  mAP50: 0.95        # Mean Average Precision @ IoU=0.5
  mAP50-95: 0.87     # Mean Average Precision @ IoU=0.5-0.95
  Precision: 0.92   # Precision
  Recall: 0.89       # Recall
```

**Đánh giá kết quả:**
- **mAP50 > 0.9**: Rất tốt ✅
- **mAP50 0.8-0.9**: Tốt ✅
- **mAP50 0.7-0.8**: Chấp nhận được ⚠️
- **mAP50 < 0.7**: Cần cải thiện (thêm ảnh training, train thêm epochs)

---

## 7. CHUYỂN MODEL VÀO N8N

### 7.1. Copy best.pt Vào Thư Mục ./models

**Từ thư mục project:**
```bash
cd /home/vantrong/Documents/n8n-install

# Copy best.pt vào thư mục models
cp runs/detect/train/weights/best.pt ./models/best.pt

# Kiểm tra
ls -lh ./models/best.pt
```

**Nếu train trong Docker container:**
```bash
# Copy từ container ra host
docker cp n8n_main:/data/runs/detect/train/weights/best.pt ./models/best.pt

# Hoặc vào container và copy
docker exec -it n8n_main bash
cp /data/runs/detect/train/weights/best.pt /data/models/best.pt
exit
```

### 7.2. Verify Docker Compose Mount

**Kiểm tra `docker-compose.yml`:**
```yaml
volumes:
  - ./models:/data/models
```

**Đảm bảo thư mục `./models` tồn tại:**
```bash
mkdir -p ./models
ls -lh ./models/
```

### 7.3. Verify Model Trong Container

**Vào container và kiểm tra:**
```bash
docker exec -it n8n_main bash

# Kiểm tra file có tồn tại không
ls -lh /data/models/best.pt

# Kiểm tra model có load được không
python3 - <<EOF
from ultralytics import YOLO
import sys

try:
    model = YOLO("/data/models/best.pt")
    print("✅ Model loaded successfully!")
    print(f"Model size: {sum(p.numel() for p in model.model.parameters())} parameters")
except Exception as e:
    print(f"❌ Error loading model: {e}", file=sys.stderr)
    sys.exit(1)
EOF
```

**Output mong đợi:**
```
✅ Model loaded successfully!
Model size: 11166560 parameters
```

### 7.4. Test detect_yolo.py Trong Container

**Test script detect với ảnh mẫu:**
```bash
# Copy ảnh test vào input
cp dataset_yolo/valid/images/frame_050.jpg ./input/test.jpg

# Vào container
docker exec -it n8n_main bash

# Test detect
python3 /data/scripts/detect_yolo.py \
    /data/input/test.jpg \
    /data/models/best.pt \
    0.25
```

**Output mong đợi:**
```json
{"x":340,"y":120,"width":90,"height":40}
```

**Nếu có lỗi:**
- Kiểm tra đường dẫn file ảnh
- Kiểm tra model path
- Kiểm tra confidence threshold (0.25 là hợp lý)

---

## 8. TÍCH HỢP VÀO N8N WORKFLOW

### 8.1. Cấu Trúc Workflow

Workflow sẽ có các node sau:
1. **Load Image** - Lấy ảnh từ input (HTTP Request hoặc Read Binary File)
2. **Detect Logo (YOLO)** - Execute Command gọi `detect_yolo.py`
3. **Parse Detection Result** - Code node parse JSON
4. **Overlay Logo** - Execute Command gọi `overlay_logo.py`
5. **Return/Upload Result** - HTTP Response hoặc Upload node

### 8.2. Node 1: Load Image

**Cách 1: HTTP Request Node**
- Method: GET hoặc POST
- URL: URL của ảnh cần xử lý
- Response Format: File
- Save to: `/data/input/image_{{ $timestamp }}.jpg`

**Cách 2: Read Binary File Node**
- File Path: `/data/input/image.jpg`
- (Nếu ảnh đã có sẵn trong container)

### 8.3. Node 2: Detect Logo (YOLO)

**Execute Command Node:**
- **Command:** `python3`
- **Arguments:**
  ```
  /data/scripts/detect_yolo.py
  /data/input/image_{{ $timestamp }}.jpg
  /data/models/best.pt
  0.25
  ```
- **Working Directory:** `/data`
- **Continue On Fail:** `false` (hoặc `true` nếu muốn xử lý lỗi)

**Lưu ý:**
- Đảm bảo đường dẫn ảnh đúng với Node 1
- Confidence threshold `0.25` có thể điều chỉnh (0.15-0.5)
- Output sẽ là JSON string trong `stdout`

### 8.4. Node 3: Parse Detection Result

**Code Node (JavaScript):**
```javascript
// Lấy output từ Execute Command
const output = $input.item.json.stdout.trim();

// Parse JSON
let bbox;
try {
  bbox = JSON.parse(output);
} catch (e) {
  // Nếu không detect được logo, trả về giá trị mặc định
  return {
    x: 0,
    y: 0,
    width: 0,
    height: 0,
    detected: false,
    error: e.message
  };
}

// Kiểm tra có detect được logo không
if (bbox.width === 0 || bbox.height === 0) {
  return {
    ...bbox,
    detected: false
  };
}

// Trả về kết quả
return {
  x: bbox.x,
  y: bbox.y,
  width: bbox.width,
  height: bbox.height,
  detected: true
};
```

**Hoặc dùng Set Node:**
- Nếu output JSON đơn giản, có thể dùng Set node để map trực tiếp

### 8.5. Node 4: Overlay Logo

**IF Node (kiểm tra có detect được logo không):**
- Condition: `{{ $json.detected }} === true`
- **TRUE branch:** Chạy overlay
- **FALSE branch:** Skip overlay (hoặc dùng fallback)

**Execute Command Node (trong TRUE branch):**
- **Command:** `python3`
- **Arguments:**
  ```
  /data/scripts/overlay_logo.py
  /data/input/image_{{ $timestamp }}.jpg
  /data/input/new_logo.png
  {{ $json.x }}
  {{ $json.y }}
  {{ $json.width }}
  {{ $json.height }}
  /data/output/result_{{ $timestamp }}.jpg
  ```
- **Working Directory:** `/data`

**Lưu ý:**
- Đảm bảo file `new_logo.png` đã có trong `/data/input/`
- Hoặc dùng HTTP Request node để download logo mới trước

### 8.6. Node 5: Return/Upload Result

**Cách 1: HTTP Response Node**
- Response Format: File
- File Path: `/data/output/result_{{ $timestamp }}.jpg`
- Content-Type: `image/jpeg`

**Cách 2: Upload to Google Drive/Cloud**
- Dùng node tương ứng (Google Drive, S3, etc.)
- Upload file từ `/data/output/result_{{ $timestamp }}.jpg`

### 8.7. Workflow Hoàn Chỉnh (Text Description)

```
1. HTTP Request (GET image)
   → Save to /data/input/image_123.jpg

2. Execute Command (detect_yolo.py)
   → Input: /data/input/image_123.jpg
   → Output: {"x":340,"y":120,"width":90,"height":40}

3. Code Node (Parse JSON)
   → Extract x, y, width, height
   → Check detected = true

4. IF Node (detected === true?)
   → TRUE: Continue
   → FALSE: Return error

5. Execute Command (overlay_logo.py)
   → Input: /data/input/image_123.jpg
   → Logo: /data/input/new_logo.png
   → BBox: x=340, y=120, w=90, h=40
   → Output: /data/output/result_123.jpg

6. HTTP Response (Return file)
   → File: /data/output/result_123.jpg
```

### 8.8. Lệnh Detect YOLO Trong N8N

**Execute Command Node - Detect:**
```bash
python3 /data/scripts/detect_yolo.py /data/input/image.jpg /data/models/best.pt 0.25
```

**Parse JSON trong Code Node:**
```javascript
const output = $input.item.json.stdout.trim();
const bbox = JSON.parse(output);
return bbox;
```

**Execute Command Node - Overlay:**
```bash
python3 /data/scripts/overlay_logo.py /data/input/image.jpg /data/input/new_logo.png {{ $json.x }} {{ $json.y }} {{ $json.width }} {{ $json.height }} /data/output/result.jpg
```

---

## 9. TROUBLESHOOTING VÀ TIPS

### 9.1. Model Detect Không Chính Xác

**Vấn đề:** Model không detect được logo hoặc detect sai vị trí.

**Giải pháp:**

1. **Giảm confidence threshold:**
   ```bash
   # Thử giảm từ 0.25 xuống 0.15
   python3 detect_yolo.py image.jpg best.pt 0.15
   ```

2. **Thêm ảnh training:**
   - Thêm ảnh có logo tương tự ảnh test
   - Đảm bảo annotate chính xác
   - Train lại model

3. **Train thêm epochs:**
   ```bash
   # Resume training từ best.pt
   yolo detect train \
       data=dataset_yolo/data.yaml \
       model=runs/detect/train/weights/best.pt \
       epochs=150 \
       imgsz=640
   ```

4. **Dùng model lớn hơn:**
   ```bash
   # Thử yolov8m.pt thay vì yolov8s.pt
   yolo detect train \
       data=dataset_yolo/data.yaml \
       model=yolov8m.pt \
       epochs=50 \
       imgsz=640
   ```

### 9.2. Model Detect Quá Nhiều False Positive

**Vấn đề:** Model detect logo ở chỗ không có logo.

**Giải pháp:**

1. **Tăng confidence threshold:**
   ```bash
   # Tăng từ 0.25 lên 0.4 hoặc 0.5
   python3 detect_yolo.py image.jpg best.pt 0.4
   ```

2. **Thêm ảnh negative vào training:**
   - Thêm ảnh KHÔNG có logo vào dataset
   - Không annotate gì (để YOLO học đây là background)
   - Train lại

3. **Kiểm tra annotation:**
   - Đảm bảo không annotate nhầm background thành logo
   - Xem lại các ảnh validation có false positive

### 9.3. Model Detect Logo Quá Nhỏ/Lớn

**Vấn đề:** Bounding box không khớp với logo thực tế.

**Giải pháp:**

1. **Kiểm tra annotation:**
   - Đảm bảo bounding box trong training data đúng
   - Không được quá rộng (nhiều background) hoặc quá hẹp (cắt mất logo)

2. **Thêm ảnh có logo kích thước tương tự:**
   - Nếu logo trong ảnh test nhỏ hơn training, thêm ảnh có logo nhỏ vào dataset
   - Tương tự với logo lớn

### 9.4. Lỗi "Model not found" Trong N8N

**Vấn đề:** `detect_yolo.py` báo lỗi không tìm thấy model.

**Giải pháp:**

1. **Kiểm tra file có tồn tại không:**
   ```bash
   docker exec -it n8n_main ls -lh /data/models/best.pt
   ```

2. **Kiểm tra quyền truy cập:**
   ```bash
   docker exec -it n8n_main chmod 644 /data/models/best.pt
   ```

3. **Kiểm tra docker-compose mount:**
   ```yaml
   volumes:
     - ./models:/data/models
   ```

4. **Restart container:**
   ```bash
   docker-compose restart n8n
   ```

### 9.5. Lỗi "Import ultralytics failed" Trong Container

**Vấn đề:** Container không có ultralytics.

**Giải pháp:**

1. **Rebuild Docker image:**
   ```bash
   docker-compose build --no-cache
   docker-compose up -d
   ```

2. **Kiểm tra Dockerfile có cài ultralytics:**
   ```dockerfile
   pip3 install --no-cache-dir --break-system-packages ultralytics
   ```

### 9.6. Tips Tăng Accuracy

1. **Dataset đa dạng:**
   - Đảm bảo có đủ ảnh từ nhiều video khác nhau
   - Đảm bảo có đủ ảnh với logo ở nhiều vị trí khác nhau

2. **Annotation chính xác:**
   - Bounding box phải sát với logo (không thừa background)
   - Tất cả ảnh cùng một logo phải annotate nhất quán

3. **Augmentation hợp lý:**
   - Bật augmentation nếu có < 200 ảnh
   - Không bật augmentation quá mạnh (có thể làm méo logo)

4. **Train đủ epochs:**
   - Train ít nhất 50 epochs
   - Dùng early stopping để tránh overfit

5. **Chọn model phù hợp:**
   - `yolov8s.pt` cho hầu hết trường hợp
   - `yolov8m.pt` nếu logo rất nhỏ hoặc phức tạp

6. **Tune confidence threshold:**
   - Test với nhiều giá trị: 0.15, 0.25, 0.35, 0.5
   - Chọn giá trị cho precision/recall tốt nhất

---

## 10. TÓM TẮT QUY TRÌNH

### Checklist Từ Đầu Đến Cuối:

- [ ] 1. Thu thập ảnh có logo (50-500 ảnh)
- [ ] 2. Truy cập MakeSense.ai và chọn task "Object Detection"
- [ ] 3. Upload ảnh lên MakeSense.ai
- [ ] 4. Tạo label "logo"
- [ ] 5. Annotate logo (vẽ bounding box cho tất cả ảnh)
- [ ] 6. Export annotations định dạng YOLO
- [ ] 7. Giải nén và chia dataset thành train/valid
- [ ] 8. Tạo file `data.yaml` (đường dẫn, names)
- [ ] 9. Train YOLO model (`yolo detect train`)
- [ ] 10. Test model trên validation set
- [ ] 11. Copy `best.pt` vào `./models/`
- [ ] 12. Verify model trong Docker container
- [ ] 13. Test `detect_yolo.py` trong container
- [ ] 14. Tạo N8N workflow với Execute Command nodes
- [ ] 15. Test end-to-end workflow

### Lệnh Quan Trọng:

```bash
# Train model
yolo detect train data=dataset_yolo/data.yaml model=yolov8s.pt epochs=50 imgsz=640

# Validate model
yolo detect val model=runs/detect/train/weights/best.pt data=dataset_yolo/data.yaml

# Copy model
cp runs/detect/train/weights/best.pt ./models/best.pt

# Test trong container
docker exec -it n8n_main python3 /data/scripts/detect_yolo.py /data/input/test.jpg /data/models/best.pt 0.25
```

---

## KẾT LUẬN

Sau khi hoàn thành tất cả các bước trên, bạn sẽ có:

1. ✅ Model YOLO đã train (`best.pt`) có thể detect logo chính xác
2. ✅ Script `detect_yolo.py` hoạt động trong Docker container
3. ✅ Script `overlay_logo.py` hoạt động để đè logo mới
4. ✅ N8N workflow hoàn chỉnh để tự động detect và overlay logo

**Lưu ý cuối cùng:**
- Model cần được retrain nếu logo thay đổi hoặc điều kiện ảnh thay đổi
- Luôn test model trên ảnh thực tế trước khi deploy production
- Monitor accuracy và retrain khi cần thiết

Chúc bạn thành công! 🚀
