# Lệnh giao việc sau đợt soát W-07/W-14/W-24 — 2026-10-21

**Đã có đợt tiếp 2026-10-22:** [lệnh giao sau W-25](lenh-giao-viec-sau-w25-2026-10-22.md). Backend/schema W-14+W-25 đã đạt và ghép `a572459`; web nhận main để chạy cổng cuối, thiết kế chỉ tiếp3 nhóm Required W-24. Các lệnh bên dưới giữ làm lịch sử, không giao lại hai race đã đóng.

**Trạng thái:** đã soạn để chủ dự án sao chép gửi từng nhóm; chưa gửi sang các phiên nhân viên. W-07 đạt tại `2a14723`, ghép `f20d198` và đã đẩy GitHub: 2.114 Python/85 React/build, browser PostgreSQL: 11 kiểm tra/6 cấu hình, 10 mutation bị bắt; 0 USD. Các nhóm nhận main mới nhất, không dừng ở nhánh W-07 cũ. W-14/W-24 chưa đạt theo phán xét đợt này.

Căn cứ: [báo cáo soát và kế hoạch](dieu-phoi-nghiem-thu-w07-w14-w24-va-ke-hoach-2026-10-21.md), [bảng vé](../task/web/00-ke-hoach.md), [quy trình nhánh](../doc/quy-trinh-nhanh-va-ghep-main.md), [runbook fixture](../doc/du-lieu-phat-trien-va-fixture.md).

## 1. Gửi nhóm lõi — ưu tiên W-25 sửa mốc backend W-14

Nhận **W-25** theo `task/web/W-25-dong-bo-xac-nhan-huy-va-ket-thuc-ban-dung.md`. Mốc W-14 `5b24ece` chưa đạt nghiệm thu: 35 test cũ xanh nhưng điều phối tái hiện hai race PostgreSQL. Chưa chờ React để sửa các lỗi này.

1. Giữ `tmp/w14-build-worker` và nhánh W-14. Tạo `work/w25-build-cancellation` trong `tmp/w25-build-cancellation` từ đúng mốc bàn giao W-14, rồi nhận main mới. Chỉ commit mã/test/báo cáo của vé; không sửa task/kế hoạch/bàn giao.
2. Sửa race xác nhận/huỷ: nếu huỷ commit sau khi confirm đọc trạng thái nhưng trước khi confirm ghi queue, kết quả cuối phải giữ huỷ. Kiểm bằng hai connection PostgreSQL và SQL độc lập; không để `queued + cancel_requested=true` vừa treo vừa mất lượt.
3. Sửa race huỷ/terminal publication: cờ huỷ phải được xét lại dưới khóa trong transaction kết thúc. Huỷ đã được nhận trước terminal commit không được ghi `succeeded`, course `ready` hoặc gửi thư thành công. Kiểm cả graph và media publication; giữ usage thực khác 0, receipt chỉ ghi một lần, fence lease cũ vẫn có hiệu lực.
4. Dùng hai ca tái hiện trong gói bằng chứng làm đầu vào, thêm guard ổn định theo thứ tự commit chứ không khóa cứng vào cách cài hiện tại. Lưu RED trên mã cũ, GREEN trên mã sửa, SQL trạng thái/quota/course/usage và Mailer giả.
5. Không tạo migration W-25; giữ `w14_0006` nối `w06_0005`. Nhận W-07 thì sinh lại OpenAPI có đủ progress/builds, giữ test tự liệt kê route. Backend/schema chỉ ghép sau khi người soát nhận đúng commit và cổng xanh; W-14 còn chờ React để đóng toàn vé.
6. Chạy qua `scripts/w05_run_tests.py`, PostgreSQL bắt buộc, React/build. Model/MediaStore/Mailer giả, 0 USD; không dùng ngân sách phục hồi hoặc mở W-15 chạy thật.

**Bàn giao:** `report/w25-dong-bo-huy-ban-dung-<ngay>.md`, commit chính xác, log/JUnit RED/GREEN, kết quả SQL, phạm vi còn chờ. Nhóm lõi tiếp tục sở hữu backend; người điều phối ghép, nhân viên không tự đẩy main.

## 2. Gửi nhóm web — React W-14, giữ phần W-11 đã làm

W-07 được xét riêng theo báo cáo nghiệm thu. Ưu tiên tiếp theo là **React/tích hợp W-14 bằng bộ dựng giả**, sau đó hoàn tất W-11 theo tuyến đã chốt. Nếu phiên đã làm W-11, commit riêng phần đang làm và giữ nguyên nhánh/worktree; không xoá hoặc cuốn mã W-11 vào W-14.

1. Làm nhánh riêng `work/w14-react`, worktree một cấp `tmp/w14-react`. Nếu backend W-14/W-25 chưa vào main, có thể chuẩn bị nhánh phụ thuộc mốc backend đã bàn giao theo mục 3.2 quy trình; ghi rõ gốc và không coi mã phụ thuộc đã đạt. Trước cổng tích hợp cuối phải nhận main có backend đã soát đạt.
2. Đọc hợp đồng trong `report/w14-backend-worker-2026-10-21.md` của nhánh lõi: chọn PDF/DOCX → xác nhận quyền dùng → kiểm tệp → tên khoá điền sẵn từ tên tài liệu, người dùng sửa trước nút “Dựng lộ trình” → POST xác nhận → queued/reading/running/kết thúc. Chưa bấm xác nhận thì không chạy. Không hiển thị tiền/token/dự toán.
3. Lưu **cả build_id và course_id** từ phản hồi. Poll mỗi 3 giây qua `GET /builds/{id}?course_id=<cid>`; cancel/retry cũng gửi course_id. Hai khoá cùng tài liệu phải giữ tên và ngữ cảnh trang riêng; quyền vẫn do server kiểm. Tôn trọng `can_cancel`, `can_retry`, `error.retryable`; reload/quay lại vẫn đúng trạng thái.
4. Quota lấy `/me/usage`, ẩn khi không giới hạn; không tự hứa hoàn lượt khi huỷ hoặc từ chối bản quét. Thẻ đang dựng hiển thị bước thật từ API; dùng lại thành công chuyển ready không gọi runner lần nữa. Render lỗi bằng message/code đã quy định, không lộ đường dẫn hay public_id.
5. Giữ logo Artboard 9–28, font/token hiện hành của main và nhãn “tài liệu”/“bài học”. Preview W-24 mới **chưa đạt**: không chép tên biến `--color-text-main`/`--color-brand-blue` không tồn tại hoặc số tiến độ sai. Được dùng taste-skill; giao diện phải chỉn chu, focus/keyboard, vùng bấm, motion 120/200 ms và reduced-motion theo spec.
6. Kiểm browser thật với PostgreSQL/runner/media/mailer giả: upload, tên trước xác nhận, tiến trình, reload, cancel/retry, rejected, succeeded/dùng lại; 390/768/1280 sáng/tối, ảnh/video, JSON thật. Ảnh mock ghi rõ phạm vi, không thay luồng thật. Nối backend sửa W-25 rồi chạy cổng đúng commit, không đóng W-14 khi mới có UI độc lập.
7. W-11 giữ tuyến `w06_0005 → w14_0006 → w11_0007`, chưa ghép trước W-14 đã sửa/soát đạt. Không bẻ tuyến để né W-25 hoặc thêm Alembic merge revision. Ngoài phạm vi đợt này: nghiệm thu W-11, bài giảng/chat/quiz W-08…W-10 và runner thật.

**Bàn giao:** `report/w14-react-tich-hop-<ngay>.md`, commit/gốc phụ thuộc, backend đã nhận, lệnh/log/JUnit, ảnh/video và giới hạn. Nếu chỉ có một phiên web, hoàn tất/lưu lát W-11 đang làm rồi chuyển có kiểm soát; không làm hai nhánh UI dở trong cùng thư mục.

## 3. Gửi nhóm thiết kế — tiếp W-24, sửa sáu nhóm lỗi

Tiếp **W-24**, chưa đóng W-22/W-24. Mốc `c1df32a` chưa đạt; đọc báo cáo soát và `report/coord-w07-w14-w24-evidence-2026-10-21/w24/review.md`. Giữ worktree/nhánh `tmp/w24-figma-evidence` / `work/w24-figma-evidence`, nhận main mới trước sửa.

1. Dùng đúng token CSS đã có: `--color-text`, `--color-brand`; sửa chữ đen trên nền tối và thanh tiến độ trong hai preview mới. So toàn bộ raw Variables với CSS thực, gồm sáng/tối, tên/kiểu/giá trị. Hiện có 7 điểm lệch ở bản raw/light đã đối chiếu; test mới phải đỏ khi đổi giá trị primary, không chỉ kiểm tên/số lượng.
2. Chứng minh nguồn Variables bằng bản xuất thực và biên nhận công cụ/file/node/mode/thời điểm; JSON tạo từ local phải ghi đúng phạm vi. Không đổi nhãn metadata thành “native export” để thay bằng chứng. Không đổi token chuẩn để khớp bản raw sai.
3. Sửa clipboard guard: đọc clipboard thật sau click; gỡ `navigator.clipboard.writeText` phải đỏ. Sửa citation guard: khởi đầu ngoài viewport, click rồi đo giao cắt viewport/scroll; bỏ `scrollIntoView` phải đỏ. `data-copied-text` hay `isVisible` không đủ.
4. Sửa đường ảnh GIF/tĩnh đang hỏng; assert `complete` và `naturalWidth>0`/decode trước so khung. Bật giảm chuyển động thì ảnh thật đứng khung qua thời gian; cho GIF thật chạy lại phải đỏ. Vòng chờ W-14 đang 32 px phải theo spec 96 px, không ghi báo cáo 96 khi CSS là 32.
5. Tiến độ mẫu W-07 dùng cùng dữ liệu để tổng/module/bài học khớp, cập nhật khi đánh dấu/hoàn tác; hiện 12/18 khác tổng module 8/18. Luồng W-14 theo hợp đồng lõi có bước đặt tên/xác nhận; không hứa không trừ lượt khi đã xác nhận rồi rejected.
6. Lập lại checklist **từng trang/trạng thái theo spec mục 11**, không thay bằng 14 nhóm chung. Giao ảnh 390/1280, kiểm 768 và tối/sáng đúng từng trang, node ID/link thực; không dùng components thay màn quản trị/thành viên/404. Bốn prototype Figma có node bắt đầu, link Present và video thao tác thật; report phân biệt local/Cloud tự báo/người soát xác minh.

**Bàn giao:** `report/w24-kiem-lai-<ngay>.md`, commit, bảng thiếu/đủ, raw export/provenance, JSON guard RED/GREEN, ảnh/video/node thật. Không làm lại thương hiệu hay sửa React. Nếu Cloud chưa truy cập được, báo rõ phần thiếu; không ghi hoàn tất 100%.

## 4. Luật dữ liệu, cổng và các mốc sau

- Thư mục chung luôn main; mỗi vé worktree riêng một cấp trong `tmp/`. Không đổi nhánh thư mục chung, không tự ghép/push main, không sửa hồ sơ điều phối.
- Chỉ chép dữ liệu theo hai manifest/bundles W-06 và đối chiếu SHA-256; không junction/symlink/hardlink, không nạp cache CLI/live hoặc tập giữ lại. Giữ mọi snapshot/ZIP/worktree, không đụng `tmp/t01a-clean-ff797eb`.
- Trước pytest tạo thư mục cha `tmp/` trong worktree. Dùng Python `.venv` thư mục chung qua `scripts/w05_run_tests.py`, không pytest trần. Không lấy setup error làm RED nghiệp vụ.
- Test/build đầy đủ và browser thật trên đúng commit; báo rõ dịch vụ giả và mock phản hồi. Ngoài W-15 mọi vé 0 USD, Vertex giữ nguyên; W-15 cần dry-run và duyệt tiền mới bằng tin nhắn.
- W-25 đạt → ghép mốc backend/schema W-14 → W-11 nối migration; React W-14 tích hợp đạt mới đóng toàn W-14 → sau đó mới xét W-15. W-08 cần soát đúng phụ thuộc SA-39/40/41 và phần sửa B2 liên quan; không coi cổng W-07 là nghiệm thu toàn Pha B2. W-23 vẫn chờ W-22/W-24 và các màn học; W-21 sau cùng.
