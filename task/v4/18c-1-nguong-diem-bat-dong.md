# 18c-1 — Pass phụ `ml`: ngưỡng tính trên các cặp được phán, lặp tới điểm bất động

**Nguồn chân lý:** [spec pass phụ không LLM](../../doc/a8-pass-phu-ml-spec.md), mục 4 "Ngưỡng theo từng tài liệu" (đã sửa 2026-10-16).
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD · **Chặn bởi:** 18c · **Trạng thái:** ready-for-agent

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

- [ ] Test qua `execute`, bộ chấm giả:
  - ca hội tụ: ngưỡng cuối bằng điểm bất động, khác t₀;
  - ca dao động hai giá trị: chọn ngưỡng lớn hơn;
  - ca k = 0;
  - ca chạm giới hạn 10 lượt.
  Mỗi ca phải thấy trượt khi bỏ luật tương ứng.
- [ ] Test cũ của 18c vẫn qua, trừ test chốt luật ngưỡng cũ: sửa test đó theo luật mới.
- [ ] Claude chạy lại 18d.
