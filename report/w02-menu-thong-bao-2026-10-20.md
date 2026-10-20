# W-02 — Menu tài khoản và thông báo, 2026-10-20

Theo phản hồi giao diện của chủ dự án.

## Thay đổi

- Menu co theo nội dung, giới hạn theo màn hình; email một dòng, email quá dài dùng dấu ba chấm và title giữ nguyên địa chỉ. Tách thông tin tài khoản và nút đăng xuất bằng đường phân cách; vùng bấm tối thiểu 44 px. Dùng token và kiểu chữ WayFinder hiện có, hỗ trợ sáng/tối.
- Theo lời làm rõ của chủ dự án: chữ căn giữa trong khung; khung thông báo giữ bên phải và rộng vừa chữ cộng 16 px đệm mỗi bên và viền. Desktop ở góc trên phải cách 24 px, mobile ở góc dưới phải cách 16 px; vẫn tự ẩn sau 5 giây.
- Chỉ chuyển trang sau API đăng xuất thành công. Cập nhật phiên và điều hướng trong cùng View Transition, khoảng 200 ms. Nút có trạng thái đang xử lý, chặn bấm lặp; lỗi mạng giữ tài khoản và cho thử lại. Trình duyệt thiếu API hoặc bật giảm chuyển động dùng điều hướng thường.

## Bằng chứng

- Trước sửa: 2 test hồi quy thất bại trên mã cũ; trình duyệt tái hiện khung thông báo 304 px có khoảng thừa 144,47 px so với chữ.
- Sau sửa: **41/41 React test đạt**, build production đạt. [XML](w02-account-menu/frontend-tests.xml).
- [Bộ kiểm menu](../scripts/w02_account_menu_check.cjs): **9 trường hợp đạt**, 336/390/1280 px, sáng/tối, email dài 254 ký tự và reduced-motion. Chữ lệch tâm khung 0 px, khung cách mép phải đúng 24/16 px; phần rộng hơn chữ đúng 34 px (đệm hai bên và viền). Email bình thường cao đúng một dòng 22 px; nút đăng xuất 44 px; không tràn trang; axe không vi phạm trong 6 cấu hình menu; không lỗi ứng dụng. CSRF vẫn được gửi khi đăng xuất. [JSON và ảnh](w02-account-menu/browser-audit.json).
- Bộ hồi quy phản hồi form: **6 trường hợp đạt**, gồm chuyển hai chiều, xoá lỗi cũ, inline lỗi đỏ, thông báo tự ẩn và giảm chuyển động. [Script](../scripts/w02_auth_feedback_check.cjs).
- Account API trong phép kiểm trình duyệt được mô phỏng; không tạo tài khoản thật, gửi mail hay gọi mô hình. Thay đổi chỉ thuộc frontend W-02.
