# 18d — Nghiệm thu pass phụ không LLM

**Nguồn chân lý:** [spec pass phụ không LLM](../../doc/a8-pass-phu-ml-spec.md), mục Testing, phần nghiệm thu.
**Ai:** Claude · **Chi phí mô hình:** 0 USD · **Chặn bởi:** 18c · **Trạng thái:** ready-for-agent

## Cần làm

- **Khớp điểm:** chạy stage `ml` trên artifact pass chính của bốn tài liệu cũ. Điểm từng chiều ứng viên phải trùng lượt `e5-d01-a`, chênh tối đa 1e-9.
- **E4 trên ba tài liệu vàng:** chạy A9 → A10 → chấm trên cạnh của stage. Q7, Q7b, bao đóng P và R phải nằm trong ±0,03 so với `e5-a-hieu-chinh`
  trên từng tài liệu. Lệch hơn thì tìm nguyên nhân, nghi đầu tiên là tập ứng viên tính ngưỡng.
- **Thời gian:** ghi số phút của stage trên doc-4, trên laptop.
- **Chuỗi đầy đủ:** chạy chuỗi đồ thị một sách D-01 từ pass chính tới A10 ở chế độ `ml`. Kiểm artifact đọc được, lộ trình sinh ra, và tính phút/cuốn,
  USD/cuốn so với chế độ `llm`.

## Nghiệm thu

- [ ] Số và phán xét ghi vào báo cáo vòng 2, kèm lệnh chạy lại.
- [ ] Nếu đạt: đề xuất chủ dự án đổi mặc định (vé 18e).
