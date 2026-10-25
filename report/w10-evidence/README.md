# Bằng chứng W-10

Mã sản phẩm/harness kiểm cuối: 4d2f652f5a9564f54587ebe08051c525200b888e. Main nền: b3c4426666dd868040ea0bc52e6485f5af6e1ac4. Chỉ commit local, chờ điều phối soát.

- gate-python-delivery/, gate-react-delivery/, gate-build-delivery/: command, native exit và source SHA-256; JUnit ở gate-python-delivery.xml/gate-react-delivery.xml.
- browser-delivery/: HTTP/PG/core thật, model/Mailer/MediaStore giả. 12 cấu hình, ảnh PNG, video WebM, audit.json, runtime.json và taste-inspect/. Nội dung bài/quiz là giả minh hoạ; không gọi nhà cung cấp thật.
- browser-delivery-run/: lệnh/native/source SHA. delivery-build-manifest.json ghim bộ frontend và bundle trước browser.
- mutations-final2/: 12 phép phá guard, native1/không setup error, phục hồi byte chính xác. delivery-mutation-source-proof.json nối nguồn cdcd836 đã phá với bản bàn giao: từng tệp sản phẩm giống SHA, không gán mutant cũ đã chạy trên HEAD mới.
- history-browsers/: giữ runtime, audit, log/native lỗi cũ. Ảnh/video dở vẫn ở thư mục local browser-dev*/browser-final*/browser-smoke*, được bỏ theo dõi Git riêng; không trộn chúng với bộ ảnh đạt.
- postgresql-gates/: bản chép JSON độc lập của cổng W-15/W-25 chạy kèm, có SHA nguồn/đích; không dùng làm phát biểu nghiệm thu lại toàn SA.
- fixture-copy.json và candidate-copy.json: bằng chứng chép allowlist/SHA; không link, không cache CLI live/learner store. basetemp và ảnh giả của unit test ở tmp/, không Git.
- dependency-audit.json: npm audit production native0, 0 lỗ hổng; chỉ thêm remark-gfm4.0.1 để render bảng Markdown.
- delivery-console-classification.json: 121 console event được giữ, không tuyên bố console sạch: 3x401 chủ ý trước đăng nhập, 1x404 sau thu hồi, 1 lỗi mạng được tiêm khi nộp, 58 CSP đọc font và 58 CSP inline style trong lượt Axe; không có sự kiện chưa phân loại hoặc pageerror. Không nới CSP để làm sạch log.

Chạy từ gốc worktree, chỉ một cổng PostgreSQL toàn repo/lúc:

~~~powershell
$wfPython = 'C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe'
& $wfPython scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/cong-w10-new-unique --junitxml=tmp/cong-w10-new-unique.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1
npm.cmd --prefix src/web/frontend run build
$env:W10_EVIDENCE_RUN = 'browser-new-unique'
& $wfPython scripts/w10_web_runtime.py
~~~

Browser harness kiểm DB test trước khi tạo UUID riêng, chặn provider thật, luôn đóng server và bỏ đúng DB UUID của lượt kiểm. Dùng Chrome đầy đủ quyền trên máy này nếu custom CDP của taste-inspector gặp Page.enable timeout. Hướng dẫn mở dịch vụ phát triển ở src/web/README.md.

Raw log/JUnit được giữ nguyên byte trong raw-text-2026-10-26.zip; xem raw-text-manifest.json và normalization-receipts.json. Tệp log/XML ngoài ZIP là bản hiển thị đã bỏ khoảng trắng cuối dòng cho Git. Bản bàn giao: ../w10-quiz-tai-lieu-thu-vien-2026-10-26.md.
