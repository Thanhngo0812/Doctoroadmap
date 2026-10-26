# Nghiệm thu ba nhóm lần 6 và kế hoạch tiếp — 2026-10-25

## 1. Kết luận

| Nhóm | Commit được soát | Phán xét | Việc tiếp |
|---|---|---|---|
| Web | `378131ec0be0ac91b599549ae13b1a192fc710ac` | **W-09 đạt**, đóng R-W09-1/2; ghép local `7f54b14` | W-10: quiz, tài liệu và thư viện theo hợp đồng mới |
| Lõi | `efed8db5b6b2cf76965a8884f23bfe2b9fe4c988` | **W-15 đạt có ghi chú trong phạm vi tích hợp và đo lượt dựng thật**, ghép local `7f54b14` | Backend W-16, dùng lại endpoint/ledger đã có; không chạy thêm lượt trả phí |
| Thiết kế | `0b5993e47a01b45bc2f645741aa38af42f99c5f4` | **Chưa nhận gói bổ sung W-10**, một Required về nhóm thư viện; chưa ghép commit này | Sửa D-R6-01 và làm đối chiếu React thực cho W-23 |

Mốc thiết kế W-22/W-24 đã nhận và các sửa công thức `aa387f3` giữ nguyên. Không mở lại Cloud Figma.
Chỉ commit local, **không push GitHub**, theo quyết định chủ dự án 24/10. Chi mới của điều phối **0 USD**.
Không sửa mã sản phẩm thay nhân viên. Các lượt W-15 có tiền đã diễn ra trong phiên nhân viên theo các chỉ thị mới được trích ở mục 4;
đợt nghiệm thu này chỉ đọc bằng chứng và SQL, không chạy lại provider.

Nền main `6249dab`, cửa kiểm `bababd0`. Đỉnh ba nhóm `7a99fbd17621b6429dec08869e07a7e4d178f97f` dùng để kiểm tương tác.
Sau khi phát hiện Required ở mẫu W-10, tạo riêng đỉnh **`c23d1111e45b8e4346887bbab83b0d7f1b7f842f`** chỉ gồm W-09/W-15
và main mới nhất, chạy lại đủ cổng trước ghép. Không đưa commit thiết kế cần sửa vào main, không viết lại lịch sử nhánh nhân viên.

## 2. Cổng kiểm độc lập

| Kiểm | Kết quả | Bằng chứng |
|---|---|---|
| Python toàn repo trên ba nhóm `7a99fbd` | **2.719 đạt / 0 fail / 1 skip / 1 xfail**, native 0 | [JUnit](coord-ba-nhom-lan6-evidence-2026-10-25/runs/full.xml), [lệnh/native](coord-ba-nhom-lan6-evidence-2026-10-25/runs/full-exit.json) |
| React/build trên ba nhóm | **203 đạt**, build native 0 | [JUnit](coord-ba-nhom-lan6-evidence-2026-10-25/runs/react.xml), [build](coord-ba-nhom-lan6-evidence-2026-10-25/runs/build-exit.json) |
| Cổng đúng đỉnh ghép `c23d111` | **2.716 Python đạt / 0 fail / 1 skip / 1 xfail; 203 React đạt**, build native 0 | [Python](coord-ba-nhom-lan6-evidence-2026-10-25/runs/safe-full.xml), [React](coord-ba-nhom-lan6-evidence-2026-10-25/runs/safe-react.xml), [build](coord-ba-nhom-lan6-evidence-2026-10-25/runs/safe-build-exit.json) |
| Browser HTTP/PostgreSQL/core use case thật, model/mail/media giả | **12 cấu hình, 102 ảnh, 46 Axe, 386 bản ghi HTTP/SSE**; native 0 | [Audit](coord-ba-nhom-lan6-evidence-2026-10-25/browser/audit.json), [SQL/runtime](coord-ba-nhom-lan6-evidence-2026-10-25/browser/runtime.json) |
| W-09: câu sau final/usage trễ | Hiện tại **5 đạt**; hook cũ **5 assertion fail, 0 error**; mutant ghi usage cũ bị bắt | [JUnit hiện tại](coord-ba-nhom-lan6-evidence-2026-10-25/web-review/r1-current.xml), [bản cũ](coord-ba-nhom-lan6-evidence-2026-10-25/web-review/r1-old.xml) |
| W-09: chuyển cờ bài giảng | 9 tổ hợp cờ; tool thường sinh đúng 1 lần, focus miss/hit không sinh | [Probe độc lập](coord-ba-nhom-lan6-evidence-2026-10-25/web-review/r2-independent.json) |
| W-15: chi/SQL/graph/ảnh | Đối chiếu read-only DB riêng, plan/grant, 1 claim/attempt, graph v8; 33 ảnh giải mã/SHA đạt | [Audit độc lập](coord-ba-nhom-lan6-evidence-2026-10-25/core-review/independent-audit.json), [doc-6/chi R5](coord-ba-nhom-lan6-evidence-2026-10-25/doc6-independent.json) |
| W-15: giữ core retry và cận chi | 5 probe offline đạt; 3 mutant đều bị bắt; không DB/provider | [Probe](coord-ba-nhom-lan6-evidence-2026-10-25/core-review/baseline-probe.json), [mutant](coord-ba-nhom-lan6-evidence-2026-10-25/core-review/offline-mutants-native.json) |
| Thiết kế mới | 61 focused đạt, CSS mutant và HTML cũ bị guard bắt; browser mẫu 12 cấu hình không tràn | [Native](coord-ba-nhom-lan6-evidence-2026-10-25/design-review/native-records.json), [quan sát](coord-ba-nhom-lan6-evidence-2026-10-25/design-review/browser-observations.json) |
| Phản chứng nhóm thư viện W-10 | Lọc hiện tại chọn sai tài liệu; control dùng group đúng đạt cả hai tab | [Phản chứng](coord-ba-nhom-lan6-evidence-2026-10-25/design-library-counterexample.json), [helper](coord-ba-nhom-lan6-evidence-2026-10-25/design-library-repro.cjs) |

Python luôn qua `scripts/w05_run_tests.py`, PostgreSQL bắt buộc; chỉ một cổng toàn repo tại một thời điểm.
Một skip là Cloudinary live không bật, một xfail là replay SA-55 có sẵn; không thêm skip hoặc giảm assertion để xanh.
Browser không có page error, vi phạm Axe, tràn ngang hay vùng bấm sai. Có **97 console error đã phân loại**:
46 probe font và 46 probe style của Axe bị CSP chặn, 2 lần 401 trước đăng nhập, 3 lần 404 sau thu hồi quyền.
23 lượt contrast incomplete có phép đo màu/vị trí thực đạt ngưỡng; không ghi console sạch hoặc nới CSP.
[Đối chiếu độc lập](coord-ba-nhom-lan6-evidence-2026-10-25/browser-independent.json).
Đã kiểm DB browser không còn, producer dừng và cổng 8019 đóng: [kết quả](coord-ba-nhom-lan6-evidence-2026-10-25/runtime-cleanup.json).

Đã nhìn ảnh React [mobile sáng](coord-ba-nhom-lan6-evidence-2026-10-25/browser/conversation-options-390-light.png),
[hai câu hoàn tất](coord-ba-nhom-lan6-evidence-2026-10-25/browser/usage-race-completed-1280-dark-reduced.png),
và [mẫu thư viện mobile](coord-ba-nhom-lan6-evidence-2026-10-25/design-review/w10-library-390.png).
Giữ token/Be Vietnam Pro/logo/hiệu ứng đã chốt. Taste inspector không FAIL; hai WARN về generic font math và bài đọc dài dưới fold
được giữ có giải thích. Mẫu W-10 được kiểm khi chặn mạng ngoài nên không nhận ảnh fallback font làm bằng chứng nạp Be Vietnam Pro.

## 3. W-09 — đóng hai Required

**R-W09-1 đóng.** Final đánh dấu terminal trên đúng request cùng lúc cập nhật UI. Request mới được nhận;
callback SSE, usage, catch và finally cũ chỉ được đổi trạng thái khi còn là request hiện tại.
Không đổi client_turn_id khi retry. Năm ca gồm usage cũ thành công/lỗi, EOF trễ/lỗi đuôi và usage về đảo thứ tự đều đạt;
chạy trên hook cũ đều fail assertion POST count, không lỗi setup. Bỏ guard usage cũ có một assertion fail.
Browser giữ phản hồi usage thật rồi gửi câu tiếp: **hai POST/ID khác nhau, câu nguyên vẹn, SQL turn 24→26**;
usage cũ về trong lúc lượt mới stream không mở khoá sai.

**R-W09-2 đóng.** Adapter chuyển `owner`, `cache_only` và `allow_spend` đúng lời gọi xuống core;
không còn ép mọi tool thành cache-only. Probe mặc định/False/True và quyền chi chứng minh tool thường sinh đúng một bài khi được phép,
không cho chi thì 0 lần gọi; focus hit/miss vẫn cache-only, không sinh ngầm. Browser từ cache rỗng **0→1**, fake lecture calls **1→2**.
Quyết định sinh/cache, retry và hạn chi nội dung thuộc core; web chuyển hợp đồng và bảo vệ quyền/DTO/HTTP.
Trần nội dung dùng chung là theo ngày của **toàn hệ thống**, không phải mỗi lộ trình; cache không xoá sau mỗi ngày.

Đối chiếu 230 hash bằng chứng và 750 hash nguồn của hồ sơ mới, không lệch. Bốn mutant mới có SHA nguồn/phục hồi khớp;
không gán các mutant lịch sử thành đã chạy lại trên HEAD mới. Các phần quyền/idempotency/DTO/session/renderer đã nhận giữ nguyên.
Thư viện chỉ đọc và preview đã có được tái dùng cho W-10, chưa thay toàn bộ tạo quiz/nộp/chấm/tạo tài liệu.

## 4. W-15 — nhận dựng thật, ghi đúng chi và giới hạn

Các phê duyệt mới được nhân viên trích trong [chỉ thị R5](w15-evidence/r5-20261025/owner-authorizations.md)
và [báo cáo retry](w15-phan-tich-timeout-va-retry-2026-10-25.md), gồm:

> tôi có duyệt tiền, phân tích tiep tuc trien khai

> nếu cần chi tiền tìm lỗi thì cứ chi

> bạn chạy lại thử luôn đi tôi duyệt tiền

Đây là provenance từ phiên nhân viên, không phải tin duyệt mới trong phiên điều phối này.
Đã đối chiếu plan/approval trước chạy, đúng PDF SHA/HEAD/pipeline/profile/DB/reference; grant consume một lần.
Nhận thay đổi opt-in trusted operator `retry_unknown_within_cap=true` theo chỉ thị để core tự retry.
Backend không thêm vòng retry: giữ reserve của attempt thiếu usage thành unknown, mọi dispatch vẫn kiểm
`known + unknown_upper + held + reserve <= cap`. Mặc định cũ chặn unknown; thiếu/sai boolean/profile/grant vẫn từ chối.
Web thường không có cờ HTTP để bật quyền này. Kết quả core thành công được giữ; còn attempt thiếu usage thì usage_complete=false.

| Lượt | Kết quả | Known USD theo profile demo | Unknown upper USD |
|---|---|---:|---:|
| Doc-6 bootstrap | succeeded, 334 request; web cache-only sau đó 0 call/0 USD | 0,12040340 | 0 |
| Candidate đầu | failed | 0,01241680 | 0,3890176 |
| Chẩn đoán | succeeded, 2 request | 0,00008380 | 0 |
| Candidate cấu hình 8 | succeeded, 1.616 request | 0,68726825 | 0 |
| Probe embedding 100 | succeeded, 101 request | 0,00292960 | 0 |
| Mixed 100 cũ | failed ở embedding A6 | 0,46637390 | 0,0248832 |
| Candidate mới theo core retry | succeeded, 1.637 request | 0,67933555 | 0 |
| **Tổng các lượt đã kiểm** | | **1,96881130** | **0,4139008** |

Tổng cận trên **2,38271210 USD**, dưới 4 USD. Không gọi unknown là 0 hoặc tiền chắc chắn đã thu.
Profile `owner-demo-embedding-token-20261025` dùng giá giả định 0,15 USD/triệu input token embedding,
**embedding_billing_verified=false, chưa đối soát hóa đơn**. Bảng là số theo profile và usage ghi nhận, không xác nhận giá SKU online.
Meter delta là chi build duy nhất; trace counted_in=build không cộng lại. SQL lượt mới 0,679336 USD khớp làm tròn sáu chữ số.

Lượt mới tại code `bd05c1b` mất **633,92 giây (10 phút 34 giây)** tính cả prepare/ADC/HTTP/worker;
graph v8, **16 module / 104 khái niệm học / 14 formula refs / 33 ảnh hợp lệ**, module và sequence phủ đúng một lần,
hard requires là DAG/đúng topo, retrieval fingerprint khớp. Đã kiểm read-only DB UUID: một claim, một attempt, một course ready, approval finished.

| Bước | Generation / embedding dispatch | Known USD | Wall giây | Khoảng chờ embedding giây |
|---|---:|---:|---:|---:|
| doc_reading | 0 / 0 | 0 | 3,1704 | 0 |
| concepts | 604 / 515 | 0,47390550 | 501,6158 | 122,0474 |
| graph | 111 / 303 | 0,20404855 | 99,9914 | 16,3010 |
| learning_prep | 0 / 104 | 0,00138150 | 6,8321 | 6,0235 |

1.635 HTTP 200 và hai **429 generation**, cùng payload sau retry có 200. Peak theo bước 100/49/54;
core tự giảm tải, không chứng minh 100 generation đồng thời hoặc giải thích được 81 timeout embedding của lượt cũ.
Không mở nghiên cứu/trả phí thêm vì chủ dự án đã chốt dùng retry của core. usage_complete=false được giữ nguyên dù unknown mới bằng 0.
Thời gian là quan sát của một lượt, có chồng thời gian chạy test ở đoạn đầu; không dùng làm benchmark kiểm soát.

Doc-6 được dựng trong kho riêng dưới doc_id từ SHA, graph v8; **2 module/15 khái niệm**, web đọc lại cache với 0 call/0 USD,
course ready và Mailer console báo xong. A9 doc-6 có cảnh báo đồ thị thưa và fallback document_order; không gọi đó là gate nội dung đạt.
Candidate mới có A9 passed=true. Các tên module còn vài tên ghép hoặc số đầu mục; đây là ghi chú chất lượng, không sửa thuật toán Pha A trong nghiệm thu web.
Báo cáo đã đọc course/roadmap/progress qua HTTP; chưa có lượt đọc bài giảng thật trên cuốn mới để chấm chất lượng, mục này không chặn W-15 theo vé.

**Phạm vi được nhận:** nối backend/worker vào core, kiểm cache/identity, đường course-ready/console mail và số chi/thời gian.
SMTP và Cloudinary trong harness vẫn giả; ảnh nguồn HTTP 29 byte không là ảnh PDF render thật. 33 ảnh artifact đã được verify riêng.
Không nhận đây là triển khai production, không nhập DB/artifact của các lượt riêng vào kho chung hoặc đổi fixture/alias phát triển.

**Đề xuất để sẵn, chưa bật:** `system_daily_build_max_usd=5` USD/ngày toàn hệ thống,
`build_monthly_max=3` **lượt dựng có chi/tài khoản/tháng**. Giá trị tháng là số lượt, không phải USD.
Căn cứ tham khảo: cuốn 52 trang mới khoảng 0,68 USD theo profile demo, vẫn cần dự phòng lỗi/unknown.
Đây là đề xuất cho Claude/chủ dự án, không thay cấu hình demo mặc định tắt và không cấp quyền chạy thêm.

## 5. Thiết kế — D-R6-01 trước khi nhận mẫu W-10

Mẫu `w10_quiz_screens.html` dòng 543/551/554/645 gắn “Tạo ở đây” với origin=button,
“Tạo ở nơi khác” với origin=assistant. Sai [Pha B2 mục 4](../doc/pha-b2-spec.md):
`here` theo home_scope giải ra module hiện tại; `elsewhere` là tạo nơi khác nhưng node_ids giao module đó.
Nguồn tạo bằng nút/trợ lý là thuộc tính riêng, không quyết định nhóm.

Phản chứng trình duyệt dùng hai record giả có origin chéo với nơi tạo: assistant tạo tại module A phải ở here;
button từ roadmap về A phải ở elsewhere. **Tab here hiện tại chọn nhầm record button**; control lọc group trong bộ nhớ đạt cả hai tab.
Không sửa tệp sản phẩm/nhân viên. Cần sửa label/filter/fixture/report và thêm guard hành vi; không chỉ kiểm có ID tab.
Web dùng group do core list_library trả về, không chép thuật toán suy module từ prototype.

61 test/CSS guard mới và công thức 12 cấu hình có giá trị, nhưng không bảo vệ nghĩa của bộ lọc.
Ghi chú chọn 6 module: mẫu hiện cảnh báo nhưng nút còn bấm được; đây là mẫu tĩnh, chưa là bằng chứng chặn provider ở W-10.
W-10 phải kiểm 6 module→scope_too_large/0 model call ở backend, và UI báo thu hẹp.

Báo cáo thiết kế W-23 hiện chứng minh **soát source React**, ảnh do script chụp **preview HTML**.
Chưa có bảng ảnh React/HTML cùng cỡ màn và video tương tác để nhận W-23 theo tiêu chí vé.
Không biến tuyên bố “12 cấu hình React đạt toàn diện” thành nghiệm thu runtime; cần đính chính phạm vi và bổ sung cặp ảnh thực.
W-08 chức năng đã đạt giữ nguyên; có thể tái dùng bằng chứng browser điều phối nếu ghim đúng SHA nguồn, không chạy lại LLM.
Toàn W-23 tiếp tục chờ W-10, không cần Cloud Figma.

## 6. Đợt việc tiếp và giao tiếp

[Lời giao riêng ba nhóm](lenh-giao-viec-ba-nhom-lan6-2026-10-25.md), mới soạn để chủ dự án chuyển, chưa gửi phiên bên ngoài.

| Nhóm | Lát việc | Điều kiện kiểm |
|---|---|---|
| Web | W-10: quiz→submit/chấm; tài liệu trực tiếp→xem/tải; thư viện đúng group | Quiz public không lộ đáp án, đảo thứ tự đúng, owner/nộp nguyên tử; ≤5 module, 10 tài liệu/giờ; PG/React/browser 0 USD |
| Lõi | Backend W-16 trên nền usage-1/GET me/usage hiện có | Ngày/tháng Việt Nam, cộng xuyên khoá, tách personal/shared/build, không USD cho người thường; không làm lại phần W-09 đã đúng |
| Thiết kế | Sửa D-R6-01 trước, cùng web đối chiếu W-08/W-09 rồi W-10 | Fixture nguồn tạo chéo với nơi tạo, ảnh React/HTML cùng cỡ, bàn phím/hiệu ứng/reduced-motion; không sửa chéo React |

Core W-16 chỉ nhận mốc backend; toàn W-16 còn trang/dải React do web làm sau W-10. W-17 chờ W-16;
W-19 chờ W-10; các vé W-04/W-12/W-18/W-20 vẫn chưa hoàn tất, W-21 triển khai chưa mở.
SA-67 document-3 và SA-68 quiz-3 đã ở main, W-10 không chờ Claude cài lại. Claude giữ làn SA/SA-61;
Vertex vẫn dùng cho tới khi chủ dự án yêu cầu đổi. Không tự ghép SA-61 hoặc bật transport khác.

Đã chép thường 3.144 tệp fixture sáu cuốn vào từng cây kiểm và candidate PDF đúng SHA, không link/learner store/tập giữ lại.
Giữ mọi worktree/artifact/snapshot/ZIP/PDF và DB dựng thật; không dọn, không đụng tmp/t01a-clean-ff797eb.
Sáu tệp dở của phiên khác giữ SHA. Hai lượt helper cộng chi đầu chỉ thiếu tên budget-requests.jsonl của diagnostic/probe,
đã giữ log thất bại và sửa reader đọc đủ tên, tổng assertion giữ nguyên; không phải lỗi sản phẩm hoặc chi bị bỏ.
Hai lượt chuẩn bị đầu bị Git owner guard trước khi chạy lệnh chính được giữ riêng; không tính là test ứng dụng đỏ.
[Manifest](coord-ba-nhom-lan6-evidence-2026-10-25/manifest.json) ghim hồ sơ nguồn/bản lưu và các native exit.
Sau commit hồ sơ local lần 6, mở lại cửa SA/cổng toàn repo; nếu main đổi trước ghép phải nhận main và kiểm lại.
