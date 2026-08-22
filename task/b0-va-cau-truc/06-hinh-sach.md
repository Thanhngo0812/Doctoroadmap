# 06 — Hình sạch, không còn thông báo lỗi trong nội dung

**What to build:** Người dùng bước truy hồi mở bất kỳ chunk nào và **không** gặp thông báo lỗi của thư viện
parse trong nội dung. Một hình có chú thích sinh ra chunk chứa đúng chú thích đó; một hình không chú thích và
không nội dung **không sinh chunk nào**, thay vì sinh một chunk chỉ gồm thông báo lỗi.

Hiện chín trên một trăm ba hai chunk chứa nguyên văn một chú thích HTML báo rằng ảnh không xuất được — bốn
phẩy bốn phần trăm ngân sách token của cả tài liệu. Một trong chín chunk đó **không có gì khác ngoài** thông
báo lỗi.

Nguyên nhân: adapter lấy nguyên khối bản xuất markdown của hình, mà bản xuất đó gồm chú thích cộng thông báo
lỗi. Nhánh dự phòng lấy chú thích riêng không bao giờ chạy, vì thông báo lỗi khiến chuỗi luôn khác rỗng.

Kèm theo: chú thích hình hiện nằm ở **cả hai** chỗ — trong nội dung chunk và trong tiền tố ngữ cảnh. Nếu bước
embed ghép hai thứ lại thì cùng một câu vào vector hai lần.

**Blocked by:** 01 — không có phiên bản adapter thì bản sửa bị cây parse cũ che mất. 02 — cần khung test nuôi
bằng kết quả parse thật.

**Status:** completed

- [x] Với node hình, lấy chú thích trước; chỉ khi không có chú thích mới lấy bản xuất markdown
- [x] Chú thích HTML bị gỡ khỏi mọi nội dung node, dù đến từ đường nào
- [x] Hình không còn chú thích lẫn nội dung thì **bỏ node**, không sinh chunk
- [x] Với node hình, tiền tố ngữ cảnh để trống — nội dung chunk đã chính là chú thích
- [x] Với node bảng, tiền tố ngữ cảnh **vẫn giữ**, vì nội dung chunk là bảng chứ không phải chú thích
- [x] Tăng phiên bản adapter
- [x] Bài đặc tả hiện trạng ở ticket 02 được lật: chín node hình đang chứa thông báo lỗi ⇒ **không node nào**
- [x] Có test trên fixture parse thật: tám hình có chú thích sinh chunk bằng đúng chú thích
- [x] Có test trên fixture parse thật: hình không chú thích ở trang chín **không sinh chunk**
- [x] Có test: không chunk nào trong toàn tài liệu chứa chuỗi mở đầu chú thích HTML
