# 19m — Bật mặc định chuỗi gộp, kèm tài liệu

**Nguồn chân lý:** [spec đổi mặc định chuỗi gộp](../../doc/doi-mac-dinh-chuoi-gop-spec.md), pha 4.
**Ai:** nhân viên (cấu hình, README) + Claude (ADR, `CONTEXT.md`, spec-addendum, bàn giao Pha B) · **Chi phí mô hình:** 0 USD · **Chặn bởi:** 19l qua
cổng · **Trạng thái:** chờ

## Cần làm

**Nhân viên:**
- chuỗi thượng nguồn mặc định đổi từ `v3` sang `gop`; cập nhật `.env.example`;
- README ghi cách chọn chuỗi, và rằng chạy `a4` mặc định trên tài liệu cũ sẽ đổi chuỗi của lần `roadmap` sau.

**Claude:**
- **ADR 0016:**
  - danh tính là một phần của gộp ở A4;
  - neo và trạng thái dạy quyết ở A5, mỗi khái niệm một lời;
  - provenance rời chuỗi;
  - vì sao bỏ neo gom A5, đề cử theo mô tả và gom lô lời phán sửa.
- **ADR 0004:** thêm mục cập nhật.
- **`CONTEXT.md`, spec-addendum (sơ đồ A1 → A10), dòng "Lịch" của spec gộp khâu.**
- **Tệp bàn giao cho phiên Pha B:** id node đổi; cache bài giảng và quiz cũ mất hiệu lực.

Tài liệu và đổi cấu hình vào cùng một đợt commit.

## Nghiệm thu

- [ ] Không đặt cấu hình thì `a4` và `roadmap` chạy chuỗi gộp. `a4 --names-only` vẫn chạy chuỗi v3 (19d).
- [ ] Tài liệu không còn mô tả ba stage cũ như luồng mặc định. Toàn bộ test qua.
