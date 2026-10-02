# 22 — Gọi mô hình song song cấu hình được (≥ 100 lời gọi đồng thời), kết quả y hệt cách chạy tuần tự

**Nguồn chân lý:** vé này (hạ tầng, không đổi phương pháp) · [báo cáo nghiên cứu](../../report/nghien-cuu-song-song-cao-2026-10-02.md) ·
**Ai:** nhân viên · **Phụ thuộc:** — · **Chi phí mô hình:** 0 để làm và kiểm; chạy tiếp doc-2 như dự toán cũ (≈ 6–9 USD)

**Trạng thái:** chờ giao — **làm trước khi chạy tiếp doc-2 và trước T10**. Chủ dự án yêu cầu 2026-10-02: tăng song song lên 100 hoặc hơn tuỳ cấu
hình, để sau này phục vụ người dùng.

## Vì sao
- Pass phụ chạy **từng cặp một** (2 lời gọi song song cho hai thứ tự hỏi), khoảng 46 lời gọi/phút. Pass phụ đầy đủ sáu tài liệu (24,7 nghìn
  lời gọi) mất hơn 9 giờ.
- **Điểm lưu ghi lại toàn bộ sau mỗi cặp.** Tệp doc-2 đã 55 MB ở 37% tiến độ, mỗi lần ghi khoảng 1 giây và tăng tuyến tính. Đây là một nút
  thắt ngang thời gian gọi mô hình. Sổ chi của script đánh giá (`MeteredGemini`) cũng ghi lại toàn bộ (3,6 MB) sau mỗi lời gọi.
- Không có bộ giới hạn chung:
  - mỗi luồng tự thử lại khi gặp 429;
  - `vertex_concurrency` đặt cứng 2;
  - embedding qua Vertex gọi tuần tự từng câu.
- **Mô phỏng 0 USD trên nhật ký thật** (`scripts/doc-lo-trinh/thu_song_song_pass_phu.py`) cho cách "hỏi trước, chốt theo thứ tự":
  - dựng lại khớp nhật ký 100%;
  - lô 50 cặp (100 lời gọi song song) chỉ thừa 0,4–2,1% lời gọi và nhanh khoảng 48 lần;
  - lô 100 cặp thừa ≤ 2,5%, nhanh khoảng 80–97 lần.
- **Giới hạn thật của Vertex** (Standard PayGo, xem báo cáo): theo bậc chi 30 ngày. Bậc 1 (10–250 USD) có thông lượng nền khoảng 2 triệu
  token/phút cho Flash/Flash-Lite, tính cho cả tổ chức.
  - Mỗi lời gọi pass phụ trung bình 2.864 token, nên khoảng 700 lời gọi/phút là mức bền vững, cỡ 30–40 lời gọi đồng thời.
  - Đặt 100 vẫn được, nhưng phải có bộ giới hạn theo token/phút và tự hạ khi gặp 429. Nếu không, phần vượt chỉ biến thành 429.

## Việc cần làm
1. **Bộ giới hạn chung cho mọi lời gọi mô hình**, dùng chung giữa sinh văn bản (`GeminiEntityExtractor`) và embedding (`GeminiEmbedding`)
   trong cùng tiến trình. **Không phụ thuộc đường gọi:** chủ dự án dùng Vertex trong lúc còn credit, sau đó quay lại Gemini Developer API.
   - `llm_max_in_flight`: trần số lời gọi đồng thời, ví dụ 100.
   - `llm_tpm_budget`: ngân sách token/phút. Ước token trước khi gửi theo số byte/3 như dự toán hiện có, rồi chỉnh theo `usageMetadata`.
   - `llm_rpm_budget`: ngân sách lời gọi/phút (bỏ trống = không giới hạn). Developer API giới hạn theo dự án trên ba chiều RPM, TPM, RPD.
   - Mọi giá trị đặt trong `.env`, không viết cứng theo đường gọi. `.env.example` ghi gợi ý:
     - Vertex bậc 1: TPM 1.600.000 (80% thông lượng nền), RPM bỏ trống;
     - Developer API: lấy RPM/TPM từ trang giới hạn của dự án trong AI Studio, đặt 80%.
   - **Tự điều chỉnh:** gặp 429/503 thì hạ mức đồng thời hiện hành còn một nửa (tối thiểu 2) và tạm dừng có jitter; sau N lời gọi thành
     công liên tiếp thì tăng 1, không quá trần. Có `Retry-After` thì tôn trọng.
   - Các thông số này **không vào khoá cache hay config hash** (như `llm_transport`, vé 19), vì không đổi kết quả. Ghi vào manifest để kiểm
     toán.
2. **Pass phụ "hỏi trước, chốt theo thứ tự"**, kích thước lô `secondary_window_pairs` (mặc định `llm_max_in_flight // 2`):
   1. Lấy B cặp kế tiếp còn phải hỏi theo ảnh chụp cạnh hiện tại. Dựng hồ sơ, hỏi cả B cặp (2B lời gọi) qua bộ giới hạn.
   2. Chốt theo **đúng thứ tự cũ**. Trước khi chốt mỗi cặp, chạy lại `select_secondary_pairs` và `pair_dossier` với cạnh đã chốt:
      - bị cắt → bỏ kết quả;
      - hồ sơ khác hồ sơ đã hỏi → dừng chốt, lô sau bắt đầu từ cặp này với ảnh chụp mới;
      - còn lại → chốt như cũ.
   3. Câu trả lời đã có cho cùng đầu vào lấy từ cache theo hash, không gọi lại.
   4. Lưu điểm lưu **sau mỗi lô**, không sau mỗi cặp.
   - Đầu ra phải **giống hệt** cách chạy tuần tự: cùng `secondary_edges`, cùng trạng thái từng cặp.
   - Bỏ `min(self.concurrency, 2)`.
3. **Embedding qua Vertex:** gọi song song từng câu qua bộ giới hạn, giữ thứ tự kết quả. Đồng thời xoá nhánh chết và bắt lỗi phản hồi hỏng
   như ghi chú vé 19.
4. **Ghi file không tăng theo bình phương:**
   - điểm lưu pass phụ ghi theo lô, nhật ký dạng nối thêm (JSONL) hoặc JSON gọn không `indent`. **Phải đọc được điểm lưu dạng cũ** để doc-2
     (đang dừng ở 3.517 cặp) chạy tiếp mà không hỏi lại;
   - sổ chi của các script đánh giá ghi nối thêm (JSONL), không ghi lại cả tệp sau mỗi lời gọi.
5. Pass chính giữ nguyên thuật toán (song song theo chương, vì đầu vào mỗi phiên chứa cạnh của phiên trước cùng chương), chỉ đi qua bộ
   giới hạn. Ghi rõ giới hạn này.
6. Tuỳ chọn, nên làm: tái dùng kết nối HTTP (keep-alive) thay vì mở kết nối mới cho mỗi lời gọi.
- Không đổi prompt, schema, luật kiểm, thứ tự cặp hay bất cứ thứ gì vào khoá cache.

## Nghiệm thu
- **Test không mạng (mô hình và đồng hồ giả):**
  - pass phụ với lô 1, 4, 50 trên fixture có cặp bị cắt giữa lô và cặp đổi hồ sơ giữa lô: `secondary_edges` và trạng thái giống hệt; cặp bị
    cắt không được chốt; cặp đổi hồ sơ được hỏi lại đúng hồ sơ mới;
  - bộ giới hạn: không bao giờ vượt `llm_max_in_flight` lời gọi đang chạy; không vượt ngân sách token/phút; gặp loạt 429 thì giảm rồi hồi
    phục;
  - các thông số mới không đổi config hash (dry-run sáu tài liệu không chuyển stage nào sang "sẽ chạy");
  - chạy tiếp được từ điểm lưu dạng cũ.
  - Mỗi test phải đỏ trên mã hiện tại hoặc khi tắt cơ chế nó canh.
- **Test phát lại 0 USD trên dữ liệu thật:**
  - chạy pass phụ chế độ lô (B = 50) cho doc-3 và nhap-mon-ml trên kho đánh giá, dùng nhật ký đã có làm cache;
  - lời gọi trượt cache trả lời bằng mô hình giả. Kết quả của chúng **không được** xuất hiện trong cạnh cuối (assert);
  - `secondary_edges` phải trùng hệt artifact v2 hiện có. Báo số lời gọi trượt cache, phải gần mức mô phỏng (≤ 1%).
- **Chạy thật:** chạy tiếp doc-2 với `llm_max_in_flight` = 64 rồi 100 (dry-run trước). Báo lời gọi/phút, số 429, mức đồng thời thực tế bộ tự
  điều chỉnh giữ được, chi phí. Sau đó A9/A10 như kế hoạch.
- **Tôi kiểm:** đọc diff, chạy test, đột biến bộ giới hạn và phép chốt theo thứ tự, đối chiếu số lời gọi thừa với mô phỏng.
