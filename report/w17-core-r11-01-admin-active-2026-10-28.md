# W-17.1 — CORE-R11-01: chỉ kiểm admin active cuối khi thực sự giảm admin active

## 1. Phạm vi và nguồn

Tiếp nhánh `work/w17-admin-users-backend` tại `tmp/w17-admin-users-backend`; bản bàn giao `862dd805180201647cd6a3dda54c2083073d1e84` chưa nhận/chưa ghép. Đọc W-17, ADR 0030, review/probe và HTTP/SQL độc lập lần 11. Review POL-R10-01 xác nhận định danh đầu tiên đã đúng; sửa này không làm lại registry hoặc migration.

Giữ `w17_0009` nối `w12_0008`, immutable UUID bootstrap, trigger DB, bootstrap/audit transaction và kế hoạch operator xác minh UUID cho DB hiện hữu. Không áp migration hoặc CLI vào DB dùng chung, không tạo role/delete API tạm, không sửa core/transport/giá/trần. Mailer/model/embedding/media giả, chặn ADC/network, chi mới 0 USD. W-17.2 chưa bắt đầu; cần điều phối nhận bản sửa trước.

## 2. Nguyên nhân và sửa

`admin_count()` đã đếm `role=admin AND status=active`, nhưng guard trước chỉ nhìn target.role admin và role mới user. Vì vậy B disabled/admin cũng bị coi là loại một admin active: A bootstrap active vẫn còn nhưng hạ B nhận 409 conflict sai.

Sửa tối thiểu ở `AdminService.update_user`, bên trong các account/admin locks và sau kiểm định danh đầu tiên:

- `was_active_admin = target.role == admin AND target.status == active`.
- `will_be_active_admin = final_role == admin AND final_status == active`, dùng giá trị PATCH nếu có, nếu không giữ giá trị cũ.
- Chỉ khi was=true và will=false mới đọc `admin_count` để từ chối nếu số admin active <=1.

Disabled B -> disabled/user, hoặc disabled B -> active/user trong cùng PATCH đều không giảm admin active. Active B đổi quota/field khác mà vẫn active/admin cũng không giảm. Active/admin -> user hoặc disabled vẫn giữ guard. Count không đổi về đếm disabled; quyền Actor/live status, lock, bootstrap guard, transaction, session revoke, audit và DTO không bị bỏ/nới.

PATCH hợp lệ trả 200 theo DTO hiện có, không thêm lỗi/endpoint/schema. Hạ B ghi role_changed, enable kèm theo ghi enabled, quota kèm theo ghi quota_changed; mỗi field đổi đúng một event với actor từ phiên và target B, meta rỗng. Replay cùng giá trị không ghi trùng. A vẫn active/admin, phiên A dùng được, registry đúng UUID A; enable B không hồi sinh cookie cũ. Audit lỗi phải rollback cả role/status/quota, không đổi registry.

## 3. RED trên bản cũ, GREEN và mutation

`test_w17_r11.py` dùng fixture PostgreSQL/cookie/Argon2 thật và phụ thuộc ngoài giả hiện hành; SQL dùng connection độc lập.

- `r11-red-01` chạy trên đúng HEAD **862dd805** chưa sửa: **4 assertion fail, 1 control pass, 0 setup error**. B disabled -> user, enable+demote, kèm/không quota đều nhận409 sai; control bảo vệ A xanh. JSON response/status và account/registry SQL lưu trước assertion.
- `r11-green-01`: 6 pass, 2 fail ở phép kiểm thứ tự audit của test. DTO chuẩn hóa thứ tự field theo schema, không giữ thứ tự field payload. Đã sửa test để kiểm disabled event đầu tiên, đúng tập event/count còn lại và replay không thêm event; không bỏ kiểm audit/SQL.
- `r11-green-02`: **8 pass**. Bao gồm bốn tổ hợp hợp lệ, control bootstrap, không query admin_count cho disabled target, guard fallback last-active vẫn từ chối và audit rollback. Guard fallback dùng port count giả=1 để kích nhánh phòng thủ; không coi đó là SQL thật có A+B active mà chỉ đếm1.
- Mutation: **2/2 bị bắt bằng assertion, 0 setup error**. Bỏ điều kiện target.status active làm4 ca disabled-demote đỏ; bỏ guard active-removal làm control fallback đỏ. Nguồn phục hồi byte/SHA sau từng lần; native/JUnit ở `mutations.json` và runs riêng.
- Cổng cuối trên `e7d54a1a7969715012c099cc0d7f028f48038c41`: **3626 Python pass**, 3 skip, 1 xfail; native0, 897.84s wrapper. **259 React pass/20 file**, native0, 143.60s; build native0, 3.67s. Toàn bộ79 ca W-17 chạy và đạt; tên/lý do skip/xfail trong summary/JUnit. Không ghi đè lịch sử cổng cũ.

Full PG đã đạt **3.626 pass, 3 skip, 1 xfail**, native0. Hai skip graph đánh giá cần DANHGIA_KHO_CHUNG; một skip Cloudinary thật; xfail replay SA-66 bản ghi answer-2 cũ cần ghi lại bằng lượt trả phí. Không bật các điều kiện ngoài phạm vi0USD; lý do nguyên bản giữ trong JUnit/summary. Không có ca W-17 bị skip.

| Invariant | Assertion |
|---|---|
| Disabled demote/enable+demote, quota và audit/SQL đúng | `test_disabled_later_admin_demotion_and_enable_demotion_are_atomic` (4 case) |
| A tự thao tác hoặc admin khác vẫn bị chặn, từ chối nguyên tử | `test_bootstrap_protection_remains_a_separate_control` |
| Disabled target không bị áp count guard | `test_disabled_transition_does_not_query_last_active_admin_count` |
| Guard last-active vẫn thực thi khi transition giảm active admin | `test_active_admin_removal_retains_count_guard_and_atomic_refusal` |
| Audit lỗi rollback tất cả field và registry | `test_disabled_demotion_audit_failure_rolls_back_all_fields_and_preserves_registry` |

Giữ toàn bộ 71 ca W-17 trước sửa: identity self/other, user thường tạo sớm được nâng, runtime reload, concurrency bootstrap/role, rollback, stale/disabled Actor, hai cookie/login race, profile/password/CSRF, metadata DTO/private marker, quota null và biên tháng Việt Nam.

## 4. Manifest 380 hàng — chốt bytes trước khi băm

Đã tái hiện nguyên nhân hai hàng stale: `redactions.json` và `packaging-note.json` được ghi bởi write_text trên Windows, SHA/bytes trong manifest tương ứng CRLF worktree; Git lưu blob LF nên reviewer checkout kiểm không khớp. Trên worktree ban đầu 380 hàng đều khớp raw bytes, nhưng đối chiếu blob Git thấy:

- redactions: worktree172 bytes, blob Git168 bytes.
- packaging-note: worktree244 bytes, blob Git237 bytes.

Chuẩn hóa hai tệp sang UTF8/LF bằng write_bytes **trước** tính bytes/SHA, cập nhật đúng hai hàng; các nội dung và kết quả không thay đổi. Manifest gốc và bản trước chuẩn hóa cùng chênh lệch row/blob được giữ trong `w17-r11-evidence/history/`. Không xóa/đổi tên SQL proof dài, không đổi global config. Git dùng `-c core.longpaths=true` theo từng lệnh. Sẽ kiểm cả worktree và blob commit của toàn bộ380 hàng trước bàn giao.

Sau commit sửa đã kiểm **380/380 raw worktree và380/380 blob Git khớp bytes/SHA** (`history/manifest-verification.json`). `.gitattributes` riêng hai thư mục evidence ghim text LF khi checkout, không sửa root/global config. Hai file redactions/packaging có nội dung JSON và blob Git không đổi; thay hash/bytes trong manifest để theo đúng blob LF. Bản manifest trước sửa vẫn giữ riêng.

## 5. Main, cổng và bàn giao

RED được ghi trước khi nhận main để chứng minh đúng bản 862dd805. Trước cổng cuối nhận main local mới có W-12 bằng merge, không rebase; kiểm sửa dở và giữ export test của worktree. Thư mục chung luôn main, không tự ghép/push main.

Source sửa `68663726`; đã nhận main local `b2fedda1` có W-12 qua merge, source HEAD chạy cổng **`e7d54a1a7969715012c099cc0d7f028f48038c41`**. Không có sửa mã sau merge khi chạy cổng. Một lệnh merge đầu dùng option không hợp lệ (`--stat=0`) chỉ trả usage/error, không sửa ref; đã nhận lại bằng `merge main --no-edit --no-stat` thành công, không rebase/restore việc người khác.

Cổng cuối phải chạy cùng source HEAD ổn định: full PG qua `scripts/w05_run_tests.py` với basetemp mới, rồi React single worker, rồi build, một cổng toàn repo mỗi lúc. Native command/cwd/HEAD/source SHA/JUnit/log và SQL ở evidence mới. Không bare pytest, không provider/SMTP/Cloudinary thật. Cả ba cổng cuối đã đạt trên cùng HEAD, không đổi nguồn giữa cổng.

## 6. Giới hạn và mốc sau

Registry/CLI đối chiếu DB hiện hữu vẫn giữ: backup, hồ sơ bootstrap/UUID có căn cứ, migration/CLI một lần trong cửa operator riêng sau nghiệm thu. Không suy từ role/status/current list/created_at, không tự phục hồi W-15. W-20 chưa có API xóa; bảo vệ trigger/FK hiện hành giữ nguyên.

Sau khi điều phối nhận bản sửa, W-17.2 chỉ metadata bản dựng GET /admin/builds và đánh dấu/bỏ mẫu PATCH /admin/courses/{cid}, tái dùng service/policy/audit, lọc/phân trang giới hạn, mẫu dev theo allowlist sáu cuốn. Không nối retry/cancel thay requested_by hoặc bảng chi khi hợp đồng chưa chốt. Toàn W-17 còn React/chi/bản dựng/khoá mẫu; không đánh dấu hoàn thành vé.

W-15 dữ liệu/plan/grant/receipt/artifact giữ nguyên; unknown0,4139008USD không biến thành0/hóa đơn. Khi làm chi sau phải loại counted_in=build khỏi cộng trùng, giữ billing_verified/unknown và nhãn “ước theo token, không thay hoá đơn”. Đề xuất build5USD/ngày và3lượt/người/tháng chưa bật, không là quyền chi.

Lệnh PG cuối: `python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/w17-r11-full-01 --junitxml=report/w17-r11-evidence/runs/r11-full-01.xml`; React `npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1`; build `npm.cmd --prefix src/web/frontend run build`. Native/cwd/source SHA/JUnit/log trong runs; JSON/schema cho React trong public. Native bytes trước chuẩn hóa giữ local ignored tmp/w17-r11-raw-evidence; manifest ghi raw SHA và SHA UTF8/LF bàn giao.
