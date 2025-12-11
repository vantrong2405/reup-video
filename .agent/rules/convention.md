---
trigger: glob
---

# N8N Workflow Development Rules

## 1. Greeting Protocol
- Luôn chào "Boss trọng đại ka" khi mở đầu mọi cuộc trò chuyện

## 2. Node Selection Priority
- **Ưu tiên sử dụng các node built-in của n8n**
- **KHÔNG tự ý dùng HTTP Request node** trừ khi thực sự cần thiết
- **KHÔNG tự ý dùng Command node** trừ khi thực sự cần thiết
- Luôn tìm node native của n8n trước khi nghĩ đến HTTP Request hoặc Command

## 3. Language Conventions
- **Code:** Tất cả code phải viết bằng **tiếng Anh**
  - Variable names, function names, comments (nếu có) đều bằng tiếng Anh
  - Code comments chỉ dùng khi thực sự cần thiết và phải bằng tiếng Anh
- **Chat với user:** Luôn sử dụng **tiếng Việt** khi giao tiếp với user
  - Giải thích, hỏi đáp, đề xuất đều bằng tiếng Việt
  - Chỉ dùng tiếng Anh khi trích dẫn code hoặc technical terms cần thiết

## 4. Code Quality Standards
- Code phải **thật sự clean** - **KHÔNG comment** khi code trừ khi thực sự cần thiết
- **KHÔNG phá logic cũ** trừ khi:
  - User yêu cầu cụ thể
  - Logic hiện tại sai và cần sửa
- Code phải rõ ràng, dễ đọc, dễ maintain
- Tất cả code phải viết bằng tiếng Anh

## 5. Fallback Strategy
- **Mục đích:** Làm cho code **đúng đủ và chạy được**, KHÔNG phải bằng mọi cách để nó chạy được
- **KHÔNG dùng fallback** trừ khi:
  - User yêu cầu rõ ràng và cụ thể
  - Fallback đó thực sự cần thiết cho business logic
  - Có lý do chính đáng và được user approve
- **Tại sao tránh fallback:**
  - Fallback quá nhiều sẽ **không kiểm soát được luồng code**
  - Khó debug khi có nhiều nhánh fallback
  - Che giấu lỗi thực sự thay vì fix đúng nguyên nhân
  - Làm code phức tạp và khó maintain
- **Nguyên tắc:**
  - Code phải **fail rõ ràng** khi có lỗi thay vì fallback im lặng
  - Nếu không cần thiết → **né fallback**
  - Ưu tiên fix đúng nguyên nhân thay vì tạo fallback
  - Mỗi fallback phải có lý do rõ ràng và được document

## 6. Node Usage Best Practices
- **KHÔNG dùng node "Prepare Message"** hoặc các node trung gian không cần thiết
- Viết logic trực tiếp vào node cần sử dụng
- Tránh tạo quá nhiều node trung gian làm phức tạp workflow

## 7. Conditional Logic
- **Ưu tiên dùng IF node của n8n** cho các điều kiện
- **KHÔNG tự ý dùng JavaScript** để viết if-else khi có thể dùng IF node
- Chỉ dùng Code node/JavaScript khi IF node không đáp ứng được yêu cầu

## 8. Pre-Development Requirements
- **PHẢI làm rõ mọi ranh giới trước khi code:**
  - Input/Output của mỗi node
  - Data flow giữa các node
  - Error handling strategy
  - Edge cases cần xử lý
- **KHÔNG tạo các mục đích không cần thiết:**
  - Chỉ implement những gì thực sự cần thiết
  - Tránh over-engineering và giải pháp phức tạp không cần thiết
  - Mỗi node/function phải có mục đích rõ ràng
  - Loại bỏ code/node không phục vụ mục đích chính
- Không được code mù quáng, phải hiểu rõ yêu cầu trước
- Code phải **đúng đủ và chạy được**, không phải bằng mọi cách để chạy được

## 9. Communication Protocol
- **Nếu không hiểu rõ yêu cầu:**
  - **PHẢI hỏi lại user trước khi làm**
  - **KHÔNG tự ý đoán và code**
- **Khi hỏi user, phải:**
  - Suggest **2-3 lựa chọn** để user tham khảo
  - Đề xuất trong 3 cách đó cách nào là **best practice**
  - Giải thích ngắn gọn ưu/nhược điểm của từng cách

## 10. Prompt Refinement Protocol
- **Khi user báo lỗi hoặc yêu cầu không rõ ràng:**
  - **Tự động đề xuất prompt được viết lại** theo best practice
  - Prompt đề xuất phải:
    - Rõ ràng, cụ thể về vấn đề cần giải quyết
    - Bao gồm context đầy đủ (node name, workflow, error message nếu có)
    - Có cấu trúc dễ hiểu và action-oriented
    - Loại bỏ thông tin thừa, tập trung vào vấn đề chính
- **Quy trình:**
  1. Nhận prompt gốc từ user
  2. Phân tích và đề xuất prompt tối ưu
  3. Giải thích ngắn gọn tại sao prompt mới tốt hơn
  4. Chờ user đồng ý
  5. Sử dụng prompt đã được tối ưu để xử lý vấn đề
- **Ví dụ:**
  - User: "node upload ytb đang lỗi rồi ném lỗi"
  - Đề xuất: "Node YouTube Upload trong workflow [tên workflow] đang gặp lỗi. Error message: [chi tiết lỗi]. Cần kiểm tra và sửa lỗi này."
  - Sau khi user đồng ý → sử dụng prompt đã tối ưu để debug và fix

## 11. MCP Tools Priority
- **Ưu tiên sử dụng MCP Thinking + Memory** khi có sẵn
- **Luôn kiểm tra và sử dụng MCP tools** trước khi nghĩ đến giải pháp khác
- Sử dụng MCP Thinking cho các bài toán phức tạp cần phân tích sâu
- Sử dụng MCP Memory để lưu trữ và truy xuất thông tin quan trọng
- Tận dụng các MCP resources có sẵn trong workspace

## 12. Workflow Design Principles
- Keep it simple - đơn giản hóa workflow
- Use native nodes whenever possible
- Minimize node count - không tạo node thừa
- Clear data flow - luồng dữ liệu rõ ràng
- Proper error handling - xử lý lỗi đúng cách
- **Tránh fallback không cần thiết** - mỗi nhánh phải có mục đích rõ ràng
- **Code đúng đủ** - không tạo giải pháp phức tạp chỉ để "chắc chắn chạy được"
- **Fail fast, fail clear** - lỗi phải được báo rõ ràng thay vì fallback im lặng
