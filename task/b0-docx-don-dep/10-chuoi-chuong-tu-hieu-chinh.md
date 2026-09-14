# 10 — Chuỗi chương tự hiệu chỉnh, xoá danh sách từ khoá ngôn ngữ

**What to build:** Một giáo trình Đức với `Kapitel 1 / Kapitel 2`, hay Trung với `第1章 / 第2章`,
ra đúng cây chương như giáo trình Việt với `CHƯƠNG I / CHƯƠNG II` — **không cần hệ thống biết trước
một từ nào của ngôn ngữ đó.**

## Cơ chế lỗi đang sửa

Danh sách từ khoá `CHƯƠNG|PHẦN|CHAPTER|PHỤ LỤC` đang gánh hai vai: gán cấp 1, và **miễn trừ khỏi
bộ lọc tiêu đề giả**. Vai hai ghép với luật tiêu-đề-lặp thành sát thương thật cho mọi ngôn ngữ ngoài
danh sách: tiêu đề `Kapitel 3` không được miễn trừ, mà PDF giáo trình hay có running header lặp tên
chương mỗi trang ⇒ **tiêu đề chương thật bị hạ xuống văn bản thường**. Cùng tài liệu đó viết bằng
tiếng Việt thì được che chở. Đây là lần thứ ba của hình dạng danh-sách-ngôn-ngữ mà dự án đã bác ở
bộ tách câu và bộ lọc cụm nối.

Ranh giới nguyên tắc (vào ADR 0003 ở ticket 09): **định dạng đếm** — chữ số, số La Mã, một chữ cái
Unicode kèm dấu ngăn — là tập đóng, giữ được; **từ vựng** là tập mở, không bao giờ đủ, phải thay
bằng luật tự hiệu chỉnh.

## Luật chuỗi

- Từ **hai** tiêu đề trở lên chung một **tiền tố** đứng ngay trước một **số** (chữ số hoặc La Mã),
  các số **khác nhau** ⇒ một chuỗi. Tiền tố so sau chuẩn hoá, không phân biệt hoa thường; số ở
  giữa tiêu đề vẫn nhận (`第1章…` — tiền tố `第`).
- Thành viên chuỗi **hưởng miễn trừ** khỏi bộ lọc tiêu đề giả — kế thừa đúng vai của danh sách cũ,
  để running header không hạ được chương của bất kỳ ngôn ngữ nào.
- **Guard bao trùm:** chuỗi chỉ gán **cấp 1** khi giữa ít nhất một cặp thành viên liên tiếp có tiêu
  đề khác chen giữa. `Bài tập 1 / Bài tập 2` đứng sát nhau không phải chương — rơi về luật thường.
- Hai chuỗi cùng bao trùm lồng nhau (PHẦN chứa CHƯƠNG): chuỗi có thành viên nằm **giữa** các thành
  viên của chuỗi kia là chuỗi trong, cấp = cấp chuỗi ngoài + 1.
- Danh sách từ khoá **xoá hẳn** — không giữ song song, đúng tiền lệ hai lần trước.

## Gap chấp nhận, ghi rõ trong ticket khi đóng

- `PHỤ LỤC` không đánh số, xuất hiện một lần: chuỗi không thấy ⇒ trên PDF phẳng sẽ lồng dưới chương
  cuối (DOCX không ảnh hưởng — cấp khai báo là bậc 2 của chuỗi ưu tiên). Nhẹ hơn hạ-nhầm-chương.
- Tài liệu trích **một chương duy nhất**: không tạo được chuỗi ⇒ đi luật thường, như hiện nay.

**Blocked by:** 05 — luật chuỗi là một nhánh của bậc 1 trong chuỗi ưu tiên, phải có khung ba bậc
trước. 02 — số vàng bốn tài liệu phải canh gác cú thay cơ chế này.

**Status:** done

- [x] Có test: `CHƯƠNG I/II/III` (La Mã, bao trùm) ⇒ cấp 1, không dùng từ khoá nào
- [x] Có test: chuỗi tiếng khác — tiền tố lạ + số, bao trùm ⇒ cấp 1 (dựng tay, ví dụ `第N章`)
- [x] Có test: thành viên chuỗi lặp trong khối thân (running header) ⇒ **không** bị hạ
- [x] Có test: `Bài tập 1 / Bài tập 2` đứng sát nhau ⇒ **không** thành cấp 1
- [x] Có test: hai chuỗi lồng nhau ⇒ chuỗi ngoài cấp 1, chuỗi trong cấp 2
- [x] Danh sách từ khoá chương biến mất khỏi mã nguồn
- [x] Số vàng: **cả bốn tài liệu đứng yên mọi cột** — DOCX đi bậc cấp-khai-báo, hai giáo trình
      đánh số chấm, slide phẳng thật; tài liệu duy nhất có kiểu `CHƯƠNG <số>` là DOCX và nó không
      đi qua nhánh này. Bất kỳ cột nào dịch ⇒ dừng và tìm ra vì sao
