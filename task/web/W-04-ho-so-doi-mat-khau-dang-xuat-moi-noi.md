# W-04 — Hồ sơ, đổi mật khẩu, đăng xuất mọi nơi

**Nguồn chân lý:** [spec chức năng](../../doc/web-chuc-nang-spec.md), mục 2 (đổi mật khẩu, đăng xuất mọi nơi), user story 11–13; spec thiết kế, trang hồ sơ.
**Ai:** nhóm web · người soát kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** W-02 · **Trạng thái:** ready-for-agent

**2026-10-20:** W-02 đã nghiệm thu, W-04 đủ điều kiện nhận. Web ưu tiên W-03 và React W-06; chỉ chia W-04 khi có người và đã phân vùng sửa
`AccountService` với W-03. Không tạo migration rỗng nếu không đổi schema. Xem [kế hoạch tiếp](../../report/dieu-phoi-nghiem-thu-w02-w05-w24-2026-10-20.md).

## Vì sao

Người dùng cần tự quản lý tài khoản, và chặn được người dùng trộm khi lỡ đăng nhập ở máy lạ.

## Cần làm

**`AccountService`:** `update_profile`, `change_password`, `logout_all`.
- `update_profile`: tên hiển thị 1–60 ký tự, cắt khoảng trắng hai đầu.
- `change_password`: cần mật khẩu hiện tại. Mật khẩu mới theo luật của W-02. Thành công thì huỷ mọi phiên **khác**, giữ phiên đang dùng.
- `logout_all`: huỷ mọi phiên, kể cả phiên hiện tại.
- Nhật ký `password_changed`, `logout_all`.

**HTTP:** `PATCH /me`, `POST /me/password`, `POST /auth/logout-all`.

**Giao diện:** trang hồ sơ gồm ba khối: thông tin (tên, email, trạng thái xác minh), đổi mật khẩu, phiên đăng nhập (nút "Đăng xuất khỏi mọi thiết bị" có
hộp xác nhận). Khối "Xoá tài khoản" để chỗ trống cho W-20.

## Tiêu chí nghiệm thu

Mỗi test thấy đỏ trước trên bản sai:
- [ ] Đổi mật khẩu với mật khẩu hiện tại sai thì `invalid_credentials` và không đổi gì.
- [ ] Hai phiên A, B; đổi mật khẩu từ A thì B bị `unauthenticated`, A vẫn dùng được.
- [ ] `logout_all` thì cả A và B bị `unauthenticated`.
- [ ] Tên hiển thị 61 ký tự bị `validation`, kèm `fields`.
- [ ] Ảnh chụp trang hồ sơ ở 390 px và 1280 px.

## Ngoài vé

Xoá tài khoản (W-20). Danh sách thiết bị đang đăng nhập.
