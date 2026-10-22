# Lệnh giao việc sau kiểm W-25, React W-14 và W-24 — 2026-10-22

**Trạng thái:** backend W-14/W-25 đã đạt tại `4dbfe8e`, ghép **`a5724597117094600152fb9a705354ebba10bde0`** và đã đẩy GitHub. Cổng độc lập 2.163 Python đạt/0 fail/1 Cloudinary live không bật, 85 React nền/build, sáu guard bị bắt; 0 USD. **Web có thể nhận main ngay để chạy cổng tích hợp cuối**, không còn chờ backend. Toàn W-14 và W-24 chưa đóng. Tệp được soạn để chủ dự án chuyển cho ba nhóm; điều phối chưa gửi phiên nhân viên.

Căn cứ: [báo cáo soát mới](dieu-phoi-kiem-lai-w25-w14-react-w24-va-ke-hoach-2026-10-22.md), [bảng vé](../task/web/00-ke-hoach.md), [quy trình nhánh/main](../doc/quy-trinh-nhanh-va-ghep-main.md). Claude ghép các nhánh SA; điều phối ghép web. Không tự nhập nhánh SA chưa được Claude nghiệm thu vào nhánh web để lấy đủ phụ thuộc.

## 1. Gửi nhóm web — nhận backend, dọn phần bàn giao và chạy cổng W-14 cuối

Tiếp tục **cùng W-14**, nhánh `work/w14-react`, worktree `tmp/w14-react`. Mốc local đã bàn giao `6494f51` được soát mã; chưa phải nghiệm thu cuối. Giữ nguyên W-11 ở nhánh/worktree riêng và mốc `a53f0d3`.

1. Đợi mốc backend đã ghép được ghi trong báo cáo, rồi `git merge main` trong worktree W-14. Nhận main mới nhất ở thời điểm chạy; không rebase, không đổi nhánh thư mục chung. Giữ hai bổ sung DTO đã được soát: `BuildView.upload_id` đúng actor/course và `UploadView.confirmed_at` riêng mỗi upload; không lấy đè chúng bằng bản backend gốc khi gỡ xung đột.
2. Trước bàn giao, bỏ **32 tệp thử giả** khỏi Git, giữ nguyên bản local. Hai thư mục là `report/w14-react-evidence/basetemp-contract-green` và `report/w14-react-evidence/basetemp-contract-green2`; chúng chứa `synthetic image`, không phải ảnh browser. Trong đúng worktree W-14 có thể chạy:

   ```powershell
   git rm -r --cached -- report/w14-react-evidence/basetemp-contract-green report/w14-react-evidence/basetemp-contract-green2
   ```

   Thêm `/basetemp*/` vào `.gitignore` riêng của `report/w14-react-evidence/`. Chỉ commit các đường dẫn của vé. Không dùng lệnh xoá thư mục, clean hoặc dọn worktree để làm bước này. Đỉnh bàn giao mới không còn các đường dẫn basetemp trong `git ls-tree -r --name-only HEAD report/w14-react-evidence`.
3. Chạy lại toàn bộ Python/PostgreSQL qua `scripts/w05_run_tests.py`, React, build và browser trên **đúng đỉnh tích hợp cuối** sau nhận main và sau vá câu chữ. Bộ ảnh/video cũ có trước `953240b`, phải ghi rõ lịch sử và giao bằng chứng mới cho đỉnh cuối. Cổng local 2.165 Python/104 React không thay lượt này.
4. Browser dùng PostgreSQL/BuildWorker thật, runner/media/mailer giả: chọn PDF/DOCX, tick quyền, đổi tên trước xác nhận, chưa bấm thì không chạy; reload/poll giữ build_id+course_id; hai khoá cùng tài liệu có tên/upload riêng; huỷ/thử lại/từ chối/thành công/dùng lại. SQL độc lập kiểm owner, trạng thái, usage giả khác 0 và reuse không gọi lại worker. Không hiện tiền/token/dự toán.
5. Kiểm 390/768/1280 sáng/tối, keyboard/focus, vùng bấm, giảm chuyển động theo hệ điều hành, ảnh/video. Axe cũ mới chạy ở trang rejected, không được ghi toàn bộ 47 ảnh đều đã axe; bổ sung upload, confirmation, running và terminal vào lượt cuối hoặc ghi đúng phạm vi còn thiếu. Dùng token/logo trên main; không lấy JSON raw chưa đạt của thiết kế làm nguồn thay thế.
6. Duy trì RED của ba guard UI và hai guard DTO. Không chạy mutation cùng full gate/server trên cùng mã; phục hồi nguồn rồi chạy cổng. Báo mốc backend đã nhận, main nền, commit cuối, log/JUnit/native exit, ảnh/video và giới hạn. Không tự đóng W-14 hoặc ghép main.

**Bàn giao:** cập nhật `report/w14-react-tich-hop-2026-10-22.md` hoặc báo cáo ngày thực tế, đánh dấu rõ **đợt cuối sau nhận main**; điều phối nghiệm thu lại đầu-cuối. Sau W-14 đạt mới quay sang hoàn tất W-11, migration `w11_0007` nối `w14_0006`.

## 2. Gửi nhóm lõi — bàn giao backend và hỗ trợ lượt tích hợp cuối

Giữ `tmp/w25-build-cancellation` và các worktree W-14 cũ làm bằng chứng. Khi báo cáo điều phối ghi backend đã đạt/ghép, không sửa tiếp hoặc tạo migration khác trên mốc đã được soát.

1. Hỗ trợ web nhận đúng mốc backend, xác nhận hai bổ sung DTO phục vụ quay lại trang upload và xác nhận tên riêng cho tài liệu dùng chung. Nếu phát hiện lỗi mới, ghi tái hiện và commit sửa trên nhánh đúng phạm vi; báo điều phối để soát lại, không sửa nóng main.
2. Đối chiếu cùng web các ca huỷ trước confirm, huỷ khi publication, hai tên/course dùng chung build, callback muộn và usage thực trong DB. Giữ FakeMailer/MediaStore/runner; không dùng SQLite CLI thay PostgreSQL web.
3. Trong lúc web chạy cổng cuối, chuẩn bị ghi chú đầu vào W-15: hợp đồng callback usage checkpoint từng bước, tổng chưa phân bổ/usage_complete, cấu hình transport Vertex và phạm vi dry-run cần làm sau này. Đây là chuẩn bị tài liệu, chưa mở lượt dựng thật hoặc chạy mô hình có tiền.
4. W-14 đầu-cuối đạt mới đề xuất W-15 theo vé: dry-run, số gọi/USD/phút theo từng bước, phần cache dùng lại, rồi chờ tin nhắn duyệt tiền mới. Không lấy phê duyệt phục hồi cũ hoặc ngân sách SA-55 của làn Pha B làm quyền chi cho W-15.

**Bàn giao:** backend không được coi là còn chặn web sau khi main đã ghép; chỉ nêu lỗi hoặc câu hỏi thực sự phát sinh. W-25 đạt không tự đóng toàn W-14.

## 3. Gửi nhóm thiết kế — tiếp W-24, chỉ sửa phần còn thiếu

Tiếp cùng `work/w24-figma-evidence` / `tmp/w24-figma-evidence`, nhận main mới. Bản `f1ca86d` đã được kiểm: chữ tối, bar xanh, tổng 8→9→8/18, spinner96px, clipboard thật, cuộn viewport và phép so khung ảnh đều có cải thiện thực. Không làm lại các phần đó.

1. Sửa CSS `prefers-reduced-motion` trong `design/preview/prototype_flows.html` còn trỏ `../assets/spinner_frame0_static.png` không tồn tại. Kiểm **cả giảm chuyển động của hệ điều hành và nút bật tay**. Ảnh DOM decode được chưa đủ nếu CSS `content:url(...)` thay bằng ảnh hỏng; phải kiểm ảnh render, kích thước, lỗi request và đứng khung thật.
2. So đủ **37 biến × 2 mode = 74 giá trị** với CSS thực. Hiện còn7 lệch: bốn dark tint0.15 so CSS0.14, surface-2 light chưa có alias thực, radius-full vắng cả hai mode. Đồng bộ hợp đồng theo CSS/spec hiện hành hoặc khai báo alias có kiểm rõ; không đổi token chuẩn để hợp thức hoá JSON sai.
3. Guard phải đọc CSS, so mọi mapping/mode, không hardcode vài giá trị. Đổi dark brand tint thành0.99 hiện cả28 test vẫn xanh; thêm RED cho tint/spacing/radius/motion ở cả hai mode. Bản raw trong thư mục bằng chứng vẫn35 biến trong khi design37: cập nhật hoặc ghi nhãn lịch sử và trỏ đúng bản hiện hành; không tuyên bố đồng bộ100% trước khi kiểm đủ.
4. Giữ các phép phá clipboard/scroll/GIF đã đạt; kiểm thêm OS reduced-motion và ảnh CSS bị gãy. Báo native exit/assertion RED, phục hồi nguồn, không lấy setup error làm RED.
5. Checklist lấy **đúng từng trang và trạng thái của spec11**, ghi thiếu/chưa kiểm nếu chưa có. Sửa link: `screens.html` không phải landing; `w03_auth_screens.html` không thay login/register. Còn thiếu quản trị, thành viên,404, tài liệu tạo và nhiều trạng thái upload, bài giảng/chat/quiz, lời mời, mức dùng; bảng22 dòng chưa phủ đủ yêu cầu gốc.
6. Variables Cloud cần export/biên nhận nguồn thật; node/link tự khai báo và JSON local không thay kiểm Cloud. Giao video bấm bốn prototype, đủ trang/trạng thái/cỡ và sáng/tối. Nếu quyền truy cập còn thiếu, báo đúng quyền/file/công cụ cần hỗ trợ, không ghi hoàn tất toàn vé. Không quy mọi phần thiếu thành hạn chế API khi chưa có bằng chứng cụ thể.

**Bàn giao:** `report/w24-kiem-lai-<ngay>.md`, commit, bảng còn thiếu/đã kiểm, raw+provenance, JSON/log RED/GREEN, ảnh/video/node. W-22/W-24 và W-23 vẫn mở cho đến khi đủ tiêu chí.

## 4. Luật giữ nguyên và thứ tự sau đó

- Thư mục chung luôn main; mỗi vé worktree một cấp trong tmp. Giữ mọi worktree/snapshot/ZIP và t01a; chỉ chép dữ liệu theo manifest/SHA-256, không tạo liên kết hoặc nạp live/tập giữ lại.
- Chỉ commit đường dẫn của mình; không sửa task/kế hoạch/handoff hoặc tệp dở của làn khác. Test dùng runner, PostgreSQL bắt buộc, basetemp dưới tmp của worktree; không đưa basetemp vào report/Git.
- Backend/schema W-14/W-25 đạt → web nhận main và cổng cuối W-14 → nghiệm thu đầu-cuối → W-11 hoàn tất/ghép, W-15 đề xuất chạy thật theo duyệt mới. Không chạy có tiền trong đợt này.
- W-08 còn chờ SA-53 cho SA-40/41; W-10 còn chờ SA-52. Claude nghiệm thu/ghép các nhánh SA; điều phối không tự ghi chúng đạt chỉ vì web xanh. W-23 chờ W-22 và các màn học, W-21 sau cùng.
