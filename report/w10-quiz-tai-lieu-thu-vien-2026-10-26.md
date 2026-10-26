# W-10 — quiz, tài liệu và thư viện

**Hoàn tất triển khai, đề nghị điều phối nghiệm thu.** Mã kiểm cuối 4d2f652; 2.727 Python/212 React/build native0; browser12cấu hình/89ảnh/58Axe native0. Commit hồ sơ kế tiếp chỉ thêm báo cáo/bằng chứng; mã chạy không đổi, có SHA đối chiếu.

Đợt triển khai 2026-10-25, hoàn tất bàn giao 2026-10-26 (Asia/Ho_Chi_Minh), nhánh work/w10-quiz-documents tại tmp/w10-quiz-documents. Nhận main local b3c4426 đã ghép W-09/W-15 ở 7f54b14; giữ nguyên mọi worktree và bằng chứng cũ. Không tự đóng vé hoặc ghép/push main.

## Phạm vi và hợp đồng

Ba lát: quiz → đề public → nộp/chấm; tài liệu trực tiếp → Markdown/LaTeX/nguồn → tải .md; thư viện theo nơi tạo. API, sinh/cache/giải mù/chấm dùng QuizUseCase/DocumentUseCase/LibraryUseCase thật của SA-67/68, không sửa core. Không thêm migration; không đụng learning_usage.py hoặc api/builds.py của W-16.

- POST /courses/{cid}/quizzes: {scope:{kind:"roadmap"} | {kind:"module",module_id}, n?:1..10}. JSON trả 201; Accept text/event-stream trả item_ready rồi final{quiz}.
- GET /courses/{cid}/quizzes/{aid}: đề không đáp án, có submitted để phục hồi kết quả sau tải lại.
- POST /courses/{cid}/quizzes/{aid}/submit: {answers:{item_id:option_id}}. Giao dịch atomic chung attempt/progress; cùng lựa chọn idempotent, khác sau nộp conflict.
- GET /courses/{cid}/quizzes/{aid}/result: chỉ sau nộp, đúng owner/cuốn.
- POST /courses/{cid}/documents: {request,module_ids:[...],home_module_id?:...}. JSON 201 hoặc skeleton/delta/final{document}/failure; quyền/phạm vi/tần suất kiểm trước SSE headers.
- GET /courses/{cid}/documents/{did}; GET .../markdown tải chú thích nguồn do core export.
- GET library tái dùng W-09; bổ sung score đúng DTO. Module dùng group here/elsewhere từ core; origin không dùng để chia nhóm.

Actor/doc/version lấy từ course, owner body bị bỏ qua. DTO lọc allowlist tại gateway và Pydantic tại HTTP/SSE; không private attempt/options, validation, solver reason, chi phí hoặc Cloudinary ID. Kho Pha B PostgreSQL; không nhập learner store CLI.

## Giao diện và taste-skill

Áp dụng design-taste-frontend/app screens, frontend-ui-engineering, API/interface và triển khai từng lát. Giữ hướng editorial-greeting đã chốt ở W-09, Be Vietnam Pro, logo Artboard 9–28 và token main. Thêm duy nhất remark-gfm 4.0.1 (MIT) để đọc bảng Markdown trong tài liệu; bật theo prop gfm, mặc định bài giảng/trợ lý giữ renderer đã nhận. Tái dùng source/KaTeX an toàn, lazy-load renderer khi cần. npm audit production: 0 lỗ hổng; lockfile đi kèm.

Câu hỏi chính của màn quiz là “Tôi đã hiểu phần đang học đến đâu?”: nội dung câu hỏi lớn nhất, thứ tự theo câu đến, lựa chọn native radio có vùng bấm rộng, thanh đếm/nộp cố định. Kết quả trình bày đáp án/giải thích/nguồn cùng câu; đỏ chỉ ở phần sai. Tài liệu là một cột đọc, nguồn trang và tải .md rõ ràng. Thư viện là danh sách phẳng, bộ lọc nhóm tách khỏi nguồn tạo, số lượng tính từ dữ liệu hiện tại.

Tham khảo HTML/CSS mẫu W-10 của nhóm thiết kế và bản sửa D-R6-01 trên nhánh thiết kế; không nhập nguyên nhánh hoặc chép quy tắc filter button/assistant sai của 0b5993e. Bản đọc tại work/w24-figma-evidence cho thấy data-group và data-origin độc lập; mốc tham chiếu 26e4a9adc66410679b616b76dff9d5f1522a0d0a, tệp design/preview/w10_quiz_screens.html. Token/font/logo lấy main b3c4426, không lấy đè token từ nhánh thiết kế.

Đối tượng thật: khoá/module, bài học, câu quiz/bốn phương án LLM/Bloom, lần làm riêng của người, điểm sau nộp, tài liệu/nhãn Sx/trang, nơi tạo here/elsewhere và nguồn button/assistant. Không dùng số trang/điểm/giới hạn bịa; ngày hiển thị theo Asia/Ho_Chi_Minh.

## RED/GREEN ban đầu

- backend-red: bốn assertion fail trên API chưa có route W-10, không setup error.
- backend-green1: bốn đạt. backend-green2 phát hiện đếm tần suất hai lần trong bước chuyển admission ra trước SSE; giữ log, sửa tại ranh giới nhận yêu cầu. Ca thu hồi ban đầu thiếu composition sharing của fixture, không coi đó là phản chứng nghiệp vụ.
- backend-green3: 10 đạt gồm guard tự liệt kê route. backend-green4: 13 đạt gồm toàn bộ ca W-10 và kiến trúc/OpenAPI. SQL đã được chuyển khỏi application sang infrastructure theo guard kiến trúc, không hạ guard.
- react-red: nút quiz/thư viện chưa có trên trang thật. react-green1: hai đạt.
- react-behavior-red: một assertion fail khi lựa chọn lúc stream bị mất sau chuyển sang đề lưu; bốn control pass. react-green2: năm đạt sau giữ lựa chọn đúng item/option ID.
- react-regression1: 13 lỗi vì fixture W-07/W-08 chưa mô tả GET library mới, và ca “không có checkbox” không còn phân biệt checklist với bộ lọc thư viện. Bổ sung response items rỗng vào fixture; giữ các assertion hồi quy, giới hạn assertion checklist vào nhãn “Đã học”. react-regression2: 46 đạt.
- typecheck-dev1 bắt import thừa do lát mới; đã bỏ import, typecheck-dev2 native 0. Build dev bằng Vite chỉ là kiểm phát triển; cổng build chuẩn npm sẽ chạy cuối.

Bằng chứng report/w10-evidence/; basetemp/fixture dưới tmp/, không trộn ảnh UI. Chỉ dùng fake/PG 0 USD. Mốc backend đầu 8d7bcf8; phần React, browser, guard và cổng đầy đủ đang tiếp tục, chưa tuyên bố W-10 đạt.

## Soát lỗi trong lúc tích hợp

- document-render-red2: 2 assertion fail/5 control pass, không setup error: bảng chưa render và tiêu đề bị lặp. document-render-green: 9 đạt gồm hồi quy renderer. File document-render-red.xml đầu có một lỗi jsdom khi helper cố in vai trò không tồn tại; không tính lỗi đó là phản chứng bảng. RED2 chuyển sang kiểm DOM trực tiếp và đỏ đúng assertion.
- quiz-reload-red: HTTP báo submitted=false dù SQL đã lưu kết quả; 1 assertion fail. quiz-reload-green: 10 backend W-10 đạt sau projection lấy cờ từ snapshot riêng đã kiểm owner/cuốn.
- Soát độc lập Luna dùng Git HEAD, chỉ đọc: phát hiện cache history React còn submitted=false. history-reload-red: 1 assertion fail/7 control pass; history-reload-green: 8 đạt sau GET trạng thái mới từ server.
- keyboard-focus-red: 1 assertion fail/8 control pass khi canonical URL thay DOM radio và kéo focus về tiêu đề. keyboard-focus-green: 9 đạt; giữ DOM lựa chọn qua canonical transition, vẫn GET server để biết đã nộp, chỉ chuyển focus heading khi thực sự mở lần làm khác.
- Browser-dev1: Axe bắt radio chỉ có công thức thiếu accessible name; thêm nhãn Phương án A/B/C/D và aria-describedby tới nội dung KaTeX, giữ nguyên Axe. Dev2/3 lần lượt tái hiện hai lỗi reload nêu trên. Không dùng bộ ảnh dev làm bằng chứng cuối.
- browser-final1 dừng do CDP Page.enable timeout trong môi trường hạn chế, không phải lỗi sản phẩm. Chạy Chrome đầy đủ quyền ở final2: taste-inspector 0 FAIL, 1 WARN font math (KaTeX), rồi bắt lỗi focus khi cache trả nhanh. final3 chưa build lại bundle focus: không dùng làm bằng chứng vá, giữ log native1. Tất cả runtime đều đóng server và bỏ đúng DB UUID của riêng lượt kiểm. Lệnh tìm tiến trình browser sau đó không còn mục khớp để dừng; không tác động service của chủ dự án.
- Cổng đầu ef6b4f9: 2.727 Python đạt/1 skip/1 xfail/native0; 211 React/build native0. Đây là lịch sử trước vá focus cdcd836; không thay cổng cuối.


## Bộ kiểm cuối và bàn giao

Mã kiểm cuối **4d2f652f5a9564f54587ebe08051c525200b888e**, main nền **b3c4426666dd868040ea0bc52e6485f5af6e1ac4**. Nhận main ở worktree W-10; main không thay đổi trước cổng cuối. Sau mốc này chỉ bổ sung báo cáo/bằng chứng, không sửa mã/test/harness. Không tự nghiệm thu/ghép/push main.

React delivery: **212 đạt/native0**; production build **native0**, TypeScript và Vite đúng lệnh npm run build. Renderer lazy: chunk Markdown/KaTeX/GFM 440,29 kB (gzip133,35), index412,76kB (gzip117,66); không đưa editor hoặc UI kit mới. Browser delivery **native0**, **12 cấu hình** 390/768/1280 × sáng/tối × giảm chuyển động thật bằng Chromium, **89 ảnh**, **58 Axe document scope/0 violation**, **217 phản hồi HTTP đã ghi**, **0 pageerror**, ba video owner/learner/outsider. Không nhận mọi ảnh đều đã Axe. 69 mục contrast KaTeX được đo riêng, tối thiểu5,84:1; guard phản chứng bắt contrast1 và chữ bị che. Taste-inspector 390/768/1280:0FAIL/1WARN generic font math; Be Vietnam Pro giữ từ main.

SQL kết nối độc lập sau browser:12quiz_attempt,12submission,28documents,6progress đúng actor; usage giả có6quiz_gen,6quiz_verify,28document và27document_validation, tất cả0USD. Sau12quiz chỉ6lượt sinh/giải mù: các lần sau lấy ngân hàng lõi. Cùng ý nộp lại sau mất phản hồi trả nguyên kết quả đã lưu; không chấm thêm. Runtime đã dừng thread server, đóng store/engine và bỏ đúng DB UUID, dirtySourcePaths=[]. Chi phí nhà cung cấp thật0USD.

Kiểm thêm đóng hộp thoại khi đang stream: server hoàn tất rồi tài liệu mở được qua HTTP/PG; không giả định có row bền trước khi mô hình xong. Lượt thứ11/giờ trả429JSON trướcSSE, Retry-After3600 và số model call không đổi. Phạm vi6module bị UI chặn POST và backend trảscope_too_large/0call. Browser lỗi core có thông báo Việt/nútThử lại; outsider404, bị gỡ membership mất quyền ở request kế tiếp.

12mutant ở cdcd836 đều native1, assertionfail/0setup error, phục hồi byte nguồn; delivery-mutation-source-proof.json xác nhận mỗi tệp bị phá giống byte ở4d2f652. Các mutant cũ ở a1833f6/21a238f giữ lịch sử riêng, không đếm là lượt chạy HEAD cuối. Hai sửa harness sau cdcd836 chỉ bảo vệ tệp evidence và sửa phép kiểm thời điểm persistence, không thay mã sản phẩm. Luna soát độc lập đã xác nhận sửa history/focus; không thấy Required khác trong bề mặt W-10 đã soát, phạm vi chỉ đọc.

Giới hạn hồ sơ: nội dung mô hình là fake, không đánh giá chất lượng sư phạm của provider thật; không chạy replay trả tiền. Có121console event được phân loại trong JSON, không tuyên bố console sạch: HTTP401/404 và lỗi mạng chủ ý, CSP từ probeAxe. Giữ nguyên CSP. Ảnh1280fullPage có thể đặt thanh sticky ở vị trí đáy viewport đầu trong tệp dài; đây là ảnh browser nguyên bản, không sửa ảnh.

Báo cáo/runs/JSON/ảnh/video: [chỉ mục](w10-evidence/README.md), [runtime và SQL](w10-evidence/browser-delivery/runtime.json), [HTTP/Axe](w10-evidence/browser-delivery/audit.json), [mutation receipts](w10-evidence/mutations-final2/results.json).

Ảnh React thật: [quiz1280sáng](w10-evidence/browser-delivery/quiz-ready-1280-light.png), [kết quả](w10-evidence/browser-delivery/quiz-result-1280-light.png), [tài liệu1280sáng](w10-evidence/browser-delivery/document-view-1280-light.png), [tạo tài liệu390](w10-evidence/browser-delivery/document-create-390-light.png), [thư viện390sáng](w10-evidence/browser-delivery/library-here-390-light.png), [1280tối](w10-evidence/browser-delivery/document-view-1280-dark.png), [video learner](w10-evidence/browser-delivery/learner.webm).


## Đối chiếu bất biến với assertion chạy được

Tệp backend: src/web/backend/tests/test_content_w10.py, tiền tố test_w10_.

| Bất biến | Ca kiểm | Phép phá guard |
|---|---|---|
| Đề public không đáp án, owner từ actor, xáo option đúng, nộp lại cùng dữ liệu | quiz_public_snapshot_has_no_answers_and_submission_preserves_shuffled_mapping | public-answer/result-owner/idempotent-submit |
| Chỉ why_wrong của lựa chọn và điểm thư viện sau nộp | wrong_answer_returns_only_selected_why_wrong_and_library_score | selected-reason |
| 6module0call; 11request429 xuyên khoá | document_six_modules_rejected_before_model_and_eleventh_request_is_rate_limited | document-scope/document-rate |
| here/elsewhere độc lập origin, A tạo về B | library_groups_are_independent_of_button_or_assistant_origin | ui-core-group + React fixture chéo |
| Tần suất kiểm trước SSE; body không validation/admin | document_stream_is_public_and_rate_limit_fails_before_sse_headers | document-rate + public-answer |
| Attempt/progress cùng rollback; hai runtime tranh nộp chỉ một kết quả | submission_rolls_back_both_attempt_and_progress_when_core_write_fails; independent_runtimes_serialize_competing_submissions | atomic-submit |
| Quiz SSE không đáp án; thu hồi quyền ở request kế tiếp | quiz_sse_keeps_answers_private_and_revocation_denies_the_next_request | guard route inventory toàn repo |
| Trần lõi, ngân hàng quiz khi hết ngân sách; sai cuốn/not_found, option lạ/422 | core_limits_stop_document_model_and_keep_quiz_bank_available; saved_content_cannot_be_opened_through_another_book | content-book |

React src/web/frontend/src/Content.test.tsx có9ca: nút trên roadmap; nhóm chéo; giữ lựa chọn lúc stream và gửi đúng optionID; sửa phạm vi6module không POST; tải lại kết quả; bảng/LaTeX/source/URL an toàn; tiêu đề chỉ một lần; bỏ snapshot history cũ; giữ keyboard focus. Ba UI mutant mất lựa chọn/snapshot cũ/cướp focus đều bị bắt. Mọi ca RED giữ ở bằng chứng, không giảm assertion/timeout hoặc thêm skip.

Các lần lỗi harness: mutations.exit.json đầu chỉ khai báo cases nhưng thiếu entrypoint nên native0 không chạy guard, không tính là phép phá. Đã sửa trước các lượt mutations-run1/mutations-final/mutations-final2. browser-final4 có88ảnh/57Axe và dừng tại giả định row sớm; chỉ browser-delivery native0/89ảnh/58Axe là bộ cuối. browser-smoke5 lỗi setup do package playwright standalone không export expect.poll; thay bằng vòng chờ native5giây và assertion độc lập, smoke6 đạt toàn luồng trước chốt4d2f652. Giữ rawlog/native các lỗi này.

## Kết quả cổng bàn giao

- Python/PostgreSQL: **2.727 đạt,0fail,1skip,1xfail,8warning; native0**, pytest541,97giây/tổng556,75giây. gate-python-delivery/exit.json, gate-python-delivery.xml và rawoutput có command/native/sourceSHA.
- React: **212đạt,0fail/native0**, gate-react-delivery.xml. Build chuẩn npm gồmTypeScript/Vite native0. Browser native0/224,84giây. Tất cả cùng mã4d2f652, sourceclean.
- Skip: test_cloudinary_satisfies_shared_media_contract_when_explicitly_enabled; không bật liveCloudinary theo0USD. Xfail: test_replay_reproduces_the_live_turns_at_zero_usd, fixtureanswer-2 trướcSA-66 cần ghi lại có phí, đã có sẵn trênmain. Không thêm skip/xfailchoW-10.
- delivery-source-proof.json kiểm766tệp src/scripts và75tệp bundle, tất cả SHA còn khớp. Các JSON SQL W-15/W-25 do gateghi vào thư mục local riêng được chép43tệp/lượt bằng SHA vào bằng chứngW-10, giữ nguyên thư mục nguồn local/không stage tệp vé khác. Các HTTP/SQL W-06/W-14 bị testghi lại được wrapper khôi phục đúngbyte từ legacy-originals. Không thay bằng chứng đã giao cũ.
- Tạo tài liệu chạy nền trong tiến trình để hoàn tất khi đóngtab/hộp thoại; không thêm hàng đợi bền hoặc cam kết tiếp tục sau restartserver trong vé này. Kiểm đóng hộp thoại đã đạt bằng HTTP/PG riêng.
- Mọi chứng cứ UI cuối dùng nguồn thật HTTP/PG/core với nội dung mô hình giả. Cổng toànrepo xanh không là tuyên bố nghiệm thu lại tất cả SA. W-10 chờ điều phối soát/ghép; chưa mởW-16frontend.

## Đóng gói bằng chứng

raw-text-2026-10-26.zip giữ493tệp JSON/log/JUnit/Markdown nguyên byte trước chuẩn hoá khoảng trắng để Git kiểm được; raw-text-manifest.json cóSHA-256 từng tệp vàZIP, normalization-receipts.json ghi97bản hiển thị đã bỏ khoảng trắng cuối dòng. Không sửa kết quả hoặc assertion test. PNG/WebM cuối là ảnh/video browser nguyên bản, không chỉnh sửa. Ảnh/video dở giữ local trong thư mục lịch sử, chỉ native/log/runtime/audit của các lượt đó được đưa vào hồ sơ. Không có basetemp/ảnh unit giả trong Git.
