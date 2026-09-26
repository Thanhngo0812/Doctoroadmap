# 07 — Dãy học chỉ gồm khái niệm được dạy

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R5 · **Ai:** nhân viên · **Phụ thuộc:** 05 · **Chi phí mô hình:** 0

**Trạng thái:** chờ giao

## Việc cần làm
- A10 chỉ xếp `taught` và `uncertain` vào dãy học và module. `mentioned_only`, `unchecked` rời dãy học; cạnh qua chúng co lại như
  nút bị loại (`bypass_excluded`).
- Hiển thị: mỗi module có mục "Nhắc tới" cho khái niệm chỉ-được-nhắc lần đầu (trong `noi_dung`) thuộc module đó; khái niệm chỉ có trong
  đề cương vào khối "Tổng quan môn học" đầu lộ trình, không phải một module.
- Payload giữ danh sách `mentioned_nodes` riêng; bộ chấm Q6 coi khái niệm vàng nằm ở danh sách này là thiếu đầu (không lặng lẽ bỏ).

## Tệp liên quan
`application/use_cases/build_roadmap.py`, `domain/sequence.py`, `application/use_cases/a8_score.py` (tên thiếu đầu).

## Nghiệm thu
- Test: khái niệm chỉ-được-nhắc không có trong `sequence`; cạnh A(taught) → M(mentioned) → B(taught) thành A → B; M không kéo B ra
  sau vị trí của M.
- **Tôi kiểm:** doc-1 mục 3.5 không còn bị tách (Độ dài, Góc, Gram-Schmidt về lại gần Tích vô hướng); "Định lý về số chiều" về mục
  4.2; doc-6 và doc-3 dãy học chỉ còn khái niệm được dạy.
