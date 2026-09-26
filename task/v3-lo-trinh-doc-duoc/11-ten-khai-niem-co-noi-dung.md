# 11 — Tên khái niệm có nội dung

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R9 · **Ai:** nhân viên · **Phụ thuộc:** 05 · **Chi phí mô hình:** ≈ 0,02 USD / tài liệu

**Trạng thái:** chờ giao

## Việc cần làm
- Từ chung ("Definition", "Theorem", "Định nghĩa", "Định lý" đứng một mình) không là khái niệm: loại ở bước neo (`not_subject_matter`,
  lý do "từ chung").
- Tên chỉ là nhãn đánh số ("Tính chất 1", "Định lý 4", "Hệ quả 2", "Proposition 3.2") nhận `display_name` ngắn sinh từ câu neo, mã kiểm
  từ nội dung có trong câu neo; nhãn cũ thành alias. `node_id`, `name` gốc giữ nguyên — bộ vàng không đổi. A10 hiển thị `display_name`.

## Tệp liên quan
`domain/anchors.py` hoặc use case riêng sau neo, `application/use_cases/build_roadmap.py` (hiển thị).

## Nghiệm thu
- Test nhận diện nhãn đánh số và từ chung (tiếng Việt, tiếng Anh); test kiểm từ của `display_name`.
- **Tôi kiểm:** doc-1 không còn "Tính chất 1…4", "Định lý 4…7" trên lộ trình; doc-2 không còn "Definition", "Theorem".
