# Trợ lý `answer-3`: gia sư tự nhiên, ngữ cảnh lấy trước, công cụ khi cần, kiểm chỉ ghi log

**Status:** accepted — 2026-10-23. Thay lời nhắc, hậu kiểm xoá câu, giao thức `KHONG_DU` và khối `:::outside_document` của trợ lý `answer-2` (spec Pha B2
mục 3). Giữ: agentic RAG với công cụ đồ thị, phạm vi phiên neo vào khái niệm (ADR 0017), tiêu điểm `focus_node_id`, nhắc nền tiên quyết chưa học, trần chi.

**Trả lời như gia sư giỏi.**
- Câu dễ thì gọn, câu khó thì đủ, có ví dụ.
- Công thức bằng LaTeX.
- Được dùng hiểu biết chung, sách là chuẩn. Sách không nói thì nói tự nhiên "Sách không nói tới điều này, nhưng…" rồi vẫn giúp.
- Câu lạc đề thì đáp lịch sự rồi kéo về bài.
- Có thể gợi ý bước học tiếp.

**Ngữ cảnh lấy trước lời gọi mô hình đầu tiên:**
- tìm kiếm trong sách, ưu tiên module đang mở;
- khái niệm khớp, kèm tiên quyết và lộ trình theo số module của ứng dụng;
- bài giảng đang mở;
- lịch sử 6 lượt;
- ảnh trang khi tư liệu có công thức.

Đa số câu trả lời xong trong một lời gọi. Công cụ vẫn còn, nhưng chỉ dùng khi tư liệu chưa đủ hay khi người học muốn tạo quiz, tài liệu. Tối đa 3 vòng.

**Không còn xoá chữ.**
- Hậu kiểm (nhãn lạ, câu không nhãn, công thức, ý ngoài sách) chỉ ghi log cho admin.
- Câu trả lời stream thẳng chữ của mô hình.
- Câu trả lời không bao giờ rỗng khi mô hình đã viết.

**Căn cứ:**
- Chủ dự án, 2026-10-23: "bạn phải nâng cấp toàn diện từ prompt, môi trường trợ lý để nó trở nên chuẩn và cực kỳ tốt, ko gò bó mà tự nhiên sáng tạo chút";
  "gò bó vậy thì sao lên production được".
- **Mã cũ:**
  - hậu kiểm `answer-2` xoá mọi câu không có nhãn hợp lệ, và mọi câu có `=`, `∑`, `√` hay `$$`;
  - không còn câu có nhãn thì trả lời rỗng;
  - lời nhắc gồm "chỉ dùng tài liệu được cung cấp" và "không tự viết công thức".
- **Bản thử 2026-10-23,** 12 câu hỏi thật của 6 cuốn, `gemini-3.1-flash-lite` qua Vertex, 0,038 USD:
  - trợ lý cũ: 3/12 câu rỗng, kể cả một câu định nghĩa sách có; 3–29 giây;
  - bản mới: 12/12 có câu trả lời đúng ý, có ví dụ, có công thức, từ chối lịch sự câu lạc đề; 1,9–6,7 giây.
- **Độ trễ:** số "embedding Vertex 11,4 giây" của SA-60 là chi phí khởi động chứng thực mỗi lượt, vì lượt đo nào cũng dựng runtime mới. Dùng lại client thì
  embedding chỉ còn khoảng 1,6 giây.

**Considered Options**

- *Giữ `answer-2`, chỉ sửa lời nhắc.* Bị bác: hậu kiểm vẫn xoá câu có công thức và câu không nhãn.
- *Bỏ hẳn công cụ, chỉ một lời gọi.* Bị bác: cần công cụ để tạo quiz và tài liệu, và để tra đồ thị sâu hơn. Báo cáo gọi trợ lý là agentic RAG kết hợp truy vấn đồ
  thị.
- *Giữ khối `:::outside_document`.* Bị bác: cứng, và người học không cần biết.

**Consequences**

- Hợp đồng `answer-3`: `answer_md`, `sources`; bỏ `citations` kiểu cũ, `outside_document_blocks`, trạng thái `insufficient_context` và `not_in_document`.
  Web hiện Markdown có KaTeX như bài giảng.
- SA-23 (đánh giá trợ lý) phải đo trên `answer-3`.
- Tài liệu do người học yêu cầu (`documents.py`) cũng dùng hậu kiểm xoá câu. Sửa ở vé riêng, cùng cách.
- Trần chi mỗi câu trả lời và trần ngày mỗi người học tăng. Chủ dự án chấp nhận chi cao hơn "miễn là phải tốt".
