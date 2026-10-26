# Nghiệm thu ba nhóm lần 7 và kế hoạch tiếp — 2026-10-26

## 1. Kết luận

| Nhóm | Mốc được soát | Phán xét | Việc tiếp |
|---|---|---|---|
| Web | `fa346c95aafb90ff9273df947b07e093f19d3fb4` | **W-10 chưa đạt, chưa ghép:** hai Required có phản chứng | Sửa admission tài liệu xuyên nguồn tạo và phản hồi nộp quiz cũ; sau nghiệm thu mới React W-16 |
| Lõi | `d1bf42b274c8015fcfdc09b861f5f9a7edfecadb` | **Nhận mốc backend W-16**, ghép local `c5b4f5f`; toàn vé còn mở | Backend W-04 trong nhánh/worktree riêng, không sửa phần web đang làm |
| Thiết kế | `26e4a9adc66410679b616b76dff9d5f1522a0d0a` | **Nhận mốc mẫu W-10/sửa D-R6-01**, ghép local `c5b4f5f`; W-23 chưa đạt | Bổ sung guard thực thi JavaScript và bảng đối chiếu React/HTML đúng nguồn/trạng thái |

Chỉ commit local, **không push GitHub** theo quyết định chủ dự án 24/10. Không yêu cầu Cloud Figma.
Giữ các mốc W-09/W-15 và thiết kế đã nhận; không giao làm lại nền, pipeline, thương hiệu hay công thức.
Chi nhà cung cấp mới **0 USD**. Không chạy operator/ADC/provider, tái dùng grant W-15 hoặc mở tập giữ lại.

Nền main `b3c4426`; cửa kiểm `0177ab3`. Cây tích hợp ba nhóm `631cdc2e2b1c755ce01faa4558db8721981ce3dd`
được dùng cho focused/React/build/browser và phản chứng. Sau hai Required W-10, tạo riêng đỉnh
**`7e8c7d1ee05660b871e54b0ac10290913e1c189a`** gồm backend W-16, mẫu thiết kế và main hiện hành để chạy cổng toàn repo trước ghép.
Không thay nhánh nhân viên, không cherry-pick viết lại mốc hoặc đưa W-10 chưa đạt vào main.

## 2. Kết quả kiểm độc lập

| Kiểm | Kết quả | Bằng chứng |
|---|---|---|
| Focused W-10/W-16/thiết kế trên cây ba nhóm | **87 đạt**, PostgreSQL bắt buộc, native 0 | [JUnit](coord-ba-nhom-lan7-evidence-2026-10-26/runs/focused.xml), [lệnh/native](coord-ba-nhom-lan7-evidence-2026-10-26/runs/focused-exit.json) |
| React/build trên cây ba nhóm | **212 đạt**, build native 0 | [React](coord-ba-nhom-lan7-evidence-2026-10-26/runs/react.xml), [build](coord-ba-nhom-lan7-evidence-2026-10-26/runs/build-exit.json) |
| Browser W-10 HTTP/PostgreSQL/core thật; nội dung/media/mail giả | **12 cấu hình, 89 ảnh, 58 Axe, 217 bản ghi HTTP**; native 0 | [Audit](coord-ba-nhom-lan7-evidence-2026-10-26/browser/audit.json), [SQL/runtime](coord-ba-nhom-lan7-evidence-2026-10-26/browser/runtime.json) |
| Phản chứng admission tài liệu | **1 assertion fail / 0 setup error**: direct lần11 bị429 nhưng assistant sinh tài liệu thứ11 | [JUnit](coord-ba-nhom-lan7-evidence-2026-10-26/runs/rate-origin-repro2.xml), [quan sát HTTP/SQL](coord-ba-nhom-lan7-evidence-2026-10-26/http-repro/observed.json) |
| Phản chứng quiz nộp chậm sau Back | **1 assertion fail / 0 setup error** trên React thật/fetch giả; control scratch **10 đạt** | [bản hiện tại](coord-ba-nhom-lan7-evidence-2026-10-26/web-review/late-submit-current.xml), [control](coord-ba-nhom-lan7-evidence-2026-10-26/web-review/late-submit-control.xml) |
| Backend W-16, probe độc lập | **12 đạt, 7 mutant bị bắt**, không kết nối PG/provider trong probe | [review](coord-ba-nhom-lan7-evidence-2026-10-26/core-review/review.md), [summary](coord-ba-nhom-lan7-evidence-2026-10-26/core-review/summary.json) |
| Mẫu W-10, browser độc lập | **12 cấu hình đạt**; bản lọc origin cũ và điều kiện đảo đều bị bắt | [probe](coord-ba-nhom-lan7-evidence-2026-10-26/design-review/browser-probe.json), [script](coord-ba-nhom-lan7-evidence-2026-10-26/design-review/browser-probe.cjs) |
| Cổng đúng đỉnh ghép backend/thiết kế `7e8c7d1` | **2.735 Python đạt / 0 fail / 1 skip / 1 xfail; 203 React đạt**, build native 0 | [Python](coord-ba-nhom-lan7-evidence-2026-10-26/runs/safe-full.xml), [React](coord-ba-nhom-lan7-evidence-2026-10-26/runs/safe-react.xml), [build](coord-ba-nhom-lan7-evidence-2026-10-26/runs/safe-build-exit.json) |

Python luôn qua `scripts/w05_run_tests.py`, PG bắt buộc, basetemp mới, một cổng toàn repo tại một thời điểm.
Một skip là Cloudinary live không bật; một xfail là replay SA-55 cũ. Không bỏ test hoặc giảm assertion để xanh.
**Không chạy cổng toàn repo mới cho toàn W-10 sau khi xác định hai lỗi**; số 2.727 Python trong báo cáo nhân viên là lượt của họ,
không ghi thành lượt điều phối. Cổng toàn repo của điều phối chạy riêng đúng phạm vi được ghép.

Browser có 0 page error, 0 vi phạm Axe/tràn ngang/vùng bấm sai; 69 phép đo tương phản từ **5,84:1**.
Có **121 console event đã phân loại**: 58 probe font và 58 probe style của Axe bị CSP chặn, 3 lần401 dự kiến,
1 lần404 quyền người ngoài/thu hồi và 1 ERR_FAILED cố ý làm mất phản hồi nộp bài. Không nới CSP hoặc ghi console sạch.
Đã kiểm thêm 109 payload nội dung đã thu, không thấy trường riêng tư; **19 response body không lấy được sau điều hướng**,
nên không nhận native browser0 là bằng chứng riêng tư của mọi SSE. Harness dùng Promise.allSettled có thể bỏ qua assertion bị reject;
đây là ghi chú kiểm thử cần cải thiện, không là phát hiện lộ đáp án thực tế. HTTP/DTO tests là bằng chứng riêng.
[Đối chiếu browser](coord-ba-nhom-lan7-evidence-2026-10-26/browser-independent.json).
Đã kiểm độc lập DB browser đã gỡ, thread dừng và cổng8020 đóng: [kết quả](coord-ba-nhom-lan7-evidence-2026-10-26/runtime-cleanup.json).

Đã xem ảnh [quiz desktop](coord-ba-nhom-lan7-evidence-2026-10-26/browser/quiz-ready-1280-light.png),
[tài liệu mobile](coord-ba-nhom-lan7-evidence-2026-10-26/browser/document-view-390-light.png),
[thư viện mobile](coord-ba-nhom-lan7-evidence-2026-10-26/browser/library-here-390-light.png): trình bày rõ, bảng/công thức/nguồn và nhãn nhóm đúng.
Thanh sticky trong fullPage capture nằm ở đáy viewport đầu là đặc tính ảnh nguyên bản, không suy đó là lỗi layout lúc cuộn.
Thị giác và cổng xanh không thay hai Required chức năng.

## 3. W-10 — hai Required trước nghiệm thu

### R-W10-1: giới hạn tài liệu không bao phủ công cụ trợ lý

Spec chức năng mục7 và W-10 quy định documents_per_hour=10 **mỗi người**, không có ngoại lệ theo origin.
`DocumentRequests.admit` chỉ được gọi tại route tạo trực tiếp; callback make_document của trợ lý đi thẳng vào core.
Vì vậy có thể vượt hạn mức bằng cách đổi nguồn tạo. Đây là thiếu sót tích hợp W-09/W-10, không phải yêu cầu viết lại sinh/cache/retry ở core.

Phản chứng điều phối qua **HTTP/PG/core thật và model giả**:
1. Cùng người/cùng giờ tạo10tài liệu qua POST, cả10ready; bộ đếm admission=10.
2. POST trực tiếp lần11 nhận429/rate_limited, model vẫn10calls: control dương chứng minh guard trực tiếp có hoạt động.
3. Gửi yêu cầu qua route chat thật, tool make_document chạy: HTTP200, tài liệu **10→11**, model **10→11calls**,
   admission bucket vẫn10; SQL độc lập có thêm một document origin=assistant/status=ready.
4. Assertion yêu cầu modelcalls vẫn10 đỏ đúng chức năng, 0 setup error, 0 USD.

[Helper](coord-ba-nhom-lan7-evidence-2026-10-26/http-repro/test_coord_r7_rate_origin.py), [quan sát](coord-ba-nhom-lan7-evidence-2026-10-26/http-repro/observed.json).
Lượt đầu của helper chỉ thiếu import fixture w07, được giữ và không tính làm phản chứng; thêm import rồi chạy lại, không đổi assertion.
Reviewer còn có probe offline đi đúng callback/core, cùng kết quả 10→11.

Sửa bằng **một admission tần suất web dùng chung cho cả nút và tool**, đúng actor, xuyên khoá, tránh tính hai lần.
Giữ core quyết định sinh/cache/retry/trần tiền; không chép use case hoặc mở chi để vá. Bổ sung test hai thứ tự button→assistant và ngược lại,
khác khoá/cùng người, người khác tách và hai runtime tranh lượt cuối; lần bị từ chối không gọi model hoặc tạo document ready.
UI/tool báo lỗi phù hợp, không biến lỗi giới hạn thành lỗi nội bộ hoặc làm hỏng lịch sử chat.

### R-W10-2: phản hồi nộp quiz cũ thay màn quiz mới

`ContentPages.tsx` trong submit() gọi setResult sau await mà không kiểm cid/aid/lần nộp còn là màn hiện tại.
Tái hiện bằng React/MemoryRouter thật, fetch giả chủ động giữ phản hồi: mở qa_2→qa_1, nộp qa_1,
bấm Back về qa_2 rồi mới trả kết quả qa_1. URL vẫn **/khoa-hoc/c/quiz/qa_2** nhưng heading thành “Kết quả quiz”,
câu hỏi qa_2 biến mất và kết quả qa_1 chiếm màn.

Ca mới **1 assertion fail/0 setup**; control có guard định danh trong scratch **10/10 đạt** gồm9ca cũ.
Không sửa mã nhân viên. [Review/nguồn](coord-ba-nhom-lan7-evidence-2026-10-26/web-review/review.md).
Sửa ranh giới request/điều hướng: phản hồi của attempt cũ không ghi result/error/sending/focus vào màn mới;
kết quả đã nộp vẫn bền phía server và mở lại đúng quiz được. Kiểm cả success/error cũ, đổi course/attempt,
Back/Forward và finally khi lượt mới đang xử lý; giữ các hồi quy reload, lựa chọn lúc stream và bàn phím đã nhận.

Những phần tốt được giữ, không giao làm lại: public DTO không đáp án/validation, owner/cuốn, ánh xạ option sau xáo,
nộp nguyên tử/idempotent, rollback progress, Markdown/GFM/KaTeX và nguồn an toàn, group theo core,
6module0call, tạo/lưu tài liệu khi đóng dialog, cache ngân hàng quiz.
Dependency remark-gfm4.0.1/MIT dùng riêng cho bảng tài liệu, lockfile khớp; renderer bài giảng/trợ lý không đổi mặc định.
Đã đọc README/license của package cài thực và soát ranh giới renderer, không lấy mô tả package thay test XSS/URL.

Reviewer đối chiếu **544 bằng chứng, 766 hash src/scripts, 52 hash frontend nguồn, 75 hash bundle,
493 thành viên ZIP thô và 12 mutation receipts** đều khớp. Các số2727Python/212React/browser nhân viên được ghim mã4d2f652;
fa346c9 chỉ thêm hồ sơ. Những số này không phủ hai ca ngoài ma trận vừa phát hiện.

## 4. Backend W-16 — nhận mốc, toàn vé vẫn mở

Dùng lại GET/me/usage và MyUsage, quota đã có. Projection gọi usage_rows với người/ngày/purpose,
loại counted_in=build và lọc ngày nửa mở **[đầu ngày, đầu ngày sau)**; quota tháng cũng nửa mở,
đếm counts_quota thay vì cộng USD. Không thêm migration hoặc sửa core/gateway/React.

Đã kiểm biên 16:59→17:00UTC, cuối tháng/năm/năm nhuận, xuyên khoá/tách người, shared theo toàn hệ thống,
trace/build tách, max=null khi demo tắt và DTO HTTP không khoá usd/cost ở mọi mức.
Probe reviewer dùng SQLite cô lập để chạy predicate/query quota thực, chỉ thích ứng cast PG;
12test đạt,7mutant đều có assertion fail/0 setup. **Đây không phải lượt PG của reviewer**;
13ca W-16 với PG thật nằm trong cổng điều phối trên đỉnh ghép. 115hash bằng chứng nhân viên đúng, không lệch nguồn từ7f98cf7 tới d1bf42b.

Nhận backend để web dùng sau W-10; **chưa đóng toàn W-16** vì còn trang và dải mức dùng React.
Mọi cost/ledger trong test là fixture tổng hợp, không phải khoản mới của W-15.
Trần build đề xuất5USD/ngày và3lượt/người/tháng vẫn chưa bật; không thay cấu hình hoặc cho quyền chi mới.
Lõi tiếp mốc backend W-04; web sở hữu frontend các vé, không viết màn tạm ở backend.

## 5. Thiết kế — nhận mẫu đúng, rút kết luận W-23 thiếu bằng chứng

**D-R6-01 đóng ở source:** data-group độc lập data-origin, hai tab lọc group; có đủ4fixture nguồn tạo chéo với nhóm.
Browser thực trên đúng tệp26e4a9a đạt12cấu hình (390/768/1280×sáng/tối×normal/reduced), tab chọn bằng bàn phím đúng record,
5→6module khoá nút/cảnh báo và về5mở lại; công thức cân bằng/MathML/cây truy cập/chỉ số dưới nhỏ và thấp hơn, không tràn ngang.
Thay hàm/onclick lọc origin cũ hoặc đảo === thành !== đều làm **hai assertion danh sách thực đỏ**.

Hai điểm trong hồ sơ nộp cần phân biệt:
- **D-R7-01:** ảnh R5 design-browser/w08-ready-390.png là **HTML**, producer mở file preview và chụp section,
  không phải React. Ảnh “ordinary-lecture-generated” là roadmap+chat, không phải màn bài giảng hoàn tất;
  lesson-768-dark là bài học có chat, không phải viewer nguồn như tên trạng thái trong bảng. Hai ảnh W-09 là React thật nhưng khác bố cục/trạng thái mẫu.
  **Rút tuyên bố “khớp hoàn hảo” và “nghiệm thu từng phần W-23”**; ghi đính chính điều phối ở đầu báo cáo nộp, giữ bản gốc bên dưới để truy nguyên.
- **D-R7-02:** 64unit hiện tại vẫn64pass khi đảo điều kiện lọc; test falsifiable chỉ kiểm biểu thức cục bộ,
  chưa chạy JavaScript của mẫu. Không nhận chúng là guard hành vi đã bảo vệ bộ lọc.
  Nhận mốc source vì **probe browser độc lập có thể chạy lại** đã chứng minh hành vi và bắt đúng hai bản sai;
  giao thiết kế thay/bổ sung guard chạy JS thật vào đợt kế tiếp, không giảm hoặc bỏ test đang có.

[Review](coord-ba-nhom-lan7-evidence-2026-10-26/design-review/review.md), [provenance ảnh](coord-ba-nhom-lan7-evidence-2026-10-26/design-review/w23-provenance.json).
Probe tĩnh chặn GoogleFonts nên đo được SegoeUI, không dùng document.fonts.check=true làm chứng cứ Be Vietnam Pro đã nạp.
Ảnh React W-10 được xem riêng ở mục2. Không ép dữ liệu mẫu y hệt nhưng mọi kết luận đối chiếu phải ghi đúng viewport/theme/state/nguồn/SHA.
W-23 còn mở, chờ W-10 đạt và đủ bảng đối chiếu/video thao tác thật; không cần Cloud/plugin/Variables/Present.

## 6. Kế hoạch tiếp và giao tiếp điều phối

[Lời giao ba nhóm](lenh-giao-viec-ba-nhom-lan7-2026-10-26.md), chỉ soạn để chủ dự án chuyển, chưa gửi phiên bên ngoài.

| Nhóm | Ưu tiên | Điều kiện xong |
|---|---|---|
| Web | Sửa R-W10-1/2, sau đạt làm React W-16 | Hai ca đỏ→xanh, PG/React/build/browser mới; W-16 hiển thị ratio/reset/ngân sách tắt đúng, không USD |
| Lõi | Mốc backend W-04: hồ sơ, đổi mật khẩu, logout-all | Mật khẩu sai không đổi; A đổi giữ A/hủy B; logout-all hủy A+B; tên1–60/CSRF/audit đúng, PG0USD |
| Thiết kế | Bổ sung guard JS thật và W-23 đúng nguồn/trạng thái | ===→!== phải đỏ; bảng cặp ảnh và video thật W-08/W-09, W-10 sau hai bản sửa, không sửa chéo React |

W-04 backend là lát riêng, không đóng toàn vé có giao diện. W-12/W-18/W-19/W-20 chưa hoàn tất;
W-17 chờ toàn W-16, W-21 triển khai chưa mở. Claude giữ làn SA/SA-61, Vertex giữ tới chủ dự án yêu cầu đổi;
SA-67/68 đã ở main, không còn chặn W-10. Không giao làm lại W-15 hoặc mở nghiên cứu/chi mới.

Hai cây kiểm chỉ nhận **3.144 tệp fixture chép thường** theo allowlist/SHA và candidate PDF có SHA riêng;
không link, learner store, livecache hay tập giữ lại. Giữ mọi worktree/artifact/snapshot/ZIP/PDF và DB W-15;
không đụng tmp/t01a-clean-ff797eb, không dọn tệp sinh từ test. Sáu tệp dở của phiên khác giữ SHA.
[Manifest](coord-ba-nhom-lan7-evidence-2026-10-26/manifest.json) ghim bằng chứng/native và hash nguồn/bản chuẩn hoá.
Sau commit hồ sơ local lần7, mở lại cửa SA/cổng toàn repo; main đổi trước ghép thì nhận main/kiểm lại theo quy trình.
