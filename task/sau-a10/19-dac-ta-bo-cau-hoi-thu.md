# SA-19 — Đặc tả bộ câu hỏi thử cho trợ lý

**Nguồn chân lý:** [spec Pha B](../../doc/pha-b-spec.md), "Ghi chú thêm" (đánh giá chất lượng);
[báo cáo trợ lý](../../report/nghien-cuu-tro-ly-hoi-dap-do-thi-2026-10-11.md), mục 5.1; quy tắc làm dữ liệu của dự án: Claude viết đặc tả, chủ dự
án dùng agentic sinh, nhãn agentic là nhãn bạc.
**Ai:** **Claude** viết; chủ dự án duyệt rồi giao agentic · **Chi phí mô hình:** 0 USD · **Chặn bởi:** không, làm ngay được ·
**Trạng thái:** ready-for-agent

## Vì sao

Đề cương yêu cầu đánh giá trợ lý trên bộ câu hỏi thử. Bộ này phải phủ các loại câu người học thật sự hỏi, gồm cả câu ngoài tài liệu và câu nối
tiếp. Nó phải được làm theo đặc tả rõ, để agentic sinh đúng mà không phải hỏi lại.

## Cần làm

Claude viết ba tệp, theo bài học của D-01:

**1. Đặc tả cho chủ dự án,** gồm:
- **Phạm vi:** sáu cuốn phát triển. Không dùng tập giữ lại.
- **Bảy loại câu:** định nghĩa, vì sao tiên quyết, so sánh, ví dụ, lộ trình tới mục tiêu, ngoài tài liệu, nhiều lượt. Cỡ mỗi loại sao cho tổng khoảng
  200 câu.
- **Trường của mỗi câu:**
  - câu hỏi, loại câu, tài liệu, module đang mở;
  - khái niệm kỳ vọng;
  - đoạn tham chiếu (`chunk_id`);
  - trả lời được hay không;
  - ý chính của đáp án (tuỳ chọn).
- **Định dạng tệp** và cách chia theo tài liệu.
- **Mẫu kiểm chất lượng:** câu có đáp án biết trước.
- **Chỗ để trống khi không chắc.**
- **Ai duyệt và duyệt bao nhiêu:** người duyệt một mẫu.
- **Tài liệu đi qua dịch vụ nào:** quyết định của chủ dự án.

**2. Hướng dẫn riêng cho agentic:**
- Ví dụ tự soạn ở lĩnh vực khác, không lấy từ sáu cuốn.
- Soát tên ví dụ, kể cả bí danh, để không trùng câu kiểm.

**3. Script kiểm định dạng,** chỉ dùng thư viện chuẩn, để agentic tự chạy giữa các đợt.

## Tiêu chí nghiệm thu

- [ ] Đủ ba tệp. Script kiểm báo đúng lỗi trên một tệp mẫu có cài lỗi: thấy đỏ trước, xanh sau khi sửa.
- [ ] Không ví dụ nào trong hướng dẫn cho agentic trùng tên khái niệm hay alias của sáu cuốn.
- [ ] Chủ dự án duyệt đặc tả trước khi giao agentic.
