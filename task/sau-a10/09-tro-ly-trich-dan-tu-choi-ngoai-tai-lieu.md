# SA-09 — Trợ lý: trích dẫn, từ chối, nội dung ngoài tài liệu

**Nguồn chân lý:** [spec Pha B](../../doc/pha-b-spec.md), mục 1, 10 (bước 4–5), 13; bất biến 1, 10;
[báo cáo trợ lý](../../report/nghien-cuu-tro-ly-hoi-dap-do-thi-2026-10-11.md), mục 2.6, 3.6, 3.7, 4.
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD (phát lại phiên của vé 08) · **Chặn bởi:** 08 · **Trạng thái:** ready-for-agent

## Vì sao

Có hai lý do:
- Đề cương yêu cầu mọi nội dung trích dẫn đoạn nguồn.
- Văn liệu cho thấy mô hình hay trả lời thay vì từ chối khi ngữ cảnh không đủ.

Chủ dự án cho phép nội dung ngoài sách, nhưng phải tách bạch. Vì vậy mã phải hậu kiểm trước khi câu trả lời tới người học.

## Cần làm

**Hậu kiểm từng câu khi stream:**
- nhãn không thuộc tập đã nạp thì xoá;
- câu có chữ số, ký hiệu toán hay tên khái niệm mà không có nhãn, và không nằm trong khối ngoài tài liệu, thì gắn cờ "chưa có nguồn".

**Từ chối:**
- Câu trả lời không có nhãn hợp lệ nào, mà cũng không phải câu "tài liệu không có", thì đổi thành câu từ chối cố định và ghi nhật ký.
- Dòng đầu là `KHONG_DU` thì đổi thành câu từ chối kèm các đoạn gần nhất.
- Câu hỏi hoàn toàn ngoài tài liệu trả `not_in_document`.

**Khối ngoài tài liệu:**
- Có cú pháp đánh dấu được nêu trong chỉ dẫn hệ thống; giữ nguyên, không gắn trích dẫn.
- Đếm vào `outside_document_blocks`.
- Định nghĩa, công thức và khẳng định về sách không được nằm trong khối này.

**Trích dẫn đầy đủ:**
- Mỗi nhãn có: `chunk_id`, trang, đường mục.
- Khoảng tô sáng do mã chọn: câu trong đoạn trùng nhiều âm tiết nhất với câu trả lời.
- Nhãn `Q#` mang câu trích nguyên văn của cạnh.

**Công thức:** nhãn `[CTk]` có tham chiếu ảnh nếu vé 04 đã có ảnh; nếu chưa thì vẫn có trang và `bbox`.

**Hợp đồng `answer-1` đầy đủ:** `status` ∈ {`answered`, `partial`, `not_in_document`, `insufficient_context`, `budget_exhausted`, `error`}.

## Tiêu chí nghiệm thu

- [ ] Test với mô hình giả, mỗi cái thấy đỏ trước:
  - nhãn bịa bị xoá;
  - câu trả lời không có nhãn bị đổi thành từ chối;
  - `KHONG_DU` thành từ chối kèm đoạn;
  - khối ngoài tài liệu được giữ, không có trích dẫn, và được đếm;
  - câu có số mà không có nhãn bị gắn cờ;
  - câu trích `Q#` trùng nguyên văn `quote` của cạnh;
  - khoảng tô sáng nằm trong chunk.
- [ ] Phát lại các phiên đã ghi ở vé 08 qua hậu kiểm, 0 USD. Báo tỉ lệ nhãn bị xoá, câu bị gắn cờ, và câu trả lời bị đổi thành từ chối.
- [ ] Một ví dụ JSON `answer-1` thật, sinh từ bản phát lại, đính kèm báo cáo của vé cho nhóm web.

## Ngoài vé

Hai việc không thuộc vé này:
- chấm "câu trả lời có được đoạn đỡ không" bằng RAGAS hay NLI (vé 23);
- khối nhắc khái niệm nền (vé 10).
