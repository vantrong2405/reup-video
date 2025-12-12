# 📹 Quy Trình Tạo Video Review Phim/Anime

> **Phương pháp Voice-First** — Giảm rủi ro bản quyền, tăng tính transformative

---

## 🎯 1. Mục Tiêu

- Tạo video review phim/anime theo hướng **biến đổi mạnh** (transformative)
- Giảm tối đa rủi ro bản quyền nhưng vẫn giữ vibe phim
- Visual phải dẫn theo voice-over, không bị lệch nhịp
- Áp dụng cho cả **Shorts/TikTok** và **YouTube dài**

---

## 📋 2. Nguyên Tắc Chính

| # | Nguyên tắc |
|---|------------|
| 1 | Voice-over là **timeline chính** |
| 2 | Visual chỉ là minh hoạ, không được chiếm ưu thế |
| 3 | Mọi scene phải được cắt ngắn và biến đổi mạnh |
| 4 | Âm thanh gốc phải bị **loại bỏ hoàn toàn** |
| 5 | Layout, overlay, subtitle phải giúp video khác biệt với bản gốc |

---

## 🔊 3. Bước 1 — Tạo Voice-Over Trước (Voice Leads)

**Prompt:**
```
Tạo voice-over đầy đủ trước. Voice-over sẽ là timeline chính của video.
Chia voice thành các câu ngắn rõ ràng, mỗi câu mang một ý duy nhất.
Mỗi câu khi đọc dài 0.8–2.0 giây.
Visual phải được dựng theo đúng thời lượng từng câu.
```

**Yêu cầu:**
- Mỗi câu = 1 đoạn visual
- Voice mạch lạc, tốc độ đều
- Không tạo clip trước voice

---

## ✍️ 4. Bước 2 — Chuẩn Hóa Script

**Prompt:**
```
Hãy viết lại script review thành nhiều câu ngắn, mỗi câu tối đa 12–18 từ.
Không dùng câu phức, không dùng câu dài.
Mỗi câu truyền tải một ý rõ ràng để dễ sync visual.
```

---

## ⏱️ 5. Bước 3 — Tách Voice + Lưu Thời Lượng

> *Áp dụng cho AI hoặc workflow thủ công*

**Prompt:**
```
Tách voice-over thành từng câu riêng biệt.
Xuất thời lượng (duration) chính xác của mỗi câu.

Danh sách output:
- Câu 1: duration …
- Câu 2: duration …
- Câu 3: duration …
```

---

## 🔇 6. Bước 4 — Loại Âm Thanh Gốc

> [!CAUTION]
> **BẮT BUỘC** — Bước này không được bỏ qua!

**Prompt:**
```
Loại bỏ toàn bộ âm thanh dialog, soundtrack, hiệu ứng từ phim/anime.
Chỉ sử dụng:
- Voice-over chính
- Nhạc nền không bản quyền (low volume để không che voice)
```

---

## 🎬 7. Bước 5 — Chọn Clip Minh Họa

**Prompt:**
```
Với mỗi câu voice-over, chọn một hoặc nhiều clip minh họa.
Mỗi clip chỉ được dài 0.4–1.2 giây.
Không clip nào được phép vượt quá 1.8 giây.
Nếu voice dài hơn 1.8 giây → chia thành nhiều clip ngắn.
```

**Yêu cầu:**
- Clip phải phù hợp nội dung câu
- Không cần clip dài → **càng ngắn càng an toàn**

---

## 🖼️ 8. Bước 6 — Không Để Clip Full-Screen

**Prompt:**
```
Không dùng clip full-screen.
Hiển thị clip trong khung nhỏ (60–85% màn hình).
Có viền, khoảng trống, hoặc background blur.
```

**Tác dụng:**
- ✅ Giảm nhận diện hình ảnh
- ✅ Tăng hiệu ứng review

---

## 🎨 9. Bước 7 — Áp Overlay Giảm Nhận Diện

**Prompt:**
```
Áp overlay dạng grain, VHS, color tint hoặc film dust ở mức 15–30% opacity.
Overlay phải bao phủ toàn màn hình.
Overlay phải giữ nguyên trong toàn clip.
```

---

## 🔄 10. Bước 8 — Biến Đổi Clip (Transformation)

> [!IMPORTANT]
> **Mục tiêu:** Làm clip khác **40–60%** so với bản gốc

**Prompt:**
```
Biến đổi mỗi đoạn clip bằng ít nhất 3 kỹ thuật:
- Crop
- Zoom in/out
- Rotate vài độ
- Blur nhẹ background
- Speed 1.02x–1.06x
- Transition nhanh
- Thay màu (color grading)
```

---

## 📝 11. Bước 9 — Subtitle Theo Câu

**Prompt:**
```
Tạo subtitle cho từng câu.
Subtitle phải xuất hiện bắt đầu khi câu bắt đầu và kết thúc cùng voice của câu đó.
Subtitle nằm ở giữa thân dưới màn hình.
Không quá dài.
```

---

## 🎵 12. Bước 10 — Chỉnh Nhạc Nền

**Prompt:**
```
Sử dụng nhạc nền không bản quyền.
Âm lượng nhỏ (6–12%) để không lấn voice.
Loop nhạc để phù hợp toàn video.
```

---

## 🎥 13. Bước 11 — Build Final Video

**Prompt:**
```
Xuất video theo đúng timeline:

1. Intro (nếu có) → 1–2s
2. Segment cho mỗi câu voice:
   [Clip ngắn + Overlay + Subtitle + Layout]
3. Outro → 1–2s (tuỳ chọn)

Tỷ lệ khung:
- 9:16 → TikTok/Shorts
- 16:9 → YouTube
```

---

## ✅ 14. Bước 12 — Tiêu Chí Giảm Rủi Ro Bản Quyền

**Checklist bắt buộc:**

| # | Tiêu chí | Yêu cầu |
|---|----------|---------|
| 1 | Audio gốc | ❌ Không chứa |
| 2 | Thời lượng clip | < 1.8 giây/cảnh |
| 3 | Biến đổi clip | ≥ 40% |
| 4 | Full-screen footage | ❌ Không dùng |
| 5 | Overlay | ✅ Toàn màn |
| 6 | Voice chiếm giá trị | 70–90% |
| 7 | Tính chất video | Phân tích/bình luận/tóm tắt (transformative) |

---

## 🚀 15. Bước 13 — Xuất Bản Final

**Prompt:**
```
Tạo bản xem thử.
Kiểm tra:
- Voice trùng khớp clip
- Không có âm thanh gốc
- Visual không quá giống phim gốc
- Subtitle khớp
- Tốc độ cắt không gây khó chịu

Sau khi hợp lệ → xuất bản final video.
```

---

## ⚡ Prompt Rút Gọn (Copy Nhanh)

```
Tạo một video review phim/anime theo quy trình voice-first:

1. Voice-over tạo trước, chia thành câu 0.8–2.0s
2. Visual phải theo đúng từng câu voice
3. Mỗi clip ngắn 0.4–1.2s, không clip nào quá 1.8s
4. Không dùng audio gốc
5. Clip không được full-screen → chỉ 60–85% khung hình
6. Áp overlay 15–30% (grain/VHS/tint)
7. Biến đổi mỗi clip ≥40% (zoom, crop, speed, color)
8. Thêm subtitle theo từng câu
9. Thêm nhạc nền free và chỉnh âm lượng thấp
10. Tạo video có tính transformative cao để giảm rủi ro bản quyền
```

---

> [!TIP]
> **Ghi nhớ:** Voice luôn đi trước, Visual đi sau!
