# 01 — Cổng trích thực thể, adapter, và cơ chế ghi–phát lại hội thoại

**What to build:** Chạy được một lệnh trích trên **một section thật** của `nhap-mon-ml`, thấy mô hình
trả về danh sách thực thể. Chạy lại lần thứ hai thì nó **phát lại từ bản ghi trong mili-giây**, không
gọi mạng, không tốn tiền, kết quả giống hệt.

Đây là viên đạn vạch đường của cả đợt: nó dựng cổng, adapter, cấu hình bí mật, và cơ chế ghi–phát lại
mà mười bốn ticket sau đứng lên.

## Vì sao ghi–phát lại phải có ngay từ ticket đầu

B0 đã trả lời: fixture Docling biến 220 giây parse thành **0,11 giây** phát lại, và đó là thứ khiến chín
vòng review chạy được. Test phụ thuộc lời gọi mô hình thì vừa chậm, vừa tốn tiền, vừa **đổi kết quả khi
nhà cung cấp cập nhật** — đúng lúc đó bộ test bảo vệ bất biến mất hết giá trị.

**Luật cứng của cả đợt:** không test nào được gọi mạng. Lời gọi thật chỉ ở hai chỗ tường minh — kịch bản
ghi fixture, và lệnh ingest thật.

**Blocked by:** None — can start immediately.

**Status:** done

- [x] Cổng trích thực thể khai báo trong `application/ports/`, theo đúng khuôn `DocumentParser` đang có:
      có `identifier` và `model_id`
- [x] Adapter thật gọi được nhà cung cấp; **thiếu API key thì báo lỗi rõ ràng ngay lúc dựng**, không để
      nổ giữa chừng sau khi đã chạy 80 section
- [x] Key đọc từ biến môi trường qua `Settings`; `.env.example` thêm tên biến với **giá trị rỗng**
- [x] Key **không** vào log, không vào manifest, không vào bất kỳ khoá băm nào — chỉ `model_id` được ghi
- [x] Kịch bản ghi fixture: chạy một section thật, ghi hội thoại ra `tests/fixtures/llm/`
- [x] Bản ghi là **nhật ký nhiều lượt có thứ tự** — phát lại trả đúng lượt thứ n cho lời gọi thứ n
      (ticket 03 phụ thuộc tính chất này)
- [x] Có test: phát lại một section từ fixture cho ra đúng kết quả đã ghi, **không chạm mạng**
- [x] Ghi lại cỡ tệp thật của fixture (không ước lượng — bài học vòng 6)
- [x] Toàn bộ bộ test hiện có vẫn xanh
