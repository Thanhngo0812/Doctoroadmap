# 08 — Hiển thị tiên quyết rút gọn và phụ thuộc cấp module

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R6 · **Ai:** nhân viên · **Phụ thuộc:** 07 · **Chi phí mô hình:** 0

**Trạng thái:** chờ giao

## Việc cần làm
- Dòng "cần:" (HTML và payload `display_prerequisites`) chỉ hiện cạnh của rút gọn bắc cầu, tối đa 3, kèm "và N khái niệm khác";
  `prerequisites` đầy đủ giữ nguyên.
- `module_dependencies`: module M cần N khi có cạnh (không mềm) từ khái niệm của N tới khái niệm của M, N ≠ M; hiện "Học trước:
  module …" (rút gọn bắc cầu ở cấp module).
- `roadmap-target` trả các module cần học (đóng theo phụ thuộc module) và khái niệm đích trong module cuối.

## Tệp liên quan
`application/use_cases/build_roadmap.py` (`render_roadmap_html`, `target_roadmap`), `domain/sequence.py`, CLI `roadmap-target`.

## Nghiệm thu
- Test: a → b → c và a → c: "cần" của c chỉ hiện b; phụ thuộc module không có cạnh bắc cầu; target roadmap trả đúng module.
- **Tôi kiểm:** "Hệ phương trình tuyến tính" (doc-1) hiện ≤ 3 tiên quyết; lộ trình tới "Cơ sở" đọc được theo module.
