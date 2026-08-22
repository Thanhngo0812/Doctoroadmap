# 06 — Lệnh `inspect` xem cây section và window

**What to build:** Người vận hành gõ một lệnh với mã tài liệu, rồi nhìn thấy cây section có phân cấp cùng các
window đã gom và chunk thuộc về từng window.

Lệnh này tồn tại vì gán section cha là phần dễ sai nhất của cả pha, và triệu chứng của nó **rất dễ nhìn ra
bằng mắt nhưng gần như không nhận ra được qua số liệu**. Lỗi kinh điển — đẩy heading vào ngăn xếp trước khi lấy
ra, hoặc lấy nhầm phần tử đáy — khiến mọi khối trỏ về section gốc. Số lượng chunk vẫn đúng y hệt, tổng vẫn
khớp, mọi thứ trông bình thường; chỉ có cây là phẳng lì và window thì phình thành cả chương.

**Blocked by:** 05 — lệnh ingest.

**Status:** completed

- [x] Nhận mã tài liệu và hiển thị cây section có thụt lề theo phân cấp, kèm đường dẫn section
- [x] Hiển thị mỗi window cùng các chunk thuộc về nó, theo thứ tự đọc
- [x] Đánh dấu section không có nội dung trực tiếp, để thấy rõ nó không sinh window
- [x] Hiển thị cờ cảnh báo cấu trúc nếu tài liệu có heading bị kẹp cấp
- [x] Đọc từ artifact đã có, **không** parse lại và không cắt lại
- [x] Đối chiếu được bằng mắt với ví dụ §4.5 của `doc/B0-ingestion-spec.md`: window của section chương phải
      **chỉ** gồm hai đoạn preamble, **không** gồm khối nào của các mục con
