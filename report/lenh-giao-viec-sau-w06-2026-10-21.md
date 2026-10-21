# Lệnh giao việc sau nghiệm thu W-06 — 2026-10-21

**Trạng thái:** đã soạn để chủ dự án sao chép gửi từng nhóm; điều phối chưa gửi sang phiên nhân viên.

W-06 đã nghiệm thu tại `8b6e500`, ghép main bằng `dc41ee8`, đã đẩy GitHub. Cổng độc lập: **2.107 Python đạt, 0 fail, 1 Cloudinary live không bật; React 77/build đạt; browser PostgreSQL 9 assertion/6 cấu hình; 8/8 mutation bị bắt; 0 USD**. Hồ sơ điều phối tới `5847700`; các nhóm nhận **main mới nhất**, không dừng ở nhánh W-06 cũ.

Căn cứ giao việc: [nghiệm thu và kế hoạch](dieu-phoi-nghiem-thu-w06-va-ke-hoach-2026-10-21.md), [bảng vé](../task/web/00-ke-hoach.md), [quy trình nhánh](../doc/quy-trinh-nhanh-va-ghep-main.md), [runbook dữ liệu](../doc/du-lieu-phat-trien-va-fixture.md).

**Chốt tuyến migration 2026-10-21:** W-14 ghép trước, W-11 nối sau: `w06_0005 → w14_0006 → w11_0007`. Giữ migration W-14 đã có; W-11 tiếp tục service/API/UI, nhận migration W-14 rồi tạo `w11_0007` với `down_revision='w14_0006'`. Trước cổng cuối W-11 nhận main đã ghép mốc W-14 được soát đạt; không tạo hai head. Nếu React W-14 chưa xong, có thể soát mốc backend/schema hoàn chỉnh để ghép trước, chưa đóng vé đầu-cuối. **Theo chỉ thị tiếp của chủ dự án, chờ chủ dự án báo mới bắt đầu nghiệm thu; quyết định tuyến này không phải phán xét đạt hay cho phép ghép ngay.**

## 1. Gửi nhóm web — W-07 lộ trình và tiến độ

Nhận **W-07** theo `task/web/W-07-trang-lo-trinh-tien-do.md`. Trước khi làm, đọc báo cáo nghiệm thu W-06 và mục 4 của tệp `report/lenh-giao-viec-sau-w06-2026-10-21.md` để áp dụng luật chung.

1. Giữ worktree W-06 làm bằng chứng. Tạo nhánh `work/w07-roadmap-progress` trong worktree một cấp `C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w07-roadmap-progress` từ main mới nhất. Nếu tên đã tồn tại, kiểm trạng thái trước khi dùng; không xoá/ghi đè hoặc đổi nhánh thư mục chung.
2. Làm một vé đầu-cuối: thêm gateway `get_progress`, `set_progress`, tóm tắt tiến độ vào roadmap; API `GET /courses/{cid}/progress`, `PUT /courses/{cid}/progress/{node_id}` với `{learned: true|false}`; React danh sách module, mở/gập, bài học theo thứ tự, đánh dấu/bỏ dấu. Lỗi lưu phải rollback UI và báo rõ, không giữ thành công giả.
3. Dùng `LearningGateway` và `PostgresPhaseBStore` W-06, owner từ actor, doc/version từ course. Giữ guard thành viên cho mọi route, node ngoài graph đã phát hành trả `not_found`; test tự liệt kê route vẫn bắt route mới bỏ guard. Doc-1 hiện v8; không ghim v45/v57 hoặc đưa kho CLI/live vào web.
4. SA-47 memory/JSON đã được điều phối soát độc lập, đủ dùng hợp đồng tiến độ hiện có. W-07 vẫn phải chứng minh bằng PostgreSQL qua connection/runtime độc lập: A học không đổi B; learner bỏ dấu rồi quiz đúng không ghi đè; race giữ trạng thái cuối đúng. Không ghi toàn SA-34 hoặc các SA khác đã đạt chỉ vì W-07 xanh.
5. Giữ nhãn người dùng **“tài liệu”/“bài học”**, logo Artboard 9–28, token/font/motion đã chốt. Giao diện phải đẹp, chỉn chu; được dùng taste-skill chủ dự án nạp, ghi skill và quyết định áp dụng. Có keyboard/focus, vùng bấm mobile theo spec, reduced-motion; kiểm sáng/tối ở 390/768/1280. Không xây bài giảng/chat/quiz W-08…W-10 trong vé này.
6. Không tạo migration rỗng nếu không thêm bảng. W-14 do lõi chuẩn bị backend/worker song song; công bố hợp đồng và liệt kê thay đổi composition để điều phối tích hợp, không lấy đè tệp nhánh kia. W-07 đạt mới chuyển ưu tiên sang W-11 hoặc React W-14 theo lịch điều phối; W-04 chưa ưu tiên nếu chỉ có một phiên web.

**Bàn giao:** `report/w07-lo-trinh-tien-do-2026-10-21.md` (đổi ngày thực tế nếu khác), commit chính xác, JSON thật roadmap/progress, log/JUnit RED/GREEN và phép phá guard, ảnh sáng/tối 390/1280, kiểm 768, video mở/gập/đánh dấu/rollback. Chạy cổng toàn repo/PostgreSQL, React/build và browser thật trên đúng commit; ghi rõ mock chỉ dùng minh hoạ trạng thái. Người làm không tự đánh dấu vé đạt hoặc ghép main.

## 2. Gửi nhóm lõi — W-14 backend/worker với bộ dựng giả

Nhận **phần backend/worker W-14** theo `task/web/W-14-tai-sach-len-ban-dung.md`. W-03/W-06/W-13 đã đạt; không cần dựng lại sáu cuốn để bắt đầu. Đọc báo cáo nghiệm thu W-06, spec chức năng/CSDL và mục 4 của tệp lệnh giao này.

1. Giữ worktree W-06. Tạo nhánh `work/w14-build-worker`, worktree một cấp `C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w14-build-worker` từ main mới nhất. Không sửa ở thư mục chung hoặc nhánh web W-07.
2. Bàn giao **hợp đồng trước**: upload, xác nhận dựng, trạng thái/tiến trình, huỷ/thử lại, lỗi và ví dụ JSON; mô tả rõ actor, ownership, idempotency và phần React sẽ nối. Luồng: chọn tài liệu → kiểm tệp/quyền sử dụng → xác nhận → queued → worker reading/running → kết thúc. Không có bước dự toán/hiện chi phí cho người dùng.
3. Làm `BuildService`/worker theo vé với **BuildRunner giả, MediaStore giả, Mailer giả**. Nối hợp đồng callback W-13 và ghi PostgreSQL usage/chi thực ở thành công/lỗi/huỷ; dùng usage giả khác 0 để chứng minh ghi đúng, giữ `usage_complete=false` khi thiếu số. Không cộng chi lịch sử từ artifact/cache, không dùng SQLite CLI thay DB web.
4. Đã có course/membership ở `w06_0005`. Migration W-14 tạo upload/build/media_asset và **thêm FK `course.build_id → build.id`**, nối nguồn upload/PDF mẫu `source_public_id`, metadata module/graph đúng phiên bản. Không sửa migration W-06. Giữ `w14_0006` nối `w06_0005`; W-14 được soát đạt và ghép trước, W-11 nối `w11_0007` sau `w14_0006`.
5. Chứng minh PostgreSQL thật: hai yêu cầu cùng tài liệu dùng chung một bản dựng; hai worker không cùng nhận một việc; kiểm xác nhận trước chạy, hết hạn, quota khi bật, heartbeat/reclaim hữu hạn, huỷ ở ranh giới bước và dọn đúng tệp tạm do worker sở hữu. Phép thử bản dựng giả chép theo allowlist/manifest, không tạo liên kết tới kho chung.
6. Chỉ sửa mã web `src/web/`; không mở quyền sửa `src/doc2roadmap/` ngoài phạm vi W-05/W-13. Nếu phát hiện thiếu port/lỗi lõi, ghi tái hiện và đề xuất cho điều phối. Backend vẫn tạm Vertex; **không chạy mô hình/SMTP/Cloudinary thật**, không lấy ngân sách phục hồi làm duyệt tiền W-15.
7. Web ưu tiên W-07 trước; có thể bàn giao backend W-14 để đợi React, nhưng chưa đóng W-14 đầu-cuối. Báo rõ phần tích hợp còn thiếu. Yêu cầu tên khoá trước index hiện là điểm cần đối chiếu khi chốt hợp đồng bước xác nhận; ghi đề xuất mặc định từ tên tài liệu, không coi đề xuất UI là quyết định đã duyệt.

**Bàn giao:** `report/w14-backend-worker-2026-10-21.md` (đổi ngày thực tế nếu khác), commit, hợp đồng JSON, tuyến migration/FK, RED/GREEN, log/JUnit, bằng chứng SQL độc lập về queue/usage/capacity/idempotency và phần React còn chờ. Chạy cổng đúng commit qua runner; không tự ghép main hoặc ghi cả W-14 đạt khi mới xong backend.

## 3. Gửi nhóm thiết kế — phần còn thiếu W-24, hỗ trợ W-07/W-14

Tiếp tục **cùng W-24**, không coi toàn bộ W-22/W-24 đã đạt. Phần plugin/preview local W-06/W-04 đã ghép trong `dc41ee8`; điều phối đã sửa các claim sai ở `8b6e500`. Đọc `task/web/W-24-bo-sung-va-sua-ban-giao-w22.md`, báo cáo nghiệm thu W-06 và mục 4 của tệp lệnh giao này.

1. Tiếp tục trong `C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w24-figma-evidence`, nhánh `work/w24-figma-evidence`. Kiểm status, lưu riêng phần mã dở nếu có rồi nhận main mới. Khi có xung đột, giữ các sửa đúng hợp đồng: link xác minh 24 giờ, link reset 60 phút, resend 3 lần/giờ; trạng thái email đã xác minh không hết hạn sau 24 giờ. Không khôi phục chữ canvas báo nối reactions thành công vô điều kiện.
2. **Hoàn tất nguồn Variables:** giao raw export thực từ file Figma có file key/collection/mode/thời điểm/công cụ; đối chiếu tên và giá trị với CSS/token. JSON tạo lại từ dữ liệu local không được ghi là export Cloud hoặc đồng bộ hai chiều 100%.
3. **Hoàn tất trang/trạng thái:** bảng spec → node → ảnh/video, đủ sáng/tối và 390/1280, kiểm 768. Chỉ đánh dấu đã có khi mở/đối chiếu được. Ưu tiên màn W-07: module mở/gập, tiến độ, đánh dấu/rollback; rồi W-14: chọn tài liệu, xác nhận, bốn bước dựng, lỗi/huỷ/thử lại. Giữ nội dung tiếng Việt “tài liệu”/“bài học”, không hiện dự toán/chi phí cho người dùng.
4. **Bốn prototype Figma:** link chạy được, node bắt đầu và video từng luồng. Clipboard phải chứng minh nội dung sao chép, citation chứng minh kết quả mở/scroll, reduced-motion chứng minh GIF đứng khung qua thời gian. Cố ý bỏ handler/chuyển bước phải đỏ đúng assertion. Audit HTML local 4/4, class mở hoặc chỉ kiểm src ảnh không thay các bằng chứng đó.
5. Helper cần báo đúng số reactions nối được/thất bại/cần làm tay. Thông báo plugin không thay kiểm bấm thực trong Figma. Báo cáo phân biệt rõ phần local, dữ liệu Cloud nhóm tự khai báo và phần đã được người soát xác minh.
6. Giao diện đẹp, nhất quán thương hiệu, focus và vùng bấm đúng spec; motion theo token và reduced-motion. Được dùng taste-skill chủ dự án nạp, ghi skill/điều đã áp dụng. Không thiết kế lại thương hiệu hoặc xây React/logic nghiệp vụ trong vé thiết kế.

**Bàn giao:** `report/w24-bo-sung-w22-2026-10-21.md` (đổi ngày thực tế nếu khác), commit, raw Variables/provenance, bảng đối chiếu CSS, checklist node/ảnh/video và bốn link prototype, log phép phá guard. Các ảnh/video phải có đường dẫn bền vững trong `report/` theo vé; không chỉ trỏ tệp tạm không được bàn giao. Người soát quyết định đóng W-24; nhân viên không tự ghi đạt toàn bộ.

## 4. Luật chung — áp dụng cho cả ba prompt

- Đọc `AGENTS.md`, spec/vé, `doc/quy-trinh-nhanh-va-ghep-main.md`, `doc/du-lieu-phat-trien-va-fixture.md` và báo cáo nghiệm thu W-06. Chỉ điều phối sửa vé/kế hoạch/handoff và ghép main; nhân viên commit mã/test/báo cáo đúng đường dẫn của vé, không `git add -A`, `git add .` hoặc `commit -a`.
- Mỗi công việc một nhánh/worktree một cấp dưới `tmp/`; thư mục chung luôn main. Giữ worktree đã nghiệm thu để đối chiếu. **Không dọn worktree/snapshot/ZIP và không đụng `tmp/t01a-clean-ff797eb`.** Không junction/symlink/hardlink.
- Dữ liệu sáu cuốn lấy theo hai manifest trong `report/w06-fixtures-evidence-2026-10-20/bundles.json`, kiểm SHA-256 nguồn/đích. Tệp đích khác hash thì dừng báo điều phối, không ghi đè. Không đọc kho Pha B live chung/tập giữ lại. Web dùng PostgreSQL; không nhập learner store CLI vào DB.
- Mọi kiểm trong đợt giao này **0 USD**: mô hình/Mailer/MediaStore giả, PostgreSQL thật và browser thật ở DB UUID riêng. Không gửi thư thật, upload Cloudinary hoặc gọi Gemini; Vertex vẫn là transport backend đã chốt. Không chạy seed hoặc kiểm phá trên DB phát triển của chủ dự án.
- Test phải bắt bản sai theo AGENTS.md mục 5, không bỏ assertion/skip/hạ ngưỡng để xanh. Ghi commit, lệnh và native exit code; phân biệt JSON/ảnh mock với bằng chứng HTTP thật. Mutation chạy tuần tự và phục hồi mã trước cổng.
- Không tạo migration rỗng; vé có bảng mới tạo một migration nối head điều phối xác nhận. Không sửa migration đã ghép. Nhận main mới trước cổng cuối, không tự merge/push main.

Cổng từ gốc worktree, dùng basetemp mới cho mỗi lần:

```text
C:/Users/ngoco/Desktop/Doctoroadmap/.venv/Scripts/python.exe scripts/w05_run_tests.py -o addopts= -q --basetemp=tmp/cong-<ve>-<lan> --junitxml=tmp/cong-<ve>-<lan>.xml
npm.cmd --prefix src/web/frontend test -- --pool=threads --maxWorkers=1
npm.cmd --prefix src/web/frontend run build
```

Không chạy pytest trần trong worktree. Chỉ khởi động kiểm browser sau khi đọc harness, xác nhận dùng DB tạm và đồ giả; kèm ảnh/video/console/network/accessibility theo vé. Thiết kế có thể dùng cổng tập trung lúc làm, nhưng cổng tích hợp trước ghép vẫn theo quy trình.
