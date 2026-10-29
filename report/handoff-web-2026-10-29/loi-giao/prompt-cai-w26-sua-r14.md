# Lời giao: W-26 sửa sau nghiệm thu lần 14 (chỉ test, không đổi hành vi)

Bạn là subagent lõi web. Đọc trước `tmp/claude-tools/so-tay-agent-web.md` (luật, môi trường, cách lưu tiến độ, cách kết thúc).

- Worktree: `C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w26-demo-local`, nhánh `work/w26-demo-local` (đỉnh `d3c2ec15`). Làm mọi thứ trong worktree này.
- Không sửa `src/web/backend/wayfinder/**`. Chỉ sửa `src/web/backend/tests/test_demo_local_w26.py`, `src/web/backend/tests/w26_mutations.py`
  và báo cáo `report/w26-demo-local-2026-10-29.md` (UTF-8, ghi bằng công cụ Write/Edit, không ghi qua PowerShell).
- Chi nhà cung cấp 0 USD. Commit local, không push. Commit chỉ đường dẫn của mình (`git commit -- <tệp>`).

## Bối cảnh

`src/web/.env` thật đặt `WAYFINDER_PUBLIC_BASE_URL='http://127.0.0.1:5173'` (chế độ Vite). Máy chủ demo phục vụ giao diện ở cổng 8000, nên
`demo_settings` ghi đè `public_base_url=origin`. Bộ phá của điều phối xoá đúng phần ghi đè đó (`public_base_url=origin, ` trong `demo_settings`)
và 32 test vẫn xanh: hàm `config()` trong test không đặt `public_base_url`, nên giá trị mặc định 8000 của `WebSettings` che mất lỗi; test mail
cũng chỉ so với `cfg.public_base_url` chứ không so với chuỗi cụ thể.

## Required

**WEB-R14-01 — liên kết trong thư phải trỏ cổng demo, không trỏ 5173.**
- Cho cấu hình gốc trong test giống `.env` thật: `public_base_url='http://127.0.0.1:5173'`.
- Test mail đăng ký phải kiểm liên kết trong thân thư bắt đầu bằng đúng `http://127.0.0.1:8000/` và không chứa `5173`.
- Thêm một ca `--port` khác (ví dụ 8010): `demo_settings(..., port=8010).public_base_url == 'http://127.0.0.1:8010'`.
- Thêm phép `base-url` vào `w26_mutations.py` (xoá `public_base_url=origin, `), chạy bộ phá, phép này phải bị bắt.
- Xác nhận test mới đỏ khi xoá phần ghi đè (chạy tay một lần rồi khôi phục bytes, kiểm SHA) — ghi kết quả vào báo cáo.

## Optional (làm nếu nhỏ)

- **WEB-R14-02:** test `allowed_origins` của demo chứa cả `http://127.0.0.1:8000` và `http://localhost:8000`; thêm phép `no-localhost-origin`.
- **WEB-R14-03:** ca biên `spent_today` đúng bằng 10 USD → `DemoSpendPolicy.activate` ném `BuildSpendStopped` (phép `if limit <= 0` → `< 0` hiện sống sót).

## Kiểm và kết thúc

1. `..\..\.venv\Scripts\python.exe scripts\w05_run_tests.py src/web/backend/tests/test_demo_local_w26.py -o addopts= -q --basetemp=tmp/w26-r14-<số>`
   phải xanh. Không chạy toàn bộ `src/web/backend/tests` (điều phối tự chạy).
2. Chạy `w26_mutations.py` cho các phép mới; JSON vào `report/w26-evidence/mutations/run4/`.
3. Cập nhật báo cáo: mục "Sửa sau nghiệm thu lần 14", từng mã WEB-R14 làm gì, test nào bắt phép nào.
4. Commit, `git status` sạch, báo lại: commit đỉnh, số test, bảng phép mới. Không ghép, không push.
