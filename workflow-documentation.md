# Tài liệu Workflow n8n - Xử lý Video Tự động

## 📋 Tổng quan

**Tên workflow:** `test`
**ID:** `D71syQuOcFQ2EFVJ`
**Trạng thái:** `Active` ✅ (đang chạy)
**Mục đích:** Tự động tải video từ YouTube, upload lên Google Drive và cập nhật thông tin vào Google Sheets

## 🏗️ Cấu trúc Workflow

Workflow được chia thành 3 phần chính:

### PHẦN 1 – LẤY HÀNG: CHỌN VIDEO CẦN XỬ LÝ
Lọc và chọn các video cần xử lý từ Google Sheets

### PHẦN 2 – TẢI VIDEO & LƯU LÊN DRIVE
Tải video từ YouTube và upload lên Google Drive

### PHẦN 3 – PHÂN TÍCH LOGO + NỘI DUNG + CATEGORY
Phân tích video (chưa được triển khai)

---

## 🔄 Chi tiết các Node

### 1. Schedule Trigger
- **Type:** `n8n-nodes-base.scheduleTrigger`
- **Mô tả:** Kích hoạt workflow theo lịch định kỳ
- **Cấu hình:** Interval trigger (cần cấu hình chi tiết)

### 2. Get Information video
- **Type:** `n8n-nodes-base.googleSheets`
- **Mô tả:** Lấy thông tin video từ Google Sheets
- **Cấu hình:**
  - **Document ID:** `1-JdoLLwnsG4460c3BNS70jmZdDLKHelzZUWTG2g_BsI`
  - **Sheet Name:** `videos_template.csv` (GID: `1492578399`)
  - **Credentials:** Google Sheets OAuth2 API
- **Output:** Danh sách các video với các trường: `id`, `videoUrl`, `title`, `drive_link`, `status`, v.v.

### 3. If
- **Type:** `n8n-nodes-base.if`
- **Mô tả:** Kiểm tra điều kiện để chỉ xử lý video chưa có drive_link
- **Điều kiện:** `drive_link` phải rỗng (empty)
- **Logic:** Chỉ tiếp tục xử lý nếu `drive_link` trống

### 4. Extract Video URL
- **Type:** `n8n-nodes-base.code`
- **Mô tả:** Trích xuất thông tin video cần thiết
- **Mode:** `runOnceForEachItem`
- **Code:**
```javascript
const row = $('Get Information video').item.json;

let videoUrl = row.videoUrl;

if (!row.id || !videoUrl) {
  return { json: {} };
}

return {
  json: {
    id: row.id,
    title: row.title,
    videoUrl
  }
};
```
- **Output:** `{ id, title, videoUrl }`

### 5. Clear video
- **Type:** `n8n-nodes-base.executeCommand`
- **Mô tả:** Xóa các file video cũ trong thư mục downloads
- **Command:** `rm -f /home/node/downloads/*.mp4`
- **Mục đích:** Dọn dẹp thư mục trước khi tải video mới

### 6. Get Url Dowload
- **Type:** `n8n-nodes-base.executeCommand`
- **Mô tả:** Tải video từ YouTube sử dụng yt-dlp
- **Command:**
```bash
yt-dlp --no-playlist -f mp4 -o "/home/node/downloads/{{ $('Extract Video URL').item.json.id }}.mp4" "{{ $('Extract Video URL').item.json.videoUrl }}"
```
- **Tham số:**
  - `--no-playlist`: Không tải playlist
  - `-f mp4`: Format mp4
  - `-o`: Đường dẫn output với tên file = `{id}.mp4`

### 7. Read/Write Files from Disk
- **Type:** `n8n-nodes-base.readWriteFile`
- **Mô tả:** Đọc file video từ disk
- **File Selector:** `/home/node/downloads/*.mp4`
- **Output:** Binary data của file video

### 8. Upload Driver
- **Type:** `n8n-nodes-base.executeCommand`
- **Mô tả:** Upload video lên Google Drive sử dụng rclone
- **Command:**
```bash
rclone copy "/home/node/downloads/{{$binary.data.fileName}}" gdrive:reup-ytb -P
```
- **Tham số:**
  - `gdrive:reup-ytb`: Remote rclone trỏ đến thư mục `reup-ytb` trên Google Drive
  - `-P`: Progress bar

### 9. Get Driver Link
- **Type:** `n8n-nodes-base.executeCommand`
- **Mô tả:** Lấy link chia sẻ của file trên Google Drive
- **Command:**
```bash
rclone link "gdrive:reup-ytb/{{ $('Read/Write Files from Disk').item.binary.data.fileName }}"
```
- **Output:** Link chia sẻ Google Drive (trong `stdout`)

### 10. Remove Binary
- **Type:** `n8n-nodes-base.code`
- **Mô tả:** Xóa binary data để giải phóng bộ nhớ
- **Code:**
```javascript
// Remove binary to free memory
for (const item of $input.all()) {
  delete item.binary;
}
return $input.all();
```

### 11. Update Drive Link
- **Type:** `n8n-nodes-base.googleSheets`
- **Mô tả:** Cập nhật thông tin vào Google Sheets
- **Operation:** `update`
- **Cập nhật:**
  - `id`: ID của video (để match)
  - `status`: `"done"`
  - `drive_link`: Link Google Drive từ node "Get Driver Link"
- **Matching Column:** `id`

---

## 🔗 Luồng dữ liệu (Flow)

```
Schedule Trigger
    ↓
Get Information video (Google Sheets)
    ↓
If (drive_link empty?)
    ↓ (TRUE)
Extract Video URL
    ↓
Clear video (rm -f *.mp4)
    ↓
Get Url Dowload (yt-dlp)
    ↓
Read/Write Files from Disk
    ↓
Upload Driver (rclone copy)
    ↓
Get Driver Link (rclone link)
    ↓
Remove Binary
    ↓
Update Drive Link (Google Sheets)
    ↓
[END]
```

---

## 📊 Schema Google Sheets

Workflow làm việc với các cột sau trong Google Sheets:

| Cột | Type | Mô tả |
|-----|------|-------|
| `id` | string | ID của video (dùng để match) |
| `videoUrl` | string | URL video YouTube |
| `title` | string | Tiêu đề video |
| `title_original` | string | Tiêu đề gốc |
| `drive_link` | string | Link Google Drive (được cập nhật) |
| `status` | string | Trạng thái (được cập nhật thành "done") |
| `logo_position` | string | Vị trí logo |
| `title_ai` | string | Tiêu đề AI |
| `content_ai` | string | Nội dung AI |
| `tags_ai` | string | Tags AI |
| `category` | string | Danh mục |
| `processed_video_drive_link` | string | Link video đã xử lý |
| `reup_channel` | string | Kênh reup |
| `youtube_video_id` | string | ID video YouTube |
| `row_number` | number | Số thứ tự dòng (readonly) |

---

## ⚙️ Yêu cầu hệ thống

### Dependencies
- **yt-dlp**: Công cụ tải video từ YouTube
- **rclone**: Công cụ đồng bộ file với Google Drive
- **n8n**: Platform automation

### Thư mục
- `/home/node/downloads/`: Thư mục lưu video tạm thời

### Credentials
- **Google Sheets OAuth2 API**: Để đọc/ghi Google Sheets
- **rclone config**: Cấu hình remote `gdrive:reup-ytb` trỏ đến Google Drive

### Rclone Remote
- **Name:** `gdrive`
- **Type:** Google Drive
- **Path:** `reup-ytb/`

---

## 🔧 Cấu hình cần thiết

### 1. Cấu hình Schedule Trigger
Hiện tại trigger chưa được cấu hình chi tiết. Cần thiết lập:
- Interval (ví dụ: mỗi giờ, mỗi ngày)
- Timezone
- Start date/time

### 2. Cấu hình rclone
```bash
rclone config
# Tạo remote với tên "gdrive"
# Type: Google Drive
# Cấu hình OAuth hoặc Service Account
```

### 3. Cấu hình Google Sheets
- Đảm bảo credentials có quyền đọc/ghi sheet
- Sheet ID: `1-JdoLLwnsG4460c3BNS70jmZdDLKHelzZUWTG2g_BsI`
- Sheet GID: `1492578399`

---

## ⚠️ Lưu ý

1. **Workflow đang chạy**: ✅ Workflow đã được kích hoạt và đang hoạt động
2. **PHẦN 3 chưa triển khai**: Phần phân tích logo, nội dung, category chưa có node
3. **Xử lý lỗi**: Workflow chưa có error handling, cần thêm try-catch hoặc error nodes
4. **Dọn dẹp file**: Node "Clear video" xóa tất cả file `.mp4` trước khi tải, có thể gây mất dữ liệu nếu có nhiều workflow chạy song song
5. **Memory management**: Node "Remove Binary" giúp giải phóng bộ nhớ, nhưng cần đảm bảo không cần binary data sau đó
6. **Concurrency**: Workflow xử lý từng video một, có thể tối ưu để xử lý song song

---

## 🚀 Trạng thái hiện tại

✅ **Workflow đã được cấu hình và đang chạy**

### Đã hoàn thành:
1. ✅ Workflow đã được import và cấu hình
2. ✅ Credentials đã được thiết lập (Google Sheets, rclone)
3. ✅ Schedule Trigger đã được cấu hình
4. ✅ Workflow đã được kích hoạt và đang chạy tự động

### Giám sát workflow:
- **Kiểm tra execution history:** Xem trong n8n interface
- **Kiểm tra kết quả:** Theo dõi Google Sheets để xem các video đã được xử lý
- **Kiểm tra log:** Xem execution logs trong n8n để phát hiện lỗi
- **Kiểm tra rclone:**
  ```bash
  rclone lsd gdrive:reup-ytb
  ```

---

## 📝 Ghi chú phát triển

### Cần bổ sung:
- [ ] Error handling cho các node
- [ ] Retry mechanism cho download/upload
- [ ] PHẦN 3: Phân tích logo, nội dung, category
- [ ] Validation cho videoUrl format
- [ ] Logging chi tiết
- [ ] Notification khi hoàn thành/thất bại
- [ ] Xử lý song song nhiều video
- [ ] Cleanup tự động sau khi upload thành công

### Tối ưu hóa:
- Sử dụng queue system cho nhiều video
- Cache credentials để giảm API calls
- Compress video trước khi upload (nếu cần)
- Validate file size trước khi upload

---

## 📄 Thông tin kỹ thuật

- **Workflow ID:** `D71syQuOcFQ2EFVJ`
- **Version ID:** `af0edbd6-1a12-4736-8d51-c0b1d04d73bc`
- **Execution Order:** `v1`
- **Instance ID:** `85d7322ab387263001b31b703ad4747f32bd4ef2ff67525ffd22eeafb96c1d17`

---

**Tài liệu được tạo tự động từ workflow JSON**
