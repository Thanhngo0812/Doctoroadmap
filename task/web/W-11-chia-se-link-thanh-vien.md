# W-11 — Chia sẻ bằng link, thành viên, rời khoá

**Nguồn chân lý:** [spec chức năng](../../doc/web-chuc-nang-spec.md), mục 3, 6; [ADR 0020](../../doc/adr/0020-khoa-hoc-la-don-vi-chia-se-du-lieu-hoc-theo-nguoi-va-cuon.md);
[spec cơ sở dữ liệu](../../doc/web-co-so-du-lieu-spec.md), bảng `share_link`, mục 6 (tham gia bằng link); spec thiết kế, hộp chia sẻ, trang tham gia, trang
thành viên.
**Ai:** nhóm web · người soát kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** W-06 · **Trạng thái:** ready-for-agent

## Vì sao

Chia sẻ khoá học cho cả lớp là chức năng chủ dự án yêu cầu. Nó cũng làm cache bài giảng có lợi thật: thêm người học không thêm tiền bài giảng.

## Cần làm

**`SharingService`:** `create_share_link`, `list_share_links`, `revoke_share_link`, `preview_share_link`, `join_by_link`, `list_members`, `remove_member`,
`leave_course`.
- **Link:**
  - token 32 byte, chỉ lưu băm; hiện đủ **một lần** lúc tạo;
  - danh sách link chỉ hiện 6 ký tự cuối;
  - hạn mặc định 7 ngày, hoặc "không hết hạn"; `max_uses` tuỳ chọn.
- **Chưa xác minh email** vẫn tạo link và tham gia được (bản demo, chủ dự án chốt 2026-10-18).
- `preview_share_link` mở cho khách; link hỏng vì bất kỳ lý do gì đều trả `link_invalid`.
- **`join_by_link`** chạy trong một giao dịch như spec cơ sở dữ liệu mục 6. Đã là thành viên thì không tăng `use_count`. Đủ 200 thành viên thì `course_full`.
- **`remove_member`:** người bị xoá mất quyền ngay ở lần gọi kế tiếp; dữ liệu học của họ giữ nguyên.
- **`leave_course`:** chủ khoá không rời được (phải xoá khoá ở W-20).
- Nhật ký: `share_link_created`, `share_link_revoked`, `member_joined`, `member_removed`, `member_left`.

**HTTP:** các điểm cuối của nhóm "chia sẻ" ở spec mục 11, trừ lời mời email (W-12) và tiến độ thành viên (W-18).

**Giao diện:**
- **hộp "Chia sẻ"** của chủ khoá: tạo link (hạn, số lượt), nút sao chép, danh sách link với nút thu hồi;
- **trang `/join/<token>`:**
  - khách thấy tên khoá, chủ khoá, số module, kèm nút đăng nhập hay đăng ký; xong thì quay lại đúng trang;
  - người đã đăng nhập thấy **thông báo dữ liệu** (chủ khoá thấy gì, không thấy gì) và nút "Tham gia";
- **trang thành viên:** chủ khoá thấy danh sách và nút xoá; thành viên thường thấy chủ khoá, số thành viên, nút "Rời khoá".

## Tiêu chí nghiệm thu

Mỗi test thấy đỏ trước trên bản sai:
- [ ] Link thu hồi, hết hạn (đồng hồ giả), hay hết lượt đều trả `link_invalid`, cùng thân phản hồi.
- [ ] `max_uses = 1`, hai tham gia đồng thời trên PostgreSQL: đúng một người vào.
- [ ] Tham gia lần hai không tăng `use_count`.
- [ ] Bị xoá thì lần gọi kế tiếp `not_found`; tham gia lại bằng link mới thì thấy lại tiến độ và phiên cũ.
- [ ] Thu hồi link không xoá thành viên đã vào.
- [ ] Bảng `share_link` không có token thô.
- [ ] Ảnh chụp: hộp chia sẻ, trang tham gia của khách và của người đã đăng nhập, link hỏng, trang thành viên của chủ khoá và của thành viên.

## Ngoài vé

Mời theo email (W-12). Tiến độ thành viên (W-18). Đồng chủ khoá.
