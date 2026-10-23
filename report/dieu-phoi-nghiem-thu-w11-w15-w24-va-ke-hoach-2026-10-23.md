# Nghiệm thu W-11, mốc W-15 và W-24 — 2026-10-23

Người điều phối: Codex. Chủ dự án yêu cầu phân tích, kiểm thử độc lập, nghiệm thu và lập kế hoạch cho ba nhóm.
Chỉ ghi nhận phạm vi đã chứng minh; chưa có quyền chi mới. Mọi lượt kiểm mới trong đợt này dùng mô hình/embedding/mail/media giả, chi dịch vụ ngoài **0 USD**.

## 1. Kết luận và các mốc

| Nhóm | Mốc bàn giao | Kết luận |
|---|---|---|
| Web | `85397092ed10bffe2db3bda96d2db6a6d2759c48`, mã đã chạy `b9b5e6817390f8189813707095a04eeac16df95a` | **W-11 cần sửa một Required**, chưa ghép: đổi form xác thực làm mất đích link mời |
| Lõi | `a8bb295df7a01e9c6c9aa79f49561e9692189c23`, mã đã chạy `446caba3e3ab608ad1ad56108fabac6e6c539398` | **Đạt mốc adapter/test 0 USD**, cổng độc lập xanh trên `eea5472`; trạng thái ghép ghi mục 3. **Không đóng toàn W-15** |
| Thiết kế | `16e95c146b8d0a07ad53208b3b084aa8628660f1` | **W-24 cần sửa năm nhóm Required**, chưa ghép gói mới; W-22/W-23 còn mở |

Main nền `dee87cc`; commit điều phối `605f6a3` ghi đề nghị cửa sổ kiểm và port trước khi tạo worktree.
Worktree độc lập W-15 `tmp/coord-w15-acceptance-20261023`, mốc tích hợp **`eea547291d1276a92f39a9f2d5f1c2fdd887e827`**, không xung đột.
Không thay nhánh thư mục chung, không sửa mã sản phẩm để làm xanh. Các test tái hiện mới nằm riêng trên nhánh review.

## 2. Web W-11: gần hoàn tất, lỗi nằm ở nhánh đổi form

### Required W11-R1

`src/web/frontend/src/Auth.tsx:258–263,319,334` dùng `switchTarget` chỉ gồm `/dang-nhap` hoặc `/dang-ky`, bỏ query `next`.

Tái hiện: `/join/<token>` → đăng nhập → bấm **Tạo tài khoản** ở header hoặc cuối form → đăng ký xong về `/khoa-hoc`.
Chiều đăng ký → đăng nhập mắc cùng lỗi. Người học mất màn hình tiếp nhận lời mời dù xác thực thành công.
Mã này có từ trước nhưng nằm trong luồng bắt buộc của W-11; bộ kiểm bàn giao chưa đi qua nhánh đổi form.

Đã chạy **10 ca Vitest độc lập** trên đúng mã sản phẩm `8539709`: **8 assertion fail, 2 control pass, 0 setup error, 0 skip, native exit 1**.
Tám ca gồm hai chiều × header/footer × có/không view transition; mọi ca thất bại đều hoàn tất xác thực rồi sai đích `/khoa-hoc`.
Hai ca xác thực trực tiếp từ link mời đạt, nên đây không phải lỗi mock hoặc lỗi tổng quát của form.
Commit review `3f3e923b178082742f3d0135919dccd356dd8bc2` chỉ thêm test; không sửa `Auth.tsx`, không ghép/push nhánh review.

Cách sửa giao nhóm web: giữ `next` đã kiểm tra trên cả `Link.to` và `navigate` của transition; giữ chặn redirect ngoài.
Thêm regression RED→GREEN, kiểm browser qua link mời thực với PostgreSQL, nhận main mới rồi chạy lại cổng trước khi bàn giao.

### Những phần được xác minh bằng đọc mã và đối chiếu hồ sơ

- Token ngẫu nhiên 32 byte, canonical; DB chỉ lưu hash/đuôi, toàn URL chỉ hiện một lần. Danh sách, log và referrer có guard.
- Join khoá link rồi khoá course; membership, lượt dùng và audit cùng transaction. Test tranh một lượt/hai link tranh chỗ thứ 200 kiểm bằng SQL độc lập; lỗi audit rollback.
- Revoke giữ thành viên cũ; remove/leave chặn truy cập nhưng giữ dữ liệu học riêng. Giới hạn quyền chủ khoá/thành viên đúng phạm vi.
- Một migration `w11_0007` nối `w14_0006`; route riêng tư được thêm vào inventory, không miễn route mới.
- **625/625 hash nguồn và 623/623 hash bằng chứng khớp**; mã/harness không đổi sau `b9b5e68`.
- Hồ sơ tác giả có JUnit **2.270 Python đạt/1 Cloudinary live không bật, 121 React đạt**, build thành công; **8/8 mutation** đỏ qua assertion, không setup error, SHA phục hồi khớp.
- Hồ sơ browser đúng **36 ảnh, 12 Axe ở 1280 px, 47 HTTP**; đã xem ba ảnh thật, bố cục rõ. Không coi 36 ảnh đều được kiểm Axe hoặc đều được soát thị giác thủ công.

Các số gate/browser cuối đoạn trên là **hồ sơ bàn giao được kiểm chứng**, không phải cổng toàn bộ do điều phối chạy lại trong đợt này.
Không chạy lại full gate cho một mốc đang có Required đã tái hiện; chờ bản sửa. Optional: thu hẹp whitelist console 401 theo route/stage trong harness khi mở rộng.

## 3. Lõi W-15: chỉ nhận mốc adapter/kiểm 0 USD

Đọc diff theo năm trục review, không thấy Required trong phạm vi adapter được tuyên bố.
Tám tệp mã/test/harness của nhánh giữ nguyên từng byte trên mốc tích hợp `eea5472`;
**265/265 tệp manifest bằng chứng khớp SHA-256 và kích thước** qua Git blob, không dựa line ending của checkout.

Điều đã làm đúng:

- Fake vẫn mặc định; cấu hình real ép Vertex/project/location. Thiếu `phase_b_store` thì từ chối trước claim job/provider/ADC.
- Recorder, kho Pha B được tiêm và dịch vụ worker dùng cùng PostgreSQL; không lách bằng tạo JSON/SQLite rồi gán lại `.store`.
- Usage checkpoint tính luỹ kế từ baseline attempt; không tính lịch sử 9 USD giả vào attempt mới. Chuẩn hoá USD đúng precision DB, thiếu usage giữ cờ false.
- Đo wall time bằng đồng hồ đơn điệu; embedding wait để null/chưa đo. Huỷ/lỗi vẫn giữ usage thực biết được và receipt, không publish lên lease mới.
- `allow_spend=False` cố định. Dry-run bị chặn khỏi queue; không có cờ mở chi ngầm trong giai đoạn này.

### Kiểm độc lập trên main mới

Đã chép **3.144 tệp** từ snapshot theo manifest, kiểm SHA-256 nguồn/đích, không liên kết và không learner live store.
Guard port được thử phá bằng cách bỏ kiểm bắt buộc `phase_b_store`: **native exit 1, đúng 1 assertion failure, 0 setup error**, nguồn phục hồi cùng SHA.
Đây là thử phá do điều phối chạy, ngoài hồ sơ 14 mutation của tác giả.

Lượt thử guard đầu lỗi setup vì điều phối chưa tạo thư mục `tmp` trong worktree mới (`WinError 3`); không tính là guard bắt được lỗi.
Giữ nguyên XML/log đầu, tạo thư mục cha và chạy lại với basetemp mới. Không sửa test/sản phẩm hoặc xoá log cũ.
React độc lập **104/104 đạt**, build native exit 0.

**Cổng Python/PostgreSQL:** **2.266 đạt, 0 fail/error, 1 skip Cloudinary live có sẵn**, native exit 0 trên đúng `eea5472`.
Pytest 1.018,62 s; wrapper 1.040,22 s. Đây là thời gian cổng kiểm, không phải phút/cuốn của pipeline thật.
Main vẫn `605f6a3` tại lúc chốt cổng; tám tệp mã/test/harness không đổi sau kiểm.
**Phán xét:** nhận mốc adapter/kiểm 0 USD; chỉ ghép chính `eea5472`, giữ toàn W-15 mở và chưa cấp quyền chi.
**Đã ghép và đẩy GitHub:** merge `d12b67c` nhận đúng `eea5472`; W-11/W-24 không nằm trong lần ghép này.
Không có thay đổi mã khi ghép lên main so với mốc đã qua cổng. Không dọn worktree sau ghép.

### Phần chưa hoàn thành và điểm chờ thật

W-15 **chưa chạy được toàn DocumentPipeline thật**: `DocumentPipeline`/runtime con chưa nhận store PostgreSQL từ web.
Test dùng core `BuildDocument` thật, pipeline giả và PostgreSQL thật; không chứng minh các dependency con trong pipeline mặc định đã được port.
Đã ghi yêu cầu cụ thể ở mục 8 bàn giao, chờ Claude/phiên pha A chốt người sửa/phạm vi:

1. `DocumentPipeline.__init__(settings, *, allow_spend, phase_b_store=None)` nhận store trước khi tạo runtime con.
2. `PhaseBRuntime.__init__(..., store=None)` chọn store trước session/spend guard/use case, mọi ghi/đọc đi cùng DB web.
3. Chốt một nguồn tổng chi build, giữ trace purpose con mà không cộng trùng với meter/receipt `purpose=build`.
4. Kiểm lại identity/cache, helper pipeline version có Git HEAD và usage baseline khi nhận port. Callback completed được adapter bọc rồi; chưa cần tự sửa `BuildDocument.execute`.

Doc-6 nguồn có graph v29 không đồng nghĩa cache web trúng: web tạo ID từ hash PDF khác `doc-6`, pipeline version cũng khác fake.
Không ép số version hay coi khoá chưa confirm là một build thành công. Chưa có lượt doc-6 thật qua web, dry-run thật hoặc cuốn mới có tiền.
Ứng viên `rau-thuy-canh.pdf` 52 trang chỉ là ứng viên; chưa có số gọi/USD/phút đo được, chưa được dùng mức “dưới 3 USD” thành quyền chi.

## 4. Thiết kế W-24: sửa báo cáo cũ đúng, phần mới tạo hồi quy

Commit `fe8ccf36ef79e364f032bc61250e2433c6fd0bc8` sửa đúng các nhận định sai trước đó.
Các tệp OS reduced-motion/token/guard cũ không đổi nội dung sau chuẩn hoá CRLF so với `78fb774`; không giao lại lỗi đã đóng và không chạy lại vô ích 32 test/74 giá trị cũ.
Không tách ghép mốc cũ trong đợt này để né phần mới chưa đạt; gói `16e95c1` giữ nguyên ngoài main.

**Năm Required:**

1. **URL một lần:** `design/preview/w11_course_management_screens.html:246,254,261,273` hiện toàn URL/token và nút copy trong danh sách đã lưu.
   Danh sách phải chỉ hiện đuôi sáu ký tự; tạo mới mới có vùng reveal/copy một lần. Chuỗi mẫu không phải bí mật thật, nhưng đang chỉ sai hợp đồng cho React.
2. **Dữ liệu/quota:** dòng 308 của preview W-11 hứa xoá dữ liệu học/graph khi xoá khoá; spec giữ dữ liệu user×document và artifact dùng chung.
   `w14_upload_screens.html:263` hứa huỷ không trừ lượt và giải phóng hết tài nguyên; confirm trước thì lượt không hoàn, chi đã phát sinh phải giữ, worker dừng ở ranh giới bước.
3. **Plugin/token:** VM chạy đúng block Variables ở cả hai nhánh tạo mode cho thấy có 37 tên nhưng thiếu `radius/radius-xl`, `motion/motion-base`, thêm `motion-normal/slow`, radius-lg 16 thay 14 và bốn dark tint alpha 1 thay 0.14.
   Phải so tên/kiểu/giá trị/alpha với hợp đồng, báo các lỗi tạo thật thay catch rỗng; cập nhật đoạn báo cáo còn nói plugin 26 biến.
4. **Mobile:** browser đo năm nút chỉ cao 36 px tại 390 px; các nút Ôn tập/Mở toàn màn hình của W-08 xuống nhiều dòng tràn khung.
   Bố trí lại hàng/cột và bảo đảm tối thiểu 44×44 px; không lấy “trang không tràn ngang” thay kiểm nút/chữ.
5. **Checklist:** chưa có trạng thái bài giảng hỏng hẳn, viewer ảnh trang/điều khiển thật, báo lỗi nội dung, hoặc phân biệt đủ pre-gate/streaming.
   Trích đoạn nguồn/xoá khoá không thay các trạng thái này. Bổ sung hoặc ghi rõ thiếu; bỏ lời hứa “OCR y khoa” không có trong spec.

Độc lập chạy **18 cấu hình Chromium**: ba HTML mới/đổi × 390/768/1280 × sáng/tối, **0 tràn trang, 0 lỗi JS**; vẫn thấy các lỗi nút nêu trên.
Font HTTP được đáp ứng cục bộ, không kết nối dịch vụ ngoài; hai ảnh mobile và ảnh huỷ được mở kiểm thị giác.
VM diagnostic native exit0 chỉ có nghĩa script đo chạy được, **không có nghĩa token parity đạt**.

### Figma Cloud đọc lại thật

Dùng skill `figma-use`, chỉ đọc file `UVhhlZnqdpV0JDcAHwJczo`, page `0:1`:

- collection `VariableCollectionId:45:2`, chỉ mode Light `45:0`, **0 Variables**;
- **0 native components/component sets, 0 node có reactions, 0 flow starting points**;
- sáu frame cấp cao, frame prototype `45:222`; chưa có frame W-11/W-08 mới trên Cloud.

Không quy nguyên nhân cho thiếu REST token/Enterprise; plugin code mới chưa phải bằng chứng đã chạy trên Cloud.
W-22/W-24 tiếp tục mở, W-23 vẫn chờ đầy đủ W-22 và W-08/W-09/W-10.

## 5. Phối hợp Claude và kế hoạch tiếp theo

| Nhóm | Làm ngay | Sau khi mốc đó đạt |
|---|---|---|
| Web | Sửa W11-R1, thêm regression và browser PG hai chiều, nhận main/cổng lại | W-08: gateway/HTTP/SSE/React của trang học, giữ stream sau cổng và không hiện bản lùi; sau đó W-09 rồi W-10 |
| Lõi | Bàn giao port W-15 cụ thể để Claude/phiên pha A chốt; kiểm identity/cache/doc-6 trên bản sao ở 0 USD | Sau port: kiểm toàn pipeline với PG, dry-run thật có guard mạng, trình số gọi/USD/phút và trần; chỉ chạy có tiền khi chủ dự án duyệt đúng lượt |
| Thiết kế | Sửa năm Required W-24; kiểm chính plugin sinh token và các trạng thái mới | Đồng bộ Variables/components/bindings/reactions lên Cloud, xuất receipt/video thật, ưu tiên màn W-11/W-08 rồi chat/quiz |

Với một phiên web, giữ đường ưu tiên **W-11 → W-08 → W-09 → W-10** để hoàn thiện hành trình học.
W-12 đã đủ phụ thuộc nhưng xếp sau hoặc chỉ tách khi có người khác; không kéo nhóm web khỏi bản vá W-11.
W-15 tiến hành song song theo port và duyệt chi riêng. Chưa mở nghiệm thu tổng W-21 hoặc W-23 khi các phụ thuộc vẫn thiếu.

**Gỡ chờ cũ:** SA-56/57 đã ghép `04c3efa`, SA-58 đã ghép `e2cfbac`; W-09 không còn chờ hai hợp đồng này.
Claude nhắc wrapper `get_lecture(concept, **kwargs)` chuyển `cache_only` xuống `LectureUseCase.make`; `wayfinder/testing.py` đang truyền sai `lecture.get`.
Giao sửa trong W-09, kiểm focus/cache hit/cache miss/công cụ thường, không tạo nội dung mới từ cache-only miss.
Search dùng scope chuẩn của SA-58; replay cũ trước `e2cfbac` không còn khớp mô tả công cụ, cần fake/fixture hợp đồng mới ở 0 USD.

SA-60 của Claude đo embedding Vertex khoảng 11,4 s/request, tổng p50 16,2 s; đây là số đo đã ghi, không phải phép đo mới trong đợt này.
Chủ dự án giữ Vertex tới demo dự kiến khoảng 2026-11-12, **không tự đổi theo ngày**. Chuyển Developer API phải có chỉ thị và SA-61 đã ghép.
Đừng sửa lỗi schema lõi trong vé web hoặc gán chậm embedding cho kho JSON; web dùng PostgreSQL.

Lời giao đầy đủ cho ba nhóm: [lenh-giao-viec-sau-w11-2026-10-23.md](lenh-giao-viec-sau-w11-2026-10-23.md).
Chỉ soạn để chủ dự án chuyển, chưa nhắn phiên nhân viên bên ngoài.

## 6. Bằng chứng và giới hạn

Bộ bằng chứng điều phối có **79 tệp trong manifest, khoảng 1,75 MB**, không kể chính manifest:

- [Tổng hợp số và mốc](coord-w11-w15-w24-evidence-2026-10-23/summary.json), [SHA-256](coord-w11-w15-w24-evidence-2026-10-23/manifest.json).
- W-11: [JUnit tái hiện đỏ](coord-w11-w15-w24-evidence-2026-10-23/w11/auth-return-red.xml), [test có thể chạy lại](coord-w11-w15-w24-evidence-2026-10-23/w11/W11AuthReturn.repro.test.tsx), [native exit/mốc/lệnh](coord-w11-w15-w24-evidence-2026-10-23/w11/result.json).
- W-15: [JUnit toàn repo](coord-w11-w15-w24-evidence-2026-10-23/w15/full.xml), [native exit/lệnh/mốc](coord-w11-w15-w24-evidence-2026-10-23/w15/full-exit.json), [React](coord-w11-w15-w24-evidence-2026-10-23/w15/react.xml), [guard bị bắt và SHA phục hồi](coord-w11-w15-w24-evidence-2026-10-23/w15/port-mutation-result.json), [kiểm package 265/265](coord-w11-w15-w24-evidence-2026-10-23/w15/w15-package-review.json).
- W-24: [review và vị trí lỗi](coord-w11-w15-w24-evidence-2026-10-23/w24/review.md), [18 cấu hình browser](coord-w11-w15-w24-evidence-2026-10-23/w24/browser-observations.json), [plugin diagnostic](coord-w11-w15-w24-evidence-2026-10-23/w24/plugin-local-contract-observations.json), [Cloud đọc thật](coord-w11-w15-w24-evidence-2026-10-23/w15/w24-cloud-read.json).

Lệnh đầy đủ/native exit/commit ở metadata từng lượt; có cả ca đỏ W-11 và setup đỏ của lượt thử guard đầu.
Hồ sơ tác giả W-11 còn trên nhánh chưa ghép; báo cáo này phân biệt rõ các số đã chạy lại và các số chỉ đối chiếu hồ sơ.
Văn bản lưu Git được chuẩn hoá UTF-8/LF và bỏ khoảng trắng cuối dòng; `normalization.json` giữ cả hash raw và hash lưu.
JSON được so lại giá trị, JUnit so lại số ca/fail/error/skip; manifest mới áp dụng cho bản lưu, không tự nhận khớp hash raw khi byte đã đổi.
Không thêm paid call, không mở tập giữ lại/live cache, không nối/xoá worktree hoặc dữ liệu. Sáu tệp đang sửa của phiên khác tại root được giữ nguyên.
