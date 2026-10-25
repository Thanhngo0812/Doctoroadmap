# W09 — rà soát độc lập R5, 2026-10-25

**Request changes: 2 Required, 0 Critical.** Ghim `work/w09-assistant` tại `da4d6399965f5a67accaacc6ea34af8ce56f0dd5`, nền `46d829a55a62d852897f07102e89cf9a1fd5185e`. Không sửa worker hoặc main. Đã đọc vé W09, spec answer-3, báo cáo chức năng và báo cáo bổ sung session UI. Áp dụng code-review-and-quality.

## Required R-W09-1 — gửi ngay sau final làm mất câu hỏi khi usage còn chậm

Vị trí: **`src/web/frontend/src/useAssistant.ts:73`**, cùng `:98`, `:102`, `:110`; hành động xoá ô nhập tại `Assistant.tsx:67`.

Khi nhận final, hook gọi `setLive(null)`. Ô nhập và nút gửi được bật trở lại, nhưng `active.current` còn giữ controller cũ cho đến khi stream kết thúc **và** GET `/me/usage` hoàn tất. Người học gửi câu tiếp theo trong khoảng đó: submit xoá draft, `run()` gặp `active.current` rồi return, không có POST và không báo lỗi. Đây là mất nội dung người dùng trên đường bình thường khi một request phụ bị chậm.

Đã chạy React/AuthProvider/Markdown thật, chỉ fake fetch. SSE đầu đã gửi final **và EOF**, còn usage refresh bị giữ lại. Composer enabled; sau gõ và gửi câu thứ hai, quan sát độc lập là `usageCalls=2`, **chỉ 1 POST `/turns`**, **draft rỗng**. `final-usage-race-red2.xml`: đúng 1 test, 1 assertion failure, 0 error/skip/setup failure; native 1. `repro-native.json` ghi lệnh và pin. Lượt đầu `final-usage-race.xml` là lỗi resolve React từ scratch, được giữ nhưng không tính chứng minh.

Cần đồng bộ khả năng nhận lượt với trạng thái UI, để câu hỏi được gửi hoặc vẫn được giữ trong draft khi chưa nhận. Metadata refresh không được âm thầm làm rơi lượt mới. Nếu cho lượt mới chạy sớm, completion/finally của lượt cũ phải kiểm danh tính trước khi cập nhật live mới. Thêm ca deferred usage này; không cần nới timeout.

## Required R-W09-2 — ép cache-only cho cả công cụ mở bài giảng thông thường

Vị trí: **`src/web/backend/wayfinder/infrastructure/learning_runtime.py:54–57`**.

Callback `get_lecture` luôn truyền `cache_only=True` và bỏ `allow_spend`, kể cả khi mô hình gọi công cụ thông thường. Vì vậy với khái niệm chưa có cache, công cụ trả `not_cached`, `body_md=''` và không thể cung cấp bài được yêu cầu; trợ lý vẫn phát thẻ lecture. Điều này khác đường chuẩn của core và yêu cầu nối W09.

Phân biệt nguồn chân lý: `doc/tro-ly-3-spec.md:43` và `:186` cấm sinh bài trong **focus prefetch**. `task/web/W-09-tro-ly-va-phien.md:27–29` yêu cầu callback chuyển `cache_only` xuống use case như `composition_phase_b.py`, kiểm cả focus hit/miss lẫn tool call bình thường. Core gọi prefetch tại `assistant.py:212` với `cache_only=True, allow_spend=False`; công cụ thông thường tại `assistant.py:302` có `allow_spend` và không ép cache-only. Canonical composition tại `composition_phase_b.py:230–231` giữ sự phân biệt này.

`repro_ordinary_lecture.py` chạy WebLearningRuntime và AssistantUseCase thật trên graph tổng hợp, InMemoryPhaseBStore, FakeClock và ScriptedModel; không PG/provider. Actual: công cụ `not_cached`, body rỗng, **0 fake lecture call**. Control chỉ thay callback trong bộ nhớ bằng forwarding chuẩn: `ready`, có nội dung, **1 fake lecture call**. Assertion native 1; kết quả tại `ordinary-lecture-result.json`. Cần forward cờ thật và quyền chi theo caller; giữ test focus miss = 0 lần sinh, thêm test ordinary tool cache miss = sinh bằng fake qua guard chuẩn.

## Phần đạt và phạm vi chấp nhận

- Ownership phiên lấy actor/doc từ course, kiểm lại trước khi chạy sau khoá phiên. Scope module lấy node_ids từ graph công bố. Adapter loại owner/doc/version do mô hình đưa vào; DTO/SSE whitelist không chuyển raw args, validation, private ID hoặc quiz answer ra client. Không phát hiện hồi quy quyền trong delta đã đọc.
- Admission dùng khoá actor cho rate mới; retry giữ payload identity, payload khác trả conflict. Khoá PG theo session tuần tự hoá intent khác nhau; đọc lịch sử trước khi gọi core chống gọi lại khi prompt đổi. Focus là từng lượt, truyền ID nguyên vào core; hit/miss qua cache đã có test thật. Usage dùng typed ledger, tách actor, không cộng counted-in-build hai lần.
- UI đã có test giữ completed turn khi lịch sử cũ về muộn, key client_turn_id giữ preview, retry giữ ID/focus và nguồn/action chỉ từ registry/sự kiện có cấu trúc. Hai lỗi mới ở trên chưa được các ca đó bao phủ.
- Chấp nhận phạm vi thư viện **chỉ đọc** và preview quiz/document đã lưu; submit/chấm và thư viện đầy đủ thuộc W10. Producer tiếp tục sau client disconnect trong cùng tiến trình; chưa có durable queue là giới hạn đã công bố. Không yêu cầu Cloud Figma hoặc gọi nhà cung cấp thật.

## Đối chiếu bằng chứng

`check_receipts.py` đã kiểm **238 hash/kích thước**, **22 tệp nguồn/blob liên quan**, native UI và JUnit chọn lọc; không có mismatch trong các manifest được kiểm. Backend không đổi từ cổng `56acc16` đến pin hiện tại. Source không đổi từ browser `c048b72` đến `da4d639`. Bằng chứng Python 2.622 pass/1 skip/1 xfail là cổng chức năng lịch sử, không bị gọi là lượt Python mới cho UI.

Đã đọc báo cáo bổ sung `w09-session-ui-2026-10-25.md` và `verification.json`: **198 React pass**, native build/browser 0; audit khớp **12 cấu hình, 99 ảnh, 43 Axe, 371 bản ghi HTTP/SSE**, 0 page error. Parse độc lập **31 trace tee** có final answer-3 và không chứa các private key được guard kiểm. Phân biệt số bản ghi HTTP/SSE với số request duy nhất như báo cáo đã nêu. Không chặn vì báo cáo chức năng cũ ghi React 192/browser-final8 khi đã có hồ sơ bổ sung đúng nguồn.

19 mutant có JUnit assertion failure/native 1 và 0 error đúng receipt. **Giới hạn:** không phải 19 phép phá trên byte của HEAD hiện tại: chỉ 2 SHA nguồn khai báo trùng byte hiện tại; nhiều SHA khác khớp commit phát triển cũ. `mutation-source-history.json` ghi điểm đối chiếu; 4 hash chưa ghép được với blob LF/CRLF đã commit. Vì vậy lần soát này chấp nhận các receipt đó là lịch sử RED, không dùng chúng làm chứng minh exact-source cho toàn bộ HEAD. Đây là giới hạn bằng chứng, không phải một lỗi sản phẩm thứ ba. Điều phối đang chạy gate/mutation/browser độc lập trên integration.

Các RED chọn lọc về cấu hình lecture, thư viện, tool order, history và preview có failure assertion thật trong JUnit; các GREEN tương ứng có case chạy, không setup error. Không chạy lại full PG/browser trong lần soát này.

## Gói bàn giao

`w09-counterexamples.zip` chứa exact helper/config đã chạy, native receipt, source SHA, JUnit và kết quả control; SHA-256 `6bdd6a21cbbe3b7178c33098f9bf27a97d81d2bfbc829041073d2600624d9bec`. `REPRO.md` có lệnh chạy từ gốc repo và cách dùng helper như focused test. `receipt-check.json` ghi kiểm chứng máy đọc được. Các tệp chỉ nằm trong `tmp/coord-r5-web-review-20261025`.

Worker có hai thư mục SQL untracked được báo cáo từ trước (`report/w15-evidence/sql/latest`, `report/w25-evidence/sql/latest`); không đọc hoặc dọn chúng. Không thay đổi tệp đã theo dõi, không mở .env, provider, ADC, live/cache/heldout hoặc push.
