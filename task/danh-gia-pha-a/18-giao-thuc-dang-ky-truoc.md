# DG-18 — Giao thức đăng ký trước và danh sách đóng băng

**Nguồn:** spec mục 15; VL §12 · **Ai:** Claude; chủ dự án duyệt · **Chi phí:** 0 · **Chặn bởi:** DG-05, DG-07, DG-08, DG-10, cùng số của tập phát triển ·
**Hạn:** 06/11, commit trước 07/11 · **Trạng thái:** ready-for-agent

## Làm được gì

Một tệp giao thức trong `evaluation/giao-thuc/`, commit và ghi SHA-256 trước khi chạy tập thử. Tệp ghi:
- RQ; thước chính từng khâu; ba phép kiểm định, kèm Holm;
- ánh xạ trạng thái sáu sang bốn giá trị; ngưỡng khớp mờ; luật căn;
- N trang và seed bốc chương; K; lời nhắc B5 nguyên văn (B5a hay B5b);
- luật tranh chấp; thứ tự cắt khi trễ;
- kết quả **mô phỏng công suất** trên số tập phát triển;
- **danh sách đóng băng**: commit mã, hash cấu hình, hash vàng, phiên bản mô hình.

## Tiêu chí

- [ ] Mọi mục spec mục 15 có mặt.
- [ ] Bản ghi của mọi lượt tập thử mang SHA-256 của giao thức. DG-08 từ chối chạy tập thử khi thiếu.
- [ ] Bản hội đồng mục 9.4 và bảng lịch được cập nhật theo giao thức.
