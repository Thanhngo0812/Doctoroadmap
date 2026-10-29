# Nghiệm thu lần 13 — React W-17.1 Người dùng/Nhật ký, 2026-10-29

**Cập nhật sau sửa — đạt, đã ghép local `e4465b4c`, chưa push.** Subagent web sửa ở `b1b699ca` (chỉ `Admin.test.tsx` và báo cáo; `Admin.tsx`
giữ SHA `ce6da3df…`). Báo cáo sạch dấu. Bản ghép thử `6dfbb3ba` (nhánh + main `f71b694c`): build đạt, **React 283/283**; hai phép phá từng sống sót
nay đều bị bắt (`mui-gio` bởi test múi giờ mới; `patch-403-giu-du-lieu` bởi test PATCH 403 mới và test GET 403 đã sửa), nên bộ phá Claude 8/8.
`ghep_guard.sh` in GUARD OK. Bằng chứng ở `coord-r13-evidence-2026-10-29/sau-sua/`. Optional ô khoá chế độ tối chưa sửa. Toàn W-17 vẫn mở.

**Người nghiệm thu:** Claude (điều phối từ 2026-10-29, thay Codex). **Kết quả: chưa đạt, chưa ghép.** Mã React đúng ở mọi chỗ đã soát; còn ba Required
về hồ sơ và test (WEB-R13-01…03), giao subagent web sửa trên cùng nhánh. Chi nhà cung cấp 0 USD, chỉ commit local, chưa push.

## 1. Mốc được soát

| | commit |
|---|---|
| nhánh web | `work/w17-admin-users-react`, mã kiểm `b75e611b`, hồ sơ `af461e8a` (không đổi `src/`, `scripts/` so với `b75e611b`) |
| nền nhánh | main `647149b3` |
| bản ghép thử | `0d5d4476` = `af461e8a` + main `3a0920b2`, worktree `tmp/coord-r13-acceptance-20261029` |

Main từ `647149b3` tới `3a0920b2` chỉ đổi `evaluation/`, `tests/evaluation/` và tài liệu. Nhánh chỉ đổi 9 tệp: `Admin.tsx`, `Admin.test.tsx`,
`admin-api.ts`, `admin.css`, hai dòng ở `App.tsx`/`Courses.tsx`, ba script harness `scripts/w17_react_*`. SHA blob `Admin.tsx` = `ce6da3df…`, khớp báo cáo.

## 2. Cổng rút gọn (chủ dự án chọn 2026-10-29)

Chủ dự án chọn cổng rút gọn thay cổng toàn repo, vì phiên Pha A đang chạy test và máy còn khoảng 2–3 GB RAM trống. Cổng toàn repo được tính là lượt của
nhóm web trên `b75e611b`: **3833 pass/0 fail/3 skip/1 xfail**, native 0 (theo `gate-python-integrated/exit.json` trên nhánh); Python của bản ghép thử
khác lượt đó chỉ ở phần đánh giá, do phiên Pha A gác bằng cổng riêng.

| phép kiểm trên `0d5d4476` | kết quả | bằng chứng |
|---|---|---|
| build TypeScript/Vite | native 0 | lệnh `npm run build` |
| React toàn bộ | **281 pass / 21 tệp**, native 0 | `coord-r13-evidence-2026-10-29/react-candidate.xml` |
| `src/web/backend/tests` qua runner, PostgreSQL bắt buộc **644 pass / 1 fail / 1 skip**, native 1. Ca đỏ duy nhất `test_internal_dry_run_w15…[candidate]` là thiếu fixture `tmp/w15-candidate/input.pdf` trong worktree nghiệm thu (FileNotFoundError khi dựng), không phải hồi quy; nhánh không đổi Python và ca này xanh trong cổng 3833 của nhóm web | `coord-r13-evidence-2026-10-29/web-backend-candidate.xml` |

## 3. Đọc mã

Đã đọc toàn bộ `Admin.tsx`, `admin-api.ts`, `Admin.test.tsx` và hai dòng nối route/menu. Đạt theo lời giao lần 12 mục 1:

- quyền: menu chỉ hiện với role admin, route kiểm role từ phiên, server quyết định cuối; 401/`account_disabled` xoá phiên, 403 gỡ dữ liệu và hiện màn Denied;
- `is_first_admin` lấy từ server; `true` khoá hai ô trạng thái/vai trò, `null` giải thích và để server trả `bootstrap_required`; không có ô nhập UUID;
- PATCH chỉ gửi trường đổi, đổi vai trò/trạng thái phải qua bước xác nhận, hạn mức `null` nghĩa là dùng hạn mức chung, báo thành công sau phản hồi thật;
- `AbortController` cho GET/PATCH, khoá component theo id/role/đường dẫn: phản hồi cũ không ghi đè sau đổi bộ lọc, đổi tài khoản hay đóng hộp thoại;
- nhật ký chỉ hiện trường công khai, không in `meta`.

Ảnh `users-1280-light`, `users-390-light`, `first-admin-768-dark` đã xem: đúng token/logo/font, 390 không tràn. Optional: hai ô bị khoá của admin đầu tiên
ở chế độ tối gần như giống ô đang bật (chỉ khác màu chữ).

## 4. Bộ phá độc lập của Claude

Tám phép, khác sáu phép của nhóm web; mỗi phép chạy `Admin.test.tsx`, khôi phục bytes và đối chiếu SHA. Script và XML ở
`coord-r13-evidence-2026-10-29/mutations/`.

| phép phá | bị bắt |
|---|---|
| `thua-truong`: luôn gửi `build_monthly_max` | có (enable+demote, `toEqual` thân PATCH) |
| `bo-xac-nhan`: đổi vai trò/trạng thái gửi ngay | có (5 test) |
| `null-la-dau-tien`: coi `is_first_admin=null` là được bảo vệ | có (`bootstrap_required`) |
| `han-muc-0`: nhận hạn mức 0 | có |
| `lo-meta`: in cả bản ghi nhật ký | có (`PRIVATE_AUDIT_MARKER`) |
| `giu-offset`: lọc mới giữ offset cũ | có |
| `mui-gio`: `value+'+07:00'` → `value+'Z'` khi lọc nhật ký | **sống sót** |
| `patch-403-giu-du-lieu`: tắt nhánh `forbidden` trong `fail` | **sống sót** |

## 5. Required

- **WEB-R13-01 — báo cáo mất dấu tiếng Việt.** Trong blob Git của `report/w17-react-tich-hop-2026-10-29.md`, từ mục "Lượt tích hợp" tới hết (23 dòng),
  chữ có dấu đã thành `?`: mục lượt tích hợp, lệnh, giới hạn, kết quả cổng PostgreSQL cuối. Số còn đọc được nhưng hồ sơ sẽ vào main nên phải đọc được.
- **WEB-R13-02 — múi giờ lọc nhật ký không có test.** Báo cáo nêu bất biến "nhập giờ Việt Nam, chuyển UTC khi gửi", nhưng phép `mui-gio` lệch 7 giờ vẫn
  qua 281 test React và browser (harness browser không thử `since`/`until`).
- **WEB-R13-03 — PATCH 403 không có test gỡ dữ liệu.** Lời giao lần 12 đòi "mất quyền thì huỷ/loại phản hồi cũ". Mã đúng, nhưng phép tắt nhánh
  `forbidden` vẫn xanh: test GET 403 chỉ tìm chữ "Bạn không có quyền quản trị.", trùng giữa màn Denied và thông báo lỗi; chưa có test PATCH 403.

Cả ba sửa trên nhánh `work/w17-admin-users-react`, không đổi hành vi mã. Lời giao: `tmp/claude-tools/prompt-cai-w17-1-sua-r13.md`.

## 6. Kế hoạch tiếp — ba subagent, từng cái một

Chủ dự án chốt 2026-10-29: ba subagent thay ba nhóm, chạy từng agent một, luật cũ giữ nguyên. Sổ tay chung `tmp/claude-tools/so-tay-agent-web.md`.

| thứ tự | subagent | việc | lời giao |
|---|---|---|---|
| 1 | web | WEB-R13-01…03 (nhỏ, mở khoá ghép W-17.1) | `prompt-cai-w17-1-sua-r13.md` |
| 2 | lõi | W-17.2 `GET /admin/builds`, `PATCH /admin/courses/{cid}` | `prompt-cai-w17-2.md` |
| 3 | thiết kế | D-R12-01 rồi mở rộng W-23 | `prompt-cai-d-r12-01.md` |

Web làm trước lõi vì việc nhỏ và cho phép ghép W-17.1 sớm; lõi không phụ thuộc mốc React này. Sau W-17.2 đạt mới giao React bản dựng/khoá mẫu.
DB dùng chung vẫn chưa áp migration `w17_0009`/CLI bảo vệ admin đầu tiên; việc đó cần chủ dự án và hồ sơ định danh, ngoài các vé trên.
