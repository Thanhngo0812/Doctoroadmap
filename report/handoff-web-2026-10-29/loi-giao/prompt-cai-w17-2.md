# Lời giao subagent lõi — W-17.2 metadata bản dựng và khoá mẫu (backend)

Bạn là subagent lõi của dự án WayFinder. Đọc theo thứ tự rồi mới làm:
1. `tmp/claude-tools/so-tay-agent-web.md` (sổ tay, luật cấm, môi trường, bằng chứng).
2. `task/web/W-17-quan-tri.md` và `task/web/00-ke-hoach.md` mục "Luật chung của mọi vé".
3. `report/lenh-giao-viec-ba-nhom-lan12-2026-10-28.md` **mục 2** (lời giao gốc của mốc này; lõi chưa nhận nên chưa ai làm).
4. `doc/web-chuc-nang-spec.md` mục 3, 9, 10, 11 (bảng HTTP nhóm quản trị), mục khoá mẫu (quanh dòng 434) và `doc/adr/0030-bao-ve-tai-khoan-admin-dau-tien.md`.
5. Mã hiện có: `src/web/backend/wayfinder/api/admin.py`, `AdminService`, `BuildService`, `CourseService`, test W-17.1 trong `src/web/backend/tests/`.

Worktree `tmp/w17-builds-samples-backend`, nhánh `work/w17-builds-samples-backend`, tạo từ main local mới nhất.

## Phạm vi — chỉ hai điểm cuối

1. **`GET /api/v1/admin/builds`**: danh sách siêu dữ liệu bản dựng, tìm/lọc/phân trang phía server có giới hạn (theo cách W-17.1 làm `limit`/`offset`/
   tổng). Tái dùng bảng/port hiện có. DTO rõ cho frontend, chỉ metadata được phép: không nội dung giáo trình, raw exception/stacktrace, chat, tài liệu,
   quiz hay dữ liệu học riêng.
2. **`PATCH /api/v1/admin/courses/{cid}`** (`is_sample`): đánh dấu/bỏ khoá mẫu theo policy W-06, chỉ ở `env=dev`, chỉ cho khoá thuộc allowlist sáu cuốn
   phát triển. Tái dùng cờ/bảng đã có; **không tạo migration rỗng**; không biến tài liệu riêng ngoài allowlist thành mẫu. Mọi mutation ghi `audit_event`
   nguyên tử (audit lỗi thì rollback cả thay đổi).

Tái dùng `AdminService`/`BuildService`/`CourseService` đúng ranh giới, không nhân đôi policy ownership/quota. Admin live kiểm ở cả service lẫn route;
người thường, tài khoản disabled, Actor cũ (stale) không đọc hay sửa được. Giữ nguyên mọi thứ W-17.1 đã nhận: định danh admin đầu tiên, guard admin active,
giao dịch/lock/audit/session, migration `w17_0009`. Không làm lại registry, không sửa migration đã ghép.

**Ngoài phạm vi mốc này:** admin retry/cancel bản dựng, bảng chi, Cloudinary, `lecture_validation`. `BuildService` hiện đòi `require_upload`/
`requested_by`: không giả Actor người tải, không nới guard chung. Không gọi provider, không chạy lại W-15, không bật trần 5 USD/ngày hay 3 lượt/tháng.

## Test cần có (mỗi cái đỏ trước trên bản sai)

- Route liệt kê: người thường/disabled/stale gọi hai route mới đều `forbidden`; test kiểm route mới tự vào danh sách route admin.
- Phân trang/lọc/biên ngày của `GET /admin/builds`, tổng đúng; giới hạn `limit`.
- DTO không lộ dữ liệu riêng: cài chuỗi đánh dấu giả vào chat/tài liệu/quiz/lỗi build, kiểm phản hồi không chứa.
- `PATCH is_sample`: bật/tắt đúng; khoá ngoài allowlist hoặc `env=prod` bị từ chối; audit ghi đúng một lần; audit lỗi thì rollback (quan sát bằng SQL
  độc lập); hai request cạnh tranh không để trạng thái lệch.
- Bảng phá của bạn: ít nhất bỏ kiểm admin ở service, bỏ kiểm allowlist, bỏ kiểm `env`, tách audit khỏi giao dịch, bỏ lọc trường riêng khỏi DTO.

## Bàn giao

Báo cáo `report/w17-2-builds-samples-backend-<ngày>.md` theo sổ tay mục 5: ví dụ JSON thật hai điểm cuối, OpenAPI/trạng thái lỗi làm hợp đồng cho mốc
React tiếp theo, lệnh/số test (`src/web/backend/tests` qua runner + test React nếu đụng frontend), bảng phá. Không chạy cổng toàn repo. Không ghép.
