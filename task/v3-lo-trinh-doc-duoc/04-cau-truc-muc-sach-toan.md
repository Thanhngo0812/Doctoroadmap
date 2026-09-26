# 04 — Cấu trúc mục kiểu sách toán

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R2 · **Ai:** nhân viên · **Phụ thuộc:** 03 · **Chi phí mô hình:** 0

**Trạng thái:** chờ giao

## Việc cần làm
- Nhận tiêu đề mục dạng "3C Matrices", "Section 3C …" là cấp mục dưới "Chapter 3".
- Mục đánh số kết quả ("3.36 definition: …", "5.1 definition: operator", "Định lý 2.1.", "Ví dụ 3.") là **khối** nằm trong mục,
  không mở section mới.
- Vùng `bai_tap` ("Exercises 3B") đóng khi gặp tiêu đề mục kế tiếp.
- Tự nhận theo mẫu, không cờ theo tài liệu; `--heading-scheme vn-textbook` giữ nguyên.

## Tệp liên quan
`domain/chunking.py` (`_heading_number_level`, `_false_heading_reason`, `_chapter_sequences`).

## Nghiệm thu
- Test cây mục cho mẫu Axler (Chapter 3 → 3A/3B/3C → khối "3.36 definition") và cho "Exercises 3B" đóng trước "3C".
- **Tôi kiểm:** nhập lại doc-2 (không tốn tiền), đọc cây mục chương 3: nội dung "Matrices" phải nằm dưới "3C", không dưới
  "Exercises 3B". Hash chunk của doc-1, xstk, doc-4 không đổi (luật không kích hoạt) — nếu đổi phải báo.
