# Soát độc lập W-10 lần 8 — 2026-10-26

Ghim nhánh work/w10-quiz-documents tại aaf68eb6795c929169e5212a05093d8d817c76e3. Đọc spec/vé và lời giao lần 7; soát delta mới từ fa346c9 và toàn bộ sản phẩm W-10 so với main153c577. Nhận xét nguồn: **đạt; 0 Critical, 0 Required mới**. Điều phối chỉ ghép khi cổng tích hợp trên main hiện hành xanh. Reviewer này không chạy PostgreSQL; root giữ cửa cổng riêng.

## Hai Required cũ

- **R-W10-1 đóng về nguồn.** learning_gateway.py:11 gắn đúng một DocumentRequests theo PostgreSQL engine, settings, clock. learning_gateway.py:404 và learning_runtime.py:65 dùng cùng admission per actor cho button/tool; callback tool gọi trước DocumentUseCase, không nhân đôi thuật toán sinh/cache/ngân sách core. assistant_tools.py:6–14 dịch riêng WebError rate_limited thành kết quả tool an toàn, lỗi khác giữ nguyên. learning_gateway.py:242–245 suy ra warning từ kết quả nội bộ; DTO chỉ cho document_rate_limited và UI dùng câu Việt cố định. Tool args/private result không được serialize ra API. Replay client_turn_id vẫn short-circuit trước callback. Năm test PG ở test_content_admission_w10.py kiểm button→tool, tool→button/replay/crosscourse/actor forged, hai runtime tranh suất cuối, physical lock và thông báo lưu bền.
- **R-W10-2 đóng.** ContentPages.tsx:30 layout cleanup vô hiệu token theo cid/aid/location.key/unmount. :69 tạo token riêng; :73/:76/:79 kiểm chính token ở success/error/finally. HTTP POST vẫn hoàn tất, mở lại quiz đọc bản chấm server; phản hồi cũ không đổi result/error/auth/focus hoặc mở khoá request mới.

## Kiểm độc lập đã thực thi

Chỉ bản sao trong tmp/coord-r8-web-review-20261026; không sửa source main/worker.

1. frontend-check.cjs: Content.test.tsx + Assistant.test.tsx **33 đạt/0 fail**, native0 (content-baseline.xml). Bỏ riêng guard success/error/finally gây tương ứng **3/3/4 assertion fail,0 errors**, native1; source phục hồi nguyên byte (mutation-results.json).
2. Thêm đúng một ca độc lập: hai history entry cùng cid/aid; submit ở entry sau rồi Back về entry trước, response cũ đến muộn. Bản hiện tại **1 đạt**, bỏ location.key khỏi dependency layout guard gây **1 assertion fail/0 errors**, native1. same-attempt-history-green/mutant.xml và same-attempt-check.cjs. Ca này kiểm được điều không chỉ đổi attempt ID.
3. offline-boundary.py chạy WebLearningRuntime, WebAssistantUseCase, core DocumentUseCase thật, core store in-memory và admission stub cô lập. Cho hai lượt rồi từ chối: model calls2→2, hai tài liệu/two artifacts, error code/message/retry_after đúng; lỗi WebError khác không bị nuốt. Bỏ admission trong bản sao: model2→3, document2→3, **1 AssertionError**, native1. Đây là kiểm boundary, **không thay PostgreSQL**. First run lỗi stdout CP1252 trước assertion, không tính RED; lượt trong offline-check.py đã đặt UTF8 và lưu native/log đầy đủ.
4. Không call provider, embedding, SMTP hoặc media thật; chi ngoài **0USD**. Node-only frontend config trỏ dependency có sẵn bằng alias, không tạo junction/symlink/hardlink.

## Xác minh hồ sơ của nhóm

- **616/616** tệp manifest evidence đúng SHA/size; **544/544** raw ZIP members đúng SHA/size, archive SHA đúng (raw-archive-check.py/receipt.json).
- Bốn receipt gate Python/React/build/browser trên source **1fc0f55** đều native0, **772 source SHA mỗi receipt** khớp worker hiện tại; source/script/test không đổi giữa1fc0f55→aaf68eb (gate-source-audit.json).
- **19** mutation receipts đúng source/restored/handoff SHA, native1,0setup errors và named failing assertions; không gán lại thời điểm mutation9bb90d9 thành chạy trên HEAD mới. mutation-provenance-audit.json.
- Author gate **2775 Python/219 React/build** là bằng chứng tác giả trên1fc0f55, nhận main163917c. Main hiện153c577 có thêm docs; root vẫn phải nhận main/chạy cổng theo quy trình, không xem thay đổi docs là tự miễn gate.
- Browser tác giả:27SSE,26terminal và1huỷ chủ ý,0privacyFailures; scripts/w10_web_check.cjs:463–470 kiểm rejected promises/missing body/cancellation. Lỗ kiểm Promise.allSettled của lần7 đã được đóng ở harness. Đây là đọc lại evidence, không thay browser root mới.

## Các trục soát và giới hạn

Correctness: DTO allowlist trước chấm không đáp án, owner/doc-bound, option mapping/atomic submit/idempotency, library group, scope tối đa5, document background completion giữ như lần7; bản vá mới có guard falsifiable. Architecture: admission tần suất ở web, sinh/cache/monetary guard vẫn core; adapter _tool private hook rất nhỏ và có test thực, không phát hiện thay đổi semantic core. Readability: diff sản phẩm mới gọn, token dùng identity đơn giản, không thêm state machine/speculative abstraction. Security: actor bind phía server, warning enum/câu cố định; Markdown skipHtml/KaTeX trustfalse và link/media policy giữ. Performance: admission theo bucket được khoá PostgreSQL, max10lượt/h; không phát hiện truy vấn/N+1 mới cần chặn.

Không yêu cầu sửa private hook chỉ vì đó là hook nội bộ; rủi ro tương thích đã có named runtime/HTTP tests. Không mở lại Cloud Figma, không thay Vertex. Chưa thấy blocker sản phẩm mới trong phạm vi soát; kết luận toàn vé còn phụ thuộc root cổng PG/React/build/browser mới.

**Bảo toàn:** 39 source/script paths của W10 đã băm trước/sau, tất cả nguyên byte (source-preservation.json). Mọi mutation chỉ trong scratch đã phục hồi. Không commit/push, không đụng dữ liệu thật/heldout/worktree nguy hiểm.
