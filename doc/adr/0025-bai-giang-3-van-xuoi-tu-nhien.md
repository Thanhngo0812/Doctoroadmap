# Bài giảng `lecture-3`: văn xuôi tự nhiên, tư liệu rộng, mô hình thấy ảnh trang có công thức

**Status:** accepted — 2026-10-23. Thay cấu trúc bài giảng `lecture-2` (từng ý kèm câu trích, câu nối, cổng, luật K1–K12) của spec Pha B2 mục 6 và ADR
0018. Giữ: không bao giờ hiện bản trích câu TextRank (ADR 0018); bài luôn hiện, kiểm chỉ ghi log, không có bài thì báo lý do và nút "Thử lại" (ADR 0024);
nhãn theo người học gắn lúc đọc (ADR 0019).

**Bài giảng là một bài văn xuôi Markdown,** do LLM viết theo lời nhắc dạy học:
- dẫn nhập vì sao cần khái niệm;
- trực giác, rồi định nghĩa chính xác theo sách;
- ví dụ giải từng bước, ưu tiên ví dụ trong sách, được thêm ví dụ đời thường;
- chỗ dễ nhầm;
- dùng vào đâu tiếp;
- một câu tự kiểm tra kèm đáp án.

Công thức viết bằng LaTeX. Dài khoảng 300–700 từ. Nhiệt độ 1,0.

**Tư liệu rộng hơn.** Lấy đoạn định nghĩa và đoạn liền sau, các mục có tên khái niệm ở tiêu đề, và các đoạn nhắc tên khái niệm nhiều nhất trong cả cuốn, tới
khoảng 9.000 ký tự. Tư liệu ít thì mô hình vẫn giảng đủ bằng hiểu biết chung, miễn không mâu thuẫn sách.

**Mô hình thấy ảnh trang khi có công thức.** Văn bản trích từ PDF thay công thức bằng `[formula]`. Khi tư liệu có chỗ như vậy, gửi kèm ảnh các trang đó.
Ảnh trang được chụp một lần lúc dựng sách và lưu trong kho artifact.

**Nguồn:** nhãn `[S1]` do mô hình gắn được giữ. Điểm trùng giữa đoạn văn và đoạn sách được dẫn chỉ ghi log cho admin. Bài luôn kèm khối "Trong sách", liệt kê
các trang đã dùng; khối này do mã dựng.

**Căn cứ:**
- Chủ dự án, 2026-10-23: "tôi muốn bài giảng phải chuẩn và tự nhiên và tốt, nó cứ cụt ngũn"; "rất tệ, tôi muốn tự nhiên và sáng tạo chút chứ ko sao mà ra
  production được"; "đừng gò bó quá"; chấp nhận tăng chi phí tới trần 100 USD "miễn là phải tốt".
- **SA-21, bài `lecture-2` đo qua Vertex:**
  - phần LLM trung vị 429 ký tự, 31/35 bài có đúng 2 ý giải thích, 32% bài hỏng ở lần bấm đầu;
  - lời nhắc mở đầu bằng "Bạn viết bài giảng ngắn", không có chỉ dẫn dạy học;
  - mỗi khái niệm chỉ có 1–2 đoạn tư liệu (570–2.200 ký tự);
  - 13/15 khái niệm doc-1 có `[formula]` trong tư liệu.
- **Bản thử 2026-10-23,** 13 khái niệm × 4 bản, 0,11 USD, `gemini-3.1-flash-lite`, khoảng 4 giây mỗi bài:
  - bài dài 500–700 từ, có dẫn nhập, ví dụ và chỗ dễ nhầm;
  - có ảnh trang thì mô hình chép đúng hệ phương trình của Ví dụ 30 trang 37 doc-1, và dùng đúng ký hiệu $\hat{s}^2$ của sách;
  - các bài cũ trước đó hỏng thì nay đều có bài.
- **Phép đo trùng chữ để kiểm nhãn quá nhiễu,** không dùng làm cổng được. Đoạn có công thức LaTeX chấm điểm thấp dù đúng nguồn; trên 100 nhãn, trung vị chỉ
  0,15.

**Considered Options**

- *Giữ `lecture-2`, chỉ sửa lời nhắc.* Bị bác: cấu trúc mỗi ý một câu trích là gốc của bài cụt.
- *Bắt mô hình chỉ gắn nhãn khi chắc.* Bị bác: ở bản thử, 5/13 bài bỏ hẳn nhãn.
- *Đổi ảnh công thức sang LaTeX lúc dựng.* Để sau. Ảnh công thức là mảnh vỡ của một công thức; ảnh trang đủ tốt và đơn giản hơn.
- *Mô hình mạnh hơn.* Chưa cần: flash-lite đã cho bài tốt. Có thể so lại sau.

**Consequences**

- Hợp đồng `lecture-3` thay `lecture-2`: có `body_md`, `self_check`, `sources`; bỏ `sections` và `bridge`. Stream gồm `skeleton`, `delta` (chữ), rồi `final`
  hoặc `failure`.
- Web phải hiện Markdown có công thức (KaTeX) và khối "Trong sách". Nhãn `[Sx]` thành link mở trang sách.
- Bài giảng không còn tất định: bài sinh một lần rồi vào cache chung, nên mọi người học thấy cùng một bài.
- Kho artifact giữ thêm ảnh các trang có công thức. Sáu cuốn đã dựng cần một lệnh chụp bù.
- Mã `lecture-2` giữ lại tới vé dọn dẹp; production không còn dùng.
