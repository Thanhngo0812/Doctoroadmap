# 02b — Bảng kiểm đọc được không phụ thuộc ngôn ngữ

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R11 (sửa 2026-09-26) · **Ai:** **tôi** (công cụ kiểm thử) ·
**Phụ thuộc:** 14 (vai trò doc-2 còn sai tới khi cây mục được sửa; chuyển sớm sẽ làm lệch mốc đo) · **Chi phí mô hình:** 0

**Trạng thái:** chờ vé 14. Trong lúc chờ, bản regex hiện có vẫn dùng để nghiệm thu trên sáu tài liệu phát triển (đều vi/en), kèm giới
hạn này.

## Vì sao
`scripts/doc-lo-trinh/kiem_doc_duoc.py` dùng regex tiếng Việt/tiếng Anh: `NON_TEACHING` cho vùng không dạy, `NUMBERED_LABEL` và `GENERIC`
cho tên khái niệm vô nghĩa. Với tài liệu ngôn ngữ khác, bảng kiểm báo 0 vi phạm dù lộ trình sai.

## Việc cần làm
- "module 1 ngoài bài giảng" và "tên từ vùng không dạy": vùng của module lấy từ vai trò section trong artifact chunks (R1). Version chunks
  chưa có vai trò thì tính bằng `assign_section_roles` trên cây đã lưu.
- "tên khái niệm vô nghĩa": họ nhãn trong chính tài liệu như R9 (tiền tố đi với ít nhất hai số khác nhau; tên đúng bằng tiền tố là từ chung).
- Chạy lại mốc "trước" trên sáu tài liệu phát triển; ghi cả số cũ và số mới vào vé 02 để so được.
- *Bổ sung 2026-09-28 (kiểm thử 09b):* bảng kiểm hiện tại đã bỏ sót và báo nhầm:
  - **Bỏ sót:** tên nền lấy từ nút gốc (doc-6 "document> — …"); tên nền chỉ có mã ("Chapter 3", "6B").
  - **Báo nhầm:** "6C Orthogonal Complements and Minimization Problems…" bị coi là "tên từ vùng không dạy" vì regex bắt chữ "Problems".
  - Thêm hai kiểm: "tên nền là gốc" và "tên nền chỉ có mã". Mã nhận bằng họ đánh số của `document_structure`, không bằng từ khoá.
  - Bảng kiểm đã nhận `--goc=<kho>` để chạy trên kho thử.

## Nghiệm thu
Test nhỏ cho hàm họ nhãn trên tên tổng hợp nhiều ngôn ngữ; bảng mốc mới trong vé 02; mọi chênh giữa mốc cũ và mới được giải thích.
