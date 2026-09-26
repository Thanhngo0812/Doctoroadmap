# 10 — Danh tính mở rộng

**Nguồn chân lý:** [spec v3](../../doc/v3-lo-trinh-doc-duoc-spec.md), R8 · **Ai:** nhân viên · **Phụ thuộc:** — · **Chi phí mô hình:** ≈ 0,05 USD / tài liệu

**Trạng thái:** đã cài đặt và chạy kiểm chứng (2026-09-26); chưa duyệt xuất bản các gộp mới

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

## Kiểm thử của nhân viên

Đã thấy test đỏ trước sửa, test bốn nguồn và luật gộp đều xanh. `a10-identity-v2`, top-3 hợp hai chiều, cosine ≥ 0,85
ghi trong config; vector mô tả A6 đề cử, câu neo đưa vào phán, không gọi thêm embedding.
Đủ **6/6 cặp L6** được đề cử; 5 same, Upper triangular/Upper-triangular được phán different do mô tả R trong QR
khác định nghĩa tổng quát. Không ép gộp để khớp danh sách lỗi.

Đã chạy doc-1/doc-2/doc-6 trên teaching v33/v27/v9: 378/723/31 lời gọi; 12/25/1 node gộp; 0/3/0 nhóm mở;
cả ba DAG, không cạnh treo. Chi telemetry **0,28330450 USD** trong mức 1,50 USD chủ dự án duyệt. Không chạy A8.
Kết quả nằm ở `artifacts/v3-identity-evaluation`, không thay kho mặc định; tái dùng 3/3 với 0 lời gọi.

**Chưa qua cổng xuất bản:** hai gộp mới thực sự chạm vàng doc-1 cần người duyệt; Q6 doc-1 1/39 → 3/39; doc-2 có
ba nhóm mở và một số phán same đáng nghi (trường hợp riêng/định lý bằng nhau bị coi là danh tính). CSDL lấy đại diện
ở đề cương, cần quyết cách giữ trạng thái dạy của nhóm trước vé 07. Không đổi luật phán/gộp ngoài phạm vi vé.
Đã xuất `review-pending.json` với quyết định để trống. [Toàn bộ số, đọc/phán và điểm cần duyệt](../../report/v3-01-03-10-ket-qua-2026-09-26.md).
