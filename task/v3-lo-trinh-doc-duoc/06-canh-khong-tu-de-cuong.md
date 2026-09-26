# 06 — Cạnh không lấy căn cứ từ đề cương hay lời nói đầu

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R4 · **Ai:** nhân viên · **Phụ thuộc:** 03 · **Chi phí mô hình:** 0

**Trạng thái:** chờ giao

## Việc cần làm
- Luật mới ở A9 (thuần): cạnh `requires` mà **mọi** chunk căn cứ có vai trò `de_cuong` hoặc `mo_dau` bị loại, ghi vào
  `validation_flags` với lý do; cạnh chỉ có căn cứ `bai_tap` thành cạnh mềm (`soft: true`), không ràng buộc dãy học.
- Áp được lên artifact `edges` đã có (không chạy lại A8): chạy lại A9 là đủ.

## Tệp liên quan
`domain/global_validation.py` (`validate_graph_rules`), `application/use_cases/validate_graph.py`, A10 đọc cờ `soft`.

## Nghiệm thu
- Test: cạnh chỉ căn cứ đề cương bị loại; cạnh có một căn cứ `noi_dung` được giữ; cạnh chỉ căn cứ bài tập thành mềm và không ép thứ
  tự trong dãy học.
- **Tôi kiểm:** doc-6 mất chuỗi giả CSDL → … → Dạng chuẩn; nhap-mon-ml mất "SVM ← Siêu tham số" nếu căn cứ chỉ ở "MỞ ĐẦU".
