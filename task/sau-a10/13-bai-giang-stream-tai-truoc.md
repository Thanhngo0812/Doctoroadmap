# SA-13 — Bài giảng stream và tải trước

**Nguồn chân lý:** [spec Pha B](../../doc/pha-b-spec.md), mục 7 (phiên JSON có stream), 8 (stream và kiểm, tải trước), 13 (sự kiện `skeleton`,
`item`, `final`), bất biến 2; [báo cáo bài giảng](../../report/nghien-cuu-bai-giang-theo-khai-niem-2026-10-11.md), mục 3.6, 4.5, 4.7.
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** lượt thử 10 khái niệm, dưới 0,05 USD, dry-run trước · **Chặn bởi:** 12 ·
**Trạng thái:** ready-for-agent

## Vì sao

Người học bấm vào khái niệm thì phải thấy nội dung ngay. Lần bấm đầu phải chờ LLM, nên cần ba thứ:
- phần do mã dựng hiện ngay;
- phần LLM hiện dần từng ý đã kiểm;
- khái niệm kế được sinh sẵn.

## Cần làm

**Phiên JSON có stream:** port gọi mô hình thêm khả năng stream structured output; adapter Gemini trả từng mẩu chữ của JSON.

**Ba loại sự kiện:**
- `skeleton` gửi ngay, gồm mọi phần do mã dựng của vé 11;
- `item` gửi khi một ý đã đóng xong **và** qua luật cục bộ K2, K3, K5, K7;
- `final` gửi sau luật toàn bài.

Lớp ứng dụng tách các ý đã đóng xong từ JSON dở. Mẩu stream có thể cắt giữa chừng một token hay một chuỗi.

**Không rút lại ý đã hiện:** luật toàn bài chỉ được thêm cờ, hoặc chuyển sang bản lùi bằng một sự kiện rõ ràng có `status` tương ứng. Bản cuối mới
vào cache.

**Tải trước:** khi khái niệm k được mở, xếp hàng sinh khái niệm k+1 trong dãy học nếu chưa có trong cache. Việc này đi qua khoá chống sinh trùng.

**Lệnh CLI** in dòng thời gian của sự kiện, gồm giây tới `skeleton`, tới ý đầu, tới `final`.

## Tiêu chí nghiệm thu

- [ ] Test với mô hình giả phát mẩu stream cắt ở chỗ bất kỳ, mỗi cái thấy đỏ trước:
  - ý hỏng K3 không bao giờ ra sự kiện `item`;
  - kết quả cuối giống hệt bản không stream của vé 12 trên cùng đầu ra kịch bản;
  - không có sự kiện nào rút lại một ý đã gửi.
- [ ] Test tải trước:
  - mở k thì có đúng một lần sinh cho k+1;
  - k+1 đã có trong cache thì không sinh.
- [ ] Lượt thật 10 khái niệm, sau dry-run và chủ dự án duyệt. Báo giây tới `skeleton`, tới ý đầu và tới `final`, ở p50 và p90.

## Ngoài vé

Giao diện hiện stream (vé 24 và web của nhóm).
