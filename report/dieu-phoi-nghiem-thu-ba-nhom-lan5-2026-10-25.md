# Nghiệm thu ba nhóm lần 5 và kế hoạch tiếp — 2026-10-25

## 1. Kết luận

| Nhóm | Mốc nhận | Phán xét | Việc tiếp |
|---|---|---|---|
| Web | `da4d6399965f5a67accaacc6ea34af8ce56f0dd5` | **Chưa nhận toàn W-09, chưa ghép**: hai Required tái hiện độc lập | Sửa mất câu hỏi sau final và chuyển đúng cache_only cho công cụ bài giảng; rồi mới W-10 |
| Lõi | `fb0c769ad146d1aa6a5b2b2e1648a12a359ad194` | **Nhận mốc sửa operator/profile demo**, đã ghép local `9028db2`; toàn W-15 vẫn mở | Chuẩn bị quyết định chạy thật đúng plan/SHA/lượt/trần; chưa có quyền chi từ lượt nghiệm thu này |
| Thiết kế | `aa387f33542250b08487c2dd1ce105abc68fd9ed` | **Đóng cả ba lỗi công thức R4**, nhận gói web và ghép local `9028db2` | Hỗ trợ sửa W-09, đối chiếu React W-08 theo W-23, chuẩn bị W-10 theo hợp đồng mới |

Chỉ commit local theo quyết định chủ dự án 24/10; **không push main**. Không yêu cầu Cloud Figma.
Mốc W-08 đã đạt giữ nguyên; không nhận lỗi W-09 thành lỗi của toàn nền web. Không tự sửa mã sản phẩm thay nhân viên.

Main nền `46d829a`, cửa kiểm local `d8d5659`. Đỉnh kết hợp ba nhóm `31d14b573a8d9852bfd0aa5d5185753a99a05ecc`
được kiểm để phát hiện tương tác; sau khi tái hiện hai Required W-09, tách đỉnh **`8bb746fd39b3bdef490ea6cc67d0f4758fb40891`**
chỉ gồm lõi/thiết kế và main mới nhất để chạy cổng riêng trước ghép. Cổng xanh chung không thay phán xét chức năng.
Không sửa, stash/reset, dọn hoặc đổi nhánh các worktree nhân viên; không thay hai nhánh bằng cherry-pick viết lại lịch sử.

## 2. Cổng và bằng chứng độc lập

| Kiểm | Kết quả | Bằng chứng |
|---|---|---|
| Python toàn repo trên ba nhóm `31d14b5` | **2.696 đạt / 0 fail / 0 error / 1 skip / 1 xfail**. native 0 | [JUnit](coord-ba-nhom-lan5-evidence-2026-10-25/runs/full.xml), [native/cwd/commit](coord-ba-nhom-lan5-evidence-2026-10-25/runs/full-exit.json) |
| React/build trên ba nhóm | **198 đạt**, build native 0 | [JUnit](coord-ba-nhom-lan5-evidence-2026-10-25/runs/react.xml), [build](coord-ba-nhom-lan5-evidence-2026-10-25/runs/build-exit.json) |
| Browser W-09 HTTP/PostgreSQL/AssistantUseCase thật; model/media/mail giả | **12 cấu hình / 99 ảnh / 43 Axe / 371 bản ghi HTTP/SSE kể cả tee**, native 0; 0 page error | [audit](coord-ba-nhom-lan5-evidence-2026-10-25/browser/audit.json), [runtime/SQL](coord-ba-nhom-lan5-evidence-2026-10-25/browser/runtime.json) |
| Phản chứng W-09 mất câu hỏi sau final | **1 assertion fail / 0 setup error**, câu thứ hai bị xoá draft nhưng không POST | [JUnit](coord-ba-nhom-lan5-evidence-2026-10-25/web-review/final-usage-race-red2.xml), [helper](coord-ba-nhom-lan5-evidence-2026-10-25/web-review/Assistant.final-usage-race.test.tsx) |
| Phản chứng W-09 công cụ đọc bài thông thường | Actual cache-only miss/0 fake call; control chuyển đúng cờ ready/1 fake call | [soát web](coord-ba-nhom-lan5-evidence-2026-10-25/web-review/review.md) |
| Mutation React guard đã có | **2/2 bản sai bị bắt**, retry đổi mã và link tự bịa; SHA phục hồi, không setup error | [kết quả](coord-ba-nhom-lan5-evidence-2026-10-25/mutations/results.json) |
| Thiết kế focused/đối chứng HTML cũ | **58 đạt**; bốn guard mới với HTML cũ `eb29f29` có **4 fail** rồi phục hồi byte | [soát thiết kế](coord-ba-nhom-lan5-evidence-2026-10-25/design-review/summary.json) |
| Thiết kế browser công thức | **12 cấu hình/24 trang**, 390/768/1280 × sáng/tối × normal/reduced, 36 snapshot toán có nội dung, không tràn ngang | [DOM/cây truy cập](coord-ba-nhom-lan5-evidence-2026-10-25/design-browser/observations.json) |
| Lõi Windows/profile, probe offline | Serializer cũ bị từ chối, serializer mới tới composition; bốn đường dẫn thoát root bị bắt; thiếu/sai profile không consume hoặc dispatch | [soát lõi](coord-ba-nhom-lan5-evidence-2026-10-25/core-review/review.md) |
| Python toàn repo trên đúng đỉnh ghép lõi/thiết kế `8bb746f` | **2.676 đạt / 0 fail / 1 skip Cloudinary live / 1 xfail replay SA-55 có sẵn**, native 0 | [JUnit](coord-ba-nhom-lan5-evidence-2026-10-25/runs/safe-full.xml), [native](coord-ba-nhom-lan5-evidence-2026-10-25/runs/safe-full-exit.json) |
| React/build trên đúng đỉnh ghép | **181 đạt**, build native 0 | [JUnit](coord-ba-nhom-lan5-evidence-2026-10-25/runs/safe-react.xml), [build](coord-ba-nhom-lan5-evidence-2026-10-25/runs/safe-build-exit.json) |

Một cổng PG toàn repo tại một thời điểm, Python luôn qua `scripts/w05_run_tests.py`, basetemp riêng.
Giữ native/lệnh/cwd/commit và mọi lượt lỗi trước, không giảm assertion/guard hoặc nâng timeout để ép xanh.
Browser có 91 console error đã phân loại: 43 probe font và 43 probe style của Axe bị CSP chặn,2 lần 401 trước đăng nhập,
3 lần 404 sau thu hồi quyền; không nới CSP. 23 finding contrast incomplete có đo màu/vị trí thực đạt ngưỡng.
Không có page error/tràn ngang/vùng bấm sai; 371 bản ghi HTTP có tee SSE, không coi là 371 request độc nhất.
[Phân loại độc lập](coord-ba-nhom-lan5-evidence-2026-10-25/browser-independent.json).
Browser fake không chứng minh chất lượng/độ trễ LLM thật; ConsoleMailer/LocalImageMedia không là kiểm SMTP/Cloudinary production.
Đã kiểm độc lập UUID DB browser được gỡ, producer dừng và cổng 8019 không nghe:
[kiểm sau chạy](coord-ba-nhom-lan5-evidence-2026-10-25/runtime-cleanup.json).

## 3. W-09 — hai Required trước nghiệm thu

**R-W09-1: mất câu hỏi tiếp theo khi refresh mức dùng chậm.** `useAssistant.ts` nhận final thành công thì thêm câu trả lời và `setLive(null)`;
khung nhập đã hết trạng thái busy. Nhưng `active.current` còn giữ tới khi stream hết và `GET /me/usage` hoàn tất.
Người học nhập/gửi câu thứ hai trong khoảng này: `Assistant.tsx` xoá draft, `run()` thấy active còn tồn tại và return, không gửi câu hỏi.
Phản chứng React thật/fetch giả xác nhận chỉ có POST câu đầu, usage đang pending, draft câu hai rỗng.
Lượt repro đầu chỉ lỗi resolve React ở scratch được giữ riêng, **không** tính làm bằng chứng chức năng.

Sửa ranh giới kết thúc lượt cho UI và bộ điều khiển nhất quán: câu tiếp theo phải được gửi hoặc giữ nguyên draft kèm trạng thái chờ rõ.
Không xoá câu mà không nhận xử lý, không dựa vào thời gian mạng thường nhanh. Thêm test final đã hiện + usage chưa resolve + gửi câu tiếp,
giữ cả mất kết nối/thử lại cùng client_turn_id/lịch sử chậm. Phản hồi usage/finally của lượt cũ không được tác động sai lượt mới đang stream.
Ghi RED→GREEN trên hành vi thực, không giảm assertion.

**R-W09-2: ép công cụ `get_lecture` thông thường thành cache-only.** Wrapper `WebLearningRuntime.assistant` luôn truyền `cache_only=True`,
bỏ giá trị do lõi gửi; khác `composition_phase_b.py` chuyển `kwargs.get('cache_only', False)`.
Đọc focus phải cache-only để không sinh bài ngầm, nhưng công cụ thông thường cần giữ đúng cờ được gọi theo hợp đồng.
Test độc lập bằng graph/store/model fake: tool thường trên bài chưa cache trả not_cached/rỗng, 0 lần sinh;
control chuyển đúng cờ trả ready và đúng1 fake call. Nguồn yêu cầu rõ ở vé W-09 phần cập nhật 23/10 và composition lõi hiện hành.
Chuyển `cache_only` đúng chữ ký, giữ owner/allow_spend/ngân sách theo lõi; kiểm riêng focus hit/miss **0 sinh** và tool thường theo mặc định/cờ tường minh.
Không sửa use case Pha B hoặc tự mở trần chi để vá wrapper.

Các phần đã có giá trị được ghi nhận, không giao làm lại: quyền người/cuốn, phạm vi máy chủ chọn, mutex PG,
idempotency, DTO riêng tư, artifact từ bản ghi ready, giữ tài liệu khi xoá phiên, hạn chi/tần suất, renderer Markdown/KaTeX và responsive.
Một phần thư viện chỉ đọc phục vụ chứng minh W-09 không thay cho sinh/submit/chấm/thư viện đầy đủ của W-10.
198 React xanh vẫn chưa kiểm hai phản chứng bên trên. [Review nguồn/hồ sơ](coord-ba-nhom-lan5-evidence-2026-10-25/web-review/review.md).
Đã đối chiếu238 hash bằng chứng,22 tệp nguồn,31 bản teeSSE; nhận bộ UI mới198test/99 ảnh thay các số192/71ở phần báo cáo cũ.
19 mutation lịch sử có native/assertion, nhưng chỉ2 raw SHA khớp HEAD hiện tại; không nhận chúng là19phép phá trên đúng mã mới nhất.
Điều phối chạy lại hai helper độc lập: React1assertionfail/0 error và Python AssertionError sau control dương;
[native React](coord-ba-nhom-lan5-evidence-2026-10-25/runs/question-repro-exit.json),
[control Python](coord-ba-nhom-lan5-evidence-2026-10-25/runs/lecture-repro.log).
Đã xem [desktop sáng](coord-ba-nhom-lan5-evidence-2026-10-25/browser/answered-1280-light.png) và
[mobile tối/reduced](coord-ba-nhom-lan5-evidence-2026-10-25/browser/answered-390-dark-reduced.png):
khung nhập/phiên/công thức đọc rõ, mobile dùng dialog toàn màn. Phán xét thị giác không thay hai điều kiện chức năng.

## 4. W-15 — nhận sửa operator và profile demo, không cấp quyền chi

**Đóng W15-R4-1:** `prepare` ghi `run_dir.relative_to(ROOT).as_posix()`; không nới `safe_path` hoặc sửa tay plan cũ.
Ca `test_prepare_saved_plan_roundtrips_to_execute_composition_and_rejects_escape` đi prepare → JSON trên đĩa → execute tới sentinel composition,
kiểm JSON nguyên byte và bốn dạng đường dẫn xấu. RED cũ đúng Path escapes its root/0 setup, GREEN mới đúng test đó.
Probe độc lập compile serializer cũ trong bộ nhớ, không sửa nguồn nhân viên hoặc chạy paid; xác nhận bản cũ đỏ và control mới xanh.

**Giữ rõ giá giả định demo theo chỉ thị được nhân viên lõi trích tại báo cáo ngày25/10:**

> bạn chốt 1 con số lý thuyết đi, và nói là chủ dự án cho, vì đây là 1 sản phẩm demo nên tính kĩ ko quan trọng, trước sau gì chủ dự án cũng nâng trần lên cao thôi

Nguồn trích là `report/w15-sua-operator-lan4-2026-10-25.md`, không phải một lượt duyệt PDF/trần của phiên điều phối.
Nhận **profile opt-in `owner-demo-embedding-token-20261025`**, giá tính thử0,15USD/triệu input token; mọi plan/grant/audit
giữ `embedding_billing_verified=false`. **Không kết luận SKU online Google đã xác minh** hoặc đây là trần hóa đơn đã đối soát.
Chỉ thị chọn giá lý thuyết không tự cấp quyền chạy1 USD/3 USD, không lấy khả năng tăng trần trong tương lai làm quyền chi hiện tại.

Thiếu/sai profile từ chối trước consume/khởi tạo paid pipeline; web mặc định `allow_spend=False`.
Approval phải khớp SHA/u-hash/pipeline/database/profile/reference/trần, consume một lần trong PG.
Usage chỉ có ký tự nhưng thiếu token vẫn unknown và chặn lời gọi tiếp; meter delta là chi build duy nhất,
`counted_in=build` không cộng lại. Hook chỉ dành process operator riêng, không nhận đây là hàng đợi bền/khôi phục sau kill.
Soát độc lập22entry SHA/kích thước,23 hash nguồn và cổng tác giả2641/39focused/181 React, bốn mutation đã lưu;
probe offline độc lập không gọi DB/provider/ADC. Cổng điều phối là mục2, không nhận số tác giả thay kiểm mới.

Nhân viên đã chuẩn bị lại hai plan HEAD bàn giao, `approved=false`, PDF có SHA, DB/artifact riêng; **chưa execute có tiền**.
Sau ghép/commit, HEAD dùng trong pipeline_version đã đổi: hai plan đó chỉ còn bằng chứng chuẩn bị ở `fb0c769`.
Nhóm lõi phải nhận main local cuối, tạo plan mới ở đúng HEAD sẽ chạy, giữ nguyên plan cũ; không sửa tay version hoặc dùng plan cũ xin duyệt.
Đề nghị còn nguyên: bootstrap doc-6 tối đa 1 USD, candidate52trang tối đa 3 USD; tổng 4 USD chỉ là đề nghị.
Số gọi/chi/phút bước downstream chưa đo giữ chưa biết; cap không là dự toán hoặc cam kết dựng xong.
**Toàn W-15 còn mở**, chờ chủ dự án quyết định đúng plan/lượt/trần rồi kiểm graph/ảnh/course-ready/mail/usage thật,
không nhận dry-run/fake hoặc cache miss label-roles của doc-6 thành dựng thật thành công.

## 5. Thiết kế — đóng ba lỗi công thức, tiếp phối hợp React

- **D-R4-01 đóng:** chỉ số dưới W-09 đo font 11,55 px dưới chữ chính 15,4 px và có y thấp hơn, đủ cả 12 cấu hình.
- **D-R4-02 đóng:** ba công thức có role math/aria-label/MathML đúng nội dung;36 snapshot thật có biểu thức, không bị tổ tiên ẩn.
- **D-R4-03 đóng:** W-08 không còn công thức lồng ngoài ý muốn; đoạn văn sau ở ngoài nút toán, giữ font chính.

Đã xem [chat desktop](coord-ba-nhom-lan5-evidence-2026-10-25/design-browser/w09-active-1280.png) và
[lecture mobile](coord-ba-nhom-lan5-evidence-2026-10-25/design-browser/w08-ready-390.png). Giữ mốc web đã nhận có ghi chú,
không mở lại Cloud/Variables/native components/Present. Cả nhánh có85 đường dẫn,14 tệp ngoài report, **không đổi src/** hoặc auth hiện tại.
Các trang chưa triển khai nghiệp vụ vẫn chỉ là preview; không nhận preview tĩnh thành tính năng React đã xong.

Optional: unit guard CSS có nhánh OR chỉ cần class `.katex` nên có thể bỏ layout `.msub/.vlist` mà test vẫn xanh;
phép đo font/y trình duyệt của điều phối đã kiểm độc lập hành vi. Nên giữ phép đo này cho thay đổi công thức sau, không chặn gói đã chạy đúng.
[Review](coord-ba-nhom-lan5-evidence-2026-10-25/design-review/review.md).

## 6. Kế hoạch tiếp và bàn giao

[Lời giao đủ ba nhóm](lenh-giao-viec-ba-nhom-lan5-2026-10-25.md), chưa gửi ra phiên bên ngoài.

| Nhóm | Ưu tiên | Điều kiện xong |
|---|---|---|
| Web | Sửa R-W09-1/2 trên nhánh hiện tại; sau đạt mới W-10 | Hai ca đỏ thành xanh, giữ kiểm focus/tool thường, nhận main local có lõi/thiết kế, cổng/browser xanh rồi trình nghiệm thu |
| Lõi | Nhận main local cuối rồi chuẩn bị hai plan mới 0 USD, trình thông tin đúng lượt/trần | Pipeline_version/HEAD/SHA/database/profile/ref khớp, không sửa plan cũ; chỉ execute khi chủ dự án duyệt rõ |
| Thiết kế | Soát React W-08/W-09 cùng web theo W-23; chuẩn bị mẫu W-10 phù hợp quiz-3/document-3 | Ảnh/interaction thực ở 390/768/1280 sáng/tối/reduced, chỉ giao lỗi mới, không làm lại thương hiệu/token/Cloud |
| Claude/Pha B | SA-61 còn ở nhánh, không coi đã ghép; các vé SA do Claude soát/ghép | Giữ Vertex tới chủ dự án yêu cầu đổi; SA-67/68 đã ở main, W-10 không còn chờ hai lõi này |

Không giao web đi tiếp W-10 bằng cách bỏ hai lỗi W-09. W-16 đã có phần usage-1 ở W-09 nhưng chưa có trang mức dùng đầy đủ;
W-23 chỉ nhận từng màn đã chạy, toàn vé chờ đủ W-09/W-10. Chưa triển khai production hoặc đổi transport trong lượt này.

Đã chép thường3144tệp fixture sáu cuốn và candidate PDF riêng, SHA khớp; không link, không learner store,
không đọc cache live dùng chung/tập giữ lại, không dọn worktree/snapshot/ZIP/artifact hay đụng tmp/t01a-clean-ff797eb.
Sáu tệp dở root của phiên khác giữ nguyên SHA. **Chi nhà cung cấp mới 0 USD**, không push main theo quyết định chủ dự án.
[Manifest bằng chứng](coord-ba-nhom-lan5-evidence-2026-10-25/manifest.json); raw ảnh/video đầy đủ giữ local có hash.
Sau commit hồ sơ local, mở lại cửa SA/cổng toàn repo cho Claude. Nhận main local mới nhất/chạy lại cổng nếu main đổi trước ghép.
