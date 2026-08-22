# 04 — `block_types` và bump `algorithm_id` v4

**What to build:** Một chunk khai báo **tất cả** các loại khối nó chứa, thay vì một nhãn duy nhất chọn bừa.

Đây là vá một lỗi **đang tồn tại**, không phải đón đầu lỗi mới:

```
block_type = first.block_type if len(blocks) == 1 else "text"
```

Chunk gộp bị gán cứng nhãn đoạn văn từ đợt gộp khối. Tài liệu thử có **34 node mục danh sách** nhưng kết quả
**không có chunk nào** mang nhãn đó — tất cả bị nuốt vào các chunk mang nhãn đoạn văn. Câu hỏi *"loại khối nào
đủ tư cách làm bằng chứng"* đang đứng trên một trường đã sai với **mọi** chunk gộp.

Ticket này cũng mang bump phiên bản thuật toán cho cả đợt, vì nó là ticket đầu tiên đổi **hình dạng** artifact
chunk.

## Một cái bẫy khi đổi tên trường

Bản ghi chunk được dựng lại từ JSON bằng cách bung thẳng khoá thành tham số, trên một lớp dữ liệu có khe cố
định. Đổi tên trường khiến **mọi artifact chunk cũ không nạp được nữa**, và lỗi hiện ra là một ngoại lệ kiểu
khó hiểu chứ không phải thông báo rõ ràng.

**Blocked by:** Không — bắt đầu ngay. Thuần tầng miền, không cần ảnh.

**Status:** completed — 2026-08-20

- [x] Trường phân loại khối đổi từ một giá trị sang **danh sách các loại có mặt** trong chunk
- [x] Danh sách khử trùng lặp và có thứ tự ổn định, để hai lần chạy cho cùng kết quả
- [x] Nạp một artifact chunk viết **trước** khi đổi tên thì hoặc chuyển đổi được, hoặc **báo lỗi tường minh** — không được ném ngoại lệ kiểu
- [x] Tăng phiên bản thuật toán từ `section-id-v3` lên `section-id-v4`
- [x] Có test: chunk gộp từ đoạn văn và mục danh sách khai **cả hai** loại
- [x] Có test: chunk từ một khối duy nhất khai đúng một loại
- [x] Có test trên tài liệu thật: sau khi sửa, có chunk khai mục danh sách — hiện tại **không có cái nào**
- [x] Các bài kiểm ổn định định danh hiện có vẫn xanh
