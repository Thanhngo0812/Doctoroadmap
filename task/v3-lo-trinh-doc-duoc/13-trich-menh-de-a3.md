# 13 — Trích mệnh đề có tên ở A3

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R13 · **Ai:** nhân viên · **Phụ thuộc:** sau vé 07 v2 (tập giữ lại) · **Chi phí mô hình:** chạy lại A3–A10 mọi tài liệu

**Trạng thái:** chờ giao

## Việc cần làm
- A3 trích định lý/mệnh đề/công thức/phương pháp có tên (và kết quả được sách dạy như một mục) thành nút `ket_qua`, tên nội dung.
- **Trước khi làm:** kế hoạch ánh xạ bộ vàng (doc-1, doc-2, xstk, doc-4 gắn `concept_hash` của canonical cũ) — hoặc giữ canonical cũ
  cho chấm và ánh xạ nút mới về nút cũ, hoặc gán lại vàng. Chủ dự án chọn.

## Nghiệm thu
- Test trích trên các mẫu T7 bị thiếu (trị riêng là nghiệm đa thức tối tiểu; phương pháp Cramer; bất đẳng thức tam giác…).
- **Tôi kiểm:** chấm lại Q3 bằng T7 (bảng đối chiếu đã có) — kỳ vọng ≥ 90%.

## Bổ sung theo nguyên tắc đa ngôn ngữ (Claude, 2026-09-26; spec v3 R16)

Làm cùng lượt chạy lại A3 của vé này: thay cụm "definition/denote/called" trong `_defined_script_symbol` bằng bằng chứng trong tài liệu —
câu bằng chứng A3 (đã kiểm có trong văn bản) chứa ký hiệu đó, và ký hiệu còn xuất hiện ở ít nhất một chunk khác. Test với câu định
nghĩa ký hiệu bằng tiếng Việt và tiếng Pháp.
