# WayFinder — chạy backend và frontend

## Mở bản W-16 React — mức dùng

Worktree: C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w16-usage-react, nhánh work/w16-usage-react. Bản này kế thừa W-10 và backend usage-1 đã nghiệm thu; không dùng service đang chạy từ một worktree cũ để kiểm API W-16.

**PowerShell 1 — PostgreSQL và backend:**

~~~powershell
cd C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w16-usage-react
$wfPython = (Resolve-Path ../../.venv/Scripts/python.exe).Path
$wfEnv = (Resolve-Path ../../src/web/.env).Path
$env:PYTHONPATH = "$($PWD.Path)\src\web\backend;$($PWD.Path)\src"
$env:WAYFINDER_FRONTEND_DIST = "$($PWD.Path)\src\web\frontend\dist"
$env:WAYFINDER_ARTIFACT_ROOT = "$($PWD.Path)\artifacts"
$env:WAYFINDER_ALLOWED_ORIGINS = '["http://127.0.0.1:8000","http://127.0.0.1:5173"]'
$env:WAYFINDER_PUBLIC_BASE_URL = 'http://127.0.0.1:5173'
$env:WAYFINDER_MAILER = 'console'
docker compose -f src/web/docker-compose.yml --env-file $wfEnv up -d --wait db
& $wfPython -m wayfinder.cli --env-file $wfEnv db upgrade
& $wfPython -m wayfinder.cli --env-file $wfEnv serve --host 127.0.0.1 --port 8000
~~~

**PowerShell 2 — frontend:**

~~~powershell
cd C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w16-usage-react
npm.cmd --prefix src/web/frontend ci --no-audit --no-fund
npm.cmd --prefix src/web/frontend run dev -- --port 5173 --strictPort
~~~

Mở **http://127.0.0.1:5173/muc-dung**, hoặc menu tài khoản → **Mức dùng**. Trang hiển thị tỷ lệ hôm nay và giờ đặt lại theo Việt Nam; quota tháng tắt sẽ ghi **Không giới hạn**. Dải hết hạn xuất hiện ở chat/thư viện; nội dung đã có và ngân hàng quiz vẫn do server kiểm, không cần worker để xem mức dùng. Không seed hoặc bật quota demo để thử trên DB phát triển.

Dừng từng terminal bằng Ctrl+C. Muốn xem bản build ở cổng 8000: chạy npm.cmd --prefix src/web/frontend run build trong đúng worktree, đổi WAYFINDER_PUBLIC_BASE_URL về http://127.0.0.1:8000 rồi mở lại backend. Harness tự động trong scripts/w16_web_runtime.py dùng DB UUID riêng, fake model/Mailer/media và ledger tổng hợp; không dùng nó làm dữ liệu thật.



## Mở bản W-10 — quiz, tài liệu và thư viện

Worktree: C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w10-quiz-documents, nhánh work/w10-quiz-documents. Bản này kế thừa W-09 đã nghiệm thu; không dùng service đang chạy từ một worktree cũ để kiểm API W-10.

**PowerShell 1 — PostgreSQL và backend:**

~~~powershell
cd C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w10-quiz-documents
$wfPython = (Resolve-Path ../../.venv/Scripts/python.exe).Path
$wfEnv = (Resolve-Path ../../src/web/.env).Path
$env:PYTHONPATH = "$($PWD.Path)\src\web\backend;$($PWD.Path)\src"
$env:WAYFINDER_FRONTEND_DIST = "$($PWD.Path)\src\web\frontend\dist"
$env:WAYFINDER_ARTIFACT_ROOT = "$($PWD.Path)\artifacts"
$env:WAYFINDER_ALLOWED_ORIGINS = '["http://127.0.0.1:8000","http://127.0.0.1:5173"]'
$env:WAYFINDER_PUBLIC_BASE_URL = 'http://127.0.0.1:5173'
$env:WAYFINDER_MAILER = 'console'
docker compose -f src/web/docker-compose.yml --env-file $wfEnv up -d --wait db
& $wfPython -m wayfinder.cli --env-file $wfEnv db upgrade
& $wfPython -m wayfinder.cli --env-file $wfEnv serve --host 127.0.0.1 --port 8000
~~~

**PowerShell 2 — frontend:**

~~~powershell
cd C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w10-quiz-documents
npm.cmd --prefix src/web/frontend ci --no-audit --no-fund
npm.cmd --prefix src/web/frontend run dev -- --port 5173 --strictPort
~~~

Mở http://127.0.0.1:5173/khoa-hoc. Trong một khoá sẵn sàng: **Làm quiz cả khoá** hoặc mở module → **Làm quiz**. Chọn phương án rồi **Nộp bài**; lúc làm không có khung chat. Mở lại lần làm đã nộp sẽ hiện kết quả đã lưu. **Tạo tài liệu** cho chọn 1–5 module và yêu cầu; tài liệu viết dần, sau đó mở để xem nguồn hoặc **Tải Markdown**.

Thư viện ở lộ trình mặc định là nội dung tạo tại lộ trình; chọn **Tất cả nội dung trong khoá** để xem rộng hơn. Module có **Tạo ở đây/Tạo ở nơi khác**, theo nhóm core trả; dòng **Tạo trực tiếp/Qua trợ lý** là thông tin nguồn tạo riêng. Xoá cuộc trò chuyện không xoá tài liệu hoặc quiz đã lưu.

API W-10 dùng quiz-3/document-3. POST quizzes/documents nhận JSON hoặc Accept: text/event-stream. Đề public không có đáp án. POST submit cùng lựa chọn trả kết quả cũ; lựa chọn khác sau nộp trả conflict. Tạo tài liệu vượt 5 module trả scope_too_large, yêu cầu thứ 11/giờ theo người xuyên khoá trả rate_limited trước SSE.

Service dev theo cấu hình trên có thể gọi provider thật khi người dùng bấm tạo. Bộ kiểm W-10 dùng PostgreSQL UUID riêng và model/media/mailer giả, chi phí 0 USD; không dùng DB dev để kiểm phá. Dừng service bằng Ctrl+C, giữ nguyên volume DB và worktree.



## Mở bản W-09 — trợ lý và phiên học

Worktree `C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w09-assistant`, nhánh `work/w09-assistant`. Backend dùng PostgreSQL, answer-3 và bài lecture-3 đã lưu; khung trợ lý có ở lộ trình và trang học.

**PowerShell 1 — backend:** bật Docker Desktop, rồi chạy:

```powershell
cd C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w09-assistant
$wfPython = (Resolve-Path ../../.venv/Scripts/python.exe).Path
$wfEnv = (Resolve-Path ../../src/web/.env).Path
$env:PYTHONPATH = "$($PWD.Path)\src\web\backend;$($PWD.Path)\src"
$env:WAYFINDER_FRONTEND_DIST = "$($PWD.Path)\src\web\frontend\dist"
$env:WAYFINDER_ARTIFACT_ROOT = "$($PWD.Path)\artifacts"
$env:WAYFINDER_ALLOWED_ORIGINS = '["http://127.0.0.1:8000","http://127.0.0.1:5173"]'
$env:WAYFINDER_PUBLIC_BASE_URL = 'http://127.0.0.1:5173'
$env:WAYFINDER_MAILER = 'console'
docker compose -f src/web/docker-compose.yml --env-file $wfEnv up -d --wait db
& $wfPython -m wayfinder.cli --env-file $wfEnv db upgrade
& $wfPython -m wayfinder.cli --env-file $wfEnv serve --host 127.0.0.1 --port 8000
```

**PowerShell 2 — frontend:**

```powershell
cd C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w09-assistant
npm.cmd --prefix src/web/frontend ci --no-audit --no-fund
npm.cmd --prefix src/web/frontend run dev -- --port 5173 --strictPort
```

Mở `http://127.0.0.1:5173/khoa-hoc`, chọn khoá sẵn sàng → **Hỏi trợ lý**. Phiên ở lộ trình dùng cả lộ trình; phiên ở trang học có phạm vi module, mỗi câu hỏi gửi bài đang mở. Có phiên mới, lịch sử, đổi tên, xoá có xác nhận, nguồn theo trang và xem nội dung quiz/tài liệu đã tạo. Làm bài/chấm điểm và thư viện đầy đủ thuộc W-10.

Đóng trang chỉ ngừng nhận chữ: server tiếp tục lượt đang chạy và lưu vào PostgreSQL. Mở lại phiên và chọn **Cập nhật phiên**; nếu cần thử lại, trình duyệt giữ mã lượt cũ. Đây chưa phải hàng đợi bền: nếu tiến trình server dừng giữa lượt, có thể phải thử lại. Dừng hai terminal bằng `Ctrl+C`; không xoá volume DB.

Cấu hình dev bên trên có thể gọi nhà cung cấp thật. **Để kiểm W-09 ở 0 USD**, dùng bộ riêng dưới đây: script chặn nhà cung cấp thật, tạo DB UUID tạm trên `db-test`, dùng use case thật và mô hình/Mailer/MediaStore giả. Không dùng DB dev để kiểm phá.

```powershell
cd C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w09-assistant
$wfPython = (Resolve-Path ../../.venv/Scripts/python.exe).Path
$wfEnv = (Resolve-Path ../../src/web/.env).Path
docker compose -f src/web/docker-compose.yml --env-file $wfEnv up -d --wait db-test
& $wfPython -X utf8 src/web/backend/tests/copy_w06_fixtures.py
npm.cmd --prefix src/web/frontend run build
$env:W09_EVIDENCE_RUN = 'browser-local-1' # Mỗi lần chọn tên mới, giữ bằng chứng cũ.
& $wfPython -X utf8 scripts/w09_web_runtime.py
```

Runtime kiểm ở `http://127.0.0.1:8019`; script tự mở/đóng server và chỉ xoá DB UUID do chính lượt kiểm tạo. Ảnh/video, JSON HTTP, SQL và audit nằm trong `report/w09-evidence/<tên lượt>/`. Tệp giả/basetemp nằm dưới `tmp/`, không trộn với ảnh UI.

## Mở bản W-08 — trang học lecture-3

Worktree: `C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w08-lecture`, nhánh `work/w08-lecture`. Đã nhận main có SA-64 tại merge `1d91b0b`; W-08 dùng `body_md`, LaTeX, nguồn và tự kiểm tra của lecture-3. Giữ worktree W-11 để đối chiếu.

**PowerShell 1 — PostgreSQL và backend:** bật Docker Desktop, rồi chạy:

```powershell
cd C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w08-lecture
$wfPython = (Resolve-Path ../../.venv/Scripts/python.exe).Path
$wfEnv = (Resolve-Path ../../src/web/.env).Path
$env:PYTHONPATH = "$($PWD.Path)\src\web\backend;$($PWD.Path)\src"
$env:WAYFINDER_FRONTEND_DIST = "$($PWD.Path)\src\web\frontend\dist"
$env:WAYFINDER_ARTIFACT_ROOT = "$($PWD.Path)\artifacts"
$env:WAYFINDER_ALLOWED_ORIGINS = '["http://127.0.0.1:8000","http://127.0.0.1:5173"]'
$env:WAYFINDER_PUBLIC_BASE_URL = 'http://127.0.0.1:5173'
$env:WAYFINDER_MAILER = 'console'
docker compose -f src/web/docker-compose.yml --env-file $wfEnv up -d --wait db
& $wfPython -m wayfinder.cli --env-file $wfEnv db upgrade
& $wfPython -m wayfinder.cli --env-file $wfEnv serve --host 127.0.0.1 --port 8000
```

**PowerShell 2 — frontend:**

```powershell
cd C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w08-lecture
npm.cmd --prefix src/web/frontend ci --no-audit --no-fund
npm.cmd --prefix src/web/frontend run dev -- --port 5173 --strictPort
```

Mở `http://127.0.0.1:5173/khoa-hoc`, vào khoá đã sẵn sàng → **Mở module** → chọn bài học. Bài hiện dần; có tiên quyết gập, nguồn đúng trang, đáp án tự kiểm tra gập và dấu đã học riêng. Các nút Hỏi trợ lý sẽ nối ở W-09. Không cần worker dựng tài liệu để đọc khoá đã sẵn sàng. Dừng từng terminal bằng `Ctrl+C`; không xoá volume DB.

Hai service trên dùng cấu hình dev của bạn: mở bài chưa có cache có thể gọi model đã cấu hình; xem ảnh/tệp dùng MediaStore. **Đợt kiểm W-08 dùng script riêng bên dưới với mô hình/Mailer/MediaStore giả và PostgreSQL UUID tạm, chi ngoài 0 USD**, không dùng tài khoản/DB dev để phá thử.

```powershell
cd C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w08-lecture
$wfPython = (Resolve-Path ../../.venv/Scripts/python.exe).Path
$wfEnv = (Resolve-Path ../../src/web/.env).Path
docker compose -f src/web/docker-compose.yml --env-file $wfEnv up -d --wait db-test
& $wfPython -X utf8 src/web/backend/tests/copy_w06_fixtures.py
npm.cmd --prefix src/web/frontend run build
$env:W08_EVIDENCE_RUN = 'browser-local-1' # Chọn tên mới mỗi lượt, không ghi đè bằng chứng.
& $wfPython -X utf8 scripts/w08_web_runtime.py
```

Harness tự mở/đóng API ở8018, tạo/gỡ DB UUID riêng và lưu JSON/ảnh/video trong `report/w08-evidence/<tên-lượt>/`. PDF chỉ chép từ snapshot theo manifest/SHA-256; không lấy kho CLI/live. [Báo cáo W-08](../../report/w08-trang-hoc-lecture3-2026-10-23.md) phân biệt kiểm phát triển và cổng cuối. Các mục W-11/W-14/W-07 dưới đây giữ hướng dẫn mốc cũ.

## Mở bản W-11 — chia sẻ bằng link và thành viên

Mã W-11 ở `C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w11-share-links`, nhánh `work/w11-share-links`, đã nhận main `865974a`. Bản vá ngày 2026-10-23 giữ link mời khi đổi giữa đăng nhập/đăng ký qua header, footer và view transition. Migration `w11_0007` nối `w14_0006`. Cổng tự động dùng PostgreSQL UUID riêng và dịch vụ giả; không chạy trên DB phát triển của bạn. Bản này chờ điều phối nghiệm thu W-11, không tự ghép main.

**PowerShell 1 — PostgreSQL và backend:** dùng `.env` dev riêng đã cấu hình, bật Docker Desktop rồi chạy:

```powershell
cd C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w11-share-links
$wfPython = (Resolve-Path ../../.venv/Scripts/python.exe).Path
$wfEnv = (Resolve-Path ../../src/web/.env).Path
$env:PYTHONPATH = "$($PWD.Path)\src\web\backend;$($PWD.Path)\src"
$env:WAYFINDER_FRONTEND_DIST = "$($PWD.Path)\src\web\frontend\dist"
$env:WAYFINDER_ARTIFACT_ROOT = "$($PWD.Path)\artifacts"
$env:WAYFINDER_ALLOWED_ORIGINS = '["http://127.0.0.1:8000","http://127.0.0.1:5173"]'
$env:WAYFINDER_PUBLIC_BASE_URL = 'http://127.0.0.1:5173'
$env:WAYFINDER_MAILER = 'console'
docker compose -f src/web/docker-compose.yml --env-file $wfEnv up -d --wait db
& $wfPython -m wayfinder.cli --env-file $wfEnv db upgrade
& $wfPython -m wayfinder.cli --env-file $wfEnv serve --host 127.0.0.1 --port 8000
```

**PowerShell 2 — frontend:**

```powershell
cd C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w11-share-links
npm.cmd --prefix src/web/frontend ci
npm.cmd --prefix src/web/frontend run dev -- --port 5173 --strictPort
```

Mở `http://127.0.0.1:5173/khoa-hoc`. Chủ khoá vào lộ trình → **Chia sẻ**, đặt hạn/số lượt rồi tạo và sao chép link một lần. Link dùng đúng `WAYFINDER_PUBLIC_BASE_URL`; khách đăng nhập/đăng ký xong quay lại link đó. Trang **Thành viên** có nút xoá hoặc rời khoá theo quyền. Không cần worker cho thao tác chia sẻ; worker giả bên dưới chỉ dành cho dựng tài liệu W-14. Dừng từng terminal bằng `Ctrl+C`, giữ volume DB.

Để dùng bản build ở8000: chạy `npm.cmd --prefix src/web/frontend run build`, đặt `WAYFINDER_PUBLIC_BASE_URL=http://127.0.0.1:8000` rồi mở lại backend. Không trộn `localhost` và `127.0.0.1`. Xem [báo cáo bản vá W-11](../../report/w11-chia-se-link-thanh-vien-2026-10-23.md) và [bằng chứng đợt trước](../../report/w11-chia-se-link-thanh-vien-2026-10-22.md). Các phần W-14/W-07 dưới đây giữ hướng dẫn của mốc trước để đối chiếu.

## W-14 React — vị trí và giới hạn

Nhánh `work/w14-react`, worktree `C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w14-react`, đã nhận main `8b85d19` chứa backend W-14/W-25 được duyệt tại `a572459`, cùng SA-52/SA-53. Các bước dưới đây dành cho DB dev riêng đã cấu hình. Bản này nhận PDF/DOCX nhưng dùng **bộ dựng giả**: kết quả học lấy từ snapshot doc-1 đã kiểm hash, không phải nội dung tài liệu vừa tải. Bản dựng thật thuộc W-15. W-11 vẫn ở worktree riêng, không nằm trong W-14.

### PowerShell 1 — mở PostgreSQL và backend

Bật Docker Desktop, rồi chạy từ đúng worktree. Dùng cấu hình PostgreSQL dev riêng trong `.env` hiện có. Đợt kiểm tự động dùng DB UUID riêng; các lệnh dev dưới đây không thuộc cổng kiểm tự động.

```powershell
cd C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w14-react
$wfPython = (Resolve-Path ../../.venv/Scripts/python.exe).Path
$wfEnv = (Resolve-Path ../../src/web/.env).Path
$env:PYTHONPATH = "$($PWD.Path)\src\web\backend;$($PWD.Path)\src"
$env:WAYFINDER_FRONTEND_DIST = "$($PWD.Path)\src\web\frontend\dist"
$env:WAYFINDER_ARTIFACT_ROOT = "$($PWD.Path)\artifacts"
$env:WAYFINDER_ALLOWED_ORIGINS = '["http://127.0.0.1:8000","http://127.0.0.1:5173"]'
$env:WAYFINDER_PUBLIC_BASE_URL = 'http://127.0.0.1:5173'
$env:WAYFINDER_MAILER = 'console'
docker compose -f src/web/docker-compose.yml --env-file $wfEnv up -d --wait db
& $wfPython -m wayfinder.cli --env-file $wfEnv db upgrade
& $wfPython -m wayfinder.cli --env-file $wfEnv serve --host 127.0.0.1 --port 8000
```

Backend ở `http://127.0.0.1:8000`; health ở `/api/v1/health`. CLI giữ cấu hình Vertex/ADC hiện có khi mở backend, không tự gọi mô hình. Media dựng W-14 dùng kho giả local; `MAILER=console` chỉ áp dụng terminal demo này để không gửi thư SMTP. Đợt kiểm tự động dùng DB UUID và provider giả hoàn toàn, không chạy những lệnh dev trên DB của chủ dự án.

### PowerShell 2 — mở frontend

```powershell
cd C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w14-react
npm.cmd --prefix src/web/frontend ci
npm.cmd --prefix src/web/frontend run dev -- --port 5173 --strictPort
```

Mở `http://127.0.0.1:5173/tai-len`. Chọn tệp và xác nhận quyền dùng; sau khi kiểm tệp, sửa tên khoá rồi bấm **Dựng lộ trình**. Trang tiến trình giữ mã bản dựng và khoá học trong URL; có thể tải lại hoặc mở lại từ **Khoá học của tôi**. Không đổi xen kẽ `localhost`/`127.0.0.1` vì phiên/CSRF.

### PowerShell 3 — worker giả

Snapshot đã có trong worktree của lần bàn giao. Nếu chưa có, dùng helper copy theo manifest dưới đây; helper kiểm SHA-256 và dừng nếu đích khác hash. Không liên kết thư mục snapshot/artifact.

```powershell
cd C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w14-react
$wfPython = (Resolve-Path ../../.venv/Scripts/python.exe).Path
$wfEnv = (Resolve-Path ../../src/web/.env).Path
$env:PYTHONPATH = "$($PWD.Path)\src\web\backend;$($PWD.Path)\src"
$env:WAYFINDER_ARTIFACT_ROOT = "$($PWD.Path)\artifacts"
& $wfPython -X utf8 src/web/backend/tests/copy_w06_fixtures.py
& $wfPython -m wayfinder.cli --env-file $wfEnv worker --fake-source doc-1 --fixture-root . --manifest report/doc1-rebuild-evidence-2026-10-20/development-fixtures.json --manifest-sha256 5fc819f723f7263fe3d443ec780009a75aae66f2c35db8fe0bc3e3c50464eb84
```

Worker chỉ nhận việc đã xác nhận, kiểm hàng đợi mỗi 3 giây khi rảnh. Nếu chưa mở worker thì bản dựng giữ `queued`. Huỷ/thử lại theo khả năng API cho phép; không hứa hoàn lượt. Để chạy một việc rồi thoát, thêm `--once`. Worker dùng mailer/media giả, không upload Cloudinary hoặc gọi runner thật.

### Bản build và cách dừng

Trong worktree chạy `npm.cmd --prefix src/web/frontend run build`, dừng backend cũ bằng `Ctrl+C`, đổi `WAYFINDER_PUBLIC_BASE_URL` về `http://127.0.0.1:8000` rồi mở lại backend để xem React build ở8000. Giữ worker chạy nếu muốn xử lý việc đã xác nhận.

Dừng từng terminal bằng `Ctrl+C`; không cần xoá volume. Có thể dừng DB bằng `docker compose -f src/web/docker-compose.yml --env-file $wfEnv stop db`. Lần sau mở lại đúng ba terminal, không cần `npm ci` nếu dependency chưa đổi. Nếu cổng8000/5173 bận, dừng phiên cũ trước. [Báo cáo tích hợp W-14](../../report/w14-react-tich-hop-2026-10-22.md) ghi commit, bằng chứng và phần còn chờ điều phối.

## Mở nhanh bản W-07 trên máy hiện tại

Bản W-07 nằm ở nhánh `work/w07-roadmap-progress`, thư mục `C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w07-roadmap-progress`. Chạy từ thư mục này để mở đúng bản mới. Bật **Docker Desktop** và chờ engine sẵn sàng trước.

### Cửa sổ PowerShell 1 — PostgreSQL và backend

```powershell
cd C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w07-roadmap-progress

# Dùng Python và cấu hình đã có ở repo gốc; import mã của W-07.
$wfPython = (Resolve-Path ../../.venv/Scripts/python.exe).Path
$wfEnv = (Resolve-Path ../../src/web/.env).Path
$env:PYTHONPATH = "$($PWD.Path)\src\web\backend;$($PWD.Path)\src"
$env:WAYFINDER_FRONTEND_DIST = "$($PWD.Path)\src\web\frontend\dist"
$env:WAYFINDER_ARTIFACT_ROOT = "$($PWD.Path)\artifacts"

docker compose -f src/web/docker-compose.yml --env-file $wfEnv up -d --wait db
& $wfPython -m wayfinder.cli --env-file $wfEnv db upgrade

# Cho phép cả trang build ở 8000 và Vite ở 5173 dùng phiên/CSRF.
$env:WAYFINDER_ALLOWED_ORIGINS = '["http://127.0.0.1:8000","http://127.0.0.1:5173"]'
$env:WAYFINDER_PUBLIC_BASE_URL = 'http://127.0.0.1:5173'
& $wfPython -m wayfinder.cli --env-file $wfEnv serve --host 127.0.0.1 --port 8000
```

Giữ cửa sổ này mở. Backend ở **http://127.0.0.1:8000**; health ở **http://127.0.0.1:8000/api/v1/health**. W-07 tái dùng bảng Pha B, không thêm migration; head vẫn là `w06_0005`.

`WAYFINDER_ARTIFACT_ROOT` ở trên dùng bản sao snapshot phát triển của worktree đã đối chiếu SHA-256. Nếu mở worktree mới chưa có dữ liệu, làm theo [báo cáo W-07](../../report/w07-lo-trinh-tien-do-2026-10-21.md) để chép theo manifest; không trỏ vào cache người học CLI. Cấu hình dữ liệu dùng thật vẫn đặt ngoài repo như phần chuẩn bị bên dưới.

### Cửa sổ PowerShell 2 — frontend React

```powershell
cd C:\Users\ngoco\Desktop\Doctoroadmap\tmp\w07-roadmap-progress

# Chỉ cần khi chưa cài dependency hoặc package-lock.json thay đổi.
npm.cmd --prefix src/web/frontend ci

npm.cmd --prefix src/web/frontend run dev -- --port 5173 --strictPort
```

Mở **http://127.0.0.1:5173**; đăng nhập để vào **http://127.0.0.1:5173/khoa-hoc**. React tự cập nhật khi sửa mã. `/api` được Vite chuyển tới backend cổng8000; dùng thống nhất `127.0.0.1`, không đổi xen kẽ sang `localhost`. `--strictPort` giúp báo rõ cổng bận, không tự đổi sang cổng ngoài cấu hình CSRF.

Liên kết xác minh/reset trong email dùng `WAYFINDER_PUBLIC_BASE_URL`, nên chế độ trên đặt về5173. Gmail/Cloudinary giữ cấu hình hiện có trong `.env`; việc mở service không tự seed mẫu, gửi thư hay upload media. Thư chỉ được gửi khi có thao tác tài khoản tương ứng và Mailer được cấu hình SMTP.

### Chạy bản build để xem demo ở một địa chỉ

Nếu chỉ muốn xem sản phẩm, không cần Vite. Dừng hai tiến trình bằng `Ctrl+C`, rồi trong cửa sổ backend đã thiết lập các biến ở trên:

```powershell
npm.cmd --prefix src/web/frontend run build
$env:WAYFINDER_PUBLIC_BASE_URL = 'http://127.0.0.1:8000'
& $wfPython -m wayfinder.cli --env-file $wfEnv serve --host 127.0.0.1 --port 8000
```

Mở **http://127.0.0.1:8000**. FastAPI phục vụ cả API và React đã build. Sau mỗi lần đổi giao diện cần build lại rồi tải lại trang. W-07 không cần worker; upload tài liệu thật thuộc W-14.

### Dừng và mở lại

- Nhấn `Ctrl+C` ở từng cửa sổ backend/frontend để dừng. Lần sau chạy lại phần thiết lập biến của cửa sổ backend và các lệnh mở service; không cần `npm ci` mỗi lần.
- Có thể để PostgreSQL chạy. Nếu muốn dừng: `docker compose -f src/web/docker-compose.yml --env-file $wfEnv stop db` trong cửa sổ backend. Dữ liệu vẫn giữ trong volume. Không dùng `down -v` khi muốn giữ tài khoản/khoá học.
- Chỉ mở một backend cổng8000. Nếu báo cổng bận, dừng tiến trình cũ trong terminal đã mở nó. Không chạy đồng thời backend W-03 và W-07 cùng cổng.

### Khi không mở được

| Hiện tượng | Cách xử lý |
|---|---|
| Docker báo không kết nối engine | Bật Docker Desktop, đợi sẵn sàng rồi chạy lại lệnh `up` |
| API lỗi503 hoặc không kết nối PostgreSQL | Xem `docker compose -f src/web/docker-compose.yml --env-file $wfEnv ps db`; kiểm `.env` và chạy `db upgrade` nếu chưa chạy |
| Backend báo cấu hình Vertex/ADC không hợp lệ | Kiểm các biến `DOC2ROADMAP_*` và ADC đã cấu hình trên máy như phần chuẩn bị bên dưới |
| Đăng nhập/join báo CSRF | Mở đúng `127.0.0.1:5173`, kiểm hai origin trong cửa sổ backend rồi khởi động lại backend và tải lại trang |
| Mở8000 nhưng giao diện cũ/chưa có | Chạy `npm.cmd --prefix src/web/frontend run build` trong đúng worktree; kiểm `WAYFINDER_FRONTEND_DIST` |
| Khoá học của tôi rỗng | Đây là danh sách từ DB đang dùng; bộ kiểm tự động dùng DB tạm và đã xoá sau kiểm, không seed vào DB của bạn |

## Quy ước hướng dẫn chạy cho các vé tiếp theo

Mỗi lần bàn giao web phải cập nhật README này: worktree/nhánh, cấu hình cần thêm, lệnh mở PostgreSQL/backend/frontend/worker nếu có, URL truy cập, lệnh dừng và giới hạn chưa triển khai. Các phần bên dưới là tham khảo cài mới và cấu hình chung.

Chạy các lệnh dưới đây từ gốc repo với Python 3.12, Node.js 24.11.1 / npm 11.6.2 (phiên bản đã kiểm) và Docker Desktop (Linux engine/WSL2).

## Phạm vi đã chốt

W-01 cung cấp nền FastAPI/React/PostgreSQL, MediaStore, CLI và bộ ứng dụng thử. Trang giới thiệu có hành trình tương tác dùng dữ liệu mẫu, ghi rõ là minh hoạ. Upload PDF mới và xử lý nền thật được nối theo các vé sau. Worker W-01 chưa nhận việc; W-14 triển khai hàng đợi.

## Chuẩn bị môi trường

```powershell
.venv/Scripts/python.exe -m pip install -e '.[web,dev]'
```

Nếu `.venv` chưa có pip: chạy `.venv/Scripts/python.exe -m ensurepip --upgrade` trước.

Tạo `src/web/.env` từ `.env.example` nếu chưa có tệp; điền mật khẩu PostgreSQL riêng cho dev và test, rồi sửa hai URL tương ứng. Giữ tệp này trên máy. Các trần có giá trị `null` được hiểu là không giới hạn. `artifact_root` cho dữ liệu dùng thật phải trỏ ra ngoài repo.

API dùng cấu hình lõi: `DOC2ROADMAP_LLM_TRANSPORT=vertex`, `DOC2ROADMAP_VERTEX_PROJECT`, `DOC2ROADMAP_VERTEX_LOCATION=global` và ADC hợp lệ trên máy chủ. Không cần Gemini API key. `web serve` kiểm cấu hình/xác thực trước khi dựng các adapter mô hình, không tự đổi transport; khởi động không sinh nội dung hay gọi mô hình tính phí.

```powershell
docker compose -f src/web/docker-compose.yml --env-file src/web/.env up -d --wait db db-test
.venv/Scripts/web.exe --env-file src/web/.env db upgrade
```

Dev dùng volume Docker có tên, test dùng `tmpfs`; không gắn dữ liệu PostgreSQL vào ổ C. Hai cổng chỉ lắng nghe loopback: 5432/5433. Bản di trú W-01 chỉ tạo bảng phiên bản Alembic. Chuỗi hiện tại là `w01_0001 → w05_0002 → w02_0003 → w03_0004 → w06_0005`, tạo kho Pha B, tài khoản/phiên/giới hạn thử/nhật ký, token email và course/membership W-06.

## Chạy ứng dụng

```powershell
.venv/Scripts/web.exe --env-file src/web/.env serve
```

Mở `http://127.0.0.1:8000`. Để FastAPI phục vụ React, dựng giao diện trước:

```powershell
npm.cmd --prefix src/web/frontend ci
npm.cmd --prefix src/web/frontend run build
```

Khi phát triển giao diện, chạy `npm.cmd --prefix src/web/frontend run dev` trong một cửa sổ lệnh khác rồi mở địa chỉ Vite in ra. Proxy `/api` chuyển về FastAPI cổng 8000; phía trình duyệt luôn gọi cùng nguồn. Bí mật không nằm trong `VITE_*`.

```powershell
.venv/Scripts/web.exe worker
.venv/Scripts/web.exe openapi export
```

OpenAPI ở `src/web/openapi.json`; thay route phải xuất lại. Worker hiện in thông báo phạm vi W-14 rồi thoát, không giả nhận hay hoàn tất việc.

## Kiểm thử

```powershell
.venv/Scripts/web.exe --env-file src/web/.env check
npm.cmd --prefix src/web/frontend test
npm.cmd --prefix src/web/frontend run build
```

`web check` chạy cả test lõi và test web, cách ly cấu hình mô hình `DOC2ROADMAP_*` của máy chủ khỏi tiến trình pytest để mỗi test dùng cấu hình giả riêng. Lệnh yêu cầu PostgreSQL test đang chạy. Thiếu cấu hình hoặc tắt `db-test` thì lệnh hỏng. Pytest thường không có `WAYFINDER_TEST_DATABASE_URL` sẽ báo rõ lý do bỏ qua test PostgreSQL. Mỗi phiên test PostgreSQL tạo một database UUID riêng, chạy toàn bộ di trú rồi chỉ xoá database do phiên đó tạo.

Nếu thư mục Temp/cache cũ của Windows bị lỗi quyền, đặt tham số pytest cho phiên shell:

```powershell
$env:PYTEST_ADDOPTS='--basetemp=.tmp/w01-pytest -o cache_dir=.tmp/w01-pytest-cache'
.venv/Scripts/web.exe --env-file src/web/.env check
Remove-Item Env:PYTEST_ADDOPTS
```

Các bài kiểm thử mô hình dùng đồ giả, không gọi mạng hay phát sinh USD. Cloudinary thật được bật riêng:

```powershell
$env:WAYFINDER_RUN_CLOUDINARY_TESTS='1'
.venv/Scripts/web.exe --env-file src/web/.env check
.venv/Scripts/web.exe --env-file src/web/.env media-smoke
Remove-Item Env:WAYFINDER_RUN_CLOUDINARY_TESTS
```

Đặt `CLOUDINARY_URL` trong dotenv phía máy chủ và bật **Allow delivery of PDF and ZIP files** trong Cloudinary Settings → Security. Smoke tạo PDF nhỏ, tải lên chế độ authenticated, kiểm ảnh trang/link tải và dọn tài sản thử. Không in URL ký hay thông tin xác thực. Tài khoản Free của chủ dự án đã qua smoke/contract; giới hạn do chủ dự án cung cấp là image 10 MB và raw 10 MB. Giới hạn upload mặc định là 10 MB. Kết quả và thời điểm kiểm ở báo cáo W-01.

## Gmail

Điền `WAYFINDER_SMTP_USERNAME`, `WAYFINDER_SMTP_PASSWORD` (Gmail App Password), `WAYFINDER_SMTP_FROM` trong dotenv phía máy chủ; dùng TLS qua `smtp.gmail.com:587` với `WAYFINDER_SMTP_STARTTLS=true`. Kết nối TLS và xác thực trên máy đã được kiểm thành công, không gửi thư. W-03 đã nối gửi thư xác minh, đặt lại mật khẩu và báo tài khoản đã tồn tại. Đặt `WAYFINDER_MAILER=smtp` để dùng Gmail, `WAYFINDER_PUBLIC_BASE_URL` là nguồn của ứng dụng (local mặc định `http://127.0.0.1:8000`; production cần HTTPS). Adapter SMTP gửi nền qua queue giới hạn, không giữ giao dịch DB trong lúc gửi. Test tự động dùng Mailer giả, không gửi thư thật.

## Bằng chứng trình duyệt

Script nghiệm thu dùng bộ công cụ tạm, không thêm vào gói ứng dụng:

```powershell
npm.cmd install --prefix .tmp/w01-browser-tools --no-save --package-lock=false playwright@1.64.1 @axe-core/playwright
$env:PLAYWRIGHT_BROWSERS_PATH="$PWD/.tmp/w01-browsers"
.tmp/w01-browser-tools/node_modules/.bin/playwright.cmd install chromium
node scripts/w01_browser_check.cjs
```

Cần FastAPI chạy với frontend đã dựng và `db` đang tốt. Script chụp 390/768/1280 px ở sáng/tối, kiểm hành trình minh hoạ trên desktop và cả sáu chặng mobile tối, vùng bấm 44 px, axe WCAG AA, deep link, theme và giảm chuyển động. Nó cố ý gỡ CSS giảm chuyển động và thay màu nút sáng trong trang test riêng để xác nhận các guard bắt được lỗi. Cảnh báo CSP do axe chèn style/fetch stylesheet được ghi riêng trong `toolDiagnostics`; console của ứng dụng được kiểm trước và ngoài quá trình axe, giữ nguyên CSP. Ảnh, video và JSON nằm ở `report/w01-evidence/`.

Để kiểm nhánh mất kết nối, dừng riêng `db`, chạy `node scripts/w01_database_failure_check.cjs`, rồi luôn bật lại `db` bằng Compose. Script kiểm HTTP 503 và quan sát yêu cầu health mới sau khi bấm Thử lại.

Nguồn triển khai: [Hatch editable paths](https://hatch.pypa.io/latest/config/build/#dev-mode), [Alembic programmatic config](https://alembic.sqlalchemy.org/en/latest/api/config.html), [SQLAlchemy engine](https://docs.sqlalchemy.org/en/20/core/engines.html), [PostgreSQL 16.15](https://www.postgresql.org/docs/16/release-16-15.html), [Cloudinary access control](https://cloudinary.com/documentation/control_access_to_media), [Playwright video](https://playwright.dev/docs/videos).

## Tài khoản W-02

- Trang `/dang-ky`, `/dang-nhap`, `/tai-khoan` dùng API và phiên PostgreSQL thật. `/demo` vẫn là hành trình mẫu.
- Đăng ký mới tự đăng nhập; email trùng nhận cùng thông báo JSON và không thay đổi tài khoản cũ. Khác biệt cookie và `/me` vẫn cho phép suy ra email đã tồn tại: giới hạn này đã được chủ dự án chấp nhận theo W-02.
- Mật khẩu 8–128 ký tự, giữ khoảng trắng, chặn danh sách phổ biến đóng kèm. Argon2id 19 MiB / 2 vòng / parallelism 1.
- Cookie HttpOnly, SameSite=Lax, Secure khi HTTPS; chế độ prod luôn Secure kể cả khi upstream proxy là HTTP. Phiên hết sau 7 ngày không dùng hoặc 30 ngày tuyệt đối.
- Mọi thao tác thay đổi dữ liệu cần Origin hợp lệ; ngoài đăng ký/đăng nhập và ba POST công khai của W-03 (xác minh, yêu cầu/hoàn tất đặt lại mật khẩu) còn cần CSRF của phiên. Gửi lại xác minh vẫn cần phiên và CSRF. allowed_origins rỗng chỉ cho cùng nguồn trên localhost/IP loopback. Khi dùng tên miền hoặc proxy, đặt WAYFINDER_ALLOWED_ORIGINS thành mảng JSON các nguồn HTTPS chính xác; cấu hình proxy tin cậy để giữ scheme/host đúng.
- Tạo quản trị viên bằng lệnh dưới đây; mật khẩu được hỏi ẩn qua stdin, không có tham số password. Tài khoản bootstrap được coi đã xác minh email và không tự cấp phiên.

```powershell
.venv/Scripts/web.exe --env-file src/web/.env create-admin --email admin@example.vn
```

Kiểm trình duyệt sau khi dựng UI và chạy server:

```powershell
$env:W02_BASE_URL='http://127.0.0.1:8000'
node scripts/w02_browser_check.cjs
Remove-Item Env:W02_BASE_URL
```

Script tạo tài khoản kiểm thử có email example.vn và chạy thử giới hạn đăng nhập; nên chạy trên cơ sở dữ liệu thử, không dùng dữ liệu tài khoản thật. Ảnh và kết quả ở report/w02-evidence; thông tin mật khẩu/cookie/CSRF không được lưu vào bằng chứng.

## Xác minh và khôi phục tài khoản W-03

- Các trang `/xac-minh`, `/quen-mat-khau`, `/dat-lai-mat-khau` dùng API thật. Mở liên kết chỉ hiển thị trang; người học bấm nút để xác nhận. Link mới mang token trong fragment, rồi UI xoá token khỏi URL.
- Token ngẫu nhiên 32 byte, DB chỉ giữ băm SHA-256; dùng một lần. Xác minh hết hạn sau 24 giờ, reset sau 60 phút. Gửi lại xác minh/yêu cầu reset tối đa 3 lần mỗi giờ; phản hồi reset giống nhau cho email có hoặc không có tài khoản.
- Reset thành công thu hồi mọi phiên và các link reset còn lại, chuyển về đăng nhập bằng mật khẩu mới. Chưa xác minh vẫn học/demo bình thường; luật chặn mời qua email được chuẩn bị cho W-12.
- `console` chỉ dành cho dev, ghi thư ở logger `wayfinder.infrastructure.mail` mức INFO. Production bắt buộc SMTP/STARTTLS. Queue thư nằm trong bộ nhớ; restart có thể mất thư đang đợi, người học dùng gửi lại.
- `WAYFINDER_EMAIL_LOGO_URL` là ảnh HTTPS công khai cho logo trong cả ba mẫu thư (ví dụ Cloudinary); không dùng địa chỉ localhost cho ảnh gửi tới Gmail. Để trống thì dùng logo ở `WAYFINDER_PUBLIC_BASE_URL`. Đổi cấu hình cần khởi động lại máy chủ; URL của nút xác minh/reset vẫn dùng `WAYFINDER_PUBLIC_BASE_URL`.

Kiểm toàn bộ Python trong worktree bằng runner để không import nhầm editable ở checkout khác:

```powershell
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/w03-check --junitxml=tmp/w03-check.xml
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w03_browser_runtime.py
```

Cổng Python toàn bộ dùng fixture phát triển `doc-1.pdf`, `doc-6.pdf`; riêng hai cuốn này trong các kho `artifacts/parse_tree`, `chunks`, `candidates`, `canonical`, `retrieval`, `graph` và `artifacts/phase_b/formula_images`. Đối chiếu danh sách/SHA-256 tại `report/ghep-main-evidence-2026-10-20/development-fixtures.json`. Chép tệp độc lập từ bản bàn giao đã có, không tạo junction; không sửa manifest, mở tập giữ lại, gọi mô hình hay bỏ test để thay fixture thiếu. Các tệp dữ liệu được Git bỏ qua.

Chạy từ gốc worktree. Script browser tạo DB UUID riêng trên db-test, dùng AuthStore/Argon2 thật với Mailer/Clock giả và server loopback tạm; lưu ảnh/video/JSON vào `report/w03-evidence/` rồi dọn DB. Các route lấy thư giả chỉ nằm trong script kiểm thử. Cần bộ Playwright và Chromium như hướng dẫn W-01; worktree có thể dùng bộ đã cài ở checkout gốc. Nếu có taste skill trong checkout gốc, script cũng chạy inspector ở 1280/768/390 px; không mở profile Chrome cá nhân.
