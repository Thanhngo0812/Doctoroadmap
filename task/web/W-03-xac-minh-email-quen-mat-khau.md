# W-03 — Xác minh email, quên mật khẩu, cổng gửi thư

**Nguồn chân lý:** [spec chức năng](../../doc/web-chuc-nang-spec.md), mục 2 (xác minh, quên mật khẩu, gửi thư), mục 3 (quyền khi chưa xác minh);
[spec cơ sở dữ liệu](../../doc/web-co-so-du-lieu-spec.md), bảng `email_token`; spec thiết kế, trang xác minh và đặt lại mật khẩu, mẫu thư.
**Ai:** nhóm web · người soát kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** W-02 · **Trạng thái:** đang làm, snapshot `fdd0620`, chưa nghiệm thu toàn vé

**Chuyển worktree 2026-10-20:** nhánh `work/w03-email-recovery`, thư mục `tmp/w03-email-recovery`; nhận main mới theo
[quy trình nhánh](../../doc/quy-trinh-nhanh-va-ghep-main.md). Không làm hay đổi nhánh trong thư mục chung.
Checkpoint `33c70ac` và snapshot `fdd0620` chưa được nghiệm thu W-03. Các commit mang theo `781415b`/`79cb9c9`/`6cd6be7` cũng chưa được soát;
phần thiết kế cần phán xét W-24 trước khi W-03 được ghép. Xem [biên bản chuyển và cổng main](../../report/dieu-phoi-ghep-main-2026-10-20.md).

**Đợt giao 2026-10-20:** W-02 đã nghiệm thu; đây là ưu tiên tiếp theo của web. Thiết kế phối hợp trang/trạng thái xác minh và đặt lại mật khẩu.
Migration dành tên `w03_0004`, nối head đã kiểm `w02_0003`; bàn giao mốc schema cho W-06 trước khi ghép migration khoá học.
Các route công khai request/confirm/verify phải nêu rõ chính sách Origin/CSRF và test cả đường từ chối; không tháo guard toàn cục.
Resend dùng phiên vẫn cần CSRF. Test thư bằng Mailer giả; không tự gửi thư thật. Xem
[kế hoạch và điểm kiểm](../../report/dieu-phoi-nghiem-thu-w02-w05-w24-2026-10-20.md).

## Vì sao

Mời người khác qua email gửi thư cho người lạ bằng tài khoản Gmail của dự án, nên chỉ tài khoản có email thật mới được làm. Người quên mật khẩu cũng cần lấy lại tài
khoản.

## Cần làm

**Port `Mailer`:**
- bản `console` ghi thư ra log (dev) và bản giả giữ thư trong bộ nhớ (test);
- bản `smtp` theo cấu hình (máy chủ, cổng, TLS, tài khoản, mật khẩu từ biến môi trường).
- **Mẫu thư tiếng Việt,** có logo theo spec thiết kế: xác minh email, đặt lại mật khẩu, "bạn đã có tài khoản". Các mẫu thư lời mời và bản dựng thêm ở W-12,
  W-14.

**`AccountService`:** `verify_email`, `resend_verification`, `request_password_reset`, `reset_password`.
- Token 32 byte, chỉ lưu băm, dùng một lần.
  - Xác minh: hạn 24 giờ; gửi lại tối đa 3 lần mỗi giờ.
  - Đặt lại mật khẩu: hạn 60 phút; tối đa 3 yêu cầu mỗi email mỗi giờ.
- Xác minh chỉ có hiệu lực khi email của token còn trùng email hiện tại của tài khoản.
- `request_password_reset` luôn trả cùng phản hồi, dù email có tài khoản hay không.
- Đặt lại thành công thì huỷ **mọi** phiên của tài khoản.
- Đăng ký trùng email (từ W-02) nay gửi thư "bạn đã có tài khoản".
- Nhật ký: `email_verified`, `password_reset_requested`, `password_reset_done`.

**Phân quyền:** thêm hàng "chưa xác minh thì không được mời theo email" vào bảng luật (bản demo: tải sách và tạo link không cần xác minh). Lỗi
`email_unverified`. Vé này chỉ thêm luật và test luật trên một hành động giả; hành động thật nối ở W-12.

**SMTP:** Gmail (`smtp.gmail.com`, cổng 587, STARTTLS) với mật khẩu ứng dụng; tài khoản và mật khẩu chỉ ở `.env`. Thiếu thì hỏi chủ dự án.

**HTTP:** `POST /auth/verify-email`, `POST /auth/resend-verification`, `POST /auth/password-reset/request`, `POST /auth/password-reset/confirm`.

**Di trú:** `email_token`.

**Giao diện:**
- dải nhắc "Xác minh email để mời bạn qua email", có nút gửi lại;
- trang mở từ link trong thư: xác minh xong, link hết hạn, link đã dùng;
- trang "Quên mật khẩu" và "Đặt mật khẩu mới".

## Tiêu chí nghiệm thu

Mỗi test thấy đỏ trước trên bản sai:
- [ ] Đăng ký xong thì `Mailer` giả có đúng một thư xác minh; mở link thì `email_verified_at` có giá trị; mở lần hai thì bị từ chối.
- [ ] Token xác minh quá 24 giờ theo đồng hồ giả bị từ chối.
- [ ] Gửi lại xác minh lần thứ 4 trong một giờ bị `rate_limited`.
- [ ] Yêu cầu đặt lại với email không có tài khoản: cùng phản hồi, và không có thư nào.
- [ ] Token đặt lại dùng lần hai hay quá 60 phút bị từ chối. Đặt lại xong thì mọi phiên cũ bị `unauthenticated`.
- [ ] Đổi email (giả lập trong test) thì token xác minh cũ không còn hiệu lực.
- [ ] Bảng `email_token` không có token thô.
- [ ] Ảnh chụp dải nhắc và ba trang; một thư mẫu xuất ra HTML.

## Ngoài vé

Đổi email (chưa có trong spec). Đăng nhập bằng Google.
