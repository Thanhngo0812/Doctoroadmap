# 04 — Đọc trường thô và đưa công thức quay lại

**What to build:** **263 node công thức** quay lại hệ thống, mỗi cái để lại một dấu vết đọc được ở đúng chỗ nó
đứng — nhưng nội dung thô **không** đi vào phần được embed.

## Nội dung chưa bao giờ mất

```
.text khác rỗng : 0/264
.orig khác rỗng : 263/264

ví dụ:  .text = ''
        .orig = 'X x1 x2 .  .  . xk ni n1 n2 .  .  . nk'
```

Adapter đọc trường đã dọn, thấy rỗng, bỏ node. Đây là **đọc nhầm trường** — cùng loại với lỗi thông báo lỗi ảnh
lọt vào nội dung ở đợt hình: gọi đúng API nhưng lấy sai thuộc tính.

Đo trên 170 mục của tài liệu một: hai trường **giống hệt ở 125 mục**, khác ở 35 — chỗ khác là trường thô còn
giữ dấu liệt kê mà bản đã dọn đã gỡ. Nên **ưu tiên bản đã dọn, rơi về bản thô**, không phải ngược lại.

Và luật *"văn bản rỗng thì bỏ node"* áp cho **mọi** loại. Vá riêng nhãn công thức là dựng lại đúng cái bẫy đó
cho nhãn tiếp theo.

## Nhưng nội dung thô không đọc được như văn xuôi

```
'1 2 ... n x x x x n + + + ='
'2 2 2 2 1 2 ( ) ( ) ... ( ) n x x x x x x s − + − + + − ='
```

Dòng sau lẽ ra là công thức phương sai mẫu. Trích xuất PDF đọc glyph theo thứ tự lưu trữ nên **toán tử bị tách
khỏi toán hạng và dồn về cuối**. Tổng **8.280 token**, tức **+28%** corpus. Đưa thẳng vào phần văn bản là bơm
28% cháo chữ vào thứ sẽ được embed.

Nên áp đúng khuôn đã dùng cho hình: **dấu vết vào văn bản, nội dung ra chỗ khác.**

## Dấu hiệu không mang ngôn ngữ nào

Chuỗi cố định đánh dấu hình không có chú thích hiện **viết bằng tiếng Việt**. Ticket này thêm một chuỗi tương tự
cho công thức, nên đây là lúc sửa **cả hai**: dấu hiệu là mã trung tính, không phải câu tiếng Việt. Tầng trình
bày dịch khi hiển thị.

Cùng lý do đã bỏ tên ngôn ngữ khỏi bộ tách câu: một câu tiếng Việt nằm giữa corpus tiếng Trung là dữ liệu sai
chỗ, và nó **còn bị embed vào vector**.

## Ticket này không tách được làm đôi

Đọc trường thô mà chưa xử lý công thức thì 8.280 token cháo chữ đổ thẳng vào chunk — **tệ hơn hiện tại**.

**Blocked by:** 01 — cần fixture có 264 công thức thật. 02 — cần trường tham chiếu và phiên bản mới.

**Status:** completed — 2026-08-22

- [x] Luật bỏ node đổi thành: thử trường đã dọn, rồi trường thô, **chỉ bỏ khi cả hai rỗng** — áp cho **mọi** loại
- [x] **I23** — node có trường thô khác rỗng **không bao giờ** bị bỏ im lặng
- [x] Node công thức được giữ; phần văn bản nhận một **chuỗi cố định trung tính ngôn ngữ**, không chứa định danh
      và không chứa nội dung thô
- [x] **Nội dung thô ở lại node** trong cây parse
- [x] **Định danh công thức** băm theo nội dung thô, cùng nguyên tắc với định danh hình và bảng
- [x] Chunk mang danh sách tham chiếu công thức: định danh cộng vị trí ký tự, cùng hệ toạ độ với vị trí sẵn có
- [x] **I24** — đổi tập tham chiếu công thức mà giữ nguyên văn bản ⇒ định danh chunk **không đổi**
- [x] Công thức vào **tập loại được phép gộp**, để không sinh hàng trăm chunk tí hon
- [x] **Dấu hiệu hình không có chú thích cũng đổi sang dạng trung tính ngôn ngữ**
- [x] Có test: node có trường đã dọn rỗng và trường thô có chữ ⇒ **được giữ**
- [x] Có test: node có **cả hai** rỗng ⇒ vẫn bị bỏ
- [x] Có test trên fixture hai: **263** node công thức quay lại
- [x] Có test: chunk chứa công thức có chuỗi cố định trong văn bản, **không** chứa nội dung thô
- [x] Có test: chunk chứa hai công thức ⇒ hai tham chiếu, vị trí đúng theo thứ tự xuất hiện
- [x] Có test: công thức xen giữa hai đoạn văn ngắn ⇒ ra **một** chunk, không phải ba
- [x] Có test ở tầng ingest: tham chiếu công thức sống sót qua vòng lưu rồi nạp lại
