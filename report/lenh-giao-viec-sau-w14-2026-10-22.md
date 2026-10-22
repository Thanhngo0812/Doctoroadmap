# Lệnh giao việc sau đợt W-14 tích hợp, lõi hỗ trợ và W-24 — 2026-10-22

**W-14 đã đạt có ghi chú và ghép/đẩy `7fe63df`, mốc kiểm `61b5d80`:2.185 Python/104 React/build, browser/SQL và5 guard đạt; chi ngoài0 USD.**
Tài liệu hỗ trợ lõi đã nhận cùng mốc; W-24 còn mở. Tệp để chủ dự án chuyển cho ba nhóm;
căn cứ [báo cáo nghiệm thu](dieu-phoi-nghiem-thu-w14-ba-nhom-va-ke-hoach-2026-10-22.md).
Thay phần giao cũ của [đợt W-25](lenh-giao-viec-sau-w25-2026-10-22.md); không giao lại lỗi token/OS reduced-motion đã được kiểm đạt.

## 1. Nhóm web — hoàn tất W-11, sau đó W-08

W-14 đã được điều phối nghiệm thu/ghép. Tiếp W-11 ở `work/w11-share-links`, worktree `tmp/w11-share-links`, mốc cũ `a53f0d3`.
Trong đúng worktree đó `git merge main`, không rebase, không đổi nhánh thư mục chung. W-11 chưa có phán xét đạt từ đợt này.

1. Hoàn tất W-11 theo [vé](../task/web/W-11-chia-se-link-thanh-vien.md): link khách/đã đăng nhập, tham gia, thu hồi, rời khoá, xoá thành viên và mất quyền
   ngay. Dữ liệu học riêng giữ nguyên. Không lấy màn token reset/email làm giao diện link tham gia hỏng.
2. Migration duy nhất `w11_0007` nối `w14_0006`, không sửa migration đã ghép hoặc tạo hai head. Giữ hai DTO `upload_id` đúng actor/course và
   `confirmed_at` riêng upload của W-14 khi nhận main.
3. Kiểm PostgreSQL bằng runner, falsifiable guards cho quyền/token/đếm lượt và transaction tham gia. Trình duyệt HTTP/PG thật, mail/media giả;
   kiểm khách đăng nhập quay lại đúng link, link hỏng, đã là thành viên, hết lượt/hết hạn, bị gỡ thành viên mất quyền ở request kế tiếp.
4. Giao JSON HTTP, ảnh 390/768/1280 sáng/tối, video, axe đúng phạm vi, RED/GREEN và cổng đầy đủ trên đúng commit sau nhận main. Không tự ghép main.

**Bàn giao:** `report/w11-chia-se-link-thanh-vien-2026-10-22.md` hoặc báo cáo W-11 hiện có được cập nhật, bằng chứng trong `report/w11-evidence/`,
commit SHA và câu hỏi còn lại. Bằng chứng/basetemp fixture không được trộn với ảnh UI; basetemp để dưới `tmp/`.

Sau W-11 được điều phối nghiệm thu, làm W-08 trong worktree mới từ main đã ghép: SA-53 đã vào main `62dad5b` nên không còn chờ câu nối.
Giữ `lecture-2`, SSE sau cổng, không hiện bản lùi; media/source luôn kiểm quyền. Sau đó W-10 theo SA-52 đã ghép `66cd439`.
W-09 đã bổ sung `focus_node_id` vào vé/spec: chỉ chốt cổng tích hợp khi Claude nghiệm thu/ghép SA-56. Không sửa use case trợ lý trong vé web.
Nếu SA-56 xong trước khi giao W-10, điều phối có thể ưu tiên W-09 sau W-08 để nối khung chat; chưa mở đồng thời ba vé cùng sửa `LearningGateway`.

## 2. Nhóm lõi — W-15, giai đoạn adapter/kiểm 0 USD

Tài liệu hỗ trợ `1acaf4e` đã được soát không còn Required; đây là hoàn tất đầu việc chuẩn bị, chưa phải runner thật đã nối.
Sau W-14 được ghi đạt, tạo worktree một cấp `tmp/w15-real-build`/nhánh `work/w15-real-build` từ main mới nhất. Đọc
[ghi chú đầu vào](w15-ghi-chu-dau-vao-sau-w25-2026-10-22.md) và [vé W-15](../task/web/W-15-noi-bo-dung-that-do-usd-cuon.md).

1. Cài phần adapter/composition web và kiểm bằng fake: dev mặc định fake, cấu hình real phải ép Vertex cho sinh/embedding; mọi use case/cache/session/name
   con và recorder dùng PostgreSQL web, không rơi về SQLite hoặc `artifacts/phase_b/live.json`. Chặn provider/ADC/SMTP/Cloudinary trong test.
2. Chốt phần port cần ở `BuildDocument`/`DocumentPipeline` trước khi sửa tệp do phiên pha A sở hữu. Ghi đường dẫn, chữ ký, payload, test vào báo cáo;
   điều phối phối hợp Claude qua mục 8 bàn giao. Trong lúc chờ làm phần adapter và test độc lập, không sửa ké SA-54/56/57.
3. Usage checkpoint là snapshot luỹ kế từ đầu attempt/lease hiện tại, không chi lịch sử hoặc delta một bước; ghi delta vào ledger một lần. Giữ
   `usage_complete=false` khi thiếu; phần terminal chưa phân bổ có `step=null`, không chia đều. Không mất usage ở lỗi/huỷ/lease cũ, không publish lại.
4. Kiểm lại guard W-25 khi nối: confirm/cancel/terminal, receipt muộn, lease fence, không mail thành công sau huỷ được nhận trước. Đo thời gian tường
   từng bước bằng đồng hồ đơn điệu; phần chờ embedding phải có điểm đo thật hoặc ghi chưa đo.
5. Kiểm identity/cache doc-6 bằng bản sao manifest được phép. Có graph doc-6 không chứng minh cache dùng cho `u-<hash>`/pipeline mới; không dựng lại để
   lấy số phiên bản cũ, không nhập chi lịch sử. Dry-run phải dùng kho bản sao riêng; không xếp `dry_run` vào queue rồi coi course ready.
6. Chuẩn bị đề xuất riêng cho lượt một cuốn mới: tệp/SHA/số trang, cache hit/miss/unknown, số gọi sinh và embedding, USD/phút từng bước, trần và điểm
   dừng. **Chưa được chạy có tiền.** Chủ dự án phải duyệt tin nhắn cho đúng lượt/trần sau khi đọc dry-run. Phê duyệt phục hồi và SA-55 không chuyển sang W-15.

**Bàn giao giai đoạn 0 USD:** `report/w15-noi-bo-dung-that-2026-10-22.md` ghi adapter đã cài/phần port chờ, RED/GREEN, log/SQL/transport/recorder,
ma trận usage/cache, lệnh dry-run đã chạy hay chưa và bảng đề nghị. Mọi giá trị chưa biết phải ghi chưa biết. Không nhận vé W-15 đã hoàn tất khi mới
có adapter/fake hoặc dự toán.

## 3. Nhóm thiết kế — tiếp W-24, sửa báo cáo trước rồi hoàn thiện Cloud

Giữ `work/w24-figma-evidence` / `tmp/w24-figma-evidence`, nhận main mới trong đúng worktree trước khi tiếp. Đỉnh soát `78fb774`; mã local OS reduced-motion/token/guard đã được xác minh đạt:
32 test, 74/74 giá trị, bốn mutation raw bị bắt, prototype local 4/4, phá đường ảnh OS bị bắt. Không giao lại các lỗi này.

1. Commit sửa báo cáo đúng phạm vi trước: trạng thái link tham gia hỏng đang trỏ màn token xác minh/reset; nút huỷ không thay trạng thái cancelled;
   dark-mode cần đúng lộ trình/bài học/chat/quiz theo spec. Thiếu thì đánh dấu thiếu, không tick bằng chứng khác.
2. Bỏ claim JSON37 biến được đồng bộ trực tiếp với plugin26 biến. Phân biệt hợp đồng local, mã plugin và dữ liệu Cloud quan sát được.
   Điều phối đã đọc file Figma thật `UVhhlZnqdpV0JDcAHwJczo`: collection `VariableCollectionId:45:2`, một mode Light `45:0`, **0 variables**;
   metadata local `45:1` là khai báo, không phải receipt. Dùng Figma connector/plugin API đã kết nối để kiểm/xuất; không yêu cầu chủ dự án dán token
   vào chat hay mua gói chỉ để chứng minh dữ liệu canvas.
3. Bốn node prototype từng khai `401:1200`, `405:2100`, `410:3500`, `415:4200` không tồn tại khi kiểm độc lập. Frame thật `45:222` có69 hậu duệ,
   **0 node có reactions** và trang không có flow starting point; ảnh Cloud thấy nội dung bị cắt và chuỗi `&bull;` chưa giải mã. Sửa đúng native nodes,
   bindings, chế độ sáng/tối, thành phần và bốn luồng tương tác, rồi đọc lại/export bằng công cụ để có bằng chứng.
4. Sau bản sửa tài liệu, giao SHA để soát/nhận riêng mốc local nếu đủ. Phần hoàn thiện Cloud/trang-trạng thái còn lại tiếp cùng W-24;
   không chờ làm hết mọi màn mới được báo phần local đã sửa, không ghi toàn bộ W-22/W-24 đạt khi chưa đủ.
5. Ưu tiên thiết kế trạng thái W-11 trước, W-08 sau, khung chat/quiz tiếp theo. Checklist giữ từng trạng thái spec11, cỡ390/768/1280 và sáng/tối;
   ảnh/render/video phải gắn đúng trang/node. Video bấm bốn prototype Figma không được thay bằng bốn flow HTML local.

**Bàn giao:** cập nhật `report/w24-kiem-lai-2026-10-22.md` hoặc báo cáo mới có liên kết; giao SHA, checklist chính xác, Cloud receipt/export, mapping
Variables, ảnh/video bốn luồng và RED/GREEN. Bằng chứng độc lập của điều phối ở báo cáo nghiệm thu cùng ngày là căn cứ gỡ những câu khai cũ sai.

## 4. Phối hợp với Claude và quy tắc giữ nguyên

- Claude nghiệm thu/ghép làn SA/Pha B, điều phối nghiệm thu/ghép web. SA-52/53 đã ghép `66cd439`/`62dad5b`, SA-54 đã ghép `7d195db`;
  SA-56/57 chỉ được nhận sau phán xét/commit ghép của Claude, không suy từ bản bàn giao nhân viên.
  SA-57 đã được Claude soát/ghép rồi tạm revert `59e72a8` để giữ cửa sổ W-14; sau điều phối mở cửa, Claude revert chính commit revert để đưa lại.
  `focus_node_id` đã có trong W-09/spec; trả lời Claude ở mục8 và nhật ký10. Không mở lại câu hỏi chủ dự án đã duyệt.
- Cổng toàn repo/PostgreSQL chạy lần lượt giữa các làn, ghi cả lượt đỏ. WinError5 chạy lại cả cổng với basetemp mới; lặp lại thì đỏ, chờ SA-57,
  không skip hoặc hạ assertion. Khi main đổi nhận main/rerun theo quy trình; chỉ điều phối/Claude ghép đúng làn, `--no-ff`, đẩy ngay.
- Thư mục chung main; mỗi vé một worktree. Chỉ commit đường dẫn của mình, không chạm tệp dở của phiên Vertex/đánh giá SA19.
  Giữ mọi worktree/snapshot/ZIP, không dọn `tmp/t01a-clean-ff797eb`. Chép dữ liệu theo manifest/SHA, không junction/symlink/hardlink, không nạp live/tập giữ lại.
- UI tiếp tục token/logo Artboard9–28, Be Vietnam Pro, chuyển động120/200ms và reduced-motion; được dùng taste-skill theo spec. Không hiện dự toán
  tiền/token cho người học. Vertex giữ nguyên cho đến khi chủ dự án yêu cầu đổi để demo. Đợt giao này không cấp quyền gọi mô hình có tiền.

**Các lời giao trên được soạn để chủ dự án chuyển; điều phối chưa gửi tin nhắn sang phiên nhân viên.**
