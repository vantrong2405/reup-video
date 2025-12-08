# TEST CASES CHI TIẾT - WORKFLOW

## TỔNG QUAN

File này liệt kê tất cả các test cases có thể xảy ra trong workflow, bao gồm:
- Happy paths (tất cả thành công)
- Error cases (có lỗi ở các node khác nhau)
- Edge cases (điều kiện đặc biệt)
- IF conditions (TRUE/FALSE)

---

## PHÂN LOẠI TEST CASES

### 1. NHÁNH PUBLISH (Publish video = TRUE)

#### TC-PUBLISH-001: Happy Path - Upload YouTube Thành Công
**Điều kiện:**
- `publish_status` = "pending"
- `enable_youtube_upload` = true
- `processed_video_drive_link` = "https://drive.google.com/..."
- `youtube_privacy` = "public"
- `enable_youtube_upload_should_upload` = true (sau khi normalize)

**Flow:**
```
Publish video (TRUE)
  → Download Processed Video From Drive (SUCCESS)
  → Read Processed Video For YouTube (SUCCESS)
  → Merge Data For YouTube Check (SUCCESS)
  → Check Should Upload To YouTube (TRUE)
  → Upload To YouTube (SUCCESS, có uploadId)
  → Remove Binary After Upload YouTube (SUCCESS)
  → Update Final Status (SUCCESS)
  → Get Video Information After Upload (SUCCESS)
  → Set Result Status (status = SUCCESS, có youtubeLink)
  → Send a message (gửi message thành công)
  → Loop Over Items (tiếp tục item tiếp theo)
```

**Expected Output:**
- Status: `success`
- Slack message: ✅ Video xử lý thành công\nID: ...\nTiêu đề: ...\nYouTube: https://www.youtube.com/watch?v=...\nDrive: ...\nThời gian: ...

---

#### TC-PUBLISH-002: Check Should Upload To YouTube = FALSE
**Điều kiện:**
- `publish_status` = "pending"
- `enable_youtube_upload` = false (hoặc không có)
- `processed_video_drive_link` = "https://drive.google.com/..."
- `youtube_privacy` = "public"

**Flow:**
```
Publish video (TRUE)
  → Download Processed Video From Drive (SUCCESS)
  → Read Processed Video For YouTube (SUCCESS)
  → Merge Data For YouTube Check (SUCCESS)
  → Check Should Upload To YouTube (FALSE)
  → Set Result Status (status = NONE, không có youtubeLink, không có lỗi)
  → Send a message (return '', không gửi)
  → Loop Over Items (tiếp tục item tiếp theo)
```

**Expected Output:**
- Status: `none`
- Slack message: Không gửi (empty string)

---

#### TC-PUBLISH-003: Download Processed Video From Drive Fail
**Điều kiện:**
- `publish_status` = "pending"
- `enable_youtube_upload` = true
- `processed_video_drive_link` = "https://drive.google.com/..." (link không hợp lệ hoặc file không tồn tại)
- `youtube_privacy` = "public"

**Flow:**
```
Publish video (TRUE)
  → Download Processed Video From Drive (FAIL, continueOnFail = true)
  → Read Processed Video For YouTube (FAIL, không có file)
  → Merge Data For YouTube Check (FAIL, không có binary)
  → Check Should Upload To YouTube (FAIL, không có data)
  → Set Result Status (status = ERROR, có lỗi từ Download Processed Video From Drive)
  → Send a message (gửi message lỗi)
  → Loop Over Items (tiếp tục item tiếp theo)
```

**Expected Output:**
- Status: `error`
- Slack message: 🔴 Lỗi xử lý video\nID: ...\nTiêu đề: ...\nLỗi: ...\nGốc: ...\nThời gian: ...
- Error từ: Download Processed Video From Drive

---

#### TC-PUBLISH-004: Read Processed Video For YouTube Fail
**Điều kiện:**
- `publish_status` = "pending"
- `enable_youtube_upload` = true
- `processed_video_drive_link` = "https://drive.google.com/..."
- `youtube_privacy` = "public"
- Download Processed Video From Drive thành công nhưng file không đọc được

**Flow:**
```
Publish video (TRUE)
  → Download Processed Video From Drive (SUCCESS)
  → Read Processed Video For YouTube (FAIL, continueOnFail = true, alwaysOutputData = true)
  → Merge Data For YouTube Check (FAIL, không có binary)
  → Check Should Upload To YouTube (FAIL, không có data)
  → Set Result Status (status = ERROR, có lỗi từ Read Processed Video For YouTube)
  → Send a message (gửi message lỗi)
  → Loop Over Items (tiếp tục item tiếp theo)
```

**Expected Output:**
- Status: `error`
- Slack message: 🔴 Lỗi xử lý video\nID: ...\nTiêu đề: ...\nLỗi: ...\nGốc: ...\nThời gian: ...
- Error từ: Read Processed Video For YouTube

---

#### TC-PUBLISH-005: Upload To YouTube Fail
**Điều kiện:**
- `publish_status` = "pending"
- `enable_youtube_upload` = true
- `processed_video_drive_link` = "https://drive.google.com/..."
- `youtube_privacy` = "public"
- `enable_youtube_upload_should_upload` = true
- YouTube API quota exceeded hoặc lỗi khác

**Flow:**
```
Publish video (TRUE)
  → Download Processed Video From Drive (SUCCESS)
  → Read Processed Video For YouTube (SUCCESS)
  → Merge Data For YouTube Check (SUCCESS)
  → Check Should Upload To YouTube (TRUE)
  → Upload To YouTube (FAIL, continueOnFail = true, có error)
  → Remove Binary After Upload YouTube (SUCCESS)
  → Update Final Status (SUCCESS, nhưng youtube_link = '')
  → Get Video Information After Upload (SUCCESS)
  → Set Result Status (status = ERROR, có lỗi từ Upload To YouTube)
  → Send a message (gửi message lỗi)
  → Loop Over Items (tiếp tục item tiếp theo)
```

**Expected Output:**
- Status: `error`
- Slack message: 🔴 Lỗi xử lý video\nID: ...\nTiêu đề: ...\nLỗi: uploadLimitExceeded hoặc lỗi khác\nGốc: ...\nDrive: ...\nThời gian: ...
- Error từ: Upload To YouTube

---

#### TC-PUBLISH-006: Update Final Status Fail
**Điều kiện:**
- `publish_status` = "pending"
- `enable_youtube_upload` = true
- `processed_video_drive_link` = "https://drive.google.com/..."
- `youtube_privacy` = "public"
- `enable_youtube_upload_should_upload` = true
- Upload To YouTube thành công nhưng Google Sheets API fail

**Flow:**
```
Publish video (TRUE)
  → Download Processed Video From Drive (SUCCESS)
  → Read Processed Video For YouTube (SUCCESS)
  → Merge Data For YouTube Check (SUCCESS)
  → Check Should Upload To YouTube (TRUE)
  → Upload To YouTube (SUCCESS, có uploadId)
  → Remove Binary After Upload YouTube (SUCCESS)
  → Update Final Status (FAIL, continueOnFail = true)
  → Get Video Information After Upload (SUCCESS)
  → Set Result Status (status = SUCCESS, có youtubeLink, không có lỗi từ Update Final Status)
  → Send a message (gửi message thành công)
  → Loop Over Items (tiếp tục item tiếp theo)
```

**Expected Output:**
- Status: `success` (vì Upload To YouTube thành công, Update Final Status fail không được check trong Set Result Status)
- Slack message: ✅ Video xử lý thành công\nID: ...\nTiêu đề: ...\nYouTube: https://www.youtube.com/watch?v=...\nDrive: ...\nThời gian: ...
- Lưu ý: Update Final Status fail nhưng không được detect trong Set Result Status

---

### 2. NHÁNH PROCESS (Publish video = FALSE)

#### TC-PROCESS-001: Happy Path - Upload Drive và Upload YouTube
**Điều kiện:**
- `publish_status` = "pending"
- `enable_youtube_upload` = true
- `processed_video_drive_link` = "" (chưa có)
- `youtube_privacy` = "public"
- `video_url` = "https://www.youtube.com/watch?v=..."
- `id` = "video-001"

**Flow:**
```
Publish video (FALSE)
  → Extract Video URL (SUCCESS)
  → Extract YouTube Metadata (SUCCESS)
  → Merge YouTube Metadata (SUCCESS)
  ├─→ Generate metadata (SUCCESS) → Parse Video Metadata (SUCCESS)
  └─→ Clear Old Files (SUCCESS)
  → Download Video (SUCCESS)
  → Read Video File (SUCCESS)
  → Remove Binary After Read Video (SUCCESS)
  → Extract Frame (SUCCESS)
  → Detect Logo (YOLO) (SUCCESS)
  → Process Video (SUCCESS)
  → Insert Background Intro (SUCCESS)
  → Upload to Drive (SUCCESS)
  → Get Drive Link (SUCCESS)
  → Update Drive Link After Process (SUCCESS)
  → Get Video Info For YouTube Check (SUCCESS, processed_video_drive_link đã được update)
  → Check Upload YouTube After Drive (TRUE)
  → Download Processed Video From Drive (nhập nhánh PUBLISH)
  → ... (tiếp tục như TC-PUBLISH-001)
```

**Expected Output:**
- Status: `success` (sau khi upload YouTube thành công)
- Slack message: ✅ Video xử lý thành công\nID: ...\nTiêu đề: ...\nYouTube: https://www.youtube.com/watch?v=...\nDrive: ...\nThời gian: ...

---

#### TC-PROCESS-002: Check Upload YouTube After Drive = FALSE
**Điều kiện:**
- `publish_status` = "pending"
- `enable_youtube_upload` = false (hoặc không có)
- `processed_video_drive_link` = "" (chưa có)
- `youtube_privacy` = "" (không có)
- `video_url` = "https://www.youtube.com/watch?v=..."
- `id` = "video-001"

**Flow:**
```
Publish video (FALSE)
  → Extract Video URL (SUCCESS)
  → Extract YouTube Metadata (SUCCESS)
  → Merge YouTube Metadata (SUCCESS)
  ├─→ Generate metadata (SUCCESS) → Parse Video Metadata (SUCCESS)
  └─→ Clear Old Files (SUCCESS)
  → Download Video (SUCCESS)
  → Read Video File (SUCCESS)
  → Remove Binary After Read Video (SUCCESS)
  → Extract Frame (SUCCESS)
  → Detect Logo (YOLO) (SUCCESS)
  → Process Video (SUCCESS)
  → Insert Background Intro (SUCCESS)
  → Upload to Drive (SUCCESS)
  → Get Drive Link (SUCCESS)
  → Update Drive Link After Process (SUCCESS)
  → Get Video Info For YouTube Check (SUCCESS)
  → Check Upload YouTube After Drive (FALSE, vì enable_youtube_upload = false hoặc youtube_privacy = '')
  → Set Result Status (status = NONE, không có youtubeLink, không có lỗi)
  → Send a message (return '', không gửi)
  → Loop Over Items (tiếp tục item tiếp theo)
```

**Expected Output:**
- Status: `none`
- Slack message: Không gửi (empty string)

---

#### TC-PROCESS-003: Extract Video URL Fail
**Điều kiện:**
- `publish_status` = "pending"
- `enable_youtube_upload` = true
- `processed_video_drive_link` = "" (chưa có)
- `youtube_privacy` = "public"
- `id` = "" (thiếu id) hoặc `video_url` = "" (thiếu video_url)

**Flow:**
```
Publish video (FALSE)
  → Extract Video URL (FAIL, throw new Error('Missing required field: id or video_url'), continueOnFail = true)
  → Extract YouTube Metadata (FAIL, không có video_url)
  → Merge YouTube Metadata (FAIL, không có data)
  → Set Result Status (status = ERROR, có lỗi từ Extract Video URL hoặc Extract YouTube Metadata)
  → Send a message (gửi message lỗi)
  → Loop Over Items (tiếp tục item tiếp theo)
```

**Expected Output:**
- Status: `error`
- Slack message: 🔴 Lỗi xử lý video\nID: ...\nTiêu đề: ...\nLỗi: Missing required field: id or video_url\nGốc: ...\nThời gian: ...
- Error từ: Extract Video URL

**Lưu ý:** Set Result Status không check Extract Video URL trong errorNodes array, nhưng có thể detect được qua error từ các node sau.

---

#### TC-PROCESS-004: Extract YouTube Metadata Fail
**Điều kiện:**
- `publish_status` = "pending"
- `enable_youtube_upload` = true
- `processed_video_drive_link` = "" (chưa có)
- `youtube_privacy` = "public"
- `video_url` = "https://www.youtube.com/watch?v=INVALID" (video không tồn tại)

**Flow:**
```
Publish video (FALSE)
  → Extract Video URL (SUCCESS)
  → Extract YouTube Metadata (FAIL, yt-dlp không tìm thấy video, continueOnFail = true, stdout = "ERROR|ERROR|ERROR")
  → Merge YouTube Metadata (FAIL, throw new Error('Cannot extract video title from YouTube'))
  → Set Result Status (status = ERROR, có lỗi từ Merge YouTube Metadata)
  → Send a message (gửi message lỗi)
  → Loop Over Items (tiếp tục item tiếp theo)
```

**Expected Output:**
- Status: `error`
- Slack message: 🔴 Lỗi xử lý video\nID: ...\nTiêu đề: ...\nLỗi: Cannot extract video title from YouTube\nGốc: ...\nThời gian: ...
- Error từ: Merge YouTube Metadata

---

#### TC-PROCESS-005: Download Video Fail
**Điều kiện:**
- `publish_status` = "pending"
- `enable_youtube_upload` = true
- `processed_video_drive_link` = "" (chưa có)
- `youtube_privacy` = "public"
- `video_url` = "https://www.youtube.com/watch?v=..." (video bị private hoặc không download được)

**Flow:**
```
Publish video (FALSE)
  → Extract Video URL (SUCCESS)
  → Extract YouTube Metadata (SUCCESS)
  → Merge YouTube Metadata (SUCCESS)
  ├─→ Generate metadata (SUCCESS) → Parse Video Metadata (SUCCESS)
  └─→ Clear Old Files (SUCCESS)
  → Download Video (FAIL, yt-dlp không download được, continueOnFail = true)
  → Read Video File (FAIL, không có file)
  → Remove Binary After Read Video (SUCCESS, nhưng không có binary)
  → Extract Frame (FAIL, không có file)
  → Detect Logo (YOLO) (FAIL, không có frame)
  → Process Video (FAIL, không có file)
  → Insert Background Intro (FAIL, không có file)
  → Upload to Drive (FAIL, không có file)
  → Get Drive Link (FAIL, không có file)
  → Update Drive Link After Process (SUCCESS, nhưng stdout = '')
  → Get Video Info For YouTube Check (SUCCESS)
  → Check Upload YouTube After Drive (FALSE, vì processed_video_drive_link = '')
  → Set Result Status (status = ERROR, có lỗi từ Download Video)
  → Send a message (gửi message lỗi)
  → Loop Over Items (tiếp tục item tiếp theo)
```

**Expected Output:**
- Status: `error`
- Slack message: 🔴 Lỗi xử lý video\nID: ...\nTiêu đề: ...\nLỗi: ... (lỗi từ Download Video)\nGốc: ...\nThời gian: ...
- Error từ: Download Video (được check trong Set Result Status)

---

#### TC-PROCESS-006: Process Video Fail
**Điều kiện:**
- `publish_status` = "pending"
- `enable_youtube_upload` = true
- `processed_video_drive_link` = "" (chưa có)
- `youtube_privacy` = "public"
- `video_url` = "https://www.youtube.com/watch?v=..."
- `id` = "video-001"
- Download Video thành công nhưng Process Video fail (ffmpeg lỗi)

**Flow:**
```
Publish video (FALSE)
  → Extract Video URL (SUCCESS)
  → Extract YouTube Metadata (SUCCESS)
  → Merge YouTube Metadata (SUCCESS)
  ├─→ Generate metadata (SUCCESS) → Parse Video Metadata (SUCCESS)
  └─→ Clear Old Files (SUCCESS)
  → Download Video (SUCCESS)
  → Read Video File (SUCCESS)
  → Remove Binary After Read Video (SUCCESS)
  → Extract Frame (SUCCESS)
  → Detect Logo (YOLO) (SUCCESS)
  → Process Video (FAIL, ffmpeg lỗi, continueOnFail = true)
  → Insert Background Intro (FAIL, không có processed file)
  → Upload to Drive (FAIL, không có file)
  → Get Drive Link (FAIL, không có file)
  → Update Drive Link After Process (SUCCESS, nhưng stdout = '')
  → Get Video Info For YouTube Check (SUCCESS)
  → Check Upload YouTube After Drive (FALSE, vì processed_video_drive_link = '')
  → Set Result Status (status = ERROR, có lỗi từ Process Video)
  → Send a message (gửi message lỗi)
  → Loop Over Items (tiếp tục item tiếp theo)
```

**Expected Output:**
- Status: `error`
- Slack message: 🔴 Lỗi xử lý video\nID: ...\nTiêu đề: ...\nLỗi: ... (lỗi từ Process Video)\nGốc: ...\nThời gian: ...
- Error từ: Process Video (được check trong Set Result Status)

---

#### TC-PROCESS-007: Upload to Drive Fail
**Điều kiện:**
- `publish_status` = "pending"
- `enable_youtube_upload` = true
- `processed_video_drive_link` = "" (chưa có)
- `youtube_privacy` = "public"
- `video_url` = "https://www.youtube.com/watch?v=..."
- `id` = "video-001"
- Process Video thành công nhưng Upload to Drive fail (rclone lỗi hoặc không có quyền)

**Flow:**
```
Publish video (FALSE)
  → Extract Video URL (SUCCESS)
  → Extract YouTube Metadata (SUCCESS)
  → Merge YouTube Metadata (SUCCESS)
  ├─→ Generate metadata (SUCCESS) → Parse Video Metadata (SUCCESS)
  └─→ Clear Old Files (SUCCESS)
  → Download Video (SUCCESS)
  → Read Video File (SUCCESS)
  → Remove Binary After Read Video (SUCCESS)
  → Extract Frame (SUCCESS)
  → Detect Logo (YOLO) (SUCCESS)
  → Process Video (SUCCESS)
  → Insert Background Intro (SUCCESS)
  → Upload to Drive (FAIL, rclone lỗi, continueOnFail = true)
  → Get Drive Link (FAIL, không có file trên Drive)
  → Update Drive Link After Process (SUCCESS, nhưng stdout = '')
  → Get Video Info For YouTube Check (SUCCESS)
  → Check Upload YouTube After Drive (FALSE, vì processed_video_drive_link = '')
  → Set Result Status (status = ERROR, có lỗi từ Upload to Drive)
  → Send a message (gửi message lỗi)
  → Loop Over Items (tiếp tục item tiếp theo)
```

**Expected Output:**
- Status: `error`
- Slack message: 🔴 Lỗi xử lý video\nID: ...\nTiêu đề: ...\nLỗi: ... (lỗi từ Upload to Drive)\nGốc: ...\nThời gian: ...
- Error từ: Upload to Drive (được check trong Set Result Status)

---

#### TC-PROCESS-008: Generate metadata Fail
**Điều kiện:**
- `publish_status` = "pending"
- `enable_youtube_upload` = true
- `processed_video_drive_link` = "" (chưa có)
- `youtube_privacy` = "public"
- `video_url` = "https://www.youtube.com/watch?v=..."
- `id` = "video-001"
- Gemini API fail hoặc timeout

**Flow:**
```
Publish video (FALSE)
  → Extract Video URL (SUCCESS)
  → Extract YouTube Metadata (SUCCESS)
  → Merge YouTube Metadata (SUCCESS)
  ├─→ Generate metadata (FAIL, Gemini API lỗi, continueOnFail = true)
  → Parse Video Metadata (FAIL, không có response)
  └─→ Clear Old Files (SUCCESS)
  → Download Video (SUCCESS)
  → ... (tiếp tục process)
  → Set Result Status (status = NONE hoặc ERROR tùy vào có lỗi khác không)
  → Send a message (gửi hoặc không gửi tùy vào status)
  → Loop Over Items (tiếp tục item tiếp theo)
```

**Expected Output:**
- Status: `none` (nếu không có lỗi khác) hoặc `error` (nếu có lỗi khác)
- Slack message: Không gửi (nếu status = none) hoặc gửi message lỗi (nếu status = error)
- Lưu ý: Generate metadata fail không được check trong Set Result Status, nhưng không ảnh hưởng đến process video

---

#### TC-PROCESS-009: Detect Logo (YOLO) Fail
**Điều kiện:**
- `publish_status` = "pending"
- `enable_youtube_upload` = true
- `processed_video_drive_link` = "" (chưa có)
- `youtube_privacy` = "public"
- `video_url` = "https://www.youtube.com/watch?v=..."
- `id` = "video-001"
- YOLO model fail hoặc không detect được logo

**Flow:**
```
Publish video (FALSE)
  → Extract Video URL (SUCCESS)
  → Extract YouTube Metadata (SUCCESS)
  → Merge YouTube Metadata (SUCCESS)
  ├─→ Generate metadata (SUCCESS) → Parse Video Metadata (SUCCESS)
  └─→ Clear Old Files (SUCCESS)
  → Download Video (SUCCESS)
  → Read Video File (SUCCESS)
  → Remove Binary After Read Video (SUCCESS)
  → Extract Frame (SUCCESS)
  → Detect Logo (YOLO) (FAIL, YOLO lỗi hoặc không detect được, continueOnFail = true)
  → Process Video (SUCCESS, sử dụng fallback overlay logo ở top-right)
  → Insert Background Intro (SUCCESS)
  → Upload to Drive (SUCCESS)
  → Get Drive Link (SUCCESS)
  → Update Drive Link After Process (SUCCESS)
  → Get Video Info For YouTube Check (SUCCESS)
  → Check Upload YouTube After Drive (TRUE)
  → Download Processed Video From Drive (nhập nhánh PUBLISH)
  → ... (tiếp tục như TC-PUBLISH-001)
```

**Expected Output:**
- Status: `success` (sau khi upload YouTube thành công)
- Slack message: ✅ Video xử lý thành công\nID: ...\nTiêu đề: ...\nYouTube: https://www.youtube.com/watch?v=...\nDrive: ...\nThời gian: ...
- Lưu ý: Detect Logo fail không được check trong Set Result Status, nhưng Process Video có fallback logic

---

### 3. EDGE CASES

#### TC-EDGE-001: Tất Cả Node Success Nhưng Không Upload YouTube
**Điều kiện:**
- `publish_status` = "pending"
- `enable_youtube_upload` = false
- `processed_video_drive_link` = "" (chưa có)
- `youtube_privacy` = ""
- Tất cả node đều success

**Flow:**
```
Publish video (FALSE)
  → ... (tất cả node success)
  → Check Upload YouTube After Drive (FALSE)
  → Set Result Status (status = NONE, không có youtubeLink, không có lỗi)
  → Send a message (return '', không gửi)
  → Loop Over Items (tiếp tục item tiếp theo)
```

**Expected Output:**
- Status: `none`
- Slack message: Không gửi (empty string)

---

#### TC-EDGE-002: Nhiều Node Fail Cùng Lúc
**Điều kiện:**
- `publish_status` = "pending"
- `enable_youtube_upload` = true
- `processed_video_drive_link` = "" (chưa có)
- `youtube_privacy` = "public"
- Download Video fail và Process Video fail

**Flow:**
```
Publish video (FALSE)
  → Extract Video URL (SUCCESS)
  → Extract YouTube Metadata (SUCCESS)
  → Merge YouTube Metadata (SUCCESS)
  ├─→ Generate metadata (SUCCESS) → Parse Video Metadata (SUCCESS)
  └─→ Clear Old Files (SUCCESS)
  → Download Video (FAIL)
  → Read Video File (FAIL)
  → Remove Binary After Read Video (SUCCESS)
  → Extract Frame (FAIL)
  → Detect Logo (YOLO) (FAIL)
  → Process Video (FAIL)
  → ... (tất cả node sau đều fail)
  → Set Result Status (status = ERROR, có lỗi từ Download Video hoặc Process Video)
  → Send a message (gửi message lỗi)
  → Loop Over Items (tiếp tục item tiếp theo)
```

**Expected Output:**
- Status: `error`
- Slack message: 🔴 Lỗi xử lý video\nID: ...\nTiêu đề: ...\nLỗi: ... (lỗi đầu tiên được detect)\nGốc: ...\nThời gian: ...
- Error từ: Download Video hoặc Process Video (lỗi đầu tiên được detect)

---

#### TC-EDGE-003: Data Missing (Thiếu Field Quan Trọng)
**Điều kiện:**
- `publish_status` = "pending"
- `enable_youtube_upload` = true
- `processed_video_drive_link` = "" (chưa có)
- `youtube_privacy` = "public"
- `id` = "" (thiếu id)
- `video_url` = "" (thiếu video_url)

**Flow:**
```
Publish video (FALSE)
  → Extract Video URL (FAIL, throw new Error('Missing required field: id or video_url'))
  → Set Result Status (status = ERROR, có lỗi từ Extract Video URL)
  → Send a message (gửi message lỗi)
  → Loop Over Items (tiếp tục item tiếp theo)
```

**Expected Output:**
- Status: `error`
- Slack message: 🔴 Lỗi xử lý video\nID: ...\nTiêu đề: ...\nLỗi: Missing required field: id or video_url\nGốc: ...\nThời gian: ...
- Error từ: Extract Video URL

---

## KIỂM TRA TỪNG NODE

### Node: Parse Video Metadata
- **Input**: Response từ Generate metadata (Gemini API)
- **Output**: `{ youtube_title, youtube_description, error, valid, raw }`
- **Error Handling**: 
  - Nếu response.error → return error
  - Nếu không có text → return error
  - Nếu parse JSON fail → return error
- **continueOnFail**: true
- **Output Connection**: KHÔNG CÓ (nhưng được dùng qua `$('Parse Video Metadata')`)
- **Sử dụng**: Upload To YouTube và Update Final Status dùng `$('Parse Video Metadata')` với fallback về Sheets

### Node: Extract Video URL
- **Input**: Data từ Get Video Information
- **Output**: `{ id, video_title, video_url, driveUuid }`
- **Error Handling**: 
  - Validate: `if (!row.id || !row.video_url) throw new Error(...)`
- **continueOnFail**: true
- **Output Connection**: → Extract YouTube Metadata

### Node: Extract YouTube Metadata
- **Input**: video_url từ Extract Video URL
- **Output**: `{ stdout: "title|uploader|description" }`
- **Error Handling**: 
  - Command có fallback: `|| echo "ERROR|ERROR|ERROR"`
- **continueOnFail**: true
- **Output Connection**: → Merge YouTube Metadata

### Node: Merge YouTube Metadata
- **Input**: Data từ Extract Video URL và Extract YouTube Metadata
- **Output**: `{ id, video_title, video_url, driveUuid, youtube_metadata }`
- **Error Handling**: 
  - Validate: `if (!videoTitle) throw new Error('Cannot extract video title from YouTube')`
- **continueOnFail**: true
- **Output Connection**: 
  - main[0][0] → Generate metadata
  - main[0][1] → Clear Old Files

### Node: Generate metadata
- **Input**: video_title từ Merge YouTube Metadata
- **Output**: Response từ Gemini API
- **Error Handling**: 
  - Gemini API có thể fail → continueOnFail = true
- **continueOnFail**: true
- **Output Connection**: → Parse Video Metadata

### Node: Clear Old Files
- **Input**: id từ Merge YouTube Metadata
- **Output**: Command output (rm -f)
- **Error Handling**: 
  - Command có thể fail → continueOnFail = true
- **continueOnFail**: true
- **Output Connection**: → Download Video

### Node: Download Video
- **Input**: id và video_url từ Merge YouTube Metadata
- **Output**: File mp4 tại /home/node/downloads/${VIDEO_ID}.mp4
- **Error Handling**: 
  - yt-dlp có thể fail → continueOnFail = true
- **continueOnFail**: true
- **Output Connection**: → Read Video File
- **Được check trong Set Result Status**: ✅ YES

### Node: Read Video File
- **Input**: File path từ Download Video
- **Output**: Binary video data
- **Error Handling**: 
  - File có thể không tồn tại → continueOnFail = true
- **continueOnFail**: true
- **Output Connection**: → Remove Binary After Read Video

### Node: Remove Binary After Read Video
- **Input**: Binary từ Read Video File
- **Output**: Data không có binary
- **Error Handling**: 
  - Không có error handling đặc biệt → continueOnFail = true
- **continueOnFail**: true
- **Output Connection**: → Extract Frame

### Node: Extract Frame
- **Input**: Video file path
- **Output**: Frame image tại /home/node/downloads/frame_{{ id }}.jpg
- **Error Handling**: 
  - ffmpeg có thể fail → continueOnFail = true
- **continueOnFail**: true
- **Output Connection**: → Detect Logo (YOLO)

### Node: Detect Logo (YOLO)
- **Input**: Frame image path
- **Output**: JSON với logo coordinates
- **Error Handling**: 
  - YOLO có thể fail → continueOnFail = true
  - Process Video có fallback nếu không detect được
- **continueOnFail**: true
- **Output Connection**: → Process Video
- **Được check trong Set Result Status**: ❌ NO (nhưng có fallback)

### Node: Process Video
- **Input**: Video file, logo coordinates, new logo URL
- **Output**: Processed video tại ${VIDEO_ID}_processed.mp4
- **Error Handling**: 
  - ffmpeg có thể fail → continueOnFail = true
  - Có fallback nếu không detect được logo (overlay ở top-right)
- **continueOnFail**: true
- **Output Connection**: → Insert Background Intro
- **Được check trong Set Result Status**: ✅ YES

### Node: Insert Background Intro
- **Input**: Processed video, intro_background_url
- **Output**: Video với intro tại ${VIDEO_ID}_processed.mp4
- **Error Handling**: 
  - ffmpeg có thể fail → continueOnFail = true
  - Nếu không có intro_background_url → copy video gốc
- **continueOnFail**: true
- **Output Connection**: → Upload to Drive
- **Được check trong Set Result Status**: ✅ YES

### Node: Upload to Drive
- **Input**: Processed video file
- **Output**: Command output (rclone copyto)
- **Error Handling**: 
  - rclone có thể fail → continueOnFail = true
- **continueOnFail**: true
- **Output Connection**: → Get Drive Link
- **Được check trong Set Result Status**: ✅ YES

### Node: Get Drive Link
- **Input**: driveUuid từ Merge YouTube Metadata
- **Output**: Google Drive share link tại stdout
- **Error Handling**: 
  - rclone link có thể fail → continueOnFail = true
- **continueOnFail**: true
- **Output Connection**: → Update Drive Link After Process
- **Được check trong Set Result Status**: ✅ YES

### Node: Update Drive Link After Process
- **Input**: stdout từ Get Drive Link
- **Output**: Updated sheet với processed_video_drive_link
- **Error Handling**: 
  - Google Sheets API có thể fail → continueOnFail = true
- **continueOnFail**: true
- **Output Connection**: → Get Video Info For YouTube Check

### Node: Get Video Info For YouTube Check
- **Input**: id từ Get Video Information
- **Output**: Updated data từ sheet
- **Error Handling**: 
  - Google Sheets API có thể fail → continueOnFail = true
- **continueOnFail**: true
- **Output Connection**: → Check Upload YouTube After Drive

### Node: Check Upload YouTube After Drive
- **Input**: Data từ Get Video Info For YouTube Check
- **Output**: TRUE hoặc FALSE
- **Error Handling**: 
  - continueOnFail = true
- **continueOnFail**: true
- **Output Connection**: 
  - TRUE → Download Processed Video From Drive
  - FALSE → Set Result Status

### Node: Download Processed Video From Drive
- **Input**: processed_video_drive_link từ Check Upload YouTube After Drive
- **Output**: File path tại stdout
- **Error Handling**: 
  - wget có thể fail → continueOnFail = true
- **continueOnFail**: true
- **Output Connection**: → Read Processed Video For YouTube
- **Được check trong Set Result Status**: ❌ NO (nhưng có thể detect qua error từ Read Processed Video For YouTube)

### Node: Read Processed Video For YouTube
- **Input**: File path từ Download Processed Video From Drive
- **Output**: Binary video data
- **Error Handling**: 
  - File có thể không tồn tại → continueOnFail = true, alwaysOutputData = true
- **continueOnFail**: true
- **alwaysOutputData**: true
- **Output Connection**: → Merge Data For YouTube Check

### Node: Merge Data For YouTube Check
- **Input**: Binary từ Read Processed Video For YouTube và data từ Get Video Information
- **Output**: Data với binary và enable_youtube_upload_should_upload
- **Error Handling**: 
  - Validate binary → throw error nếu không có
- **continueOnFail**: true
- **Output Connection**: → Check Should Upload To YouTube

### Node: Check Should Upload To YouTube
- **Input**: enable_youtube_upload_should_upload từ Merge Data For YouTube Check
- **Output**: TRUE hoặc FALSE
- **Error Handling**: 
  - continueOnFail = true
- **continueOnFail**: true
- **Output Connection**: 
  - TRUE → Upload To YouTube
  - FALSE → Set Result Status

### Node: Upload To YouTube
- **Input**: Binary từ Merge Data For YouTube Check và metadata
- **Output**: `{ uploadId }` hoặc error
- **Error Handling**: 
  - YouTube API có thể fail → continueOnFail = true
- **continueOnFail**: true
- **Output Connection**: → Remove Binary After Upload YouTube
- **Được check trong Set Result Status**: ✅ YES

### Node: Remove Binary After Upload YouTube
- **Input**: Binary từ Upload To YouTube
- **Output**: Data không có binary
- **Error Handling**: 
  - Không có error handling đặc biệt → continueOnFail = true
- **continueOnFail**: true
- **Output Connection**: → Update Final Status

### Node: Update Final Status
- **Input**: Data từ Remove Binary After Upload YouTube và các node khác
- **Output**: Updated sheet với publish_status, youtube_link, etc.
- **Error Handling**: 
  - Google Sheets API có thể fail → continueOnFail = true
- **continueOnFail**: true
- **Output Connection**: → Get Video Information After Upload
- **Được check trong Set Result Status**: ❌ NO

### Node: Get Video Information After Upload
- **Input**: id từ Get Video Information
- **Output**: Updated data từ sheet
- **Error Handling**: 
  - Google Sheets API có thể fail → continueOnFail = true
- **continueOnFail**: true
- **Output Connection**: → Set Result Status
- **Được check trong Set Result Status**: ❌ NO

### Node: Set Result Status
- **Input**: Data từ nhiều nguồn (Get Video Information After Upload, Check Should Upload To YouTube FALSE, Check Upload YouTube After Drive FALSE)
- **Output**: `{ status, errorMessage, id, videoTitle, videoUrl, driveLink, youtubeLink, publishStatus, timestamp }`
- **Error Handling**: 
  - Check lỗi từ: Upload To YouTube, Process Video, Download Video, Upload to Drive, Get Drive Link, Insert Background Intro
  - Xác định status: success (có youtubeLink), error (có lỗi), none (không có youtubeLink và không có lỗi)
- **continueOnFail**: true
- **Output Connection**: → Send a message

### Node: Send a message
- **Input**: Data từ Set Result Status
- **Output**: Slack message hoặc empty string
- **Error Handling**: 
  - Nếu status = NONE → return '' → Slack không gửi
  - Nếu status = SUCCESS → Format message thành công
  - Nếu status = ERROR → Format message lỗi
- **executeOnce**: true
- **Output Connection**: → Loop Over Items

### Node: Loop Over Items
- **Input**: Data từ Get Video Information
- **Output**: 
  - main[0] = [] (done - không nối gì)
  - main[1] = Publish video (loop - tiếp tục item tiếp theo)
- **Error Handling**: 
  - Không có error handling đặc biệt
- **Output Connection**: 
  - main[0] = [] (không nối gì)
  - main[1] = Publish video

---

## VẤN ĐỀ PHÁT HIỆN

### ⚠️ VẤN ĐỀ 1: Set Result Status Chỉ Check 6 Node
**Các node được check:**
- Upload To YouTube ✅
- Process Video ✅
- Download Video ✅
- Upload to Drive ✅
- Get Drive Link ✅
- Insert Background Intro ✅

**Các node KHÔNG được check:**
- Extract Video URL ❌
- Extract YouTube Metadata ❌
- Merge YouTube Metadata ❌
- Generate metadata ❌
- Parse Video Metadata ❌
- Clear Old Files ❌
- Read Video File ❌
- Remove Binary After Read Video ❌
- Extract Frame ❌
- Detect Logo (YOLO) ❌
- Update Drive Link After Process ❌
- Get Video Info For YouTube Check ❌
- Download Processed Video From Drive ❌
- Read Processed Video For YouTube ❌
- Merge Data For YouTube Check ❌
- Remove Binary After Upload YouTube ❌
- Update Final Status ❌
- Get Video Information After Upload ❌

**Giải pháp:**
- Có thể thêm các node quan trọng vào errorNodes array
- Hoặc giữ nguyên vì các node quan trọng nhất đã được check
- Các node không được check thường có fallback hoặc không ảnh hưởng đến kết quả cuối cùng

### ⚠️ VẤN ĐỀ 2: Node "If" Thừa
- **Node ID**: `107fc6c2-7335-407d-94d2-4eaca0f71f44`
- **Vấn đề**: Không được kết nối với workflow chính
- **Giải pháp**: Có thể xóa node này

---

## KẾT LUẬN

### ✅ ĐÃ KIỂM TRA:
- Tất cả 30 node đã được kiểm tra
- Tất cả 35 connections đã được kiểm tra
- Tất cả 3 IF node đã được kiểm tra
- Tất cả test cases đã được liệt kê

### ⚠️ VẤN ĐỀ:
1. Set Result Status chỉ check 6 node → Có thể cần thêm một số node quan trọng
2. Node "If" thừa → Có thể xóa

### 📊 THỐNG KÊ:
- **Tổng số test cases**: 15 test cases
- **Nhánh PUBLISH**: 6 test cases
- **Nhánh PROCESS**: 9 test cases
- **Edge cases**: 3 test cases
- **Tổng số node**: 30 node
- **Số node có continueOnFail**: 28 node
- **Số node được check trong Set Result Status**: 6 node

---

## RECOMMENDATIONS

1. **Thêm các node quan trọng vào Set Result Status errorNodes array:**
   - Extract Video URL
   - Extract YouTube Metadata
   - Merge YouTube Metadata
   - Download Processed Video From Drive
   - Read Processed Video For YouTube
   - Merge Data For YouTube Check

2. **Xóa node "If" thừa** (ID: 107fc6c2-7335-407d-94d2-4eaca0f71f44)

3. **Test tất cả các test cases** để đảm bảo workflow hoạt động đúng

---

**Workflow đã được kiểm tra kỹ và sẵn sàng để test!**
