# DG-07 — B5 "LLM đọc thẳng"

**Nguồn:** spec mục 11 (B5), 8 (truy nguyên, thước phụ Q38); kế hoạch Q36, Q38, Q39 · **Ai:** Claude viết lời nhắc v1 (`evaluation/giao-thuc/b5/`); agent B
làm công cụ; Claude chạy dry-run và lượt thật trên tập phát triển ngày 01/11 · **Chi phí:** 0 khi cài (mô hình giả); lượt thật vài USD, chủ dự án duyệt ·
**Chặn bởi:** DG-04 · **Hạn:** 31/10 · **Trạng thái:** ready-for-agent

## Làm được gì

Một lệnh chạy B5 trên một cuốn: flash-lite đọc văn bản sách, rồi trả theo lược đồ JSON:
- khái niệm, kèm câu định nghĩa nguyên văn và trang;
- quan hệ tiên quyết, kèm câu bằng chứng và trang;
- lộ trình (dãy và module).

Bộ chuyển đổi đưa kết quả sang hợp đồng `danh-gia-xuat-1`, với `cau_truc` để `null`. Có hai chế độ:
- **B5a:** một lời gọi cho cả cuốn;
- **B5b:** mỗi chương một lời gọi, kèm danh sách khái niệm của các chương trước.

Thêm vào đó:
- K biến thể định dạng lời nhắc, giữ nghĩa, chọn bằng seed;
- gọi mô hình qua adapter Gemini sẵn có của dự án, để chạy đúng transport và ghi usage;
- dry-run báo số token vào ước tính, trần token đầu ra, và dự toán USD.

## Tiêu chí

- [ ] Parser chạy trên phản hồi đã ghi, không gọi mạng. JSON hỏng hay thiếu trường thì lượt đó thất bại, có lý do, không vá.
- [ ] Đầu ra bị cắt vì chạm trần token được phát hiện và ghi cờ. Đây là thước "độ phủ theo độ dài sách".
- [ ] B5b hợp nhất khái niệm giữa các chương **chỉ** theo tên trùng sau chuẩn hoá. Không thêm bước gộp thông minh, vì B5 phải là cách làm thẳng.
- [ ] Hợp đồng B5 qua validator DG-04.
- [ ] Lời nhắc so với tệp lời nhắc đã commit. Không nhúng lời nhắc vào mã.
- [ ] Bảng phá, gồm ít nhất: nhận câu trích mà không kiểm trong sách; bỏ qua cờ cắt; gộp khái niệm khác tên.

**Claude, sau ghép:** dry-run trên một cuốn phát triển để chọn B5a hay B5b; chạy K lượt trên tập phát triển ngày 01/11; báo F1 quan hệ và tỉ lệ bằng chứng có thật
so với hệ chính, theo luật Q39.
