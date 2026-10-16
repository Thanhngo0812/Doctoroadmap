# 19o — Gỡ ba tuỳ chọn đã đo là thua

**Nguồn chân lý:** [spec đổi mặc định chuỗi gộp](../../doc/doi-mac-dinh-chuoi-gop-spec.md), pha 5; số đo ở
[17i](../../report/v4-17i-nghiem-thu-chuoi-gop-luot-1-2026-10-16.md) và [nghiên cứu](../../report/nghien-cuu-cai-thien-chuoi-gop-2026-10-16.md).
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD · **Chặn bởi:** 19m (nên làm sau 19n) · **Trạng thái:** chờ

## Cần làm

- **Gỡ chế độ neo gom vào A5** (`a5`): bỏ prompt và schema A5 gộp, bỏ nhánh thu neo trong lời mô tả và kiểm.
- **Gỡ nguồn đề cử theo mô tả nháp** và các tham số top-k, ngưỡng, bật/tắt của nó.
- **Gỡ gom lô lời phán sửa:** cỡ lô, prompt lô, bộ kiểm từng mục.
- **Gỡ tuỳ chọn chọn chuỗi** khỏi đường chạy mới, vì chỉ còn một chuỗi. Đường lớp tên giữ như 19n.
- Cập nhật `.env.example` và README.

## Nghiệm thu

- [ ] Cấu hình không còn các mục kể trên; đặt biến môi trường cũ thì bị bỏ qua có cảnh báo, hoặc báo lỗi rõ.
- [ ] Canonical của chuỗi gộp trên fixture thật vẫn ra cùng payload với cấu hình mặc định trước khi gỡ.
- [ ] Toàn bộ test qua; test của tuỳ chọn đã gỡ được gỡ cùng.
