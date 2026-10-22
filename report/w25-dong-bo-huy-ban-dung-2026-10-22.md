# W-25 — đồng bộ xác nhận, huỷ và kết thúc bản dựng — 2026-10-22

## Phạm vi và mốc Git

Nhóm lõi sửa hai race PostgreSQL của backend W-14; không thay runner thật, React W-14 hoặc schema. Chờ người soát nhận đúng commit; báo cáo này không tự nghiệm thu W-14 đầu-cuối, không ghép hoặc đẩy main.

- Worktree: `tmp/w25-build-cancellation`, nhánh `work/w25-build-cancellation`.
- Tách đúng W-14 `5b24ece9b76edb8d5686fd33114ebdb442bbe336`; giữ nguyên worktree/nhánh W-14.
- Nhận main `46703b4686087553250ff3156b5551e64dea9eee` bằng merge `6a2e7f129d5cfe6c3ebc15bcb5ec299a51253394`. Xung đột duy nhất là OpenAPI; sinh lại từ app có cả progress và builds.
- RED sạch: `76199c44e394e4d6402eb9173fe714c62452e1b2`; ba tệp production gây lỗi giống hệt `5b24ece`.
- Sửa production: `536a87ae4062099fd2adf1a4c713f5a2e512d5c1`. Chỉ 14 dòng thêm/đổi trong ba tệp; còn lại là kiểm thử và bằng chứng.
- Mốc mã/test đầy đủ: `0a2afa89b13010100b721909ed749f0585b73031`; production giống `536a87a`, thêm test/mutation chứng minh khoá terminal bằng thứ tự commit quan sát được.
- Trong lúc chạy cổng, main có thêm tài liệu `8afb7a70d1dbae6841e0a46328af2048e9a860e9`. Đã nhận bằng merge **`37a7728e0fe84d857d72e286a4a3534bd8b936c6`**; `git diff 0a2afa8 37a7728 -- src tests scripts design` rỗng. Đây là mốc chốt cổng sau nhận main, không sửa thủ công vé/kế hoạch của làn khác.

## Nguyên nhân và cách sửa

### Confirm và cancel

Confirm giữ khoá account/document nhưng đọc trạng thái build không khoá. Cancel dùng khoá hàng build, nên có thể commit `cancelled` giữa lần đọc và UPDATE queued vô điều kiện.

Đổi UPDATE queued thành chuyển trạng thái có điều kiện: chỉ từ `awaiting_confirmation AND NOT cancel_requested`, có `RETURNING id`. PostgreSQL xét lại predicate khi có cập nhật cạnh tranh. Không chuyển được thì trả `conflict`, rollback cả xác nhận upload và tên khoá; không tính lượt. Nếu confirm commit trước thì cancel vẫn huỷ và giữ lượt đã dùng theo luật cũ.

### Cancel và terminal publication

Worker từng kiểm huỷ trước khi đọc graph/tải media. `record_usage` khoá build nhưng không xét lại cờ, nên vẫn chốt success từ kết quả cũ.

Trong transaction `record_usage`, sau khi khoá build và xác minh receipt/lease, lease đang hoạt động có `cancel_requested` được chuẩn hoá thành `cancelled`: bỏ lỗi, graph version và metadata publication. Số usage giữ nguyên. Cùng kết quả callback được cập nhật để worker không gửi thư theo success cũ. Receipt cũ vẫn bất biến; callback lease cũ chỉ ghi usage đã biết, không đổi trạng thái lease mới.

Media được kiểm huỷ trước upload và dưới khoá sau upload. Nếu huỷ được nhận trong upload không dừng được, xoá đúng public ID vừa tải, không đăng ký asset đó và không tải ảnh tiếp. Không xoá PDF nguồn hoặc tệp dùng chung.

## RED/GREEN và thứ tự commit

Điểm xuất phát là [hai ca điều phối](coord-w07-w14-w24-evidence-2026-10-21/w14-cancellation-repros.py.txt). Ca confirm được đồng bộ ngay trước câu UPDATE queue, không đếm số lần `get_job`. Các ca publication dùng Event và một BuildService/engine riêng để huỷ commit trước khi tiếp tục worker. Mọi quan sát SQL lại mở engine độc lập.

- RED sạch trên mã cũ: **10 fail nghiệp vụ, 2 pass, 0 setup error**, native exit 1. [JUnit](w25-evidence/runs/red.xml), [log](w25-evidence/runs/red.log), [commit/lệnh/hash](w25-evidence/runs/red-exit.json).
- GREEN đầu: **47 pass**, gồm 35 ca W-14 cũ và 12 ca W-25; native exit 0. Lượt này trước commit sửa, có SHA-256 production trong metadata. [JUnit](w25-evidence/runs/focused-green.xml), [metadata](w25-evidence/runs/focused-green-exit.json).
- Thêm ca quan sát thứ tự commit ngay sau terminal row read: chờ `pg_blocking_pids` hoặc thấy cancel đã commit, rồi xét trạng thái cuối theo yêu cầu huỷ thực sự được nhận. Bỏ khoá hàng phải gây sai trạng thái cuối; không dùng việc thiếu khoá hoặc timeout làm bằng chứng chính.

Các lượt ban đầu cũng được giữ: `red-environment` có 12 setup error vì Docker tắt, không tính RED; `red-initial` có một assertion dư do thư đăng ký tài khoản nằm chung Mailer giả, được sửa fixture để tách thư đăng ký rồi chạy RED sạch. Không tính các lỗi này thành lỗi production.

### Ma trận bắt buộc

| Ca | Quan sát SQL/side effect bắt buộc |
|---|---|
| Cancel commit trước queue write | `cancelled`, quota 0, `confirmed_at=NULL`, tên chưa bị đổi, không attempt/ledger, worker không claim |
| Confirm commit trước cancel | `cancelled`, quota 1 giữ nguyên, course failed, không claim |
| Cancel trong graph publication | cancelled; course failed, version NULL, module 0; không thư |
| Cancel trong formula/media upload | như trên; dừng sau upload đang diễn ra, xoá đúng asset mới, không ghi media_asset |
| Cancel trước terminal row lock | cancelled dù mọi kiểm huỷ của worker trước đó đã qua |
| Terminal commit trước cancel | success/ready/version 8 được giữ; huỷ không được nhận, một thư thành công |
| Lease cũ trả kết quả sau reclaim/cancel | không đổi lease mới; tổng `.009 + .003 = .012` giả, hai receipt; receipt lặp không cộng |
| Usage thiếu số | `usage_complete=false` giữ nguyên; không thay bằng chi 0 |

Các ca graph/formula/media/terminal đều chạy với usage complete và incomplete. Mỗi lần có `.003` giả, 3 calls/300 input/60 output; ledger cộng đúng `.003`, final receipt đúng một lần, callback lặp không thêm ledger. [SQL GREEN](w25-evidence/sql/focused-green/), [SQL RED](w25-evidence/sql/red/), [queue/capacity W-14 chạy lại](w25-evidence/sql/w14-regressions/).

## Migration, hợp đồng và dữ liệu

- Không tạo hoặc sửa migration. Tuyến giữ `w06_0005 → w14_0006`, một head `w14_0006`; W-11 là successor do điều phối ghép sau.
- Giữ nguyên API upload/confirm/poll/cancel/retry/quota và tên course trước index. Confirmation nhận `{}` hoặc `{"title":"Tên trước index"}` như W-14 đã bàn giao. Không có dự toán hoặc chi phí trong DTO cho người dùng.
- OpenAPI nhận W-07 có GET progress, PUT node progress cùng toàn bộ uploads/builds. Giữ bộ kiểm tự liệt kê route `{cid}`; không miễn route khỏi kiểm quyền.
- Dữ liệu sáu cuốn được chép 3.144 tệp theo hai manifest W-06, kiểm hash nguồn/đích; không link, không nhập learner store/live.json và không dựng lại sách. Doc-1 v8, doc-6 v29.
- Models, embedding, MediaStore và Mailer đều giả/chặn mạng trong harness. Các số `.003`/`.012` là usage tổng hợp để kiểm DB; **chi nhà cung cấp mới 0 USD**. Không dùng ngân sách phục hồi, không chạy W-15.

## Cổng cuối và phép phá guard

Mọi pytest qua `scripts/w05_run_tests.py`, PostgreSQL bắt buộc; không pytest trần, không hạ ngưỡng/skip test để xanh.

| Cổng | Kết quả | Bằng chứng |
|---|---|---|
| Python toàn repo + PostgreSQL bắt buộc tại `0a2afa8` | **2.163 pass, 1 skip**, 0 fail/error, exit 0 | [JUnit](w25-evidence/runs/final-gate.xml), [log](w25-evidence/runs/final-gate.log), [mốc/lệnh](w25-evidence/runs/final-gate-exit.json) |
| Python toàn repo + PostgreSQL bắt buộc tại `37a7728` | **2.163 pass, 1 skip**, 0 fail/error, exit 0 | [JUnit](w25-evidence/runs/received-main-gate.xml), [log](w25-evidence/runs/received-main-gate.log), [mốc/lệnh](w25-evidence/runs/received-main-gate-exit.json) |
| React tại `37a7728` | **85 pass**, exit 0 | [JUnit](w25-evidence/runs/received-main-react.xml), [log](w25-evidence/runs/received-main-react.log), [mốc/lệnh](w25-evidence/runs/received-main-react-exit.json) |
| TypeScript/Vite tại `37a7728` | **Đạt**, exit 0 | [log](w25-evidence/runs/received-main-build.log), [mốc/lệnh](w25-evidence/runs/received-main-build-exit.json) |
| Mutation W-14/W-25 | **20/20 bị bắt**, native 1 mỗi bản sai; không setup error; nguồn phục hồi đúng byte | [19 guard](w25-evidence/mutations/mutations.json), [bỏ khoá terminal](w25-evidence/mutations/mutations-terminal-row-lock.json), [log harness](w25-evidence/runs/mutations.log) |
| Thứ tự commit ngay sau terminal row read | **1 pass**; bỏ khoá thì assertion `succeeded != cancelled` đỏ | [GREEN](w25-evidence/runs/row-lock-green.xml), [RED](w25-evidence/mutations/terminal-row-lock.xml), [SQL/khoá](w25-evidence/sql/row-lock-green/terminal-row-lock-order.json) |
| Chạy lại riêng 6 guard W-25 tại `37a7728` | **6/6 bị bắt**, không setup error; nguồn phục hồi | [ledger](w25-evidence/mutations/final-w25-guards.json), [mốc/lệnh/exit](w25-evidence/runs/final-w25-guards-exit.json) |

Mutation `boundary-cancel` cũ được đổi sang bỏ kiểm huỷ ở đầu bước. Kiểm huỷ chỉ ở đầu callback nay có guard terminal bọc lại, nên xoá riêng kiểm đầu callback không còn là mutation nghiệp vụ có ý nghĩa. Giữ đầy đủ 35 test W-14 và 14 nhóm guard cũ; bổ sung 6 guard W-25: CAS confirm, huỷ terminal, huỷ media, receipt, mail và khoá terminal.

Skip duy nhất là Cloudinary live yêu cầu bật riêng `WAYFINDER_RUN_CLOUDINARY_TESTS=1`; không skip PostgreSQL. Cổng gồm đủ **13 ca W-25, 35 ca W-14**. Lượt đầu mất 837,93 giây pytest / 858,51 giây wrapper; giữ thời gian thực trong metadata, không ước lượng hoặc dùng timeout thay kết quả nghiệp vụ.

Lượt chốt tại `37a7728` mất **813,00 giây pytest / 831,53 giây wrapper**. Không có thay đổi mã/test sau mốc này; commit bàn giao tiếp theo chỉ thêm báo cáo/bằng chứng. [Đối chiếu cây nguồn khi nhận main](w25-evidence/received-main-source-comparison.json), [OpenAPI/migration](w25-evidence/contract-schema.json), [manifest dữ liệu đã chép](w25-evidence/fixture-copy.json).

Gói bằng chứng có [tóm tắt máy đọc](w25-evidence/summary.json) và [SHA-256 từng tệp](w25-evidence/manifest.json). Log/XML được chuẩn hoá LF và bỏ khoảng trắng cuối dòng; [normalization](w25-evidence/normalization.json) giữ hash trước/sau và kiểm số testcase/failure/error/skip không đổi. Bản thô của các tệp thay đổi được giữ trong `tmp/w25-raw-evidence/` của worktree. `.gitattributes` trong gói giữ nguyên byte khi checkout. Không có mật khẩu/khoá cấu hình trong bằng chứng.

Tự soát theo correctness/readability/architecture/security/performance: thay đổi dùng transaction và kiểu DTO hiện có, không thêm lớp/dependency; kiểm quyền/CSRF không đổi; SQL tham số hoá; tận dụng khoá đã có, không giữ transaction qua graph/media/network. Kết luận kiểm được giới hạn ở bộ dựng giả. Chưa thay việc người soát kiểm độc lập.

## Tái lập

Chạy từ worktree W-25; Python của `.venv` ở repo gốc. `db-test` phải healthy; cấu hình riêng do runner đọc, không đưa credentials vào lệnh/log. Tạo thư mục `tmp` trước và dùng basetemp mới cho mỗi lượt.

```powershell
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 src/web/backend/tests/copy_w06_fixtures.py
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py src/web/backend/tests/test_build_cancellation_w25.py src/web/backend/tests/test_builds_w14.py -o addopts= -q --basetemp=tmp/w25-recheck-new --junitxml=tmp/w25-recheck-new.xml
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe -X utf8 src/web/backend/tests/w25_mutations.py
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/w25-full-new --junitxml=tmp/w25-full-new.xml
npm.cmd --prefix src/web/frontend ci --no-audit --no-fund
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1
npm.cmd --prefix src/web/frontend run build
```

Mutation phải chạy riêng, không cùng cổng/server trên cùng mã; harness luôn phục hồi nguồn. `w25_capture.py <nhãn> <lệnh...>` thu native exit, commit/hash và log UTF-8; các lệnh thực tế nằm trong `runs/*-exit.json`. Test cũ có sinh lại bằng chứng W-14/W-06; chỉ giữ bản sao của lượt mới dưới W-25, phục hồi archive cũ trước commit.

## Phần còn chờ

Người soát nhận commit backend/schema W-14 + W-25 và chạy kiểm độc lập trước khi ghép main. React/tích hợp browser của W-14 vẫn thuộc nhóm web, chưa được thực hiện hoặc nghiệm thu trong vé W-25. Cổng React/build ở đây chỉ bảo vệ W-07 hiện có trên main; không thay bằng chứng upload → tên/xác nhận → poll/huỷ/thử lại/kết thúc trên trình duyệt W-14. Không tự đóng toàn vé W-14.
