# 19d — Neo "một khái niệm" mặc định; `--names-only` dùng chuỗi v3

**Nguồn chân lý:** [spec đổi mặc định chuỗi gộp](../../doc/doi-mac-dinh-chuoi-gop-spec.md), pha 1b.
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không · **Trạng thái:** sẵn sàng giao

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

- [ ] Không đặt cấu hình thì chuỗi gộp dùng neo `single`.
- [ ] Đặt mặc định là `gop`, thì `--names-only` và `--prepare` không có `--upstream-chain` vẫn chạy chuỗi v3. Có `--upstream-chain gop` thì báo lỗi.
- [ ] Băm config v3 giữ nguyên. Toàn bộ test qua.
