# W-04 — Hồ sơ, đổi mật khẩu, đăng xuất mọi nơi

**Phân công sau nghiệm thu lần 7, 2026-10-26:** giao nhân viên lõi mốc backend W-04 ở worktree riêng; React/tích hợp vẫn do web làm sau W-10/W-16. Dùng lại AccountService/session/CSRF/audit W-02/W-03: hồ sơ tên 1–60, đổi mật khẩu từ A giữ A/hủy B, logout-all hủy cả A+B; định danh phiên hiện tại từ server, không tin payload. Không tạo migration rỗng hoặc viết frontend tạm. Chỉ 0 USD, [biên bản lần 7](../../report/dieu-phoi-nghiem-thu-ba-nhom-lan7-2026-10-26.md) và [phạm vi/lời giao](../../report/lenh-giao-viec-ba-nhom-lan7-2026-10-26.md). Backend đạt không đóng toàn vé có giao diện.

**Nguồn chân lý:** [spec chức năng](../../doc/web-chuc-nang-spec.md), mục 2 (đổi mật khẩu, đăng xuất mọi nơi), user story 11–13; spec thiết kế, trang hồ sơ.
**Ai:** lõi làm mốc backend; web làm React/tích hợp · người soát kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** W-02 · **Trạng thái:** ready-for-agent

**2026-10-20, sau W-03:** W-02/W-03 đã nghiệm thu, W-04 đủ điều kiện nhận. Web ưu tiên React/tích hợp W-06;
xếp W-04 sau nếu chỉ có một phiên web, chỉ làm song song khi có người riêng và phân vùng AccountService.
Không tạo migration rỗng nếu không đổi schema. Xem [kế hoạch tiếp](../../report/dieu-phoi-nghiem-thu-w03-va-ke-hoach-2026-10-20.md).

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
