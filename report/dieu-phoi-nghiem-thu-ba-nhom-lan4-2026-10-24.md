# Nghiệm thu ba nhóm lần 4 và kế hoạch tiếp — 2026-10-24

## 1. Phán xét và phạm vi ghép

| Nhóm | Mốc đã soát | Phán xét | Tiếp theo |
|---|---|---|---|
| Web | `c8c687b63afff86d628688de73abb92dfd4f17a2`, nguồn cuối `b413698` | **W-08 đạt**, đóng R-W08-1/2; đã ghép local `bad8e45` | W-09 answer-3; sau đó W-10 theo document-3/quiz-3 |
| Lõi | Toàn gói `9b3bd8287e50c095e946eb4301ccc00a5572ca02`; mốc an toàn `bf761fe` | **Nhận và ghép riêng mốc kiểm/dry-run 0 USD** tại `bad8e45`; toàn W-15 còn mở | Sửa đường dẫn Windows của operator; xác minh đơn vị tính phí embedding trước duyệt profile; xin chi riêng khi đủ điều kiện |
| Thiết kế | `eb29f291709245a9ccf3d121415f6202fdeaae7f` | **Giữ đạt có ghi chú mốc thiết kế web W-22/W-24 theo chủ dự án**. Bản preview mới còn 3 lỗi công thức; chưa ghép cả nhánh | Vá giới hạn HTML công thức, hỗ trợ React W-09/W-23; không làm Cloud Figma |

Không đóng toàn W-15 bằng bằng chứng fake/dry-run, không coi kiểm metadata là một cuốn thật đã dựng thành công.
Không thu hồi phạm vi thiết kế web đã nhận và không tạo lại điều kiện Cloud/Variables export/native components/Present.
Luồng giao diện tiếp tục **HTML/CSS/token của thiết kế → React của web → cùng soát giao diện chạy thật**.

Main ban đầu `5936a5d`, nhận SA-67 `6cfc535` và cửa kiểm `a3804cf` trên mốc kết hợp `ab48fd2`.
Trong lúc kiểm main có thêm tài liệu `c093eed`; đã nhận và chạy cổng trên `0dc14af8bde31baf352238fd6cc0c3cdf17f017d`.
Sau đó Claude ghép SA-68 `21cfab3` và hồ sơ thật `574831b` trong lúc cổng này còn chạy. Codex ghi lại cửa kiểm `5e19b9b`,
nhận toàn main đó và chạy lại toàn cổng/browser trên **`c4d281b7fef7e750162162dcc290812a7637ca92`**, rồi mới ghép.
Giữ cả ba lượt; không dùng cổng ở main cũ để nhận tích hợp quiz-3. Lệnh ghép kiểm SHA main trong cùng script rồi mới `merge --no-ff` đúng mốc, đồng bộ bằng commit local theo quyết định mới của chủ dự án.
Không nhận các commit operator W-15 `5ed9ca1`, `ffd070d`, `9b3bd82` hoặc cả nhánh thiết kế chưa đạt.

**Quyết định của chủ dự án, 2026-10-24 — tạm thời chỉ commit local, chưa cần push main:**

> tạm thời k cần push lên main, commit đồng bộ mới nhất ở đây là đc, viết vô điều phối giao tiep đây là quyết định của tôi

Đã dừng các lượt truyền tiếp theo. Commit ghép trên máy là `bad8e45`; hồ sơ/ticket/kế hoạch/bàn giao tiếp tục commit local.
Chỉ tiếp tục push main khi chủ dự án yêu cầu; đây là chỉ thị mới có ưu tiên so với yêu cầu tự đẩy sau mỗi lần ghép trước đây.
Mọi điều kiện soát mã, nhận main local mới nhất và cổng xanh trước ghép vẫn giữ nguyên.

Trước quyết định này, push main bị reset (`curl55`); mốc main remote xác minh gần nhất là `5e19b9b`.
Gói Git khoảng145MB, có video W-08 lớn nhất56,2MB. Đã truyền được nhánh remote W-08 tới `89122f6` và
tham chiếu `refs/tags/coord-transfer/w08-owner-20261024` tới blob owner; lượt truyền `c8c687b` và video learner chưa thành công.
Không có lượt truyền nào còn chạy. Giữ các tham chiếu đã tạo; không chạy thêm push hoặc xoá ref remote sau khi chủ dự án yêu cầu dừng.
**Chưa đồng bộ main mới lên GitHub**; không ghi “đã đẩy”. Không viết lại lịch sử, không force-push hoặc xoá bằng chứng.
[Kích thước object](coord-ba-nhom-lan4-evidence-2026-10-24/transfer-stats.json),
[lượt truyền đã dừng](coord-ba-nhom-lan4-evidence-2026-10-24/runs/push-w08-learner-video-exit.json).

## 2. Cổng độc lập và giới hạn bằng chứng

| Kiểm | Kết quả | Bằng chứng |
|---|---|---|
| Python toàn repo, runner bắt buộc PostgreSQL, đúng mốc cuối | **2.602 đạt / 0 fail / 1 bỏ qua Cloudinary live / 1 xfail replay SA-55 có sẵn**, native 0 | [JUnit](coord-ba-nhom-lan4-evidence-2026-10-24/runs/full-current.xml), [lệnh/cwd/commit/native](coord-ba-nhom-lan4-evidence-2026-10-24/runs/full-current-exit.json) |
| React và build trên đúng mốc cuối | **181 đạt**, build native 0; npm ci native 0 | [JUnit](coord-ba-nhom-lan4-evidence-2026-10-24/runs/react-current.xml), [build](coord-ba-nhom-lan4-evidence-2026-10-24/runs/build-current-exit.json) |
| Browser HTTP/PostgreSQL/Lecture3UseCase thật, model/media/mail giả | **12 cấu hình**, 390/768/1280 × sáng/tối × normal/reduced; **109 ảnh, 341 HTTP, 17 Axe**, native 0 | [audit](coord-ba-nhom-lan4-evidence-2026-10-24/browser/audit.json), [runtime/SQL](coord-ba-nhom-lan4-evidence-2026-10-24/browser/runtime.json), [đọc độc lập raw SSE/tiến độ](coord-ba-nhom-lan4-evidence-2026-10-24/browser-independent.json) |
| Phá hai sửa W-08 trên mã thật | **2/2 bản sai bị bắt**, tương ứng 2 và 4 assertion fail, 0 setup error, SHA phục hồi khớp | [kết quả](coord-ba-nhom-lan4-evidence-2026-10-24/mutations/results.json) |
| Thiết kế đúng worktree qua runner | **52 đạt / 28 deselected**, native 0 | [JUnit](coord-ba-nhom-lan4-evidence-2026-10-24/runs/design-focused.xml), [lệnh](coord-ba-nhom-lan4-evidence-2026-10-24/runs/design-focused-exit.json) |
| Preview thiết kế bằng Chromium | 24 lượt trang, 12 cấu hình mỗi W-08/W-09, không tràn ngang; xác nhận 3 lỗi công thức. **Chẩn đoán, không phải gói đạt** | [DOM/accessibility](coord-ba-nhom-lan4-evidence-2026-10-24/design-browser/observations.json), [soát cấu trúc](coord-ba-nhom-lan4-evidence-2026-10-24/design-review/structural-observations.json) |
| Operator Windows | Hai plan thực đều bị `safe_path` từ chối; control đổi dấu phân cách sang `/` qua kiểm đường dẫn | [counterexample](coord-ba-nhom-lan4-evidence-2026-10-24/core-review/repro_windows_plan.py), [phán xét](coord-ba-nhom-lan4-evidence-2026-10-24/core-review/summary.json) |

Giữ nguyên lượt đầu đỏ tại `ab48fd2`: **2.567 đạt / 1 fail / 1 skip / 1 xfail**, lỗi duy nhất do worktree điều phối thiếu `tmp/w15-candidate/input.pdf`.
Đã chép thường bản mẫu train từ worktree lõi, đối chiếu đủ SHA-256/kích thước, rồi chạy lại **toàn cổng** với basetemp mới; không sửa sản phẩm hoặc bỏ test:
[bản sao](coord-ba-nhom-lan4-evidence-2026-10-24/candidate-copy.json), [JUnit lượt đầu](coord-ba-nhom-lan4-evidence-2026-10-24/runs/full.xml).
Cần chép cả bản mẫu này khi kiểm W-15 ở worktree khác; snapshot sáu cuốn không bao gồm nó.
Cổng trung gian tại `0dc14af`: **2.568 đạt / 0 fail / 1 skip / 1 xfail**, React181/build xanh;
[giữ JUnit](coord-ba-nhom-lan4-evidence-2026-10-24/runs/full-final.xml). Mốc này chưa có SA-68 nên không phải cổng dùng để ghép cuối.

Browser lần đầu ở mốc cuối chạy hết ma trận nhưng **native1**: một yêu cầu tải font Google trả `ERR_QUIC_PROTOCOL_ERROR`;
guard console/mạng đã bắt, không nhận lượt này đạt. Đã giữ [log lỗi](coord-ba-nhom-lan4-evidence-2026-10-24/runs/browser-current.log),
[audit](coord-ba-nhom-lan4-evidence-2026-10-24/browser-font-failure/audit.json) và kiểm DB/port đã dừng;
chạy lại toàn browser trên **cùng commit, không đổi mã/timeout/guard hoặc lọc lỗi font**, với thư mục bằng chứng mới.
Lượt sau native0, không lỗi mạng/console ngoài các lỗi giả được định nghĩa sẵn:
[lệnh](coord-ba-nhom-lan4-evidence-2026-10-24/runs/browser-current-retry-exit.json).

Axe chỉ gồm 17 lượt theo harness, không nhận mọi ảnh là đã Axe. Không violation/incomplete chưa soát, lỗi trang, request fail hoặc tràn ngang;
giữ finding glyph công thức đã đo màu thực cùng phép phản chứng màu trùng nền. Log giữ lỗi SQL giả để kiểm rollback,
Windows Proactor reset và grace-shutdown warning. Thread đã dừng; kiểm SQL/port độc lập xác nhận UUID DB không còn và cổng 8018 không nghe:
[kiểm sau browser](coord-ba-nhom-lan4-evidence-2026-10-24/runtime-cleanup.json).

Đã xem ảnh [desktop sáng](coord-ba-nhom-lan4-evidence-2026-10-24/browser/ready-1280-light.png) và
[mobile tối/reduced](coord-ba-nhom-lan4-evidence-2026-10-24/browser/ready-390-dark-reduced.png): chữ/công thức đọc được, nguồn xuống dòng,
đáp án gập, sidebar tách đúng chế độ; ảnh trích công thức gốc vẫn có nền trắng khi tối. Không nhận chất lượng nội dung LLM thật từ nội dung fake.

## 3. Web — W-08 đạt

**Đóng R-W08-1:** bài giảng nhận `progress.nodes` hiện tại; nhãn Cần biết trước/Tiếp theo theo thao tác sidebar,
save thành công và rollback đều đúng. Browser đối chiếu SQL và số request: không fetch/sinh lại bài chỉ để đổi nhãn.
**Đóng R-W08-2:** regex React nhận 2–4 dấu #, thụt đầu, dấu hai chấm/khác hoa thường; SA-70 đã ghép `5188908`
giữ toàn tiêu đề tự kiểm tra khỏi delta, kể cả chia nhỏ từng ký tự. Năm raw HTTP/SSE xác nhận delta không có đáp án;
final luôn thay nội dung stream bằng `body_md`, kể cả `self_check=null` để không mất phần cuối hợp lệ.

Soát độc lập hồ sơ web: **392** bằng chứng SHA/kích thước, **19** tệp nguồn/blob, **15** mutation và **5** raw SSE khớp;
hai Required không còn. Lượt RED2 lịch sử là 6 fail/11 control, không nhận hook timeout là phép phản chứng:
[soát nguồn/hồ sơ](coord-ba-nhom-lan4-evidence-2026-10-24/web-review/review.md), [summary](coord-ba-nhom-lan4-evidence-2026-10-24/web-review/summary.json).

## 4. Lõi — nhận mốc 0 USD, trả phần operator

Mốc `bf761fe` chỉ thêm **5 tệp test/harness, 458 dòng**, không đổi mã sản phẩm. Đã kiểm DocumentPipeline thật với generation/embedding giả,
PostgreSQL qua connection độc lập, tiêm cùng kho vào tên module/A12/chỉ mục, meter/trace tính đúng một lần, hủy/lease và terminal receipt.
Hai dry-run nội bộ dùng byte PDF thật trên bản sao, đọc/kiểm chữ thật, collector web một receipt; không queue/course/usage/cache SQL side effect, không gọi nhà cung cấp.
Doc-6 qua đường web mặc định dừng ở **label-roles cache miss / SpendNotAllowed**, 0 USD; **không phải** cache-only dựng xong, không ready/course/mail thành công.
[Soát độc lập](coord-ba-nhom-lan4-evidence-2026-10-24/core-review/review.md). Hồ sơ tác giả có 76 ca phạm vi, 29 mutation; điều phối kiểm chọn lọc 10 manifest entry/23 source hash,
đọc mutation đã lưu, không tuyên bố tự chạy lại toàn 29 phép phá. Cổng điều phối ở mục 2 là bằng chứng tích hợp hiện tại.

**W15-R4-1 — bắt buộc sửa:** `src/web/backend/tests/w15_operator_run.py:88` ghi `run_dir` bằng `str(relative_to(...))`, tạo dấu `\` trên Windows;
`execute` dòng 122 dùng `safe_path` vốn từ chối dấu này. Cả hai plan đã lưu thực tế đều lỗi `ValueError: Path escapes its root` trước DB/provider.
Test dòng 60 tự ghi `.as_posix()` nên bỏ qua lỗi prepare. Sửa serialization sang đường dẫn portable, giữ `safe_path` nghiêm;
thêm test thực sự đi **prepare → JSON trên đĩa → execute validation**, fake provider/PG riêng, thấy RED trước sửa rồi GREEN.
Không sửa tay plan thật để thay cho sửa lỗi và không nới guard.

**W15-R4-P1 — trước duyệt profile/có tiền:** xác minh đúng đơn vị của SKU **online Vertex** cho `gemini-embedding-001` và trường usage tính chi.
Tài liệu Google cho batch ủng hộ đơn vị token, nhưng bảng online “count” và response có cả token/billable-character chưa đủ chốt ánh xạ profile.
**Chưa chứng minh code tính thiếu tiền**; đây là điều kiện bằng chứng trước lượt có tiền, không chặn mốc 0 USD đã ghép.
Nguồn chính thức và giới hạn suy luận trong [đối chiếu giá](coord-ba-nhom-lan4-evidence-2026-10-24/core-review/embedding-pricing-primary-check.md).

Đề nghị tác giả: bootstrap doc-6 tối đa 1 USD, cuốn 52 trang tối đa 3 USD, tổng đề nghị 4 USD. **Chưa được duyệt, chưa chạy**;
số gọi/chi/thời gian các bước chưa đo phải giữ “chưa biết”, không coi cap là dự toán. Approval JSON dựa vào operator tin cậy,
không phải chữ ký xác thực chủ dự án. Chỉ xin duyệt chính xác cuốn/SHA/lượt/profile/trần sau hai điều kiện trên;
không dùng quyền chi phục hồi/SA trước đây. Chi build duy nhất vẫn meter delta, `counted_in=build` không cộng lần hai.

## 5. Thiết kế — giữ mốc web đã nhận, vá công thức mới

Đóng phần cũ đã sửa: nhân vật chờ 96px (GIF decode đủ 61 frame), retry ở lỗi sớm/fatal, giữ chữ sau lỗi đuôi,
hai anchor báo cáo, guard VM đếm đúng output (74 giá trị, lỗi create primary 72/2; bỏ accounting bị test bắt).
**Không giao làm lại token, plugin, layout, thương hiệu, usage/chat hoặc Cloud.**

Ba lỗi nằm ở bản công thức HTML mới, được tái hiện bằng DOM/accessibility và ảnh:

1. **D-R4-01**, `design/preview/w09_chat_screens.html:254`: markup giả hình KaTeX thiếu CSS toán/chỉ số dưới.
   DOM đo chữ chính/chỉ số cùng y, cùng 14px/baseline; [ảnh desktop](coord-ba-nhom-lan4-evidence-2026-10-24/design-browser/w09-active-1280.png).
2. **D-R4-02**, công thức W-08/W-09 bị `aria-hidden` nhưng không MathML/nhãn tương đương: trình đọc màn hình mất biểu thức.
   W-09 và công thức khối W-08 cho snapshot rỗng; công thức đầu W-08 chỉ còn phần văn xuôi bị lồng sai.
3. **D-R4-03**, `w08_lecture_screens.html:272`: thiếu thẻ đóng span, công thức khối/văn xuôi sau bị lồng trong `.katex` đầu,
   làm văn xuôi nhận font toán; [ảnh mobile](coord-ba-nhom-lan4-evidence-2026-10-24/design-browser/w08-ready-390.png).

Vá tối thiểu bằng cấu trúc/render toán đúng, nội dung truy cập được và thẻ cân bằng; thêm guard quan sát đầu ra thực.
Đây là trả phần preview mới để dùng tiếp cho React; mốc thiết kế web đã được chủ dự án nhận **vẫn đạt có ghi chú**.
[Chi tiết](coord-ba-nhom-lan4-evidence-2026-10-24/design-review/review.md). Có thể đổi câu “lưu an toàn” thành “phần đã nhận vẫn hiện trên màn hình”
để không hứa cache bền cho `cat_ngan`; không tạo thêm việc Cloud.

## 6. Kế hoạch giao tiếp

[Lời giao đủ ba nhóm](lenh-giao-viec-ba-nhom-lan4-2026-10-24.md), chưa gửi phiên nhân viên bên ngoài.

| Nhóm | Ưu tiên ngay | Xong khi |
|---|---|---|
| Web | Nhận main có W-08, mở W-09 answer-3; SA-66/69/70 đã ghép | HTTP/gateway/session/focus/cache-only + React chạy PG/fake, quyền và idempotency, nguồn/artifact an toàn, browser sáng/tối/reduced; cổng xanh trước đề nghị ghép |
| Lõi | Sửa W15-R4-1 rồi W15-R4-P1, giữ mặc định không chi | prepare→execute GREEN có RED hợp lệ, profile online có nguồn/ánh xạ hoặc fail closed; bảng đề nghị chi đúng cuốn/hash/profile/lượt và các số chưa biết rõ ràng |
| Thiết kế | Vá D-R4-01/02/03; hỗ trợ W-09 và soát W-08 theo W-23 | Công thức nhìn đúng, cây truy cập có biểu thức, DOM không lồng sai; giao HTML/CSS/token và ảnh đối chiếu React, không chờ Cloud |
| Claude/Pha B | SA-61 còn đang cài; các nâng cấp SA vẫn do Claude soát/ghép | SA-67 document-3 đã vào main `6cfc535`, SA-68 quiz-3 tại `21cfab3`; W-10 đã có cả hai lõi, vẫn phải nghiệm thu HTTP/React riêng |

W-09 không còn chờ lõi; web không vá scope ở core. Sau W-09 tới W-10, rồi nghiệm thu W-23 trên đủ màn học/trợ lý/quiz/tài liệu.
Giữ Vertex đến khi chủ dự án yêu cầu đổi cho demo; SA-61 chưa được coi là đã ghép/chuyển transport chỉ vì đã có số đo embedding.

## 7. An toàn dữ liệu và bàn giao

Đã chép thường **3.144 tệp fixture phát triển**, SHA khớp, không learner store, và một PDF mẫu train riêng có SHA:
[manifest copy](coord-ba-nhom-lan4-evidence-2026-10-24/fixture-copy.json). Không mở live cache dùng chung/tập giữ lại;
không dọn hoặc gỡ bất kỳ worktree/snapshot/ZIP/artifact, không link và không đụng `tmp/t01a-clean-ff797eb`.
Sáu tệp dở ở root của phiên khác giữ nguyên SHA; các tệp untracked cũ không đưa vào commit.
[Ledger bằng chứng](coord-ba-nhom-lan4-evidence-2026-10-24/manifest.json),
[ảnh/video/raw đầy đủ giữ local có hash](coord-ba-nhom-lan4-evidence-2026-10-24/browser-local-files.json).
**Chi nhà cung cấp mới của cả đợt: 0 USD**; fake usage SQL không phải tiền đã trả. Không cấp quyền paid W-15.
Sau ghép và commit hồ sơ local theo quyết định chủ dự án, **mở lại cửa ghép SA/cổng toàn repo cho Claude**. Main phải được nhận và cổng chạy lại nếu main thay đổi trước ghép.
