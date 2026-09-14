---
status: accepted
---

# Tin dữ liệu khai báo, suy diễn là dự phòng

Ba lỗi vòng 9 có cùng nguyên nhân: luật suy diễn được hiệu chỉnh trên giáo trình PDF đã ghi đè dữ liệu đúng
của thể loại khác. Rõ nhất là DOCX đã khai heading level 1/2 bằng style Word nhưng chunker bỏ level đó và suy
lại từ text, làm 12/27 section lạc cha. Vế đối ngẫu của bài học vòng 8 là: khi parser trả dữ liệu đúng và đủ,
không thay nó bằng phỏng đoán của hệ thống.

## Decision

Mọi luật suy diễn phải là đường dự phòng cho dữ liệu thiếu hoặc thoái hoá. Chuỗi bằng chứng xác định cấp
heading, từ mạnh đến yếu:

1. Định dạng đếm tác giả gõ trực tiếp trong text: mục số, một chữ cái Unicode theo sau bởi `.`/`)`, hoặc
   chuỗi từ hai heading chung tiền tố đứng trước các số khác nhau. Chuỗi chỉ tạo cấp chương khi có heading
   khác chen giữa hai thành viên; chuỗi bao trùm lồng nhau tạo cấp lồng nhau. Tiền tố chỉ có ký hiệu không
   tạo chuỗi.
2. Level parser khai báo khi toàn tài liệu có ít nhất hai level phân biệt.
3. Luật suy diễn hiện hành khi cây khai báo phẳng hoặc không có level.

Đánh số tường minh thắng level khai báo khi hai nguồn mâu thuẫn. Guard `tree_depth`, bộ lọc heading giả và
clamp vẫn độc lập: chúng quyết định một item có phải heading và có vi phạm nesting hay không, không thay đổi
thứ tự bằng chứng trên.

Chuỗi chương đồng thời miễn thành viên khỏi heuristic heading lặp, nên running header không hạ nhầm heading
thật. Quyết định này không dùng danh sách từ vựng theo ngôn ngữ: định dạng đếm là tập đóng; từ vựng là tập mở.
Heading chương đơn lẻ hoặc phụ lục không đánh số không tạo được chuỗi và đi đường dự phòng thông thường.

Nguyên tắc tương tự áp dụng ngoài heading: bbox/page chỉ điều khiển repair bố cục khi thật sự có; trích ảnh
không được gác sau cờ sửa glyph PDF; marker thiếu ref phải được giải thích bằng cảnh báo.

## Considered Options

**Luôn tin raw level.** Bị loại vì ba PDF trong corpus khai toàn bộ heading ở level 1; mục `2.3.1` sẽ mất cây
ba cấp dù text có bằng chứng mạnh hơn.

**Phân nhánh theo đuôi `.docx`/`.pdf`.** Bị loại vì định dạng không bảo đảm chất lượng level. Kiểm tra cây có
từ hai level phân biệt trở lên dùng chính dữ liệu cần đánh giá và áp dụng được cho định dạng tương lai.

**Tiếp tục chỉ suy từ regex.** Bị loại vì lặp lại lỗi vòng 9: thêm từng regex không thể thay thế style và cây
mà tác giả đã khai đúng.

## Consequences

- DOCX có cây khai báo 1/2 giữ đủ `section_path`; ba PDF phẳng tiếp tục đi đường suy diễn cũ.
- Thêm thể loại mới phải vào corpus số-vàng để thấy ngay luật nào đang ghi đè dữ liệu thật.
- Cây parser phân cấp sai trong tương lai có thể được tin; đánh số tường minh vẫn thắng và giảm rủi ro này.
- Đổi chuỗi ưu tiên là đổi semantics chunk, phải bump `CHUNK_ALGORITHM_ID` và đối chiếu định danh.
