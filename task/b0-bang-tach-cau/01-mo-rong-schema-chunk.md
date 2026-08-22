# 01 — Mở rộng schema chunk và bump `section-id-v5`

**What to build:** Chunk có sẵn chỗ cho hai thứ mà hai nhánh sau sẽ điền vào: một danh sách tham chiếu bảng, và
một trường nói **vì sao** chunk vượt trần token. Chưa nhánh nào điền — danh sách còn rỗng, lý do còn trống.
Kết thúc ticket, toàn bộ bộ test vẫn xanh và **không một định danh chunk nào đổi**.

Đây là **prefactor**: nó không thêm hành vi nào, nó giữ cho hai nhánh sau không chặn nhau. *Make the change
easy, then make the easy change.*

Vì sao cần: nhánh bảng thêm tham chiếu bảng, nhánh tách câu đổi cờ vượt trần. Cả hai đều đổi **hình dạng**
artifact chunk, nên cả hai đều cần bump phiên bản thuật toán. Nếu bump nằm trong một nhánh thì nhánh kia phải
chờ nó xong — mất tính song song mà không được gì.

## Cờ vượt trần đổi thành lý do

Cờ đúng/sai **được thay hẳn** bằng một trường lý do, không giữ song song. Một nguồn sự thật duy nhất: trường
rỗng nghĩa là chunk nằm trong trần. Giữ cả hai sẽ tạo ra khả năng lệch nhau — cờ bật mà lý do rỗng — và buộc
phải thêm một bất biến chỉ để canh hai trường khớp nhau.

Hai lý do sẽ được dùng ở các ticket sau: một hàng bảng không chia nhỏ được, và bộ tách câu không tìm được
ranh giới nào trong khối.

## Cái bẫy đã gặp một lần rồi

Bản ghi chunk được dựng lại từ JSON bằng cách bung thẳng khoá thành tham số, trên một lớp dữ liệu có khe cố
định. Đợt trước đổi tên trường phân loại khối đã làm **mọi artifact chunk cũ không nạp được nữa**, và lỗi hiện
ra là một ngoại lệ kiểu khó hiểu chứ không phải thông báo rõ ràng. Lần này đổi cờ vượt trần sẽ gây đúng chuyện
đó.

**Blocked by:** Không — bắt đầu ngay.

**Status:** completed — 2026-08-21

- [x] Chunk mang thêm danh sách tham chiếu bảng, mặc định rỗng
- [x] Cờ vượt trần **được thay hẳn** bằng một trường lý do; trống nghĩa là không vượt trần
- [x] Chỗ nào đang tự bật cờ khi vượt trần thì nay điền một lý do tương ứng, để hành vi hiện tại không mất
- [x] Nạp một artifact chunk viết **trước** khi đổi thì hoặc chuyển đổi được, hoặc **báo lỗi tường minh** —
      không được ném ngoại lệ kiểu
- [x] Phiên bản thuật toán tăng từ `section-id-v4` lên `section-id-v5`
- [x] Cả hai trường mới **không** tham gia khoá băm định danh chunk
- [x] Có test: chunk không vượt trần thì trường lý do trống
- [x] Có test: danh sách tham chiếu bảng rỗng chứ không phải thiếu trường
- [x] Toàn bộ bộ test vẫn xanh
- [x] **Ingest lại tài liệu thử nghiệm và khẳng định tập định danh chunk giống hệt trước ticket này** — hai 
      trường mới ngoài khoá băm nên không được phép đổi gì
