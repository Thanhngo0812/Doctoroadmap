# 19o — Gỡ ba tuỳ chọn đã đo là thua

**Nguồn chân lý:** [spec đổi mặc định chuỗi gộp](../../doc/doi-mac-dinh-chuoi-gop-spec.md), pha 5; số đo ở
[17i](../../report/v4-17i-nghiem-thu-chuoi-gop-luot-1-2026-10-16.md) và [nghiên cứu](../../report/nghien-cuu-cai-thien-chuoi-gop-2026-10-16.md).
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD · **Chặn bởi:** 19m (nên làm sau 19n) · **Trạng thái:** xong 2026-10-17 — Claude kiểm đạt, commit chung với 19n

## Cần làm

- **Gỡ chế độ neo gom vào A5** (`a5`): bỏ prompt và schema A5 gộp, bỏ nhánh thu neo trong lời mô tả và kiểm.
- **Gỡ nguồn đề cử theo mô tả nháp** và các tham số top-k, ngưỡng, bật/tắt của nó.
- **Gỡ gom lô lời phán sửa:** cỡ lô, prompt lô, bộ kiểm từng mục.
- **Gỡ tuỳ chọn chọn chuỗi** khỏi đường chạy mới, vì chỉ còn một chuỗi. Đường lớp tên giữ như 19n.
- Cập nhật `.env.example` và README.

## Nghiệm thu

- [x] Cấu hình không còn các mục kể trên; đặt biến môi trường cũ thì bị bỏ qua có cảnh báo, hoặc báo lỗi rõ.
- [x] Canonical của chuỗi gộp trên fixture thật vẫn ra cùng payload với cấu hình mặc định trước khi gỡ.
- [x] Toàn bộ test qua; test của tuỳ chọn đã gỡ được gỡ cùng.

## Bàn giao nhân viên

Đã gỡ ba tuỳ chọn và selector khỏi API/CLI; sửa `.env.example`, README và danh mục
prompt. Biến cũ trong môi trường/dotenv bị bỏ qua có cảnh báo nêu tên.
15 ca kiểm âm đã thấy đỏ trước sửa, xanh sau sửa. Payload gộp mặc định giữ nguyên
hash; names-only/prepare giữ cả payload và config hash. Toàn kho **1.535 test qua**,
thêm **1 ca tương thích bộ chấm v3 qua riêng**. Chi phí mô hình **0 USD**.
[Báo cáo 19n–19o](../../report/v4-19no-go-stage-va-tuy-chon-cu-2026-10-17.md).

## Kiểm của Claude 2026-10-17 — đạt

- **Kho thật, dry-run, 0 USD, không ghi artifact:**
  - `roadmap --dry-run` doc-1 tái dùng mọi stage chuỗi gộp;
  - `--stop-after identity` bị từ chối ở bước đọc lệnh;
  - doc-2 (canonical v3) nhận lỗi "chạy lại A4";
  - `DOC2ROADMAP_UPSTREAM_CHAIN=v3` chỉ sinh cảnh báo nêu tên biến.
- **Hệ quả cần biết:** 19o bỏ các mục cấu hình nên băm cấu hình canonical đổi. Lần `a4` kế tiếp trên tài liệu cũ sẽ embed lại tên và dựng canonical
  mới. Payload không đổi (test đóng băng của nhân viên). `a4 --dry-run` doc-1 báo phần embedding "sẽ chạy", các phần còn lại "chưa biết".
- **Commit:** tách bỏ hai hunk Pha B trong `cli/main.py` (module của Pha B chưa được track) và các thay đổi A1/D-01 đang dở. Chạy toàn bộ test trên
  checkout sạch của commit.
