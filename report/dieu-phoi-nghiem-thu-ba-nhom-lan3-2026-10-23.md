# Nghiệm thu ba nhóm lần 3 và kế hoạch tiếp — 2026-10-23 tối

## 1. Kết luận

**Chưa có gói mới nào đủ điều kiện đóng toàn vé hoặc ghép mã sản phẩm.** Web W-08 có hai lỗi được tái hiện bằng 6 assertion đỏ;
lõi W-15 mới nộp hồ sơ kiểm trước port, chưa làm phần tích hợp sau SA-62; thiết kế W-24 sửa đúng Variables/chat nhưng còn sai hợp đồng bài giảng,
hai anchor và chưa hoàn thiện Figma thật. Không giao lại các phần đã được kiểm đạt.

| Nhóm | Đúng mốc nhận | Phán xét | Phần tiếp ngay |
|---|---|---|---|
| Web | `89122f66e6d3075e5d0c44beff31d27d4026b642` | Chưa nhận toàn W-08, chưa ghép | Đồng bộ nhãn tiến độ trong bài; gập đáp án đúng mọi tiêu đề core nhận; sau nghiệm thu mới W-09 |
| Lõi | `6bcbae61e821981e5254314aee7ee65db9868eeb` | Nhận hồ sơ pre-port có giới hạn; W-15 vẫn mở | Nhận main có SA-62/64/65, kiểm toàn pipeline/PG và dry-run 0 USD; lập đề nghị chi có số đo |
| Thiết kế | `f292f18c823045c327e5e5a0fb1881961be15390` | Nhận riêng sửa Variables/chat; chưa nhận cả gói W-24 | Sửa preview lecture-3 và báo cáo; hoàn thiện Variables/components/bindings/prototype trên Cloud |

Main nền `e5fa4924cc7e3d6eda924d6668c8c15b453cea91`; điều phối ghi cửa kiểm tại `0ccedae` rồi nhận W-08/main vào worktree một cấp
`tmp/coord-r3-acceptance-20261023`, mốc **`1449d51abf6b35d285614a7c39928db61cd158dc`**. Mã `src/tests/scripts/design` khớp nguồn cuối của web `e6b336e`;
`e6b336e → 89122f6` chỉ bổ sung hồ sơ. Main đã có SA-62 `9ac2a85`, SA-64 `1d91b0b`, SA-65 `4a4b957`;
không còn chờ phân công Pha A hoặc ghép port. SA-66 vẫn là nhánh đang làm tại thời điểm kiểm, chưa nhận là main.

## 2. Cổng và bằng chứng độc lập

| Kiểm | Kết quả thực tế | Bằng chứng |
|---|---|---|
| Python toàn repo qua runner, PostgreSQL bắt buộc | **2.385 đạt / 0 fail / 1 Cloudinary live không bật**; 8 warning, native 0; pytest 756,37 giây, wrapper 772,53 giây | [JUnit](coord-ba-nhom-lan3-evidence-2026-10-23/runs/full.xml), [lệnh/cwd/commit/native](coord-ba-nhom-lan3-evidence-2026-10-23/runs/full-exit.json) |
| React trên nguồn chưa sửa | **158 đạt**, native 0; npm ci và build native 0, npm ci báo 0 vulnerability | [JUnit](coord-ba-nhom-lan3-evidence-2026-10-23/runs/react.xml), [build](coord-ba-nhom-lan3-evidence-2026-10-23/runs/build-exit.json) |
| Phá guard cache-only / HTTP DTO privacy / KaTeX trust | **3/3 bị assertion bắt**, mỗi bản sai native 1, không setup error; phục hồi cùng SHA trước cổng/browser | [kết quả](coord-ba-nhom-lan3-evidence-2026-10-23/mutations/results.json) |
| Browser HTTP/PostgreSQL, Lecture3UseCase thật + model/media giả | **12 cấu hình**, 390/768/1280 × sáng/tối × normal/reduced, **101 ảnh / 306 HTTP / 17 Axe**; native 0, không violation hoặc incomplete chưa soát | [audit](coord-ba-nhom-lan3-evidence-2026-10-23/browser/audit.json), [runtime/SQL](coord-ba-nhom-lan3-evidence-2026-10-23/browser/runtime.json) |
| Ca phản chứng bổ sung cho W-08, sau cổng xanh | **6 assertion fail / 11 pass / 0 error**, native 1, không sửa sản phẩm | [JUnit](coord-ba-nhom-lan3-evidence-2026-10-23/runs/repro.xml), [6 ca đỏ](coord-ba-nhom-lan3-evidence-2026-10-23/repro-finish.json) |
| Thiết kế trên đúng worktree qua runner | **49 đạt / 28 deselected**, native 0; không phải cổng toàn repo của gói thiết kế | [JUnit](coord-ba-nhom-lan3-evidence-2026-10-23/runs/design-focused2.xml), [lệnh](coord-ba-nhom-lan3-evidence-2026-10-23/runs/design-focused2-exit.json) |
| Plugin đầu ra thực, bình thường/fallback và lỗi create/set mode | **9 kịch bản** xác nhận 74/74 khi thường; lỗi create primary 72 tạo/2 lỗi, lỗi một mode 73/1, thiếu Dark 37/37; có cảnh báo | [VM](coord-ba-nhom-lan3-evidence-2026-10-23/design-review/plugin-adversarial-observations.json) |
| Browser preview W-24 | **12 cấu hình chẩn đoán** xác nhận LaTeX thô/không nút retry ở fatal; diagnostic native 0 không có nghĩa gói đạt | [quan sát](coord-ba-nhom-lan3-evidence-2026-10-23/design-browser/observations.json) |
| Figma Cloud đọc mới trong lượt này | 1 collection Light nhưng **0 Variables, 0 components/sets/instances, 0 bindings, 0 reactions, 0 starting points**; 289 node, 6 frame cấp đầu, 1 page | [receipt Cloud](coord-ba-nhom-lan3-evidence-2026-10-23/cloud-read.json) |

Axe 17 lượt tập trung 1280 px theo harness, không nhận toàn bộ 101 ảnh là đã Axe. Giữ 8 finding glyph KaTeX đã soát màu thực và phép phá cùng màu nền;
không có incomplete chưa xử lý. Inspector còn cảnh báo font generic `math`; ba font Be Vietnam Pro/KaTeX đã tải.
Log browser giữ nguyên lỗi SQL giả để kiểm rollback, Windows Proactor reset khi đóng kết nối và cảnh báo grace shutdown;
native vẫn 0, thread đã dừng. Kiểm độc lập xác nhận UUID DB riêng đã gỡ và cổng 8018 không còn nghe:
[cleanup](coord-ba-nhom-lan3-evidence-2026-10-23/runtime-cleanup.json).

Đã xem trực tiếp [desktop sáng](coord-ba-nhom-lan3-evidence-2026-10-23/browser/ready-1280-light.png),
[mobile tối/reduced](coord-ba-nhom-lan3-evidence-2026-10-23/browser/ready-390-dark-reduced.png): bố cục đọc rõ, sidebar tách cột,
nguồn xuống dòng, công thức bài giảng được dựng; ảnh công thức gốc giữ nền trắng trong tối. Không yêu cầu đổi hướng thiết kế vì hai lỗi chức năng bên dưới.

## 3. Web W-08 — hai Required trước ghép

**R-W08-1: nhãn tiến độ không đổi theo thao tác hiện tại.** `src/web/frontend/src/Learning.tsx:88–90,127` lấy nhãn tiên quyết và Tiếp theo từ snapshot `lecture`;
thao tác sidebar chỉ cập nhật `data.progress`. Mở bài A, đánh dấu B đã học: checkbox B và tiến độ đã đổi nhưng nhãn B trong bài A vẫn “Chưa học”.
Hai test mới tái hiện riêng hai vùng. Sửa dùng nguồn tiến độ hiện tại cho toàn trang; kiểm lưu thành công và rollback, không sinh lại bài để cập nhật nhãn.

**R-W08-2: đáp án lộ khi stream ở các tiêu đề hợp lệ.** `Learning.tsx:82` chỉ cắt `### Tự kiểm tra` không thụt đầu/dấu hai chấm;
core `lecture3.py:73–95` nhận 2–4 dấu `#`, khoảng trắng đầu và dấu `:` cuối. Thử splitter thật và renderer thật:
`## Tự kiểm tra`, `#### Tự kiểm tra`, `### Tự kiểm tra:` và `  ### Tự kiểm tra` làm đáp án hiện trước `final`, rồi mới gập.
Control `### Tự kiểm tra` đạt. Đồng bộ quy tắc trong lúc stream; giữ bài không có `self_check` theo hợp đồng, không cắt bỏ nội dung hợp lệ.

[Helper tái hiện](coord-ba-nhom-lan3-evidence-2026-10-23/web-review/Learning.review-repro.test.tsx) giữ 10 ca của tác giả và thêm 7 ca.
Đã chép thường vào worktree điều phối **sau** cổng nguồn gốc, chạy 17 ca, rồi chuyển riêng helper sang scratch giữ nguyên byte;
không sửa worktree nhân viên hoặc mã sản phẩm. SHA helper `d5d4f470765b513bd60e643745aa7c1a4a400c64e87049ccf4e1aa231edf92cf`.
Chưa có bản vá nên chưa ghi GREEN cho 6 ca mới.

Đã đối chiếu **1.007/1.007 nguồn, 1.007 blob Git, 587/587 bằng chứng và 13/13 mutation** của nhân viên;
[review nguồn/hồ sơ](coord-ba-nhom-lan3-evidence-2026-10-23/web-review/summary.json). Các cổng và biện pháp quyền/DTO/media có bằng chứng tốt,
nhưng chưa thay được việc sửa hai lỗi trên. Tiếp cùng W-08, không phát sinh vé mới chỉ để làm lại công việc đang mở.

## 4. Lõi W-15 — hồ sơ chuẩn bị đạt, công việc sau port chưa làm

Diff so main chỉ **5 tệp docs/evidence**, báo cáo thêm **30 dòng**; không có mã/test mới so mốc adapter đã ghép.
**3/3 entry** manifest audit khớp SHA/kích thước Git. Audit ghim `f96fc00` là lịch sử trước port, kiểm 127 hash doc-6,
graph v29/chunks v4/parse v2/retrieval v1, fingerprint và thay text trong bộ nhớ bị bắt;
không execute/claim/receipt/provider. [Review](coord-ba-nhom-lan3-evidence-2026-10-23/core-review/review.md).

Thông tin “chưa có port” đúng ở mốc audit đó; **không còn là điểm chờ hiện tại**. Ca dương default factory/PG tại SA-62 đã được điều phối làm và ghép,
không giao làm lại. Cần kiểm tiếp toàn chuỗi thật với model/embedding fake, kho PG xuyên kết nối, cache/tên/A12/usage/cancellation/lease.
Sau đó mới dry-run nội bộ trên bản sao có SHA, `allow_spend=False`, guard mạng, không vào queue hoặc làm course ready.

ID web `u-<hash PDF>` khác alias `doc-6`; các miss đường dẫn trong bản sao không chứng minh mọi cache miss hoặc một lượt doc-6 miễn phí.
Chưa có số gọi/USD/phút đo được cho cuốn 52 trang; giữ “chưa biết” đến khi có dry-run. Meter delta là chi build duy nhất,
trace `counted_in=build` không cộng lần hai; DailySpendGuard Pha B không nhận các purpose dựng chỉ để áp trần học.
Artifact Pha A và ảnh trang SA-65 ở kho tệp theo ADR 0022, không chuyển graph/chunks/index vào DB.

## 5. Thiết kế W-24 — nhận sửa đúng, phần còn thiếu

**Đóng** lỗi nuốt Variables của mã hiện tại và alpha 0.99 thực; đóng hạn mức 30 lượt/ngày/raw tools; xác nhận chat rỗng,
pending invitation và các anchor section mới có thật. Mã sửa không cần làm lại.
49 test xanh chủ yếu là kiểm cấu trúc; mutation bỏ accounting lỗi create của guard hiện vẫn lọt test riêng,
trong khi VM kiểm độc lập bắt đầu ra thực. Phải giữ/đưa kiểm VM này vào luồng kiểm hồi quy; không dùng claim “13 mutation đỏ” thay cho bằng chứng mọi nhánh lỗi.

**R-W24-1, preview/hợp đồng:** mọi cấu hình đều có **0 `.katex`**, công thức `$P_{...}$` hiện nguyên văn.
Khối chờ chữ đầu dùng CSS spinner cao 20 px (mobile bị co chiều rộng), không phải nhân vật 96 px như báo cáo/spec.
Trạng thái fatal vẫn dùng lời “không thể phục hồi” và không có retry; hợp đồng hiện hành yêu cầu chưa có chữ luôn có message/Thử lại.
Bản tail phải giữ chữ và `cat_ngan`, không hứa tải một bản đủ nếu chưa có thao tác hợp đồng tương ứng.
[Ảnh công thức](coord-ba-nhom-lan3-evidence-2026-10-23/design-browser/ready-1280-light.png),
[fatal mobile](coord-ba-nhom-lan3-evidence-2026-10-23/design-browser/fatal-390-dark.png).
Chỉ yêu cầu đủ minh chứng thiết kế và tương tác local đã giao; không yêu cầu nhóm thiết kế viết lại React.

**R-W24-2, hồ sơ:** báo cáo `w24-kiem-lai-2026-10-22.md:138,152` còn trỏ `#text-tool-action` và `#btn-delete-course` không tồn tại;
nút thực là `#btn-delete-course-permanent`. Sửa claim KaTeX/96 px/100% đã đóng theo đúng output.
W-09 KaTeX mới dừng ở lời claim, chưa có mẫu/render; ghi rõ chuẩn bị tương lai hoặc minh chứng đúng, không tự coi trần “cấm ký hiệu $” là cấm cú pháp LaTeX.

**R-W24-3, bàn giao Cloud gốc:** đọc mới xác nhận canvas hiện vẫn trống các cấu trúc cần nghiệm thu ở bảng trên;
chưa có bốn video Present. HTML/plugin source không thay receipt Variables/components/variants/bindings/reactions và bốn luồng bấm thật.
W-22/W-24 còn mở; W-23 chưa đủ đầu vào để đối chiếu trọn bộ.

## 6. Kế hoạch, quyền chi và hồ sơ

1. **Web:** sửa R-W08-1/2, đưa ca phản chứng vào suite, RED→GREEN, cổng toàn repo và browser đúng commit nhận main mới nhất.
   Điều phối soát/ghép sau đạt; rồi W-09 theo answer-3. Có thể chuẩn bị bằng fake nhưng cổng cuối chờ Claude ghép SA-66.
2. **Lõi:** tiếp W-15 ngay sau nhận main có SA-62/64/65; toàn pipeline fake/PG → identity/cache → dry-run guarded 0 USD → bảng ước tính và đề nghị trần riêng.
   Không chạy sách thật có tiền khi chưa được chủ dự án duyệt đúng cuốn/lượt/trần.
3. **Thiết kế:** sửa các điểm local/hồ sơ còn lại, giữ guard đầu ra plugin, rồi hoàn thiện Cloud/video; ưu tiên trang học/chat trước màn phụ thuộc sau.
   Không giao lại Variables/chat đã sửa đúng; vẫn dùng logo Artboard 9–28, Be Vietnam Pro/token và taste-skill theo quy định.
4. **Sau đó:** W-09 → W-10 theo spec/mốc SA-67/68 khi Claude chốt; W-16/17/19/21/W-23 chưa nhận đủ luồng sản xuất.
   Admin phải giữ validation riêng và lọc trace build; triển khai phải sao lưu artifact/ảnh trang cùng index/SHA bên cạnh DB.

[Lời giao riêng ba nhóm](lenh-giao-viec-ba-nhom-lan3-2026-10-23.md). Đã soạn, chưa gửi các phiên nhân viên bên ngoài.
Giữ Vertex đến khi chủ dự án yêu cầu đổi; không biến mốc demo dự kiến thành lịch tự đổi API.

Tổng chi dịch vụ ngoài mới **0 USD**. Dữ liệu kiểm chỉ chép từ allowlist: **3.144/3.144 SHA**, không links/live.json/tập giữ lại;
giữ mọi worktree/snapshot/ZIP và `tmp/t01a-clean-ff797eb`. Sáu tệp dở của phiên khác ở root giữ nguyên SHA.
Hồ sơ [manifest](coord-ba-nhom-lan3-evidence-2026-10-23/manifest.json) có **125 entry cùng manifest**, khoảng **7,74 MB** được đưa vào Git;
hai video thô **56,89 MB** giữ nguyên local ở hai vị trí ghi trong manifest, có SHA và được bỏ qua khi commit. Không xoá video hay ảnh gốc.
Các lệnh đầy đủ/cwd/commit/native ở `runs/*-exit.json`; helper tạo/chốt hồ sơ cũng được lưu.
Lượt `design-focused` đầu native 4 vì pytest chưa nạp conftest định nghĩa `--require-postgres`, không có test chạy;
lượt đúng `design-focused2` nạp thêm backend test để đăng ký option, chọn đúng 49 test thiết kế và deselect 28 test khác. Giữ cả hai log, không coi lượt đầu là xanh.

Không ghép W-08/W-15/W-24 mới trong lượt này. Khi hồ sơ được đẩy, mở lại cửa ghép SA cho Claude; cổng PostgreSQL và browser của điều phối đã kết thúc.
