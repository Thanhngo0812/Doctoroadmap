# 04 — Adapter parse thật + đóng băng artifact cây parse

**What to build:** Đưa vào bytes của một file PDF hoặc DOCX, nhận ra cây tài liệu có thứ tự đọc toàn cục và cấp
heading — rồi đóng băng kết quả đó lại. Lần parse thứ hai trên cùng file và cùng cấu hình đọc từ kết quả đã
đóng băng thay vì chạy lại mô hình bố cục.

Đây là nhánh song song với 02 và 03: nó là thư viện parse mà không cần logic cắt chunk, còn 02–03 là logic cắt
chunk mà không cần thư viện parse. Hai nhánh chỉ gặp nhau ở ticket 05.

**Blocked by:** 01 — khung dự án và kiểm chứng thư viện parse.

**Status:** completed

### Chất lượng parse

- [x] Đọc được cả PDF và DOCX
- [x] Thứ tự đọc toàn cục đúng, kể cả trên bố cục nhiều cột — đây là nguồn của mọi tín hiệu "cái gì trước cái
      gì" cho các bước sau, sai chỗ này là hỏng cả hai cách phân vùng ở tầng suy luận quan hệ
- [x] Nhận diện được heading và cấp của nó
- [x] Bảng được giữ nguyên khối, **không** bị dàn phẳng thành các dòng văn bản rời
- [x] Khối thuộc khung trang — header, footer, số trang lặp — bị lọc khỏi luồng nội dung. Đây là nơi việc loại
      bỏ chúng xảy ra, **không** phải ở bước chuẩn hoá văn bản

### Cổng và adapter

- [x] Adapter nằm sau một cổng khai báo ở tầng ứng dụng, đổi được sang thư viện khác mà không đụng logic cắt chunk
- [x] Cổng nhận bytes và trả về cây tài liệu — tầng miền không được biết gì về bytes hay thư viện parse

### Artifact

- [x] Cây parse được đóng băng thành artifact ngay sau lần parse đầu tiên
- [x] Manifest ghi hash cấu hình gồm: adapter parse cùng phiên bản, tuỳ chọn chuẩn hoá, tham số cắt, định danh
      tokenizer
- [x] Manifest ghi riêng hash của file gốc, tách khỏi định danh logic của tài liệu
- [x] Hash cấu hình đổi thì tăng version; hash cấu hình trùng thì dùng lại kết quả cũ
- [x] Parse lần hai trên cùng file và cùng cấu hình **đọc từ artifact**, không chạy lại mô hình bố cục

> Đây chính là cơ chế thay cho lời hứa "cùng đầu vào cho ra kết quả giống nhau tới từng byte" của spec gốc —
> lời hứa đó không giữ được với mô hình học máy. Đóng băng cây parse khiến bước cắt trở nên tất định trên thực
> tế, và khiến cắt lại chunk không phải parse lại.

### Test

- [x] Test tích hợp trên một hai file thật, **tách khỏi** bộ test bất biến của ticket 02 và 03
- [x] Bộ test bất biến vẫn chạy được mà không cần thư viện parse — nếu chúng bắt đầu phụ thuộc vào nó thì
      thiết kế seam đã sai
