# Soát W-17.1 lần 12

Ghim bàn giao a07bff3f604c253cad030b45f744409ab7897bee, nguồn tác giả e7d54a1a, candidate độc lập34c1712f. **Đạt mốc backend W-17.1 sau cổng cuối ghi trong gate-summary.json; toàn W-17 chưa đóng.**

CORE-R11-01 sửa đúng: chỉ gọi count guard khi was_active_admin và kết quả không còn active/admin. Không áp cho người đã disabled; enable+demote cũng không loại admin active. Không bỏ lock, live authorization, bootstrap guard, transaction/audit/session. Không thêm dependency hoặc endpoint trong bản vá.

Độc lập đặt nguyên admin.py từ862dd805 lên candidate:hai probe HTTP/PG đỏ đúng409,0setup error. Bỏ target.status khỏi was_active_admin:6 assertionfail/2pass; bỏ countguard:1assertionfail/7pass. Khôi phục byte/SHA trước GREEN:79 ca W-17+2 probe độc lập =81pass. SQL qua connection độc lập xác nhận role/status/quota, registry giữ A và phiên A dùng được, phiên B vẫn chết sau bật lại.

Lượt đầu2setup errors vì Docker Desktop tắt, không phải RED hành vi. Giữ log, bật lại Docker Desktop hidden và chỉ up db-test hiện có; không xoá volume/DB người khác. Retry label/basetemp riêng.

380/380 manifest cũ và209/209 manifest lượt sửa khớp bytes/SHA blob Git. Hai hàng CRLF/LF stale đã sửa đúng. Source e7d54a1a→delivery không thay src/scripts. Migration duy nhất w17_0009 nối w12_0008; public DTO is_first_admin nullable, protected_admin/bootstrap_required giữ field lỗi. Root không chạy migration hoặc CLI trên DB dùng chung.

Năm trục: đúng chuyển trạng thái và rollback; sửa nhỏ/dễ đọc; giữ port/service/store hiện hữu; quyền Actor live/metadata whitelist và query tham số hoá; list bounded không thêm fanout. Các guard registry/trigger/CLI/W04 hồ sơ-mật khẩu và không lộ chat/quiz/tài liệu riêng được giữ, kiểm lại qua bộ test W-17 và cổng toàn repo. Không có Required mới.

Backend có GET/PATCH admin/users và GET admin/audit. Chưa có React admin, admin/builds/sample mutation/chi/validation/retry/cancel/W20delete APIs. Việc nhận backend gỡ chặn React Người dùng/Nhật ký; W17.2 metadata/mẫu có thể đi song song.
