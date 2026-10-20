# W-06 — Khoá mẫu, "Khoá học của tôi", `LearningGateway`, test người ngoài khoá

**Nguồn chân lý:** [spec chức năng](../../doc/web-chuc-nang-spec.md), mục 1 (`LearningGateway`), 3, 5, 7; [ADR 0020](../../doc/adr/0020-khoa-hoc-la-don-vi-chia-se-du-lieu-hoc-theo-nguoi-va-cuon.md);
[spec cơ sở dữ liệu](../../doc/web-co-so-du-lieu-spec.md), bảng `course`, `membership`; spec thiết kế, trang "Khoá học của tôi".
**Ai:** nhân viên lõi phụ trách backend/gateway; nhóm web phụ trách React và tích hợp · người soát kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** W-02, W-05 · **Trạng thái:** đủ điều kiện giao sau nghiệm thu 2026-10-20

**Đợt giao 2026-10-20:** W-02/W-05 đã nghiệm thu, không còn chặn. Cùng một vé đầu-cuối; backend xong riêng chưa tính cả vé đạt.
Mã mới ở `src/web/`; không mở thêm quyền sửa `src/doc2roadmap/` ngoài phạm vi W-05/W-13 đã được phép.
Migration dành tên `w06_0005`, nối `w03_0004` do web bàn giao trước; service/test/UI làm song song, ghép schema theo một tuyến.
Xem [nghiệm thu, phân việc và điểm kiểm](../../report/dieu-phoi-nghiem-thu-w02-w05-w24-2026-10-20.md).

**Khởi động lại sau sự cố, 2026-10-20:** W-03 đạt tại `9de8e75`, đã ghép `63f09ad`; schema head là `w03_0004`.
W-06 là ưu tiên tiếp theo, chưa được xem là đã hoàn tất. Nhánh lõi `work/w06-courses-gateway` ở `tmp/w06-courses-gateway` cần nhận main mới;
React làm nhánh/worktree riêng `work/w06-web` / `tmp/w06-web`, tích hợp thành một vé trước nghiệm thu.
Sáu graph dev tải được (doc-1 v8, doc-6 v29), không dựng lại hay dùng v45/v57 cứng.
Chốt trước cách kiểm `join-sample`: người tham gia lần đầu chưa là thành viên, trong khi test liệt kê mọi `{cid}` bên dưới chưa có ngoại lệ.
Nhóm đề xuất hợp đồng hẹp cho điều phối chốt; không tự bỏ guard hoặc mở mọi route.
Xem [kế hoạch và điểm nghiệm thu](../../report/dieu-phoi-nghiem-thu-w03-va-ke-hoach-2026-10-20.md),
[lời giao lõi/web](../../report/lenh-giao-viec-sau-w03-2026-10-20.md). Dữ liệu test chép theo manifest/SHA-256, không dùng liên kết, không dọn worktree/snapshot.

## Vì sao

Phần học (W-07…W-10) và chia sẻ (W-11) cần khoá học có thật để chạy. Khoá mẫu từ sáu cuốn phát triển cho khoá học ngay, không chờ khâu dựng (W-14,
W-15). Vé này cũng đặt **một chỗ duy nhất gọi Pha B**, cùng test chặn người ngoài khoá cho mọi route sau này.

## Cần làm

**Domain:** thực thể `Course`, `Membership`; thêm các hàng của bảng luật về thành viên và chủ khoá. Người không phải thành viên nhận `not_found`.

**`CourseService`:** `list_my_courses` (ba nhóm `owned`, `joined`, `samples`), `get_course`, `update_course` (tên, mô tả), `list_sample_courses`,
`join_sample_course`.
- Mỗi mục có tóm tắt "xong x/y" của người hỏi, lấy qua gateway từ `get_progress`. Pha B chưa có tiến độ (SA-34) thì để trống và ghi vào báo cáo.
- `resume`: module gần nhất của người hỏi, suy từ phiên gần nhất; không có thì module 1.

**Lệnh `web seed-samples`** (chỉ chạy khi `env = dev`; bản demo không có khoá mẫu, chủ dự án chốt 2026-10-18):
- Tạo khoá mẫu từ sáu cuốn phát triển, theo **danh sách cho phép viết trong mã**: doc-1, nhap-mon-ml, naive-bayes, doc-6, xstk-ch3-1, doc-4.
- `published_graph_version` là bản A10 hoàn tất mới nhất của mỗi cuốn; chủ khoá là admin chạy lệnh.
- Tải PDF gốc của cuốn lên Cloudinary qua `MediaStore`; PDF nhap-mon-ml đã được khôi phục và kiểm trong [nghiệm thu W-13](../../report/dieu-phoi-kiem-lai-w13-w24-2026-10-19.md), không còn ghi thiếu PDF này.
  Test dùng MediaStore giả; ảnh công thức và media làm ở W-08.
- Mọi `doc_id` khác bị từ chối. Test dùng một `doc_id` giả có dạng giống tập giữ lại; không dùng tên thật.

**`LearningGateway`:**
- Mỗi hàm tải khoá học, kiểm thành viên, rồi gọi Pha B với `owner = actor.user_id`, `doc_id = course.doc_id`, `graph_version =
  course.published_graph_version`.
- Đồ thị của mỗi `(doc_id, graph_version)` nạp một lần và giữ trong bộ nhớ tiến trình.
- Nối các use case qua port để chúng và spend guard dùng cùng `PostgresPhaseBStore` đã nghiệm thu W-05.
  `PhaseBRuntime` của CLI hiện tự tạo kho JSON; chỉ gán lại trường store ngoài composition không thay các phụ thuộc con đã giữ kho cũ.
  Kiểm đọc/ghi PostgreSQL thật từ kết nối độc lập, không chỉ assert kiểu của thuộc tính.
- Composition tạm truyền cấu hình Vertex AI cho runtime Pha B, cả mô hình sinh lẫn embedding (chủ dự án cập nhật 2026-10-19). Thông tin xác thực chỉ ở
  backend theo spec chức năng mục 1; chuyển sang Developer API khi chủ dự án yêu cầu chuẩn bị demo. Các test gateway dùng đồ giả, không gọi API thật.
- Ghi `membership.last_active_at` khi cũ hơn 5 phút.
- Vé này cài khung cùng một hàm thật `get_roadmap` (danh sách module, tên, mô tả, khái niệm theo thứ tự). Các hàm học khác cài ở W-07…W-10.

**HTTP:** `GET /courses`, `GET /courses/{cid}`, `PATCH /courses/{cid}`, `POST /courses/{cid}/join-sample`, `GET /courses/{cid}/roadmap`.

**Test người ngoài khoá:**
- Một test tự liệt kê **mọi** route có `{cid}` trong ứng dụng FastAPI, gọi bằng tài khoản không phải thành viên, và kỳ vọng `not_found`.
- Route mới ở các vé sau tự vào test này. Route nào cố ý mở cho người ngoài (hiện không có) phải vào một danh sách miễn trừ ghi rõ lý do.

**Di trú:** `course`, `membership`. Ràng buộc đúng một chủ mỗi khoá.

**Giao diện:** trang "Khoá học của tôi" với ba nhóm; thẻ khoá học (tên, chủ khoá, số module, "xong x/y", nút "Học tiếp"); trạng thái rỗng "Chưa có khoá học
— thử một khoá mẫu"; nút tham gia khoá mẫu.

## Tiêu chí nghiệm thu

Mỗi test thấy đỏ trước trên bản sai:
- [ ] Test liệt kê route: thêm thử một route `{cid}` không gọi kiểm thành viên thì test đỏ.
- [ ] Gateway: thân yêu cầu có `owner` khác thì bị bỏ qua; bản ghi Pha B mới có `owner` là người đăng nhập.
- [ ] Use case và spend guard dùng kho PostgreSQL thật; kết nối độc lập quan sát đúng bản ghi/usage, không rơi về JSON hay kho bộ nhớ.
- [ ] Test nối dây runtime Pha B theo cấu hình tạm thời: bản giả sinh/embedding ghi nhận `transport=vertex`; cố ý truyền `developer_api` thì test đỏ.
  Không dùng mạng; chưa tự chuyển transport trước chỉ thị chuẩn bị demo.
- [ ] `seed-samples` từ chối `doc_id` ngoài danh sách cho phép, kể cả `doc_id` giả có dạng giống tập giữ lại; từ chối chạy khi `env = prod`.
- [ ] `env = prod` không có khoá mẫu nào thì giao diện ẩn nhóm "Khoá học mẫu"; trạng thái rỗng mời tải giáo trình hay nhập link mời.
- [ ] Không chèn được chủ thứ hai cho cùng một khoá; tạo khoá mà lỗi ở bước chèn chủ thì không còn hàng `course`.
- [ ] Tham gia khoá mẫu hai lần không tạo hai hàng `membership`.
- [ ] Ví dụ JSON thật của `GET /courses` và `GET /courses/{cid}/roadmap` cho doc-1; ảnh chụp trang "Khoá học của tôi" có và không có khoá học.

## Ngoài vé

Trang lộ trình đầy đủ (W-07). Xoá khoá (W-20). Tạo khoá từ tệp tải lên (W-14).
