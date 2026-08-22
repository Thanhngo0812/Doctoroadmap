# 02 — Định danh bảng ở adapter

**What to build:** Mỗi bảng trong tài liệu có một **định danh tất định**, sinh từ chính nội dung của nó, mang
theo trong cây parse. Cùng một bảng luôn nhận cùng định danh — dù nó dịch chỗ trong sách, dù ingest lại bao
nhiêu lần.

Đây là mảnh đầu tiên để pha sau dựng được node loại bảng. Hiện bảng **không có gì cả**: nó tan vào phần văn
bản của chunk dưới dạng markdown, không định danh, không cách nào trỏ vào.

## Vì sao băm theo nội dung, không theo vị trí

Cùng lý do đã ghi trong [ADR 0001](../../doc/adr/0001-dinh-danh-tat-dinh.md) cho chunk và section, và trong
[ADR 0002](../../doc/adr/0002-anh-va-tham-chieu-ngoai-dinh-danh-chunk.md) cho hình: định danh theo vị trí sẽ
đổi hết chỉ vì ai đó chèn một đoạn ở trang đầu. Bảng cũng vậy.

Băm theo **các hàng đã chuẩn hoá**, không băm bản markdown đã dựng — vì cách dựng markdown là chi tiết trình
bày, và đổi cách thoát ký tự gạch đứng sẽ đổi định danh dù bảng không đổi.

## Tính ở adapter, không tính ở tầng miền

Cấu trúc hàng cột chỉ còn nguyên vẹn ở adapter. Đến tầng cắt chunk thì bảng đã thành markdown. Nên định danh
phải sinh ở nơi còn nhìn thấy hàng cột, và đi kèm node bảng trong cây parse.

Cấu trúc hàng cột **ở nguyên trong cây parse** — không thêm tầng lưu trữ, không nhân đôi sang artifact chunk.
Khác với hình: byte ảnh không sống được trong văn bản nên phải có file; nội dung bảng thì đã nằm trong văn bản
rồi.

## Tài liệu thử nghiệm không có bảng nào

Phần này **không kiểm được** trên giáo trình đang dùng. Fixture DOCX sẵn có **có đúng một bảng** và đang được
một test tích hợp khẳng định — dùng nó cho đường đi thật, và dựng node bằng tay cho các ca còn lại.

**Blocked by:** Không — bắt đầu ngay. Chỉ đụng cây parse, độc lập với schema chunk.

**Status:** completed — 2026-08-21

- [x] Node bảng trong cây parse mang một định danh tất định
- [x] Định danh băm theo **nội dung các hàng đã chuẩn hoá**, không băm bản markdown đã dựng
- [x] Không dùng vị trí, số trang hay thứ tự đọc trong phép băm
- [x] Cấu trúc hàng cột vẫn ở nguyên trong cây parse, không nhân đôi đi đâu
- [x] Tăng phiên bản adapter
- [x] Có test trên fixture DOCX: bảng duy nhất trong đó nhận một định danh
- [x] Có test: cùng nội dung bảng ở hai tài liệu khác nhau ⇒ **cùng** định danh
- [x] Có test: đổi một ô trong bảng ⇒ định danh đổi
- [x] Có test: đổi cách thoát ký tự khi dựng markdown **không** làm đổi định danh
- [x] Có test: node không phải bảng thì không có định danh bảng 
