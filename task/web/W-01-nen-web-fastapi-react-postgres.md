# W-01 — Nền web: FastAPI, React, PostgreSQL, Alembic, đường nối test

**Nguồn chân lý:** [spec chức năng](../../doc/web-chuc-nang-spec.md), mục 1, 11, 12, "Quyết định kiểm thử"; [spec cơ sở dữ liệu](../../doc/web-co-so-du-lieu-spec.md),
mục 1, 8; [spec thiết kế](../../doc/web-thiet-ke-giao-dien-spec.md), phần token.
**Ai:** nhóm web · người soát kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không · **Trạng thái:** ready-for-agent

## Vì sao

Mọi vé sau cần cùng một khung: ứng dụng FastAPI mỏng gọi dịch vụ, React cùng nguồn, PostgreSQL có di trú, và một bộ đồ giả để test không cần mạng. Làm
khung một lần để các vé sau chỉ thêm lát dọc của mình.

## Cần làm

**Phía máy chủ:**
- Ứng dụng FastAPI ở tầng presentation, dựng bằng một hàm tạo ứng dụng nhận cấu hình và các dịch vụ đã nối (composition). Route không tự tạo kho hay mô hình.
- `WebSettings` đọc từ biến môi trường, với mọi khoá ở spec chức năng mục 12. Các trần Pha B vẫn ở `BSettings`.
- `GET /api/v1/health` trả `{status, version, db: ok|down}`.
- **Khuôn lỗi** chung `{"error": {"code", "message", "retry_after", "ref"}}`, kèm bảng mã ở spec mục 11. Lỗi chưa bắt trả `internal_error` có `ref`;
  stack trace chỉ vào log.
- **Header an ninh** mặc định: CSP, `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin`.
- **OpenAPI:** lệnh xuất `openapi.json` vào repo; test hỏng nếu tệp đã commit lệch với ứng dụng.
- Lệnh CLI `web serve` (máy chủ API) và `web worker` (khung rỗng; W-14 làm việc thật).

**Cơ sở dữ liệu:**
- docker compose có hai dịch vụ PostgreSQL 16: `db` (dev) và `db-test` (test, dữ liệu tạm).
- Alembic với bản di trú gốc rỗng, cùng lệnh `web db upgrade`.
- Fixture test: tạo cơ sở dữ liệu sạch cho mỗi phiên test, chạy di trú lên mới nhất.
  - Thiếu biến môi trường của `db-test` thì test PostgreSQL bỏ qua, kèm dòng báo rõ.
  - Lệnh kiểm của vé (`web check`, hay một tuỳ chọn pytest) thì coi thiếu là **hỏng**.

**Đồ giả cho tầng dịch vụ** (dùng chung mọi vé sau):
- đồng hồ giả: dùng lại `ClockPort` của Pha B2;
- `Mailer` giả: giữ thư trong bộ nhớ để test đọc lại;
- `BuildRunner` giả: chỉ khung, W-14 làm đầy đủ;
- một "bộ ứng dụng thử" dựng mọi dịch vụ trên kho bộ nhớ, và Pha B trên mô hình giả theo kịch bản cộng embedding giả, như test Pha B hiện có.

**Phía giao diện:**
- Ứng dụng React (Vite, TypeScript) ở thư mục riêng ở gốc repo; có router, bố cục chung (thanh trên có logo, vùng nội dung), trang 404.
- **Cùng nguồn:** dev dùng proxy của Vite tới FastAPI; bản dựng do FastAPI phục vụ tệp tĩnh.
- **Lớp gọi API:**
  - luôn gửi cookie;
  - tự gắn `X-CSRF-Token` cho yêu cầu đổi dữ liệu;
  - đổi `error.code` thành câu tiếng Việt;
  - một hàm đọc SSE dùng chung cho W-08 và W-09.
- **Token thiết kế** theo spec thiết kế: font Be Vietnam Pro, màu, cỡ chữ, khoảng cách, bo góc, bóng; chế độ sáng và tối.
- Favicon WayFinder (`design/OTP*.png`) và logo theo bảng tệp của spec thiết kế.
- Trang chủ tạm gọi `/health` và hiện trạng thái.

**Test kiến trúc:** mở rộng test tầng hiện có: domain và application không import FastAPI, SQLAlchemy, Alembic, hay thư viện băm mật khẩu.

## Tiêu chí nghiệm thu

- [ ] `docker compose up db` cùng `web db upgrade` cùng `web serve` chạy được; trình duyệt mở trang chủ thấy "máy chủ: tốt, cơ sở dữ liệu: tốt".
- [ ] Dừng `db` thì `/health` trả `db: down`, và trang chủ hiện trạng thái lỗi theo spec thiết kế.
- [ ] Test khuôn lỗi: một route thử ném lỗi thì phản hồi là `internal_error` có `ref`, thân không có stack trace. Thấy đỏ trước khi có bộ bắt lỗi.
- [ ] Test OpenAPI lệch: sửa một route mà không xuất lại thì test hỏng.
- [ ] Test kiến trúc mới thấy đỏ khi thêm thử một dòng `import fastapi` vào application, rồi gỡ.
- [ ] Lệnh kiểm của vé hỏng khi tắt `db-test`; bỏ qua có báo khi chạy pytest thường.
- [ ] Ảnh chụp trang chủ ở 390 px và 1280 px, chế độ sáng và tối.

## Ngoài vé

Tài khoản (W-02). Bảng dữ liệu nào ngoài bảng phiên bản của Alembic.
