# 04 — Bộ vàng: file Excel gán mù và hướng dẫn gán nhãn

**What to build:** Hai người gán nhãn mở một **file Excel** ra là làm được ngay: đọc chương trong sách, ghi các
quan hệ tiên quyết họ thấy, và đánh cờ khi danh sách khái niệm có gì sai. Kèm một **hướng dẫn** viết theo giao
thức PREAP. Đọc ngược file đó về thành dữ liệu chấm được.

Luật ở spec D13 và ADR 0009.

**Blocked by:** None — bắt đầu được ngay. (Việc của Claude.)

**Status:** ready-for-agent

- [ ] Lệnh sinh file Excel từ artifact canonical của một tài liệu và một chương.
- [ ] Bốn sheet: hướng dẫn; khái niệm (khoá, kèm nơi dạy theo chương, mục, trang); quan hệ; cờ.
- [ ] Sheet quan hệ: khái niệm đích chọn trong phạm vi **chương đã chọn**; đầu được cần chọn trong **mọi khái
      niệm của tài liệu**; kèm vị trí trong sách, loại bằng chứng, ghi chú.
- [ ] **Mù:** file không chứa cạnh nào của pipeline, kể cả quan hệ đề xuất của A3 và 2a.
- [ ] Ô ẩn ghi phiên bản artifact và phiên bản danh sách khái niệm.
- [ ] Đọc ngược file: bắt được khái niệm không tồn tại, cặp trùng, cạnh tự nối, và file gán cho phiên bản
      artifact khác.
- [ ] Hướng dẫn gán nhãn bằng tiếng Việt: định nghĩa quan hệ tiên quyết, luật "như đoạn này trình bày", ví dụ
      đúng và sai, các ca khó (nhắc trong định nghĩa nhưng không cần để hiểu; cha–con; anh em), và luật không
      phải gán mọi cặp.
- [ ] `openpyxl` khai thành phụ thuộc trực tiếp.
- [ ] Test theo seam bộ vàng; đột biến tối thiểu: rò cạnh pipeline vào file, danh sách chọn sai phạm vi, bỏ ô
      phiên bản.
