# WayFinder — nền web W-01

Chạy các lệnh dưới đây từ gốc repo với Python 3.12, Node.js 24.11.1 / npm 11.6.2 (phiên bản đã kiểm) và Docker Desktop (Linux engine/WSL2).

## Phạm vi đã chốt

W-01 cung cấp nền FastAPI/React/PostgreSQL, MediaStore, CLI và bộ ứng dụng thử. Trang giới thiệu có hành trình tương tác dùng dữ liệu mẫu, ghi rõ là minh hoạ. Upload PDF mới và xử lý nền thật được nối theo các vé sau. Worker W-01 chưa nhận việc; W-14 triển khai hàng đợi.

## Chuẩn bị môi trường

```powershell
.venv/Scripts/python.exe -m pip install -e '.[web,dev]'
```

Nếu `.venv` chưa có pip: chạy `.venv/Scripts/python.exe -m ensurepip --upgrade` trước.

Tạo `src/web/.env` từ `.env.example` nếu chưa có tệp; điền mật khẩu PostgreSQL riêng cho dev và test, rồi sửa hai URL tương ứng. Giữ tệp này trên máy. Các trần có giá trị `null` được hiểu là không giới hạn. `artifact_root` cho dữ liệu dùng thật phải trỏ ra ngoài repo.

API dùng cấu hình lõi: `DOC2ROADMAP_LLM_TRANSPORT=vertex`, `DOC2ROADMAP_VERTEX_PROJECT`, `DOC2ROADMAP_VERTEX_LOCATION=global` và ADC hợp lệ trên máy chủ. Không cần Gemini API key. `web serve` kiểm cấu hình/xác thực trước khi dựng các adapter mô hình, không tự đổi transport; khởi động không sinh nội dung hay gọi mô hình tính phí.

```powershell
docker compose -f src/web/docker-compose.yml --env-file src/web/.env up -d --wait db db-test
.venv/Scripts/web.exe --env-file src/web/.env db upgrade
```

Dev dùng volume Docker có tên, test dùng `tmpfs`; không gắn dữ liệu PostgreSQL vào ổ C. Hai cổng chỉ lắng nghe loopback: 5432/5433. Bản di trú W-01 chỉ tạo bảng phiên bản Alembic.

## Chạy ứng dụng

```powershell
.venv/Scripts/web.exe --env-file src/web/.env serve
```

Mở `http://127.0.0.1:8000`. Để FastAPI phục vụ React, dựng giao diện trước:

```powershell
npm.cmd --prefix src/web/frontend ci
npm.cmd --prefix src/web/frontend run build
```

Khi phát triển giao diện, chạy `npm.cmd --prefix src/web/frontend run dev` trong một cửa sổ lệnh khác rồi mở địa chỉ Vite in ra. Proxy `/api` chuyển về FastAPI cổng 8000; phía trình duyệt luôn gọi cùng nguồn. Bí mật không nằm trong `VITE_*`.

```powershell
.venv/Scripts/web.exe worker
.venv/Scripts/web.exe openapi export
```

OpenAPI ở `src/web/openapi.json`; thay route phải xuất lại. Worker hiện in thông báo phạm vi W-14 rồi thoát, không giả nhận hay hoàn tất việc.

## Kiểm thử

```powershell
.venv/Scripts/web.exe --env-file src/web/.env check
npm.cmd --prefix src/web/frontend test
npm.cmd --prefix src/web/frontend run build
```

`web check` chạy cả test lõi và test web, cách ly cấu hình mô hình `DOC2ROADMAP_*` của máy chủ khỏi tiến trình pytest để mỗi test dùng cấu hình giả riêng. Lệnh yêu cầu PostgreSQL test đang chạy. Thiếu cấu hình hoặc tắt `db-test` thì lệnh hỏng. Pytest thường không có `WAYFINDER_TEST_DATABASE_URL` sẽ báo rõ lý do bỏ qua test PostgreSQL. Mỗi phiên test PostgreSQL tạo một database UUID riêng, chạy toàn bộ di trú rồi chỉ xoá database do phiên đó tạo.

Nếu thư mục Temp/cache cũ của Windows bị lỗi quyền, đặt tham số pytest cho phiên shell:

```powershell
$env:PYTEST_ADDOPTS='--basetemp=.tmp/w01-pytest -o cache_dir=.tmp/w01-pytest-cache'
.venv/Scripts/web.exe --env-file src/web/.env check
Remove-Item Env:PYTEST_ADDOPTS
```

Các bài kiểm thử mô hình dùng đồ giả, không gọi mạng hay phát sinh USD. Cloudinary thật được bật riêng:

```powershell
$env:WAYFINDER_RUN_CLOUDINARY_TESTS='1'
.venv/Scripts/web.exe --env-file src/web/.env check
.venv/Scripts/web.exe --env-file src/web/.env media-smoke
Remove-Item Env:WAYFINDER_RUN_CLOUDINARY_TESTS
```

Đặt `CLOUDINARY_URL` trong dotenv phía máy chủ và bật **Allow delivery of PDF and ZIP files** trong Cloudinary Settings → Security. Smoke tạo PDF nhỏ, tải lên chế độ authenticated, kiểm ảnh trang/link tải và dọn tài sản thử. Không in URL ký hay thông tin xác thực. Tài khoản Free của chủ dự án đã qua smoke/contract; giới hạn do chủ dự án cung cấp là image 10 MB và raw 10 MB. Giới hạn upload mặc định là 10 MB. Kết quả và thời điểm kiểm ở báo cáo W-01.

## Gmail

Điền `WAYFINDER_SMTP_USERNAME`, `WAYFINDER_SMTP_PASSWORD` (Gmail App Password), `WAYFINDER_SMTP_FROM` trong dotenv phía máy chủ; dùng TLS qua `smtp.gmail.com:587` với `WAYFINDER_SMTP_STARTTLS=true`. Kết nối TLS và xác thực trên máy đã được kiểm thành công, không gửi thư. W-01 cung cấp Mailer giả cho test; nối gửi thư tài khoản thật thuộc W-02.

## Bằng chứng trình duyệt

Script nghiệm thu dùng bộ công cụ tạm, không thêm vào gói ứng dụng:

```powershell
npm.cmd install --prefix .tmp/w01-browser-tools --no-save --package-lock=false playwright@1.64.1 @axe-core/playwright
$env:PLAYWRIGHT_BROWSERS_PATH="$PWD/.tmp/w01-browsers"
.tmp/w01-browser-tools/node_modules/.bin/playwright.cmd install chromium
node scripts/w01_browser_check.cjs
```

Cần FastAPI chạy với frontend đã dựng và `db` đang tốt. Script chụp 390/768/1280 px ở sáng/tối, kiểm hành trình minh hoạ trên desktop và cả sáu chặng mobile tối, vùng bấm 44 px, axe WCAG AA, deep link, theme và giảm chuyển động. Nó cố ý gỡ CSS giảm chuyển động và thay màu nút sáng trong trang test riêng để xác nhận các guard bắt được lỗi. Cảnh báo CSP do axe chèn style/fetch stylesheet được ghi riêng trong `toolDiagnostics`; console của ứng dụng được kiểm trước và ngoài quá trình axe, giữ nguyên CSP. Ảnh, video và JSON nằm ở `report/w01-evidence/`.

Để kiểm nhánh mất kết nối, dừng riêng `db`, chạy `node scripts/w01_database_failure_check.cjs`, rồi luôn bật lại `db` bằng Compose. Script kiểm HTTP 503 và quan sát yêu cầu health mới sau khi bấm Thử lại.

Nguồn triển khai: [Hatch editable paths](https://hatch.pypa.io/latest/config/build/#dev-mode), [Alembic programmatic config](https://alembic.sqlalchemy.org/en/latest/api/config.html), [SQLAlchemy engine](https://docs.sqlalchemy.org/en/20/core/engines.html), [PostgreSQL 16.15](https://www.postgresql.org/docs/16/release-16-15.html), [Cloudinary access control](https://cloudinary.com/documentation/control_access_to_media), [Playwright video](https://playwright.dev/docs/videos).
