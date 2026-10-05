# v4-02 — Mọi stage ghi thời gian chạy và lời gọi mô hình

**Nguồn chân lý:** nguyên tắc số một của v4 (phút/cuốn, USD/cuốn) · **Ai:** nhân viên (ghi số), Claude (báo cáo) · **Phụ thuộc:** — ·
**Chi phí mô hình:** 0

**Trạng thái:** phần nhân viên đã hoàn tất (0 USD); phần script báo cáo `bao_cao.py` vẫn do Claude phụ trách. Xem [báo cáo](../../report/v4-01-02-nghiem-thu-2026-10-04.md).

## Vì sao (Claude, 2026-10-04)
- Muốn tối ưu phút/cuốn thì phải đo được phút theo từng khâu. Hiện chỉ cụm và nhắc tên ghi `runtime_seconds`. Các khâu gọi mô hình (A2,
  A3, A4/A5, A7, neo, danh tính, A8 chính, A8 phụ, tên khái niệm, tên module) chỉ ghi token, không ghi thời gian.
- `created_at` không dùng thay được: giữa hai stage có thời gian chờ chủ dự án duyệt chi, tạm dừng máy, dry-run.

## Việc cần làm
- Mọi stage ghi vào `stats`:
  - `runtime_seconds`: thời gian chạy thật của `execute` trong lượt tạo artifact. Nếu chạy tiếp từ điểm lưu thì cộng các đoạn chạy;
    điểm lưu giữ phần đã chạy;
  - số lời gọi mô hình, token vào, token ra, gồm cả thử lại và sửa phản hồi, theo cùng tên trường cho mọi stage (`model_calls`,
    `input_tokens`, `output_tokens`).
- Các trường này **không** vào config hash; artifact cũ vẫn tái dùng được.
- A1 (ingest) ghi số trang và thời gian parse trong manifest chunks.

## Nghiệm thu
- **Test:** mỗi stage có `runtime_seconds` và ba trường đếm; config hash không đổi khi chỉ có số đo khác; chạy tiếp từ điểm lưu thì cộng
  thời gian.
- **Chạy thử 0 USD:** dry-run một tài liệu nhỏ không làm hỏng cache.
- **Claude:** viết `scripts/do-chi-phi/bao_cao.py`, in phút và USD theo khâu cho một tài liệu từ manifest, để mọi vé v4 báo trước và sau
  bằng cùng một lệnh.

## Bàn giao nhân viên — 2026-10-04

- 19 `execute` tạo artifact đã dùng bộ đo chung; số đo ở `manifest.stats`, **không** trong payload/config/hash. Chốt timer sau khi
  `execute` trả về để tính cả xử lý/render sau lưu artifact. Parse tree không bị tính thêm một lượt ingest trùng chunks.
- Checkpoint giữ số đo cộng dồn; chỉ khôi phục sau khi stage chấp nhận checkpoint. Không cộng thời gian tắt máy/chờ duyệt, không cộng
  trùng các checkpoint phụ cùng lượt, không lấy số đo từ checkpoint khác cấu hình hoặc bị bác vì đổi nguồn.
- Lỗi/ngắt mềm flush số đo batch dở nhưng không tiến checkpoint công việc. Kill cưỡng bức/tắt máy đột ngột vẫn có thể mất phần số đo
  sau checkpoint cuối, không được báo phần đó là đã đo đủ.
- `model_calls` đếm HTTP attempt thật ở transport Gemini/embedding, gồm retry và sửa JSON. Token cộng usage từng phản hồi, cả token
  suy nghĩ; không đếm thêm usage gộp của session. Context đo được truyền tới worker song song A3, model jobs và Vertex embedding.
- `usage_responses`, `token_usage_complete`, `measurement_history_complete` chỉ rõ phần thiếu số đo. API không trả token không được
  hiểu là đã đo được 0; checkpoint/artifact cũ không được dựng số phút hay chi phí ngược từ `created_at`.
- `embedding_model_calls`, `embedding_input_tokens` tách embedding khỏi tổng để script chi phí không áp nhầm giá LLM cho khâu có cả hai.
- Chunks mới có `page_count` (đếm trang Docling, gồm trang trắng), `parse_runtime_seconds`, `parse_reused`. DOCX/parser không có số trang
  trả `null`; parse tái dùng có thời gian parse **lượt hiện tại** bằng 0 và `parse_reused=true`.
- Dry-run naive-bayes khóa transport mạng: 0 lời gọi, 60 manifest giữ nguyên byte/hash. Cache cũ không bị ghi lại để bổ sung telemetry.
- Test bao phủ resume, checkpoint phụ, nguồn sai, cache legacy, đủ 19 stage, retry/repair song song và embedding. Test timer đã đỏ khi
  bỏ restore; test transport đã đỏ khi bỏ truyền context tới worker; cổng đủ stage đã bắt hai nhánh resume bị bỏ sót trước khi sửa.
