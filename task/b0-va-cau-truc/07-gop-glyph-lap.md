# 07 — Gộp ký hiệu toán bị nhân bản glyph

**What to build:** Người đọc giáo trình tìm khái niệm `P` hoặc tập huấn luyện `D` và **tìm thấy** — thay vì
gặp `P P P` và `D D D` như hiện nay. Hai mươi hai phần trăm số chunk đang dính lỗi này.

Nguyên nhân: PDF vẽ chữ đậm toán học bằng cách chồng cùng một glyph ba lần lệch nhau vài phần trăm point, và
thư viện parse đọc trung thực cả ba. Đây là hành vi đã biết của trình trích xuất PDF, không phải lỗi thư viện.

Nghiêm trọng vì đây là **giáo trình học máy**: `x`, `y`, `P`, `T`, `E`, `D` chính là những khái niệm mà bước
trích khái niệm phải lấy ra làm đỉnh của đồ thị.

**Đặt ở adapter, không đặt ở tầng chuẩn hoá của miền.** Đây là hiện vật của việc trích xuất PDF, không phải
chuẩn hoá ngôn ngữ — DOCX không có lỗi này. Và quan trọng hơn: mọi bước chuẩn hoá hiện có đều **bảo toàn
nghĩa**, còn bước này **xoá chữ**. Một hàm có thể xoá chữ không nên nằm chung chỗ với các hàm không thể.

Đây là ticket **rủi ro nhất đợt** — nó sửa nội dung tài liệu, và dương tính giả là mất chữ thật.

Các ca bắt buộc, lấy từ tài liệu đã đo:

| Đầu vào | Đầu ra mong muốn |
|---|---|
| `tiêu chí P P P khi giải quyết` | `tiêu chí P khi giải quyết` |
| `T T T : Cần phán đoán` | `T : Cần phán đoán` |
| `{ x x x 1 , x x x 2 , ..., x x xN }` | `{ x 1 , x 2 , ..., xN }` |
| `ha ha ha` | **không đổi** |
| `Hà Nội và Hà Nam` | **không đổi** |

Ca `x x xN` là ca khó: lần lặp cuối dính liền chỉ số dưới nên **không có ranh giới từ ở cuối**. Bỏ sót ca này
thì hai mươi hai phần trăm số chunk vẫn còn bẩn.

**Blocked by:** 01 — không có phiên bản adapter thì bản sửa bị cây parse cũ che mất. 02 — cần khung test nuôi
bằng kết quả parse thật.

**Status:** completed

- [x] Việc gộp glyph nằm trong adapter parse, **không** nằm trong tầng chuẩn hoá của miền
- [x] Chỉ gộp chuỗi lặp của cùng **một chữ cái Latin đơn không dấu**, phân cách bằng đúng một khoảng trắng
- [x] Xử lý đúng cả ca lần lặp cuối dính liền chỉ số dưới
- [x] Tầng chuẩn hoá của miền **không đổi một dòng nào** — giữ tính chất mọi bước đều bảo toàn nghĩa
- [x] Tăng phiên bản adapter
- [x] Có test cho **cả năm** ca ở bảng trên, gồm hai ca phải **không** đổi
- [x] Có test trên fixture parse thật: số node dính lặp glyph giảm từ hai mươi chín xuống không
- [x] Có test: nguồn DOCX không đi qua bước gộp glyph
- [x] Nếu tìm được ca dương tính giả nào khác trong tài liệu thật, **dừng và báo** trước khi nới luật — mất
      chữ thật tệ hơn để sót glyph lặp
