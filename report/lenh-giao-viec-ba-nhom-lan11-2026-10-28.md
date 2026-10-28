# Lời giao ba nhóm sau nghiệm thu lần 11 — 2026-10-28

[Biên bản lần 11](dieu-phoi-nghiem-thu-ba-nhom-lan11-2026-10-28.md). Chủ dự án chuyển từng phần; điều phối chưa gửi phiên bên ngoài. Giữ **chỉ commit local, chưa push**, Vertex, chi nhà cung cấp mới 0 USD, không Cloud Figma.

## 1. Nhóm lõi — sửa CORE-R11-01 trước, rồi W-17.2

Tiếp work/w17-admin-users-backend tại tmp/w17-admin-users-backend, bản bàn giao 862dd805 chưa được nhận/chưa ghép. Nhận main local mới có W-12 trước cổng cuối; giữ thay đổi định danh admin đầu tiên và migration w17_0009 nối w12_0008. Không áp dụng migration/CLI vào DB dùng chung trong vé sửa.

Đọc [W-17](../task/web/W-17-quan-tri.md), [ADR 0030](../doc/adr/0030-bao-ve-tai-khoan-admin-dau-tien.md), [review lõi](coord-ba-nhom-lan11-evidence-2026-10-28/core-review/review.md), [probe](coord-ba-nhom-lan11-evidence-2026-10-28/core-review/test_core_probe.py) và [HTTP/SQL](coord-ba-nhom-lan11-evidence-2026-10-28/core-review/core-probe-proof.json).

**CORE-R11-01 — guard admin cuối áp nhầm vào admin đã bị khoá.** Trên source không sửa: A là bootstrap admin active, B là admin thêm sau; A disable B thành công; A PATCH B role=user (kèm quota=7) trả409 conflict “quản trị viên cuối cùng”. SQL vẫn có A active/admin và B disabled/admin. Hạ B không làm mất một admin active nào. Test độc lập assertion đỏ/0 setup error, còn control bảo vệ A xanh.

Chỉ áp guard admin active cuối khi chuyển đổi thực sự làm giảm số admin active. Không bỏ guard quyền/lock/đầu tiên hoặc đổi admin_count về đếm cả disabled. Thêm test B disabled→user, kết hợp enable+demote, nhiều field/quota/audit; A vẫn active và registry giữ đúng A. Giữ test tự thao tác/admin khác, người thường tạo sớm được nâng, concurrency/rollback/login-session và DTO không dữ liệu riêng. Chứng minh RED trên862dd805→GREEN, phá điều kiện vừa sửa để test đỏ bằng assertion, phục hồi SHA.

POL-R10-01 đã sửa đúng phần định danh bền vững; không làm lại toàn registry hoặc tạo thêm role. Kế hoạch DB hiện hữu với UUID đối chiếu/bootstrap_required/CLI một lần được giữ; trước vận hành thật phải có backup và cửa operator riêng. W-20 chưa có deleteAPI; không dựng tạm endpoint xoá trong bản sửa.

**Sửa hồ sơ cùng lượt:** manifest380 tệp có hai hàng stale: redactions.json và packaging-note.json; chốt nội dung rồi cập nhật bytes/SHA. Giữ lịch sử. Tên đường dẫn SQL dài cần git -c core.longpaths=true theo từng lệnh, không đổi global config hoặc xoá evidence.

Bàn giao báo cáo mới, source pin, JUnit/native và SQL độc lập. Full PostgreSQL qua scripts/w05_run_tests.py trong cửa riêng, React/build đúng nguồn sau nhận main; không bare pytest, không SMTP/LLM/media thật. Sau khi được nhận: **W-17.2 chỉ metadata bản dựng + đánh dấu/bỏ khoá mẫu**, tái dùng service/policy/audit, phân trang/lọc giới hạn, mẫu dev theo allowlist sáu cuốn. Chưa nối retry/cancel hoặc bảng chi.

## 2. Nhóm web — W-12 đã nhận; mốc kế tiếp React W-17.1

W-12 a8e2075d đạt sau sửa WEB-R10-01, toàn vé backend+React được nhận. Giữ W-04 Auth epoch/profile/password/logout-all và W-12 fragment/inbox/50 email/200 thư/TTL 7 ngày/email verified; không làm lại. Browser mới của điều phối có source pin và HTTP/SQL, có thể dùng làm nguồn đối chiếu W-23 khi ghi đúng nguồn/state.

**Điều kiện bắt đầu tích hợp React W-17.1:** main local phải đã nhận backend W-17.1 sau sửa CORE-R11-01. Hiện862dd805 còn ở nhánh; không giả backend đã ghép. Trong lúc chờ bản sửa ngắn, chuẩn bị danh sách trạng thái/màn theo spec và phối hợp thiết kế chụp React hiện tại, không tạo API/DTO quản trị giả để bàn giao chức năng đã hoàn tất.

Khi đủ điều kiện, tạo work/w17-admin-users-react trong tmp/w17-admin-users-react từ main local mới. Mốc này chỉ màn **Người dùng và Nhật ký**: tìm/lọc/phân trang, cập nhật trạng thái/vai trò/quota override, audit metadata. Không hiện thẻ Bản dựng/Chi/Khoá mẫu chưa có backend thành chức năng đã chạy.

DTO is_first_admin và lỗi protected_admin/bootstrap_required phải theo OpenAPI bản backend cuối: true bảo vệ nút khoá/hạ quyền; null giải thích chưa xác lập bảo vệ và phản ánh lỗi server. Server luôn kiểm quyền, không suy bootstrap từ hàng đầu bảng/created_at/bộ lọc. Giữ profile/password bình thường. Kiểm401/403/stale callback khi chuyển tài khoản, field422/409, xác nhận thao tác nguy hiểm và kết quả thật. Không raw meta/token/hash/chat/tài liệu riêng/đáp án quiz.

Giao diện rõ, đẹp theo token/taste-skill, logo/font đúng;1280/768/390 không vỡ, focus/bàn phím/reduced-motion thật. Browser HTTP/PG với tài khoản tổng hợp, SQL độc lập, ảnh/video và mutation guard. Không cần Cloud Figma. W-17 vẫn mở cho các mốc tiếp theo.

## 3. Nhóm thiết kế — hoàn thiện receipt lát 1 rồi mở rộng W-23

Tiếp work/w23-paired-web-evidence tại tmp/w23-paired-web-evidence;60412c87 chưa nhận/chưa ghép cả gói. Đã xác nhận ba crop React đúng từng pixel, hash nguồn raw CRLF/Git LF đúng, đính chính AA/target/no-lag và copy W-04/W-12 đúng. **Giữ các phần đó**, không làm lại token/branding/math hay Cloud.

Đọc [W-23](../task/web/W-23-doi-chieu-figma-va-giao-dien.md), [review](coord-ba-nhom-lan11-evidence-2026-10-28/design-review/review.md) và [kiểm ảnh/hash](coord-ba-nhom-lan11-evidence-2026-10-28/design-review/evidence-inspection.json). Sửa đúng hai Required:

1. **D-R11-01 — ràng buộc nguồn hiện hành.** Ảnh React lịch sử phải giữ nhãn lịch sử. Chụp component hiện tại hoặc chứng minh reuse hẹp cho đúng leaf/style/state; diff1fc0f553 → aaf68eb không chứng minh currentmain. ContentLibrary hiện có thêm UsageLimits; W-08 có thêm library/assistant. Ghi source/assets/URL/viewport/DPR/theme/motion/state/crop và số đo thực của React, không chỉ trích một con số guard lịch sử. Được phối hợp web/harness0 USD; không sửa React chéo. Không kết luận self-check hỏng chỉ vì diff file có phần khác.
2. **D-R11-02 — một receipt cho đúng một run/ảnh.** Báo cáo§3.2 nói W-08 offline SegoeUI/no font faces, JSON lại ghi custom Be Vietnam Pro, 78 glyph/loaded. Hai run khác nhau phải tách rõ; không gán số đo/font mới cho PNG tái dùng mà không có cùng nguồn. PNG thực W-08 folded808×62, open808×154; W-10 HTML366×808. Sửa bảng/JSON; lưu floating CSS rect riêng với decoded PNG dimensions, không Math.round(rect.height) làm kích thước PNG. Đính kèm command/cwd/native, full SHA và font/assets cùng run. Nếu dùng fallback phải ghi nhãn; nếu chứng nhận font thiết kế thì dùng font thật và giữ SHA asset.

Script đã tái tạo được cục bộ trong browser cô lập; không cần xây một hệ capture mới. Nhận main mới trước chốt; giữ hai cặp self-check/thư viện cho đủ bằng chứng rồi mở rộng W-08/09/10,768/sáng-tối, bàn phím/reduced-motion/video. Đề xuất2/3tab và cách trình bày câu hỏi vẫn mở; giữ React hiện có cho tới quyết định, không tự sửa spec. W-23 chưa đóng toàn vé.

Không sửa đè tám bản untrackedW-23 ở thư mục chung; điều phối giữ SHA. Giữ mọi ảnh/video/crop cũ, sửa hồ sơ bằng commit mới.

## 4. Thứ tự và các việc chưa mở

Lõi sửa W-17.1 → điều phối soát/ghép local → web React W-17.1 và lõi W-17.2 có thể chạy song song vì tách frontend/backend. Thiết kế hoàn thiện hai receipt rồi hỗ trợ màn quản trị. Tiếp đó mới các mốc chi/validation, W-18/W-19/W-20 và W-21; không coi hiện đã xong hoặc sẵn production. W-20 phải giữ bảo vệ xoá bootstrap admin.

**Điểm cần phối hợp Claude còn mở:** port admin retry/cancel thay chủ khoá; BuildService hiện require_upload/requested_by, HTTP có admin retry nhưng chưa admin cancel. Chốt quyền/trạng thái/audit/idempotency/grant/budget/receipt trước triển khai, không giả Actor người tải hay nới guard chung. Không cản việc sửa CORE-R11-01.

Mỗi vé một worktree một cấp dưới tmp, root luônmain; chỉ commit đường dẫn được giao, không tự ghép/push. Một full PG mỗi lúc, fixture chỉ ordinarycopy có allowlist/SHA; không liên kết, không live learner cache/tập giữ lại. Không xoá/dọn WT/artifact/PDF/ZIP/snapshot/DBW-15; tuyệt đối không đụng tmp/t01a-clean-ff797eb. Không paid grant/rerun W-15, không đổi Vertex hay bật trần demo.
