# W-02 — Đăng ký, đăng nhập, đăng xuất, phiên cookie, CSRF, giới hạn thử

**Nguồn chân lý:** [spec chức năng](../../doc/web-chuc-nang-spec.md), mục 2, 3, 10, 11; [ADR 0021](../../doc/adr/0021-phien-dang-nhap-phia-may-chu-trong-cookie.md);
[spec cơ sở dữ liệu](../../doc/web-co-so-du-lieu-spec.md), bảng `account`, `auth_session`, `rate_limit_event`, `audit_event`; spec thiết kế, trang
đăng ký và đăng nhập.
**Ai:** nhóm web · người soát kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** W-01 · **Trạng thái:** done-local

**Đợt tiếp theo 2026-10-19:** W-01 đã đạt nền local, web chốt commit nền rồi bắt đầu W-02. Không cần chờ toàn bộ Figma;
phối hợp thiết kế cung cấp trang tài khoản theo spec. Dự kiến migration W-02 `w02_0003` nối sau W-05 `w05_0002`,
để giữ một tuyến Alembic; domain/service/API/UI làm song song được, chỉ chốt migration sau mốc W-05 đã bàn giao.
Xem checkpoint và đầu ra tại [kế hoạch ba nhóm](../../report/dieu-phoi-soat-ba-nhom-2026-10-19.md).

## Vì sao

Mọi chức năng sau cần biết ai đang gọi. Đây cũng là chỗ dễ sai an ninh nhất, nên phải có test cho từng luật.

## Cần làm

**Domain:** thực thể `Account`, `Actor`, và hàm phân quyền `decide(actor, action, course, membership)` với các hàng của bảng luật mà vé này dùng (khách,
chưa xác minh, bị khoá). Các hàng về khoá học thêm ở W-06 và W-11.

**`AccountService`:** `register`, `login`, `logout`, `me`.
- Đăng ký theo spec mục 2: chuẩn hoá email; mật khẩu 8–128 ký tự; danh sách mật khẩu phổ biến đóng kèm; băm Argon2id.
- **Phản hồi đăng ký trùng:** trả cùng HTTP status và thân thông báo chung. Theo quyết định chủ dự án 2026-10-19, giữ tự đăng nhập cho đăng ký mới; khác biệt cookie và `/me` vẫn cho phép suy ra email đã tồn tại (đã chấp nhận). Vé này chưa gửi thư; W-03 thêm thư "bạn đã có tài khoản".
- Đăng nhập: lỗi chung `invalid_credentials`; giới hạn 5 lần sai mỗi email và 20 lần mỗi IP trong 15 phút, đếm bằng `rate_limit_event`.
- **Phiên phía máy chủ:**
  - token 32 byte trong cookie `d2r_session` (`HttpOnly`, `SameSite=Lax`, `Secure` khi HTTPS);
  - chỉ lưu băm của token;
  - hạn 7 ngày không dùng và 30 ngày tuyệt đối;
  - `csrf_token` riêng cho mỗi phiên.
- Tài khoản `disabled` bị từ chối, kể cả khi đang có phiên.
- Nhật ký `audit_event`: `login_ok`, `login_failed`, `logout`.
- Lệnh CLI `web create-admin --email …`, hỏi mật khẩu qua stdin, không nhận mật khẩu trên dòng lệnh.

**Tầng HTTP:** `POST /auth/register`, `POST /auth/login`, `POST /auth/logout`, `GET /me`.
- Phụ thuộc chung "lấy `Actor` từ cookie" dùng cho mọi route sau.
- **Kiểm CSRF** cho mọi phương thức không phải GET: `X-CSRF-Token` khớp phiên, và `Origin` thuộc `allowed_origins`. Đăng ký và đăng nhập (chưa có phiên)
  chỉ kiểm `Origin`.

**Di trú:** `account`, `auth_session`, `rate_limit_event`, `audit_event`.

**Giao diện:** trang đăng ký, đăng nhập; menu tài khoản ở thanh trên (tên hiển thị, đăng xuất); chuyển về trang đăng nhập khi gặp `unauthenticated`; trạng
thái lỗi và giới hạn thử theo spec thiết kế.

## Tiêu chí nghiệm thu

Mỗi test thấy đỏ trước trên bản sai:
- [x] Đăng ký `A@x.vn` rồi `a@x.vn` thì lần hai không tạo tài khoản mới, và phản hồi giống hệt lần một.
- [x] Cột `password_hash` bắt đầu bằng `$argon2id$`; quét cơ sở dữ liệu không thấy mật khẩu hay token phiên thô.
- [x] Sai mật khẩu với email có và email không có trả cùng mã và cùng thân phản hồi.
- [x] Lần sai thứ 6 trong 15 phút trả `rate_limited` kèm `retry_after`; qua 15 phút theo đồng hồ giả thì thử lại được.
- [x] Phiên quá 7 ngày không dùng, hay quá 30 ngày, thì `unauthenticated`.
- [x] Admin đặt `disabled` thì yêu cầu kế tiếp của phiên đang mở bị `account_disabled`.
- [x] Tầng HTTP: cookie có đủ cờ; một test **liệt kê mọi route không phải GET** và kỳ vọng `csrf_failed` khi thiếu token hay sai `Origin`.
- [x] Ví dụ JSON thật của bốn điểm cuối; ảnh chụp hai trang ở 390 px và 1280 px.

## Ngoài vé

Xác minh email, quên mật khẩu (W-03). Đổi mật khẩu, đăng xuất mọi nơi (W-04).

## Bàn giao local 2026-10-19

Nhánh `work/w02-accounts` đã tích hợp bàn giao W-05 `8b920d6`. Migration `w02_0003` nối `w05_0002`, một head, được kiểm từ database rỗng và đã áp dụng local. Toàn bộ 2.062 test đạt, 1 Cloudinary live bỏ qua theo cờ bật riêng; backend 150 đạt; React 29/29 và build đạt; 12 màn trình duyệt + 9 assertion luồng đạt. Chi phí mô hình 0 USD. Xem [báo cáo W-02](../../report/w02-tai-khoan-phien-2026-10-19.md). Chưa mở W-06/W-15/W-23.
