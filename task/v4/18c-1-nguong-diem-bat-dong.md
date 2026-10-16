# 18c-1 — Pass phụ `ml`: ngưỡng tính trên các cặp được phán, lặp tới điểm bất động

**Nguồn chân lý:** [spec pass phụ không LLM](../../doc/a8-pass-phu-ml-spec.md), mục 4 "Ngưỡng theo từng tài liệu" (đã sửa 2026-10-16).
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD · **Chặn bởi:** 18c · **Trạng thái:** implemented — kiểm thử xanh, chờ Claude nghiệm thu lại 18d

## Vì sao

18c cài đúng spec bản đầu. Nghiệm thu 18d cho thấy **luật ngưỡng của spec** chưa đúng, còn mã thì đúng:
- điểm từng chiều trùng nghiên cứu, chênh 0;
- với cùng một ngưỡng, bộ lắp của sản phẩm ra đúng tập cạnh của bộ lắp nghiên cứu.

Spec bản đầu tính ngưỡng một lần, trên mọi cặp chưa bị cạnh pass chính tỉa. Tập này lớn hơn tập nghiên cứu dùng, nên ngưỡng cao hơn: doc-1 mất 9
cạnh, Q7 giảm 0,042 và R giảm 0,038, trượt mức ±0,03. Claude đã mô phỏng luật điểm bất động bằng bộ lắp nghiên cứu: doc-1 cho E4 trùng hệt nghiên
cứu, doc-4 lệch tối đa 0,006.

## Cần làm

- Thay luật ngưỡng:
  1. t₀ = luật hiện tại, tức tính trên chiều ứng viên của các cặp chưa bị cạnh pass chính tỉa.
  2. Lắp cạnh với t (đúng vòng lặp hiện có, tỉa trước từng cặp). Ghi lại các cặp **không bị tỉa** trong lượt đó.
  3. k = round(tổng xác suất hiệu chỉnh trên chiều ứng viên của các cặp ấy). t' là điểm thứ k giảm dần; k = 0 thì không tạo cạnh và dừng.
  4. t' = t thì dừng. t' đã gặp trước đó thì chọn ngưỡng lớn nhất trong vòng dao động. Tối đa 10 lượt; hết lượt thì chọn ngưỡng lớn nhất đã gặp.
  5. Artifact là kết quả của lượt lắp với ngưỡng được chọn. Lắp lại bằng ngưỡng đó nếu lượt cuối dùng ngưỡng khác.
- Đổi tên luật ngưỡng trong config (khoá cache đổi theo). `stats` ghi chuỗi ngưỡng đã thử, số lượt, có dao động hay không, k và ngưỡng cuối.
- Lượt lắp thử không được ghi nhật ký vào artifact, trừ lượt cuối.

## Nghiệm thu

- [x] Test qua `execute`, bộ chấm giả:
  - ca hội tụ: ngưỡng cuối bằng điểm bất động, khác t₀;
  - ca dao động hai giá trị: chọn ngưỡng lớn hơn;
  - ca k = 0;
  - ca chạm giới hạn 10 lượt.
  Mỗi ca phải thấy trượt khi bỏ luật tương ứng.
- [x] Test cũ của 18c vẫn qua, trừ test chốt luật ngưỡng cũ: sửa test đó theo luật mới.
- [ ] Claude chạy lại 18d.

## Bàn giao triển khai — 2026-10-16

- Đổi `threshold_rule` thành `round-sum-isotonic-on-judged-directions-fixed-point-10-v1`, nên không dùng nhầm cache 18c cũ.
- Chấm điểm/hiệu chỉnh một lần; mỗi lượt lắp từ main, chỉ tính lại ngưỡng từ chiều ứng viên của các cặp không bị tỉa ở lượt đó.
- Nhật ký và cạnh thử không đi vào artifact. Nếu ngưỡng được chọn khác lượt cuối, lắp lại bằng ngưỡng ấy; k=0 xoá cạnh thử và dừng.
- Stats có lịch sử ngưỡng, số lượt, dao động, lý do dừng, cờ lắp lại cuối, k và ngưỡng đã chọn.
- 4 ca bắt buộc đã thấy đỏ trên mã cũ trước sửa; bộ stage hiện **21 passed**. Bộ đột biến **28/28 detected**, gồm 8 đột biến mới cho vé này.
- Hồi quy toàn worktree: **1.384 passed**; snapshot riêng phần commit (không lấy mã Pha B đang dở): **1.202 passed**.
- Chạy stage thật trong kho thử riêng: doc-1 **199 cạnh**, xstk **60**, doc-4 **749**. 0 lời gọi API, 0 USD; lần chạy kế tiếp tái dùng cache.
- Doc-4 đo riêng: **244,58 giây (4,08 phút)**; hai lượt độc lập ra cùng config_hash và SHA-256 payload. Lượt đo cùng kiểm thử: 463,48 giây, ghi
  riêng trong báo cáo, không dùng làm phép đo tốc độ không tải nền.
- Chi tiết, lệnh tái lập và số đo: [báo cáo 18c-1](../../report/v4-18c1-nguong-diem-bat-dong-2026-10-16.md).
- Không đổi mặc định `llm`, không học lại E5/đổi đặc trưng hoặc mở T-01/D-01. Chưa tự đánh dấu nghiệm thu chất lượng 18d.
