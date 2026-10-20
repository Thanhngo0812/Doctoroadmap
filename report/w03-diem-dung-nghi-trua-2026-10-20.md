# W-03 — Điểm dừng nghỉ trưa, 2026-10-20

**Tạm dừng theo yêu cầu chủ dự án. Chưa nghiệm thu W-03; chưa ghép main.**

## Nơi tiếp tục

- Worktree: C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w03-email-recovery.
- Nhánh: work/w03-email-recovery. Đã nhận main tại 66d8160; snapshot trước đó fdd0620 và schema checkpoint 33c70ac.
- Thư mục chung luôn ở main; mọi lệnh và chỉnh sửa tiếp theo phải chỉ rõ workdir worktree. Không cần chủ dự án chuyển session thủ công.
- Chỉ W-03 của nhóm web. W-06 thuộc nhóm lõi. Không sửa task/, kế hoạch/handoff hay báo cáo điều phối; không tự ghép/push main.

## Đã lưu và kiểm được

- Backend tập trung: **40 test đạt**, gồm HTTP Origin/CSRF, token, PostgreSQL thật, rollback, giới hạn yêu cầu và cạnh tranh login/reset. [XML](w03-evidence/backend-focused.xml).
- PostgreSQL race đã kiểm bằng backend PID + pg_stat_activity: reset thực sự chờ Lock của login; bỏ alias khoá trong mutant thì phiên đăng nhập bằng mật khẩu cũ còn sống. Token reset sai/hết hạn/đã dùng bị từ chối trước khi băm mật khẩu. Đăng ký trùng chỉ gửi đúng một notice, không tạo token/phiên hay đổi tài khoản cũ.
- Mailer **20 test đạt**, gồm fake SMTP hoàn chỉnh và các mutant bỏ guard thực sự đi tới kết nối/giao thư giả. [XML](w03-email-templates/test_mailer.xml). Mẫu xác minh đã sửa lời văn đúng mục đích mời qua email.
- React **55 test đạt**, build đạt. [XML](w03-evidence/frontend-tests.xml). Sửa lỗi mở link khác trong cùng tab còn kết quả cũ; chặn response cũ ghi đè link mới; xoá toast thành công cũ khi nhận token link mới, vẫn giữ toast sau chính thao tác thành công.
- Browser lượt 4 **đạt**: 18 cấu hình (390/768/1280 × sáng/tối × verify/forgot/reset), axe WCAG AA 0 lỗi, không tràn ngang, vùng bấm 44 px; 8 nhóm assertion luồng. Bốn trạng thái expired/used còn được kiểm axe sau khi animation kết thúc và không còn toast thành công cũ. [Audit](w03-evidence/browser-audit.json), [runtime](w03-evidence/isolated-runtime.json), [video](w03-evidence/w03-auth-flow.webm).
- Runtime browser dùng PostgreSQL/AuthStore/Argon2 thật, Mailer/Clock giả; không POST khi chỉ mở link GET; reset thu hồi hai phiên cũ, mật khẩu cũ bị từ chối và mật khẩu mới đăng nhập được. DB kiểm UUID riêng đã dọn.
- Taste inspector: **0 FAIL, 3 WARN** ở 1280/768/390. [Log](w03-evidence/taste-inspect.log), [JSON](w03-evidence/taste-inspect/report.json). Còn cần hoàn tất critique bằng ảnh; không coi đo lường tự động là chấm thiết kế. Bám màn design/preview/w03_auth_screens.html và token thương hiệu, giữ toast bên phải/khung vừa chữ/text giữa.
- README W-03 và OpenAPI đã cập nhật. Chưa nâng DB dev hoặc thay server dev hiện tại.

## Cổng toàn bộ chưa đạt

Lệnh đã chạy:

    C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/cong-w03-final-1 --junitxml=tmp/cong-w03-final-1.xml

**Bị dừng ở khoảng 13% theo yêu cầu nghỉ trưa.** Log có **4 ký hiệu F** ở đoạn đầu, chưa in traceback/tên test và chưa sinh JUnit. Không kết luận nguyên nhân hay báo cổng xanh. [Log dở](w03-evidence/full-gate-interrupted.log). Khi tiếp tục cần xác định bốn failure trước, rồi chạy lại toàn bộ cổng với basetemp mới. Không cộng các lượt tập trung thành số test toàn bộ.

## Việc còn dở khi tiếp tục

1. Chẩn đoán bốn failure của cổng toàn bộ (có thể chạy lại với -x --tb=short qua runner để lấy lỗi đầu). Không chạy pytest trần vì .venv editable trỏ checkout chung.
2. Review phát hiện góc cạnh request-reset/confirm-reset: request có thể chèn và commit token sau UPDATE quét sibling nhưng trước commit của confirm. Chưa sửa. Backend agent đã nhận yêu cầu test hai kết nối tái hiện thứ tự commit, rồi thêm alias account:normalized_email vào khoá request (giữ known/unknown giống nhau). Request được tuần tự hoá SAU reset vẫn là yêu cầu mới hợp lệ, không được chặn sai.
3. Review nêu logout xoá cookie dùng request.scheme trong khi login/reset dùng _secure_cookie. Chưa sửa/kiểm. Cần xác định hành vi prod qua TLS proxy, thêm assertion đúng Secure rồi sửa nếu tái hiện.
4. Hoàn tất review ảnh/critique taste ở mọi viewport, kể cả trạng thái lỗi mới; frontend agent bị dừng trước khi viết critique. Không thay lại phần thiết kế W-24 đã đạt và không coi preview local là bằng chứng Figma.
5. Cổng cuối sau khi sửa: toàn bộ Python qua runner, React với 1 worker, build, browser + taste. Gặp WinError 5 phải chạy lại cả vòng với basetemp mới và lưu cả hai lượt; tái diễn thì đỏ. Lưu số test thật, không bỏ qua guard.
6. Soát diff/phạm vi/secret/trailing whitespace, báo cáo nghiệm thu local, commit đúng tệp của vé, gửi điều phối soát độc lập. Các commit W-02/W-24 mang theo (781415b/79cb9c9/6cd6be7) cũng chưa tự coi đạt.
7. Sau khi đủ điều kiện mới chuẩn bị local runtime W-03 bằng đúng mã worktree; không lặng lẽ thay server checkout chung. SMTP thật chưa gửi trong kiểm thử.

## Tạm dừng và giới hạn

Ba agent Luna đã được dừng. Cổng Python đã ngắt; browser lượt 4 đã thoát thành công và dọn DB. Đã kiểm và dừng tiến trình kiểm W-03 còn sót bằng tên script/basetemp cụ thể; không dừng Docker hay server dev đang có.

Queue SMTP là bộ nhớ, tối đa 32 tác vụ/2 thread, timeout adapter 10 giây; restart có thể mất thư đang đợi, gửi lại là cách phục hồi. Không có outbox bền vững trong vé này. Không gửi Gmail thật, không gọi Cloudinary/mô hình; chi phí mô hình 0 USD. Không tự động tiếp tục trước khi chủ dự án yêu cầu.
