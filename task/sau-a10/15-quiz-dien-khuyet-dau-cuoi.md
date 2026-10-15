# SA-15 — Quiz điền khuyết đầu-cuối

**Nguồn chân lý:** [spec Pha B](../../doc/pha-b-spec.md), mục 9 (dạng câu, phản hồi, lịch sử, báo câu lỗi) và 13 (hợp đồng `quiz-1`), bất biến 7;
[báo cáo quiz](../../report/nghien-cuu-quiz-tu-kiem-tra-2026-10-11.md), mục 1.4, 3.7, 3.9, 4.
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** 01, 02 · **Trạng thái:** ready-for-agent

## Vì sao

Làm trọn đường quiz ở mức 0 USD trước, gồm sinh, làm, nộp, phản hồi và lịch sử. Có ba cái lợi:
- hợp đồng `quiz-1` và luồng lưu trữ được kiểm sớm;
- vé 16 chỉ còn thay nguồn câu hỏi;
- câu điền khuyết là bản lùi, đồng thời là mốc không LLM để so.

## Cần làm

**Ngân hàng câu điền khuyết theo khái niệm:**
- **Khái niệm đủ điều kiện:** câu neo có chứa tên khái niệm. Mọi lần xuất hiện của tên, `display_name` và alias được thay bằng "___".
- **Câu hỏi:** "Câu sau trích từ tài liệu nói về khái niệm nào?"
- **Phương án:** 3 phương án, gồm đáp án và 2 câu nhiễu. Câu nhiễu lấy theo thứ tự cạnh mở → cùng module → cùng cụm ở module đã học, ưu tiên cùng
  `node_type`.
- **Luật kiểm:** Q1, Q3 (câu nhiễu không là tên, alias hay danh tính đã gộp của đáp án), Q5–Q8.

**Hợp đồng `quiz-1`:**
- **Đề của một lần làm:** không có `is_correct`, `why_wrong` hay lời giải thích. Thứ tự phương án do mã xáo.
- **Bài nộp, và kết quả kèm phản hồi:** đáp án đúng, câu trích làm nguồn, vì sao phương án đã chọn sai, danh sách khái niệm làm sai kèm tham chiếu bài
  giảng. Chỉ ghi "đúng m/n câu", không khen chê.
- **Báo câu lỗi:** câu bị báo nhiều lần (số lần nằm trong cấu hình) thì ẩn khỏi ngân hàng.

**Lịch sử theo người học**, lưu trong kho Pha B: điểm theo khái niệm, câu đã chọn, thời điểm, `origin = module_button`.

**Lệnh CLI** tạo lần làm cho một module, nộp bằng tệp câu trả lời, rồi in kết quả.

## Tiêu chí nghiệm thu

- [ ] Sáu cuốn: tỉ lệ khái niệm đủ điều kiện (báo cáo nghiên cứu ước 46–100%), và tỉ lệ đáp án dài nhất. Số là thông tin.
- [ ] Test, mỗi cái thấy đỏ trước:
  - JSON đề không chứa đáp án hay lời giải thích;
  - câu nhiễu không bao giờ là alias hay danh tính đã gộp của đáp án;
  - đếm đúng câu;
  - lịch sử được lưu;
  - câu bị báo đủ số lần thì bị ẩn.
- [ ] Đính kèm một ví dụ JSON thật của bốn đối tượng hợp đồng cho nhóm web.
- [ ] 0 USD.

## Ngoài vé

Câu hỏi do LLM sinh (vé 16).
