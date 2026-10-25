# Lời giao ba nhóm sau nghiệm thu lần 4 — 2026-10-24

[Biên bản và bằng chứng](dieu-phoi-nghiem-thu-ba-nhom-lan4-2026-10-24.md). Chủ dự án có thể chuyển riêng từng phần;
điều phối đã soạn, **chưa gửi phiên nhân viên bên ngoài**. W-08 và mốc W-15 0 USD đã ghép local `bad8e45`.
Không giao lại các phần đã đạt; không dùng cap đề nghị hoặc quyền chi cũ để tự chạy có tiền.

**Quyết định mới của chủ dự án 2026-10-24:** tạm thời chỉ đồng bộ bằng commit local, chưa cần push main.
Đây là quyết định của chủ dự án; ghi vào bàn giao giao tiếp điều phối, không tự tiếp tục push đến khi được yêu cầu.
Nhận `main` local mới nhất khi bắt đầu/ghép vé; điều kiện soát/test/quyền chi vẫn giữ nguyên. Main GitHub chưa chứa mốc local mới.

## Nhóm web — W-08 đạt, chuyển W-09

> W-08 `c8c687b` đã đạt, đóng hai lỗi nhãn tiến độ và lộ đáp án khi stream.
> Cổng kết hợp: 2.602 Python đạt, 0 fail, một Cloudinary skip và một replay xfail có sẵn; 181 React/build xanh.
> Browser PG thật: 12 cấu hình, 109 ảnh/341 HTTP/17 Axe; hai mutation lỗi cũ đều bị bắt.
> Nhận main mới, mở worktree `tmp/w09-assistant`, nhánh `work/w09-assistant` nếu chưa tồn tại; nếu đã có thì nhận main tại worktree đó.
> Không đổi nhánh thư mục chung, không tự ghép main. Giữ worktree W-08 và dữ liệu bằng chứng, không tự dọn.
>
> Đọc `task/web/W-09-tro-ly-va-phien.md`, `doc/tro-ly-3-spec.md` mục 6/8, spec web và ADR0026.
> SA-66 `ba4350f`, SA-69 `973fa99`, SA-70 `5188908` đã ghép: **W-09 không còn chờ lõi**. Không cài trợ lý answer-2 hoặc tự dịch/vá scope ở web.
>
> 1. Đi một lát hoàn chỉnh HTTP/gateway/React cho phiên trợ lý: ownership theo người/cuốn, `client_turn_id` idempotent,
>    history/chuyển/xóa phiên, lỗi/mất kết nối/thu hồi membership; không lộ raw tool args hoặc validation admin.
> 2. Answer-3: `answer_md`, Markdown/LaTeX/sources/delta và trạng thái công cụ theo spec.
>    Thẻ quiz/tài liệu chỉ từ sự kiện `artifact`; `quiz:…` hay URL tự bịa trong chữ không thành link hành động.
>    Kiểm nguồn/Markdown an toàn, không XSS/URL nguy hiểm, không lấy public_id/URL Cloudinary riêng tư đưa ra DTO.
> 3. Gửi focus khái niệm đang mở bài giảng ở mỗi lượt; trang lộ trình không gửi, không kế thừa focus từ phiên.
>    Lõi xử lý ID lạ và focus_ignored. Tool lecture chỉ dùng bài `body_md` đã cache; miss không sinh bài mới/không gọi provider.
> 4. UI `used_ratio/limited/resets_at`, trần chi học theo hợp đồng hiện hành 1 USD/người/ngày, tần suất riêng 10 lượt/phút;
>    không bịa số lượt/ngày. Fake provider/PG độc lập; giữ đúng một nguồn tính chi, không cộng counted_in=build lần hai.
> 5. Dùng mẫu HTML/CSS/token của nhóm thiết kế để chuyển thành React; chọn bản đúng spec và có ghi chú ba lỗi công thức preview đang vá.
>    Cùng soát 390/768/1280 sáng/tối/giảm chuyển động, bàn phím/focus/vùng bấm44px, ảnh và tương tác thật. Không cần Cloud Figma.
>
> Bàn giao commit, lệnh/native/JUnit/SQL/browser và falsifiable guard ở nhánh riêng; cổng qua runner, main mới nhất trước đề nghị ghép.
> Mọi lời gọi nhà cung cấp thật vẫn chặn; không cần chạy lại replay có tiền. Không tự sửa use case Pha B thuộc làn Claude.
> Sau W-09 mới W-10: SA-67 document-3 đã ghép `6cfc535`, SA-68 quiz-3 đã ghép `21cfab3`; đã đủ hai mốc lõi mới.
> Đọc `doc/tai-lieu-3-spec.md` và `doc/quiz-3-spec.md`; vẫn phải kiểm HTTP/React/privacy/submit/library của web trước nhận toàn W-10.

## Nhóm lõi — mốc W-15 0 USD đạt, sửa operator trước xin chi

> Mốc `bf761fe` (5 tệp test/harness, 458 dòng) đã nhận/ghép; không làm lại toàn pipeline fake/PG, hai dry-run hoặc doc-6 cache-miss đã đạt.
> Toàn nhánh `9b3bd82` **chưa được ghép**, toàn W-15 vẫn mở. Tiếp `tmp/w15-real-build`, nhánh `work/w15-real-build`, nhận main mới nhất;
> giữ các commit đã nộp và lịch sử bằng chứng. Đọc biên bản lần4, `core-review/review.md` và summary.
>
> 1. **W15-R4-1 bắt buộc:** `src/web/backend/tests/w15_operator_run.py:88` serialize `str(relative_to(...))` thành đường dẫn Windows có dấu `\`,
>    nhưng execute dòng122 dùng safe_path từ chối dấu này. Hai plan thật đã lưu đều tái hiện `ValueError: Path escapes its root`.
>    Sửa portable path ở nơi ghi plan, giữ safe_path nghiêm. Test hiện tại tự `.as_posix()` nên không chứng minh prepare thật.
>    Thêm ca thực sự đi prepare→JSON đã lưu→execute validation/composition bằng fake; ghi RED trên hành vi cũ, GREEN sau sửa,
>    kiểm đường dẫn thoát root vẫn bị bắt. Không sửa tay plan làm thay đổi quyền chạy đã chuẩn bị.
> 2. **W15-R4-P1 trước duyệt profile/có tiền:** xác minh SKU online Vertex gemini-embedding-001 dùng đơn vị gì và metadata nào.
>    Đối chiếu reserve/actual-cost với nguồn Google chính thức, phân biệt batch và online, token và billable_character_count.
>    Chưa có kết luận tính thiếu tiền. Nếu chưa chốt được profile thì giữ từ chối chạy, không tự chọn cách tính thuận lợi.
>    Nguồn đã đọc ở `report/coord-ba-nhom-lan4-evidence-2026-10-24/core-review/embedding-pricing-primary-check.md`.
> 3. Giữ mặc định web `allow_spend=False`, approval chỉ operator tin cậy, đúng PDF SHA/u-hash/pipeline/profile/lượt/trần,
>    consume một lần và không retry có tiền ngầm. Meter delta là chi build duy nhất; counted_in=build chỉ trace, không mở purpose dựng vào DailySpendGuard học.
> 4. Cập nhật đề nghị bootstrap doc-6 trần1USD và cuốn52trang trần3USD sau khi hai mục trên đạt; **đó mới là đề nghị, chưa duyệt**.
>    Tách cache/hit/miss/unknown, số gọi/embedding/USD/phút từng bước đã đo và chưa đo. Cap không phải dự toán.
>    Chỉ chủ dự án gửi duyệt mới được chạy đúng lượt đã soát, trích nguyên tin duyệt vào báo cáo và ghi chi thật vào mục10 bàn giao qua điều phối.
>
> Doc-6 cache-only thật hiện dừng label-roles/SpendNotAllowed với0USD; không ghi đã ready/course/mail hoặc dựng xong miễn phí.
> Worktree kiểm mới cần chép fixture sáu cuốn qua helper và **bản PDF train candidate riêng** theo `report/w15-evidence/candidate.json`,
> đối chiếu SHA/ordinary copy; snapshot sáu cuốn không chứa nó. Không commit PDF, không trỏ vào artifact dùng chung.
> Chạy cổng bắt buộc và giữ kết quả trước/sau; mọi việc được giao hiện tại0USD. Không tự ghép main.

## Nhóm thiết kế — giữ mốc web đã nhận, vá công thức và hỗ trợ W-09/W-23

> W-22/W-24 **đạt có ghi chú trong phạm vi thiết kế web đã kiểm theo quyết định chủ dự án**. Không cần Cloud Figma,
> Variables export/native component/binding/reaction/Present; không làm lại bộ token, layout, thương hiệu hoặc usage/chat đã đạt.
> Đã xác nhận bản mới sửa nhân vật96px/retry/lỗi đuôi/hai anchor/guard VM. Toàn nhánh `eb29f29` chưa ghép do ba lỗi mới ở HTML công thức.
> Tiếp `tmp/w24-figma-evidence`, nhánh `work/w24-figma-evidence`, nhận main mới nhất; không sửa các tệp React mà web đang làm.
>
> 1. **D-R4-01:** W09 `w09_chat_screens.html:254` có markup giống KaTeX nhưng thiếu CSS toán/chỉ số dưới;
>    browser đo subscript cùng y/font/baseline, hình công thức sai. Dùng renderer/output/CSS đúng hoặc markup toán phù hợp.
> 2. **D-R4-02:** công thức W08/W09 aria-hidden, không MathML/nhãn tương đương; cây truy cập mất biểu thức.
>    Bổ sung biểu diễn truy cập thực, kiểm accessibility snapshot có nội dung toán, không chỉ kiểm chuỗi class trong HTML.
> 3. **D-R4-03:** inline span W08 dòng272 thiếu thẻ đóng, lồng công thức khối và văn xuôi sau vào .katex,
>    làm văn xuôi nhận font toán. Sửa cấu trúc, kiểm DOM không nested formula ngoài ý muốn và đoạn văn giữ font chính.
>
> Ảnh/DOM/test tại `report/coord-ba-nhom-lan4-evidence-2026-10-24/design-browser/` và `design-review/`.
> Kiểm 390/768/1280 sáng/tối/reduced-motion, nội dung đọc đúng và truy cập được; guard phải bắt được bản sai thực.
> Có thể đổi câu lỗi đuôi sang “phần đã nhận vẫn hiện trên màn hình” để tránh hứa cache bền; không phát sinh kiến trúc cache.
> Đây là sửa giới hạn bản preview mới để dùng tiếp, không thu hồi mốc thiết kế web đã được chủ dự án nhận.
>
> Sau đó giao HTML/CSS/token cùng ghi chú trạng thái cho web cài W-09; cùng soát React W-08 ở W-23 ngay,
> ghi lỗi thị giác/hiệu ứng và ảnh trước/sau, không tự sửa tệp web đang dùng. W-23 nhận từng màn;
> toàn vé chỉ đóng khi đủ W-08/W-09/W-10 theo spec, không chờ Cloud.
> Logo Artboard9–28, Be Vietnam Pro, token/motion và taste-skill đã nạp được dùng; không bịa nghiệp vụ hoặc lời hứa dữ liệu.

## Luật chung và liên lạc Claude

> Root luôn main, mỗi vé/worktree đúng một cấp tmp/<tên>; commit đúng tệp vé, không tự sửa task/kế hoạch/handoff hoặc tự ghép.
> Không xóa/dọn worktree/snapshot/ZIP/artifact, không junction/symlink/hardlink và không đụng tmp/t01a-clean-ff797eb,
> live cache dùng chung/tập giữ lại. Dữ liệu chỉ chép allowlist/SHA, không commit .env/PDF/artifact.
> Python luôn qua scripts/w05_run_tests.py; focused unit-only cần nạp backend conftest định nghĩa --require-postgres.
> Một cổng PostgreSQL toàn repo tại một thời điểm; main đổi phải nhận main/chạy lại trước ghép, không giảm assertion/skip/guard/timeout để xanh.
> Giữ Vertex đến khi chủ dự án yêu cầu đổi; SA-61 chưa coi là đã ghép/chuyển chỉ vì có so sánh tốc độ.
> Claude tiếp làn SA/SA-61; SA-67 document-3 và SA-68 quiz-3 đã nhận. Cửa SA/cổng toàn repo được mở lại sau khi hồ sơ lần4 được commit local.
> Mọi việc hiện được giao0USD; chưa có phê duyệt paid W-15. Chủ dự án chuyển lời giao từng nhóm khi muốn, điều phối chưa gửi ra ngoài.
