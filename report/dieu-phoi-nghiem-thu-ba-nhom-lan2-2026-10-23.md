# Nghiệm thu ba nhóm lần 2 — 2026-10-23

Codex kiểm độc lập theo yêu cầu chủ dự án. Đợt trước ở [biên bản buổi sáng](dieu-phoi-nghiem-thu-w11-w15-w24-va-ke-hoach-2026-10-23.md).
Chi dịch vụ ngoài mới **0 USD**. Không sửa mã sản phẩm, không xoá dữ liệu/worktree; test review và phép phá chỉ ở bản kiểm riêng.

## 1. Mốc và phán xét

| Nhóm | Mốc đã soát | Phán xét |
|---|---|---|
| Web W-11 | `253874bbd83e4224477542928b4a3ef9344db93a`; mã bản vá `0a72f31`, cổng tác giả `33f9c25` | **Đạt nghiệm thu**, đã sửa Required mất next, full gate và browser độc lập xanh trên `b625752` |
| Lõi W-15 | `6627c00b5b86436fba5d54a1659ca6d90d6559a6`; mã mới `dba19e508631cb2d81f6c69b0a8709d13835ef9b` | **Đạt mốc chống cộng trùng chi/test tương thích port**, cổng chung xanh; không đóng toàn W-15 |
| Thiết kế W-24 | `7a522e5b5a703c83b0bce761483067040991d365`; checkpoint `d72993ed0a698e36398bd6339c2f8a0a63d92515` | Cả hai gói **cần sửa**, giữ ngoài main; đóng các lỗi cũ đã chứng minh, không giao lại |

Main ban đầu `5d8be6f`; commit điều phối `d74bea9` nhận phản hồi SA-62, ADR 0024 và đề nghị giữ cửa sổ ghép.
Worktree mới `tmp/coord-r2-acceptance-20261023`, mốc tích hợp web+lõi **`b625752d929efd1a94f0975586a9c80296966aa7`**, merge không xung đột.
Mốc này không chứa SA-62/SA-63 hoặc gói W-24 chưa đạt. Không tự ghép mã làn SA thay Claude.

## 2. Kiểm độc lập phần được xét ghép

### Web W-11

Đã đọc lại bản vá và luồng xác thực: `switchTarget` dùng `next` đã sanitize, cả header/footer và view transition giữ cùng đích.
Không mở redirect ngoài; ký tự biểu tượng đổi theme thành SVG để Axe không còn incomplete, không thay palette/font/motion.
Backend transaction/token/migration không viết lại so với mốc đã soát trước.

- Chạy độc lập **32/32 React test đạt, native exit 0**: repro gốc 10 ca và bản mở rộng 22 ca, gồm hai chiều × header/footer × có/không transition, 12 next nguy hiểm.
- Đối chiếu **hai manifest nguồn 639/639 mỗi bộ**, **318/318 tệp evidence** khớp SHA-256; mã/test/script không đổi từ mốc cổng tới mốc bàn giao.
- Hồ sơ tác giả: **2.292 Python đạt/1 skip Cloudinary live, 143 React/build**, browser **48 ảnh/16 Axe tại 1280 px/113 HTTP**, 8 luồng đổi form thật.
- Bốn luồng browser thường xác nhận native transition thực sự được gọi; bốn reduced-motion xác nhận không gọi. SQL kiểm link dùng đúng 8 lượt cho 8 tài khoản mới.
- Tám backend mutation và 12 unsafe-next mutation có failure assertion, không setup error, ghi nhận SHA nguồn phục hồi.

Các số hồ sơ tác giả là số được đối chiếu, không nhận thành lượt browser/cổng độc lập của điều phối. Lượt độc lập trên mốc tích hợp ghi bên dưới.
Optional giữ từ trước: whitelist console 401 nên gắn route/stage khi mở rộng harness; không phải Required chặn bản vá này.

### Lõi W-15

Phần mới chỉ năm tệp `src/web/`: hai test no-port dùng `PipelineWithoutStorePort` giả để vẫn chặn trước constructor/claim/provider,
không khẳng định pipeline lõi thật mãi không có port. Không phải chỉ preflight/tài liệu.

`PostgresPhaseBStore.append_usage` giữ nguyên raw trace trong `extra`; với đúng `counted_in="build"`, cột typed tiền/token bằng 0.
Receipt `purpose=build` ghi tổng meter một lần. Dòng không cờ/cờ khác giữ hành vi trước; không migration hoặc sửa lịch sử.
Đọc `usage_rows()` để đối soát/spend guard vẫn nhận raw. Bảng chi đọc raw phải lọc trace; không lấy tổng raw thành tiền provider.

- **229/229** tệp manifest mới khớp SHA và kích thước qua Git blob; sau `dba19e5` không đổi mã/test/script/design.
- **15/15** mutation tác giả có native exit 1, assertion, không setup error và hồ sơ phục hồi nguồn.
- Điều phối thử bỏ nhánh triệt cộng trùng ở bản kiểm: **1 assertion fail, 0 setup error, native exit 1**, nguồn phục hồi cùng SHA.
- Hồ sơ test tổng meter `.003`, hai trace raw `.001` mỗi dòng nhưng typed 0 là **số fake**, không phải tiền nhà cung cấp.
- Rà **92 manifest** trên bản sao được phép: doc-6 nguồn alias `doc-6`/v29 khác ID upload hash; ứng viên 52 trang chưa thấy hash trong bộ sáu cuốn.
  Chỉ kết luận miss định danh trong phạm vi đã kiểm; không suy ra model/embedding cold-cache toàn cục, chưa có dự toán đo được.

**DailySpendGuard:** chỉ tính purpose lecture/quiz/assistant/document; trace module_title/embedding của dựng không thuộc trần Pha B đó.
Test raw trace purpose lecture kiểm đúng ca lecture, không chứng minh naming/embedding của build đã bị trần này chặn. Web có guard build riêng.

### Cổng trên mốc tích hợp

Đã chép **3.144 tệp** đúng allowlist/SHA nguồn và đích, không liên kết/live store/tập giữ lại.
React **143/143 đạt**, build native exit 0 trên `b625752`.
Python/PostgreSQL toàn repo **2.296 đạt, 0 fail/error, 1 Cloudinary live không bật**, native exit 0 trên đúng `b625752`.
Pytest 582,72 s, wrapper 600,91 s; main vẫn `d74bea9` khi chốt cổng, mã/test/script của bản kiểm không thay đổi.
Đây là thời gian cổng kiểm, không phải thời gian dựng một cuốn.

Browser HTTP/PostgreSQL độc lập trên chính `b625752`: **48 ảnh, 16 Axe ở 1280 px, 115 HTTP**, 6 nhóm assertion và **8 ca auth-return** đều đạt,
native exit 0, 123,98 s. Không unexpected console/page error/failed request. Không gọi tất cả 48 ảnh đều được Axe.
Auth/CSRF/Argon2/Course/Sharing/Gateway/PG thật, FakeMailer và provider/ADC/SMTP/Cloudinary bị chặn; không giả API để làm UI xanh.
SQL kết nối độc lập: auth-return link dùng đúng 8 lượt/8 tài khoản, link chính một lượt, còn owner và một hàng Pha B riêng,
không có cột token thô, đủ audit tạo/thu hồi/tham gia/gỡ/rời. Test remove/leave/rejoin giữ tiến độ riêng.
Điều phối kiểm độc lập DB UUID đã biến mất và cổng 8011 đã đóng sau harness. Đã mở xem ảnh auth 390 tối và 1280 sáng; bố cục rõ, không hồi quy thị giác.

**Quyết định ghép:** nhận đúng `b625752` chứa W-11 và mốc W-15 nêu trên. Không nhận W-24, SA-62 hoặc SA-63 trong lần ghép này.

**Ghép `e85427a` và đã đẩy GitHub.** Ngay trước lệnh ghép, Claude commit tài liệu `9ee69ce` (ADR 0025/spec lecture-3) trên main;
điều phối chỉ thấy sau khi ghép nên chưa nhận main mới/chạy lại cổng theo đúng trình tự trước ghép. Đây là thiếu sót quy trình, không bỏ qua trong biên bản.
Diff mã/test/script/design giữa `b625752` và commit ghép rỗng. Đã nhận main vào worktree kiểm tại **`817f487639880e2ca052fbe28ad2d8423c615ace`**
và chạy lại toàn cổng Python/PostgreSQL, React/build với basetemp/log riêng để kiểm chứng sau ghép.
**Kiểm chứng sau ghép đã xanh:** **2.296 Python đạt/0 fail/error/1 Cloudinary live không bật, 143 React/build**, mọi native exit 0 tại `817f487`.
Pytest 801,27 s/wrapper 815,67 s; giữ cả hai lượt cổng. Không sửa hoặc nới test để đạt; một skip có sẵn được đối chiếu tên trong JUnit.
Browser trên `b625752` giữ giá trị vì mã/harness/design giống hệt; không chạy lại browser chỉ vì tài liệu đổi.
Commit `cbad648` tiếp theo chỉ đổi một dòng kế hoạch SA-21, không thay mã; không ghép thêm sản phẩm ở đợt kiểm chứng này.

## 3. W-24: nhiều sửa đúng, ba nhóm Required còn lại

Đã chứng minh sửa đúng và **không giao lại**: list link chỉ sáu ký tự, copy ở vùng tạo mới; wording dữ liệu/quota/huỷ đúng;
bỏ lời hứa OCR; plugin normal/fallback khớp **37 tên × 2 mode = 74/74 giá trị**; các nút cũ đủ 44 px, chữ không tràn.
Chạy **45 test ở head, 40 test ở checkpoint**, native exit 0; **18 cấu hình Chromium** W-08/W-09/W-10 ×390/768/1280×sáng/tối,
0 tràn trang/0 lỗi JS/0 nút-link dưới 44 px. Đã mở xem ba ảnh mobile thật. Đây là local mockup, chưa phải ứng dụng backend hoặc Figma Cloud.

Required còn lại:

1. **Plugin nuốt lỗi tạo Variables:** bốn catch rỗng còn nguyên. Ép tạo `color/primary` lỗi thì script vẫn trả thành công, còn **72/74 giá trị**, không log lỗi.
   Có cả ở `d72993e` và head; không chuyển Required cũ thành ngoại lệ để nhận checkpoint. Cần thống kê attempted/created/failed và assertion khi tạo thiếu.
   Guard hiện chỉ dò vài chuỗi: đổi alpha thật `0.14→0.99` vẫn xanh, native exit 0. Phải so hành vi output 74 giá trị, không dựa chuỗi ở nơi khác.
2. **Chat sai hợp đồng mức dùng:** “còn 24 lượt”/“0/30 lượt hôm nay” không tồn tại trong `usage-1`.
   Dùng `used_ratio`, `limited`, `resets_at`; tần suất 10 lượt/phút là luật khác. Bỏ tên công cụ và JSON arguments nội bộ khỏi giao diện người học;
   hiện tiến trình bằng lời dễ hiểu.
3. **Checklist vượt bằng chứng:** anchor email pending/xoá khoá sai; form gửi mail không thay danh sách lời mời chờ; phiên chat mới phải có màn rỗng riêng.
   Viewer hiện là placeholder có điều khiển, không được gọi là ảnh nguồn và các thao tác đã hoạt động. Đồng bộ số 45/40 test với mốc tương ứng.

Không có native export/receipt/binding manifest/video Present mới trong gói. Đợt này không có Figma MCP để đọc lại,
**không tuyên bố số đối tượng Cloud hiện tại**. Receipt Cloud rỗng của lần trước là bằng chứng lịch sử có ngày, không phải đo mới.
W-22/W-24/W-23 vẫn mở; local prototype/plugin source không thay components/variants/token bindings/reactions thực.

## 4. Điểm chờ W-15 đã được Claude trả lời

**Không còn chờ xác định người làm/Pha A.** Claude nhận port bằng SA-62, agent của Claude cài và Claude nghiệm thu/ghép;
không cần phiên Pha A sửa use case. SA-62 `266dbdc` đã có mã, chưa vào main; hai test web từng đỏ đã được W-15 sửa tương thích ở mốc được soát này.
Sau khi phần web được ghép, Claude nhận main rồi chạy cổng và ghép SA-62 theo quyền của làn SA. Chưa gọi port là đã lên main trước bước đó.

Kiến trúc không đổi: graph/chunks/manifest/chỉ mục Pha A ở **kho tệp**; chỉ kho Pha B và sổ chi của đường web dùng PostgreSQL được tiêm.
Không đề xuất chuyển toàn artifact Pha A vào database production.

Sau SA-62 vào main, lõi kiểm default factory có port, pipeline thật với provider/ADC/JSON/SQLite bị chặn, PG xuyên connection độc lập,
identity/cache, callback/receipt/lease và nguồn usage duy nhất. Sau đó dry-run thật trên bản sao, không queue/course ready,
lập bảng số gọi/USD/phút/trần. Chỉ chạy có tiền sau chủ dự án duyệt đúng cuốn/lượt/trần; chưa có quyền chi mới.

## 5. Kế hoạch tiếp theo và đổi chính sách bài giảng

| Làn | Việc tiếp |
|---|---|
| Web | W-11 đã ghép: W-08 lecture-3, cổng cuối chờ SA-64 thay SA-63; W-09 answer-3 chờ SA-66, rồi W-10 |
| Lõi | Sau mốc trace/test tương thích ghép: phối hợp Claude ghép SA-62; kiểm toàn pipeline PG và dry-run 0 USD, chưa chạy cuốn mới có tiền |
| Thiết kế | Sửa ba Required còn lại, guard output/failure plugin thật; cập nhật W-08 theo lecture-3, rồi hoàn thiện Cloud và video Present |
| Claude | SA-62 nhận main có web tests tương thích; SA-64 thay SA-63, SA-65 ảnh trang, SA-66 answer-3; SA-61 trước lần đổi Developer API được yêu cầu |

**Quyết định mới nhất của chủ dự án là ADR 0025/lecture-3**, kế thừa chính sách luôn hiện/giữ chữ/báo lỗi của ADR 0024.
SA-63 dừng, SA-64 thay; không dùng thay đổi mới để bác thiết kế đã làm theo lời giao cũ.
Đã cập nhật W-08/W-10/spec giao diện: `body_md` Markdown/LaTeX bằng KaTeX, `sources` và khối Trong sách/nhãn `[Sx]`, `self_check` đáp án gập;
stream skeleton → delta{text} → final{lecture}/failure. Bỏ sections/bridge/item của lecture-2; chữ hiện ngay, validation chỉ admin.
Chưa có chữ dùng được thì failure.message và luôn Thử lại; lỗi sau delta đầu giữ chữ, ready + cat_ngan. SA-65 tạo ảnh trang công thức trong artifact,
không đổi kiến trúc DB. W-17 đọc log validation theo số đo mới, bảng chi loại trace counted_in=build để không cộng trùng.

**Cập nhật kế tiếp `a50955b`:** ADR 0026/spec trợ lý 3, SA-66 sau SA-64, thay answer-2 bằng answer-3 (`answer_md`, Markdown/LaTeX,
sources, delta; giữ graph_cards/artifacts/focus). Trần người học/ngày lên 1,00 USD; used_ratio vẫn là tỷ lệ, không phải số lượt/ngày.
Đã đồng bộ W-09 và spec chức năng theo quyết định, cổng cuối W-09 chờ SA-66. Claude đính chính độ trễ SA-60 là khởi tạo chứng thực mỗi lượt;
server giữ client khoảng 1,6 s trong bản thử của Claude, không phải số điều phối đo lại hoặc SLA mới. Không lấy 11,4 s làm mặc định cố hữu.
Giữ Vertex tới khi chủ dự án yêu cầu đổi cho demo, không tự đổi theo ngày; SA-61 phải ghép trước lần chuyển Developer API.
W-12/W-04 có thể xếp sau nếu có thêm người; không tách phiên web duy nhất khỏi đường học W-08→W-09→W-10.
W-23/W-21 chưa đủ điều kiện nghiệm thu tổng.
Kế hoạch Pha B `f346e71` dự kiến tiếp SA-67 tài liệu/SA-68 quiz sau bài giảng/trợ lý; trước khi mở W-10 phải đối chiếu đặc tả/mốc mới khi có.
Đây là kế hoạch tiếp, chưa phải mã hay hợp đồng đã được nghiệm thu; không tự đổi quiz/document trong đợt này.

[Lời giao ba nhóm lần 2](lenh-giao-viec-ba-nhom-lan2-2026-10-23.md) đã soạn để chủ dự án chuyển; chưa nhắn phiên nhân viên bên ngoài.

## 6. Bằng chứng và an toàn dữ liệu

Bộ bằng chứng tại `report/coord-ba-nhom-lan2-evidence-2026-10-23/`, có manifest SHA, lệnh/native exit/mốc, test đỏ thật,
các số chẩn đoán chưa đạt và ảnh/video thật. Những bằng chứng chính:

- [Tổng hợp sau kiểm chứng](coord-ba-nhom-lan2-evidence-2026-10-23/summary-final.json), [SHA-256 từng tệp](coord-ba-nhom-lan2-evidence-2026-10-23/manifest.json).
- [Python kiểm chứng sau ghép](coord-ba-nhom-lan2-evidence-2026-10-23/gate-final/full-final.xml), [native exit/mốc/lệnh](coord-ba-nhom-lan2-evidence-2026-10-23/gate-final/full-final-exit.json), [React](coord-ba-nhom-lan2-evidence-2026-10-23/gate-final/react-final.xml).
- [Browser/Axe/HTTP và 8 auth-return](coord-ba-nhom-lan2-evidence-2026-10-23/browser/audit.json), [SQL runtime](coord-ba-nhom-lan2-evidence-2026-10-23/browser/runtime.json), [video auth-return](coord-ba-nhom-lan2-evidence-2026-10-23/browser/auth-return.webm), [kiểm DB/cổng đã dừng](coord-ba-nhom-lan2-evidence-2026-10-23/gate/browser-cleanup.json).
- [32 ca auth độc lập](coord-ba-nhom-lan2-evidence-2026-10-23/w11-review/auth-return-independent-green.xml), [kiểm manifest W-15](coord-ba-nhom-lan2-evidence-2026-10-23/w15-review/review.json), [trace mutation/restore](coord-ba-nhom-lan2-evidence-2026-10-23/gate/trace-mutation.json).
- [Review W-24](coord-ba-nhom-lan2-evidence-2026-10-23/w24-review/review.md), [output/fault plugin](coord-ba-nhom-lan2-evidence-2026-10-23/w24-review/plugin-contract-observations.json), [mutation alpha lọt guard](coord-ba-nhom-lan2-evidence-2026-10-23/w24-review/plugin-alpha-mutation.xml).

Phân biệt rõ số tự chạy, hồ sơ tác giả đã đối chiếu và phần chưa kiểm. Không nhận diagnostic exit0 thành conformance pass.
Raw ở scratch được giữ; bản lưu chuẩn hoá UTF-8/LF, so giá trị JSON/số ca JUnit, ghi cả SHA raw và archive.
Sáu tệp đang sửa của phiên khác được giữ nguyên, không stage; không nhập cache/live hoặc tập giữ lại, không dọn worktree/snapshot/ZIP.
