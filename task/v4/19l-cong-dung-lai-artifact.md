# 19l — Cổng đổi mặc định, kiêm dựng lại artifact chuẩn

**Nguồn chân lý:** [spec đổi mặc định chuỗi gộp](../../doc/doi-mac-dinh-chuoi-gop-spec.md), pha 3 "Cổng".
**Ai:** Claude · **Chi phí mô hình:** khoảng 5 USD; nằm trong trần 10 USD của đợt, dry-run trước · **Chặn bởi:** 19a, 19b, 19c, 19d, 19f, 19g,
19h, 19i, 19j, và 19k nếu 19j nhận · **Trạng thái:** chờ

## Cần làm

- **Chạy ở kho chính, với cấu hình sau pha 1:**
  - canonical chuỗi gộp cho doc-1, xstk, doc-4, nhap-mon-ml, naive-bayes, doc-6;
  - chuỗi đồ thị cho 3 tài liệu có vàng.
- **Tiêu chí:**
  - neo ở đích vàng không kém 17i: doc-1 25/26, xstk 26/26, doc-4 47/47 cùng trạng thái;
  - gộp sai mà vàng phát hiện không quá 3;
  - E4 nằm trong dải nhiễu của 19j;
  - lời gọi và USD trước A8 không vượt mức ước (doc-4 khoảng 1.230 lời, khoảng 1,0 USD);
  - E4 của pass phụ ML không tụt rõ so với 18d.
- **Luật khi trượt:**
  - trượt về chất lượng thì chưa bật; sửa rồi chạy lại phần hỏng;
  - E4 lệch mà vẫn trong dải nhiễu thì coi là qua;
  - vượt tiền hay thời gian mà chất lượng đạt thì vẫn bật và mở vé tối ưu.
- **Báo cáo cổng:**
  - phút/cuốn, USD/cuốn, lời gọi theo phần, và các chỗ đã đọc;
  - thời gian toàn stage mentions của doc-4, cho ô còn mở của 19g.
- **Lưu ý cấu hình:** `.env` của máy chủ dự án đã sửa ngày 2026-10-17. `CANONICAL_CONCURRENCY` từ 4 thành 16, bỏ `VERTEX_CONCURRENCY`.
  Trước khi chạy cổng, in `Settings()` để chắc giá trị thật.

## Nghiệm thu

- [ ] Báo cáo cổng có đủ tiêu chí và phán qua hay trượt kèm lý do.
- [ ] Artifact chuẩn mới của 6 tài liệu nằm ở kho chính.
