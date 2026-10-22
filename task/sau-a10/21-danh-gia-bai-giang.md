# SA-21 — Đánh giá bài giảng

**Nguồn chân lý:** [báo cáo bài giảng](../../report/nghien-cuu-bai-giang-theo-khai-niem-2026-10-11.md), mục 6; [spec Pha B](../../doc/pha-b-spec.md),
"Ghi chú thêm".
**Ai:** agent Sonnet chạy và xuất bảng · hai thành viên nhóm chấm · Claude phân tích · **Chi phí mô hình:** trần 5 USD, dry-run trước, chủ dự án
duyệt · **Chặn bởi:** 04, 12, 26, 30, 53 (đều đã đạt) · **Trạng thái:** sẵn sàng

**Dữ liệu (cập nhật 2026-10-22):** graph ghim và kho Pha B theo [bảng kế hoạch, đợt đánh giá 20–23](00-ke-hoach.md). Bài giảng là `lecture-2`, validator `lecture-validator-7`.

## Vì sao

Cần trả lời bốn câu hỏi bằng số và bằng người chấm:
- Bài giảng LLM có đúng, trung thực, và có ích hơn bản trích câu không?
- Đồ thị có đóng góp không?
- Nhiệt độ 0 có làm bài lặp không?
- Nội dung ngoài sách có gây sai không?

## Cần làm

**Mẫu:** khoảng 50 khái niệm, phân tầng theo sáu cuốn, cố ý gồm khái niệm có công thức (doc-1, xstk) và khái niệm triết học (doc-4).

**Năm cấu hình trên cùng mẫu:**
- LLM, nhiệt độ 0 (vé 12);
- LLM, nhiệt độ mặc định;
- mốc trích câu (vé 11);
- **ablation không đồ thị:** chỉ chunk dạy, bỏ tiên quyết, cạnh mở, bài tập;
- **tuỳ chọn, còn trần chi mới chạy:** gửi ảnh công thức cho mô hình trên các khái niệm có công thức trong câu định nghĩa.

**Bảng chấm mù theo cặp:**
- Rubric: đúng, trung thực, giá trị sư phạm, đọc được, độ dài.
- **Thêm 2026-10-18, theo spec Pha B2:** chấm trên bản `lecture-2`, với hai tiêu chí:
  - **câu nối:** đúng quan hệ, đúng nguồn, không bịa;
  - **phần gợi lại tiên quyết và khối "Tiếp theo":** có ích cho người học.

  "Mốc trích câu" chỉ còn là cấu hình so sánh, không phải thứ người học thấy (ADR 0018).
- Bảng hiện ảnh công thức gốc (vé 04) và câu trích nguồn.

**Đo tự động:**
- tỉ lệ bỏ ý theo luật;
- tỉ lệ lặp câu (K6);
- tỉ lệ nội dung ngoài sách;
- chỉnh ngưỡng K4 từ dữ liệu;
- kiểm "ý có được đoạn đỡ" trên một mẫu, bằng NLI hay LLM giám khảo, đảo thứ tự để giảm thiên lệch;
- USD và giây chờ ở p50 và p90;
- **thay lượt thật của SA-13:** giây tới `skeleton`, tới ý đầu và tới `final`, ở p50 và p90, đo trên cấu hình LLM nhiệt độ 0. Lượt này phải đo ở chế độ
  stream, kho rỗng, không có cache.

**Luật quyết định**, viết trước khi đo:
- tỉ lệ lặp quá 2%, hoặc nhánh nhiệt độ mặc định thắng chấm mù, thì đề xuất đổi nhiệt độ;
- ví dụ ngoài sách sai hoặc gây hiểu lầm quá 5% thì đề xuất tắt.

Hai luật này là đề xuất cho chủ dự án, không phải cổng tự động.

**Cách chấm (chốt 2026-10-22):** mỗi khái niệm là một nhóm 4–5 bản (LLM nhiệt độ 0, LLM nhiệt độ mặc định, mốc trích câu, ablation không đồ thị,
và bản ảnh công thức nếu chạy). Người chấm chấm tuyệt đối từng bản, rồi xếp hạng trong nhóm; kết quả từng cặp suy từ thứ hạng. Trung thực theo ý
(phần 2) chỉ chấm trên bản thiết kế chính, ở tệp riêng giao sau khi nộp phần 1. Mẫu 50 khái niệm theo vé.

## Tiêu chí nghiệm thu

- [ ] **Phiếu chấm theo hướng dẫn** [`doc/huong-dan-cham/21-bai-giang.md`](../../doc/huong-dan-cham/21-bai-giang.md) và [luật chung](../../doc/huong-dan-cham/00-chung.md):
  - mỗi người chấm (`C1`, `C2`) có tệp Excel riêng, đúng các cột và giá trị trong hướng dẫn, có danh sách chọn;
  - tệp HTML đọc được khi không có mạng, ảnh công thức nhúng sẵn;
  - thứ tự mục và nhãn A/B/C/D trộn riêng cho từng người, hạt giống cố định ghi trong báo cáo;
  - một bộ chấm thử nằm ngoài mẫu;
  - tệp khoá cấu hình để riêng, không nằm trong thư mục giao người chấm;
  - kiểm bằng script rằng tệp giao người chấm không chứa tên cấu hình, mã nhánh hay đường dẫn kho.

- [ ] Dry-run và chạy thật trong trần. Báo USD.
- [ ] Bảng chấm mù và tệp khoá cấu hình để riêng.
- [ ] Hai người chấm xong. Claude tính độ đồng thuận (κ, AC1), áp luật, và viết báo cáo kết quả gồm cả ca xấu.
