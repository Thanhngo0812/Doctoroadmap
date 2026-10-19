# W-01 — Nền web: FastAPI, React, PostgreSQL, Alembic, đường nối test

**Nguồn chân lý:** [spec chức năng](../../doc/web-chuc-nang-spec.md), mục 1, 11, 12, "Quyết định kiểm thử"; [spec cơ sở dữ liệu](../../doc/web-co-so-du-lieu-spec.md),
mục 1, 8; [spec thiết kế](../../doc/web-thiet-ke-giao-dien-spec.md), phần token và mục 3a (chất lượng thị giác, hiệu ứng, `taste-skill`).
**Ai:** nhóm web · người soát kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không · **Trạng thái:** done-local (nghiệm thu 2026-10-19)

**Điều phối kiểm lại sau bàn giao ba nhóm, 2026-10-19:** nền local đạt kiểm trọng tâm, React 23 test/build đạt, trình duyệt 6 tổ hợp sáng/tối ×
390/768/1280 đạt. `src/web/` và báo cáo vẫn chưa được Git theo dõi ở nhánh đã kiểm; chốt commit đúng phạm vi trước checkpoint mở W-02/W-05.
Xem [kết quả và kế hoạch tiếp](../../report/dieu-phoi-soat-ba-nhom-2026-10-19.md). Không đồng nhất nền local với nghiệm thu Figma hay dựng sách thật.

## Vì sao

Mọi vé sau cần cùng một khung: ứng dụng FastAPI mỏng gọi dịch vụ, React cùng nguồn, PostgreSQL có di trú, và một bộ đồ giả để test không cần mạng. Làm
khung một lần để các vé sau chỉ thêm lát dọc của mình.

## Cần làm

**Cấu trúc thư mục** (chủ dự án chốt 2026-10-18; spec chức năng mục 1):
- `src/web/backend/wayfinder/` gồm `domain/`, `application/`, `infrastructure/`, `api/`, `worker`, `migrations/`; `src/web/backend/tests/`;
- `src/web/frontend/` (React); `src/web/docker-compose.yml`; `src/web/.env.example` (chỉ tên biến, không có giá trị thật).
- `pyproject.toml`: thêm gói `wayfinder` vào bản dựng; nhóm tuỳ chọn `web` cho FastAPI, Uvicorn, SQLAlchemy, psycopg, Alembic, argon2-cffi, cloudinary,
  python-multipart; `testpaths` thêm `src/web/backend/tests`. Cài: `pip install -e .[web,dev]` trong `.venv` hiện có.
- `.gitignore` thêm `node_modules/`, `dist/`, `.env`. Tệp này đang có người sửa dở chưa commit: hỏi người đó trước, không commit lẫn thay đổi của họ.

**Phía máy chủ:**
- Ứng dụng FastAPI ở `wayfinder/api`, dựng bằng một hàm tạo ứng dụng nhận cấu hình và các dịch vụ đã nối (composition). Route không tự tạo kho hay mô hình.
- `WebSettings` đọc từ biến môi trường, với mọi khoá ở spec chức năng mục 12. Các trần Pha B vẫn ở `BSettings`.
- **Gemini tạm qua Vertex AI** (chủ dự án cập nhật 2026-10-19): composition API/worker dùng `Settings` lõi với
  `DOC2ROADMAP_LLM_TRANSPORT=vertex`, `DOC2ROADMAP_VERTEX_PROJECT`, `DOC2ROADMAP_VERTEX_LOCATION` và ADC phía máy chủ; không bắt buộc Gemini API key.
  `.env.example` chỉ ghi tên biến/giá trị mẫu; React không nhận bí mật. Chỉ chuyển sang Developer API khi chủ dự án yêu cầu chuẩn bị demo.
  Áp dụng spec chức năng mục 1 và bất biến 27 bằng test đồ giả, 0 USD.
- `GET /api/v1/health` trả `{status, version, db: ok|down}`.
- **Khuôn lỗi** chung `{"error": {"code", "message", "retry_after", "ref"}}`, kèm bảng mã ở spec mục 11. Lỗi chưa bắt trả `internal_error` có `ref`;
  stack trace chỉ vào log.
- **Header an ninh** mặc định: CSP, `X-Content-Type-Options: nosniff`, `Referrer-Policy: same-origin`.
- **OpenAPI:** lệnh xuất `openapi.json` vào repo; test hỏng nếu tệp đã commit lệch với ứng dụng.
- Lệnh CLI `web serve` (máy chủ API) và `web worker` (khung rỗng; W-14 làm việc thật).

**Cơ sở dữ liệu:**
- `src/web/docker-compose.yml` có hai dịch vụ, ảnh `postgres:16` ghim phiên bản nhỏ, có healthcheck:
  - `db` (dev): volume có tên, cổng 5432;
  - `db-test` (test): dữ liệu trong `tmpfs`, cổng 5433.
  - Mật khẩu đọc từ `.env`. Trên Windows dùng Docker Desktop nền WSL2; không gắn thư mục dữ liệu trên ổ C.
- Lúc dev chỉ cơ sở dữ liệu chạy trong Docker; API, worker và Vite chạy thẳng trên máy.
- Alembic với bản di trú gốc rỗng, cùng lệnh `web db upgrade`.
- Fixture test: tạo cơ sở dữ liệu sạch cho mỗi phiên test, chạy di trú lên mới nhất.
  - Thiếu biến môi trường của `db-test` thì test PostgreSQL bỏ qua, kèm dòng báo rõ.
  - Lệnh kiểm của vé (`web check`, hay một tuỳ chọn pytest) thì coi thiếu là **hỏng**.

**Port `MediaStore`** (ADR 0023): `upload(path, folder, resource_type) → public_id`, `download(public_id) → đường dẫn tạm`, `fetch_page_image(public_id, page,
width) → bytes`, `fetch_image(public_id) → bytes`, `temporary_download_url(public_id, expires_at)`, `delete(public_id)`.
- Bản Cloudinary dùng SDK chính thức, đọc `CLOUDINARY_URL`; mọi tài sản `authenticated`.
- Lệnh `web media-smoke` (chạy tay, cần `CLOUDINARY_URL`): tải một PDF nhỏ tự tạo, lấy ảnh trang 1, xin link tải có hạn, xoá. In kết quả từng bước, không
  in khoá. Ghi vào báo cáo vé kết quả trên tài khoản của chủ dự án, kèm cỡ tệp tối đa và cài đặt giao PDF của gói.

**Đồ giả cho tầng dịch vụ** (dùng chung mọi vé sau):
- đồng hồ giả: dùng lại `ClockPort` của Pha B2;
- `Mailer` giả: giữ thư trong bộ nhớ để test đọc lại;
- `BuildRunner` giả: chỉ khung, W-14 làm đầy đủ;
- `MediaStore` giả: giữ tệp trong bộ nhớ, đếm số lần lấy, trả ảnh trang giả;
- một "bộ ứng dụng thử" dựng mọi dịch vụ trên kho bộ nhớ, và Pha B trên mô hình giả theo kịch bản cộng embedding giả, như test Pha B hiện có.

**Phía giao diện:**
- **Đầu vào W-22 (tiếp nhận 2026-10-19):** token/preview dùng làm đầu vào tạm theo spec, chưa là Figma đã nghiệm thu;
  người thiết kế đang cần xử lý [W-24](W-24-bo-sung-va-sua-ban-giao-w22.md). W-01 tiếp tục phần nền, kiểm cặp màu nút tối, vùng bấm mobile và GIF tĩnh
  khi giảm chuyển động trước khi tích hợp. Test đồng bộ phải so CSS thực với JSON Variables xuất từ Figma có nguồn gốc; không chỉ so mã màu viết sẵn.
- Ứng dụng React (Vite, TypeScript) ở `src/web/frontend/`; có router, bố cục chung (thanh trên có logo, vùng nội dung), trang 404.
- **Cùng nguồn:** dev dùng proxy của Vite tới FastAPI; bản dựng do FastAPI phục vụ tệp tĩnh.
- **Lớp gọi API:**
  - luôn gửi cookie;
  - tự gắn `X-CSRF-Token` cho yêu cầu đổi dữ liệu;
  - đổi `error.code` thành câu tiếng Việt;
  - một hàm đọc SSE dùng chung cho W-08 và W-09.
- **Token thiết kế** theo spec thiết kế: font Be Vietnam Pro, màu, cỡ chữ, khoảng cách, bo góc, bóng; chế độ sáng và tối.
- **Chất lượng và hiệu ứng:** khung chung/trang chủ phải có bố cục hoàn thiện, căn chỉnh và trạng thái tương tác nhất quán theo spec mục 3a. Thiết lập
  token chuyển động và xử lý `prefers-reduced-motion` dùng chung; dùng CSS cho các hiệu ứng đơn giản. Được phép dùng các skill trong bộ `taste-skill` do
  chủ dự án nạp, theo luật chung của kế hoạch web.
- Favicon WayFinder (`design/OTP*.png`) và 20 logo `design/Artboard 9.png` đến `design/Artboard 28.png`, theo bảng spec thiết kế mục 1. Thanh trên dùng
  `Artboard 24.png` (sáng) và `Artboard 28.png` (tối), đều nền trong; logo đã có, không chờ bộ `logo1`–`logo8` giả định trước đây.
- Trang chủ tạm gọi `/health` và hiện trạng thái.

**Test kiến trúc:**
- domain và application của `wayfinder` không import FastAPI, SQLAlchemy, Alembic, SDK Cloudinary, hay thư viện băm mật khẩu;
- `doc2roadmap` không import `wayfinder`;
- lõi vẫn qua test tầng hiện có.

## Tiêu chí nghiệm thu

- [x] `docker compose up db` cùng `web db upgrade` cùng `web serve` chạy được; trình duyệt mở trang chủ thấy "máy chủ: tốt, cơ sở dữ liệu: tốt".
- [x] Dừng `db` thì `/health` trả `db: down`, và trang chủ hiện trạng thái lỗi theo spec thiết kế.
- [x] Test khuôn lỗi: một route thử ném lỗi thì phản hồi là `internal_error` có `ref`, thân không có stack trace. Thấy đỏ trước khi có bộ bắt lỗi.
- [x] Test OpenAPI lệch: sửa một route mà không xuất lại thì test hỏng.
- [x] Test cấu hình Gemini tạm thời: `vertex` được truyền tới bản giả, không yêu cầu Gemini API key; thiếu project/xác thực Vertex bị chặn trước lời gọi,
  không tự chuyển sang Developer API. Thấy đỏ khi bỏ kiểm cấu hình; không gọi mạng, dùng bản giả xác thực.
- [x] Test kiến trúc mới thấy đỏ khi thêm thử một dòng `import fastapi` vào `wayfinder/application`, và khi thêm `import wayfinder` vào `doc2roadmap`; rồi
  gỡ.
- [x] Cài từ đầu bằng `pip install -e .[web,dev]` trong một venv mới, rồi chạy được toàn bộ test lõi lẫn test web.
- [x] Lệnh kiểm của vé hỏng khi tắt `db-test`; bỏ qua có báo khi chạy pytest thường.
- [x] `MediaStore` giả và bản Cloudinary qua cùng một bộ test hợp đồng; bản Cloudinary chỉ chạy khi có `CLOUDINARY_URL`. `web media-smoke` chạy xanh
  trên tài khoản của chủ dự án; chủ dự án hay người được giao chạy, vì cần khoá.
- [x] Ảnh chụp trang chủ ở 390 px và 1280 px, chế độ sáng và tối.
- [x] Người thiết kế/người soát xác nhận khung chung và trang chủ đạt chất lượng thị giác theo spec mục 3a; kiểm bố cục thêm ở 768 px, kèm video ngắn
  các tương tác có hiệu ứng. Test giảm chuyển động thấy đỏ khi bỏ xử lý, xanh khi vòng chờ tĩnh/chuyển động không thiết yếu bị tắt và thao tác vẫn dùng được.

Bằng chứng và giới hạn bàn giao: [báo cáo nghiệm thu W-01](../../report/w01-nen-web-2026-10-19.md). Chủ dự án giao điều phối viên trực tiếp soát/kiểm thử; token W-22 vẫn là đầu vào tạm, không thay nghiệm thu Figma W-24/W-23.

## Ngoài vé

Tài khoản (W-02). Bảng dữ liệu nào ngoài bảng phiên bản của Alembic.
