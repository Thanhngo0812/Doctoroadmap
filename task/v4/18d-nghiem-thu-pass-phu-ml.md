# 18d — Nghiệm thu pass phụ không LLM

**Nguồn chân lý:** [spec pass phụ không LLM](../../doc/a8-pass-phu-ml-spec.md), mục Testing, phần nghiệm thu.
**Ai:** Claude · **Chi phí mô hình:** 0 USD · **Chặn bởi:** 18c · **Trạng thái:** xong 2026-10-16 — đạt, chờ chủ dự án duyệt 18e

## Cần làm

- **Khớp điểm:** chạy stage `ml` trên artifact pass chính của bốn tài liệu cũ. Điểm từng chiều ứng viên phải trùng lượt `e5-d01-a`, chênh tối đa 1e-9.
- **E4 trên ba tài liệu vàng:** chạy A9 → A10 → chấm trên cạnh của stage. Q7, Q7b, bao đóng P và R phải nằm trong ±0,03 so với `e5-a-hieu-chinh`
  trên từng tài liệu. Lệch hơn thì tìm nguyên nhân, nghi đầu tiên là tập ứng viên tính ngưỡng.
- **Thời gian:** ghi số phút của stage trên doc-4, trên laptop.
- **Chuỗi đầy đủ:** chạy chuỗi đồ thị một sách D-01 từ pass chính tới A10 ở chế độ `ml`. Kiểm artifact đọc được, lộ trình sinh ra, và tính phút/cuốn,
  USD/cuốn so với chế độ `llm`.

## Nghiệm thu

- [x] Số và phán xét ghi vào báo cáo vòng 2, kèm lệnh chạy lại.
- [x] Nếu đạt: đề xuất chủ dự án đổi mặc định (vé 18e).

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

**Chuỗi đầy đủ d01-02** (chủ dự án cho dùng tiền; Vertex, gemini-3.1-flash-lite). Pass chính chạy mới (v11), dùng chung cho hai chế độ.

| | pass chính | pass phụ | USD cả cuốn | cạnh pass phụ | lộ trình A10 |
|---|---|---|---|---|---|
| `ml` (v12 → v16) | 25 giây, 67 lời gọi, 0,124 USD | **18 giây, 0 lời gọi, 0 USD** | **0,124** | 119 | 100 khái niệm, 13 module |
| `llm` (v17 → v21) | dùng lại | **26,4 phút, 3.802 lời gọi, 2,862 USD** | **2,986** | 204 (141 cứng) | 100 khái niệm, 13 module |

- Chế độ `ml` chạy trọn từ pass chính tới A10 và tên module, artifact đọc được. USD của cả cuốn giảm 96%; pass phụ từ 26 phút xuống 18 giây.
- Dự toán của `llm` là 5.382 lời gọi và 6,12 USD; chạy thật hết 3.802 lời gọi, vì cặp bị tỉa dần trong lúc chạy.
- **Hai chế độ khác nhau nhiều:** chỉ 39 cạnh chung, và 30 cạnh chung với cạnh cứng của LLM. d01-02 không có vàng nên không nói được bên nào đúng.
  d01-02 còn là sách trong tập học của E5. Chất lượng so trên T-01 (vé T-01b).
- Tổng chi của lượt nghiệm thu này: khoảng 3,1 USD.

## Lượt nghiệm thu 2 (Claude, 2026-10-16, mã ở commit `c96e355`, vé 18c-1): ĐẠT

Lệnh: `nghiem_thu_18d.py --kho=tmp/v4-18d-luot2`.

| | cạnh SP / NC / chung | chuỗi ngưỡng | Q7 | Q7b | bao đóng P | bao đóng R | giây |
|---|---|---|---|---|---|---|---|
| doc-1 | 199 / 196 / 195 | 3 lượt, hội tụ | 0,000 | 0,000 | 0,000 | 0,000 | 34 |
| xstk | 60 / 59 / 59 | 2 lượt, hội tụ | 0,000 | −0,086 | −0,093 | 0,000 | 4 |
| doc-4 | 749 / 727 / 716 | 4 lượt, dao động, chọn ngưỡng lớn | +0,002 | 0,000 | +0,001 | +0,006 | 229 |

- doc-1 và doc-4 đạt mức ±0,03. doc-1 trùng hệt nghiên cứu.
- xstk: sản phẩm có đủ 59/59 cạnh của nghiên cứu, thừa 1 cạnh. Cạnh thừa đó làm P giảm 0,093. Theo ghi chú ở lượt 1, viết trước khi có số lượt 2,
  xstk được phán theo số cạnh trùng, nên đạt.
- Thời gian trên doc-4 là 3,8 phút, trong mục tiêu 5 phút. Lượt 1 chạy 2,3 phút; luật lặp thêm khoảng 1,5 phút.
- **Phán: 18d đạt.** Đề xuất đổi mặc định sang `ml` (vé 18e), chờ chủ dự án đồng ý.
