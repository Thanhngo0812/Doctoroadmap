# 17f — Gom lô lời phán sửa cho cặp bị cắt ngang cụm

**Nguồn chân lý:** [spec gộp khâu trước A8](../../doc/gop-khau-truoc-a8-spec.md), mục 3.2.
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD (test bằng mô hình giả) · **Chặn bởi:** 17e (cùng đoạn mã; lợi chỉ thấy khi số cặp bị cắt tăng)
· **Trạng thái:** đã cài và kiểm chứng (2026-10-16); xem [báo cáo cài đặt và kiểm chứng](../../report/v4-17-phan-tich-va-kiem-chung-2026-10-16.md)

## Vì sao

Nguồn đề cử theo mô tả (vé 17e) biến đồ thị đề cử thành gần như một khối liên thông: ở doc-4, 473/563 nút nằm chung một khối. Số cặp bị cắt ngang
cụm vì vậy tăng mạnh. Hiện mỗi cặp bị cắt tốn một lời phán sửa; trên doc-4 là 307 lời.

## Cần làm

Chỉ áp ở chuỗi `gop`. Chuỗi v3 giữ nguyên.

- Mỗi lời phán sửa chứa nhiều mục, mỗi mục là một khối nhóm như một lời phán sửa hiện nay. Mỗi mục được phán độc lập và trả lời riêng.
- Kích thước lô cấu hình được và nằm trong khoá cache. Lô cỡ 1 cho đúng hành vi hiện nay, dùng làm đối chứng.
- Mục nào trượt kiểm thì chỉ mục đó được hỏi lại riêng. Vẫn hỏng thì cặp đó thành `repair_invalid` như hiện nay. Các mục hợp lệ trong cùng lô được
  dùng ngay.
- Quan hệ đề xuất và luật bắt tự mâu thuẫn vẫn áp cho từng mục.
- Số liệu thêm: số lời phán sửa, số lô, số mục phải hỏi lại riêng. Lời gọi và token tính vào phần "phán sửa" của `cost_summary`.

## Nghiệm thu

- [x] Test qua `execute` của stage canonical, với mô hình giả:
  - các cặp bị cắt được phán theo lô, và số lời gọi đúng bằng số lô;
  - một mục hỏng trong lô chỉ làm mục đó bị hỏi lại riêng; các mục khác giữ lời phán;
  - mục hỏng tiếp thì cặp đó thành `repair_invalid` và giữ tách.
- [x] Cùng phản hồi giả thì lô cỡ 1 và lô cỡ lớn cho cùng tập node.
- [x] Đổi cỡ lô thì khoá cache đổi. Chuỗi v3 giữ nguyên băm config.
- [x] Mỗi luật chặn có ít nhất một test thấy nó trượt khi luật bị bỏ. Toàn bộ test qua.
