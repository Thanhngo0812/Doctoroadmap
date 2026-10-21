# W-14 — backend/worker giả, 2026-10-21

## Hợp đồng bàn giao trước triển khai

Nền main `eb6af08`; nhánh `work/w14-build-worker`, worktree `tmp/w14-build-worker`.
W-06 đã nghiệm thu/ghép `dc41ee8`. Đã đọc bàn giao W-07 `cd1ecb8`: không thêm
migration, không sửa composition; chưa tự nhập nhánh W-07. Giữ các worktree cũ.

### HTTP `/api/v1`, phiên cookie và CSRF hiện có

| Route | Yêu cầu | Phản hồi |
|---|---|---|
| POST /uploads | multipart `file`, `rights_confirmed=true` | upload-1 + build-1; chưa chạy |
| GET /uploads/{id} | người tải | upload-1, build hiện tại |
| POST /uploads/{id}/build | `{"title":"Tên khoá do người dùng đặt"}` xác nhận rõ ràng | build-1; idempotent theo upload |
| GET /builds/{id} | chủ một upload liên kết bản dựng | build-1 theo course của actor |
| POST /builds/{id}/cancel | `{}` | build-1; chỉ người yêu cầu chạy được huỷ việc dùng chung |
| POST /builds/{id}/retry | `{}` | build-1; chỉ lỗi retryable, không trừ lượt lại |
| GET /me/usage | actor | quota lượt/tháng; không trả tiền/token |

Khách 401, disabled 403, upload/build của người khác 404. Admin không được đọc
upload/build người khác qua các route người dùng này. Không nhận owner/doc/version
từ body. Người chưa xác minh email vẫn được tải/xác nhận. `rights_confirmed` bắt buộc.

Ví dụ JSON **mẫu thiết kế**, chưa phải log HTTP:

```json
{"contract_version":"upload-1","upload_id":"<uuid>","original_name":"Dai so.pdf","kind":"pdf","size_bytes":1234,"page_count":2,"build":{"contract_version":"build-1","build_id":"<uuid>","course_id":"<uuid>","status":"awaiting_confirmation","step":null,"step_index":0,"step_count":4,"started_at":null,"finished_at":null,"confirmation_expires_at":"2026-10-24T00:00:00Z","cancel_requested":false,"can_cancel":true,"can_retry":false,"error":null}}
```

Sau POST xác nhận, cùng build_id/course_id có status queued; worker báo reading /
doc_reading, running / concepts → graph → learning_prep, rồi succeeded. Lỗi đọc
ban_quet/ngon_ngu_khong_ho_tro/chu_loi: rejected. Lỗi mạng: failed/retryable.
Không xác nhận đủ 72 giờ: cancelled, error confirmation_expired, không trừ lượt.
Lỗi HTTP dùng envelope hiện có `{"error":{"code":"file_invalid","message":"…","retry_after":null,"ref":null}}`.
Không public_id, đường dẫn nội bộ, chi phí, token hay dự toán trong các DTO người dùng.

### Ownership, dùng chung và idempotency

Mỗi lần tải hợp lệ tạo upload và course riêng, đúng một owner membership cùng
transaction. SHA-256 → doc_id u- + 20 hex, pipeline_version do server cấu hình.
Cùng tài liệu/pipeline dùng chung build đang dở hoặc thành công. Khoá DB theo
doc/pipeline và unique partial index bảo vệ đồng thời. POST xác nhận lặp không
tạo course/build thứ hai. Upload mới là một lần tải mới; không hứa dedup upload.

Build đang chờ: actor xác nhận đầu tiên thành requested_by, chịu quota/usage.
Actor khác xác nhận cùng việc chỉ gắn course riêng, không trừ lượt. Build thành
công dùng lại: course ready theo đúng graph/module metadata đã lưu, không chạy
runner và không nhập chi lịch sử. Một actor không có quyền huỷ/retry việc đang
chạy do actor khác yêu cầu; UI dùng can_cancel/can_retry.

### Schema và tuyến migration

Đề xuất tuyến hiện tại: w06_0005 → **w14_0006**. Chưa có migration W-11 trong
main/nhánh hiện thấy; người soát chốt successor theo thứ tự ghép W-11/W-14,
không tạo hai head. Ghi ở đây cho chủ dự án chuyển, không nhắn phiên khác.

Tạo upload/build/media_asset; course.build_id có FK build, upload.course_id
liên kết nguồn PDF/DOCX riêng của course; khoá mẫu vẫn source_public_id và null
build. Bổ sung bản ghi attempt/checkpoint để fence worker cũ và chống cộng usage
hai lần. Không sửa migration W-06.

### Điểm cần chốt / giới hạn port

- **Chủ dự án đã chốt trong phiên:** được đặt tên khoá trước khi index. Tên điền
  sẵn từ tên tài liệu; POST xác nhận nhận title (1–120 ký tự sau trim), ghi tên
  trước khi queued trong cùng transaction. Không truyền title vẫn giữ tên mặc định.
  Xác nhận lặp không đổi tên lần đầu; muốn sửa tiếp dùng PATCH course sẵn có.
- Vé ghi PDF 400 trang, spec chức năng và WebSettings ghi build_max_pages mặc
  định không giới hạn. Theo nguồn chân lý spec: giữ mặc định None, kiểm trần khi bật.
- BuildResult W-13 có tổng usage của lần chạy; progress không bắt buộc usage từng
  bước. Ghi từng bước khi có số thực; phần tổng chưa phân bổ ghi step=null, không
  bịa chia tiền đều. Báo rõ khả năng phân bổ khi nối W-15; không sửa lõi.
- Bộ dựng thật, React W-14 và nghiệm thu toàn vé chưa nằm trong bàn giao backend này.

## Kế hoạch và phép kiểm

1. Migration + upload/xác nhận → kiểm tệp/quyền, atomic owner/FK, chưa chạy trước xác nhận.
2. Queue/worker → hai worker, dedup, timeout/reclaim một lần, quota/cap, huỷ theo bước.
3. Callback W-13 → SQL độc lập đối chiếu số khác 0 ở success/error/cancel, thiếu số giữ false.
4. Copy giả → allowlist/manifest/hash, không liên kết; đúng graph/media, dọn tệp do worker sở hữu.
5. RED/GREEN/mutation + cổng qua runner trên commit, báo cáo log/JUnit và React còn chờ.
