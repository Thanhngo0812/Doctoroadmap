# Đăng nhập bằng phiên phía máy chủ trong cookie, không dùng JWT

**Status:** proposed — 2026-10-18 (chờ chủ dự án duyệt cùng [spec web](../web-chuc-nang-spec.md))

**Đăng nhập tạo một phiên phía máy chủ.**
- Token ngẫu nhiên 32 byte nằm trong cookie `d2r_session`: `HttpOnly`, `Secure` khi chạy HTTPS, `SameSite=Lax`.
- Cơ sở dữ liệu chỉ lưu băm SHA-256 của token, cùng hạn dùng (7 ngày không dùng, 30 ngày tuyệt đối).
- Mỗi phiên có một `csrf_token`. Mọi yêu cầu đổi dữ liệu phải gửi lại token đó trong header, và `Origin` phải đúng nguồn.
- Mật khẩu băm bằng Argon2id.

**Căn cứ:**
- **Thu hồi được ngay.** Đổi mật khẩu, đăng xuất mọi nơi, admin khoá tài khoản, và xoá thành viên đều cần có hiệu lực ở lần gọi kế tiếp. Với phiên phía máy
  chủ, chỉ cần xoá hàng.
- **Trình duyệt không đọc được token** (`HttpOnly`), nên lỗi XSS ở giao diện không lấy được phiên.
- **Gọn cho nhóm 4 người:** React cùng nguồn với API, không cần làm mới token, không cần khoá ký và xoay khoá.
- Truy vấn phiên mỗi yêu cầu là một tra khoá chính, rẻ so với lời gọi mô hình.

**Considered Options**

- *JWT truy cập ngắn hạn cộng token làm mới.* Hợp khi nhiều dịch vụ độc lập kiểm token, hay khi có ứng dụng di động. Bị bác: phải dựng danh sách thu hồi
  để đạt cùng hành vi, thêm khoá ký, và token trong bộ nhớ trình duyệt dễ lộ hơn.
- *JWT trong cookie, không lưu phía máy chủ.* Không thu hồi được trước khi hết hạn.
- *Đăng nhập bằng Google.* Để sau. Phiên phía máy chủ không cản: đăng nhập Google xong cũng tạo cùng loại phiên.

**Consequences**

- Có bảng phiên đăng nhập và token email (xác minh, đặt lại mật khẩu), chỉ lưu băm.
- Có kiểm CSRF ở tầng HTTP. Một test liệt kê mọi route đổi dữ liệu và kỳ vọng `csrf_failed` khi thiếu token.
- Giao diện React phải phục vụ cùng nguồn với API. Khác nguồn thì phải đổi `SameSite` và CORS, cần ADR mới.
