# SA-39 — Bài giảng stream sau cổng

**Nguồn chân lý:** [spec Pha B2](../../doc/pha-b2-spec.md), mục 6.1; [ADR 0018](../../doc/adr/0018-bai-giang-khong-hien-ban-lui-stream-sau-cong.md); [nghiên cứu bài giảng](../../report/nghien-cuu-bai-giang-tien-quyet-goi-mo-xu-ly-hong-2026-10-18.md), mục 5.
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD (mô hình giả và phát lại) · **Chặn bởi:** 38 · **Trạng thái:** ready-for-agent

## Vì sao

Hiện mỗi ý qua kiểm là hiện ngay, nên bài có thể hiện vài ý rồi báo hỏng. Mà bài hỏng thì không còn bản lùi để thay. Giữ các ý tới khi bài chắc tạo được
(đủ 2 ý giải thích đạt), rồi mới hiện dần, thì người học không bao giờ thấy một bài bị huỷ giữa chừng.

## Cần làm

- **Trước cổng:** ý đạt luật cục bộ được giữ trong bộ đệm, chưa gửi sự kiện `item`.
- **Cổng mở** khi đủ `lecture_min_explanations` (2) ý giải thích đạt. Gửi các ý trong bộ đệm theo thứ tự lược đồ, rồi stream các ý sau ngay khi đạt.
- **Sau cổng, bài không còn hỏng được.** Hết token, JSON vỡ ở đuôi, hay K6 đều thế: giữ các ý đã đạt, bỏ phần còn lại, trả `ready` kèm cảnh báo `cat_ngan`.
- **Hỏng trước cổng:** đi đường sinh lại hoặc bài hỏng của vé 38.
- **Bất biến:** không ý nào đã gửi bị rút lại.
- **Đo**, ghi vào sổ chi hoặc nhật ký chẩn đoán:
  - thời gian tới `skeleton`;
  - thời gian tới cổng, tức ý đầu tiên;
  - thời gian tới `final`;
  - khoảng từ cổng tới `final`.

## Tiêu chí nghiệm thu

- [ ] Test với mô hình giả phát mẩu stream cắt ở chỗ bất kỳ, mỗi cái thấy đỏ trước:
  - trước khi có 2 ý giải thích đạt thì không có sự kiện `item` nào;
  - stream có 1 ý đạt rồi hỏng thì không có `item` nào, và đi đường hỏng;
  - stream có 3 ý đạt rồi JSON vỡ thì `ready` kèm `cat_ngan`, đủ 3 ý, không rút ý nào;
  - kết quả cuối giống bản không stream trên cùng đầu ra kịch bản;
  - bốn số thời gian có mặt và đúng thứ tự.
- [ ] Phát lại 0 USD 12 bài của nhóm 2. Báo khoảng từ cổng tới `final` ở p50 và p90. Nếu p50 dưới 1 giây, báo Claude để cân nhắc chờ cả bài (S2).
