# W-06 — Hợp đồng và triển khai backend/gateway

Ngày 2026-10-20. Nhánh `work/w06-courses-gateway`, worktree `tmp/w06-courses-gateway`. Đã kiểm sạch và nhận main `06c98ea` (W-03 ghép `63f09ad`). **Đây là hợp đồng dự kiến để web bắt đầu; JSON trong mục này là mẫu, chưa phải kết quả API đã chạy.** Chưa nghiệm thu W-06 đầu-cuối.

## Hợp đồng HTTP v1 — bản 1

Tiền tố `/api/v1`. Dùng cookie W-02 và `Origin` + `X-CSRF-Token` cho PATCH/POST. Chủ thể luôn lấy từ phiên đăng nhập. Các trường `owner`, `owner_id`, `doc_id`, `graph_version` trong body không quyết định quyền hay phạm vi dữ liệu.

### GET /courses — 200, mẫu

```json
{"owned":[],"joined":[],"samples":[{"course_id":"00000000-0000-4000-8000-000000000006","doc_id":"doc-1","title":"Đại số tuyến tính","description":"Khoá mẫu phát triển","status":"ready","is_sample":true,"published_graph_version":8,"role":null,"owner":{"user_id":"00000000-0000-4000-8000-000000000001","display_name":"Quản trị"},"module_count":35,"member_count":null,"progress":null,"resume":null}]}
```

Ba nhóm luôn tồn tại. `samples` chỉ có ở dev, chỉ chứa mẫu chưa tham gia; prod trả `samples: []`. Mẫu chưa tham gia chỉ hiển thị metadata, không đọc graph/Pha B để tính tiến độ. `module_count` lưu từ graph khi tạo mẫu. `member_count` chỉ có giá trị số khi actor là chủ khóa; người khác nhận null. `role` là `owner`/`learner`/null. `progress` của thành viên: `{"learned":0,"total":223}`. `resume` của thành viên: `{"module_id":"module_001"}` hoặc null nếu chưa ready/không có module. Resume lấy phiên module mới nhất còn giải được trong graph, rồi tiến độ gần nhất, rồi module đầu.

### GET /courses/{cid} — 200, mẫu sau tham gia

```json
{"course_id":"00000000-0000-4000-8000-000000000006","doc_id":"doc-1","title":"Đại số tuyến tính","description":"Khoá mẫu phát triển","status":"ready","is_sample":true,"published_graph_version":8,"role":"learner","owner":{"user_id":"00000000-0000-4000-8000-000000000001","display_name":"Quản trị"},"module_count":35,"member_count":null,"progress":{"learned":0,"total":223},"resume":{"module_id":"module_001"}}
```

Chưa tham gia kể cả mẫu: GET detail/roadmap trả 404; metadata mẫu lấy từ danh sách. Admin không có ngoại lệ học ngoài membership.

### PATCH /courses/{cid} — 200

Body `{"title":"Tên mới","description":"Mô tả mới"}`; một hoặc cả hai trường. Title 1–120 ký tự sau trim, description tối đa 1.000 ký tự. Chỉ chủ khóa được sửa; trả cùng shape detail. Thành viên thường 403; người ngoài 404. Body có trường khác bị bỏ qua, không được thay chủ/doc/version.

### POST /courses/{cid}/join-sample — 200

Body `{}`; không nhận user_id từ client. Tài khoản active đã đăng nhập (không bắt xác minh email) tham gia mẫu ready ở dev được ngay, chưa cần membership. Trả cùng shape detail với `role: "learner"`; chủ mẫu gọi lại giữ `role: "owner"`. Gọi lặp không tạo membership mới. Khóa riêng tư hoặc prod: 404. Khách không được tham gia (bị auth/CSRF từ chối, không thay đổi DB). Đầy khóa: 409 `course_full`.

### GET /courses/{cid}/roadmap — 200, mẫu nhỏ minh họa shape

```json
{"course_id":"00000000-0000-4000-8000-000000000006","doc_id":"doc-1","graph_version":8,"modules":[{"module_id":"module_001","index":0,"title":"Module đầu","description":"Mô tả từ graph","concepts":[{"node_id":"node-example","name":"Khái niệm mẫu"}]}]}
```

Thứ tự module theo `index`, khái niệm theo thứ tự `node_ids` đã công bố của module. Nội dung lấy từ graph, không tự gọi mô hình để đặt tên. Khóa chưa ready: 409 `conflict`.

### Lỗi — dùng nguyên envelope W-01/W-02

```json
{"error":{"code":"not_found","message":"Không tìm thấy nội dung yêu cầu","retry_after":null,"ref":null}}
```

401 `unauthenticated`; 403 `account_disabled`/`forbidden`/`csrf_failed`; 404 `not_found`; 409 `conflict`/`course_full`; 422 `validation`. Không trả chi phí/usage cho người học. Test tự duyệt tất cả route `{cid}`, không whitelist bỏ qua join-sample; nhắm khóa riêng tư, actor ngoài phải nhận đúng 404 envelope.

## Schema, ownership, visibility và phân vùng

- Migration duy nhất `w06_0005 → w03_0004`: bảng `course`, `membership`. Khóa/membership chủ tạo cùng transaction. PK membership `(course_id, account_id)` chống tham gia trùng; partial unique owner theo course. Chủ khóa là admin chạy seed, cũng có membership owner. Tài khoản admin khác không tự được học.
- Mẫu là khóa bình thường có `is_sample=true`; không phải bản sao dữ liệu học. Dữ liệu cá nhân vẫn theo `(actor.user_id, doc_id)` trong PostgreSQL Pha B. Danh mục mẫu dev không cấp quyền nội dung trước join.
- Backend sở hữu `src/web/backend/wayfinder/{application,domain,infrastructure,api}/` liên quan course/gateway, composition, CLI seed, migration và test backend. Web sở hữu `src/web/frontend/`. Không cùng sửa composition/migration; tích hợp qua commit/backend contract. Không sửa `src/doc2roadmap/`, vé, kế hoạch hoặc handoff.
- Fixture: chép từng tệp theo manifest cố định và kiểm SHA-256 nguồn/đích, từ chối mọi reparse point/symlink/hardlink. Không đọc/copy `artifacts/phase_b/live.json`. Không chạm t01a hay dọn snapshot/worktree.

## Các lát thực hiện

1. Khóa/membership + một mẫu tham gia được qua HTTP/PostgreSQL → kiểm rollback, unique owner, join lặp, mọi route private và auth.
2. Gateway kiểm membership trước graph; composition Pha B/spend guard dùng một store PostgreSQL → đọc/ghi từ connection độc lập, cache graph theo doc/version, owner giả bị bỏ qua, Vertex giả ghi nhận đúng transport.
3. Seed sáu cuốn dev qua MediaStore giả, JSON thật doc-1, RED/GREEN guard/owner/store/transport, full gate và bàn giao cho web/điều phối; không tự đóng vé đầu-cuối.

## Điểm cần ghi nhận về schema

Bảng `build`/`upload` chưa có ở head W-03. W-06 sẽ giữ `build_id` nullable dạng UUID, chưa gắn FK vào bảng chưa tồn tại; FK cần thêm khi W-14 đưa bảng build vào. PDF mẫu cần lưu public_id MediaStore; lưu `source_public_id` nullable ở course cùng `module_count` metadata để danh mục chưa tham gia không tải graph. Không tạo trước toàn bộ bảng upload/build ngoài vé.

## Kết quả thực hiện

Đang triển khai. Chưa có lời gọi mô hình/media thật; chưa chạy seed vào DB phát triển.
