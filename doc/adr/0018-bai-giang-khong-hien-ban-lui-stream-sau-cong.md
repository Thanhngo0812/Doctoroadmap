# Bài giảng không hiện bản lùi, stream sau cổng, gợi lại tiên quyết bằng câu nối có trích dẫn

**Status:** accepted — 2026-10-18. Thay phần "mọi đường hỏng đều về mốc trích câu" của spec Pha B mục 8, và phần tương ứng trong hệ quả của ADR 0011.

**Bản lùi trích câu không bao giờ hiện cho người học.**
- Khi bài hỏng hẳn, người học vẫn thấy phần do mã dựng: vị trí, câu định nghĩa nguyên văn kèm trang, tiên quyết, hình đã xác nhận, khối "Tiếp theo".
- Kèm theo là lời nhắn và các nút "Đọc trang p trong sách", "Hỏi trợ lý"; nút "Thử lại" chỉ hiện khi lỗi là tạm thời.
- Bài hỏng không vào cache chung:
  - hỏng vì luật kiểm thì ghi nhớ 24 giờ;
  - hỏng vì lỗi mạng thì ghi nhớ 60 giây;
  - đổi prompt hay luật kiểm thì đổi khoá.

**Stream sau cổng.**
- Các ý đạt luật cục bộ được giữ lại tới khi có đủ 2 ý giải thích, rồi mới hiện dần.
- Sau mốc đó, lỗi ở đuôi chỉ làm bài ngắn lại, không làm bài hỏng. Không ý nào đã hiện bị rút lại.

**Gợi lại tiên quyết** có hai phần:
- phần mã dựng: tên, module, câu định nghĩa gập sẵn;
- một câu nối do LLM viết, trung tính, chỉ dựa câu trích của cạnh `requires`, có trích dẫn.

Thiếu câu nối thì chỉ hiện phần mã dựng, không sinh lại cả bài. Khối "Tiếp theo" do mã dựng, 0 USD.

**Căn cứ:**
- Chủ dự án, 2026-10-18: "bài giảng fallback sẽ ko bao giờ đc hiện cho user", và "bài giảng cũng phải làm ngta biết có cái tính tiên quyết". Đợt tra hỏi
  cùng ngày chốt Q10–Q18 và Q25–Q28.
- **Số đo trên lượt thật:**
  - 0/3 bài có tiên quyết có ý nhắc nền;
  - 5/12 bài hỏng cả hai lần sinh;
  - mã cũ còn cache cả bản lùi vĩnh viễn.
- **Đọc 10 bài trích câu:** 6 bài dở, gồm câu vụn ở công thức, `[formula]`, và gạch đầu dòng slide.
- [Báo cáo nghiên cứu bài giảng](../../report/nghien-cuu-bai-giang-tien-quyet-goi-mo-xu-ly-hong-2026-10-18.md):
  - advance organizer dạng viết có hiệu ứng nhỏ nhưng dương;
  - expertise reversal là lý do để gập câu định nghĩa;
  - bằng chứng cho phần gợi mở cuối bài yếu nhất, nên phần này để mã dựng;
  - hướng dẫn "graceful failure" của Google PAIR và Microsoft HAX.

**Considered Options**

- *Giữ bản lùi trích câu, làm cho sạch hơn.* Bị bác theo chủ dự án. Công làm sạch không đáng, vì bản lùi chỉ còn là mốc so sánh.
- *Chỉ hiện lời nhắn khi bài hỏng.* Bị bác: bỏ phí dữ liệu đã kiểm ở phần mã dựng. Phần này không phải câu do máy tự chọn.
- *Stream ngay mỗi ý (S1).* Bị bác: bài có thể hiện vài ý rồi báo hỏng.
- *Chờ cả bài (S2).* Người học chờ khoảng 3–7 giây. Được giữ làm phương án thay thế, nếu đo thấy khoảng từ cổng tới hết bài dưới 1 giây.
- *Câu "vì sao cần" do LLM tự suy, không bám câu trích cạnh.* Bị bác vì nguy cơ bịa quan hệ.
- *Gợi mở do LLM viết.* Bị bác: thêm tiền và thêm rủi ro, trên phần có bằng chứng yếu nhất.

**Consequences**

- Hợp đồng nâng lên `lecture-2`: `recall`, `bridge`, `next_up`, `failure`; bỏ trạng thái `fallback`.
- Tỉ lệ bài hỏng thành lỗi mà người học thấy trực tiếp. Vì vậy:
  - phải ghi lý do hỏng theo luật (SA-26);
  - phải sửa các luật dò sai, như K6 trên cả JSON (SA-30).
- Máy chủ phải giữ PDF gốc để mở trang sách.
- Hàm trích câu chỉ còn làm mốc so sánh ở vé đánh giá 21.
- Hai cuốn còn đồ thị chuỗi v3 (nhap-mon-ml, naive-bayes) không có câu trích cạnh, nên không có câu nối.
