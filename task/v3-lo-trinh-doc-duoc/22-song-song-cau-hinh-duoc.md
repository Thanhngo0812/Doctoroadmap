# 22 — Gọi mô hình song song cấu hình được (≥ 100 lời gọi đồng thời), kết quả y hệt cách chạy tuần tự

**Nguồn chân lý:** vé này (hạ tầng, không đổi phương pháp) · [báo cáo nghiên cứu](../../report/nghien-cuu-song-song-cao-2026-10-02.md) ·
**Ai:** nhân viên · **Phụ thuộc:** — · **Chi phí mô hình:** 0 để làm và kiểm; chạy tiếp doc-2 như dự toán cũ (≈ 6–9 USD)

**Trạng thái:** mã và nghiệm thu 0 USD đã xong 2026-10-02; lượt chạy thật doc-2 tiếp tục thuộc vé 12. Chủ dự án yêu cầu
2026-10-02: tăng song song lên 100 hoặc hơn tuỳ cấu hình, để sau này phục vụ người dùng.

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

## Kết quả triển khai 2026-10-02

- Một `AdaptiveModelLimiter` dùng chung cho sinh văn bản và embedding trong từng tiến trình, có trần đồng thời, TPM, RPM tùy chọn,
  giảm một nửa khi gặp 429/503, hồi phục dần và tôn trọng `Retry-After`. Các giới hạn chỉ nằm trong manifest, không tham gia config hash.
- Pass phụ hỏi trước theo cửa sổ rồi chốt đúng thứ tự cũ; checkpoint ghi một lần mỗi lô, đọc được checkpoint doc-2 cũ. Ledger đánh giá
  chuyển sang JSONL nối thêm nhưng vẫn đọc/migrate được JSON cũ. Vertex embedding chạy song song và giữ nguyên thứ tự kết quả.
- Unit test toàn kho và 6 integration test đều xanh. Test riêng bao phủ cửa sổ 1/4/50, cặp bị cắt, hồ sơ đổi phải hỏi lại, trần
  concurrent/TPM/RPM, hạ rồi hồi phục sau throttle, ledger JSONL và phản hồi Vertex hỏng.
- Phát lại 0 USD, cửa sổ 50: `doc-3` khớp tuyệt đối 18 cạnh, trượt cache 2/380 (0,526%); `nhap-mon-ml` khớp tuyệt đối
  88 cạnh, trượt cache 8/1.381 (0,579%). Không câu trả lời giả nào lọt vào cạnh cuối.
- Dry-run sáu tài liệu với max 100/cửa sổ 50: năm tài liệu đã xong đều `reused`; doc-2 tiếp tục đúng checkpoint
  `secondary-5a1e6d…`, còn 5.996 cặp, 4.758 cặp cần hỏi hai chiều, ước 9.516 lời gọi/8,252907 USD trước retry.

### Sửa sau phép chạy thật 2026-10-02

- 429 được giảm theo **thế hệ permit**: một làn sóng nghẽn chỉ chia đôi concurrency một lần, kể cả phản hồi cùng thế hệ về sau khi
  thời gian tạm dừng đã hết. Permit của thế hệ mới mới được phép giảm tiếp; sàn concurrency là 2.
- Hồi phục cộng 1 sau mỗi `current_limit` lời gọi thành công thay vì mốc cố định 20. Retry Gemini mặc định tăng từ 3 lên 8 để một làn
  sóng nghẽn khi chạy song song cao không làm cả stage bỏ cuộc quá sớm.
- Test hồi quy đã được nhìn thấy đỏ trên mã cũ (`2 != 4` khi 429 cũ về muộn), rồi xanh sau sửa; toàn bộ unit test xanh.

## Góp ý giữa chừng (Claude, 2026-10-02) — giới hạn sụp 64→1 trong một đợt nghẽn

**Chẩn đoán của nhân viên đúng.** `AdaptiveModelLimiter.release` chia đôi `current_limit` cho **mỗi** 429. Một đợt nghẽn làm hàng chục lời gọi
đang bay cùng nhận 429, nên giới hạn bị chia đôi hàng chục lần. Đây là lỗi kinh điển của AIMD; TCP xử lý bằng luật "mỗi sự kiện nghẽn chỉ
giảm một lần".

**Không nên khử trùng theo cửa sổ thời gian** (cách trong test đang viết dở: "một lần mỗi cửa sổ tạm dừng"). Một lời gọi gửi **trước** lần
giảm có thể trả 429 **sau** khi cửa sổ 1–2 giây đã hết: độ trễ một lời gọi 2–5 giây, tới timeout. Khi đó vẫn bị chia đôi thêm cho cùng một
đợt nghẽn.

**Làm theo thế hệ (epoch):**
- `acquire` ghi `permit.epoch = limiter.epoch`.
- 429 trên permit có `epoch == limiter.epoch`, tức gửi sau lần giảm gần nhất:
  - chia đôi, tối thiểu `llm_min_in_flight` (mặc định 2, như vé đã ghi; mã hiện để 1);
  - `epoch += 1`;
  - đặt tạm dừng chung.
- 429 trên permit **thế hệ cũ**: không đổi giới hạn, không xoá chuỗi thành công. Chỉ tạm dừng và thử lại lời gọi đó. Đếm riêng
  `throttle_same_event` để báo.
- **Hồi phục:** +1 sau `current_limit` lời gọi thành công liên tiếp của thế hệ hiện tại (khoảng một vòng, như pha tránh nghẽn của TCP), thay
  cho mốc cố định 20. Từ 32 lên 64 mất khoảng 32 vòng, thay vì 640 lời gọi không một lỗi.

**Test đỏ trước khi sửa:**
- 8 permit cùng thế hệ đều 429, **có cái nhả sau khi đồng hồ giả đã vượt cửa sổ tạm dừng** → giới hạn chỉ giảm một lần (8 → 4).
- Permit lấy **sau** lần giảm rồi 429 → giảm lần nữa (4 → 2).
- Không bao giờ dưới `llm_min_in_flight`.
- Hồi phục: sau đúng `current_limit` thành công cùng thế hệ thì tăng 1; 429 thế hệ cũ không xoá chuỗi.
- Đột biến bỏ kiểm `epoch` → test đầu đỏ.

**Ghi chú thêm:**
- Bộ chuyển đổi (`gemini.py`) vừa để bộ giới hạn tạm dừng chung, vừa tự `sleep(2**attempt + random())`. Giữ được, nhưng kiểm `gemini_max_retries`
  đủ lớn khi chạy song song cao, để một đợt nghẽn không làm lời gọi bỏ cuộc và dừng cả stage.
- Báo trong lượt chạy thật: số 429 theo thế hệ, `current_limit` theo thời gian, lời gọi/phút.
