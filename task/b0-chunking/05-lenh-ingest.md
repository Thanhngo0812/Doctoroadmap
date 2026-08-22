# 05 — Lệnh `ingest` chạy đầu-cuối trên PDF thật

**What to build:** Người vận hành gõ một lệnh với đường dẫn file và mã tài liệu, rồi nhận về sections và chunks
ghi ra đĩa. Đây là lần đầu hai nhánh gặp nhau — logic cắt chunk thuần của 02–03 chạy trên cây tài liệu thật do
04 sinh ra, thay vì cây dựng bằng tay trong test.

Cũng là lần đầu tính ổn định của định danh được kiểm trên đường chạy thật chứ không phải trên fixture.

**Blocked by:** 03 — luật cắt đầy đủ, và 04 — adapter parse cùng artifact.

**Status:** completed

### Lệnh

- [x] Nhận đường dẫn file và **mã tài liệu logic do người dùng cấp**
- [x] Mã tài liệu **không** được suy ra từ hash nội dung file. Nếu suy ra từ hash thì sửa một dấu phẩy trong
      PDF cũng sinh mã mới và mọi định danh đổi theo — toàn bộ quyết định ở ADR 0001 thành vô nghĩa
- [x] Xuất artifact sections và chunks ra đĩa, tách khỏi artifact cây parse
- [x] Báo lỗi rõ ràng và thoát với mã lỗi khác không khi file không đọc được hoặc không đúng định dạng
- [x] In ra tóm tắt sau khi chạy: số section, số chunk, số window, và cờ cảnh báo cấu trúc nếu có

### Điều phối

- [x] Việc gom window và ráp ngữ cảnh là **logic ứng dụng**, không được lọt xuống tầng lưu trữ
- [x] Cắt lại chunk với tham số khác **không** phải parse lại — đọc từ artifact cây parse đã đóng băng
- [x] Phát hiện được file đã ingest trước đó qua hash file gốc trong manifest, và báo cho người dùng biết

### Bất biến trên đường chạy thật

- [x] **I5** — chạy lệnh hai lần trên cùng file cho **đúng** tập định danh
- [x] **I11** — sửa vài đoạn trong tài liệu rồi chạy lại, phần **không đổi** vẫn giữ nguyên định danh. Đây là
      lời hứa cốt lõi của cả pha; nếu nó gãy trên đường chạy thật thì mọi bằng chứng của các bước sau sẽ gãy
      theo mỗi lần tài liệu được cập nhật
- [x] Toàn bộ bất biến của ticket 02 và 03 vẫn xanh
