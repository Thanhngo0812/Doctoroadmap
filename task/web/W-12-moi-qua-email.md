# W-12 — Mời qua email, lời mời trong ứng dụng

**Phân công sau nghiệm thu lần 8, 2026-10-26:** lõi đã xong mốc backend W-04, được giao **mốc backend W-12** trong nhánh/worktree mới; web làm React/tích hợp sau W-16/W-04. Dùng lại SharingService/AuthStore/Mailer W-03/W-11; thêm invitation/migration đúng một head, 50 email/lần, 200 thư/chủ/ngày, TTL 7 ngày, đúng email đã xác minh và membership nguyên tử. Mẫu thư dùng FakeMailer/0 USD; không gửi thư thật, không tự đóng toàn W-12 từ backend. [biên bản lần 8](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan8-2026-10-26.md) và [lời giao lần 8](../../report/lenh-giao-viec-ba-nhom-lan8-2026-10-26.md).

**Nguồn chân lý:** [spec chức năng](../../doc/web-chuc-nang-spec.md), mục 6 (mời theo email), user story 36–37; [spec cơ sở dữ liệu](../../doc/web-co-so-du-lieu-spec.md),
bảng `invitation`; spec thiết kế, hộp mời, khối lời mời ở trang chủ, mẫu thư.
**Ai:** lõi làm mốc backend/mẫu thư; web làm React/tích hợp · người soát kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** W-03, W-11 · **Trạng thái:** ready-for-agent

## Vì sao

Giảng viên hay trưởng nhóm thường có sẵn danh sách email. Mời đúng người an toàn hơn một link có thể bị chuyển tiếp.

## Cần làm

**`SharingService`:** `invite_by_email`, `list_course_invitations`, `cancel_invitation`, `list_my_invitations`, `accept_invitation`, `decline_invitation`.
- Tối đa 50 email mỗi lần, 200 thư mỗi chủ khoá mỗi ngày. Email trùng trong một lần gửi được gộp.
- **Email đã có tài khoản:** lời mời `pending`, hiện ở trang chủ của người đó, kèm thư báo.
- **Email chưa có tài khoản:** thư có link đăng ký mang token mời. Khi một tài khoản **xác minh** đúng email đó, mọi lời mời `pending` cùng email được gắn vào
  tài khoản.
- **Mời lại** cùng email làm mới lời mời cũ, không tạo hàng thứ hai.
- Lời mời hết hạn sau 7 ngày; chủ khoá huỷ được lời mời đang chờ.
- Chấp nhận thì thêm `membership` với `via = email`; khoá đã đầy thì `course_full`.
- **Chưa xác minh email** thì không mời được (`email_unverified`).
- Mẫu thư "bạn được mời vào khoá …".
- Nhật ký: `invitation_sent`, `invitation_accepted`, `invitation_declined`, `invitation_cancelled`.

**HTTP:** `POST/GET /courses/{cid}/invitations`, `DELETE /courses/{cid}/invitations/{iid}`, `GET /me/invitations`, `POST /invitations/{iid}/accept`,
`POST /invitations/{iid}/decline`.

**Di trú:** `invitation`.

**Giao diện:**
- **hộp "Mời qua email"** trong hộp chia sẻ: dán nhiều email, cách bằng dấu phẩy hay xuống dòng; báo email sai định dạng; danh sách lời mời đang chờ với nút
  huỷ;
- **khối "Lời mời"** ở trang "Khoá học của tôi": chấp nhận hay từ chối, kèm thông báo dữ liệu như W-11.

## Tiêu chí nghiệm thu

Mỗi test thấy đỏ trước trên bản sai:
- [ ] Mời một email chưa có tài khoản; đăng ký bằng email đó **chưa xác minh** thì chưa thấy lời mời; xác minh xong thì thấy.
- [ ] Đăng ký bằng email khác rồi mở link mời: không được gắn lời mời.
- [ ] Mời lại cùng email: vẫn một hàng `pending`, hạn được làm mới.
- [ ] Lời mời quá 7 ngày (đồng hồ giả) không chấp nhận được.
- [ ] Thư thứ 201 trong ngày của một chủ khoá bị `rate_limited`.
- [ ] Người không phải người được mời không chấp nhận được lời mời (`not_found`).
- [ ] Ảnh chụp hộp mời, khối lời mời; một thư mời xuất ra HTML.

## Ngoài vé

Nhập danh sách từ tệp CSV. Nhắc lại lời mời tự động.
