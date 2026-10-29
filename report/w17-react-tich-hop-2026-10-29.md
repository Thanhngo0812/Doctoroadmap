# W-17.1 React — Người dùng và Nhật ký, 2026-10-29

**Báo cáo triển khai, đang hoàn thiện kiểm cuối; chưa tự nghiệm thu W-17.1 hoặc toàn W-17.** Chỉ hai màn Người dùng/Nhật ký và ba API backend đã nhận. Bản dựng/khoá mẫu/chi/lecture_validation tiếp tục thuộc mốc sau. Không sửa use case lõi, registry, migration, profile/password/epoch hoặc W-12.

## Nền, hợp đồng và phạm vi

Tạo `work/w17-admin-users-react` tại `tmp/w17-admin-users-react` từ main `84428bf6` có backend W-17.1 `a07bff3f`, đã ghép `4e6f33cb`. Đọc W-17, spec chức năng 3/9/10/11, ADR 0030, lời giao lần 12, `wayfinder/api/admin.py` và OpenAPI trên main. Đã nhận thêm main đánh giá `f2bcda6b` bằng merge (không rebase); không đổi nhánh/root, không sửa vé/kế hoạch/handoff, không ghép/push main.

React `/admin` chuyển `/admin/nguoi-dung`; khu admin chỉ có Người dùng và Nhật ký. Entry menu chỉ cho role admin từ phiên, route trực tiếp vẫn chặn người thường. Server kiểm quyền cuối ở mỗi request. Tái dùng CourseShell/logo/font/token và `apiJson`/CSRF hiện hành. Không thêm framework hoặc dependency.

- `GET /api/v1/admin/users`: email/role/status/limit/offset phía server, tổng và phân trang theo response. Bảng danh tính, trạng thái/vai trò, khoá sở hữu, lượt dựng; chi tiết ngày tạo/login/xác minh trong dialog.
- `PATCH /api/v1/admin/users/{uid}`: chỉ gửi role/status/build_monthly_max thực đổi. Hạn mức riêng là integer 1..2147483647, null là dùng cấu hình chung; max hiệu lực null hiển thị Không giới hạn, không biến thành 0. Thay trạng thái/vai trò có bước xác nhận nêu email/hệ quả; quota riêng gửi trực tiếp sau nút lưu. Chỉ thông báo thành công sau response canonical, tải lại danh sách đúng nguồn.
- `GET /api/v1/admin/audit`: actor/action/since/until/limit/offset phía server. Nhập thời gian Việt Nam, chuyển UTC khi gửi, until không bao gồm; chỉ render field public id/at/actor/action/target/ip. Không stringify raw meta, không mở nội dung học riêng, không bịa tên cho UUID.
- `is_first_admin=true`: chặn chọn khoá/hạ quyền bằng UI, nói rõ bảo vệ; quota và hồ sơ/mật khẩu giữ theo server. Không đoán bootstrap từ hàng/created_at. null: giải thích chưa đối chiếu định danh và phản ánh lỗi bootstrap_required, không có input UUID/API bootstrap trong web.
- Không mang guard sai CORE-R11-01 vào client: admin disabled thêm sau vẫn được demote hoặc enable+demote. Protected admin và last-active do backend quyết định; UI không tự đếm admin từ trang đang lọc.
- Xử lý 401/account_disabled bằng clearSession, forbidden gỡ dữ liệu và báo đúng quyền quản trị; CSRF có lỗi riêng. 409/422 theo fields, mạng lỗi giữ draft/thử lại. Không báo thành công lạc quan.
- Component keyed theo id/role/path; AbortController cho GET/PATCH. Đổi filter/route/identity/role hoặc đóng dialog huỷ quyền nhận response cũ. GET đang tải ẩn dữ liệu/hành động chỉnh sửa; dialog khoá bộ lọc/tải lại/phân trang. Vì vậy GET trước không có cửa ghi đè PATCH sau; mutation xong revalidate bằng lượt đọc mới. Không lưu dữ liệu quản trị vào storage.

## Thiết kế và taste-skill

Chọn **Framed sheet**, seed **1925552326**, draw trước markup tại đúng worktree, giữ palette/type. So với Accent ladder, khung phẳng hợp màn vận hành tài khoản cần đọc hàng và kiểm quyền; không cần thẻ plan/KPI. Dùng vùng điều hướng trên nền nhạt, sheet 1px/radius16 không bóng, tab/nhãn bảo vệ bằng brand, số tabular và cột danh tính rộng. Font Be Vietnam Pro, logo Artboard24/28, màu theo main. Câu hỏi Người dùng: “cần điều chỉnh tài khoản nào, thay đổi gì?”; Nhật ký: “ai làm gì/lúc nào/với đối tượng nào?”. Định danh admin đầu tiên từ server là chi tiết riêng của sản phẩm, không biểu tượng trang trí.

Tái dùng header 64px của WayFinder thay 48px từ sheet để giữ thương hiệu và vùng bấm44px đã duyệt; giữ tỷ lệ màu/khung của hướng đã chọn. 1280 có nav trái; 768/390 nav xếp trên, bảng Người dùng thành hàng có nhãn trên mobile, audit cuộn riêng trong vùng có tên/bàn phím, cả trang không tràn. Modal cuộn theo viewport; Escape/đóng trả focus về nút mở, confirm mặc định Quay lại. Reduced-motion thật qua browser; không thêm hiệu ứng vào trang. Không dùng Cloud Figma hay preview chưa nhận làm nguồn thay token.

## Test và lịch sử lỗi thiết lập

Test mới `Admin.test.tsx` dùng App/Auth thật và fetch giả đúng DTO chỉ để kiểm component; không dùng làm chứng minh HTTP/PG. `red-initial2.xml`: **13 assertion fail**, không setup error, trên App chưa có route quản trị. `red-initial.log` khởi chạy khi npm ci chưa xong nên thiếu binary vitest; giữ làm setup error, không tính RED.

GREEN lần đầu có ba vấn đề fixture/harness: offset string “0” bị coi truthy; query tìm text trùng option datalist ẩn; fireEvent.cancel không tồn tại. Sửa đúng fixture offset số/query cell và dispatch native cancel. Datalist đã tách khỏi label để accessible name input không chứa toàn bộ option. Sau thêm guard filter/identity/network, một query quota bị đổi accessible name bởi inline error; input có tên ARIA ổn định và lỗi vẫn nối describedby. `green-admin-05.xml`: **20 pass**, có GET/PATCH cũ sau đổi tài khoản/vai trò, GET cũ sau lọc, POST thất bại và mạng/thử lại, không skip/hạ assertion.

`build-browser-01`: type fixture role/status bị rộng thành string sau khai báo rows theo DTO; khai báo first/later là AdminUser, giữ kiểm enum. Build-browser-02 native0. Không dùng Vitest transpile xanh thay TypeScript/build.

Kiểm bàn phím thêm sau GREEN ban đầu: `red-focus.xml` một assertion fail trên hành vi mất focus khi row revalidate; đưa focus tới thông báo hoàn tất, `green-focus.xml` 21 pass. Browser-final1 sau đó bắt trường hợp **lưu cùng email lần thứ hai**: notice có cùng text nên effect không chạy lại, thông báo cũ còn sau khi mở editor. `red-repeat-focus.xml` một assertion fail/0 setup; mở editor xoá notice cũ, `green-repeat-focus.xml` **22 pass**. Không hạ assertion browser về focus; bổ sung chờ effect DOM hợp lệ, vẫn khẳng định focus chính xác trên notice và confirm mặc định Quay lại.

Browser smoke giữ mọi lịch sử:

- smoke1: label wrapper trùng thư mục output runtime; không chạy nghiệp vụ.
- smoke2: Docker/db-test đang tắt, connection timeout trước CREATE DATABASE; không tính phản chứng nghiệp vụ. Khởi động Docker Desktop ẩn và container db-test đã có, không động db phát triển.
- smoke3: harness chưa compose SharingService dùng ở trang sau login và nhầm APIResponse có request(); đã compose service thật và ghi method đúng lệnh HTTP, không fake response hoặc sửa backend.
- smoke4: harness đếm hàng trước filter mới render (8 hàng cũ, JSON mới đúng 1); sửa chờ kết quả DOM tương ứng.
- smoke5/6: chờ action có sẵn hoặc “loading hidden” có thể đi qua trước request filter bắt đầu; XML/JSON cho thấy API đúng 5 audit rows. Gắn phép kiểm vào response đúng query + tổng DOM; giữ assertion số row/action/actor/time.
- matrix1: route cũ đã bị client abort, harness cố fulfill sau khi handler kết thúc gây unhandled “Route is already handled”; run không có audit cuối, ảnh còn nguyên làm lịch sử, không chứng nhận lượt này. Sửa harness quan sát requestfailed đúng `net::ERR_ABORTED`, kết thúc handler sau khi xác nhận request cũ bị huỷ; không fake DTO/nuốt lỗi chung. smoke7 native0: 7 ảnh/7 Axe, 53 JSON HTTP, 7 SQL stages, không pageerror, held GET thật20 items không ghi đè lọc linh@.
- browser-final1: chưa đạt do lỗi focus lặp nêu trên, không dùng 38 ảnh trước lỗi thay bằng chứng cuối. React280 pass/build tại a2d0791e là lịch sử trước bản vá lặp; phải chạy lại trên nguồn cuối ce86f12c.

## Guard và tự soát

Mutation chạy tuần tự, không trùng server/full gate. Bộ cũ trên 6f8fbc3d/a2d0791e giữ nguyên source pin và SHA, không gán cho HEAD mới. Mutant role=false thô gây thêm null dereference ở probe mount sớm nên không dùng làm guard quyền chuẩn; thay bằng mutant chỉ kiểm có account nhưng bỏ điều kiện role (`role-presence`), vẫn giữ loading an toàn để failure là assertion về quyền thật.

Bộ cuối trên `ce86f12c9bd1bd1199b2b1f66adb6ca04622a4f7`: role-presence, read, callback, first, focus, repeat. Mỗi lượt Vitest native1, assertion failure/0 setup error; khôi phục `Admin.tsx` cùng SHA **ce6da3df5cb30c1e4a78b6d278908feaef8fcb6564f36a15a881caf9bcb896da** trước cổng bình thường. Helper outer native0 chỉ nghĩa đã xác nhận mutant native1 và restore; XML/native bên trong là bằng chứng lỗi.

Các kiểm chính có quan sát runnable:

| Bất biến | Assertion |
|---|---|
| Quyền client không thay server, regular không có bảng/request | `blocks a regular account without requesting an admin list`; browser regular-denied + GET thật403 |
| GET cũ không thay kết quả filter mới | `does not apply an older list after a newer filter result`; browser heldRealGet/requestfailed/DOM |
| Identity/role mới không nhận GET/PATCH/finally cũ | `discards a delayed list...`, `discards an old PATCH success/finally...`; `removes admin data when the live server returns...` |
| Guard first-admin độc lập vị trí hàng, nullable và lỗi policy | `uses the server first-admin flag...`, `keeps an unsuccessful mutation...`; browser protected-admin409/SQL, legacy-null/bootstrap_required |
| Disabled B demote/enable+demote đúng DTO/response | `allows enable plus demote...`; browser disabled-demoted/enabled-demoted + SQL registry và cookie cũ401 |
| Quota null, lỗi/retained draft, không success giả | `rejects invalid quota locally...`, `a failed list is not an empty result...`; SQL quota7/inheritednull |
| Không raw audit.meta | `renders public audit fields...` chứa marker extra nhưng DOM không có; browser kiểm key công khai của từng item trước redaction |
| Focus sau nhiều lần lưu, không notice cũ | `keeps keyboard focus...`, `clears the previous completion...`; browser confirm() Quay lại/notice focus |

Tự soát theo `code-review-and-quality`: ranh giới quyền ở server; Auth/context dùng lại; không middleware/role mới; typed DTO bám schema; không dữ liệu quản trị trong URL ngoài bộ lọc công khai/không storage; mọi text React escape; chỉ enum/value public. GET/PATCH đều có abort/ownership, không mutation cache lạc quan; bảng đầy đủ qua server tổng/limit/offset. CSS scoped `.admin-*`, không thay token/global layout; code thay Courses.tsx chỉ thêm link admin có điều kiện. Chi phí/render giữ một request list mỗi query/retry và một PATCH mỗi submit; không polling/provider.

## Cổng và bằng chứng cuối

Đang chốt cổng tích hợp trên **`b75e611b60ca64db539b364d8dce0eb20cf4ad4f`**, nhận main mới **`647149b3977f8b58e4c086e7521d4991ffc0e693`**. Không có câu trả lời chốt ngoại lệ cho main nền 6ab379db, nên đã nhận main hiện hành theo quy trình. Diff `src/` và `scripts/` giữa ce86f12c và b75e611b rỗng; các thay đổi nhận thêm là làn đánh giá, không thay hợp đồng web. Cửa PG do chủ dự án xác nhận “Cửa trống; web chạy khi chốt mã”. Mọi kiểm dùng model/embedding/media/Mailer giả (không gọi provider), HTTP/auth/Argon2/PostgreSQL thật, account tổng hợp, DB UUID riêng và connection SQL độc lập, 0 USD. Không migrate/gán bootstrap trên DB dùng chung. Dữ liệu phát triển ordinary-copy 3145 tệp theo manifest/SHA và PDF train được allowlist phục vụ full regression; không live learner store, không held-out/junction/symlink/hardlink.

`scripts/w17_react_capture.py` ghi command/cwd/HEAD/native/source SHA/log; khi có runner full PG thì giữ JSON mới và phục hồi tám report lịch sử W-06/W-14 theo byte gốc (dựa command, không dựa tiền tố label). Basetemp dưới tmp; JSON fixture/SQL không trộn ảnh UI. Report final sẽ chỉ ghi đạt khi đủ native/JUnit/SQL/source pin và bằng chứng browser đúng nguồn.

### Lịch sử cổng ce86f12c — không thay cổng sau nhận main

- React-final2: 277 pass/4 fail ở W11AuthReturn (3 timeout và một assertion chuyển route sau các timeout). Không đổi Auth/W-11/timeout; `w11-recheck-1/2` mỗi lượt22 pass, rồi `gate-react-final3` toàn bộ **281 pass**, native0. Giữ log thất bại và cả hai lượt xác nhận.
- `gate-python-final`: **3.780 pass, 1 fail, 3 skip, 1 xfail**, native1, 1512,74 giây pytest. Test lõi `test_transport_failure_preserves_every_finished_call_and_reuses_it[main]` đòi model.peak==4 nhưng thực tế3; dữ liệu checkpoint vẫn được ghi. Test dùng sleep ngắn để quan sát overlap; không sửa test, hạ assertion hay đổi executor trong vé web. Hai lượt kiểm riêng qua runner (`checkpoint-confirm-1/2`) đều **18 pass**, giữ toàn bộ tệp test checkpoint và settings web. Lệnh `checkpoint-recheck-1` trước đó thiếu conftest web nên --require-postgres không được đăng ký, native4 là setup, không tính phản chứng hoặc GREEN. Không gọi một targeted rerun là full gate.
- Tám report lịch sử do full gate ghi lại đã được wrapper giữ bản mới dưới `legacy-test-output/` và phục hồi byte gốc; git diff ngoài vùng vé rỗng sau lượt đó.
- Browser-final2 ở ce86f12c: 12 cấu hình, **40 ảnh/40 Axe/89 HTTP/7 SQL stages**, không pageerror; legacy-final2 **3 ảnh/3 Axe/10 HTTP/1 SQL stage**, bootstrap_required đúng và không đổi registry/role/audit. DB UUID hai lượt đã gỡ, server đã dừng. Taste inspector0 FAIL/0 WARN.
- Có13 kết quả Axe incomplete/color-contrast ở cột ngoài vùng cuộn hoặc dialog; **không** gọi chúng tự động đạt. Hai run bổ sung `browser-manual1` và `browser-manual-legacy1` đo **765 lượt phần tử thực**, tất cả contrast>=4,5, tối thiểu **5,8448:1**, hit-test thấy được sau scroll. Bằng chứng CSS rect, scroll position, font CDP và PNG thuộc đúng run bổ sung; không ghép số đo này vào PNG canonical cũ. `manual-a11y-summary.json` và `manual-a11y-equivalence.json` ghi scope và đối chiếu source không đổi sau ghép.
- Runtime giữ các warning Windows WinError10054 khi đóng kết nối và graceful shutdown “Cancel0”; console giữ HTTP401/403/409 có chủ ý và CSP do Axe/font inspection. Không hạ CSP; không gọi log tuyệt đối sạch. Pageerror và kiểm nghiệp vụ nằm riêng trong audit JSON.

### L??t t?ch h?p b75e611b tr?n n?n ?? ch?t 647149b3

- `gate-build-integrated`: native0, 13,41 gi?y, TypeScript/Vite build th?nh c?ng.
- `gate-react-integrated`: native0, **281 test/21 t?p**, kh?ng fail/skip; 290,84 gi?y theo wrapper. C? ??22 ca Admin c?ng h?i quy W-04/W-08/W-09/W-10/W-11/W-12/W-16.
- `gate-browser-integrated`: native0, **12 c?u h?nh/40 ?nh/40 Axe/89 HTTP/7 SQL stages**, kh?ng pageerror/vi ph?m Axe. Font Be Vietnam Pro th?t ? t?ng ?nh; 390/768/1280 ? s?ng/t?i ? normal/reduced-motion. Taste inspector ba chi?u r?ng0 FAIL/0 WARN. DB UUID ?? g? v? server ?? d?ng sau ki?m.
- S?u mutation ch?y l?i t?i **b75e611b** tr??c c?ng b?nh th??ng; native1 v?i assertion fail/0 setup error, ngu?n ph?c h?i c?ng SHA Admin.tsx n?u tr?n. `mutation-summary.json` l? b? hi?n h?nh; b? ce86f12c v? tr??c ?? ch? l? l?ch s?.

?nh ch?nh: [Ng??i d?ng s?ng1280](w17-react-evidence/browser-integrated/users-1280-light.png), [Ng??i d?ng s?ng390](w17-react-evidence/browser-integrated/users-390-light.png), [dialog t?i768](w17-react-evidence/browser-integrated/first-admin-768-dark.png), [Nh?t k? s?ng1280](w17-react-evidence/browser-integrated/audit-1280-light.png). Video `owner.webm` g?m l?c/trang/ch?nh s?a/x?c nh?n/quy?n/audit; c?c context B/B2/learner c? video ri?ng. Payload JSON th?t v? SQL n?m trong audit/runtime, kh?ng d?ng fetch gi? cho b?ng ch?ng n?y.

- `gate-browser-legacy-integrated`: native0, **3 ?nh/3 Axe/10 HTTP/1 SQL stage**, kh?ng pageerror/vi ph?m t? ??ng. Registry r?ng, is_first_admin=null, thao t?c h?n ch? quy?n tr?409/bootstrap_required v? kh?ng ??i role/registry/audit. DB UUID ri?ng ?? g?; kh?ng g?n bootstrap tr?n DB ch? d? ?n.
- T?ng browser hi?n h?nh43 ?nh/43 Axe. Axe c? **13 incomplete** (12 regular +1 legacy) c?n quan s?t b? sung. Ngu?n React/CSS/scripts t??ng ???ng byte v?i l??t b? sung765 ph?p ?o ? ce86f12c; c?c ?nh/s? ?o b? sung gi? source pin c? trong `manual-a11y-equivalence.json`, kh?ng nh?n ch?ng l? s? ?o m?i tr?n43 ?nh hi?n h?nh. ?? xem l?i tr?c ti?p c?c PNG users-390-light, users-1280-light v? first-admin-768-dark c?a l??t t?ch h?p, kh?ng v?/tr?n/c?t ?i?u khi?n.

### L?nh c?a ??t t?ch h?p (ch?y t? g?c worktree)

Python l? `C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe`. Wrapper v? JSON exit l?u nguy?n command/cwd/native/source SHA, kh?ng suy native0 t? stdout.

```powershell
& $wfPython scripts/w17_react_capture.py gate-build-integrated npm.cmd --prefix src/web/frontend run build
& $wfPython scripts/w17_react_capture.py gate-react-integrated npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1 --reporter=default --reporter=junit --outputFile=../../../report/w17-react-evidence/gate-react-integrated.xml
& $wfPython scripts/w17_react_capture.py gate-python-integrated $wfPython scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/cong-w17-react-integrated --junitxml=report/w17-react-evidence/gate-python-integrated.xml
$env:W17_REACT_RUN='browser-integrated'
# Kh?ng ??t W17_REACT_SMOKE ho?c W17_REACT_LEGACY trong l??t ch?nh.
& $wfPython scripts/w17_react_capture.py gate-browser-integrated $wfPython -X utf8 scripts/w17_react_runtime.py
$env:W17_REACT_RUN='browser-legacy-integrated'
$env:W17_REACT_LEGACY='1'
& $wfPython scripts/w17_react_capture.py gate-browser-legacy-integrated $wfPython -X utf8 scripts/w17_react_runtime.py
```

Kh?ng ch?y l?i v?i label/basetemp ?? c?: m?i l??t m?i ch?n t?n m?i, gi? b?ng ch?ng c?. Mutation ?? ch?y tr??c server/full gate, l?n l??t `role-presence`, `read`, `callback`, `first`, `focus`, `repeat` b?ng helper `report/w17-react-evidence-mutate.py`; m?i l??t ph?c h?i ngu?n trong finally v? ??i chi?u SHA tr??c l??t k? ti?p. Kh?ng thay m?/t?ng timeout/skip trong khi ch?y c?ng.

## Gi?i h?n v? b?n giao ?? ?i?u ph?i so?t

M?c n?y ch? React Ng??i d?ng/Nh?t k?. Kh?ng nh?n to?n W-17: B?n d?ng, Chi, Kho? m?u v? log lecture_validation v?n ngo?i ph?n React ??t n?y. Kh?ng th?m API/DTO qu?n tr? gi?, migration ho?c thay use case l?i. Kh?ng ch?y SMTP/Cloudinary/provider th?t; kh?ng c?n Cloud Figma.

DB d?ng chung ch?a ???c nh?m React migrate/g?n bootstrap. Ng??i v?n h?nh th?c hi?n theo h? s? backend ?? nh?n, sau ??i chi?u ??nh danh; kh?ng ch?n admin ??u ti?n t? h?ng ??u/ng?y t?o. Browser ch?ng minh c? registry ?? x?c l?p v? registry r?ng tr?n DB UUID t?ng h?p ri?ng.

?nh v? JSON fetch gi? trong test component ch? l? h?i quy UI; JSON HTTP/SQL, ?nh/video browser-integrated v? browser-legacy-integrated m?i l? b?ng ch?ng ??u-cu?i hi?n h?nh. C?c m?c Axe incomplete ???c gi? nguy?n v? c? h? s? b? sung ri?ng/t??ng ???ng ngu?n, kh?ng vi?t l? m?i node t? ??ng ?? ki?m. Warning ??ng k?t n?i Windows/console HTTP t? ch?i c? ch? ? v?n ???c l?u.

Commit m? ???c ki?m l? b75e611b60ca64db539b364d8dce0eb20cf4ad4f; commit b?n giao b? sung b?o c?o/b?ng ch?ng s? gi? nguy?n src/scripts, ??i chi?u to?n b? SHA trong manifest v? git diff. Kh?ng g?n l??t mutation/c?ng c? cho ngu?n m?i. Ch? ?i?u ph?i nghi?m thu/gh?p main; nh?nh v? d? li?u l?ch s? ???c gi? nguy?n, ch?a push.

### K?t qu? c?ng PostgreSQL cu?i v? tr? c?a

`gate-python-integrated`: **3.833 passed, 0 failed, 3 skipped, 1 xfailed, 8 warnings**, native exit **0**; pytest1589,62 gi?y, wrapper1621,22 gi?y. JUnit `gate-python-integrated.xml`; stdout/stderr nguy?n ? `gate-python-integrated/output.log`, l?nh/source SHA/native ? `exit.json`. Ba skip c? s?n: hai replay ??nh gi? y?u c?u DANHGIA_KHO_CHUNG (kh?ng tr? kho live chung) v? Cloudinary live ch?a b?t; m?t xfail l? replay answer-2 c?, kh?ng tr? ti?n ?? ghi l?i. Kh?ng ??i assertion/skip/threshold c?a test ?? c? k?t qu? n?y. Ca checkpoint c? l?i peak3/4 ?? ?i qua trong c?ng ??y ?? m?i, gi? nguy?n ngu?n test v? l?ch s? th?t b?i.

T?m t?p report W-06/W-14 do full gate ghi ?? ph?c h?i byte g?c ? finally; b?n JSON m?i gi? d??i gate-python-integrated/legacy-test-output. SQL m?i W-15/W-25 ???c ordinary-copy sang evidence c?a v? v? ??i chi?u SHA, gi? nguy?n ngu?n local. `git diff -- src scripts` r?ng su?t l??t; sau c?ng kh?ng c?n tracked diff ngo?i v?. **?? tr? c?a PostgreSQL khi native0 ho?n t?t**, kh?ng c?n full gate/server W-17 ?ang ch?y. Chi ph? nh? cung c?p0 USD.

`gate-summary.json`, `mutation-summary.json`, `preserved-source.json`, `manual-a11y-equivalence.json`, `privacy-scan.json` v? `manifest.json` l? ?i?m v?o h? s?. Manifest b?m to?n b? src/scripts tracked, ngu?n thi?t k? v? t?ng b?ng ch?ng/b?o c?o/helper; tested-source.zip ch?a ch?n t?p m?/test/harness thay ??i so v?i n?n ???c ch?t. Kh?ng c? c?u h?i c?n ch?n ph?m vi React W-17.1; thao t?c operator tr?n DB d?ng chung v? c?c m?c W-17 c?n l?i gi? ngo?i ??t n?y.

Byte b?ng ch?ng d??i w17-react-evidence ???c gi? -text; report/.gitattributes ch? ghim LF cho helper/b?o c?o W-17.1 ?? checkout Windows kh?ng ??i hash ?? b?n giao. Kh?ng thay quy t?c t?p c?a v? kh?c. ?? ??i chi?u SHA c?a t?ng blob staged v?i manifest, ngo?i ki?m file working tree.
