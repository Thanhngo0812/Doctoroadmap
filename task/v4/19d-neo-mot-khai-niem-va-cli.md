# 19d — Neo "một khái niệm" mặc định; `--names-only` dùng chuỗi v3

**Nguồn chân lý:** [spec đổi mặc định chuỗi gộp](../../doc/doi-mac-dinh-chuoi-gop-spec.md), pha 1b.
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không · **Trạng thái:** đã cài và kiểm chứng 2026-10-17

## Vì sao

- **Neo.** Chế độ neo gom vào A5 tốn tiền như neo riêng, nhưng phán "được dạy" dễ dãi hơn C8: doc-4 có thêm 67 khái niệm chỉ được nhắc vào dãy học.
  Chủ dự án đã duyệt neo "một khái niệm" làm mặc định (17i mục 7–8).
- **CLI.** Khi mặc định đổi sang `gop` (vé 19m), `a4 --names-only` sẽ dừng hẳn, mà D-01 gọi đúng lệnh này.

## Cần làm

- **Chế độ neo mặc định là `single`**, ở cả cấu hình lẫn hàm dựng stage canonical. Cập nhật `.env.example`.
- **`a4 --names-only` và `a4 --prepare`** không có `--upstream-chain` tường minh thì tự dùng chuỗi `v3`, kể cả khi cấu hình mặc định là `gop`. Có
  `--upstream-chain gop` tường minh thì vẫn báo lỗi như hiện nay.
- **Chưa đổi chuỗi thượng nguồn mặc định.** Việc đó thuộc vé 19m.

## Nghiệm thu

- [x] Không đặt cấu hình thì chuỗi gộp dùng neo `single`.
- [x] Đặt mặc định là `gop`, thì `--names-only` và `--prepare` không có `--upstream-chain` vẫn chạy chuỗi v3. Có `--upstream-chain gop` thì báo lỗi.
- [x] Băm config v3 giữ nguyên. Toàn bộ test qua.

**Kiểm chứng 2026-10-17:** 8 test riêng kiểm mặc định, gọi neo riêng và CLI bằng fixture thật/mô hình giả; 3 test đỏ trước sửa. Băm v3 đóng băng vẫn qua. Chi tiết ở [báo cáo 19d–19e](../../report/v4-19de-mac-dinh-va-pha-b-2026-10-17.md).

Toàn kho: **1.617 test qua**, xem [báo cáo tích hợp](../../report/v4-19-phan-tich-va-kiem-chung-2026-10-17.md).
