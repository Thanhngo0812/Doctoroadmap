# SA-23 — Đánh giá trợ lý: 4 cấu hình, RAGAS

**Nguồn chân lý:** [ADR 0012](../../doc/adr/0012-tro-ly-la-agent-goi-cong-cu.md); [báo cáo trợ lý](../../report/nghien-cuu-tro-ly-hoi-dap-do-thi-2026-10-11.md),
mục 2.8, 5; đề cương đồ án, mục 5.3.
**Ai:** nhân viên chạy · nhóm duyệt bộ câu hỏi và chấm · Claude phân tích · **Chi phí mô hình:** lượt 1 trần khoảng 8 USD, dự toán lại bằng
dry-run vì kiến trúc agent tốn hơn bản báo cáo ước; lượt 2 xin duyệt riêng · **Chặn bởi:** 07, 10, 19 · **Trạng thái:** ready-for-agent

## Vì sao

Đề cương yêu cầu ba thứ:
- đánh giá trợ lý bằng RAGAS (tính trung thực, mức liên quan);
- mốc so sánh "hỏi LLM trực tiếp không kèm bằng chứng";
- ablation để biết từng thành phần đóng góp gì.

Phép so "agent có công cụ đồ thị" với "agent không có" là bằng chứng chính cho giá trị của đồ thị.

## Cần làm

**Bộ câu hỏi thử:** do agentic sinh theo đặc tả của vé 19, rồi người duyệt một mẫu.

**Bốn cấu hình trên cùng bộ câu:**
- LLM không bằng chứng;
- RAG thuần: truy hồi lai, một lời gọi;
- agent không có công cụ đồ thị;
- agent đầy đủ.

Mỗi câu ghi lại câu trả lời, các lời gọi công cụ, USD và giây chờ.

**RAGAS:**
- Cài trong một môi trường riêng, ghim phiên bản; không cài vào môi trường của dự án.
- **Cấu hình LLM và embedding sang Gemini.** Kiểm bằng cách chặn mạng tới OpenAI khi chấm.
- Đo bốn độ đo: faithfulness, response relevancy, context precision, context recall.
- **Câu từ chối chấm riêng**, vì RAGAS cho câu từ chối relevancy bằng 0.

**Chấm người:** khoảng 60 câu trả lời, chấm mù theo cặp giữa agent đầy đủ và RAG thuần, cộng một rubric tuyệt đối.

**Đo thêm:**
- độ chính xác liên kết khái niệm, theo tên và theo mô tả (vé 07);
- tỉ lệ gọi công cụ sai;
- tỉ lệ từ chối đúng ở câu ngoài tài liệu;
- **nhánh tuỳ chọn:** BM25 thêm cặp âm tiết liền kề, và vector A6 thay chỉ mục khái niệm.

**Luật quyết định viết trước khi đo,** gồm luật nhận biết RAGAS tự đề cao: đối chiếu với điểm người chấm.

## Tiêu chí nghiệm thu

- [ ] Dry-run dự toán lại lượt 1 và chủ dự án duyệt. Chạy trong trần.
- [ ] Bảng số theo cấu hình: bốn độ đo RAGAS, từ chối đúng, USD và giây chờ ở p50 và p90.
- [ ] Bảng chấm mù và tệp khoá để riêng. Hai người chấm xong. Claude tính độ đồng thuận và viết báo cáo kết quả gồm cả ca xấu.
- [ ] Không có lưu lượng nào tới OpenAI trong lúc chấm. Ghi rõ cách kiểm.
