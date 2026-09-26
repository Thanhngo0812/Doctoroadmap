# 10 — Danh tính mở rộng

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R8 · **Ai:** nhân viên · **Phụ thuộc:** — · **Chi phí mô hình:** ≈ 0,05 USD / tài liệu

**Trạng thái:** chờ giao

## Việc cần làm
Thêm nguồn ứng viên trong `identity_candidates`:
- chuẩn hoá tên như bước neo (`anchors._compact`: NFKC, bỏ dấu LaTeX, gộp gạch nối);
- viết tắt ↔ tên đầy đủ (chữ đầu các từ, bỏ dấu: CSDL ↔ Cơ sở dữ liệu);
- tên ký hiệu ↔ tên chữ qua tương tự mô tả + câu neo (vector nút sẵn có từ A6, top-3, ngưỡng ghi trong config);
- tiền tố chung chung thêm "hệ ", "phép ".
Phán và luật gộp (nhóm kiểm đủ; người duyệt gộp chạm vàng) giữ nguyên.

## Tệp liên quan
`domain/identity.py`, `application/use_cases/judge_identity.py`.

## Nghiệm thu
- Test mỗi nguồn: CSDL/Cơ sở dữ liệu; Upper triangular matrix/Upper-triangular matrix; Độc lập tuyến tính cực đại/Hệ độc lập tuyến
  tính cực đại; một cặp chỉ giống mô tả được đưa ra xét nhưng vẫn cần phán `same` mới gộp.
- **Tôi kiểm:** các cặp trong báo cáo L6 được đưa ra xét; đọc các gộp mới trên doc-1, doc-2, doc-6.
