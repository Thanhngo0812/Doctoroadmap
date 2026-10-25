# Lời giao ba nhóm sau nghiệm thu lần 6 — 2026-10-25

[Biên bản và bằng chứng](dieu-phoi-nghiem-thu-ba-nhom-lan6-2026-10-25.md). Soạn để chủ dự án chuyển từng phần;
điều phối chưa gửi phiên bên ngoài. W-09 `378131e` và W-15 `efed8db` đạt, ghép **local `7f54b14`**.
Nhận main local cuối sau commit hồ sơ; không push GitHub theo quyết định chủ dự án 24/10.

## 1. Nhóm web — bắt đầu W-10

> W-09 đã nhận, đóng R-W09-1/2. Không làm lại session/quyền/idempotency/renderer/usage-race/cache-only đã kiểm.
> Nhận main local mới nhất; tạo nhánh `work/w10-quiz-documents` trong `tmp/w10-quiz-documents`.
> Đọc `task/web/W-10-quiz-tai-lieu-thu-vien.md`, `doc/quiz-3-spec.md`, `doc/tai-lieu-3-spec.md`,
> `doc/pha-b2-spec.md` mục4 và spec web/thiết kế. SA-67/68 đã ghép, không chờ Claude cài lại.
>
> Làm từng lát có thể kiểm:
> 1. Quiz từ roadmap/module → đề public → chọn/nộp → kết quả. Gọi QuizUseCase hiện hành, không viết lại sinh/giải mù/chấm ở adapter.
>    Public đề không có correct_index/explanation/why_wrong/validation/đáp án; 4 phương án LLM/LaTeX/Bloom đúng quiz-3,
>    giữ cơ chế fallback của core. Xáo option đúng ánh xạ, nộp nguyên tử/idempotent theo hợp đồng, sai owner trả not_found.
>    Kết quả sau nộp có giải thích/why_wrong của lựa chọn và nguồn đúng trang; ẩn chat trong lúc làm quiz.
> 2. Tạo tài liệu trực tiếp → xem Markdown/LaTeX/nguồn → tải .md. Roadmap chọn tối đa5module,
>    chọn6 phải scope_too_large và0modelcall; lượt thứ11/giờ bị rate_limited theo người xuyên khoá.
>    Giữ origin=button/home_scope/session theo core, nguồn và ngoài-sách có nhãn; dùng renderer/viewer an toàn đã có.
> 3. Thư viện: tái dùng phần chỉ đọc/preview W-09, thêm những phần thiếu. `here/elsewhere` theo `group` do core trả,
>    **không suy nhóm từ origin button/assistant**. Module A tạo tài liệu về B: here ở A và elsewhere ở B.
>    Hai origin đều có thể ở mỗi nhóm. Roadmap theo home_scope=roadmap và bộ lọc all; quiz có điểm sau nộp.
>
> Thiết kế W-10 `0b5993e` chưa được nhận vì sai bộ lọc thư viện; dùng phần trình bày phù hợp spec và nhận bản sửa D-R6-01,
> không cần dừng các lát quiz/tài liệu hoặc chép luật sai từ mẫu. HTML/CSS/token → React; không chờ Cloud Figma.
> Giao diện đẹp/chỉn chu, dùng taste-skill đã nạp khi phù hợp, ghi skill đã áp dụng; giữ Be Vietnam Pro/logo Artboard9–28/token/motion.
>
> Tầng nghiệp vụ sinh/cache/retry/ngân sách nội dung ở core; adapter web giữ quyền, truyền đúng tham số, DTO và giới hạn tần suất web.
> Không gắn cứng cache_only/allow_spend để đổi ý định core, không thêm vòng retry riêng.
> Việc W-10 chỉ dùng fake/replay/PG0USD, không dùng các grant W-15 đã consume để sinh nội dung thật.
>
> Mỗi bất biến có test hành vi RED trên bản sai→GREEN; giữ hồi quy W-09, không giảm assertion/skip.
> Một cổng PostgreSQL toàn repo/lúc qua runner, React/build và browser thật 390/768/1280 sáng/tối/reduced,
> có raw HTTP/SSE/SQL độc lập/ảnh/video/native/commit/sourceSHA. Chốt mốc từng lát, rồi nghiệm thu toàn W-10.
> Core đang nhận backend W-16; web không sửa `learning_usage.py` hoặc GET me/usage trong `api/builds.py` của họ.
> Nếu gateway/app/OpenAPI cần phối hợp, ghi yêu cầu rõ; web sở hữu đăng ký route W-10 và OpenAPI cho tới khi ghép backend W-16.

## 2. Nhóm lõi — W-15 đã nhận, tiếp mốc backend W-16

> W-15 `efed8db` được nhận có ghi chú phạm vi tích hợp/đo số, ghép local `7f54b14`.
> Đã xác minh core retry thật, graph/ảnh/SQL/meter và doc6cache-only. Không chạy lại W-15,
> không tiếp nghiên cứu 81timeout cũ, không tự sửa core/transport hoặc thử burst100 mới.
> Giữ nguyên mọi DB/artifact/PDF/receipt/plan/grant đã consume; không đưa run riêng vào kho chung.
> Giá demo vẫn billing_verified=false, unknown cũ0,4139008USD giữ riêng, không ghi là0 hoặc hoá đơn thật.
>
> Nhận main local cuối. Bắt đầu **mốc backend W-16** ở `work/w16-usage-backend`, `tmp/w16-usage-backend`;
> đọc vé W-16/spec web mục8 và PhaB2mục8. Đây là phân công backend của điều phối, không yêu cầu sửa `src/doc2roadmap/`.
> `GET /api/v1/me/usage`, projection/build quota đã có từ W-14/W-09: **soát và dùng lại**, chỉ bổ sung chỗ thiếu hoặc sai.
>
> 1. Hoàn thiện usage-1 bằng sổ chi/cổng truy vấn hiện có: assistant/document theo người qua mọi khoá,
>    lecture/quiz_gen/quiz_verify theo toàn hệ thống, build tách riêng; counted_in=build không cộng trùng.
>    Ưu tiên usage_rows(learner_id,since,purposes) và quota hiện hành, không tải cả ledger hoặc chép logic DailySpendGuard vào backend.
> 2. Kiểm ngày/tháng Asia/Ho_Chi_Minh: 16:59→17:00UTC reset đúng ngày; biên cuối tháng đúng.
>    Build tháng là số lượt, max=null khi demo tắt; learner_today là ratio/limited/resets_at,
>    shared_content_today chỉ limited. Người thường không thấy khoá usd/cost ở bất kỳ mức JSON nào.
>    Hai khoá/cùng người cộng chung, người khác tách; phân biệt ledger fixture và chi thật.
> 3. Test service/repository/HTTP bằng PG/fake clock, RED trên bản sai→GREEN, kiểm quyền và DTO thật;
>    giữ nguyên callback sinh/cache/retry core và endpoint/chat W-09 đã nhận.
>
> Phạm vi ưu tiên `infrastructure/learning_usage.py`, phần DTO/GET me/usage của `api/builds.py`,
> repository quota nếu test chứng minh cần và `tests/test_usage_w16.py`. Không sửa route W-10/gateway/app/React của web đang làm.
> Không thêm migration nếu schema có sẵn đủ dùng; nếu thật sự cần thì nêu căn cứ/head trước khi cài.
> Giao JSON usage-1 thật cho web, lệnh/native/sourceSHA/báo cáo mốc backend. Web giữ OpenAPI; phối hợp cập nhật sau mốc backend ghép.
>
> Cổng runner PG/React/build theo quy trình một cổng toàn repo/lúc,0USD. Mốc này **không đóng toàn W-16**:
> trang mức dùng và dải React do web làm sau W-10. Không viết frontend tạm hoặc mở thêm vé admin.
> Đề xuất để sẵn sau W-15 là dailybuild5USD và monthly3lượt/người; **chưa bật/chưa được duyệt làm cấu hình**,
> không nhầm monthly là USD hoặc lấy đề xuất thành quyền chi mới.

## 3. Nhóm thiết kế — sửa D-R6-01, đối chiếu React thật theo W-23

> Giữ W-22/W-24 mốc web và ba sửa công thức `aa387f3` đã nhận. Không làm lại thương hiệu/token/math/Cloud Figma.
> Gói mới `0b5993e` chưa ghép. Tiếp `tmp/w24-figma-evidence`, nhánh `work/w24-figma-evidence`, nhận main local cuối.
>
> **D-R6-01:** `w10_quiz_screens.html` đang dùng filterLibrary(button/assistant) cho here/elsewhere.
> Sửa theo PhaB2mục4: `group=here|elsewhere` độc lập origin; UI nhận group đã xác định, không cài thuật toán suy module của core trong prototype.
> Ghi rõ module/phạm vi đang xem; nhãn nguồn tạo bằng nút/trợ lý là thông tin riêng.
> Fixture cần origin chéo với nhóm: assistant tại A→here, button từ roadmap về A→elsewhere; cả hai nguồn tạo đều có thể ở hai nhóm.
> Cập nhật label/filter/data fixture/báo cáo và test hành vi hai tab; thấy đỏ trên bản hiện tại rồi xanh sau sửa.
> Helper phản chứng ở `report/coord-ba-nhom-lan6-evidence-2026-10-25/design-library-repro.cjs` và JSON kết quả.
>
> Giữ các phần quiz-3/document-3 đã đúng: 4option/Bloom/LaTeX/why_wrong sau nộp, không chat lúc làm,
> ≤5module/cảnh báo thu hẹp, xem nguồn/tải Markdown. Mẫu tĩnh không là bằng chứng backend chặn model;
> không thêm lời hứa nghiệp vụ hoặc đổi hợp đồng để khớp mẫu.
>
> Đính chính W-23: báo cáo hiện là soát source React, ảnh script là preview HTML, chưa đủ ghi runtimeReact12cấu hình đạt toàn diện.
> Cùng web lập bảng **ảnh React và mẫu HTML cùng viewport/trạng thái** cho W-08/W-09; dùng nguồn/bằng chứng điều phối
> khi SHA khớp hoặc chạy lại browser với fake/PG0USD. Ghi từng chỗ lệch và cách xử lý; không tự sửa tệp React web đang làm.
> Kiểm390/768/1280, sáng/tối, keyboard/focus/44px, reduced-motion/menu/dialog/source/math;
> video ngắn thao tác thật, nêu rõ font/ngoại mạng có bị chặn không. Sau W-10 React đủ thì soát tiếp, toàn W-23 vẫn mở tới lúc đó.
> Dùng taste-skill đã nạp phù hợp; tiêu chuẩn thương hiệu/spec chủ dự án ưu tiên. Không yêu cầu Cloud/Variables/plugin/Present.

## 4. Luật chung và giao tiếp với Claude

> **Theo quyết định chủ dự án: chỉ commit local, chưa push main/GitHub.** Root luôn main; mỗi vé/worktree một cấp tmp.
> Không tự ghép main, không sửa task/kế hoạch/handoff của điều phối; chỉ commit tệp của vé/bằng chứng.
> Không stash/reset tệp chung, không dọn DB dựng thật/worktree/artifact/snapshot/ZIP/PDF hoặc tạo link; không đụng tmp/t01a-clean-ff797eb.
> Fixture chỉ chép allowlist/SHA, không learner store/livecache/tập giữ lại, không commit .env/PDF/artifact.
> Python luôn qua scripts/w05_run_tests.py, PG bắt buộc, basetemp mới; chỉ một cổng toàn repo/lúc.
> Khi main đổi phải nhận main local và kiểm lại trước trình ghép. Giữ native lỗi trước, không hạ guard để xanh.
> Mọi việc mới của đợt này0USD. Không dùng phê duyệt W-15/khôi phục cũ để chạy lại provider.
> Vertex giữ tới chủ dự án yêu cầu đổi. SA-61 còn nhánh do Claude soát/ghép; SA-67/68 đã ở main, không còn chặn W-10.
> Cửa SA/cổng toàn repo mở lại sau commit hồ sơ local lần6; Claude đọc mục8/10 bàn giao và nhận main local mới.
