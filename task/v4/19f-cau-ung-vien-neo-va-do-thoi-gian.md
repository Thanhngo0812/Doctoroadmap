# 19f — Dựng câu ứng viên neo một lần, đo thời gian đủ phần

**Nguồn chân lý:** [spec đổi mặc định chuỗi gộp](../../doc/doi-mac-dinh-chuoi-gop-spec.md), pha 2 mục 1–2.
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không · **Trạng thái:** đã cài và kiểm chứng 2026-10-17

## Vì sao

- **Dựng câu ứng viên neo chậm.** Bước này chuẩn hoá lại toàn bộ chunk cho từng khái niệm: khoảng 200 giây trên doc-4 (nghiên cứu mục 4).
- **Thời gian đo thiếu.** Khoảng 45% thời gian canonical doc-4 nằm ngoài mọi phép đo phần, và stage đặt tên module không ghi thời gian.

## Cần làm

- Chuẩn hoá chunk **một lần** cho cả tài liệu, rồi dùng lại cho mọi khái niệm. Câu ứng viên phải giống hệt trước.
- Đo phần cho các đoạn CPU của canonical: dựng node, dựng đồ thị đề cử, đề cử thêm, chuẩn bị neo.
- Stage đặt tên module ghi thời gian vào `stats`.
- Không đổi config hay khoá cache.

## Nghiệm thu

- [x] Test trên fixture thật: câu ứng viên trước và sau cùng băm.
- [x] Manifest canonical có số đo cho từng đoạn CPU kể trên; manifest đặt tên module có thời gian.
- [x] Ghi số giây trước và sau cho một tài liệu lớn có sẵn trong kho, 0 USD, chạy ở kho thử.
- [x] Khoá cache không đổi. Toàn bộ test qua.

**Kiểm chứng 2026-10-17:** doc-4 (630 node, 671 chunk), `prepare_anchors`: 257,526 → 38,667 giây (nhanh hơn 6,66 lần), băm ứng viên và băm vùng ngoài nội dung giống hệt. Fixture thật và phép đo CPU: 60 test qua. Chi tiết ở [báo cáo 19f–19h](../../report/v4-19fh-neo-va-song-song-2026-10-17.md).

Toàn kho: **1.617 test qua**, xem [báo cáo tích hợp](../../report/v4-19-phan-tich-va-kiem-chung-2026-10-17.md).
