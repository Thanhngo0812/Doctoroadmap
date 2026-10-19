# W-02 — Tài khoản và phiên cookie

Trạng thái: đang triển khai; chưa chốt nghiệm thu hoặc migration.

## Quyết định chủ dự án ngày 2026-10-19

- Đăng ký mới tự đăng nhập theo W-02; đăng ký trùng email sau chuẩn hoá trả cùng HTTP 200 và thân thông báo chung, không sửa tài khoản cũ và không cấp phiên mới.
- Chủ dự án đã chọn giữ cách này sau khi được giải thích: cookie và kết quả /me khác nhau vẫn cho phép suy ra email đã tồn tại. Vì thế chỉ cam kết phản hồi JSON/status giống nhau, không tuyên bố chống dò email hoàn toàn. W-03 sẽ bổ sung thư theo spec.
- Tài khoản disabled: yêu cầu hợp lệ đầu tiên phát hiện trạng thái khoá trả account_disabled và thu hồi mọi phiên; các cookie đã thu hồi trả unauthenticated sau đó. Mở khoá không phục hồi phiên cũ.
- CLI tạo quản trị viên là đường bootstrap tin cậy, đánh dấu email quản trị viên đã xác minh; HTTP đăng ký không nhận role/status/email_verified.
- W-02 không gửi thư, không gọi mô hình, không dựng PDF; không mở W-06/W-15/W-23.
- Migration dự kiến w02_0003 nối w05_0002; chỉ hoàn tất sau bàn giao W-05, không tạo migration W-05 giả.

## Tiến độ kiểm thử

- Argon2id và danh sách mật khẩu đóng kèm: 3 test đạt; đã thấy đỏ khi module chưa tồn tại.
- HTTP auth cùng hồi quy API: 37 test đạt ở mốc ghép đầu. Sẽ ghi số cuối sau khi hoàn tất.
- Hợp đồng OpenAPI được xuất từ ứng dụng thật. Kiểm thử nghiệp vụ, adapter PostgreSQL, CLI và trình duyệt đang tiếp tục.

## Nguồn bảo mật và dữ liệu

- Tham số Argon2id: 19 MiB, 2 vòng, parallelism 1 theo [OWASP Password Storage](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html).
- Danh sách mật khẩu phổ biến từ [SecLists](https://github.com/danielmiessler/SecLists), commit và SHA-256 đóng trong wayfinder/data/README.md; giấy phép MIT đi kèm, không cần mạng lúc chạy.
