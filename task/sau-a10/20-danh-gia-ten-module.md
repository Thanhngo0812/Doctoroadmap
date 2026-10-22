# SA-20 — Đánh giá tên module

**Nguồn chân lý:** [ADR 0014](../../doc/adr/0014-ten-module-do-llm-dat.md); [báo cáo tên module](../../report/nghien-cuu-ten-va-mo-ta-module-2026-10-11.md),
mục 7, gồm mục 7.6 đã sửa ngày 2026-10-11.
**Ai:** agent Sonnet chạy và xuất bảng · hai thành viên nhóm chấm độc lập · Claude phân tích · **Chi phí mô hình:** dưới 1 USD (biến thể LLM thứ
hai), dry-run trước · **Chặn bởi:** 06 (đạt qua SA-29) · **Trạng thái:** sẵn sàng

**Dữ liệu (cập nhật 2026-10-22):** graph ghim, kho Pha B và luật đọc tên đã có theo [bảng kế hoạch, đợt đánh giá 20–23](00-ke-hoach.md).

## Vì sao

Tên module là thứ người học thấy đầu tiên. Luật quyết định đã viết trước khi đo:
- không tự bỏ LLM;
- chỉ chọn biến thể LLM tốt nhất;
- LLM thua bản tất định thì báo đánh đổi bằng số, chủ dự án quyết.

## Cần làm

**Hai biến thể LLM trên 162 module của sáu cuốn** (graph ghim; ngày 2026-10-11 là 142 module trên graph cũ):
- L1: có đối chứng module ±1, là bản hiện hành sau SA-29;
- L2: không có đối chứng.

**Mốc so sánh:** tên A10 của Pha A có trong graph ghim, và đường lùi tất định của vé 05 (khuôn lùi sau SA-29).

**Độ đo tự động:**

| độ đo | cách đo |
|---|---|
| tiêu đề tác giả bị giấu | Với các module loại E (trùng đúng một mục), đếm lại trên graph ghim theo định nghĩa ở mục 2.1 của báo cáo tên (ngày 2026-10-11 là 51/142), giấu tiêu đề tác giả rồi so tên sinh ra với nó. Đây là tham chiếu bạc |
| độ giống giữa tên kề | Đo giữa các module kề nhau |
| từ có căn cứ | Tỉ lệ tên có mọi từ có căn cứ trong module |
| mượn từ | Tỉ lệ tên mượn từ module kề |
| đường lùi | Tỉ lệ module phải đi đường lùi |
| khớp tên với module | Cho tên, chọn đúng module trong các module kề. Theo tinh thần phép thử "intrusion" |

**Bảng chấm mù theo cặp:**
- Ba cặp so: L1 với v9, L1 với L2, và L1 với bản tất định.
- Thứ tự trộn ngẫu nhiên; bảng không lộ cấu hình.
- Rubric: đúng nội dung, phân biệt với module kề, ngắn gọn, tự nhiên.

**Phân tích:** độ đồng thuận bằng κ của Cohen và Gwet AC1, kiểm định dấu, rồi áp luật quyết định 7.6.

## Tiêu chí nghiệm thu

- [ ] Dry-run rồi chạy L2, sau khi chủ dự án duyệt. Báo USD.
- [ ] Bảng số tự động cho cả bốn bản tên.
- [ ] Bảng chấm mù xuất ra. Một tệp khoá cấu hình để riêng, người chấm không thấy.
- [ ] Hai người chấm xong. Claude tính độ đồng thuận, áp luật quyết định, và viết báo cáo kết quả gồm cả các ca thắng và thua.
