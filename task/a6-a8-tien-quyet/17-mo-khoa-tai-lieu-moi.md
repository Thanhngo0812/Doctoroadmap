# 17 — Mở khoá đường chạy tài liệu mới: guard tên ký hiệu, telemetry A3/A4, cổng bộ vàng

**What to build:** Ba sửa nhỏ để `doc-1`, `doc-2`, `doc-3` đi hết A1–A5. Cả ba đều nằm trong phase đã đóng, nên vé
này là **ngoại lệ có chủ đích**, phạm vi hẹp, mỗi mục một test đỏ được khi bỏ guard.

Gốc: [F107, F108, F109](../../feedback/F19-a6-a10-cum-chu-de-va-tien-quyet.md) — nhân viên phát hiện khi chạy thật
`doc-3` và dừng đúng luật của vé 11.

**Blocked by:** None. **Chặn:** vé 11 không chạy tiếp được cho tới khi vé này xong.

**Status:** done — **chủ dự án đã đồng ý ngoại lệ ngày 2026-09-20**: vé này được sửa code trong phase A3
và A4 đã đóng, đúng ba mục dưới đây và không hơn. Code, test, chạy thật và replay hoàn tất ngày 2026-09-20.

**Điều kiện nhận lại:** bốn tài liệu cũ chạy lại cho `reused=true`, và điểm vàng A4 giữ nguyên **35/2/12**
(reviewer tính lại ngày 2026-09-20: 11/0/0 · 10/0/0 · 7/1/3 · 7/1/9; mốc 31/0/16 trong bản giao việc là baseline v1 cũ, nhân viên đính chính đúng). Kèm
danh sách đột biến đã thử cho từng mục, như mọi vé khác.

> **Đính chính mốc nghiệm thu:** `31/0/16` là baseline A4 v1 trước khi chủ dự án nhận quan hệ mở v3 ở Vòng 27.
> Baseline có thẩm quyền trên `main` hiện nay là **35/2/12**; chạy lại bốn artifact hiện hành cho đúng từng dòng
> `11/0/0`, `10/0/0`, `7/1/3`, `7/1/9`. Vé này không đổi config A4 nên cả bốn đều `reused=true` ở v8/v7/v7/v7.

## A. F107 — A3 phải tự loại tên chỉ là ký hiệu

- [x] Validation của A3 loại ứng viên có **tên chỉ gồm ký hiệu** (`alias_kind(name) == "symbol"`), đếm vào stats
      bằng một khoá riêng, ví dụ `rejected_symbol_only_name`.
- [x] **Không** loại viết tắt: `DL`, `AI`, `ERD` phải sống sót (`alias_kind` trả `abbreviation`).
- [x] Ký hiệu vẫn vào được trường `symbols` của một khái niệm có tên chữ, như hiện nay; chỉ cấm nó **làm tên node**.
- [x] Bất biến `node chỉ có tên ký hiệu` ở `canonical.py` **giữ nguyên** làm chốt cuối; sau sửa thì không còn ai chạm tới.
- [x] Test: mô hình trả entity tên `X` thì A3 loại và đếm; trả `DL` thì giữ. Đột biến: bỏ guard, đổi `symbol` thành
      `abbreviation`, loại luôn cả alias ký hiệu.
- [x] Chạy lại A3 cho `doc-3`, dán số ứng viên trước/sau và danh sách ứng viên bị loại.

Dữ liệu thật của `doc-3`: `candidate_e70160c0a9cacaf16e6e4a95` tên `X` và một ứng viên tên `Y`, cả hai
`learnable=true`, trích từ câu *"X and Y can be anything and it can be multi-modal!"*. Luật cấm ký hiệu **chỉ nằm
trong prompt few-shot**, không có trong code — trái user story 40 ("mọi kiểm tra cấu trúc nằm trong code chứ không
trong prompt").

## B. F108 — A3 và A4 phải ghi token và chi phí

- [x] Mỗi lời gọi của A3 và của A4/A5 lấy `usage` từ API và cộng dồn, như `model_calls.py` của A8 đang làm.
- [x] Manifest ghi `cost_summary`: `model_id`, input/output token, USD, và **nguồn bảng giá + ngày kiểm**.
- [x] Stats giữ luôn `llm_calls` như cũ để không mất số cũ.
- [x] Test: fixture phát lại có `usage` thì cost_summary cộng đúng; không có `usage` thì ghi 0 và không nổ.
- [x] Chạy lại A3 `doc-3` và dán token/USD thật.

Hiện chỉ có `llm_calls=256` cho `doc-3`, không có token. `doc-2` ước tính hàng nghìn lời gọi, nên không có telemetry
thì **không giữ được trần 50 USD** mà vé 11 yêu cầu.

## C. F109 — Cổng bộ vàng A4 cho tài liệu mới

Quyết định của reviewer, có căn cứ ở spec D13: *"Cờ node sai thu được ở [bộ vàng tiên quyết] dùng luôn làm mẫu kiểm
A4 trên tài liệu mới; đợt này không gán vàng A4 mới."* Nghĩa là **không** gán bộ vàng A4 mới cho `doc-1`/`doc-2`.

- [x] `a4` vẫn **bắt buộc** `--gold` là một bộ vàng hợp lệ, đầy đủ: nó là cổng hồi quy chứng minh A4 đã được đo.
- [x] Khi `doc_id` **không** nằm trong bộ vàng, chỉ chạy nếu có cờ tường minh mới, ví dụ `--no-gold-for-doc`, và
      manifest ghi `a4_gold_coverage: "none"` cùng `gold_sheet_id` của bộ vàng đã dùng làm cổng hồi quy.
- [x] Không có cờ thì vẫn báo lỗi như cũ. **Không** thêm document rỗng vào bộ vàng để lách.
- [x] Không sửa `tests/fixtures/a4/gold-blind.json`.
- [x] Test: doc trong bộ vàng chạy như cũ; doc ngoài bộ vàng không cờ thì lỗi, có cờ thì chạy và manifest ghi đúng.
- [x] Báo cáo cuối phải nói rõ: ba tài liệu mới **không có bộ vàng A4**, chất lượng gộp của chúng chỉ được kiểm gián
      tiếp qua cờ của người gán nhãn tiên quyết.

## Sau khi xong

- [x] Chạy tiếp vé 11 theo đúng thứ tự `doc-3` → `doc-1` → `doc-2`, và kiểm hai điểm đã ghi ở vé 11: watermark của
      `doc-1` (dừng và báo nếu chunk còn chứa email), và luật ngôn ngữ của A5 với hai tài liệu tiếng Anh.

## Kết quả nghiệm thu ngày 2026-09-20

- A3 `doc-3`: candidates v1 → v2 là **201 → 198**, `learnable` **105 → 102**. Guard đếm đúng **2** và loại
  `X`, `Y`. Một bản lặp `Deep Learning` ở section khác cũng mất do biến thiên đầu ra lần chạy thật, không phải guard.
- Telemetry A3: **256 calls**, 671.846 input + 47.240 output token, **0,2388215 USD**. A4/A5: **56 calls**,
  57.327 input + 16.733 output token, **0,03943125 USD**. Tổng doc-3: **0,27825275 USD**.
- A4/A5 `doc-3` v1: 154 node (58 text, 96 media), 129 cạnh, `document_language=en`; **58/58** mô tả text qua
  luật tiếng Anh. Manifest ghi `a4_gold_coverage=none`, đúng `gold_sheet_id`; replay A3/A4 không mạng đều tái dùng.
- Mutation đã thấy đỏ: bỏ guard (hành vi cũ), đổi `symbol` thành `abbreviation`, loại alias ký hiệu, bỏ
  `thoughtsTokenCount`, và bỏ yêu cầu cờ `--no-gold-for-doc`. Test không-usage giữ ba số token/USD bằng 0.
- Toàn suite **434 test xanh**. Bốn A4 cũ tái dùng v8/v7/v7/v7; baseline hiện hành **35/2/12** không đổi.
- Tiếp tục Vé 11 tới `doc-1`: ingest v1 xong, nhưng **114/229 chunk trên 110 trang** còn watermark
  `lOMoARcPSD`; regex email cho 0 chunk. Đã dừng trước A3 doc-1 và chưa chạy doc-2 đúng điều kiện dừng.
