# 02 — Mở rộng schema và bump phiên bản

**What to build:** Chunk có sẵn chỗ cho tham chiếu công thức, và node có sẵn chỗ cho nội dung thô cùng định
danh công thức. Chưa ai điền — danh sách còn rỗng, hai trường kia còn trống. Kết thúc ticket, toàn bộ bộ test
vẫn xanh và **không một định danh chunk nào đổi**.

Đây là **prefactor**: nó giữ cho ba nhánh sau không chặn nhau.

## Ba ticket cần bump, nên bump phải đứng riêng

`04` đổi hình dạng artifact chunk, `05` đổi nội dung manifest, `06` đổi tập section. Cả ba đều cần phiên bản
mới. Để bump trong một nhánh thì hai nhánh kia phải chờ nó xong mà không được gì.

Và nếu **không** bump: artifact cũ bị tìm thấy và dùng lại im lặng, bản sửa không có tác dụng, người sửa tưởng
mình viết sai. Đó là con lỗi F21 đã gặp ở đợt hai.

## Cái bẫy đã gặp hai lần

Bản ghi chunk được dựng lại từ JSON bằng cách bung thẳng khoá thành tham số, trên một lớp dữ liệu có khe cố
định. Hai đợt trước, đổi tên trường đã làm **mọi artifact chunk cũ không nạp được**, và lỗi hiện ra là ngoại lệ
kiểu khó hiểu. Lần này chỉ **thêm** trường có mặc định nên rủi ro thấp hơn — nhưng vẫn phải kiểm.

**Blocked by:** Không — bắt đầu ngay.

**Status:** completed — 2026-08-22

- [x] Chunk mang thêm danh sách tham chiếu công thức, mặc định rỗng
- [x] Node mang thêm chỗ cho **nội dung thô** và **định danh công thức**, mặc định trống
- [x] Cả hai trường mới trên chunk **không** tham gia khoá băm định danh chunk
- [x] Phiên bản adapter tăng một bậc
- [x] Phiên bản thuật toán cắt tăng một bậc
- [x] Nạp một artifact chunk viết **trước** khi thêm trường thì vẫn nạp được, hoặc **báo lỗi tường minh** —
      không được ném ngoại lệ kiểu
- [x] Hành vi trích xuất và cắt chunk **không đổi một chút nào** trong ticket này
- [x] Có test: chunk không chứa công thức thì danh sách tham chiếu **rỗng**, không phải thiếu trường
- [x] Toàn bộ bộ test vẫn xanh, **không bài nào phải sửa khẳng định**
- [x] **Ingest lại cả hai tài liệu và khẳng định tập định danh chunk giống hệt trước ticket này** — hai trường
      mới ngoài khoá băm nên không được phép đổi gì
