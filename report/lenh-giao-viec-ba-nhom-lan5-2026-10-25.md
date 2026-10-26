# Lời giao ba nhóm sau nghiệm thu lần 5 — 2026-10-25

[Biên bản/bằng chứng](dieu-phoi-nghiem-thu-ba-nhom-lan5-2026-10-25.md). Chủ dự án có thể chuyển riêng từng phần;
điều phối chưa gửi phiên nhân viên bên ngoài. Chỉ commit local, **không push main**, theo quyết định chủ dự án 24/10.
Mốc lõi `fb0c769` và thiết kế `aa387f3` đã ghép local `9028db2`; W-09 chưa đạt/chưa ghép.

## Nhóm web — sửa hai lỗi W-09 trước, rồi W-10

> Tiếp `tmp/w09-assistant`, nhánh `work/w09-assistant`, mốc nộp `da4d639`. Nhận main local mới nhất có lõi/thiết kế đã ghép,
> không tự ghép main. Các phần quyền/DTO/session/idempotency/usage/Markdown/artifact/responsive đã kiểm tốt không giao làm lại.
> Điều phối đã chạy198 React/build, browser 99 ảnh/43 Axe/12 cấu hình; cổng xanh không thay cho hai phản chứng sau:
>
> 1. **R-W09-1 — mất câu hỏi:** final thành công làm `setLive(null)` nên composer mở, nhưng `active.current` còn chờ
>    EOF và `GET /me/usage`. Gửi câu tiếp trong lúc usage chậm: `Assistant.tsx` xoá draft, `run()` return vì active còn giữ,
>    không có POST thứ hai. Helper React thật có1 assertion fail/0 setup; quan sát draft rỗng và POST count 1.
>    Sửa ranh giới kết thúc lượt/UI nhất quán: gửi được câu tiếp hoặc giữ draft/chờ rõ; không để mất câu.
>    Thêm ca final xong, usage pending, người dùng gửi câu nữa; giữ replay/retry cùng client_turn_id, history chậm và lỗi mạng.
>    Kiểm thêm phản hồi usage/finally cũ về khi câu thứ hai đang stream: không được xoá hoặc mở khoá sai lượt mới.
> 2. **R-W09-2 — tool bài giảng thường:** `learning_runtime.py:54–57` luôn ép cache_only True và bỏ allow_spend,
>    làm tool get_lecture trên bài chưa cache trả not_cached/rỗng. Chuyển kwargs xuống như composition_phase_b.py hiện hành,
>    theo task W-09 mục cập nhật 23/10. **Focus prefetch vẫn cache-only, miss 0 lần sinh**; tool thường theo cờ được gọi và trần lõi,
>    không sửa core hoặc tự mở trần. Kiểm riêng thường mặc định, cache_only True/False, focus hit/miss và owner/allow_spend.
>
> Counterexample source/README/config/XML và ZIP ở `report/coord-ba-nhom-lan5-evidence-2026-10-25/web-review/`.
> Mỗi hồi quy phải RED trên hành vi cũ rồi GREEN sau sửa, không giảm assertion/skip/timeout. Giữ log setup failed lịch sử,
> không tính chúng làm phản chứng chức năng. Giữ mutation receipts đúng phiên nguồn, không gán 19 mutant cũ là đã chạy trên HEAD mới.
> Sau sửa nhận main local mới, cổng runner PostgreSQL/React/build và browser mới, ghi commit/lệnh/native/SQL/SHA.
>
> Sau W-09 đạt mới W-10. SA-67 document-3 `6cfc535` và SA-68 quiz-3 `21cfab3` đã ghép; đủ hai lõi, không chờ Claude triển khai nữa.
> Đọc spec `doc/tai-lieu-3-spec.md`, `doc/quiz-3-spec.md` trước cài: sinh quiz/submit/chấm, sinh/xem tài liệu trực tiếp,
> thư viện lọc theo nơi tạo. Phần library chỉ đọc/preview ở W-09 được tái dùng, không làm lại hoặc coi nó thay toàn W-10.
> Kiểm ẩn đáp án trước nộp, xáo phương án đúng, nộp nguyên tử/đúng owner, source/Markdown an toàn, đúng phạm vi,
> trần/tần suất, không lộ validation/privateIDs. Dùng giả/PG 0 USD, không chạy lại replay có tiền.
> Tham khảo HTML/CSS/token mới thiết kế đã ghép, chuyển thành React và cùng thiết kế soát; không chờ Cloud Figma.

## Nhóm lõi — mốc operator/profile đã nhận; chuẩn bị lượt cụ thể từ main mới

> `fb0c769` đã soát đạt mốc operator/profile demo, ghép local `9028db2`; lỗi Windows W15-R4-1 đã đóng,
> không làm lại serializer/test prepare→JSON→execute, port PG hoặc toàn pipeline fake đã nhận. **Toàn W-15 vẫn mở**.
> Tiếp `tmp/w15-real-build`, nhánh `work/w15-real-build`, nhận main local cuối sau hồ sơ điều phối.
>
> 1. HEAD ảnh hưởng pipeline_version, nên các plan ở `fb0c769` **không còn dùng để chạy ở main mới**.
>    Chuẩn bị lại doc-6 và candidate ở đúng HEAD/config sẽ chạy, có guard provider/ADC/mạng và dry-run 0 USD.
>    DB/artifact riêng, PDF được đối chiếu SHA độc lập, đường dẫn portable, `approved=false`.
>    Không sửa tay plan cũ/version/hash hoặc tái dùng reference cũ. Lưu plan trong local tmp có hash;
>    giữ HEAD ổn định giữa prepare/duyệt/execute. Nếu commit báo cáo làm đổi HEAD trước execute thì phải chuẩn bị lại.
> 2. Đề nghị để chủ dự án xem gồm book/SHA/HEAD/pipeline/profile/database/đường dẫn và SHA của plan/reference/lượt/trần.
>    Giữ đề nghị bootstrap doc-6 tối đa 1 USD và một cuốn 52 trang tối đa 3 USD; tổng 4 USD **chưa được duyệt**.
>    Bảng từng bước ghi cache hit/miss/unknown, số gọi sinh/embedding/USD/phút và thời gian chờ embedding đã đo hoặc chưa đo.
>    Trần đề nghị không phải dự toán hoặc cam kết dựng xong.
> 3. Giữ giá giả định demo `owner-demo-embedding-token-20261025`, 0,15 USD/triệu input token embedding theo chỉ thị đã trích.
>    Mọi audit/plan/grant giữ `embedding_billing_verified=false`; không ghi giá online Google đã xác minh hoặc hóa đơn đã đối soát.
>    Chỉ thị chọn giá lý thuyết không là phê duyệt trả tiền cho PDF cụ thể hoặc hứa tăng trần.
> 4. **Chờ tin chủ dự án duyệt đúng lượt trước execute**. Chưa duyệt thì chỉ chuẩn bị/kiểm fake/tài liệu 0 USD;
>    không bootstrap, tự retry trả phí, nâng trần hoặc dùng phê duyệt phục hồi/SA cũ. Có duyệt thì trích nguyên tin vào báo cáo,
>    dùng đúng grant consume một lần, giữ meter delta là chi build duy nhất, `counted_in=build` chỉ trace.
>
> Sau lượt thật cần số graph/module/concept/edge, ảnh/công thức/roadmap, đúng identity/version/cache,
> usage known/unknown/trần/thời gian chờ embedding và course-ready/mail/SQL độc lập. Web doc-6 cache-only sau bootstrap phải chặn provider;
> không đổi alias/version/roles để ép reuse. Dừng vì usage unknown hoặc chạm trần thì giữ receipt và xin quyết định mới.
> Không nhận fake/parse/dry-run hoặc label-roles cache miss thành cuốn thật đã dựng xong. Artifact Pha A/ảnh vẫn là tệp,
> không chuyển vào DB. Giữ Vertex; thiếu/sai profile/grant vẫn từ chối trước consume/dispatch.

## Nhóm thiết kế — đóng lỗi công thức, phối hợp W-23 và mẫu W-10

> `aa387f3` đã soát đạt và ghép local `9028db2`: đóng D-R4-01/02/03. Có 58 test đạt,
> bốn guard với HTML cũ đều đỏ; browser 12 cấu hình/24 trang, subscript 15,4→11,55 px/vị trí đúng,
> 36 snapshot toán có nội dung, không lồng katex/tràn ngang. Không giao làm lại công thức/token/layout/plugin.
> W-22/W-24 giữ đạt có ghi chú trong phạm vi thiết kế web; **không cần Cloud Figma**.
>
> Tiếp worktree riêng `tmp/w24-figma-evidence`, nhận main local mới; cùng web soát React W-08 theo W-23 ngay,
> W-09 sau hai bản sửa chức năng. Chỉ ghi lỗi thị giác/hiệu ứng/thao tác mới và ảnh đối chiếu, không tự sửa tệp React web đang làm.
> Dùng 390/768/1280, sáng/tối, reduced-motion, bàn phím/focus/vùng bấm 44 px, công thức/nguồn/cỡ chữ/trạng thái lỗi.
> Giữ phép đo browser về subscript/accessibility/DOM để bảo vệ công thức sau này: unit CSS hiện có nhánh OR còn quá dễ xanh.
>
> Chuẩn bị/giao mẫu HTML/CSS/token W-10 đúng quiz-3/document-3 hiện hành: quiz đang làm ẩn chat, kết quả sau nộp,
> tạo tài liệu theo yêu cầu/chọn ≤5 module, xem nguồn và thư viện Tạo ở đây/Tạo ở nơi khác.
> Preview hiện có chỉ cập nhật phần lệch spec, không thiết kế lại từ đầu. Ghi rõ mẫu nào đã nhận và mẫu nào đang chuẩn bị.
> Sau web chuyển React, hai nhóm cùng soát màn chạy thật; W-23 nhận từng màn, toàn vé chờ W-09/W-10 xong.
> Logo Artboard 9–28, Be Vietnam Pro, token/motion và taste-skill đã nạp giữ theo spec; không bịa nghiệp vụ hoặc lời hứa dữ liệu.

## Luật chung và giao tiếp điều phối

> **Quyết định chủ dự án 24/10 tiếp tục hiệu lực: chỉ commit local, chưa push main; chỉ đẩy khi chủ dự án yêu cầu.**
> Root luôn main, mỗi vé/worktree một cấp tmp; commit đúng tệp của vé, không tự sửa task/kế hoạch/handoff hoặc ghép main.
> Giữ mọi worktree/artifact/snapshot/ZIP/PDF, không dọn hoặc tạo junction/symlink/hardlink, không đụng tmp/t01a-clean-ff797eb,
> live cache chung/tập giữ lại. Dữ liệu chỉ chép allowlist/SHA, không commit .env/PDF/artifact.
> Python luôn qua scripts/w05_run_tests.py, PG bắt buộc; một cổng toàn repo một lúc, main đổi thì nhận main/kiểm lại trước ghép.
> Giữ Vertex tới khi chủ dự án yêu cầu đổi; SA-61 còn nhánh, không coi đã ghép. Claude giữ làn SA/soát ghép SA.
> Cửa SA/cổng toàn repo mở lại sau commit local hồ sơ lần 5; mọi việc được giao hiện 0 USD, paid W-15 cần duyệt chính xác riêng.
