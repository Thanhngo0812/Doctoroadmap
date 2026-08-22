# 01 — Adapter công bố phiên bản của riêng nó

**What to build:** Người phát triển sửa mã adapter parse, chạy lại lệnh ingest trên một tài liệu đã ingest
trước đó, và tài liệu được **parse lại** thay vì dùng lại cây parse đã đóng băng. Bản sửa của họ có tác dụng
ngay, không cần xoá artifact bằng tay.

Hiện hash cấu hình parse chỉ gồm định danh của adapter, mà định danh đó chỉ là phiên bản của thư viện parse.
Đổi mã adapter mà thư viện giữ nguyên phiên bản thì hash không đổi, nên bước tìm cây parse cũ tìm thấy và dùng
lại — **bản sửa im lặng không có tác dụng**.

Lỗi này chưa lộ vì đến giờ chưa ai sửa adapter sau khi đã ingest. Nó sẽ lộ **ngay ở ticket 06** nếu không làm
trước. Đó là toàn bộ lý do ticket này đứng đầu.

**Blocked by:** Không — bắt đầu ngay.

**Status:** completed

- [x] Adapter công bố một số phiên bản của riêng nó, tách khỏi phiên bản thư viện parse
- [x] Số phiên bản đó nằm trong cấu hình parse, nên nó tham gia hash quyết định có dùng lại cây parse hay không
- [x] Tăng số phiên bản này lên một bậc trong chính ticket này — các ticket adapter phía sau sẽ tăng tiếp khi cần
- [x] Có test: đổi phiên bản adapter làm hash cấu hình parse đổi theo
- [x] Có test: cây parse lưu dưới phiên bản adapter cũ **không** được dùng lại khi phiên bản đã tăng
- [x] Có test: cùng phiên bản adapter và cùng file nguồn thì **vẫn** dùng lại cây parse cũ, không parse lại vô ích
- [x] Manifest của tầng parse ghi rõ phiên bản adapter, để nhìn artifact là biết nó sinh từ mã nào
- [x] Ghi một dòng ở nơi khai báo phiên bản, nhắc rằng phải tăng tay mỗi khi đổi cách dựng node
