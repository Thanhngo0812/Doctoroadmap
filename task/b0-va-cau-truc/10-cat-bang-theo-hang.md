# 10 — Cắt bảng theo hàng và bất biến trần token

**What to build:** Một bảng dài trong giáo trình trở thành nhiều chunk, mỗi mảnh giữ lại dòng tiêu đề cột nên
đọc riêng một mảnh vẫn hiểu — thay vì một chunk vài nghìn token không dùng được cho truy hồi.

Hiện bảng **bỏ qua trần token hoàn toàn**: đường dựng chunk cho bảng luôn trả về đúng một mảnh, dài bao nhiêu
cũng mặc. Tài liệu đã đo không có bảng nào nên lỗi chưa lộ.

Và không bất biến nào chặn: rà lại toàn bộ danh sách bất biến hiện có, **không bài nào khẳng định số token của
chunk không vượt trần**. Lời hứa cốt lõi của tham số trần chưa từng được test bảo vệ. Đó là lý do ticket này
mang theo một bất biến mới chứ không chỉ sửa một nhánh mã.

**Blocked by:** 09 — cùng đụng vào đường dựng chunk, và bảng là loại nội dung mà luật gộp cố tình để đứng một
mình.

**Status:** completed

- [x] Bảng được cắt theo **hàng**, không cắt giữa hàng
- [x] Mỗi mảnh giữ lại dòng tiêu đề cột
- [x] Mỗi mảnh không vượt trần token
- [x] Một hàng đơn lẻ dài hơn trần thì giữ nguyên và được **đánh dấu vượt trần** trong chunk
- [x] **I15** — mọi chunk có số token không vượt trần, trừ chunk được đánh dấu vượt trần tường minh
- [x] Bất biến không cắt ngang câu ghi rõ **không áp dụng cho bảng** — ranh giới của bảng là ranh giới hàng
- [x] Có test: bảng bốn mươi hàng với trần nhỏ ⇒ nhiều mảnh, mảnh nào cũng có dòng tiêu đề cột
- [x] Có test: bảng ngắn vẫn ra đúng một chunk, không bị cắt vô cớ
- [x] Có test: một hàng dài quá trần ⇒ chunk được đánh dấu vượt trần, và I15 vẫn xanh
- [x] Chạy I15 trên tài liệu thật đã ingest — phải xanh
