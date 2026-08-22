# 05 — Cảnh báo khi bộ tách bó tay, và lý do vượt trần

**What to build:** Khi một khối vượt trần token mà bộ tách câu **không cắt nổi**, hệ thống **kêu lên**. Hiện nó
lặng lẽ gắn cờ vượt trần và đi tiếp — người vận hành không có cách nào biết chữ viết đó chưa được hỗ trợ.

Và mỗi chunk vượt trần nói rõ **vì sao** vượt: một hàng bảng không chia nhỏ được, hay bộ tách không tìm được
ranh giới nào.

## Bất biến hiện tại không thể đỏ

Cờ vượt trần được **tự bật** mỗi khi số token vượt trần. Nên bất biến I15 — *"không chunk nào vượt trần, trừ
khi được đánh dấu tường minh"* — chỉ khẳng định lại điều mà code vừa tự gán cho nó. Nó **không bao giờ có thể
đỏ**, nên nó không canh gì cả.

Đây là **lần thứ ba** dự án gặp cùng một hình dạng lỗi:

- Vòng 1, F4 — tên test hứa hai điều, thân test kiểm một
- Vòng 3, F23 — guard đa cột chưa từng chạy nhánh chặn
- Bây giờ, I15 — bất biến khẳng định lại thứ code vừa tự gán

Điểm chung: **một thứ trông như đang bảo vệ nhưng không bảo vệ gì.** Ticket này thay nó bằng một bất biến có
thể đỏ thật.

## Cảnh báo khác gì với cờ

Cờ nói *chunk này vượt trần*. Cảnh báo nói *bộ tách không hiểu chữ viết trong tài liệu này* — đó là thông tin
về **tài liệu**, không phải về một chunk, nên nó thuộc danh sách lý do cảnh báo ở manifest và hiện ra ở dòng
lệnh, cùng chỗ với cảnh báo cây phẳng và chú thích mồ côi.

**Blocked by:** 01 — cần trường lý do vượt trần đã tồn tại.

**Status:** completed — 2026-08-21

- [x] Khi một khối vượt trần mà bộ tách trả về **đúng một** ranh giới bao trọn khối, ghi một lý do cảnh báo
- [x] Lý do cảnh báo đọc lên là hiểu phải đi xem chỗ nào, và nêu được trang hoặc mục
- [x] Lý do vượt trần trên chunk được điền đúng: hàng bảng không chia nhỏ được, hay bộ tách bó tay
- [x] Cảnh báo ghi vào manifest tầng chunk và in ra ở dòng lệnh
- [x] **I17** — khối vượt trần mà bộ tách chỉ trả về một ranh giới ⇒ **có** lý do cảnh báo
- [x] Có test: một câu đơn dài hơn trần, không có dấu kết câu bên trong ⇒ cảnh báo bật, lý do là bộ tách bó tay
- [x] Có test: một hàng bảng dài hơn trần ⇒ cảnh báo **không** bật vì đây là ngoại lệ đã biết, nhưng lý do
      vượt trần ghi đúng là hàng bảng
- [x] Có test: khối vượt trần mà cắt được ⇒ **không** cảnh báo, **không** lý do vượt trần trên các mảnh
- [x] Có test: tài liệu thử nghiệm hiện tại ⇒ **không** cảnh báo nào loại này, vì bộ tách chưa từng phải chạy
- [x] Bất biến I15 cũ được thay hoặc phát biểu lại sao cho nó **có thể đỏ** — nếu bạn giữ nguyên nó thì phải 
      ghi rõ vì sao nó vẫn có giá trị

> Ca kiểm ở đây nên dùng **một câu rất dài không có dấu kết câu**, chứ đừng dùng văn bản CJK. Ticket `04` sẽ
> làm CJK cắt được, và một ca kiểm dựa vào CJK sẽ hỏng ngay sau đó. Câu dài không dấu là ca ổn định trước và
> sau `04`.
