# W-20 — Xoá tài khoản, xoá khoá học, dọn artifact mồ côi

**Quyết định chủ dự án 2026-10-28:** admin đầu tiên không được xoá tài khoản, kể cả tự xoá có mật khẩu. Kiểm phía server theo định danh được bảo vệ bền vững, không chỉ ẩn nút; giữ giao dịch/bảo toàn dữ liệu học và sổ chi của các tài khoản khác. [ADR 0030](../../doc/adr/0030-bao-ve-tai-khoan-admin-dau-tien.md). W-20 chưa được nhận hoàn tất; điều kiện này bắt buộc khi triển khai.

**Nguồn chân lý:** [spec chức năng](../../doc/web-chuc-nang-spec.md), mục 5 (xoá khoá), user story 14, 32; [spec cơ sở dữ liệu](../../doc/web-co-so-du-lieu-spec.md), mục 6
(thủ tục xoá tài khoản), mục 7; [ADR 0020](../../doc/adr/0020-khoa-hoc-la-don-vi-chia-se-du-lieu-hoc-theo-nguoi-va-cuon.md).
**Ai:** nhóm web · người soát kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** W-11, W-14 · **Trạng thái:** ready-for-agent

## Vì sao

Người dùng phải rời hệ thống sạch được. Chủ khoá phải dọn được khoá tạo nhầm. Không được mất dữ liệu học của người khác, và không được để sổ chi lệch.

## Cần làm

**`CourseService.delete_course`:**
- chỉ chủ khoá; phải gõ lại tên khoá;
- xoá khoá học, thành viên, link, lời mời, báo lỗi;
- **giữ** dữ liệu học của các thành viên;
- nhật ký `course_deleted`.

**`AccountService.delete_account`:**
- cần mật khẩu;
- chạy đúng thủ tục ở spec cơ sở dữ liệu mục 6, trong một giao dịch;
- còn là chủ của khoá có thành viên khác thì `owns_shared_courses`.

**Lệnh admin `web gc-orphans --dry-run`:**
- liệt kê tệp tải lên, `media_asset` và artifact của `doc_id` không còn khoá học nào trỏ tới;
- khi xoá thật thì xoá cả trên Cloudinary qua `MediaStore`, rồi mới xoá hàng trong cơ sở dữ liệu;
- chỉ xoá khi bỏ `--dry-run`;
- không bao giờ chạm `doc_id` của sáu cuốn phát triển hay `doc_id` không bắt đầu bằng `u-`.

**Việc dọn định kỳ** ở spec cơ sở dữ liệu mục 7: lệnh `web cleanup`.

**HTTP:** `DELETE /courses/{cid}`, `DELETE /me`.

**Giao diện:**
- vùng "Nguy hiểm" ở trang quản lý khoá và trang hồ sơ;
- hộp xác nhận nói rõ cái gì bị xoá và cái gì còn lại;
- lỗi `owns_shared_courses` liệt kê các khoá cần xử lý trước.

## Tiêu chí nghiệm thu

Mỗi test thấy đỏ trước trên bản sai:
- [ ] Tài khoản admin đầu tiên không bị xoá qua service/API, kể cả có mật khẩu; không chạy dở thủ tục xoá/ẩn danh/sổ chi trước khi từ chối.
- [ ] Xoá tài khoản thì kho Pha B không còn bản ghi nào có `owner` là người đó; tổng `cost_usd` của sổ chi không đổi; không dòng nào mang `learner_id` cũ.
- [ ] Còn là chủ khoá có thành viên khác thì từ chối, và không xoá gì (giao dịch).
- [ ] Xoá khoá học thì bản ghi Pha B của các thành viên còn nguyên.
- [ ] `gc-orphans` không đụng `doc_id` của khoá học khác cùng tệp, không đụng sáu cuốn phát triển; khi xoá thật thì `MediaStore` giả ghi nhận lệnh xoá
  đúng các `public_id` mồ côi.
- [ ] `cleanup` xoá phiên hết hạn, token cũ, `rate_limit_event` cũ, bản ghi hỏng hết hạn; không xoá dữ liệu học.
- [ ] Ảnh chụp hai hộp xác nhận và lỗi `owns_shared_courses`.

## Ngoài vé

Chuyển chủ khoá. Xuất dữ liệu cá nhân.
