# 03 — Vai trò vùng văn bản

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R1 · **Ai:** nhân viên · **Phụ thuộc:** — · **Chi phí mô hình:** 0

**Trạng thái:** chờ giao

## Việc cần làm
- `Section` mang `role` ∈ `noi_dung`, `bai_tap`, `de_cuong`, `mo_dau`, `hanh_chinh`; chunk thừa hưởng vai trò section của nó.
- Luật thuần theo mẫu tiêu đề và vị trí (danh sách mẫu trong spec v3 R1); trang mục lục đã phát hiện (`_toc_runs`) là `de_cuong`;
  mọi thứ trước tiêu đề chương có số đầu tiên là `mo_dau` trừ khi tiêu đề nói khác.
- Lưu vào artifact chunks (thêm trường, cấu hình chunk đổi → tăng `CHUNK_ALGORITHM_ID`); cung cấp hàm `chunk_roles(chunks)` cho các
  stage sau.
- **Tái dùng:** vai trò tính lại được từ cây section có sẵn mà không nhập lại PDF (ghi rõ cách).

## Tệp liên quan
`domain/chunking.py`, `domain/models.py` (`Section`, `Chunk`), `application/use_cases/ingest_document.py`.

## Nghiệm thu
- Test mỗi mẫu tiêu đề (tiếng Việt, tiếng Anh, có/không dấu; "Exercises 3B", "Câu hỏi ôn tập", "Nội dung môn học", "Preface",
  "Lời nói đầu", "Mục lục"); test vùng `bai_tap` đóng khi gặp tiêu đề cùng cấp; test phần trước chương đầu là `mo_dau`.
- **Tôi kiểm:** vai trò trên doc-1 (đề cương học phần, "Bài tập chương n", "Đề số n"), doc-2 (Preface, "Exercises nX"), doc-6
  ("Nội dung môn học", slide "Nội dung" lặp), nhap-mon-ml ("MỞ ĐẦU") — liệt kê section theo vai trò và đọc.
