# Kế hoạch nhóm web — W-03, 2026-10-20

**Trạng thái:** đã lập kế hoạch, chưa bắt đầu triển khai W-03.
**Phạm vi đã làm rõ với chủ dự án:** nhóm web nhận W-03; W-04 xét sau. W-06 do nhóm lõi chủ trì, không thuộc kế hoạch triển khai này. Điểm phối hợp bắt buộc là bàn giao migration W-03 để lõi nối migration W-06.

## 1. Đầu vào và kết luận

- [Báo cáo điều phối](dieu-phoi-nghiem-thu-w02-w05-w24-2026-10-20.md): W-02/W-05 đạt nghiệm thu local; giữ kết quả đó làm nền. Số test điều phối báo là kết quả đã có, không phải lượt chạy mới của kế hoạch này.
- [Vé W-03](../task/web/W-03-xac-minh-email-quen-mat-khau.md) và [kế hoạch chung](../task/web/00-ke-hoach.md) là phạm vi và tiêu chí nghiệm thu.
- Chỉ hai nhóm bằng chứng Figma/prototype của W-24 còn mở. Chúng thuộc nhóm thiết kế và không chặn W-03. Không giao lại lỗi màu tối, tràn auth, GIF hoặc vùng bấm đã đạt.
- Mã hiện có: AccountService/AuthStore, kho PostgreSQL và bộ nhớ, guard Origin/CSRF, validation mật khẩu, WebSettings SMTP/TTL, port Mailer. Tái sử dụng các phần này, không xây lại xác thực W-02.
- Tham khảo thiết kế: design/preview/w03_auth_screens.html, token và spec giao diện. Preview local không được coi là bằng chứng Figma đã nghiệm thu.
- Cấu hình Gmail đã được chủ dự án thêm vào env; không yêu cầu cung cấp lại và không đưa bí mật vào tài liệu. Kế hoạch/kiểm tự động không gửi thư thật.

## 2. Phân công khi triển khai

| Vai trò | Phần việc | Ranh giới |
|---|---|---|
| Luna backend | Schema, token, AccountService, luật xác minh, API và guard | Chủ sửa accounts.py/auth_store/auth.py; migration W-03 do đầu mối này tạo |
| Luna frontend | Ba trang React, dải nhắc xác minh, liên kết từ đăng nhập, các trạng thái và kiểm thử UI | Theo taste skill và tài liệu thiết kế; không nhận giao diện W-06 |
| Luna mailer | Mailer fake/console/SMTP, ba mẫu thư tiếng Việt, test adapter và HTML mẫu | Không sửa AccountService; chốt hợp đồng Mailer trước khi chạy song song |
| Agent chính | Chốt hợp đồng, điều phối phần dùng chung, ghép composition, soát và nghiệm thu | Một người ghép migration/composition; không tự nhận nghiệm thu thay điều phối |

Không khởi chạy agent hay giao việc sang phiên nhóm khác trong lượt chỉ lập kế hoạch này. Thiết kế bàn giao màn/trạng thái W-03; lõi nhận mốc migration qua chủ dự án hoặc handoff của nhóm web.

## 3. Các bước và tiêu chí kiểm

### Bước 1 — Hợp đồng và schema sớm

- [ ] Chốt request/response/lỗi cho bốn POST: /api/v1/auth/verify-email, /auth/resend-verification, /auth/password-reset/request, /auth/password-reset/confirm (cùng tiền tố /api/v1).
- [ ] Chốt thay đổi tối thiểu của Mailer hiện có để hỗ trợ mẫu thư HTML và bản văn bản; chốt cách xử lý lỗi SMTP mà không làm lộ email tồn tại hay làm hỏng luồng đăng ký đã tạo tài khoản.
- [ ] Tạo đúng một migration w03_0004, down_revision=w02_0003, bảng email_token theo spec. Tái sử dụng rate_limit_event và audit_event đã có.
- [ ] Kiểm nâng DB rỗng, nâng DB ở W-02, metadata và một Alembic head trên PostgreSQL thật; không sửa migration cũ.

**Bàn giao:** commit/schema w03_0004 và kết quả kiểm cho nhóm lõi; lõi nối w06_0005 sau đó. Không chờ hoàn thành toàn bộ giao diện W-03 mới bàn giao schema. Quy mô: chia hợp đồng và migration thành hai phần nhỏ nếu cần.

### Bước 2 — Đăng ký → thư xác minh → xác minh email

- [ ] Token ngẫu nhiên 32 byte; DB chỉ giữ SHA-256, purpose/email lúc gửi, thời hạn và used_at. Tiêu thụ token nguyên tử để hai yêu cầu đồng thời không cùng thành công.
- [ ] Đăng ký mới gửi đúng một thư xác minh qua fake Mailer; đăng ký trùng gửi mẫu “bạn đã có tài khoản” nhưng giữ nguyên phản hồi và quyết định tự đăng nhập đã chốt trong W-02.
- [ ] Xác minh thành công cập nhật email_verified_at và audit; token đã dùng, hết 24 giờ, sai purpose hoặc email tài khoản đã đổi bị từ chối.
- [ ] React /xac-minh hiển thị đang xử lý, thành công, link sai/hết hạn/đã dùng; cập nhật lại trạng thái tài khoản sau thành công.

**Kiểm:** service trên fake store/đồng hồ/Mailer và PostgreSQL; token thô không có trong DB; test yêu cầu đồng thời. React và browser kiểm trạng thái thật, không chỉ tên nút. Các thao tác xác minh thay đổi dữ liệu đi qua POST, không làm GET backend tiêu thụ token.

### Bước 3 — Gửi lại xác minh và luật quyền

- [ ] Dải nhắc đúng câu “Xác minh email để mời bạn qua email”, nút gửi lại có pending/success/lỗi.
- [ ] Gửi lại tối đa ba lần/giờ, lần thứ tư bị rate_limited; giới hạn dùng DB chung và đồng hồ giả để kiểm biên.
- [ ] Resend yêu cầu phiên và CSRF; luật email_unverified chặn hành động mời email giả trong test. Việc tải sách, học và tạo link không bị thêm điều kiện xác minh.

**Kiểm:** guard từ chối CSRF thiếu/sai, Origin thiếu/sai và vượt tần suất; kết quả gửi thư quan sát qua fake Mailer. Hành động mời email thật vẫn ở W-12.

**Checkpoint A:** luồng xác minh chạy đầu-cuối; migration đã bàn giao; hồi quy auth W-02 còn đạt.

### Bước 4 — Quên → đặt lại mật khẩu

- [ ] /quen-mat-khau luôn trả phản hồi chung cho email có/không có tài khoản; email không tồn tại không sinh thư. Throttle tối đa ba yêu cầu/email/giờ áp dụng nhất quán để không tạo nhánh tiết lộ sự tồn tại của email.
- [ ] /dat-lai-mat-khau có mật khẩu mới/xác nhận, dùng lại chính sách 8–128 ký tự và blocklist; token reset riêng purpose, hạn 60 phút, dùng một lần.
- [ ] Đổi mật khẩu, đánh dấu token và thu hồi mọi phiên trong cùng giao dịch. Sau thành công đưa về đăng nhập với thông báo rõ ràng, không tự đăng nhập lại.
- [ ] Ghi password_reset_requested/password_reset_done; không ghi token thô hoặc mật khẩu vào audit/log ứng dụng.

**Kiểm:** hai phiên trên hai trình duyệt/kết nối đều mất hiệu lực; mật khẩu cũ không đăng nhập được, mật khẩu mới được; sai purpose/hết hạn/dùng lại/đồng thời bị chặn; lỗi validation không làm đổi mật khẩu. Giữ thông báo bên phải, khung vừa chữ và text căn giữa theo yêu cầu mới nhất.

### Bước 5 — Hoàn thiện ranh giới HTTP và SMTP

- [ ] Bảng chính sách rõ: verify/reset request/reset confirm dùng Origin hợp lệ và token theo chức năng, không bắt buộc phiên cũ; resend dùng Origin + phiên + CSRF. Chỉ ngoại lệ đúng POST công khai được liệt kê, không tháo guard toàn cục.
- [ ] Test route công khai vẫn từ chối Origin thiếu/null/ngoài danh sách; route mới không được làm lọt kiểm unsafe-route có sẵn.
- [ ] Mailer console cho dev, fake giữ thư cho test, SMTP theo env hiện có, Gmail STARTTLS 587. Adapter SMTP kiểm bằng kết nối giả; không chặn event loop và không giữ giao dịch DB mở trong khi gửi thư.
- [ ] Ba mẫu thư tiếng Việt có logo, link cùng nguồn cấu hình tin cậy, HTML và văn bản; dữ liệu người dùng được escape. Xuất HTML mẫu bằng dữ liệu giả.

**Kiểm:** kết nối SMTP giả ghi nhận STARTTLS/auth/send đúng thứ tự; lỗi gửi có test; không gọi Gmail thật và không đưa mật khẩu/token vào log SMTP. Console dev chỉ xuất thư để thử theo yêu cầu vé, không bật xuất nội dung thư trong production.

### Bước 6 — Nghiệm thu và handoff W-03

- [ ] Chạy service tests bằng fake và PostgreSQL bắt buộc; HTTP/Origin/CSRF tập trung; React và production build. PostgreSQL thiếu là fail, không skip.
- [ ] Browser 390/768/1280, sáng/tối, giảm chuyển động; kiểm ba trang và banner, focus/bàn phím, lỗi nhỏ dưới trường đỏ, xoá lỗi khi đổi form, thông báo và menu W-02 không hồi quy.
- [ ] Kiểm luồng thật trên DB riêng với fake Mailer: đăng ký → lấy link từ thư → xác minh; quên → lấy link → reset → mọi phiên cũ bị từ chối → đăng nhập mật khẩu mới.
- [ ] Mỗi bất biến gắn assertion có tên. Lưu bằng chứng đỏ trên bản sai, gồm bỏ kiểm used_at/hạn token, bỏ thu hồi phiên và mở sai ngoại lệ CSRF; không tính lỗi setup là guard bắt được sai.
- [ ] Bàn giao commit, XML/JSON kết quả, ví dụ JSON API, HTML thư, ảnh/video, migration head và giới hạn chưa kiểm. Không nhận “đạt” nếu mới xong backend.

**Checkpoint B:** W-03 đủ lát dọc và bằng chứng để điều phối nghiệm thu local. Chi phí mô hình dự kiến 0 USD; Cloudinary không có thay đổi trong vé.

## 4. Thứ tự làm và phần hoãn

1. Chốt hợp đồng và migration trước để gỡ điểm ghép schema cho nhóm lõi.
2. Sau hợp đồng, backend xác minh, Mailer và React xác minh có thể làm song song trong phạm vi tệp riêng.
3. Hoàn thành xác minh/gửi lại rồi hoàn thành quên/đặt lại; agent chính ghép và kiểm sau mỗi lát dọc.
4. W-04 chỉ xem xét khi W-03 ổn định và không còn tranh AccountService; chưa đưa W-04 vào phần đang triển khai.
5. W-06 thuộc nhóm lõi; W-14/W-15/W-23 chưa mở trong kế hoạch này. Không sửa src/doc2roadmap/.

## 5. Lệnh kiểm dự kiến

Tên tệp test W-03 chốt khi triển khai; không ghi chúng là đã tồn tại hoặc đã chạy.

- PostgreSQL: dùng scripts/w05_run_tests.py với tập backend auth/W-03, --basetemp riêng và -p no:cacheprovider theo runner.
- React: npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1.
- Build: npm.cmd --prefix src/web/frontend run build.
- Browser: bổ sung script W-03 riêng dựa trên runner W-02, DB/profile cô lập, fake Mailer; kiểm UI mô phỏng API ghi rõ là mô phỏng.

Kế hoạch nằm trong report/ theo tổ chức tài liệu web hiện có; không ghi đè tasks/plan.md và tasks/todo.md của công việc lõi. Không thay đổi vé hoặc kế hoạch điều phối khi chưa triển khai.
