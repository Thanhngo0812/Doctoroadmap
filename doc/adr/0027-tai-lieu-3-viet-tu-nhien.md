# Tài liệu `document-3`: viết tự nhiên theo yêu cầu, tư liệu rộng, kiểm chỉ ghi log

**Status:** accepted — 2026-10-24. Thay lời nhắc, đầu ra JSON có trích nguyên văn, khối "ngoài tài liệu" và hậu kiểm xoá câu (`check_text`) của tài liệu
`document-2` (spec Pha B mục 11, spec Pha B2 mục 7). Giữ: phạm vi tối đa 5 module, `scope_too_large` 0 USD, trần chi người học, thư viện, `home_scope`,
`origin`.

**Viết đúng thứ người học xin.** Đề cương ôn tập, tóm tắt công thức, bảng so sánh, hướng dẫn từng bước, tổng quan: mô hình chọn hình thức hợp với yêu cầu
(văn xuôi, danh sách, bảng). Công thức bằng LaTeX. Được dùng hiểu biết chung, sách là chuẩn.

**Tư liệu rộng, như bài giảng:**
- đoạn định nghĩa của từng khái niệm trong phạm vi;
- các đoạn khớp yêu cầu, qua tìm kiếm;
- đoạn kề, tới 20.000 ký tự, theo thứ tự đọc;
- chữ thô của công thức (như bài giảng bản 2);
- ảnh trang có công thức, tối đa 8.

**Không còn xoá chữ.** Đầu ra là Markdown stream thẳng. Nhãn, câu không nhãn, công thức chỉ ghi log cho admin (ADR 0024). `failed` chỉ khi không có chữ nào.

**Không bật suy nghĩ.**

**Căn cứ:**
- Chủ dự án, 2026-10-23: chấp nhận nâng cấp cả 4 khâu "để thật chuẩn đỉnh chuẩn các app lớn production".
- **Bản cũ, chạy thật 6 yêu cầu ngày 2026-10-24:**
  - tài liệu 280–1.583 ký tự, không công thức;
  - yêu cầu "tóm tắt công thức tương quan và hồi quy" ra bài về phương pháp tính trực tiếp, vì tư liệu bị cắt mất đúng các khái niệm được hỏi;
  - yêu cầu "hướng dẫn Naive Bayes có ví dụ số" ra hai câu.
- **Bản thử mới, cùng 6 yêu cầu:**
  - 584–908 từ, đúng hình thức được xin: bảng so sánh, bảng công thức, hướng dẫn từng bước;
  - công thức đối chiếu ảnh trang đều đúng;
  - chữ đầu 1,0–3,2 giây (một lần 7 giây khi khởi động lạnh); 0,002–0,005 USD mỗi tài liệu.
- **Thử bật suy nghĩ** (`low`, `medium`), 12 lần lặp cho hai yêu cầu bẫy: không chữa được lỗi tính số lẻ hay lỗi đảo chiều "r = 0 thì độc lập", mà chậm và đắt
  hơn.

**Giới hạn đã biết** (ghi để đợt đánh giá tổng đo, không chặn):
- **Tính số lẻ trong ví dụ tự nghĩ dễ sai.** Ví dụ Gaussian Naive Bayes trên dữ liệu chỉ có bảng số: khoảng nửa số lần có một bước exp hay phương sai sai. Ví dụ
  đếm tần suất có sẵn trong sách thì đúng mọi lần.
- **"r = 0 thì độc lập".** Lỗi này xuất hiện khi tóm tắt thành gạch đầu dòng, ở mọi biến thể lời nhắc đã thử. Sách viết chiều ngược lại.

**Considered Options**
- **Giữ `document-2`, chỉ nới hậu kiểm:** không chữa gốc. Tư liệu 8.000 token bị cắt mất khái niệm được hỏi, và đầu ra JSON có trích nguyên văn ép mô hình chép
  câu.
- **Bật suy nghĩ hay cho mô hình chạy mã để tính:** đã thử, không đổi được hai lỗi trên. Mô hình không tự gọi công cụ chạy mã khi viết.
- **Kiểm lại bằng lời gọi thứ hai rồi viết lại:** gấp đôi chi và thời gian; ADR 0024 không cho chặn hay sửa chữ của mô hình. Để dành cho đợt đánh giá tổng, nếu
  số đo cho thấy cần.
