# W-06 — Khoá mẫu, "Khoá học của tôi", `LearningGateway`, test người ngoài khoá

**Nguồn chân lý:** [spec chức năng](../../doc/web-chuc-nang-spec.md), mục 1 (`LearningGateway`), 3, 5, 7; [ADR 0020](../../doc/adr/0020-khoa-hoc-la-don-vi-chia-se-du-lieu-hoc-theo-nguoi-va-cuon.md);
[spec cơ sở dữ liệu](../../doc/web-co-so-du-lieu-spec.md), bảng `course`, `membership`; spec thiết kế, trang "Khoá học của tôi".
**Ai:** nhóm web · người soát kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** W-02, W-05 · **Trạng thái:** ready-for-agent

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
- Tải PDF gốc của cuốn lên Cloudinary qua `MediaStore` (5/6 cuốn có PDF, đều ≤ 3,2 MB; nhap-mon-ml không có PDF gốc). Ảnh công thức và media làm ở W-08.
- Mọi `doc_id` khác bị từ chối. Test dùng một `doc_id` giả có dạng giống tập giữ lại; không dùng tên thật.

**`LearningGateway`:**
- Mỗi hàm tải khoá học, kiểm thành viên, rồi gọi Pha B với `owner = actor.user_id`, `doc_id = course.doc_id`, `graph_version =
  course.published_graph_version`.
- Đồ thị của mỗi `(doc_id, graph_version)` nạp một lần và giữ trong bộ nhớ tiến trình.
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
- [ ] `seed-samples` từ chối `doc_id` ngoài danh sách cho phép, kể cả `doc_id` giả có dạng giống tập giữ lại; từ chối chạy khi `env = prod`.
- [ ] `env = prod` không có khoá mẫu nào thì giao diện ẩn nhóm "Khoá học mẫu"; trạng thái rỗng mời tải giáo trình hay nhập link mời.
- [ ] Không chèn được chủ thứ hai cho cùng một khoá; tạo khoá mà lỗi ở bước chèn chủ thì không còn hàng `course`.
- [ ] Tham gia khoá mẫu hai lần không tạo hai hàng `membership`.
- [ ] Ví dụ JSON thật của `GET /courses` và `GET /courses/{cid}/roadmap` cho doc-1; ảnh chụp trang "Khoá học của tôi" có và không có khoá học.

## Ngoài vé

Trang lộ trình đầy đủ (W-07). Xoá khoá (W-20). Tạo khoá từ tệp tải lên (W-14).
