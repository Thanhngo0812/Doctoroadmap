# 02 — Trích, lưu ảnh và thay fixture

**What to build:** Ingest một giáo trình PDF và **mọi bức hình trong đó có mặt trên đĩa**, nằm trong thư mục
của chính phiên bản cây parse đã sinh ra chúng. Bức hình bên phải ở trang 9 — hiện đang mất hẳn khỏi hệ thống
vì không có chú thích — nay có node và có file.

Đây là ticket lớn nhất đợt, và ba phần của nó **không tách rời được**: trích ảnh mà vẫn bỏ hình không chú
thích thì có file PNG không node nào trỏ tới; thay fixture mà chưa sửa adapter thì cây test đỏ.

## Mìn phải gỡ, không phải chuyện phụ

Bật trích ảnh **đổi hành vi** của bản xuất markdown. Trước đây nó trả một dòng thông báo lỗi ngắn; sau khi bật
nó trả **nguyên ảnh nhúng base64**. Adapter hiện dùng nó làm nhánh dự phòng khi hình không có chú thích. Đo
thật:

```
p9 len=295568  '![Image](data:image/png;base64,iVBORw0KGgoAAAANSUhEU…'
```

**295.568 ký tự base64 trở thành nội dung một node.** Nó sẽ thành chunk, được đếm token, và được embed.

Nhánh dự phòng đó phải bị **gỡ hẳn** cho hình, không phải chỉ thêm chuỗi thay thế bên cạnh. Chuỗi lấy nội dung
cho hình chỉ còn hai bậc: chú thích, hoặc chuỗi cố định.

## Vì sao chuỗi cố định chứ không phải tên ảnh

Định danh ảnh băm theo nội dung byte. Nếu nó nằm trong phần văn bản thì cấu hình trích ảnh chui vào khoá băm
định danh chunk qua đường vòng — đúng thứ [ADR 0001](../../doc/adr/0001-dinh-danh-tat-dinh.md) tồn tại để ngăn.
Đổi độ phân giải trích ảnh khi ấy sẽ đổi mọi định danh chunk có hình.

**Blocked by:** 01 — không có chỗ cho byte ảnh đi qua cổng parse thì không lưu được gì.

**Status:** completed — 2026-08-20

- [x] Bật trích ảnh trong tuỳ chọn thư viện parse, **ghim độ phân giải bằng 2,0** vào cấu hình parse
- [x] Độ phân giải tham gia hash quyết định parse lại — đổi nó làm cây parse cũ hết hạn
- [x] Định danh ảnh băm theo **nội dung byte** của ảnh đã trích
- [x] Node hình mang định danh ảnh của nó
- [x] **Gỡ hẳn** nhánh dự phòng lấy bản xuất markdown cho hình — chỉ còn chú thích hoặc chuỗi cố định
- [x] Hình không có chú thích **không còn bị bỏ**; phần văn bản của nó là một **chuỗi cố định**, không chứa định danh ảnh
- [x] Kho lưu trữ ghi ảnh xuống thư mục của phiên bản parse đã sinh ra chúng
- [x] Tăng phiên bản adapter
- [x] **Thay fixture** bằng bản sinh lại kèm ảnh; ghi chú nguồn gốc nêu rõ nó chứa ảnh và cách sinh lại
- [x] Hai bài đặc tả hiện trạng đang khẳng định về thông báo lỗi và về tám hình **phải được viết lại** — fixture mới làm chúng vô nghĩa
- [x] Có test trên fixture: trích đủ **chín** ảnh, không ảnh nào bị bỏ
- [x] Có test: **không node nào** có phần văn bản dài bất thường — bài này là lưới chặn mìn base64
- [x] Có test: định danh ảnh ổn định qua hai lần chạy trên cùng fixture
- [x] Có test ở tầng ingest: ảnh nằm đúng trong thư mục phiên bản parse sau khi chạy thật
- [x] Có test: nguồn DOCX không đi qua đường trích ảnh
