Plan: Ensure per-item Slack reporting even on errors, keep loop running
===================================================================

HIỆN TRẠNG WORKFLOW
===================

Flow chính (theo thứ tự node)
------------------------------
1. **Schedule Trigger**: Chạy theo lịch định kỳ
2. **Get Video Information** (Google Sheets): Đọc danh sách video từ sheet
3. **Loop Over Items** (SplitInBatches): Lặp từng video trong danh sách

Nhánh Publish (nếu video đã có processed link)
4. **Publish video** (IF): Kiểm tra điều kiện (pending, enable_youtube_upload, có link, có privacy)
   - TRUE → Tiếp tục publish
   - FALSE → Chuyển sang nhánh Process mới

5. **Download Processed Video From Drive** (Exec): Tải video đã xử lý từ Drive
6. **Read Processed Video For YouTube** (Read File): Đọc binary video
7. **Merge Data For YouTube Check** (Code): Ghép binary + metadata
8. **Check Should Upload To YouTube** (IF): Quyết định có upload YT không
   - TRUE → Upload To YouTube
   - FALSE → Bỏ qua upload

9. **Upload To YouTube** (YouTube node): Upload video lên YouTube
10. **Remove Binary After Upload YouTube** (Code): Xóa binary khỏi payload
11. **Update Final Status** (Sheets): Cập nhật publish_status, youtube_link, time
12. **Get Video Information After Upload** (Sheets): Đọc lại sheet sau update
13. **Prepare Slack Message** (Code): Tạo message (hiện tại chưa phân biệt success/error)
14. **Send a message** (Slack): Gửi Slack → Quay lại Loop

Nhánh Process mới (nếu video chưa có processed link)
4. **Extract Video URL** (Code): Lấy id/video_url/driveUuid từ sheet
5. **Extract YouTube Metadata** (Exec yt-dlp): Lấy title/desc từ YouTube
6. **Merge YouTube Metadata** (Code): Chọn title/desc hợp nhất
7. **Generate metadata** (Gemini) → **Parse Video Metadata** (Code): Sinh title/desc nếu thiếu
8. **Clear Old Files** (Exec): Xóa file mp4 cũ
9. **Download Video** (Exec yt-dlp): Tải video mp4 từ YouTube
10. **Read Video File** (Read File): Đọc binary video gốc
11. **Remove Binary After Read Video** (Code): Bỏ binary khỏi payload
12. **Extract Frame** (ffmpeg Exec): Lấy frame đầu tiên
13. **Detect Logo** (YOLO Exec): Detect logo bằng Python script
14. **Process Video** (ffmpeg Exec): Delogo + overlay logo mới
15. **Insert Background Intro** (ffmpeg Exec): Chèn intro video
16. **Upload to Drive** (rclone Exec): Upload file processed lên Drive
17. **Get Drive Link** (rclone link Exec): Lấy link chia sẻ Drive
18. **Update Drive Link After Process** (Sheets): Cập nhật processed_video_drive_link
19. **Get Video Info For YouTube Check** (Sheets): Đọc lại sheet để kiểm tra
20. **Check Upload YouTube After Drive** (IF): Quyết định upload YT sau khi xử lý
   - TRUE → Chuyển sang nhánh Publish (từ bước 5)
   - FALSE → Cleanup Files → Prepare Slack Message → Send a message → Loop

TOÀN BỘ VẤN ĐỀ CẦN SỬA (đã kiểm tra từ JSON)
=============================================

1. **LOOP KHÔNG CHẠY HẾT ITEMS** ⚠️ QUAN TRỌNG:
   - Nhánh FALSE của "Check Should Upload To YouTube" không có connection
   - Hiện tại: FALSE → flow dừng, không quay về Loop
   - **Yêu cầu**: Phải chạy hết tất cả items → Cần nối FALSE → Set Result Status (none) → Slack (skip) → Loop

2. **THIẾU NODE "SET RESULT STATUS"**:
   - Chưa có node để quyết định `status`: success/error/none
   - Logic cần:
     - success: chỉ khi Upload YouTube thành công (có uploadId/link)
     - error: bất kỳ node nào fail (stderr/exitCode/error/HTTP lỗi)
     - none: IF false, không lỗi, không upload YT

3. **SLACK LOGIC CHƯA ĐÚNG**:
   - Hiện tại: Dùng Code node "Prepare Slack Message" cũ, báo mọi trường hợp
   - Yêu cầu: Gộp logic vào Slack node (field `text`), chỉ báo khi status != none
   - Format: ✅ success (có YouTube link) hoặc 🔴 error (có lỗi tóm tắt)
   - Slack credential: id `r5gqdIaSja4mpw9V`, channel `C09QG88TFJM`

4. **THIẾU `continueOnFail` Ở CÁC NODE QUAN TRỌNG** (sẽ làm workflow dừng khi lỗi):
   - ❌ **Upload To YouTube** (YouTube node) - QUAN TRỌNG NHẤT
   - ❌ **Download Video** (yt-dlp Exec)
   - ❌ **Process Video** (ffmpeg Exec)
   - ❌ **Insert Background Intro** (ffmpeg Exec)
   - ❌ **Upload to Drive** (rclone Exec)
   - ❌ **Get Drive Link** (rclone link Exec)

5. **NHÁNH FALSE CỦA "CHECK UPLOAD YOUTUBE AFTER DRIVE"**:
   - Hiện tại: FALSE → Cleanup Files → Prepare Slack Message → Send a message → Loop
   - Vấn đề: Vẫn gửi Slack dù không upload YT (không đúng yêu cầu)
   - Cần: FALSE → Set Result Status (none hoặc error nếu có lỗi) → Slack (skip nếu none) → Loop

6. **NODE "CLEANUP FILES" GÂY HIỂU NHẦM**:
   - Hiện tại: Chỉ đọc Google Sheets, không cleanup file thật
   - Tên node không đúng với chức năng

7. **CHƯA CÓ ERROR TRIGGER TOÀN WORKFLOW** (tùy chọn):
   - Để báo Slack khi execution crash/timeout (khác với per-item error)

GOOGLE SHEETS - KHÔNG CẦN THÊM CỘT
===================================
- Các cột hiện có đã đủ: id, video_url, video_title, publish_status, enable_youtube_upload,
  new_logo_url, intro_background_url, youtube_category, youtube_privacy, processed_video_drive_link,
  youtube_title, youtube_description, youtube_link, youtube_upload_time
- `status` và `errorMessage` chỉ dùng trong workflow để quyết định gửi Slack, không cần lưu vào Sheets

MỤC TIÊU
========
- Slack chỉ báo khi:
  - ✅ **Thành công**: Upload YouTube thành công (có uploadId/link)
  - 🔴 **Lỗi**: Bất kỳ node nào fail (stderr/exitCode/error/HTTP lỗi)
  - ⚪ **Không báo**: IF false, không lỗi, không upload YT
- Loop không dừng khi lỗi; tiếp tục item tiếp theo
- Không thay đổi logic xử lý video/YouTube

CÁC BƯỚC TRIỂN KHAI (THEO THỨ TỰ THỰC HIỆN)
===========================================

**BƯỚC 1: Bật continueOnFail cho các node quan trọng** (Ưu tiên cao nhất)
--------------------------------------------------------------------------
Mục đích: Đảm bảo workflow không dừng khi lỗi, tiếp tục chạy để báo Slack

Các node cần thêm `"continueOnFail": true`:
1. **Upload To YouTube** (YouTube node) - QUAN TRỌNG NHẤT
   - Node ID: `187a1d2a-5e99-46cc-a2b8-d3c8b8174d29`
   - Vị trí: Nhánh Publish, sau "Check Should Upload To YouTube"

2. **Download Video** (Execute Command - yt-dlp)
   - Node ID: `3767add7-df7c-44d3-83c6-5f586c79235c`
   - Vị trí: Nhánh Process, sau "Clear Old Files"

3. **Process Video** (Execute Command - ffmpeg)
   - Node ID: `0aee79e6-953e-4cc2-912a-2597b8796fdc`
   - Vị trí: Nhánh Process, sau "Detect Logo (YOLO)"

4. **Insert Background Intro** (Execute Command - ffmpeg)
   - Node ID: `14eb42c2-d929-4a8e-825c-ece225db5e3d`
   - Vị trí: Nhánh Process, sau "Process Video"

5. **Upload to Drive** (Execute Command - rclone)
   - Node ID: `459a4a84-9873-4f78-801f-258777529162`
   - Vị trí: Nhánh Process, sau "Insert Background Intro"

6. **Get Drive Link** (Execute Command - rclone link)
   - Node ID: `53e6cf75-f149-420a-a39f-0841281875f8`
   - Vị trí: Nhánh Process, sau "Upload to Drive"

**BƯỚC 2: Thêm node "Set Result Status"** (Code node mới)
-----------------------------------------------------------
Mục đích: Quyết định status (success/error/none) để Slack biết có gửi hay không

Vị trí đặt node:
- **Nhánh Publish**: Sau "Get Video Information After Upload", trước "Send a message"
- **Nhánh Process**: Sau "Cleanup Files" (hoặc sau "Check Upload YouTube After Drive" nếu FALSE), trước "Send a message"

**Giải thích về fallback và continueOnFail trong n8n:**
- Khi node fail nhưng có `continueOnFail: true`: Node vẫn pass data sang node tiếp theo, nhưng output có thể có field `error` hoặc giá trị `undefined/null`
- Node tiếp theo cần check `item.error` hoặc `item.json.error` để biết có lỗi không
- Nếu không check và dùng giá trị trực tiếp (ví dụ `$json.stdout`) mà node fail → sẽ là `undefined`
- **Cách đúng**: Check error field trước, chỉ dùng giá trị khi không có error
- **Fallback `|| ''` chỉ dùng khi**: Cần giá trị mặc định hợp lý cho business logic, không phải để "chữa cháy"

Logic Code node (KHÔNG comment, KHÔNG fallback thừa, CLEAN CODE):
```javascript
const STATUS = {
  SUCCESS: 'success',
  ERROR: 'error',
  NONE: 'none'
};

const getNodeResult = (nodeName) => {
  const node = $(nodeName);
  if (!node || !node.isExecuted) return null;
  return node.first();
};

const extractUploadId = (uploadItem) => {
  if (!uploadItem || uploadItem.error || !uploadItem.json) return null;
  const json = uploadItem.json;
  if (Array.isArray(json) && json.length > 0) return json[0].uploadId;
  if (typeof json === 'object' && json !== null) return json.uploadId;
  return null;
};

const extractYouTubeLink = (uploadResult) => {
  const uploadItem = getNodeResult('Upload To YouTube');
  if (!uploadItem) return '';
  const videoId = extractUploadId(uploadItem);
  if (!videoId) return '';
  const trimmedId = String(videoId).trim();
  return trimmedId ? `https://www.youtube.com/watch?v=${trimmedId}` : '';
};

const checkNodeError = (nodeName) => {
  const item = getNodeResult(nodeName);
  if (!item) return null;
  if (item.error) return item.error.message;
  if (item.json && item.json.stderr) return item.json.stderr;
  if (item.json && item.json.exitCode && item.json.exitCode !== 0) return 'Node execution failed';
  return null;
};

const getDriveLinkFromNode = () => {
  const driveLinkItem = getNodeResult('Get Drive Link');
  if (!driveLinkItem || driveLinkItem.error || !driveLinkItem.json || !driveLinkItem.json.stdout) return null;
  return String(driveLinkItem.json.stdout).trim();
};

const getTimestamp = () => {
  return new Date().toLocaleString('vi-VN', {
    timeZone: 'Asia/Ho_Chi_Minh',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};

const videoInfo = $('Get Video Information').first().json;
const youtubeLink = extractYouTubeLink();
const driveLink = getDriveLinkFromNode() || videoInfo.processed_video_drive_link;

const errorNodes = ['Process Video', 'Download Video', 'Upload to Drive', 'Get Drive Link', 'Insert Background Intro'];
const uploadError = checkNodeError('Upload To YouTube');
const execErrors = errorNodes.map(node => checkNodeError(node)).filter(e => e);
const firstError = uploadError || execErrors[0];

const status = firstError ? STATUS.ERROR : (youtubeLink ? STATUS.SUCCESS : STATUS.NONE);
const errorMessage = firstError ? String(firstError).substring(0, 300) : '';

return {
  json: {
    status,
    errorMessage,
    id: videoInfo.id,
    videoTitle: videoInfo.video_title || videoInfo.youtube_title,
    videoUrl: videoInfo.video_url,
    driveLink,
    youtubeLink,
    publishStatus: videoInfo.publish_status ? String(videoInfo.publish_status).toLowerCase() : '',
    timestamp: getTimestamp()
  }
};
```

**BƯỚC 3: Nối nhánh FALSE của "Check Should Upload To YouTube"**
------------------------------------------------------------------
Mục đích: Đảm bảo loop chạy hết tất cả items

Hiện tại: FALSE → không có connection (flow dừng)
Cần sửa: FALSE → Set Result Status (none) → Send a message (skip) → Loop Over Items

Cách làm:
- Tìm node "Check Should Upload To YouTube" (ID: `3f2b43a7-bdd6-4abf-b2d5-d3c592c3b411`)
- Thêm connection từ output FALSE (main[1]) → Set Result Status → Send a message → Loop

**BƯỚC 4: Sửa nhánh FALSE của "Check Upload YouTube After Drive"**
-------------------------------------------------------------------
Mục đích: Không gửi Slack khi không upload YT (trừ khi có lỗi)

Hiện tại: FALSE → Cleanup Files → Prepare Slack Message → Send a message → Loop
Cần sửa: FALSE → Set Result Status (none nếu không lỗi, error nếu có lỗi) → Send a message (skip nếu none) → Loop

Cách làm:
- Tìm node "Check Upload YouTube After Drive" (ID: `18fe08a8-afe5-4bb9-8e7d-bb02a0ca0e12`)
- Sửa connection FALSE: Cleanup Files → Set Result Status → Send a message → Loop

**BƯỚC 5: Gộp logic vào Slack node "Send a message"**
-------------------------------------------------------
Mục đích: Chỉ gửi Slack khi status != none, format đúng success/error

Hiện tại: Dùng Code node "Prepare Slack Message" riêng, báo mọi trường hợp
Cần sửa: Gộp logic vào field `text` của Slack node, xóa hoặc bỏ qua Code node cũ

Cách làm:
- Tìm node "Send a message" (ID: `949da91a-3e6c-4f99-b738-defd04c520fe`)
- Sửa field `text` thành expression (KHÔNG comment, KHÔNG fallback thừa):
```javascript
{{ (() => {
  const STATUS = {
    SUCCESS: 'success',
    ERROR: 'error',
    NONE: 'none'
  };

  const MESSAGE = {
    SUCCESS_PREFIX: '✅ Video xử lý thành công',
    ERROR_PREFIX: '🔴 Lỗi xử lý video'
  };

  const status = $json.status;
  if (status === STATUS.NONE) return '';

  const id = $json.id;
  const videoTitle = $json.videoTitle;
  const videoUrl = $json.videoUrl;
  const driveLink = $json.driveLink;
  const youtubeLink = $json.youtubeLink;
  const errorMessage = $json.errorMessage;
  const timestamp = $json.timestamp;

  if (status === STATUS.SUCCESS) {
    return `${MESSAGE.SUCCESS_PREFIX}\nID: ${id}\nTiêu đề: ${videoTitle}\nYouTube: ${youtubeLink}\nDrive: ${driveLink}\nThời gian: ${timestamp}`;
  } else if (status === STATUS.ERROR) {
    const drivePart = driveLink ? `Drive: ${driveLink}\n` : '';
    const youtubePart = youtubeLink ? `YouTube: ${youtubeLink}\n` : '';
    return `${MESSAGE.ERROR_PREFIX}\nID: ${id}\nTiêu đề: ${videoTitle}\nLỗi: ${errorMessage}\nGốc: ${videoUrl}\n${drivePart}${youtubePart}Thời gian: ${timestamp}`;
  }
  return '';
})() }}
```

- Xóa hoặc bỏ qua Code node "Prepare Slack Message" (ID: `54d24cac-ec96-4b24-bcc8-306cac44e315`)
- Nối trực tiếp: Set Result Status → Send a message

**BƯỚC 6: (Tùy chọn) Đổi tên node "Cleanup Files"**
---------------------------------------------------
Mục đích: Tránh hiểu nhầm

Hiện tại: Tên "Cleanup Files" nhưng chỉ đọc Sheets
Có thể đổi thành: "Get Video Info For Status" hoặc giữ nguyên nhưng thêm note

**BƯỚC 7: Sắp xếp lại position của các node**
-----------------------------------------------
Mục đích: Để workflow dễ nhìn, dễ maintain

Nguyên tắc sắp xếp:
- **Nhánh Input** (trái, y = -900): Schedule Trigger → Get Video Information → Loop Over Items → Publish video
- **Nhánh Publish** (trên, y = -1160): Download Processed → Read Processed → Merge Data → Check Should Upload → Upload YT → Remove Binary → Update Final Status → Get Video Info After Upload → Set Result Status → Send a message
- **Nhánh Process** (giữa, y = -400): Extract URL → Extract Metadata → Merge Metadata → Generate/Parse → Clear Old Files → Download Video → Read/Remove binary → Extract Frame → Detect Logo → Process Video → Insert Intro → Upload Drive → Get Drive Link → Update Drive Link → Get Video Info → Check Upload After Drive → Set Result Status → Send a message
- **Nhánh FALSE** (dưới nhánh chính): Set Result Status → Send a message
- **Slack node** (cuối bên phải, x > 2000): Send a message

Các node mới thêm cần đặt position hợp lý:
- Set Result Status: Đặt ngay trước Send a message ở cả 2 nhánh
- Khoảng cách giữa các node: 200-300 pixels (x), cùng hàng (y)

**BƯỚC 8: (Tùy chọn) Thêm Error Trigger toàn workflow**
---------------------------------------------------------
Mục đích: Báo Slack khi workflow crash/timeout

Có thể thêm sau khi hoàn thành các bước trên

Data fields to add in per-item status
-------------------------------------
- status: 'success' | 'error' | 'none'
- errorMessage: string ngắn (cắt ~300 chars)
- id, videoTitle, videoUrl, driveLink, youtubeLink, publishStatus, timestamp

Test plan
---------
- Success: đi trọn publish, Upload YT OK → status=success, Slack ✅ (có YouTube link).
- Error Upload YT (quota/uploadLimitExceeded): status=error, Slack 🔴, loop tiếp.
- Error download/process (ffmpeg/yt-dlp/rclone): status=error, Slack 🔴, loop tiếp.
- IF false, không lỗi, không upload YT: status=none → không gửi Slack.

Out-of-scope
------------
- Không sửa logic delogo/intro/metadata.
- Không đổi Sheets schema hay điều kiện IF publish/process.

Next actions (sau khi bạn duyệt)
--------------------------------
- Thêm node “Set Result Status” vào cả hai nhánh (publish & process).
- Sửa “Prepare Slack Message” đọc status/error.
- (Nếu cần) Bật continueOnFail cho Upload To YouTube, Process Video, Upload Drive để chắc chắn không stop.

Chi tiết node sẽ chỉnh sửa
---------------------------
**Set Result Status** (Code node mới):
- Đặt trước "Prepare Slack Message" ở cả nhánh Publish và Process
- Logic: Kiểm tra uploadId từ "Upload To YouTube" → success; Kiểm tra stderr/error từ các node → error; Mặc định → none

**Send a message** (Slack node hiện có):
- **Gộp logic vào field `text`** (không dùng Code node riêng):
  - Check `status != none` trong expression
  - Format: ✅ success hoặc 🔴 error
  - Nếu `status = none` → trả về empty string hoặc skip

**Upload To YouTube**:
- Bật `continueOnFail: true` (nếu chưa có)

**Các node Execute Command** (CHƯA CÓ continueOnFail):
- Bật `continueOnFail: true` cho:
  - Download Video (yt-dlp)
  - Process Video (ffmpeg)
  - Insert Background Intro (ffmpeg)
  - Upload to Drive (rclone)
  - Get Drive Link (rclone link)

PLAN TRIỂN KHAI
===============
- Schedule Trigger
- Get Video Information (Google Sheets)
- Loop Over Items (SplitInBatches)

IF Publish video (đã có processed link, đủ điều kiện)
- Publish video (IF)
  - TRUE (đã có processed link, đủ publish):
    1) Download Processed Video From Drive
    2) Read Processed Video For YouTube
    3) Merge Data For YouTube Check
    4) Check Should Upload To YouTube (IF)
       - TRUE:
         5) Upload To YouTube
         6) Remove Binary After Upload YouTube
         7) Update Final Status (Sheets)
         8) Get Video Information After Upload
         9) Set Result Status (mới)
         10) Prepare Slack Message (status != none)
         11) Send a message (Slack) → Loop Over Items
       - FALSE (không upload):
         **BẮT BUỘC**: Nối FALSE → Set Result Status (none) → Send a message (skip) → Loop
         - Lý do: Phải chạy hết tất cả items
  - FALSE (không đủ điều kiện publish) → đi nhánh process mới

Nhánh process mới (chưa có processed link)
1) Extract Video URL (Code)
2) Extract YouTube Metadata (yt-dlp)
3) Merge YouTube Metadata (Code)
4) Generate metadata (Gemini) → Parse Video Metadata (Code)
5) Clear Old Files
6) Download Video (yt-dlp)
7) Read Video File
8) Remove Binary After Read Video
9) Extract Frame (ffmpeg)
10) Detect Logo (YOLO)
11) Process Video (ffmpeg delogo/overlay)
12) Insert Background Intro (ffmpeg concat)
13) Upload to Drive (rclone)
14) Get Drive Link
15) Update Drive Link After Process (Sheets)
16) Get Video Info For YouTube Check (Sheets)
17) Check Upload YouTube After Drive (IF)
    - TRUE: nhập nhánh publish (Download Processed Video... → Upload YT → Slack như trên)
    - FALSE:
      a) Cleanup Files (Sheets passthrough)
      b) Set Result Status (mới: nếu lỗi thì error; nếu không lỗi & không upload YT thì none)
      c) Prepare Slack Message (skip nếu none)
      d) Send a message (Slack) → Loop Over Items

Set Result Status (Code node, mới, đặt trước Prepare Slack Message ở cả hai nhánh)
- Input: id, title, video_url, driveLink, youtubeLink, publishStatus, timestamp + stderr/exitCode/error từ các bước trước.
- Logic:
  - status = 'none' mặc định.
  - Nếu phát hiện lỗi → status = 'error', errorMessage = tóm tắt (ưu tiên Upload/YT quota, ffmpeg, rclone, yt-dlp stderr).
  - Nếu có youtubeLink hợp lệ (uploadId) → status = 'success'.
  - success không dựa vào Drive link.
- Output: status, errorMessage (nếu có) và giữ nguyên các field cho Slack.

Prepare Slack Message (Code node)
- Nếu status = error: Slack 🔴, ngắn gọn ID, Tiêu đề, lỗi tóm tắt, link gốc, Drive/YouTube (nếu có), thời gian.
- Nếu status = success: Slack ✅, YouTube link, Drive link, ID, Tiêu đề, thời gian.
- Nếu status = none: không tạo message (Slack node sẽ bỏ qua).

Error Trigger (tùy chọn)
- Báo Slack khi workflow fail toàn cục (timeout/crash), khác với per-item.

CHI TIẾT CÁC NODE VÀ SCRIPT (từ test(3).json)
=============================================

FLOW DIAGRAM CHI TIẾT
---------------------
```
Schedule Trigger (ID: 2ee1c648-7f96-48fe-8fca-d12bff93c3e6)
  ↓
Get Video Information (Google Sheets, ID: 7232a3f8-34a4-4bb9-891f-f3c7da5379ed)
  ↓
Loop Over Items (SplitInBatches, ID: 35f612ca-42af-4a55-845f-3dcaee0377e5)
  ↓
Publish video (IF, ID: c08562cc-1a36-4f5b-9166-28ccd516434a)
  ├─ TRUE → Nhánh Publish
  └─ FALSE → Nhánh Process
```

NHÁNH PUBLISH (video đã có processed link)
-------------------------------------------
```
Publish video (IF) - TRUE
  ↓
Download Processed Video From Drive (Exec, ID: a2e0222a-5499-47d5-89bb-6b14f3e3fd62)
  Command: wget từ Drive link, extract FILE_ID từ URL
  ↓
Read Processed Video For YouTube (Read File, ID: e04f33a3-0d32-4519-90ae-75319786a8bf)
  File: {{ $json.stdout }}
  ↓
Merge Data For YouTube Check (Code, ID: 84ef31cb-a712-4d57-83e4-9542a7e955cc)
  Script: Ghép binary + metadata, normalize enable_youtube_upload
  ↓
Check Should Upload To YouTube (IF, ID: 3f2b43a7-bdd6-4abf-b2d5-d3c592c3b411)
  Condition: enable_youtube_upload_should_upload === true
  ├─ TRUE → Upload To YouTube
  └─ FALSE → [CẦN NỐI] Set Result Status (none) → Send a message (skip) → Loop
  ↓
Upload To YouTube (YouTube node, ID: 187a1d2a-5e99-46cc-a2b8-d3c8b8174d29)
  Title: từ Parse Video Metadata hoặc Sheets
  Category: map từ youtube_category
  Description: từ Parse Video Metadata hoặc Sheets
  Privacy: từ youtube_privacy
  [CẦN THÊM] continueOnFail: true
  ↓
Remove Binary After Upload YouTube (Code, ID: 5eddfb61-8c99-47d0-b3ce-2319d8891b90)
  Script: for (const item of $input.all()) { delete item.binary; }
  ↓
Update Final Status (Sheets, ID: ccc3d40e-dcea-4258-aff7-a521a3b41aa7)
  Update: publish_status="published", youtube_link, youtube_upload_time, processed_video_drive_link, youtube_title, youtube_description
  ↓
Get Video Information After Upload (Sheets, ID: 41337008-8e93-435c-97ed-fe82d4c95799)
  Read lại sheet sau update
  ↓
[CẦN THÊM] Set Result Status (Code node mới)
  Script: Xem BƯỚC 2 trong plan
  ↓
[CẦN SỬA] Send a message (Slack, ID: 949da91a-3e6c-4f99-b738-defd04c520fe)
  Text: Expression với STATUS enum, chỉ gửi khi status != none
  ↓
Loop Over Items (quay lại)
```

NHÁNH PROCESS (video chưa có processed link)
---------------------------------------------
```
Publish video (IF) - FALSE
  ↓
Extract Video URL (Code, ID: 9d92e35a-1ec4-4475-813d-d113736fb5df)
  Script:
    const row = $('Get Video Information').item.json;
    if (!row.id || !row.video_url) throw new Error('Missing required field: id or video_url');
    const driveUuid = generateUuid();
    return { id, video_title, video_url, driveUuid };
  ↓
Extract YouTube Metadata (Exec yt-dlp, ID: 2898ccf7-b5d5-44b8-97f3-0c41e003b586)
  Command: yt-dlp --print "%(title)s|%(uploader)s|%(description)s" {{ video_url }}
  ↓
Merge YouTube Metadata (Code, ID: ed16e7af-2e9c-4392-ad33-3dd44e5ae9d0)
  Script: Parse stdout, chọn video_title từ sheet hoặc yt-dlp
  ↓
Generate metadata (Gemini, ID: ed9a414a-82de-4df6-b1b6-226a883bbb5c)
  Model: gemini-2.5-flash
  Prompt: Tạo youtube_title (60-100 chars) và youtube_description (200-5000 chars)
  ↓
Parse Video Metadata (Code, ID: 605022c0-4c72-43f3-bc75-21ad89535435)
  Script: Parse JSON từ Gemini response, extract youtube_title và youtube_description
  ↓
Clear Old Files (Exec, ID: f1b6401a-d469-4506-84c9-5108838ba6a8)
  Command: rm -f "/home/node/downloads/${VIDEO_ID}.mp4"
  ↓
Download Video (Exec yt-dlp, ID: 3767add7-df7c-44d3-83c6-5f586c79235c)
  Command: yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" -o "/home/node/downloads/{{ id }}.mp4"
  [CẦN THÊM] continueOnFail: true
  ↓
Read Video File (Read File, ID: 3a61608b-9f2a-465d-8303-0c23a7e4f075)
  File: /home/node/downloads/{{ id }}.mp4
  ↓
Remove Binary After Read Video (Code, ID: 7e7dc808-4539-4a5b-814f-f78ef14bbae3)
  Script: for (const item of $input.all()) { delete item.binary; }
  ↓
Extract Frame (Exec ffmpeg, ID: 992da484-9e25-4f4a-ad44-3c7099598378)
  Command: ffmpeg -i video.mp4 -vf "select=eq(n\,0)" frame_{{ id }}.jpg
  ↓
Detect Logo (YOLO Exec, ID: 692fcf97-d559-448c-af42-9e1953d206eb)
  Command: python3 /data/src/controller/logo_controller.py detect frame_{{ id }}.jpg /data/models/best.pt 0.25
  ↓
Process Video (Exec ffmpeg, ID: 0aee79e6-953e-4cc2-912a-2597b8796fdc)
  Script: Delogo + overlay logo mới (bash script dài)
  - Nếu detect được logo cũ: delogo + overlay logo mới tại vị trí cũ
  - Nếu không detect được: overlay logo mới ở top-right
  [CẦN THÊM] continueOnFail: true
  ↓
Insert Background Intro (Exec ffmpeg, ID: 14eb42c2-d929-4a8e-825c-ece225db5e3d)
  Script: Chèn intro video vào đầu (bash script dài)
  - Download intro từ intro_background_url
  - Scale intro theo kích thước video chính
  - Concat intro + video chính
  [CẦN THÊM] continueOnFail: true
  ↓
Upload to Drive (Exec rclone, ID: 459a4a84-9873-4f78-801f-258777529162)
  Command: rclone copyto "${VIDEO_ID}_processed.mp4" "gdrive:reup-ytb/${DRIVE_UUID}.mp4"
  [CẦN THÊM] continueOnFail: true
  ↓
Get Drive Link (Exec rclone, ID: 53e6cf75-f149-420a-a39f-0841281875f8)
  Command: rclone link "gdrive:reup-ytb/{{ driveUuid }}.mp4"
  [CẦN THÊM] continueOnFail: true
  ↓
Update Drive Link After Process (Sheets, ID: 5b71a674-a541-43e5-95e3-816735c0ab3f)
  Update: processed_video_drive_link = {{ $json.stdout }}
  ↓
Get Video Info For YouTube Check (Sheets, ID: f2e7ab7e-ffb8-4442-bb16-3edeffe90e11)
  Read lại sheet để kiểm tra
  ↓
Check Upload YouTube After Drive (IF, ID: 18fe08a8-afe5-4bb9-8e7d-bb02a0ca0e12)
  Condition: publish_status="pending" AND enable_youtube_upload=true AND có processed_video_drive_link AND có youtube_privacy
  ├─ TRUE → Download Processed Video From Drive (nhập nhánh Publish)
  └─ FALSE → Cleanup Files → [CẦN SỬA] Set Result Status → Send a message → Loop
  ↓
Cleanup Files (Sheets, ID: 801361c9-22b5-46ca-9227-8ca1a67f581a)
  [CHỈ ĐỌC SHEETS, KHÔNG CLEANUP FILE THẬT]
  ↓
[CẦN THÊM] Set Result Status (Code node mới)
  Script: Xem BƯỚC 2 trong plan
  ↓
[CẦN SỬA] Send a message (Slack)
  Text: Expression với STATUS enum, chỉ gửi khi status != none
  ↓
Loop Over Items (quay lại)
```

CHI TIẾT CÁC NODE CODE/SCRIPT
------------------------------

**1. Extract Video URL (Code)**
```javascript
const row = $('Get Video Information').item.json;
if (!row.id) throw new Error('Missing required field: id');
if (!row.video_url) throw new Error('Missing required field: video_url');
const videoUrl = row.video_url;
function generateUuid() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}
const driveUuid = generateUuid();
return {
  json: {
    id: row.id,
    video_title: row.video_title,
    video_url: videoUrl,
    driveUuid
  }
};
```

**2. Merge YouTube Metadata (Code)**
```javascript
const row = $('Get Video Information').item.json;
const extractResult = $('Extract YouTube Metadata').item.json;
const extractUrl = $('Extract Video URL').item.json;
let ytTitle = '';
let ytDescription = '';
if (extractResult.stdout) {
  const parts = extractResult.stdout.trim().split('|');
  if (parts.length >= 3) {
    ytTitle = parts[0].trim();
    ytDescription = parts[2].trim().substring(0, 500);
  }
}
const videoTitle = row.video_title && row.video_title.trim() ? row.video_title.trim() : ytTitle;
if (!videoTitle) {
  throw new Error('Cannot extract video title from YouTube');
}
return {
  json: {
    ...extractUrl,
    video_title: videoTitle,
    youtube_metadata: {
      title: ytTitle,
      description: ytDescription
    }
  }
};
```

**3. Merge Data For YouTube Check (Code)**
```javascript
const videoInfo = $('Get Video Information').first().json;
const currentItem = $input.item;
if (!currentItem.binary || !currentItem.binary.data) {
  throw new Error('No video binary found from "Read Processed Video For YouTube"');
}
const binaryData = currentItem.binary.data;
if (!binaryData.data && !binaryData.mimeType) {
  throw new Error('Invalid binary data structure');
}
const enableYoutubeUpload = videoInfo.enable_youtube_upload;
const normalizedValue = String(enableYoutubeUpload).trim().toLowerCase();
const shouldUpload = normalizedValue === 'true' || normalizedValue === '1' || normalizedValue === 'yes';
let originalMimeType = binaryData.mimeType;
let fixedMimeType = originalMimeType;
if (originalMimeType && (originalMimeType === 'application/mp4' || originalMimeType === 'application/x-mp4')) {
  fixedMimeType = 'video/mp4';
}
const mergedData = {
  json: {
    ...videoInfo,
    id: videoInfo.id || currentItem.json.id,
    enable_youtube_upload_normalized: normalizedValue,
    enable_youtube_upload_should_upload: shouldUpload
  },
  binary: {
    data: {
      ...binaryData,
      mimeType: fixedMimeType
    }
  }
};
return mergedData;
```

**4. Prepare Slack Message (Code) - HIỆN TẠI (sẽ bị thay thế)**
```javascript
const mergeMetadata = $('Merge YouTube Metadata').first();
let videoInfo = $('Get Video Information After Upload');
if (!videoInfo || !videoInfo.isExecuted) {
  videoInfo = $('Get Video Information');
}
const allVideoInfo = videoInfo && videoInfo.isExecuted ? videoInfo.all() : [];
const currentVideoId = mergeMetadata ? mergeMetadata.json.id : '';
const currentVideo = allVideoInfo.find(v => v.json.id === currentVideoId);
let driveLink = '';
const getDriveLink = $('Get Drive Link');
if (getDriveLink && getDriveLink.isExecuted) {
  const driveLinkResult = getDriveLink.first();
  if (driveLinkResult && driveLinkResult.json && driveLinkResult.json.stdout) {
    driveLink = String(driveLinkResult.json.stdout).trim();
  }
}
if (!driveLink && currentVideo && currentVideo.json.processed_video_drive_link) {
  driveLink = currentVideo.json.processed_video_drive_link;
}
const now = new Date();
const timeStr = now.toLocaleString('vi-VN', {
  timeZone: 'Asia/Ho_Chi_Minh',
  year: 'numeric',
  month: '2-digit',
  day: '2-digit',
  hour: '2-digit',
  minute: '2-digit',
  second: '2-digit'
});
const id = currentVideo ? currentVideo.json.id : currentVideoId;
const videoTitle = currentVideo ? (currentVideo.json.video_title || currentVideo.json.youtube_title) : null;
const videoUrl = currentVideo ? currentVideo.json.video_url : null;
const publishStatus = currentVideo && currentVideo.json.publish_status ? String(currentVideo.json.publish_status).toLowerCase() : '';
let youtubeLink = '';
let youtubeUploadTime = '';
const uploadResult = $('Upload To YouTube');
if (uploadResult && uploadResult.isExecuted) {
  const uploadItem = uploadResult.first();
  if (uploadItem && uploadItem.json) {
    let json = uploadItem.json;
    let videoId = '';
    if (Array.isArray(json) && json.length > 0) {
      videoId = json[0].uploadId;
    } else if (typeof json === 'object' && json !== null) {
      videoId = json.uploadId;
    }
    if (videoId && String(videoId).trim() !== '') {
      youtubeLink = `https://www.youtube.com/watch?v=${String(videoId).trim()}`;
      youtubeUploadTime = timeStr;
    }
  }
}
const urlProcess = youtubeLink || driveLink;
const isSuccess = urlProcess && urlProcess.trim() !== '';
const lines = [];
lines.push(isSuccess ? '✅ Video xử lý xong' : '⏳ Video đang xử lý');
lines.push(`ID: ${id}`);
lines.push(`Tiêu đề: ${videoTitle}`);
lines.push(`Gốc: ${videoUrl}`);
if (youtubeLink) lines.push(`YouTube: ${youtubeLink}`);
if (driveLink) lines.push(`Drive: ${driveLink}`);
lines.push(`Trạng thái: ${publishStatus}`);
if (youtubeUploadTime) lines.push(`Upload YT: ${youtubeUploadTime}`);
lines.push(`Thời gian: ${timeStr}`);
const message = lines.join('\n');
return {
  json: {
    message,
    successCount: isSuccess ? 1 : 0,
    timestamp: timeStr,
    videoId: id,
    videoTitle: videoTitle,
    driveLink: driveLink,
    youtubeLink: youtubeLink,
    publishStatus: publishStatus,
    originalVideoUrl: videoUrl
  }
};
```

**5. Send a message (Slack) - HIỆN TẠI**
- Channel: C09QG88TFJM
- Text: `={{ $json.message || 'Done processing all YouTube jobs! Time: ' + new Date().toLocaleString('vi-VN') }}`
- Credential: r5gqdIaSja4mpw9V
- [CẦN SỬA] Text expression theo BƯỚC 5 trong plan

CONNECTIONS HIỆN TẠI (từ JSON)
--------------------------------
- Loop Over Items → Publish video (main[1])
- Publish video TRUE → Download Processed Video From Drive
- Publish video FALSE → Extract Video URL
- Check Should Upload To YouTube TRUE → Upload To YouTube
- Check Should Upload To YouTube FALSE → [KHÔNG CÓ CONNECTION - CẦN THÊM]
- Check Upload YouTube After Drive TRUE → Download Processed Video From Drive
- Check Upload YouTube After Drive FALSE → Cleanup Files
- Cleanup Files → Prepare Slack Message
- Prepare Slack Message → Send a message
- Send a message → Loop Over Items (main[0])

TOÀN BỘ CODE/SCRIPT CÁC NODE (từ test(3).json)
==============================================

**1. Parse Video Metadata (Code, ID: 605022c0-4c72-43f3-bc75-21ad89535435)**
```javascript
const extractTextFromResponse = (response) => {
  if (Array.isArray(response) && response.length > 0) {
    const firstItem = response[0];
    const textPart = firstItem.content?.parts?.[0];
    if (textPart?.text) return textPart.text.trim();
  }
  if (response.candidates && response.candidates.length > 0) {
    const textPart = response.candidates[0].content?.parts?.find(part => part.text);
    if (textPart?.text) return textPart.text.trim();
  }
  if (response.content?.parts?.length > 0) {
    const textPart = response.content.parts[0];
    if (textPart?.text) return textPart.text.trim();
  }
  return null;
};

const cleanJsonText = (text) => {
  let cleaned = text.replace(/^```json\s*/i, '').replace(/^```\s*/i, '').replace(/\s*```$/i, '').trim();
  const jsonMatch = cleaned.match(/\{[\s\S]*\}/);
  return jsonMatch ? jsonMatch[0] : cleaned;
};

const parseMetadata = (text) => {
  try {
    const meta = JSON.parse(text);
    if (!meta || typeof meta !== 'object') {
      return { error: 'Parsed result is not an object', raw: meta };
    }
    return {
      youtube_title: meta.youtube_title ? String(meta.youtube_title).trim() : '',
      youtube_description: meta.youtube_description ? String(meta.youtube_description).trim() : '',
      raw: meta
    };
  } catch (e) {
    return { error: `Parse error: ${e.message}`, rawText: text.substring(0, 400) };
  }
};

const response = $input.item.json;

if (response.error) {
  return {
    json: {
      youtube_title: '',
      youtube_description: '',
      error: `API Error: ${response.error.message || JSON.stringify(response.error)}`,
      valid: false,
      raw: response
    }
  };
}

const rawText = extractTextFromResponse(response);
if (!rawText) {
  return {
    json: {
      youtube_title: '',
      youtube_description: '',
      error: 'No text found in response',
      valid: false,
      raw: response
    }
  };
}

const cleanedText = cleanJsonText(rawText);
const parsed = parseMetadata(cleanedText);

if (parsed.error) {
  return {
    json: {
      youtube_title: '',
      youtube_description: '',
      error: parsed.error,
      valid: false,
      rawText: parsed.rawText,
      raw: parsed.raw
    }
  };
}

return {
  json: {
    youtube_title: parsed.youtube_title,
    youtube_description: parsed.youtube_description,
    error: null,
    valid: !!(parsed.youtube_title && parsed.youtube_description),
    raw: parsed.raw
  }
};
```

**2. Extract Video URL (Code, ID: 9d92e35a-1ec4-4475-813d-d113736fb5df)**
```javascript
const generateUuid = () => {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0;
    const v = c === 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
};

const row = $('Get Video Information').item.json;

if (!row.id || !row.video_url) {
  throw new Error('Missing required field: id or video_url');
}

return {
  json: {
    id: row.id,
    video_title: row.video_title,
    video_url: row.video_url,
    driveUuid: generateUuid()
  }
};
```

**3. Extract YouTube Metadata (Exec, ID: 2898ccf7-b5d5-44b8-97f3-0c41e003b586)**
```bash
yt-dlp --no-playlist --print "%(title)s|%(uploader)s|%(description)s" --no-warnings "{{ $('Extract Video URL').item.json.video_url }}" 2>/dev/null || echo "ERROR|ERROR|ERROR"
```

**4. Merge YouTube Metadata (Code, ID: ed16e7af-2e9c-4392-ad33-3dd44e5ae9d0)**
```javascript
const parseYouTubeMetadata = (stdout) => {
  if (!stdout) return { title: '', description: '' };
  const parts = stdout.trim().split('|');
  if (parts.length < 3) return { title: '', description: '' };
  return {
    title: parts[0].trim(),
    description: parts[2].trim().substring(0, 500)
  };
};

const row = $('Get Video Information').item.json;
const extractResult = $('Extract YouTube Metadata').item.json;
const extractUrl = $('Extract Video URL').item.json;

const ytMeta = parseYouTubeMetadata(extractResult.stdout);
const videoTitle = row.video_title && row.video_title.trim() ? row.video_title.trim() : ytMeta.title;

if (!videoTitle) {
  throw new Error('Cannot extract video title from YouTube');
}

return {
  json: {
    ...extractUrl,
    video_title: videoTitle,
    youtube_metadata: {
      title: ytMeta.title,
      description: ytMeta.description
    }
  }
};
```

**5. Clear Old Files (Exec, ID: f1b6401a-d469-4506-84c9-5108838ba6a8)**
```bash
VIDEO_ID="{{ $('Merge YouTube Metadata').item.json.id }}"
rm -f "/home/node/downloads/${VIDEO_ID}.mp4"
```

**6. Download Video (Exec, ID: 3767add7-df7c-44d3-83c6-5f586c79235c)**
```bash
PATH="/home/node/.local/bin:$PATH" yt-dlp --no-playlist -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" --merge-output-format mp4 --no-part -o "/home/node/downloads/{{ $('Merge YouTube Metadata').item.json.id }}.mp4" "{{ $('Merge YouTube Metadata').item.json.video_url }}" 2>&1 || PATH="/home/node/.local/bin:$PATH" yt-dlp --no-playlist -f "best[ext=mp4]/best" --merge-output-format mp4 --no-part -o "/home/node/downloads/{{ $('Merge YouTube Metadata').item.json.id }}.mp4" "{{ $('Merge YouTube Metadata').item.json.video_url }}" 2>&1
```

**7. Remove Binary After Read Video (Code, ID: 7e7dc808-4539-4a5b-814f-f78ef14bbae3)**
```javascript
for (const item of $input.all()) {
  delete item.binary;
}
return $input.all();
```

**8. Extract Frame (Exec, ID: 992da484-9e25-4f4a-ad44-3c7099598378)**
```bash
ffmpeg -y -i "/home/node/downloads/{{ $('Merge YouTube Metadata').item.json.id }}.mp4" -vf "select=eq(n\,0)" -q:v 3 "/home/node/downloads/frame_{{ $('Merge YouTube Metadata').item.json.id }}.jpg" 2>&1
```

**9. Detect Logo (YOLO) (Exec, ID: 692fcf97-d559-448c-af42-9e1953d206eb)**
```bash
python3 /data/src/controller/logo_controller.py detect "/home/node/downloads/frame_{{ $('Merge YouTube Metadata').item.json.id }}.jpg" /data/models/best.pt 0.25 2>&1
```

**10. Process Video (Exec, ID: 0aee79e6-953e-4cc2-912a-2597b8796fdc)**
```bash
#!/bin/bash
set -e

VIDEO_ID="{{ $('Merge YouTube Metadata').first().json.id }}"
FILE_NAME="{{ $('Read Video File').first().binary.data.fileName }}"
DETECT_OUTPUT="{{ $('Detect Logo (YOLO)').item.json.stdout }}"
NEW_LOGO_URL="{{ $('Get Video Information').first().json.new_logo_url }}"
OUTPUT_FILE="/home/node/downloads/${VIDEO_ID}_processed.mp4"
VIDEO_INPUT="/home/node/downloads/${FILE_NAME}"
LOGO_INPUT="/home/node/downloads/logo_${VIDEO_ID}.png"

if [ ! -f "$VIDEO_INPUT" ]; then
  echo "Error: Video file not found: $VIDEO_INPUT" >&2
  exit 1
fi

if [ ! -f "$LOGO_INPUT" ]; then
  if [ -z "$NEW_LOGO_URL" ] || [ "$NEW_LOGO_URL" = "" ]; then
    echo "Error: Logo file not found and new_logo_url is empty: $LOGO_INPUT" >&2
    exit 1
  fi

  echo "Downloading logo from: $NEW_LOGO_URL"

  if echo "$NEW_LOGO_URL" | grep -q "drive.google.com"; then
    FILE_ID=""
    FILE_ID=$(echo "$NEW_LOGO_URL" | sed -n 's/.*\/d\/\([^\/]*\)\/.*/\1/p' | head -1)
    if [ -z "$FILE_ID" ]; then
      FILE_ID=$(echo "$NEW_LOGO_URL" | sed -n 's/.*[?&]id=\([^&]*\).*/\1/p' | head -1)
    fi
    if [ -z "$FILE_ID" ]; then
      if echo "$NEW_LOGO_URL" | grep -qE '^[a-zA-Z0-9_-]+$'; then
        FILE_ID="$NEW_LOGO_URL"
      fi
    fi
    if [ -n "$FILE_ID" ]; then
      NEW_LOGO_URL="https://drive.google.com/uc?export=download&id=${FILE_ID}"
    fi
  fi

  wget -O "$LOGO_INPUT" "$NEW_LOGO_URL" || {
    echo "Error: Failed to download logo from: $NEW_LOGO_URL" >&2
    exit 1
  }

  if [ ! -f "$LOGO_INPUT" ] || [ ! -s "$LOGO_INPUT" ]; then
    echo "Error: Downloaded logo file is empty or not found: $LOGO_INPUT" >&2
    exit 1
  fi
fi

DETECT_JSON=$(echo "$DETECT_OUTPUT" | grep -o '\{[^}]*"logos"[^}]*\}' | head -1 || echo '{"logos":[],"count":0}')

if command -v jq >/dev/null 2>&1; then
  LOGO_COUNT=$(echo "$DETECT_JSON" | jq -r '.count // 0')
  if [ "$LOGO_COUNT" -gt 0 ]; then
    X=$(echo "$DETECT_JSON" | jq -r '.logos[0].x // 0')
    Y=$(echo "$DETECT_JSON" | jq -r '.logos[0].y // 0')
    WIDTH=$(echo "$DETECT_JSON" | jq -r '.logos[0].width // 0')
    HEIGHT=$(echo "$DETECT_JSON" | jq -r '.logos[0].height // 0')
    OLD_LOGO_FOUND="true"
  else
    X=0
    Y=0
    WIDTH=0
    HEIGHT=0
    OLD_LOGO_FOUND="false"
  fi
else
  if echo "$DETECT_JSON" | grep -q '"count":[1-9]'; then
    X=$(echo "$DETECT_JSON" | grep -o '"x":[0-9]*' | head -1 | grep -o '[0-9]*' || echo '0')
    Y=$(echo "$DETECT_JSON" | grep -o '"y":[0-9]*' | head -1 | grep -o '[0-9]*' || echo '0')
    WIDTH=$(echo "$DETECT_JSON" | grep -o '"width":[0-9]*' | head -1 | grep -o '[0-9]*' || echo '0')
    HEIGHT=$(echo "$DETECT_JSON" | grep -o '"height":[0-9]*' | head -1 | grep -o '[0-9]*' || echo '0')
    OLD_LOGO_FOUND="true"
  else
    X=0
    Y=0
    WIDTH=0
    HEIGHT=0
    OLD_LOGO_FOUND="false"
  fi
fi

VIDEO_WIDTH=$(ffprobe -v error -select_streams v:0 -show_entries stream=width  -of csv=p=0 "$VIDEO_INPUT")
VIDEO_HEIGHT=$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 "$VIDEO_INPUT")
VIDEO_WIDTH=${VIDEO_WIDTH:-0}
VIDEO_HEIGHT=${VIDEO_HEIGHT:-0}

OLD_LOGO_OK=false
if [ "$OLD_LOGO_FOUND" = "true" ] && [ "$WIDTH" -gt 0 ] && [ "$HEIGHT" -gt 0 ] && [ "$X" -ge 0 ] && [ "$Y" -ge 0 ]; then
  if [ "$VIDEO_WIDTH" -gt 0 ] && [ "$VIDEO_HEIGHT" -gt 0 ]; then
    if [ $((X + WIDTH)) -le "$VIDEO_WIDTH" ] && [ $((Y + HEIGHT)) -le "$VIDEO_HEIGHT" ]; then
      OLD_LOGO_OK=true
    fi
  else
    OLD_LOGO_OK=true
  fi
fi

if [ "$OLD_LOGO_OK" = "true" ]; then
    EXPAND=15
  DELOGO_X=$((X - EXPAND))
  DELOGO_Y=$((Y - EXPAND))
  DELOGO_W=$((WIDTH + EXPAND * 2))
  DELOGO_H=$((HEIGHT + EXPAND * 2))

  if [ "$DELOGO_X" -lt 0 ]; then DELOGO_X=0; fi
  if [ "$DELOGO_Y" -lt 0 ]; then DELOGO_Y=0; fi

  if [ "$VIDEO_WIDTH" -gt 0 ] && [ $((DELOGO_X + DELOGO_W)) -gt "$VIDEO_WIDTH" ]; then
    DELOGO_W=$((VIDEO_WIDTH - DELOGO_X))
  fi
  if [ "$VIDEO_HEIGHT" -gt 0 ] && [ $((DELOGO_Y + DELOGO_H)) -gt "$VIDEO_HEIGHT" ]; then
    DELOGO_H=$((VIDEO_HEIGHT - DELOGO_Y))
  fi

  SCALE_WIDTH_NUM=3
  SCALE_WIDTH_DEN=2
  SCALE_HEIGHT_NUM=12
  SCALE_HEIGHT_DEN=5
  NEW_WIDTH=$((WIDTH * SCALE_WIDTH_NUM / SCALE_WIDTH_DEN))
  NEW_HEIGHT=$((HEIGHT * SCALE_HEIGHT_NUM / SCALE_HEIGHT_DEN))

  OFFSET_X=$(((NEW_WIDTH - WIDTH) / 2))
  OFFSET_Y=$(((NEW_HEIGHT - HEIGHT) / 2))
  NEW_X=$((X - OFFSET_X))
  NEW_Y=$((Y - OFFSET_Y))

  if [ "$NEW_X" -lt 0 ]; then NEW_X=0; fi
  if [ "$NEW_Y" -lt 0 ]; then NEW_Y=0; fi

  nice -n 10 ffmpeg -y \
    -i "$VIDEO_INPUT" \
    -i "$LOGO_INPUT" \
    -filter_complex "[0:v]delogo=x=${DELOGO_X}:y=${DELOGO_Y}:w=${DELOGO_W}:h=${DELOGO_H}[v0];[v0]drawbox=x=${X}:y=${Y}:w=${WIDTH}:h=${HEIGHT}:color=black@0.98:t=fill[v1];[1:v]scale=${NEW_WIDTH}:${NEW_HEIGHT}[logo];[v1][logo]overlay=${NEW_X}:${NEW_Y}[v]" \
    -map "[v]" -map 0:a? \
    -c:v libx264 -preset veryfast -crf 25 \
    -c:a copy \
    "$OUTPUT_FILE"
else
  DEFAULT_LOGO_WIDTH=220
  DEFAULT_LOGO_HEIGHT=110
  PADDING=10

  nice -n 10 ffmpeg -y \
    -i "$VIDEO_INPUT" \
    -i "$LOGO_INPUT" \
    -filter_complex "[1:v]scale=${DEFAULT_LOGO_WIDTH}:${DEFAULT_LOGO_HEIGHT}[logo];[0:v][logo]overlay=W-w-${PADDING}:${PADDING}[v]" \
    -map "[v]" -map 0:a? \
    -c:v libx264 -preset veryfast -crf 25 \
    -c:a copy \
    "$OUTPUT_FILE"
fi

if [ ! -f "$OUTPUT_FILE" ]; then
  echo "Error: Output file not created!" >&2
  exit 1
fi
```

**11. Insert Background Intro (Exec, ID: 14eb42c2-d929-4a8e-825c-ece225db5e3d)**
```bash
#!/bin/bash
set -e

VIDEO_ID="{{ $('Merge YouTube Metadata').first().json.id }}"
INTRO_VIDEO_URL="{{ $('Get Video Information').first().json.intro_background_url }}"

VIDEO_INPUT="/home/node/downloads/${VIDEO_ID}_processed.mp4"
VIDEO_OUTPUT="/home/node/downloads/${VIDEO_ID}_processed.mp4"
VIDEO_OUTPUT_TEMP="/home/node/downloads/${VIDEO_ID}_processed_temp.mp4"
OUTPUT_DIR="/home/node/downloads"

if [ ! -f "$VIDEO_INPUT" ]; then
  echo "Error: Processed video file not found: $VIDEO_INPUT" >&2
  exit 1
fi

if [ -z "$INTRO_VIDEO_URL" ] || [ "$INTRO_VIDEO_URL" = "" ]; then
  cp "$VIDEO_INPUT" "$VIDEO_OUTPUT"
  exit 0
fi

INTRO_VIDEO="${OUTPUT_DIR}/intro_${VIDEO_ID}.mp4"

if echo "$INTRO_VIDEO_URL" | grep -q "drive.google.com"; then
  FILE_ID=""
  FILE_ID=$(echo "$INTRO_VIDEO_URL" | sed -n 's/.*\/d\/\([^\/]*\)\/.*/\1/p' | head -1)
  if [ -z "$FILE_ID" ]; then
    FILE_ID=$(echo "$INTRO_VIDEO_URL" | sed -n 's/.*[?&]id=\([^&]*\).*/\1/p' | head -1)
  fi
  if [ -z "$FILE_ID" ]; then
    if echo "$INTRO_VIDEO_URL" | grep -qE '^[a-zA-Z0-9_-]+$'; then
      FILE_ID="$INTRO_VIDEO_URL"
    fi
  fi
  if [ -n "$FILE_ID" ]; then
    INTRO_VIDEO_URL="https://drive.google.com/uc?export=download&id=${FILE_ID}"
  fi
fi

echo "Downloading intro video from: $INTRO_VIDEO_URL"
wget -O "$INTRO_VIDEO" "$INTRO_VIDEO_URL" || {
  echo "Error: Failed to download intro video"
  exit 1
}

if [ ! -f "$INTRO_VIDEO" ] || [ ! -s "$INTRO_VIDEO" ]; then
  echo "Error: Intro video file is empty or not found"
  exit 1
fi

MAIN_W=$(ffprobe -v error -select_streams v:0 -show_entries stream=width  -of csv=p=0 "$VIDEO_INPUT")
MAIN_H=$(ffprobe -v error -select_streams v:0 -show_entries stream=height -of csv=p=0 "$VIDEO_INPUT")
MAIN_FPS=$(ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 "$VIDEO_INPUT")
MAIN_HAS_AUDIO=$(ffprobe -v error -select_streams a:0 -count_frames -show_entries stream=codec_name -of csv=p=0 "$VIDEO_INPUT" 2>/dev/null || true)

INTRO_TEMP="${OUTPUT_DIR}/intro_scaled_${VIDEO_ID}.mp4"

if [ -n "$MAIN_HAS_AUDIO" ]; then
  INTRO_HAS_AUDIO=$(ffprobe -v error -select_streams a:0 -count_frames -show_entries stream=codec_name -of csv=p=0 "$INTRO_VIDEO" 2>/dev/null || true)
  if [ -n "$INTRO_HAS_AUDIO" ]; then
    ffmpeg -y \
      -i "$INTRO_VIDEO" \
      -vf "scale=${MAIN_W}:${MAIN_H}:force_original_aspect_ratio=decrease,pad=${MAIN_W}:${MAIN_H}:(ow-iw)/2:(oh-ih)/2:color=black,fps=${MAIN_FPS}" \
      -af "aresample=48000:resampler=soxr" \
      -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p \
      -c:a aac -ar 48000 -ac 2 -b:a 128k \
      "$INTRO_TEMP"
  else
    ffmpeg -y \
      -i "$INTRO_VIDEO" \
      -f lavfi -i anullsrc=channel_layout=stereo:sample_rate=48000 \
      -vf "scale=${MAIN_W}:${MAIN_H}:force_original_aspect_ratio=decrease,pad=${MAIN_W}:${MAIN_H}:(ow-iw)/2:(oh-ih)/2:color=black,fps=${MAIN_FPS}" \
      -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p \
      -c:a aac -ar 48000 -ac 2 -b:a 128k \
      -shortest \
      "$INTRO_TEMP"
  fi
else
  ffmpeg -y \
    -i "$INTRO_VIDEO" \
    -vf "scale=${MAIN_W}:${MAIN_H}:force_original_aspect_ratio=decrease,pad=${MAIN_W}:${MAIN_H}:(ow-iw)/2:(oh-ih)/2:color=black,fps=${MAIN_FPS}" \
    -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p \
    "$INTRO_TEMP"
fi

if [ -n "$MAIN_HAS_AUDIO" ]; then
  ffmpeg -y \
    -i "$INTRO_TEMP" -i "$VIDEO_INPUT" \
    -filter_complex "[0:a]aresample=48000:resampler=soxr[a0];[0:v][a0][1:v][1:a]concat=n=2:v=1:a=1[outv][outa]" \
    -map "[outv]" -map "[outa]" \
    -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p \
    -c:a aac -ar 48000 -ac 2 -b:a 128k \
    "$VIDEO_OUTPUT_TEMP"
else
  ffmpeg -y \
    -i "$INTRO_TEMP" -i "$VIDEO_INPUT" \
    -filter_complex "[0:v][1:v]concat=n=2:v=1[outv]" \
    -map "[outv]" \
    -c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p \
    "$VIDEO_OUTPUT_TEMP"
fi

if [ ! -f "$VIDEO_OUTPUT_TEMP" ]; then
  echo "Error: Output file not created!"
  exit 1
fi

rm -f "$VIDEO_INPUT"
mv "$VIDEO_OUTPUT_TEMP" "$VIDEO_OUTPUT"
rm -f "$INTRO_TEMP" "$INTRO_VIDEO"

if [ -f "$VIDEO_OUTPUT" ]; then
  echo "Video with intro created: $VIDEO_OUTPUT"
  else
  echo "Error: Final output file not found!"
  exit 1
fi
```

**12. Upload to Drive (Exec, ID: 459a4a84-9873-4f78-801f-258777529162)**
```bash
#!/bin/bash
set -e

VIDEO_ID="{{ $('Merge YouTube Metadata').first().json.id }}"
DRIVE_UUID="{{ $('Merge YouTube Metadata').first().json.driveUuid }}"
SOURCE_FILE="/home/node/downloads/${VIDEO_ID}_processed.mp4"
DEST_PATH="gdrive:reup-ytb/${DRIVE_UUID}.mp4"

if [ ! -f "$SOURCE_FILE" ]; then
  echo "ERROR: Source file not found: $SOURCE_FILE" >&2
  exit 1
fi

rclone copyto "$SOURCE_FILE" "$DEST_PATH" -P >/dev/null 2>&1
```

**13. Get Drive Link (Exec, ID: 53e6cf75-f149-420a-a39f-0841281875f8)**
```bash
rclone link "gdrive:reup-ytb/{{ $('Merge YouTube Metadata').first().json.driveUuid }}.mp4"
```

**14. Download Processed Video From Drive (Exec, ID: a2e0222a-5499-47d5-89bb-6b14f3e3fd62)**
```bash
VIDEO_ID="{{ $json.id }}"
LINK="{{ $json.processed_video_drive_link }}"

[ -z "$LINK" ] && exit 0

FILE_ID=$(echo "$LINK" | sed -n 's/.*\/d\/\([^\/]*\)\/.*/\1/p')
[ -z "$FILE_ID" ] && FILE_ID=$(echo "$LINK" | sed -n 's/.*[?&]id=\([^&]*\).*/\1/p')
[ -z "$FILE_ID" ] && echo "$LINK" | grep -qE '^[a-zA-Z0-9_-]+$' && FILE_ID="$LINK"
[ -z "$FILE_ID" ] && exit 0

URL="https://drive.google.com/uc?export=download&id=${FILE_ID}"

header=$(wget --server-response --spider -q "$URL" 2>&1)
name=$(echo "$header" | sed -n 's/.*filename="\([^"]*\)".*/\1/p')

[ -z "$name" ] && name="${VIDEO_ID}.mp4"

mkdir -p /home/node/downloads

OUTPUT="/home/node/downloads/$name"

wget -q "$URL" -O "$OUTPUT"

[ ! -s "$OUTPUT" ] && exit 0

echo "$OUTPUT"
```

**15. Merge Data For YouTube Check (Code, ID: 84ef31cb-a712-4d57-83e4-9542a7e955cc)**
```javascript
const videoInfo = $('Get Video Information').first().json;
const currentItem = $input.item;

if (!currentItem.binary || !currentItem.binary.data) {
  throw new Error('No video binary found from "Read Processed Video For YouTube"');
}

const binaryData = currentItem.binary.data;
if (!binaryData.data && !binaryData.mimeType) {
  throw new Error('Invalid binary data structure');
}

const enableYoutubeUpload = videoInfo.enable_youtube_upload;
const normalizedValue = String(enableYoutubeUpload).trim().toLowerCase();
const shouldUpload = normalizedValue === 'true' || normalizedValue === '1' || normalizedValue === 'yes';

let originalMimeType = binaryData.mimeType || 'application/mp4';
let fixedMimeType = originalMimeType;

if (originalMimeType === 'application/mp4' || originalMimeType === 'application/x-mp4') {
  fixedMimeType = 'video/mp4';
}

const mergedData = {
  json: {
    ...videoInfo,
    id: videoInfo.id || currentItem.json.id,
    enable_youtube_upload_normalized: normalizedValue,
    enable_youtube_upload_should_upload: shouldUpload
  },
  binary: {
    data: {
      ...binaryData,
      mimeType: fixedMimeType
    }
  }
};

return mergedData;
```

**16. Remove Binary After Upload YouTube (Code, ID: 5eddfb61-8c99-47d0-b3ce-2319d8891b90)**
```javascript
for (const item of $input.all()) {
  delete item.binary;
}
return $input.all();
```

**17. Upload To YouTube - Title Expression**
```javascript
{{ (() => {
  const getParsedTitle = () => {
    const parseMeta = $('Parse Video Metadata');
    if (!parseMeta || !parseMeta.isExecuted) return null;
    const metaItem = parseMeta.first();
    if (!metaItem || !metaItem.json || !metaItem.json.youtube_title) return null;
    const title = String(metaItem.json.youtube_title).trim();
    return title ? title : null;
  };
  const parsedTitle = getParsedTitle();
  if (parsedTitle) return parsedTitle;
  const sheetData = $('Get Video Information').first().json;
  if (sheetData.youtube_title) return sheetData.youtube_title;
  if (sheetData.video_title) return sheetData.video_title;
  return null;
})() }}
```

**18. Upload To YouTube - CategoryId Expression**
```javascript
{{ (() => {
  const CATEGORY_MAP = {
    'other': 24,
    'hoạt hình': 1,
    'âm nhạc': 10,
    'tâm sự': 24,
    'music': 10,
    'animation': 1,
    'entertainment': 24
  };
  const cat = $('Get Video Information').first().json.youtube_category;
  if (!cat) return null;
  const catLower = String(cat).toLowerCase().trim();
  return CATEGORY_MAP[catLower] || null;
})() }}
```

**19. Upload To YouTube - Description Expression**
```javascript
{{ (() => {
  const getParsedDescription = () => {
    const parseMeta = $('Parse Video Metadata');
    if (!parseMeta || !parseMeta.isExecuted) return null;
    const metaItem = parseMeta.first();
    if (!metaItem || !metaItem.json || !metaItem.json.youtube_description) return null;
    const desc = String(metaItem.json.youtube_description).trim();
    return desc ? desc : null;
  };
  const parsedDesc = getParsedDescription();
  if (parsedDesc) return parsedDesc;
  const sheetData = $('Get Video Information').first().json;
  return sheetData.youtube_description || null;
})() }}
```

**20. Upload To YouTube - PrivacyStatus Expression**
```javascript
{{ $('Get Video Information').first().json.youtube_privacy }}
```

**21. Update Final Status - youtube_link Expression**
```javascript
{{ (() => {
  const extractVideoId = (uploadItem) => {
    if (!uploadItem || !uploadItem.json) return null;
    const json = uploadItem.json;
    if (Array.isArray(json) && json.length > 0) return json[0].uploadId;
    if (typeof json === 'object' && json !== null) return json.uploadId;
    return null;
  };
  const uploadResult = $('Upload To YouTube');
  if (!uploadResult || !uploadResult.isExecuted) return '';
  const uploadItem = uploadResult.first();
  const videoId = extractVideoId(uploadItem);
  if (!videoId) return '';
  const trimmedId = String(videoId).trim();
  return trimmedId ? `https://www.youtube.com/watch?v=${trimmedId}` : '';
})() }}
```

**22. Update Final Status - youtube_upload_time Expression**
```javascript
{{ (() => {
  const now = new Date();
  const dateStr = now.toLocaleDateString('vi-VN', {
    timeZone: 'Asia/Ho_Chi_Minh',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  });
  const timeStr = now.toLocaleTimeString('vi-VN', {
    timeZone: 'Asia/Ho_Chi_Minh',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
  return `${dateStr} ${timeStr}`;
})() }}
```

**23. Update Final Status - processed_video_drive_link Expression**
```javascript
{{ (() => {
  const getDriveLink = $('Get Drive Link');
  if (getDriveLink && getDriveLink.isExecuted) {
    const result = getDriveLink.first();
    if (result && result.json && result.json.stdout) {
      return String(result.json.stdout).trim();
    }
  }
  return $('Get Video Information').first().json.processed_video_drive_link;
})() }}
```

**24. Update Final Status - youtube_title Expression**
```javascript
{{ (() => {
  const getParsedTitle = () => {
    const parseMeta = $('Parse Video Metadata');
    if (!parseMeta || !parseMeta.isExecuted) return null;
    const metaItem = parseMeta.first();
    if (!metaItem || !metaItem.json || !metaItem.json.youtube_title) return null;
    const title = String(metaItem.json.youtube_title).trim();
    return title ? title : null;
  };
  const parsedTitle = getParsedTitle();
  if (parsedTitle) return parsedTitle;
  const sheetData = $('Get Video Information').first().json;
  if (sheetData.youtube_title) return sheetData.youtube_title;
  if (sheetData.video_title) return sheetData.video_title;
  return null;
})() }}
```

**25. Update Final Status - youtube_description Expression**
```javascript
{{ (() => {
  const getParsedDescription = () => {
    const parseMeta = $('Parse Video Metadata');
    if (!parseMeta || !parseMeta.isExecuted) return null;
    const metaItem = parseMeta.first();
    if (!metaItem || !metaItem.json || !metaItem.json.youtube_description) return null;
    const desc = String(metaItem.json.youtube_description).trim();
    return desc ? desc : null;
  };
  const parsedDesc = getParsedDescription();
  if (parsedDesc) return parsedDesc;
  return $('Get Video Information').first().json.youtube_description || null;
})() }}
```

**26. Prepare Slack Message (Code, ID: 54d24cac-ec96-4b24-bcc8-306cac44e315) - HIỆN TẠI (sẽ bị thay thế)**
```javascript
const getVideoInfoNode = () => {
  let videoInfo = $('Get Video Information After Upload');
  if (!videoInfo || !videoInfo.isExecuted) {
    videoInfo = $('Get Video Information');
  }
  return videoInfo && videoInfo.isExecuted ? videoInfo.all() : [];
};

const getCurrentVideo = (videoId, allVideoInfo) => {
  return allVideoInfo.find(v => v.json.id === videoId);
};

const extractYouTubeLink = (uploadResult) => {
  if (!uploadResult || !uploadResult.isExecuted) return { link: '', time: '' };
  const uploadItem = uploadResult.first();
  if (!uploadItem || !uploadItem.json) return { link: '', time: '' };
  const json = uploadItem.json;
  const videoId = Array.isArray(json) && json.length > 0 ? json[0].uploadId : json.uploadId;
  if (!videoId) return { link: '', time: '' };
  const trimmedId = String(videoId).trim();
  const timeStr = getTimestamp();
  return trimmedId ? { link: `https://www.youtube.com/watch?v=${trimmedId}`, time: timeStr } : { link: '', time: '' };
};

const getDriveLinkFromNode = () => {
  const getDriveLink = $('Get Drive Link');
  if (!getDriveLink || !getDriveLink.isExecuted) return null;
  const result = getDriveLink.first();
  if (!result || !result.json || !result.json.stdout) return null;
  return String(result.json.stdout).trim();
};

const getTimestamp = () => {
  return new Date().toLocaleString('vi-VN', {
    timeZone: 'Asia/Ho_Chi_Minh',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
};

const mergeMetadata = $('Merge YouTube Metadata').first();
const currentVideoId = mergeMetadata ? mergeMetadata.json.id : '';
const allVideoInfo = getVideoInfoNode();
const currentVideo = getCurrentVideo(currentVideoId, allVideoInfo);
const driveLink = getDriveLinkFromNode() || (currentVideo && currentVideo.json && currentVideo.json.processed_video_drive_link);
const youtubeData = extractYouTubeLink($('Upload To YouTube'));
const timeStr = getTimestamp();

const id = currentVideo ? currentVideo.json.id : currentVideoId;
const videoTitle = currentVideo ? (currentVideo.json.video_title || currentVideo.json.youtube_title) : null;
const videoUrl = currentVideo ? currentVideo.json.video_url : null;
const publishStatus = currentVideo && currentVideo.json.publish_status ? String(currentVideo.json.publish_status).toLowerCase() : '';
const isSuccess = youtubeData.link || driveLink;

const lines = [
  isSuccess ? '✅ Video xử lý xong' : '⏳ Video đang xử lý',
  `ID: ${id}`,
  `Tiêu đề: ${videoTitle}`,
  `Gốc: ${videoUrl}`,
  youtubeData.link ? `YouTube: ${youtubeData.link}` : null,
  driveLink ? `Drive: ${driveLink}` : null,
  `Trạng thái: ${publishStatus}`,
  youtubeData.time ? `Upload YT: ${youtubeData.time}` : null,
  `Thời gian: ${timeStr}`
].filter(line => line !== null);

return {
  json: {
    message: lines.join('\n'),
    successCount: isSuccess ? 1 : 0,
    timestamp: timeStr,
    videoId: id,
    videoTitle,
    driveLink,
    youtubeLink: youtubeData.link,
    publishStatus,
    originalVideoUrl: videoUrl
  }
};
```

**27. Send a message (Slack) - Text Expression - HIỆN TẠI**
```javascript
{{ $json.message || 'Done processing all YouTube jobs! Time: ' + new Date().toLocaleString('vi-VN') }}
```

**28. Generate metadata (Gemini) - Prompt**
```
Bạn là chuyên gia tối ưu hóa metadata YouTube. Nhiệm vụ của bạn là tạo tiêu đề và mô tả YouTube mới dựa trên video_title đầu vào.

DỮ LIỆU ĐẦU VÀO:
video_title: ={{ $json.video_title }}

========================================
YÊU CẦU BẮT BUỘC CHO TIÊU ĐỀ (youtube_title)
========================================
- Độ dài: CHÍNH XÁC 60-100 ký tự (tính toàn bộ ký tự, bao gồm khoảng trắng)
- Tiêu đề phải hấp dẫn, thu hút click và tối ưu SEO
- Phải chứa từ khóa chính liên quan đến video_title đầu vào
- Dùng Title Case hoặc Sentence Case (một kiểu duy nhất)
- KHÔNG được dùng emoji hoặc ký tự đặc biệt (ngoại trừ dấu chấm, phẩy, dấu gạch)
- Không được thừa khoảng trắng ở đầu hoặc cuối

========================================
YÊU CẦU BẮT BUỘC CHO MÔ TẢ (youtube_description)
========================================
- Độ dài: 200-5000 ký tự (tối thiểu 200, tối ưu 500-2000)
- 2-3 dòng đầu phải chứa từ khóa chính của video_title và thu hút người xem
- Nội dung phải liên quan chặt chẽ tới video, mô tả rõ ràng giá trị video
- Có thể thêm lời kêu gọi hành động (Subscribe, Like)
- Có thể thêm timestamp, link, hoặc hashtag (3-10 hashtag) nếu phù hợp
- Sử dụng ký tự \n để xuống dòng (không xuống dòng thật)
- Không được thừa khoảng trắng ở đầu hoặc cuối

========================================
YÊU CẦU VỀ ĐỊNH DẠNG OUTPUT (CỰC KỲ QUAN TRỌNG - SẼ ĐƯỢC PARSE BẰNG JSON.parse())
========================================
Bạn PHẢI trả về DUY NHẤT một JSON object hợp lệ có đúng 2 trường:

{"youtube_title":"...","youtube_description":"..."}

QUY ĐỊNH NGHIÊM NGẶT:
- KHÔNG được dùng markdown code blocks (```json, ```)
- KHÔNG có văn bản giải thích bên ngoài JSON
- KHÔNG có comment trong JSON (//, /* */)
- KHÔNG có trailing comma
- KHÔNG được trả về array ([{...}])
- KHÔNG được thêm bất kỳ trường nào khác
- Tất cả giá trị phải là string, dùng dấu nháy kép "
- Escape special characters đúng cách: \" cho quotes, \\ cho backslash, \n cho newline
- JSON phải hợp lệ và parse được bằng JSON.parse()
- Field names PHẢI chính xác: "youtube_title" và "youtube_description" (lowercase, underscore)

VÍ DỤ FORMAT ĐÚNG:
{"youtube_title":"This Is An Example YouTube Title That Is Between 60 And 100 Characters Long","youtube_description":"This is an example description that must be at least 200 characters long to meet the requirements. It should include relevant keywords and be engaging for viewers. You can add more content here to reach the minimum character count. This description should provide value and encourage viewers to watch the video."}

========================================
ĐIỀU KIỆN BẮT BUỘC PHẢI ĐẠT
========================================
- youtube_title: 60-100 ký tự (inclusive), non-empty string
- youtube_description: 200-5000 ký tự (inclusive), non-empty string
- Cả hai field đều bắt buộc, không được null hoặc undefined
- KHÔNG được dùng emoji
- Response phải parse được bằng JSON.parse() không lỗi

========================================
HÃY TIẾN HÀNH TẠO TIÊU ĐỀ VÀ MÔ TẢ NGAY BÂY GIỜ.
CHỈ TRẢ VỀ ĐÚNG JSON OBJECT, KHÔNG THÊM BẤT KỲ THỨ GÌ KHÁC.
KHÔNG CÓ MARKDOWN, KHÔNG CÓ GIẢI THÍCH, CHỈ CÓ JSON OBJECT THUẦN TÚY.
```
