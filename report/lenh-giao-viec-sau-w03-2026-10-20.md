# Lời giao việc sau nghiệm thu W-03 — 2026-10-20

Ba đoạn dưới dành cho chủ dự án chuyển đến từng nhóm. Đây là kế hoạch tiếp nhận lại sau khi dự án dừng vì artifact; không khẳng định W-06 đã làm hoặc đã nghiệm thu. **W-03 đã đạt và ghép `63f09ad`, đã đẩy GitHub**; xem [biên bản](dieu-phoi-nghiem-thu-w03-va-ke-hoach-2026-10-20.md). Các nhóm nhận main mới trước khi bắt đầu.

## Gửi nhóm lõi — backend/gateway W-06

Nhận W-06 theo `task/web/W-06-khoa-mau-khoa-hoc-cua-toi-gateway.md`. W-02/W-05/W-13 đã đạt; W-03 đã được điều phối kiểm và mốc ghép ghi trong báo cáo trên. Đọc `doc/quy-trinh-nhanh-va-ghep-main.md`, `doc/du-lieu-phat-trien-va-fixture.md` và báo cáo trước khi làm.

1. Mở đúng `C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w06-courses-gateway`, nhánh `work/w06-courses-gateway`; kiểm status, giữ/commit riêng mã dở nếu có rồi nhận main mới. Không đổi nhánh thư mục chung. Không tự dọn bất kỳ worktree nào.
2. Đầu ra đầu tiên là hợp đồng W-06 để web dùng: JSON thật/mẫu có nhãn rõ cho danh sách khoá, chi tiết, tham gia mẫu, roadmap và lỗi; schema/ownership/visibility của khoá mẫu; phân vùng tệp. Test tự liệt kê mọi `{cid}` nhắm khoá riêng tư: người ngoài nhận `not_found`, kể cả `join-sample`. Test riêng cho tài khoản đăng nhập tham gia mẫu ở dev khi chưa có membership; khách chưa đăng nhập không được tham gia. Không miễn route khỏi bộ kiểm hay bỏ kiểm thành viên ở gateway.
3. Làm `CourseService`, `LearningGateway`, `course`/`membership`, migration đúng `w06_0005` nối `w03_0004`. Đúng một chủ, tạo khoá và membership chủ cùng transaction, tham gia lặp không nhân đôi. Mã mới chỉ trong `src/web/`; lỗi ở lõi thì ghi yêu cầu, không tự mở quyền sửa `src/doc2roadmap/`.
4. Gateway lấy owner từ actor, kiểm quyền trước khi đọc graph/gọi Pha B; use case và spend guard dùng cùng PostgreSQL thật, chứng minh bằng kết nối độc lập. Không chỉ thay thuộc tính store của runtime CLI đang giữ JSON ở phụ thuộc con. Backend tạm dùng Vertex cho sinh/embedding; test giả, 0 gọi mạng/0 USD.
5. Sáu graph phát triển tải được; doc-1 hiện v8, doc-6 v29. Không dựng lại chỉ để lấy lại số v45/v57. Seed chỉ allowlist sáu cuốn trong vé, chỉ ở dev; test dùng MediaStore giả. Dữ liệu test lấy bản sao cố định theo manifest, kiểm SHA-256 từng tệp, tuyệt đối không junction/symlink/hardlink và không nhập `artifacts/phase_b/live.json`.
6. Chứng minh test đỏ khi route mới bỏ guard, giả owner, dùng sai kho/transport; chạy PostgreSQL bắt buộc qua runner. Phối hợp web làm một khoá mẫu tham gia được đầu-cuối trước rồi hoàn thiện phần còn lại. Backend riêng xong chưa đóng W-06.

Bàn giao: `report/w06-backend-gateway-2026-10-20.md` (đổi ngày thực tế nếu khác), commit chính xác, hợp đồng JSON, tuyến migration, kết quả RED/GREEN, log/JUnit và giới hạn chưa xong. Không sửa vé/kế hoạch/handoff; không tự ghép main. Không đụng `tmp/t01a-clean-ff797eb`, snapshot/ZIP hay dữ liệu giữ lại.

## Gửi nhóm web — React và tích hợp W-06

W-03 đã được kiểm; xem mốc ghép, cổng và ghi chú trong `report/dieu-phoi-nghiem-thu-w03-va-ke-hoach-2026-10-20.md`. Việc tiếp theo ưu tiên là **React và tích hợp W-06**, cùng backend/gateway do nhóm lõi làm; không tính vé đạt khi chỉ có giao diện mock.

1. Giữ nguyên worktree W-03 để đối chiếu. Tạo nhánh/worktree riêng một cấp `tmp/w06-web` từ main mới, ví dụ nhánh `work/w06-web`; không dùng chung nhánh backend, không sửa thư mục chung, không tự ghép main.
2. Đọc vé W-06, spec chức năng/CSDL/thiết kế và hợp đồng backend do lõi bàn giao. Chốt shape JSON/lỗi/route trước khi nối; nếu làm giao diện bằng mock thì ghi rõ, sau đó bắt buộc thay bằng API thật trước nghiệm thu. Đầu mối tích hợp W-06 là điều phối, không để hai nhóm cùng sửa một tệp migration/composition.
3. Làm trang “Khoá học của tôi”: nhóm owned/joined/samples, thẻ khoá, tham gia mẫu, học tiếp theo hợp đồng; đủ đang tải/rỗng/lỗi, sáng/tối. Prod không có khoá mẫu thì ẩn nhóm mẫu, lời mời tải giáo trình/nhập link đúng spec. Trang lộ trình đầy đủ thuộc W-07; không tự mở rộng vé.
4. Giao diện đẹp, chỉn chu, đúng token, logo Artboard 9–28 và motion; được dùng bộ taste-skill chủ dự án nạp, ghi skill/điều đã áp dụng. Có focus/keyboard, vùng bấm mobile theo spec và `prefers-reduced-motion`. Không tự đợi W-24 hoàn tất hết mới làm W-06 theo spec hiện hành.
5. Kiểm một tài khoản thật tham gia mẫu và thấy khoá trong danh sách qua HTTP + PostgreSQL thật, dùng mô hình/Mailer/MediaStore giả; chặn người ngoài và không nhận owner tuỳ ý từ body. Không gọi mô hình, không gửi thư thật, không tự đưa media lên Cloudinary. Doc-1 hiện v8; không khóa v45/v57 hoặc dùng cache CLI thay PostgreSQL.
6. Chạy test/build React và cổng đầy đủ trong worktree tích hợp nhận cả hai nhánh; dữ liệu chỉ chép từ snapshot theo manifest + SHA-256, không liên kết. Giao ảnh 390/1280 sáng/tối, kiểm 768, video tương tác, audit console/network/accessibility và JSON thật cho React/API.

Bàn giao: `report/w06-react-tich-hop-2026-10-20.md` (đổi ngày thực tế nếu khác), commit, ảnh/video, lệnh/kết quả kiểm và phần backend đang phụ thuộc. W-04 đủ điều kiện nhưng xếp sau tích hợp W-06 nếu chỉ có một phiên web; chỉ làm song song khi có người riêng và phân vùng AccountService. Không sửa vé/kế hoạch/handoff; không dọn worktree/snapshot, không đụng `tmp/t01a-clean-ff797eb`.

## Gửi nhóm thiết kế — hoàn tất W-24, ưu tiên hỗ trợ W-06

Tiếp tục cùng W-24; không giao lại các lỗi đã đóng và không ghi W-22/W-24 hoàn tất chỉ vì có HTML/JSON local. Đọc vé W-24, spec thiết kế, báo cáo nghiệm thu W-03 và các giới hạn còn lại.

1. Mở `C:/Users/ngoco/Desktop/Doctoroadmap/tmp/w24-figma-evidence`, nhánh `work/w24-figma-evidence`; giữ/commit riêng phần đang làm rồi nhận main mới. Các helper/preview cũ có lịch sử mang theo W-03; khi hợp nhất không khôi phục câu TTL sai.
2. Điều phối đã sửa hai bản local tại `9de8e75`: link reset **60 phút**, xác minh **24 giờ**. Cập nhật phần tương ứng trong Figma thật; không đổi backend về 15 phút.
3. Giao Variables xuất thật có nguồn gốc từ Figma, bảng tên/giá trị đối chiếu CSS; JSON local tái xuất không tính là Figma export. Giao bảng đủ trang/trạng thái/node ở 390/1280 sáng/tối, ghi nhận 768. Ưu tiên ngay trang W-06 cùng thẻ khoá/rỗng/tải/lỗi để React tích hợp; sau đó trang hồ sơ W-04 theo spec.
4. Bốn luồng prototype phải bấm được trong Figma, có node bắt đầu, link và video. Kiểm clipboard/citation/scroll/reduced-motion bằng kết quả quan sát được; cố ý bỏ handler phải đỏ đúng bước. Audit HTML 4/4 và phép phá accordion bị bắt là bằng chứng cải thiện local, chưa thay bốn prototype Figma.
5. Helper không được báo nối reaction thành công nếu API không sẵn sàng hoặc nối thất bại; ghi đúng phần đã tạo/phần cần làm thủ công. Không dùng thông báo helper làm bằng chứng đã kiểm Figma.
6. Giao diện đẹp, nhất quán, hiệu ứng đúng token 120/200 ms và giảm chuyển động; được dùng taste-skill chủ dự án nạp, ghi rõ quyết định áp dụng. Không thiết kế lại thương hiệu hoặc làm ứng dụng React trong vé này.

Bàn giao: cập nhật `report/w24-bo-sung-w22-2026-10-19.md` hoặc báo cáo mới ghi ngày thật, kèm commit, Variables/provenance, bảng checklist→node→ảnh/video, link bốn prototype và log phép phá guard. Không tự đánh dấu vé đạt, không sửa kế hoạch/handoff, không tự ghép main. Không dọn worktree/snapshot hay đụng `tmp/t01a-clean-ff797eb`.
