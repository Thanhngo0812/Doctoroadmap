# 04 — Suy cấp heading từ cách đánh số

**What to build:** Người dựng lộ trình mở cây section của `nhap-mon-ml` và thấy `1.1.1 Vài quan điểm về ML`
nằm **dưới** `1.1 Các khái niệm và bài toán học cơ bản`, nằm **dưới** `CHƯƠNG 1`. Chương sách sở hữu các mục
con của nó. Đường dẫn section của mỗi chunk chứa đủ lối đi từ chương xuống mục.

Đây là **ticket nặng nhất của đợt**. Thư viện parse trả cấp bằng một cho cả hai mươi bảy heading — nó nhận ra
"đây là tiêu đề" nhưng không nói "tiêu đề cấp mấy", và nó sẽ không bao giờ nói. Đừng chờ. Nguồn tín hiệu còn
lại là **cách đánh số trong chính tiêu đề**, thứ mà người đọc vẫn dùng và bản thân giáo trình tuân theo.

Việc này thuộc **tầng miền**: nó là suy luận cấu trúc từ văn bản, thuần, không chạm vào vào ra. Adapter tiếp
tục báo trung thực điều thư viện nói và ghi vào trường cấp thô.

Luật, xét theo thứ tự, dừng ở luật đầu tiên khớp:

| Mẫu tiêu đề | Cấp |
|---|---|
| `CHƯƠNG <số>` · `PHẦN <số>` · `Chapter <số>` · `Phụ lục` | 1 |
| `<số>` nối bằng dấu chấm, theo sau là khoảng trắng | bằng số thành phần |
| `<chữ cái>)` | cấp của mục đánh số đang mở, cộng một |
| Không đánh số, **trước** tiêu đề đánh số đầu tiên | 1 |
| Không đánh số, **sau** đó | cấp của mục đang mở, cộng một |

Hai luật cuối là thứ đặt `MỞ ĐẦU` lên đầu sách và đặt `Làm sạch dữ liệu` xuống dưới `1.4.2 Tiền xử lý dữ
liệu` — cả hai đều có thật trong tài liệu đã đo.

**Blocked by:** 03 — cần danh sách lý do cảnh báo để ghi lại khi luật kẹp cấp chạy, và để bài kiểm cây phẳng
có chỗ mà khẳng định.

**Status:** completed

- [x] Cấp heading được suy từ văn bản tiêu đề theo bảng luật trên, đặt trong tầng miền
- [x] Trường cấp thô do thư viện parse báo vẫn được giữ nguyên trong section, không bị ghi đè
- [x] Luật kẹp cấp hiện có vẫn chạy sau khi suy, và ghi lý do cảnh báo khi nó can thiệp
- [x] **I13** — cây dựng tay có mọi heading cấp một, tiêu đề đánh số `1`, `1.1`, `1.1.1`, `1.2`, `2` ⇒ cây thu
      được có **ba cấp**, và `1.1.1` có tổ tiên là `1.1` rồi tới `1`
- [x] **I14** — cùng đầu vào nhưng tiêu đề **không** đánh số ⇒ có lý do cảnh báo cây phẳng
- [x] Có test: `a)` và `b)` nằm dưới mục đánh số đang mở, không ngang hàng với nó
- [x] Có test: tiêu đề không đánh số **trước** mục đánh số đầu tiên ra cấp một
- [x] Có test: tiêu đề không đánh số **sau** mục đánh số ra mục con của mục đang mở
- [x] Có test: `CHƯƠNG 2` xuất hiện sau `1.1.1` vẫn ra cấp một, không bị kẹp thành mục con — chương mới là
      chuyện bình thường
- [x] Đường dẫn section của chunk chứa đủ đường đi, không còn chỉ một phần tử
- [x] Section không có nội dung trực tiếp nhưng có section con vẫn tồn tại trong cây
- [x] Các bài kiểm ổn định định danh hiện có vẫn xanh sau khi đổi luật
