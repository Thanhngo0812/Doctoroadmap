# 01 — Khung dự án + kiểm chứng Docling cài được

**What to build:** Một khung dự án Python cài được và chạy được, cùng bằng chứng rằng thư viện parse có nhận
biết bố cục thật sự hoạt động trên máy này. Kết thúc ticket, người vận hành gõ một lệnh đồng bộ môi trường rồi
chạy một smoke test, và thấy thư viện parse đọc được một file PDF nhỏ.

Đây là **spike rủi ro, không phải việc dọn dẹp**. Máy đang chạy Python 3.14.3, còn thư viện parse kéo theo một
framework học máy nặng vốn thường chưa có bánh xe cài đặt cho phiên bản Python mới thế — đó là lý do spec ghim
phiên bản xuống 3.12. Nếu chỗ này gãy thì ticket 04, 05, 06 phải đổi hướng, nên nó chạy trước mọi dòng logic.

**Blocked by:** Không — bắt đầu ngay.

**Status:** completed

- [x] Khai báo dự án ghim phiên bản Python ở mức thư viện parse còn hỗ trợ, không dùng phiên bản đang cài sẵn trên máy
- [x] Lệnh đồng bộ môi trường chạy hết, không lỗi phụ thuộc
- [x] Import được thư viện parse trong môi trường đã đồng bộ
- [x] Smoke test parse một file PDF nhỏ và khẳng định số khối trả về lớn hơn không
- [x] Bộ khung bốn tầng dựng sẵn với thư mục rỗng, phụ thuộc hướng vào trong: tầng miền không import gì từ dự án
- [x] Có một nơi duy nhất nối các tầng lại với nhau
- [x] Cấu hình đọc được từ biến môi trường, có sẵn tham số cắt chunk với giá trị mặc định theo spec
- [x] Bộ chạy test dựng xong và chạy được dù chưa có test nào
- [x] **Nếu thư viện parse không cài được:** ghi lại chính xác lỗi và phiên bản đã thử, rồi **dừng và báo** — đừng tự đổi sang thư viện parse nhẹ hơn, vì spec đã loại phương án đó có lý do (cấp heading đoán theo cỡ chữ sẽ làm hỏng ticket 02)
