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

## Lượt nghiệm thu 1 (Claude, 2026-10-16, mã ở commit `8053ace`)

Lệnh: `scripts/pass-phu-ml/nghiem_thu_18d.py`. Mốc so là `e5-a-hieu-chinh` trong `sua-y.jsonl`, tức số sau khi sửa bộ khớp. Bản đầu của script lấy
nhầm `e5.jsonl`, là số trước khi sửa; đã chữa.

**Đạt:**
- Điểm từng chiều ứng viên trùng `e5-d01-a`: chênh 0 trên 4.905 chiều của ba tài liệu.
- Bộ lắp cạnh tương đương bộ lắp nghiên cứu: cùng ngưỡng thì ra cùng tập cạnh (doc-1 187/187, xstk 58/58).
- Stage trên doc-4 chạy 138 giây, 0 lời gọi.

**Chưa đạt, do luật ngưỡng của spec bản đầu:** ngưỡng tính trên mọi cặp chưa bị cạnh pass chính tỉa.

| | cạnh SP / NC / chung | Q7 | Q7b | bao đóng P | bao đóng R |
|---|---|---|---|---|---|
| doc-1 | 187 / 196 / 180 | −0,042 | −0,004 | −0,001 | −0,038 |
| xstk | 58 / 59 / 58 | 0,000 | +0,067 | +0,103 | 0,000 |
| doc-4 | 715 / 727 / 710 | +0,007 | 0,000 | 0,000 | 0,000 |

(SP: sản phẩm; NC: nghiên cứu.)

**Luật điểm bất động** (Claude mô phỏng bằng bộ lắp nghiên cứu; vé 18c-1):
- doc-1: hội tụ sau 2 lượt, 199 cạnh, E4 trùng hệt nghiên cứu.
- doc-4: dao động giữa hai ngưỡng; chọn ngưỡng lớn hơn thì được 749 cạnh, E4 lệch tối đa 0,006.
- xstk: 60 cạnh, bao đóng P 0,50 so với 0,593 của nghiên cứu.
  - Ở xstk, ±1 cạnh làm P đổi khoảng 0,1. Độ lệch chuẩn của P qua 6 seed E5 là 0,079.
  - Vì vậy mức ±0,03 không đo được trên vàng xstk. Phán xét xstk theo số cạnh trùng. Đây là ghi chú, không phải nới tiêu chí: doc-1 và doc-4 vẫn
    giữ mức ±0,03.
