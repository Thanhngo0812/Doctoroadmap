# W-02 — Hoàn thiện phản hồi form ngày 2026-10-20

Theo yêu cầu chủ dự án: thông báo xuất hiện mượt; chuyển đăng nhập/đăng ký không giữ lỗi cũ; trường sai tô đỏ và có lỗi nhỏ bên dưới; khung lỗi không viền xanh dương.

## Thay đổi

- Tách state bằng key login/register tại route, xoá lỗi, giá trị mật khẩu và trạng thái hiện mật khẩu khi đổi form. Phản hồi lỗi của yêu cầu cũ về muộn không xuất hiện trên form mới.
- Link giữa hai form dùng native View Transitions, khoảng 200 ms, không thêm thư viện. Trình duyệt thiếu API hoặc bật giảm chuyển động vẫn chuyển trang bình thường. Focus chuyển tới tiêu đề form mới.
- Thông báo lỗi mở nhẹ bằng CSS; giữ focus/role alert để đọc được bằng screen reader, bỏ outline xanh trên khung lỗi. Ô nhập sai và focus dùng màu đỏ theo token danger.
- Kiểm required/email/độ dài/xác nhận ngay tại form, hiển thị lỗi nhỏ với aria-describedby; sửa ô nào xoá lỗi ô đó. Lỗi API hỗ trợ cả loc dạng body.password và mảng; thông báo mật khẩu phổ biến được hiển thị đúng thay vì nhầm sang độ dài.
- Lỗi đăng nhập vẫn dùng câu chung cho email/mật khẩu, không xác nhận trường nào đúng.
- Đăng nhập/đăng ký mới/đăng xuất thành công có thông báo xanh lá theo token success, tồn tại qua điều hướng rồi tự ẩn sau 5 giây. Trên mobile đặt phía dưới để không đè tiêu đề tài khoản.

## Kiểm thử

- Đã tái hiện 8 test lỗi trên mã cũ trước khi sửa: lỗi lưu qua hai form, lỗi trả về muộn, thiếu thông báo thành công, thiếu inline validation, sai thông báo password và thiếu chuyển cảnh native.
- Cuối cùng **38/38 React test đạt**, build production đạt. [XML](w02-auth-feedback/frontend-tests.xml).
- Chromium: **6 trường hợp đạt**, 390/1280 px, sáng/tối; chuyển hai chiều, thông báo mở có opacity trung gian thực, viền input đỏ và alert không outline; axe không vi phạm; success tự ẩn; reduced-motion không animation đang chạy; không lỗi ứng dụng. [JSON](w02-auth-feedback/browser-audit.json).
- Các ảnh ở w02-auth-feedback/. Phản hồi account API được mô phỏng rõ ràng trong phép kiểm UI, không tạo/sửa tài khoản local hay gọi mô hình. Script tái chạy: node scripts/w02_auth_feedback_check.cjs.
- Đã build và phục vụ bản cuối tại http://127.0.0.1:8000; health 200, db ok. Backend không đổi trong đợt này.

Nguồn cách triển khai: [React — reset state bằng key](https://react.dev/learn/preserving-and-resetting-state), [MDN — startViewTransition và fallback](https://developer.mozilla.org/en-US/docs/Web/API/Document/startViewTransition), [React — flushSync](https://react.dev/reference/react-dom/flushSync).
