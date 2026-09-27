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

## Bổ sung (Claude, 2026-09-27)

- Vai trò có thêm `hanh_chinh` và `cuoi_sach` sau khi vé này được viết: cạnh mà **mọi** chunk căn cứ thuộc `de_cuong`, `mo_dau`,
  `hanh_chinh` hoặc `cuoi_sach` đều bị loại (spec R4 đã sửa theo).
- A9 phải đọc vai trò qua `load_role_chunks` đúng version chunks mà đồ thị A8 ghim (như bước neo ở vé 05), không đọc version mới nhất.
- Nghiệm thu trên doc-2 chờ vé 14b (vai trò doc-2 cây cũ đang sai: 104 mục bài giảng bị gắn đề cương). Các tài liệu khác nghiệm thu
  được ngay.
