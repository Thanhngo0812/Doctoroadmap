# Nghiệm thu W-02, W-05 và soát W-24 — 2026-10-20

**Kết luận điều phối:** W-02 và W-05 **đạt nghiệm thu phạm vi vé local**, đã ghép đúng tuyến migration.
W-24 **đạt phần vá kỹ thuật đã kiểm**, nhưng **chưa đủ nghiệm thu toàn bộ W-22/W-24** vì bằng chứng Figma và prototype chưa chứng minh tiêu chí gốc.

**Đợt tiếp:** web ưu tiên W-03; lõi phụ trách backend/gateway W-06, phối hợp React với web; thiết kế hoàn thiện W-24 và bản vẽ cho W-03.
W-04 mở sau W-02, có thể chia người khi không tranh sửa AccountService. W-15 vẫn chờ W-14; W-23 chưa mở.

Đầu vào đã ghim tại HEAD `63256e0`, gồm W-05 `0602768`/`e163815`/`8600e27`, ghép `b918209`, W-02 `87aa562` và hai sửa UI `3711d12`/`63256e0`,
W-24 `ba73cfc`. [Manifest SHA-256](../artifacts/coord-w02-w05-w24-2026-10-20/manifest.json) ghi 80 tệp được soát.
Trong lúc kiểm, nhóm web bổ sung menu/thông báo/đăng xuất trên working tree. Điều phối đọc diff, build và kiểm lại bản UI đó;
[manifest bổ sung](../artifacts/coord-w02-w05-w24-2026-10-20/manifest-ui-update.json) ghim hash tệp, không gán các sửa chưa commit vào HEAD trên.
Không sửa mã sản phẩm, không gọi mô hình, Cloudinary thật hay gửi thư. **Chi phí mô hình đợt kiểm: 0 USD.**

## 1. Kiểm độc lập và bằng chứng

| Phép kiểm | Kết quả |
|---|---|
| Backend đầy đủ W-01/W-02/W-05 + token W-24, PostgreSQL bắt buộc | **168 passed, 1 skipped**, không fail/error; [XML](../artifacts/coord-w02-w05-w24-2026-10-20/backend-and-tokens.xml). Chỉ bỏ qua Cloudinary live theo cờ bật riêng |
| Hồi quy lõi store/budget/SA-48 sau nới port | **33 passed**, không skip; [XML](../artifacts/coord-w02-w05-w24-2026-10-20/core-regression.xml) |
| React hiện hành, gồm menu/đăng xuất mới | **41/41 passed**, TypeScript + Vite build đạt; [kết quả lệnh](../artifacts/coord-w02-w05-w24-2026-10-20/frontend-verification.json) |
| W-02 HTTP + PostgreSQL thật trên DB riêng | **12 màn, 9 assertion luồng đạt**, 0 lỗi console ứng dụng; [browser audit](../artifacts/coord-w02-w05-w24-2026-10-20/w02-browser/browser-audit.json) |
| W-02 phản hồi form/chuyển trang | **6 trường hợp đạt**, gồm lỗi, success, chuyển form, reduced-motion và axe; API được mô phỏng rõ ràng trong phép kiểm UI này; [audit](../artifacts/coord-w02-w05-w24-2026-10-20/w02-feedback/browser-audit.json) |
| W-02 kiểm lại sau sửa UI mới | Auth thật vẫn **12 màn/9 assertion**, form **6 ca**; thêm menu/đăng xuất **9 ca** ở 336/390/1280, sáng/tối, email dài, giảm chuyển động; [runtime](../artifacts/coord-w02-w05-w24-2026-10-20/w02-ui-update/w02-isolated-runtime.json), [menu audit](../artifacts/coord-w02-w05-w24-2026-10-20/w02-ui-update/account-menu/browser-audit.json). API menu/form là đồ giả, không cộng lượt lặp thành thêm ca độc lập |
| Mutation W-02 bỏ hạn idle | Test đỏ đúng assertion; không hỏng collection hay sửa tệp nguồn; [kết quả](../artifacts/coord-w02-w05-w24-2026-10-20/w02-idle-mutation.json) |
| Mutation W-05 bỏ flight lock / atomic lock | **2/2 bị bắt** trên hai tiến trình, đúng lỗi sinh trùng/nhận quá ngân sách; [kết quả](../artifacts/coord-w02-w05-w24-2026-10-20/w05-mutations.json) |
| W-24 sửa token/GIF/mobile/auth | Ba mutation token bị bắt; sáu màu plugin khớp; auth 390 hết tràn; GIF tĩnh bốn preview; [runtime](../artifacts/coord-w02-w05-w24-2026-10-20/design/runtime.json), [màu](../artifacts/coord-w02-w05-w24-2026-10-20/plugin-six-dark-colors.json) |
| W-24 mutation giảm chuyển động trên browser | Cùng assertion hash ảnh: bản đúng tĩnh, bỏ cả hai đường ảnh tĩnh trong DOM thì **4/4 preview đỏ đúng assertion**, không sửa nguồn; [bằng chứng](../artifacts/coord-w02-w05-w24-2026-10-20/gif-mutation.json) |
| Dependency audit | `npm audit --omit=dev --json`: 0 advisory trong phạm vi dependency chạy ứng dụng |
| Quét secret đã cấu hình trên tệp được soát | Không thấy giá trị secret trong phạm vi 80 tệp; không in secret; [tóm tắt](../artifacts/coord-w02-w05-w24-2026-10-20/secret-scan-summary.json) |

168 và 33 là hai tập test riêng; không cộng lượt mutation đỏ, lượt chạy lại hoặc số test nhân viên báo vào số passed này.
Không chạy lại toàn bộ 2.062 test của [bàn giao W-02](w02-tai-khoan-phien-2026-10-19.md); kết quả ở trên là phần điều phối tự chạy.

Lệnh kiểm chính (runner PostgreSQL tự thêm `-p no:cacheprovider`):

```text
.venv/Scripts/python.exe scripts/w05_run_tests.py src/web/backend/tests tests/unit/presentation/test_tokens_and_wcag.py --basetemp=tmp/coord-20261020-pg-ready --junitxml=tmp/coord-20261020-pg-ready.xml
.venv/Scripts/python.exe -m pytest tests/unit/application/test_phase_b_store.py tests/unit/application/test_phase_b_budget_sa48.py tests/unit/application/test_phase_b_sa48_review.py -p no:cacheprovider --basetemp=tmp/coord-20261020-core-isolated --junitxml=tmp/coord-20261020-core-isolated.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1
npm.cmd --prefix src/web/frontend run build
```

**Môi trường và lần đỏ cần giữ lại:** lúc đầu `db-test` đang tắt, lệnh kiểm báo lỗi đúng thay vì bỏ qua. Đã khởi động riêng dịch vụ đó và chạy lại đạt.
Trong lượt đầu có thêm một assertion JSON cũ, timeout 30 ms, chưa thấy provider vào khi chạy đồng thời các bộ kiểm.
Chạy riêng ca đó đạt, rồi chạy đủ 33 test lõi ở trên cũng đạt. Không sửa timeout, nguồn hay assertion để lấy xanh.
[XML lượt đầu](../artifacts/coord-w02-w05-w24-2026-10-20/first-run-environment-errors.xml),
[ca JSON chạy riêng](../artifacts/coord-w02-w05-w24-2026-10-20/json-timeout-isolated.xml).

## 2. W-02 — đạt

Đã đọc dịch vụ tài khoản, store PostgreSQL, ranh giới HTTP, schema/migration, test và phần React mới.
Trọng tâm soát là đầu vào HTTP → tài khoản/phiên trong DB; cookie/Origin/CSRF → quyền thao tác;
và nhiều kết nối → giới hạn thử dùng chung. Test kiểm cả đường từ chối, không chỉ đăng nhập thành công.

- Argon2id, blocklist đóng kèm, token phiên chỉ lưu băm, hai hạn idle/absolute, thu hồi phiên khi disabled và logout đều có assertion chạy đạt.
- Origin được kiểm trước body; route unsafe mới tự vào test guard; CSRF gắn với phiên. Cookie production Secure và giới hạn email/IP dùng PostgreSQL chung.
- Phản hồi known/unknown login giống nhau. **Giữ quyết định chủ dự án về tự đăng nhập sau đăng ký mới**: status/body đăng ký trùng giống nhau,
  nhưng cookie và `/me` vẫn cho phép suy ra email tồn tại. Đây là giới hạn đã được chấp nhận trong spec, không mở lại quyết định đó.
- Đã kiểm thực trên browser ở 390/768/1280, sáng/tối; focus, lỗi trường, xoá lỗi khi đổi form, success và giảm chuyển động đạt.

Browser dùng database UUID riêng, nâng đầy đủ schema, API/auth/băm mật khẩu và PostgreSQL thật. Composition chỉ thay bước kiểm xác thực mô hình cùng adapter mô hình bằng đồ giả,
vì vé này không cần sinh nội dung. Đã đóng server kiểm và xoá đúng database do lượt kiểm tạo;
[biên bản runtime](../artifacts/coord-w02-w05-w24-2026-10-20/w02-isolated-runtime.json).

Đã xem [đăng nhập mobile tối](../artifacts/coord-w02-w05-w24-2026-10-20/w02-browser/dang-nhap-390-dark.png),
[đăng ký desktop](../artifacts/coord-w02-w05-w24-2026-10-20/w02-browser/dang-ky-1280-light.png),
[phản hồi lỗi mobile](../artifacts/coord-w02-w05-w24-2026-10-20/w02-feedback/login-error-390-light.png).
[Danh sách video tự ghi](../artifacts/coord-w02-w05-w24-2026-10-20/video-index.json) đi kèm ảnh và kiểm hiệu ứng.
Sau bổ sung UI đã xem thêm [menu mobile tối](../artifacts/coord-w02-w05-w24-2026-10-20/w02-ui-update/account-menu/menu-390-dark.png)
và [đăng xuất desktop](../artifacts/coord-w02-w05-w24-2026-10-20/w02-ui-update/account-menu/logout-1280-light.png).
Test chờ API logout thành công mới chuyển trang; lỗi mạng giữ tài khoản và cho thử lại, không hiện success sớm. Menu giữ email một dòng,
có dấu ba chấm/title khi dài, nút 44 px; thông báo căn giữa vừa chữ và reduced-motion không còn animation chạy trong các ca đã kiểm.
Áp dụng `code-review-and-quality`, `security-and-hardening`, hướng dẫn app-screen của `design-taste-frontend`; spec thương hiệu được ưu tiên.

## 3. W-05 — đạt, bao gồm checkpoint tích hợp W-02

Đã kiểm CRUD/copy semantics, extra giữ dict usage gốc, bộ lọc/ẩn danh, negative cache, advisory lock trên pool riêng,
`atomic()` lồng/rollback/READ COMMITTED và các regression Pha B trên PostgreSQL.
Các mutation tạo được vi phạm quan sát độc lập: generator chạy hai lần, hoặc hai tiến trình cùng nhận phần ngân sách cuối.
Không dùng lỗi setup/collection làm bằng chứng guard bắt được sai.

Tuyến thực tế **`w01_0001 → w05_0002 → w02_0003`**, một head. Test DB rỗng/metadata và test baseline W-01 cùng đạt;
DB browser độc lập cũng ở `w02_0003`, có bốn bảng Pha B và bốn bảng tài khoản cùng `alembic_version`.
Đóng ô tích hợp cuối W-05, không yêu cầu nhóm lõi kiểm lại phần này khi chưa có thay đổi mới.

Giữ giới hạn thiết kế đã công khai: atomic dùng một khoá DB chung cho cập nhật ngắn, ưu tiên tính đúng theo port hiện tại;
đợt này chưa phải đo tải production. Số USD trong kiểm ngân sách là dữ liệu giả, không phát sinh lời gọi nhà cung cấp.

## 4. W-24 — phần vá đạt, hai nhóm bàn giao chưa đạt

**Đã đóng:** sáu màu tối của mã plugin; lỗi auth tràn 20 px ở 390; các lỗi GIF/vùng bấm/spacing/RGBA/chat đã đóng ở đợt trước vẫn đạt.
Không giao lại các lỗi này. [Ảnh auth 390 mới](../artifacts/coord-w02-w05-w24-2026-10-20/design/auth_screens.html-390.png).

**A. Chưa có nguồn độc lập cho Figma Variables.** `scripts/generate_figma_variables_export.py` chỉ đọc `design/tokens/tokens.json`,
tự ghi metadata exporter/timestamp rồi tạo `figma_variables_export.json`. Điều phối chạy bản sao trong bộ nhớ, chặn ghi tệp,
tái lập được nội dung **giống từng byte**. [Kết quả](../artifacts/coord-w02-w05-w24-2026-10-20/figma-export-provenance.json).
Tệp này dùng được làm dữ liệu nhập/đối chiếu cục bộ; chưa chứng minh Variables trong file Figma đã khớp.
Không ghi metadata/báo cáo như thể đã xuất trực tiếp từ Figma khi chưa có bằng chứng nguồn đó.

**B. Audit chưa kiểm đủ bốn prototype theo vé.** Hai dòng của `scripts/verify_prototype_flows.cjs` ghi `passed: true` sau thao tác gập/scroll mà không kiểm kết quả.
Điều phối cố ý gỡ handler accordion trong trang thử, thao tác không đổi trạng thái (`block → block`), nhưng script vẫn thoát 0 và báo **4/4 đạt**.
[Trạng thái không đổi](../artifacts/coord-w02-w05-w24-2026-10-20/prototype-mutation/disabled-accordion.json),
[audit vẫn xanh](../artifacts/coord-w02-w05-w24-2026-10-20/prototype-mutation/prototype_flows_audit.json).
Không sửa HTML hay mã nguồn gốc để làm phép thử này.

Bốn mục trong audit còn là hiện mật khẩu, accordion, xem vùng upload và nộp quiz. Chúng chưa chứng minh bốn luồng gốc:
đăng ký → khoá mẫu → bài giảng; chia sẻ → tham gia; tải → xác nhận → dựng; quiz → nộp → kết quả.
Plugin vẫn tạo khung chữ mô tả, chưa có lệnh gắn liên kết prototype trong mã. Đường đọc Figma của công cụ web không truy cập được file;
không kết luận file Figma không tồn tại.

**Người thiết kế chỉ cần hoàn tất hai nhóm trên:** giao bản xuất thật có nguồn, node/ảnh từng trang-trạng thái, bốn prototype bấm được và video;
đổi audit sang assertion kết quả, buộc đỏ khi cố ý bỏ tương tác. Bảng đủ/thiếu phải phản ánh sản phẩm thực, không thay trang bằng tên nút mẫu.
Đây là tiêu chí gốc W-22/W-24, không thêm một vòng thiết kế lại thương hiệu.

## 5. Giao việc đợt tiếp

| Nhóm | Việc ngay | Đầu ra và điểm kiểm |
|---|---|---|
| Web | **W-03**; bố trí React/tích hợp cho W-06; W-04 chia sau nếu còn người | Mailer fake/console/SMTP, token một lần/hạn/throttle, reset thu hồi mọi phiên; JSON API, HTML thư, ảnh/video; test PostgreSQL và CSRF/Origin |
| Lõi | **Backend/gateway W-06**, phối hợp một người React của web | Course/membership, seed allowlist sáu cuốn, ghim graph hoàn tất, get_roadmap và progress qua kho PostgreSQL; test người ngoài khoá/owner giả mạo; báo cáo vé chung khi UI thật cũng đạt |
| Thiết kế | **Hai nhóm bàn giao W-24 còn lại**, đồng thời ưu tiên màn W-03 | Variables export có nguồn và node/prototype/video thật; xác minh, quên/đặt lại mật khẩu và trạng thái token hết hạn/đã dùng |

Mã W-06 ở `src/web/`, lõi phối hợp backend không mở thêm quyền sửa `src/doc2roadmap/` ngoài phạm vi các vé đã được phép.
`PhaseBRuntime` hiện tự khởi tạo kho JSON; không coi trường `WebServices.phase_b_store` đã có là bằng chứng mọi use case đã dùng PostgreSQL.
W-06 phải nối phụ thuộc qua port/use case và kiểm dữ liệu đọc/ghi thật bằng kết nối độc lập, gồm spend guard dùng cùng kho.
Không chỉ gán lại một thuộc tính bên ngoài trong khi phụ thuộc con vẫn giữ kho cũ.

**Migration đợt này:** từ head `w02_0003`, web bàn giao `w03_0004` (`email_token`) trước; lõi chốt `w06_0005`
(`course`, `membership`) sau với `down_revision=w03_0004`. Có thể làm service/test/UI song song; ghép schema theo một tuyến.
W-04 không cần tạo migration rỗng nếu không thêm bảng/đổi schema. Giữ mọi kiểm baseline và một-head đã có.

**Lưu ý W-03:** các route công khai dùng token như reset request/confirm phải có chính sách Origin/CSRF rõ và test riêng;
không tháo guard toàn cục để chúng chạy. Resend gắn phiên vẫn cần CSRF. Test gửi thư dùng Mailer giả; lượt điều phối này không gửi thư cho người khác.

## 6. Sau mốc W-03/W-06

- W-06 đạt thì mở W-07 lộ trình và W-11 chia sẻ; W-03 cùng W-06 đạt thì mở W-14 tải sách/hàng đợi dùng bộ dựng giả.
- W-14 đạt mới mở W-15 nối bộ dựng thật; W-13 đã đạt, không mở lại việc doc-6.
- W-23 vẫn chờ W-22/W-24 và W-08/W-09/W-10. W-24 chưa đủ không chặn W-03/W-06 làm theo spec đã chốt.
- Theo ghi chú Claude ngày 2026-10-19: cần người soát độc lập SA-46/47/49/50/51 trước khi chuyển các trạng thái Pha B liên quan sang đạt;
  SA-48 đã có báo cáo soát. Bàn giao nhân viên không tự thay thế bước này.
- `focus_node_id` vẫn là đề xuất chờ chủ dự án duyệt; chưa sửa `answer-2` hay mở rộng W-09 theo đề xuất đó. Giữ Vertex theo quyết định hiện hành.

Kế hoạch và lời giao đã được ghi để chủ dự án chuyển sang ba nhóm; lượt này chưa gửi thông điệp sang các phiên nhân viên.
