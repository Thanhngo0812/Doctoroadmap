# SA-21 — Đánh giá bài giảng

**Nguồn chân lý:** [báo cáo bài giảng](../../report/nghien-cuu-bai-giang-theo-khai-niem-2026-10-11.md), mục 6; [spec Pha B](../../doc/pha-b-spec.md),
"Ghi chú thêm".
**Ai:** nhân viên chạy và xuất bảng · hai thành viên nhóm chấm · Claude phân tích · **Chi phí mô hình:** trần 5 USD, dry-run trước, chủ dự án
duyệt · **Chặn bởi:** 04, 12 · **Trạng thái:** ready-for-agent

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
- USD và giây chờ ở p50 và p90.

**Luật quyết định**, viết trước khi đo:
- tỉ lệ lặp quá 2%, hoặc nhánh nhiệt độ mặc định thắng chấm mù, thì đề xuất đổi nhiệt độ;
- ví dụ ngoài sách sai hoặc gây hiểu lầm quá 5% thì đề xuất tắt.

Hai luật này là đề xuất cho chủ dự án, không phải cổng tự động.

## Tiêu chí nghiệm thu

- [ ] Dry-run và chạy thật trong trần. Báo USD.
- [ ] Bảng chấm mù và tệp khoá cấu hình để riêng.
- [ ] Hai người chấm xong. Claude tính độ đồng thuận (κ, AC1), áp luật, và viết báo cáo kết quả gồm cả ca xấu.
