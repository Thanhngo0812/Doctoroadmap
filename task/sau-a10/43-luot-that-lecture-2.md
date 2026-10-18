# SA-43 — Lượt thật bài giảng `lecture-2`

**Nguồn chân lý:** [spec Pha B2](../../doc/pha-b2-spec.md), mục 6 và "Quyết định kiểm thử" (lượt có tiền); đợt tra hỏi 2026-10-18, Q12, Q13.
**Ai:** nhân viên chạy · Claude đọc và phân tích · **Chi phí mô hình:** khoảng 12 khái niệm × hai cấu hình sinh lại, ước dưới 0,10 USD. Dry-run trước,
chủ dự án duyệt · **Chặn bởi:** 40 · **Trạng thái:** ready-for-agent

## Vì sao

Cần số thật cho ba quyết định:
- **cổng S3:** khoảng từ cổng tới khi xong bài có đủ lớn để S3 đáng hơn S2 không;
- **câu nối:** có đạt K10–K12 với tỉ lệ đủ cao không;
- **lần sinh lại:** nhiệt độ 1,0 có cứu được nhiều bài hơn nhiệt độ 0 không.

Ngoài ra, vé 13 vẫn còn thiếu số giây đo trên lượt thật.

## Cần làm

- **Chọn 12 khái niệm có ít nhất một tiên quyết có câu trích cạnh:** 4 ở doc-1, 4 ở xstk, 4 ở doc-4. Dùng đồ thị hiện hành, ghim phiên bản. Chọn bằng hạt
  giống cố định; ghi danh sách trước khi chạy.
- **Dry-run:** báo số lời gọi và USD ước. Chạy sau khi chủ dự án duyệt.
- **Hai cấu hình** cho lần sinh lại: `lecture_retry_temperature` = 0 và = 1,0. Lần sinh đầu giống nhau ở cả hai cấu hình, nên chỉ phát lại, không gọi lại.
- **Ghi lại phản hồi** để phát lại 0 USD.

## Tiêu chí nghiệm thu

- [ ] Báo cho từng bài và tổng:
  - `status` và `reason_code`;
  - USD;
  - giây tới `skeleton`, tới cổng và tới `final`, ở p50 và p90;
  - khoảng cổng → `final`.
- [ ] **Câu nối:** số tiên quyết có `Q#`, số câu nối đạt, số bị bỏ theo K10, K11, K12.
- [ ] **So nhiệt độ của lần sinh lại:** số bài được cứu ở 0 và ở 1,0, cùng USD thêm.
- [ ] Claude đọc cả 12 bài: câu nối đúng quan hệ không, có bịa không, phần gợi lại có ích không. Ghi phán xét vào vé.
- [ ] Theo số đo, Claude đề xuất giữ S3 hay chuyển S2, và nhiệt độ của lần sinh lại, rồi báo chủ dự án.
