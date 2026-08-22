# 05 — Lọc tiêu đề giả

**What to build:** Người dựng lộ trình mở danh sách section của `nhap-mon-ml` và **không** còn thấy
`trong đó:` — cụm từ đứng sau một công thức để liệt kê ý nghĩa các ký hiệu. Hai trăm năm mươi bảy token nội
dung thật từng bị gán vào mục vô nghĩa đó nay quay về đúng `1.1.1`, và window của `1.1.1` liền một mạch thay
vì bị cắt làm đôi.

Thư viện parse gán nhãn tiêu đề theo **hình dạng trình bày**, không theo ngữ nghĩa. Bằng chứng: cùng cụm
`trong đó:` xuất hiện lại một trang sau và lần đó được gán nhãn văn bản thường — thành chunk ba token, nhỏ
nhất tài liệu. Cùng một cụm từ, hai nhãn khác nhau, cách nhau một trang.

Một tiêu đề bị loại phải được **hạ xuống thành khối văn bản thường**, không bị vứt đi — nếu không thì nội dung
của chính nó biến mất.

**Blocked by:** 04 — bộ lọc dùng chung phép nhận biết đánh số đã xây ở ticket đó.

**Status:** completed

- [x] Tiêu đề ứng viên bị loại khi: kết thúc bằng dấu hai chấm **và** không đánh số **và** ký tự đầu là chữ
      thường
- [x] Tiêu đề ứng viên bị loại khi: dài hơn mười lăm từ **và** không đánh số
- [x] Tiêu đề bị loại trở thành khối văn bản thường, nội dung của nó vào chunk như mọi khối khác
- [x] Mỗi lần loại ghi một lý do cảnh báo kèm nguyên văn tiêu đề, để người vận hành biết hệ thống vừa quyết
      định thay mình
- [x] Có test: `trong đó:` **bị loại**
- [x] Có test: `TẬP THỂ TÁC GIẢ:` **được giữ** — kết thúc bằng dấu hai chấm nhưng viết hoa
- [x] Có test: `a) Chọn kiểu mô hình:` **được giữ** — kết thúc bằng dấu hai chấm nhưng có đánh số
- [x] Có test: `Làm sạch dữ liệu` **được giữ** — không đánh số, không dấu hai chấm, là mục con thật
- [x] Có test: nội dung nằm ngay sau một tiêu đề bị loại thuộc về đúng section cha, không mất và không lạc
- [x] Có test: window của section bao quanh liền một mạch, không bị tiêu đề giả xen giữa cắt đôi

> Bốn ca kiểm ở trên đều **lấy nguyên từ tài liệu đã đo**, không phải ca bịa. `Làm sạch dữ liệu` được xác nhận
> là tiêu đề thật: cùng lề trái với các tiêu đề khác, câu ngay trước giới thiệu nó, đoạn ngay sau khai triển nó.
