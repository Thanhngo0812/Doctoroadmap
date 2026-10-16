# 17i — Nghiệm thu chuỗi gộp

**Nguồn chân lý:** [spec gộp khâu trước A8](../../doc/gop-khau-truoc-a8-spec.md), Testing Decisions (nghiệm thu nghiên cứu) và mục 7.
**Ai:** Claude · **Chi phí mô hình:** ước dưới 6 USD; phải chạy dry-run trước và được chủ dự án duyệt · **Chặn bởi:** 17c, 17d, 17f, 17g, 17h
· **Trạng thái:** chờ nhân viên

## Vì sao

Phải đo trước khi tính chuyện đổi mặc định. Câu hỏi: chuỗi gộp có bớt lời gọi, USD và phút mà chất lượng gộp, neo và cạnh không kém đi quá nhiễu
hay không.

## Cần làm

**Chuẩn bị (0 USD)**
- Sửa các script nghiên cứu (phát lại E4, quy lỗi thượng nguồn, bảng cặp) để đọc được artifact chuỗi gộp và quy vàng qua hàm của vé 17h.
- Dry-run chuỗi gộp trên 6 tài liệu, rồi gửi dự toán để chủ dự án duyệt.

**Chạy:** A4/A5 chuỗi gộp trên 6 tài liệu phát triển tiếng Việt có A4 đầy đủ: doc-1, nhap-mon-ml, naive-bayes, doc-6, xstk-ch3-1, doc-4. Pass
chính chạy trên ba tài liệu vàng. Dùng gemini-3.1-flash-lite.

**So với chuỗi v3**
- **Gộp:**
  - nhóm gộp so với A4 cũ cộng danh tính cũ: gộp nào mất, gộp nào mới;
  - đọc mọi gộp khác tên mới;
  - số gộp sai mà vàng phát hiện được không tăng (mốc: 3);
  - số cặp đề cử theo nguồn.
- **Neo và trạng thái dạy:**
  - độ khớp theo từng khái niệm;
  - đọc mọi chỗ lệch trên đích vàng và một mẫu chỗ lệch khác;
  - câu neo đúng trên đích vàng không thấp hơn mốc 79/84;
  - so hai cỡ lô của phần neo trên ít nhất một tài liệu.
- **Đầu cuối:**
  - E4 trên doc-1, xstk, doc-4 với vàng đã chuyển id. Pass phụ là stage sản phẩm `a8-secondary-ml-v1` (mô hình đóng băng của vé 18) ở cả hai
    chuỗi; mốc phía v3 là kết quả vé 18d;
  - chạy lại phép quy lỗi thượng nguồn;
  - hồi tưởng và độ chính xác bao đóng, Q7 và Q7b không giảm quá mức nhiễu;
  - bộ vàng nào bị từ chối thì ghi lại và để riêng.
- **Pass phụ ML:** đo riêng mức E5 tụt do đặc trưng lệch phân bố, vì chunk neo thay cho chunk do provenance vá. Nếu tụt thì đề xuất vé học lại
  (ADR 0015).
- **Chi phí:** số lời gọi, USD và phút của stage canonical và chuỗi đồ thị, trước và sau, trên doc-4.

**Ghi kết quả:** viết một mục báo cáo, gồm số đo, các chỗ đã đọc, và phán đạt hay không. Đạt thì làm thêm:
- ADR 0016: danh tính là một phần của gộp thực thể ở A4; neo và trạng thái dạy quyết ở A5; provenance rời chuỗi;
- ADR 0004: thêm mục cập nhật về vector mô tả nháp dùng để đề cử ở A4;
- `CONTEXT.md` và `doc/spec-addendum.md` theo spec mục 7.

Đổi mặc định sang chuỗi gộp **không** nằm trong vé này. Việc đó cần thêm số T-01 và quyết định của chủ dự án.

## Nghiệm thu

- [ ] Dự toán đã được chủ dự án duyệt trước khi chi.
- [ ] Báo cáo có đủ bốn nhóm số đo, các chỗ đã đọc, và kết luận đạt hay không kèm lý do.
- [ ] Nếu đạt: ADR 0016, cập nhật ADR 0004, `CONTEXT.md` và spec-addendum đã commit.
