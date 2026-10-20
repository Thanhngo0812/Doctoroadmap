# W-03 — Snapshot chuyển worktree, 2026-10-20

**Trạng thái: đang triển khai; CHƯA nghiệm thu toàn vé.** Dừng mọi agent trong checkout chung theo điều phối; chỉ lưu phần W-03 rồi chờ điều phối tạo tmp/w03-email-recovery. Không đổi nhánh hoặc sửa tệp điều phối.

## Đã lưu và kiểm

- Nhánh work/w03-email-recovery, dựa trên nhánh W-02 đã có. Schema checkpoint commit **33c70ac**: migration w03_0004 nối w02_0003; 18 test schema/migration/auth-store đạt trên PostgreSQL bắt buộc, giữ baseline W-01/W-02. [Checkpoint](w03-schema-handoff-2026-10-20.md).
- Root composition/settings/privacy: **33 test đạt**; [XML](w03-evidence/composition-privacy.xml). Lượt RED đầu có 12 failure, 0 collection error; privacy 5 failure trước khi thêm header. Cấu hình public_base_url tin cậy; Mailer SMTP được bọc queue nền giới hạn 32, 2 thread, timeout adapter hữu hạn. Console chỉ dev, production buộc SMTP/STARTTLS và public HTTPS.
- Guard mutations trong bộ nhớ: **3 test đạt**, mỗi test chứng minh assertion quan sát account/audit/phiên bắt được bỏ TTL, bỏ tiêu thụ token và bỏ xoá phiên. [XML](w03-evidence/guard-mutations.xml). Không sửa file nguồn để phá guard.
- React: **51 test đạt**, build đạt theo lượt frontend cuối. [XML](w03-evidence/frontend-tests.xml). Có banner/resend, xác minh, quên/reset; terminal link lỗi ẩn hành động hỏng, lỗi mạng còn retry; token fragment/query được giữ trong state rồi xoá khỏi URL; không POST xác minh khi mở trang GET.
- Mailer: **18 test đạt** theo lượt agent cuối; fake SMTP hoàn chỉnh đã lưu. XML ở w03-email-templates/test_mailer.xml là lượt trước khi sửa ba fake guard, chưa phải bằng chứng của harness cuối. Ba HTML mẫu dùng dữ liệu giả. Guard recipient/header/STARTTLS cần chạy mutation lại bằng harness hoàn chỉnh; lượt RED TypeError cũ không được tính là guard hợp lệ.
- Service W-03: **8 test đạt trước các điều chỉnh P1/P2 cuối** theo agent backend, chưa tính là kết quả cuối. Lượt HTTP/service cuối bị dừng trước khi có kết quả.

## Mã hiện có nhưng cần kiểm tiếp

- accounts.py: register gửi verify/duplicate notice, token một lần/TTL, resend/reset throttle, reset đổi hash và thu hồi mọi phiên/token reset khác; mail enqueue lỗi trả chung và log không chi tiết.
- P1 đã sửa trong mã nhưng thiếu regression: login và reset cùng lock alias account:normalized_email để phiên dùng mật khẩu cũ không được tạo sau khi reset đã thu hồi phiên.
- P2 đã sửa trong mã nhưng thiếu regression: từ chối token reset sai/hết hạn/đã dùng trước khi băm Argon2, rồi kiểm lại trong giao dịch trước cập nhật.
- API W-03 và test_w03_auth_http.py đã lưu nhưng chưa chạy xong. Cần cập nhật test_auth_http.py guard liệt kê unsafe routes để nhận đúng ba POST public mới; vẫn kiểm Origin trước body và vẫn giữ CSRF cho resend/mọi route khác.
- PostgreSQL service/token integration, cuộc đua hai kết nối/tiến trình, generic known/unknown khi mail queue đầy, rollback và audit cần kiểm bổ sung.
- scripts/w03_browser_runtime.py và w03_browser_check.cjs đã viết nhưng **chưa chạy**. Runtime dự kiến DB UUID riêng + Argon2/AuthStore thật + fake Mailer/clock + server loopback 8003, endpoint lấy thư chỉ tồn tại trong script nghiệm thu. Có 18 cấu hình màn, expired/used, reset hai phiên, video và DB hậu kiểm. Cần kiểm script và nhãn form khi chạy lần đầu.

## Việc tiếp theo ở worktree riêng

1. Chờ điều phối báo worktree sẵn sàng; dùng đúng cwd mới. Không thao tác tiếp trong checkout chung.
2. Nhận main theo quy trình điều phối; npm ci; Python luôn qua scripts/w05_run_tests.py để không import nhầm editable từ checkout chung. Chép env nếu cần chạy dev, tuyệt đối không commit.
3. Hoàn thành regression P1/P2, test HTTP/Origin/CSRF và PG service/concurrency. Chạy lại Mailer guard mutations và toàn bộ phần backend liên quan.
4. Chỉnh đường browser tools/binaries/env trong script cho worktree (hiện chúng trỏ .tmp tương đối gốc script; tools và browsers đang ở .tmp của checkout chung). Chạy browser runtime thật, xem ảnh, lưu XML/JSON/video; không gửi thư thật.
5. Chạy cổng cuối trên đúng mã worktree, báo cáo giới hạn; chỉ nhận local-ready khi đầy đủ lát dọc, bàn giao điều phối soát. Không tự ghép main, không tự sửa vé/kế hoạch/handoff.

## Giới hạn đã biết

SMTP nền hiện là queue bộ nhớ: restart có thể mất thư đang đợi; người dùng gửi lại để phục hồi. Không triển khai outbox bền vững ngoài phạm vi schema W-03. Chưa gửi Gmail thật, chưa gọi Cloudinary hay mô hình; chi phí mô hình 0 USD. Chưa nâng DB dev hoặc restart server dev theo W-03.

Nguồn triển khai: [OWASP Forgot Password](https://cheatsheetseries.owasp.org/cheatsheets/Forgot_Password_Cheat_Sheet.html), [Python smtplib](https://docs.python.org/3/library/smtplib.html), [Python secrets](https://docs.python.org/3/library/secrets.html). Quy trình nhánh: doc/quy-trinh-nhanh-va-ghep-main.md trên main, quyết định chủ dự án 2026-10-20.
