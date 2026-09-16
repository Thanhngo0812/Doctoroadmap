# 01 — Tách cơ chế gọi mô hình dùng chung

**What to build:** 2a và 2b dùng **chung một chỗ** cho các việc quanh mỗi lời gọi mô hình: gom lô, cache theo
hash đầu vào (gồm cả luật coi là cache miss khi đầu ra cũ không qua nổi validator hiện tại), đúng **một lượt
retry** kèm thông báo lỗi, ghi nhật ký từng lượt thử, và đếm chỉ số. Sau vé này, A4 chạy **y hệt** như trước,
còn vé 06 và 07 không phải chép lại vòng lặp đó lần nữa.

Đây là prefactor: làm cho việc sau dễ, chứ không thêm hành vi nào.

**Blocked by:** None — bắt đầu được ngay.

**Status:** ready-for-agent

- [ ] `prompt_hash` của cả bốn khâu A4 không đổi; test hash vàng xanh mà không sửa số nào.
- [ ] Chạy lại A4 cho bốn tài liệu khi chặn mạng: `reused=true`, 0 lời gọi, không sinh phiên bản mới.
- [ ] Fixture hợp đồng A3 và A4 phát lại được, **không ghi lại**.
- [ ] Module chung có test riêng cho: cache trúng; cache miss vì validator đổi; retry đúng một lượt rồi dừng;
      nhật ký ghi đủ mọi lượt thử kể cả lượt hỏng.
- [ ] Không thêm phụ thuộc mới.
- [ ] Toàn bộ test xanh khi chặn mạng.
- [ ] Nộp danh sách đột biến đã thử, tối thiểu: bỏ lượt retry, bỏ ghi lượt hỏng vào nhật ký, cho cache bỏ qua
      validator, gom lô sai thứ tự.
