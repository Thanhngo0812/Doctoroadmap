# Rà soát độc lập W08, vòng 4 — 2026-10-24

Kết luận: **Approve phạm vi delta được giao; 0 Critical, 0 Required**. Hai lỗi R-W08-1 và R-W08-2 đã đóng trong mã tại `c8c687b63afff86d628688de73abb92dfd4f17a2`. Không yêu cầu sửa mã thêm từ lần soát này.

Ghim nguồn: worktree `tmp/w08-lecture`, nhánh `work/w08-lecture`, mốc cũ `89122f6`, nguồn cổng cuối `b4136987668c3fb822ea374f399b947064ce7f18`, main nền `5936a5d91b6c3979f1918b33ce330403414b776f`. Đã đọc `AGENTS.md` và áp dụng `.agents/skills/code-review-and-quality/SKILL.md`. Chỉ ghi tệp trong thư mục scratch này; không sửa worker/main, không chạy PostgreSQL, full suite, browser hoặc provider.

## Hai Required đã đóng

- **R-W08-1:** `Learning.tsx:19`, `:92`, `:129`, `:202` truyền và đọc `data.progress.nodes` hiện tại cho tiên quyết và tiếp theo. Checkbox, bộ đếm và nhãn cùng một nguồn. Đường lưu lỗi tại `:178` phục hồi node trong nguồn đó, nên nhãn cũng rollback. Dependency sinh bài tại `:72` không chứa tiến độ. Hai ca deferred save trong `Learning.test.tsx:129` quan sát đồng thời nhãn, checkbox, bộ đếm, nội dung đang đọc và số request lecture; không chỉ assert một flag mới gán. Hai ca helper độc lập kiểm từng nhãn riêng.
- **R-W08-2:** `Learning.tsx:84` đã nhận đúng dạng tiêu đề của `lecture3.py:75`: 2–4 dấu `#`, thụt space/tab, không bắt buộc space sau `#`, không phân biệt hoa/thường và cho đuôi `:`. Phần lọc chỉ dùng lúc streaming. Khi hoàn tất, `body_md` lấy nguyên từ final; `self_check` có dữ liệu được render trong disclosure. Bốn ca `self_check: null` tại `Learning.test.tsx:153` khẳng định đoạn cuối không có khuôn hỏi/đáp trở lại đầy đủ, không tự tạo đáp án.
- Core SA70 tại `lecture3.py:137` giữ phần dòng bắt đầu bằng `#` cho đến khi nhận đủ tiêu đề. Các assertion có tên trong `test_phase_b_lecture3_sa70.py:151`, `:161`, `:177`, `:192`, `:216`, `:222` bao phủ tiêu đề hợp lệ, tiêu đề bị cắt ở mọi vị trí, từng ký tự, tiêu đề có hậu tố không phải tự kiểm tra, lỗi khi còn nửa dòng và final không tách được. Đây là nguồn SA70 đã nhận, không phải bản sửa core do web tự viết.

## Kiểm chứng bằng chứng

Đã chạy `check_receipts.py` bằng Python stdlib trong scratch. Script chỉ đọc các đường W08 đã cho phép, nguồn liên quan và blob Git; không import ứng dụng. Kết quả đầy đủ tại `receipt-check.json`:

- **392/392 receipt** khớp SHA-256 và kích thước trong `required3/sha256-manifest.json`.
- **19/19 tệp nguồn liên quan** khớp SHA làm việc, manifest blob Git và commit nguồn `b413698`; khác biệt checkout chỉ là CRLF/LF. Không có thay đổi `src/scripts/tests` hoặc cấu hình nguồn từ `b413698` đến `c8c687b`.
- JUnit cuối chứa **2.511 Python pass, 0 failure/error, 1 skip và 1 xfail**; **181 React pass, 0 failure/error/skip**. Tất cả **33 assertion Learning** và **18 assertion backend** của invariant map đều tồn tại bằng classname/name thực. Bốn receipt lệnh/native exit cuối khớp gate-results và đều là 0.
- RED đầu đúng là lỗi hook: 17 skip và 1 hook failure, không phải chứng minh hai lỗi. RED2 có đúng **6 assertion fail, 11 control pass, 0 skip/error**. GREEN sau đó 17/17; focused 33/33. Sáu failure của RED2 đúng là hai nhãn và bốn dạng heading bị lọt ở bản cũ. Toàn bộ thân test helper của điều phối giữ nguyên.
- **15/15 mutant** có native exit 1, assertion failure thật, 0 error, cùng SHA nguồn trước/sau và JUnit failure count khớp. Tám backend mutant là bằng chứng cũ với byte nguồn vẫn khớp; bảy UI mutant được làm mới. Không nhầm đây là 15 lần chạy lại trên lượt cổng cuối.
- Đã parse lại độc lập **5 raw SSE trace**: thứ tự skeleton/delta/final hợp lệ; delta nối lại chỉ là `Phần chính hiện ngay.`; final có câu hỏi/đáp án; không lộ validation, public_id hoặc URL Cloudinary. Audit thực có **12 cấu hình, 109 ảnh, 17 Axe, 348 trao đổi HTTP**, không có unexpected error/page error/failed request.

## Rollback, cô lập người dùng và bảo mật

Không phát hiện hồi quy trong delta. Tiến độ UI lấy từ endpoint theo actor và không đi vào cache lecture. Đã đọc test cùng đường gateway/DTO: `test_w08_real_lecture3_cache_validation_stays_private_and_status_is_per_learner` kiểm hai actor, cache chung nhưng tiến độ riêng, SQL độc lập thấy validation chỉ nằm cache và không có learner_status trong cache; test DTO cố ý đưa admin key vào gateway rồi kiểm HTTP loại bỏ chúng. Các guard quyền truy cập, CSRF, node công bố, trang nguồn và Markdown/KaTeX giữ nguyên so với mốc W08 trước. Các ca backend này đều có trong JUnit cuối, cùng mutant bắt lỗi thực.

Receipt rollback trình duyệt có đọc SQL độc lập: B learned sau lưu, vẫn learned sau bỏ dấu lỗi, rồi not_learned sau bỏ dấu thành công; số request lecture và fake model không tăng. Bộ thu SSE dùng `Response.clone().text()` thật. Báo cáo đã nói rõ nhánh tee là instrumentation và bằng chứng hoàn tất cache sau disconnect đến từ ca direct HTTP/PostgreSQL riêng, không suy từ browser collector.

Giới hạn: lần soát này kiểm mã và bằng chứng được bàn giao, không tự chạy lại các cổng runtime. Điều phối đang chạy gate/browser độc lập để quyết định nghiệm thu; không dùng kết luận này thay cho kết quả chạy đó.
