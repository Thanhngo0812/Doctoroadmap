# W-03 — Nghiệm thu local sau cập nhật doc-1, 2026-10-20

**Kết luận của nhóm web: đạt phạm vi W-03 trên local.** Cổng toàn repo đã chạy xong và xanh; ba lượt soát nội bộ không có lỗi bắt buộc sửa. Không còn bị chặn bởi cache doc-1. Chưa ghép hoặc đẩy main; người điều phối giữ quyền soát và ghép theo quy trình.

**Bổ sung sau nghiệm thu:** chủ dự án đã xác nhận Gmail thật hoạt động. Logo email được chuyển sang URL Cloudinary qua env tại mã `1a658ca`; cổng toàn repo chạy lại **2.085 đạt, 1 Cloudinary live bỏ qua**, exit code 0. Xem [phụ lục logo và xác nhận Gmail](web-w03-logo-email-2026-10-20.md); các số liệu bên dưới ghim lượt nghiệm thu trước bản sửa này.

## Mã và dữ liệu được kiểm

- Nhánh `work/w03-email-recovery`, worktree `tmp/w03-email-recovery`.
- Commit nghiệm thu: **`e940633ae6a6bfa34088c484fcf9ea2fceeddce4`**. Mã W-03 cuối ở `7cc60fa`; nhận main `37ad48f` bằng merge. Đã kiểm không có khác biệt `src/web` hoặc `design` giữa `7cc60fa` và commit nghiệm thu.
- Main mới thay phụ thuộc của hai test quiz bằng fixture tổng hợp đã được duyệt. Không sửa mã sản phẩm, assertion hay cấu hình test để lấy kết quả xanh trong lượt này.
- Snapshot cố định `document-data/development-rebuilt-2026-10-20`, theo [manifest bàn giao](doc1-rebuild-evidence-2026-10-20/development-fixtures.json). Đã đối chiếu nguồn và đích **3.081 tệp / 195.556.758 byte**: chép 2.294 tệp thiếu, 787 tệp đã đúng hash, **0 xung đột, 0 sai SHA-256, không junction**. [Kết quả chép](w03-evidence/rebuilt-fixtures-copy.json).
- Loader thật nhập mã trong worktree, đọc doc-1 **v8**, 35 module, 223 khái niệm học được, 302 chunk và retrieval tương thích; doc-6 **v29**. [Kết quả loader](w03-evidence/acceptance-loader.json).
- Đây là dữ liệu dựng mới, không tuyên bố đã khôi phục graph v45/v57 hoặc 140 tệp lịch sử còn thiếu. Không chạm worktree t01a, không dọn snapshot/cache hoặc worktree khác.

## Kết quả chạy mới

| Cổng | Kết quả |
|---|---|
| Toàn repo Python/PostgreSQL bắt buộc | **2.075 đạt, 0 failure, 0 error, 1 skip**, 329,54 giây, process exit code **0**; [JUnit](w03-evidence/acceptance-full-python.xml), [log](w03-evidence/acceptance-python.log) |
| Backend web, là tập con của cổng trên | **223 đạt, 1 skip**; không cộng thêm vào tổng |
| React | **62 đạt**, không bỏ qua, exit code **0**; [JUnit](w03-evidence/acceptance-react.xml), [log](w03-evidence/acceptance-react.log) |
| TypeScript và Vite | **Đạt**, exit code **0**, JS gzip 96,57 kB; [log](w03-evidence/acceptance-build.log) |
| Trình duyệt sau bản sửa header cuối | **18 cấu hình màn, 4 trạng thái link terminal, 8 nhóm kiểm luồng**, 0 page error, 0 tràn ngang, 0 lỗi axe; [audit](w03-evidence/browser-audit.json), [log](w03-evidence/acceptance-browser.log), [video](w03-evidence/w03-auth-flow.webm) |
| Runtime kiểm luồng | HTTP/AuthStore/Argon2/PostgreSQL thật, Mailer và clock giả; head **w03_0004**, token chỉ giữ hash 32 byte; DB UUID riêng đã dọn đúng DB đó; [runtime](w03-evidence/isolated-runtime.json) |
| Taste inspector | **0 FAIL, 1 WARN**, exit code 0; [JSON](w03-evidence/taste-inspect/report.json). WARN là khoảng trống desktop cân hai bên form, đã giải thích trong [critique](w03-evidence/ui-critique.md) |
| Soát nội bộ | Backend, frontend, Mailer/HTTP đều approve, không finding bắt buộc sửa; [phạm vi và giới hạn](w03-evidence/independent-review.md) |

Số liệu tổng hợp trực tiếp từ XML/audit: [acceptance-summary.json](w03-evidence/acceptance-summary.json). Một test bỏ qua là `test_cloudinary_satisfies_shared_media_contract_when_explicitly_enabled`; chưa bật cờ live, không phải test W-03 bị bỏ. Cổng Python có 8 cảnh báo deprecation từ thư viện; không tắt hoặc sửa assertion để giấu cảnh báo.

## Đối chiếu vé

Toàn bộ tiêu chí chạy lại trong cổng mới, gồm:

- Đăng ký gửi đúng một thư xác minh; xác minh cập nhật tài khoản, token dùng lại bị từ chối.
- Xác minh quá 24 giờ hoặc email hiện tại đã đổi bị từ chối; gửi lại lần thứ tư trong giờ bị giới hạn.
- Quên mật khẩu trả cùng phản hồi với email có/không có tài khoản; email không tồn tại không nhận thư.
- Reset quá 60 phút hoặc dùng lại bị từ chối; reset thành công thu hồi mọi phiên cũ và token reset còn lại.
- PostgreSQL chỉ lưu SHA-256; migration một tuyến `w02_0003 → w03_0004`.
- Có ảnh dải nhắc/ba trang và mẫu thư HTML; UI có trạng thái đang xử lý, thành công, hết hạn, đã dùng, thiếu mã và lỗi trường. Header xác minh/reset giữ logo và đổi sáng/tối, đã bỏ liên kết Đăng nhập/Tài khoản theo yêu cầu.

Các tên assertion và bằng chứng RED/GREEN, phép phá guard token/SMTP/cookie/race được giữ trong [báo cáo triển khai](web-w03-ket-qua-local-2026-10-20.md). Không coi lỗi thiếu fixture của lượt cũ là RED nghiệp vụ. Lượt mới không thay mã W-03 nên không tạo lại các phép phá đã lưu; đã chạy lại toàn bộ test và kiểm luồng trên mã đã ghim.

## Lệnh đã chạy

Từ gốc worktree, dùng Python chung và runner để không nhập nhầm mã main:

```text
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 tmp/w03_copy_rebuilt_fixtures.py
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/cong-w03-rebuilt-final --junitxml=report/w03-evidence/acceptance-full-python.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1 --reporter=default --reporter=junit --outputFile=report/w03-evidence/acceptance-react.xml
npm.cmd --prefix src/web/frontend run build
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 scripts/w03_browser_runtime.py
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 report/doc1-rebuild-evidence-2026-10-20/verify_copy.py.txt
```

Vitest giải quyết outputFile theo frontend root nên XML sinh vào `src/web/frontend/report/...`; đã chuyển đúng tệp đó về thư mục bằng chứng rồi bỏ các thư mục rỗng vừa tạo, không chạy lại hay đổi kết quả. Chạy Python qua `cmd.exe` và redirect native log, giữ mã thoát thật; không diễn giải cảnh báo stderr của PowerShell thành test fail. Khi tái kiểm, chọn basetemp mới.

## Giới hạn và bàn giao

- Theo vé, kiểm tự động dùng **Mailer giả**, không tự gửi Gmail thật. Local có adapter SMTP dùng cấu hình đã cấp; chưa chứng minh thư đã tới hộp thư Gmail bằng lượt này. Mẫu thư đã kiểm Chromium, chưa nghiệm thu từng ứng dụng đọc thư Gmail/Outlook.
- Queue SMTP có giới hạn nhưng ở bộ nhớ; khởi động lại có thể mất thư đang đợi. Chưa chứng minh không thể phân biệt tài khoản bằng đo thời gian phản hồi. Hai giới hạn được ghi nhận, không đổi phạm vi vé.
- Chi phí mô hình của lượt nghiệm thu này **0 USD**, không dựng lại tài liệu hoặc gọi mô hình. Chi phí đợt dựng doc-1 thuộc báo cáo khôi phục, không gộp vào số 0 này.
- Không làm W-06; không đóng W-24. Nhánh vẫn mang các commit thiết kế/W-02 cũ đã ghi trong báo cáo triển khai; điều phối cần phán xét phạm vi đó trước khi ghép cả nhánh. Không tự sửa vé, bảng kế hoạch hoặc handoff.
- Báo cáo trực tiếp chủ dự án; không gửi sang session điều phối khác. Bước tiếp theo: điều phối soát commit nghiệm thu và xử lý ghép main theo quy trình.
