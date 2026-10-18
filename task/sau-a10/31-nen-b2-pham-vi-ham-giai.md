# SA-31 — Nền B2: phạm vi, hàm giải phạm vi, port kho và đồng hồ

**Nguồn chân lý:** [spec Pha B2](../../doc/pha-b2-spec.md), mục 1, 8 (đồng hồ), 9, 12; [ADR 0017](../../doc/adr/0017-pham-vi-phien-la-noi-luu-neo-vao-khai-niem.md).
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** SA-30, vì cùng sửa kho Pha B và `BSettings` · **Trạng thái:** ready-for-agent

## Vì sao

Mọi vé Pha B2 cần ba thứ chung:
- **cách lưu phạm vi** (lộ trình, hoặc module neo vào `node_ids`);
- **một hàm giải phạm vi** sang module của đồ thị hiện hành;
- **vài khả năng kho và thời gian** mà lõi chưa có.

Làm phần này trước thì các vé sau chỉ còn dùng lại.

Số đo dẫn tới việc neo vào khái niệm: doc-1 từ v45 sang v53 có 33 mã module vẫn còn, nhưng chỉ 2 module giữ nguyên tập khái niệm; 202/205 `node_id` còn
nguyên.

## Cần làm

- **Đối tượng phạm vi `scope-1`**, theo spec mục 1:
  - `roadmap`;
  - `module`, gồm `node_ids`, `module_id_at_creation`, `graph_version_at_creation`.
- **Hàm giải phạm vi**, là hàm thuần ở domain:
  - nhận phạm vi và đồ thị học hiện hành;
  - trả `module_id` (hay null), `stale` và `jaccard`;
  - ngưỡng `scope_remap_min_jaccard` = 0,5;
  - hoà điểm thì chọn module có thứ tự nhỏ hơn.
- **Port kho:**
  - thêm `delete_record(kind, record_id)`;
  - liệt kê bản ghi có lọc theo `doc_id`.

  Cả hai bản cài (JSON và bộ nhớ) qua chung bộ test hợp đồng.
- **Port đồng hồ:** "bây giờ" và "ngày hôm nay" theo `spend_day_timezone`, cộng bản giả cho test.
- **Thêm vào `BSettings` mọi khoá ở spec mục 12.** Prompt và luật kiểm lấy giá trị từ đây.
- **Dữ liệu thử:** một cặp đồ thị tổng hợp v1, v2 cùng tập khái niệm nhưng chia module khác nhau. Có ít nhất ba ca:
  - một module giữ nguyên;
  - một module bị tách;
  - một module "biến mất", tức không module nào của v2 đạt Jaccard ≥ 0,5.
- **Lệnh CLI giải phạm vi:** nhận tài liệu, phạm vi lưu dạng JSON và phiên bản đồ thị; in kết quả giải. 0 USD.

## Tiêu chí nghiệm thu

- [ ] Test hàm giải phạm vi, mỗi cái thấy đỏ trên bản sai:
  - phạm vi lộ trình trả null, không stale;
  - module giữ nguyên trả đúng module;
  - module bị tách trả phần có Jaccard cao nhất;
  - module biến mất trả `stale = true`;
  - hoà điểm thì chọn module có thứ tự nhỏ hơn;
  - giải sai theo `module_id_at_creation` (bản sai cố ý) phải đỏ trên ca module bị tách.
- [ ] Chạy lệnh giải phạm vi trên đồ thị thật doc-1, với một phạm vi lấy từ v45 giải trên v53. Báo Jaccard và module được chọn cho ba module mẫu.
- [ ] Test hợp đồng kho: `delete_record` và lọc theo `doc_id` cho cùng kết quả ở cả hai bản cài.
- [ ] Đổi một khoá mới trong `BSettings` thì giá trị dùng ở chỗ đọc đổi theo.
- [ ] Test kiến trúc vẫn xanh: application không import infrastructure; domain chỉ dùng thư viện chuẩn.

## Ngoài vé

Phiên, tiến độ, thư viện, trần chi: các vé 32–42.
