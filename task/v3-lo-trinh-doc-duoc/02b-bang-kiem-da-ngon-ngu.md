# 02b — Bảng kiểm đọc được không phụ thuộc ngôn ngữ

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R11 (sửa 2026-09-26) · **Ai:** **tôi** (công cụ kiểm thử) ·
**Phụ thuộc:** 03 · **Chi phí mô hình:** 0

**Trạng thái:** chờ làm

## Vì sao
`scripts/doc-lo-trinh/kiem_doc_duoc.py` dùng regex tiếng Việt/tiếng Anh: `NON_TEACHING` cho vùng không dạy, `NUMBERED_LABEL` và `GENERIC`
cho tên khái niệm vô nghĩa. Với tài liệu ngôn ngữ khác, bảng kiểm báo 0 vi phạm dù lộ trình sai.

## Việc cần làm
- "module 1 ngoài bài giảng" và "tên từ vùng không dạy": vùng của module lấy từ vai trò section trong artifact chunks (R1). Version chunks
  chưa có vai trò thì tính bằng `assign_section_roles` trên cây đã lưu.
- "tên khái niệm vô nghĩa": họ nhãn trong chính tài liệu như R9 (tiền tố đi với ít nhất hai số khác nhau; tên đúng bằng tiền tố là từ chung).
- Chạy lại mốc "trước" trên sáu tài liệu phát triển; ghi cả số cũ và số mới vào vé 02 để so được.

## Nghiệm thu
Test nhỏ cho hàm họ nhãn trên tên tổng hợp nhiều ngôn ngữ; bảng mốc mới trong vé 02; mọi chênh giữa mốc cũ và mới được giải thích.
