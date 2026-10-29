# Mở backend và frontend — W-17.1 React

Worktree `C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w17-admin-users-react`, nhánh `work/w17-admin-users-react`. Đăng nhập tài khoản admin, mở `/admin/nguoi-dung` hoặc `/admin/nhat-ky`; menu tài khoản có mục **Quản trị**. Người thường không có quyền vào khu này.

## Chuẩn bị DB

Backend W-17.1 dùng schema `w17_0009`. DB hiện hữu cần người vận hành sao lưu, đối chiếu UUID admin đầu tiên từ hồ sơ đáng tin cậy, áp dụng migration và CLI bảo vệ theo [bàn giao backend](../w17-bao-ve-admin-dau-tien-2026-10-28.md). Không chọn UUID từ hàng đầu bảng/ngày tạo, không nhập UUID bảo vệ trong web. Nhóm React chưa thực hiện bước operator này trên DB phát triển của chủ dự án.

Khi schema đã có nhưng định danh chưa được đối chiếu, màn hình hiển thị trạng thái chưa xác lập và phản ánh `bootstrap_required` khi server từ chối thao tác hạn chế quyền. Hồ sơ/mật khẩu thông thường vẫn dùng `/tai-khoan`.

## Terminal 1 — PostgreSQL và backend

Bật Docker Desktop. Sau khi DB đã được operator chuẩn bị:

```powershell
cd C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w17-admin-users-react
$wfPython = (Resolve-Path ../../.venv/Scripts/python.exe).Path
$wfEnv = (Resolve-Path ../../src/web/.env).Path
$env:PYTHONPATH = "$($PWD.Path)\src\web\backend;$($PWD.Path)\src"
$env:WAYFINDER_FRONTEND_DIST = "$($PWD.Path)\src\web\frontend\dist"
$env:WAYFINDER_ARTIFACT_ROOT = "$($PWD.Path)\artifacts"
$env:WAYFINDER_ALLOWED_ORIGINS = '["http://127.0.0.1:8000","http://127.0.0.1:5173"]'
$env:WAYFINDER_PUBLIC_BASE_URL = 'http://127.0.0.1:5173'
$env:WAYFINDER_MAILER = 'console'
docker compose -f src/web/docker-compose.yml --env-file $wfEnv up -d --wait db
& $wfPython -m wayfinder.cli --env-file $wfEnv serve --host 127.0.0.1 --port 8000
```

## Terminal 2 — frontend

```powershell
cd C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w17-admin-users-react
npm.cmd --prefix src/web/frontend ci
npm.cmd --prefix src/web/frontend run dev -- --port 5173 --strictPort
```

Mở **http://127.0.0.1:5173/admin/nguoi-dung**. Dừng từng terminal bằng Ctrl+C, giữ nguyên volume DB/worktree/snapshot.

Xem bản build cùng nguồn ở cổng 8000: chạy `npm.cmd --prefix src/web/frontend run build`, đổi `WAYFINDER_PUBLIC_BASE_URL` thành `http://127.0.0.1:8000`, rồi mở lại backend. Không dùng service từ worktree cũ để đối chiếu W-17.1.

## Kiểm tự động 0 USD

`scripts/w17_react_runtime.py` là harness kiểm, không phải service dữ liệu thật: dùng DB UUID riêng, tài khoản tổng hợp, FakeMailer/FakeClock và chặn provider. Nó khởi động/đóng server `127.0.0.1:8037` và gỡ đúng DB kiểm do chính lượt đó tạo; không seed/kiểm phá trên DB phát triển.

Kết quả và ảnh xem ở [báo cáo W-17.1 React](../w17-react-tich-hop-2026-10-29.md). Browser thật kiểm thao tác, quyền và SQL độc lập; ảnh snapshot cho taste inspector chỉ dùng soát thị giác, không thay bằng chứng HTTP/PostgreSQL.
