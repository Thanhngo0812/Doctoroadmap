# 01 — Cổng parse mang được ảnh

**What to build:** Cổng parse trả về **cây tài liệu cộng một tập ảnh** thay vì chỉ cây, và kho lưu trữ nhận
được cả hai. Chưa ảnh nào được trích trong ticket này — tập ảnh còn rỗng. Kết thúc ticket, đường ống đã có chỗ
cho pixel đi qua và toàn bộ bộ test vẫn xanh y như trước.

Đây là **prefactor**: nó không thêm hành vi nào, nó làm ticket `02` khả thi. *Make the change easy, then make
the easy change.*

Vì sao cần: cổng parse hiện trả đúng một cây tài liệu, mà cây đó là dữ liệu miền thuần được tuần tự hoá thành
JSON. Byte ảnh **không có đường nào đi qua**, và không nên có — nhét ảnh vào cây sẽ biến tệp JSON 96 KB thành
vài MB base64, làm chậm mọi lần nạp lại artifact chỉ để phục vụ một thứ không ai đọc từ đó.

**Blocked by:** Không — bắt đầu ngay.

**Status:** completed — 2026-08-20

- [x] Cổng parse trả một bản ghi gồm cây tài liệu và tập ảnh khoá theo định danh ảnh
- [x] Cổng kho lưu trữ nhận thêm tập ảnh khi đóng băng một phiên bản parse
- [x] Cây tài liệu **không đổi một trường nào** — vẫn là dữ liệu miền thuần, vẫn tuần tự hoá như cũ
- [x] Tầng miền **không** chạm tới byte nhị phân
- [x] Adapter vẫn không biết kho lưu trữ nằm ở đâu — nó trả dữ liệu, không ghi file
- [x] Tập ảnh rỗng trong ticket này; kho lưu trữ nhận rỗng thì không tạo thư mục thừa
- [x] Test kiến trúc hiện có vẫn xanh — không tầng nào import ngược
- [x] Toàn bộ bộ test vẫn xanh, **không bài nào phải sửa khẳng định**
