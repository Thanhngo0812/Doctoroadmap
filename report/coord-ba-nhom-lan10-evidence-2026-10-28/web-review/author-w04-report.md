# W-04 — React hồ sơ và phiên đăng nhập

## Phạm vi bàn giao

Nhánh `work/w04-account-react`, worktree `tmp/w04-account-react`, main nền
`4c69322c9ee23f65902a2ab4f42b519c5e4ca828`. Backend W-04 `c1f2fe9` đã nhận;
không đổi backend, use case lõi, migration, vé/kế hoạch/handoff. Chỉ điều phối quyết định nghiệm thu/ghép.
Mốc nguồn sản phẩm và harness cuối: `bc4349fd7369af467f7064bf88794a118800d529`.
Commit bằng chứng/báo cáo được ghi ở lịch sử nhánh; mã `src/` và `scripts/` không đổi sau cổng.

Trang `/tai-khoan` có ba khối: tên/email/trạng thái xác minh; đổi mật khẩu; đăng xuất mọi nơi
có xác nhận. Tái dùng PATCH `/me`, POST `/me/password`, POST `/auth/logout-all` và gửi lại xác minh W-03.
Tên trim rồi kiểm 1–60 ký tự. Mật khẩu 8–128; danh sách mật khẩu phổ biến do backend W-02 kiểm.
Lỗi `fields.loc` dạng chuỗi/mảng gắn đúng trường; sai mật khẩu hiện tại không xoá phiên hiện hành.
Trạng thái đang gửi/thành công/lỗi, trường đỏ và thông báo nhỏ; không hiện outline xanh trên trường lỗi.

Mật khẩu chỉ nằm trong state form, xoá sau thành công/rời trang. Một yêu cầu mutation đang hoạt động
cho mỗi form; abort khi unmount và epoch ở AuthProvider chặn phản hồi của phiên cũ ghi đè tài khoản mới.
Logout-all xác nhận trước POST, xoá account/CSRF và chuyển an toàn về đăng nhập. Không thêm thiết bị/xoá tài khoản.

## Nguồn và thiết kế

Đã đối chiếu AGENTS.md, quy trình nhánh/fixture, vé W-04, spec chức năng mục 2/10/11,
spec thiết kế, backend/public JSON và OpenAPI hiện hành, `design/preview/w04_profile_screens.html`.
Áp dụng design-taste-frontend (app screens), frontend-ui-engineering, TDD, Git và security.
Câu hỏi của màn: “Tôi đang dùng tài khoản nào, và thay đổi cách đăng nhập ở đâu?”
Danh tính ở trước, mật khẩu riêng một khối, thao tác huỷ phiên nằm cuối và có xác nhận.
Giữ Be Vietnam Pro, logo Artboard 24/28 và token main; không nhập nhánh thiết kế chưa được nhận.

Taste draw đối chiếu: `achromatic-ledger`, seed `714672961`, giữ palette/type.
Direction được ghi sau vòng dựng đầu để soát màn đang có, không tuyên bố draw trước implementation.
Giữ bề mặt phẳng, đường viền nhẹ, không chart/KPI/trang trí giả. Token xanh/nút và shell hiện hành
được ưu tiên theo yêu cầu thương hiệu, thay vì đổi sang primary đen/sidebar từ sheet.
390 px xếp dọc; 768/1280 chia danh tính/mật khẩu; logout-all cùng hàng trên desktop.
Phản hồi dùng motion 200 ms, trường 120 ms; reduced-motion tắt animation thông báo.
Heading nhận focus khi mở trang, không vẽ khung trên heading; focus controls/bàn phím vẫn hiện.

Inspector app tại 1280/768/390: 0 FAIL, 1 WARN `panel-void` 44 px trong khối danh tính.
Khoảng này dành chỗ phản hồi gửi lại xác minh, để form tên không nhảy khi thông báo xuất hiện;
không kéo dài panel cho bằng cột bên cạnh (`align-items:start`). Bản DOM dùng để inspect chỉ là bản
thiết kế của trang HTTP thật, bỏ script và xoá giá trị input mật khẩu; không thay bằng chứng HTTP/SQL.

## RED, guard và lịch sử được giữ

- `react-red`: 8 assertion fail trên màn hồ sơ chỉ đọc trước thay đổi, không setup error.
  Các GREEN phát triển nằm trong `react-green2`/`account-green3`; xem lệnh/native trong `exit.json`.
- `build-check1` lỗi typing test `getByRole(...exact)`; sửa option không hợp lệ, không giảm assertion.
- `react-green1` một lỗi mock thông báo mật khẩu không khớp backend; sửa dữ liệu mock theo hợp đồng.
- `transition-red` là tên lượt kiểm ban đầu, **thực tế native 0**: control chuyển trang cập nhật muộn
  đã xanh; không dùng nó làm RED và không sửa guard theo giả thuyết chưa tái hiện.
- Browser smoke1 lỗi setup thiếu khóa `atomic`; smoke2 bắt lỗi focus sau Escape. Đã sửa đóng dialog
  trước khi trả focus nút mở. `focus-red-source.json` ghi hash mã phát triển của lượt này.
- Smoke3 đã qua luồng A/B nhưng lỗi thu JSON khi đóng browser; lượt final1 gặp đọc body sau điều hướng
  và so border trước khi transition màu kết thúc. Giữ audit/log; không gọi các lượt này là browser đạt.
  Harness cuối clone/đọc JSON trước khi ứng dụng nhận response và chờ animation trước phép so màu;
  không mock HTTP hoặc bỏ assertion.
- `mutation-stale-identity-final`: bỏ riêng guard epoch của refresh trên nguồn `bc4349fd`, test
  `a profile refresh from the old session cannot resurrect A after logout-all and login as B`
  fail assertion tại tài khoản B bị ghi đè, 0 setup error. Phục hồi nguyên byte và kiểm SHA trong
  `mutation-restored-final.json`, rồi chạy cổng trên mã đã phục hồi. Mutation trước ở `e20b1841`
  vẫn giữ riêng; không gán receipt cũ cho nguồn cuối.
- `gate-python-final1` chủ động dừng đúng pytest leaf của W-04 sau 205,52 giây để chốt harness;
  native `4294967295`, không có JUnit hoàn chỉnh, không phải GREEN. Không dừng nhóm khác/dọn fixture.

## Browser/HTTP/PostgreSQL cuối

`gate-browser-final2` native 0, nguồn `bc4349fd`, runtime `dirtySourcePaths=[]`.
DB UUID riêng, schema `w12_0008`, real AccountService/Argon2/PostgreSQL/HTTP; clock và Mailer giả.
Không gọi model/embedding/media/SMTP/Cloudinary. DB riêng đã được huỷ sau kiểm, server đã dừng.
12 cấu hình (390/768/1280 × sáng/tối × thường/giảm chuyển động), 38 ảnh, 38 Axe document,
2 video A/B, 70 JSON HTTP đã che trường nhạy cảm. 0 Axe violations, 0 pageerror.

Đã kiểm overflow/vùng bấm 44 px, focus lỗi đỏ, mặc định focus “Giữ đăng nhập”, Escape trả focus
đúng nút mở, form đang gửi bị khoá, motion giảm theo emulation media hệ điều hành Chromium.
Các lỗi console giữ nguyên trong audit: 16 lỗi tải HTTP 401 có chủ đích; 38 cảnh báo CSP chặn
Google-font connect và 38 cảnh báo style injection của lượt Axe. Không tuyên bố console hoàn toàn sạch;
không nới CSP để làm sạch log. Inspector font thực tải và đo riêng.
Đã kiểm bổ sung bằng CDP `CSS.getPlatformFontsForNode` trên heading trang HTTP thật:
`Be Vietnam Pro`, `isCustomFont=true`, 17 glyph; không chỉ dựa vào computed font-family hoặc DOM clone.
Nguồn/lệnh/native 0 tại `font-proof/`, kết quả `browser-font-proof/font-proof.json`.
Soát thị giác độc lập các ảnh 390/768/1280 sáng/tối không tìm thấy Required về bố cục/focus;
phép kiểm font bổ sung giải quyết điểm chưa chắc từ cảnh báo CSP trong lượt Axe.

SQL qua engine/connection độc lập kiểm tên sau PATCH; sai mật khẩu/CSRF/tên 61 không đổi dữ liệu;
đổi mật khẩu từ A giữ A (1 phiên), B `/me` trả 401, password cũ không đăng nhập được, password mới dùng được.
Sau B đăng nhập lại có 2 phiên; logout-all từ A đưa cả A/B về 401 và số phiên về 0;
phiên tài khoản khác vẫn 1. Audit password_changed/logout_all không chứa secret.
GET `/me` cũ được giữ sau HTTP thật rồi trả sau đăng nhập tài khoản khác: UI vẫn là Bình.
URL/history/localStorage/sessionStorage không chứa mật khẩu tổng hợp của kiểm thử.

Ảnh xem nhanh: [1280 sáng](w04-react-evidence/browser-final2/profile-1280-light.png),
[390 tối](w04-react-evidence/browser-final2/profile-390-dark.png),
[xác nhận](w04-react-evidence/browser-final2/logout-confirm-1280-light.png).
Video [A](w04-react-evidence/browser-final2/a.webm), [B](w04-react-evidence/browser-final2/b.webm).
JSON/SQL và phạm vi Axe tại `browser-final2/audit.json`; DB/runtime ở `browser-final2/runtime.json`.

## Cổng cuối

Chủ dự án xác nhận cửa PG trống: “Cổng trống; web chạy khi chốt mã”. Mỗi lượt full gate một mình;
browser dùng UUID DB độc lập. Main nền kiểm lại trước cổng vẫn `4c69322c`.
Lệnh/native/source SHA đầy đủ trong các thư mục capture; basetemp chỉ dưới `tmp/`.

```text
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/cong-w04-react-final2 --junitxml=report/w04-react-evidence/gate-python-final2.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1 --reporter=default --reporter=junit --outputFile=../../../report/w04-react-evidence/gate-react-final2.xml
npm.cmd --prefix src/web/frontend run build
```

Cổng Python cuối: **3407 pass, 0 fail/0 error, 3 skipped và 1 xfailed**; phân loại chi tiết trong JUnit/log. React: **239 pass**, build native 0 (`build-check4`), browser native 0. Full PG native 0, nguồn `bc4349fd`, không đổi mã sau kiểm. Fixture copy từ hai manifest W-06, kiểm hash nguồn/đích
3145 tệp thường trong `fixture-copy.json`; PDF candidate phát triển cần cho gate cũng copy/hash riêng
trong `candidate-copy.json`. Không link dữ liệu, không đọc held-out/live CLI learner store, không seed DB chủ dự án.

## Giới hạn và việc kế tiếp

Bằng chứng browser dùng dữ liệu tài khoản tổng hợp, HTTP/PG thật; không phải mock DTO thay cho auth.
Không gửi thư thật. Không tự ghép main hoặc tự đánh dấu vé đạt. W-12 React sẽ ở nhánh/worktree khác
từ main hiện hành sau bàn giao W-04; backend W-12 đã nhận không được tính là UI đã hoàn tất.

Bằng chứng lịch sử browser dạng text nguyên byte ở `historical-browser-text-originals.zip`; ảnh/video thử cũ giữ local, không trộn với ảnh browser cuối. Log/XML được Git giữ nguyên byte (`-text`, `-diff` cho log/XML), không chuẩn hoá làm thay hash. SHA nguồn/bằng chứng ở `manifest.json`. SQL phát sinh từ guard W-15/W-25 được chép vào thư mục W-04 có receipt hash; bản local gốc không xoá và không stage vào vé này.
