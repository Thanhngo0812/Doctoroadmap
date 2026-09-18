# 01 — Tách cơ chế gọi mô hình dùng chung

**What to build:** 2a và 2b dùng **chung một chỗ** cho các việc quanh mỗi lời gọi mô hình: gom lô, cache theo
hash đầu vào (gồm cả luật coi là cache miss khi đầu ra cũ không qua nổi validator hiện tại), đúng **một lượt
retry** kèm thông báo lỗi, ghi nhật ký từng lượt thử, và đếm chỉ số. Sau vé này, A4 chạy **y hệt** như trước,
còn vé 06 và 07 không phải chép lại vòng lặp đó lần nữa.

Đây là prefactor: làm cho việc sau dễ, chứ không thêm hành vi nào.

**Blocked by:** None — bắt đầu được ngay.

**Status:** done — 2026-09-16

- [x] `prompt_hash` của cả bốn khâu A4 không đổi; test hash vàng xanh mà không sửa số nào.
- [x] Chạy lại A4 cho bốn tài liệu khi chặn mạng: `reused=true`, 0 lời gọi, không sinh phiên bản mới.
- [x] Fixture hợp đồng A3 và A4 phát lại được, **không ghi lại**.
- [x] Module chung có test riêng cho: cache trúng; cache miss vì validator đổi; retry đúng một lượt rồi dừng;
      nhật ký ghi đủ mọi lượt thử kể cả lượt hỏng.
- [x] Không thêm phụ thuộc mới.
- [x] Toàn bộ test xanh khi chặn mạng.
- [x] Nộp danh sách đột biến đã thử, tối thiểu: bỏ lượt retry, bỏ ghi lượt hỏng vào nhật ký, cho cache bỏ qua
      validator, gom lô sai thứ tự.

## Feedback nghiệm thu

- Cơ chế chung nằm ở `src/doc2roadmap/application/model_calls.py`; A4, pass chính và pass phụ cùng dùng
  `ModelJob`/`run_model_jobs`. Riêng prefactor này không thêm phụ thuộc; `leidenalg` được thêm độc lập ở vé 02.
- Test hợp đồng A3/A4 phát lại fixture cũ; bốn hash sản phẩm A4 giữ nguyên. Kiểm tra với adapter mô hình bị thay
  bằng adapter luôn ném `network blocked` vẫn cho kết quả:
  `baocao-canhan=true`, `naive-bayes=true`, `nhap-mon-ml=true`, `xstk-ch3-1=true`.
- Test riêng bao phủ cache hợp lệ, cache cũ không qua validator, đúng một retry, log từng attempt và thứ tự kết
  quả khi chạy đồng thời.
- Mutation đã thử và đều bị test bắt: bỏ retry; bỏ log attempt hỏng; cho cache bỏ qua validator; đảo thứ tự kết
  quả của lô.
- Toàn bộ test suite chạy offline xanh ngày 2026-09-16.
