# Nội dung học sinh khi cần, cache chung theo băm ngữ cảnh

**Status:** accepted — 2026-10-15

Bài giảng của một khái niệm được sinh ở lần bấm đầu tiên. Ngân hàng câu quiz của một khái niệm được sinh khi có người bấm "làm quiz", hoặc khi
trợ lý gọi `make_quiz`. Cả hai đều được cache **chung cho mọi người học**, với khoá là băm của:
- ngữ cảnh đã lắp (`context_hash`, tức JSON chuẩn hoá của mọi khối gửi mô hình);
- prompt, lược đồ, mô hình, cấu hình sinh và phiên bản hợp đồng.

`graph_version` chỉ là siêu dữ liệu. ADR này thay câu "sinh offline, không sinh on-the-fly lúc học" của A11 trong spec addendum.

Căn cứ:
- Chủ dự án chốt ngày 2026-10-11 và 2026-10-15.
- [Báo cáo bài giảng](../../report/nghien-cuu-bai-giang-theo-khai-niem-2026-10-11.md) mục 4.5 và
  [báo cáo quiz](../../report/nghien-cuu-quiz-tu-kiem-tra-2026-10-11.md) mục 3.5 ước chi phí: khoảng 0,002 USD mỗi bài giảng, khoảng
  0,0025 USD mỗi khái niệm của quiz.
- Sinh trọn cuốn trước cũng chỉ khoảng 1 USD cho doc-4. Vì vậy cái được của việc sinh khi cần không phải tiền, mà là ba điều:
  - không kéo dài thời gian tải tài liệu;
  - không sinh những bài không ai đọc;
  - bài luôn theo đúng đồ thị hiện hành.

**Considered Options**

- *Sinh trước trọn cuốn sau A10* (đúng chữ A11 cũ). Người học không phải chờ, nhưng phút/cuốn tăng, sinh cả nội dung thừa, và phải sinh lại cả cuốn
  mỗi lần Pha A chạy lại.
- *Sinh mỗi lần mở, không cache.* Tiền tăng theo số người học, và hai người học thấy hai bài khác nhau.
- *Cache theo phiên bản đồ thị.* Đơn giản nhưng sai hai chiều:
  - chạy lại Pha A mà khái niệm không đổi vẫn phải sinh lại;
  - nếu không tăng phiên bản thì bài cũ sống sót khi ngữ cảnh đã đổi.
- *Bài giảng theo module thay cho theo khái niệm* (đúng chữ "từng giai đoạn" của đề cương). Bị bác vì chủ dự án muốn bấm vào khái niệm. Trang
  module vẫn có tên, mô tả và danh sách khái niệm theo thứ tự lộ trình.

**Consequences**

- Ngữ cảnh đổi (chữ chunk, tiên quyết, tên module) thì bài tự sinh lại; không cần danh sách vô hiệu hoá viết tay. Đổi `model_id`, ví dụ khi
  `gemini-3.1-flash-lite` tắt từ 2027-05-07, thì bài sinh lại dần theo lượt bấm.
- Lần bấm đầu phải chờ, phải đo giây chờ. Bốn cách bù:
  - phần do mã dựng hiện ngay;
  - phần LLM stream từng ý đã kiểm;
  - bài giảng tải trước khái niệm kế;
  - quiz sinh song song theo khái niệm và hiện câu nào xong trước.
- Hai người bấm cùng lúc thì chỉ có một lời gọi (chống sinh trùng). Bản lỗi không vào cache.
- Lời gọi bài giảng và quiz dùng nhiệt độ 0. Tính tái lập dựa vào cache, nên nhiệt độ có thể đổi nếu lượt thử thấy lặp câu.
- Câu trả lời của trợ lý và tài liệu theo yêu cầu **không** cache chung, vì chúng phụ thuộc hội thoại và yêu cầu riêng của từng người.
