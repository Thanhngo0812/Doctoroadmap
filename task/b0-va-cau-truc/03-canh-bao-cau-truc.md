# 03 — Cảnh báo cấu trúc thành danh sách lý do

**What to build:** Người vận hành ingest giáo trình `nhap-mon-ml` và **được cảnh báo** rằng cây heading phẳng
— thay vì dòng `Cảnh báo cấu trúc: không` như hiện nay. Cảnh báo nói rõ *chuyện gì*, không chỉ *có chuyện*, và
được ghi vào manifest để soi lại về sau mà không phải chạy lại parse.

Cờ hiện tại chỉ bật khi một heading con có cấp **nhỏ hơn** cha — tình huống bất thường. Ca hỏng thật thì cấp
hoàn toàn bình thường: đều bằng một, hợp lệ, nhất quán. Không nhánh nào chạm tới. Cần thêm một lượt nhìn **cả
cây sau khi dựng xong**, chứ không chỉ nhìn từng heading một.

Một cảnh báo im lặng đúng lúc cần kêu **tệ hơn không có cảnh báo**, vì nó tạo niềm tin sai. Đây cũng là ticket
mang bump phiên bản thuật toán cho cả đợt.

**Blocked by:** Không — bắt đầu ngay.

**Status:** completed

- [x] Cờ cảnh báo đúng/sai đổi thành danh sách lý do dạng chuỗi, mỗi lý do đọc lên là hiểu phải đi xem chỗ nào
- [x] Có phép kiểm chạy **sau khi duyệt xong toàn cây**: từ bốn heading trở lên mà mọi heading rơi vào cùng một
      cấp ⇒ thêm lý do cây heading phẳng, kèm số heading
- [x] Luật kẹp cấp hiện có được giữ, và cũng ghi một lý do khi nó chạy
- [x] Danh sách lý do được ghi vào manifest của tầng chunk
- [x] Lệnh dòng lệnh in ra **từng lý do**, không in một chữ có/không
- [x] Phiên bản thuật toán tăng từ `section-id-v2` lên `section-id-v3`
- [x] Có test: cây dựng tay với năm heading cùng cấp một ⇒ danh sách lý do chứa cảnh báo cây phẳng
- [x] Có test: cây có heading phân cấp bình thường ⇒ danh sách lý do **rỗng**
- [x] Có test: ba heading cùng cấp ⇒ **không** cảnh báo, vì tài liệu ngắn phẳng thật là chuyện bình thường
- [x] Ingest lại `nhap-mon-ml` thì cảnh báo cây phẳng **thật sự bật trước khi suy cấp và hết bật sau khi suy cấp**
