# 08 — Thống kê node bị bỏ vào manifest

**What to build:** Người vận hành mở manifest của một tài liệu đã ingest và thấy ngay **cái gì đã bị bỏ** —
mà không phải chạy lại parse mất một trăm bốn mươi mốt giây để biết.

Trên tài liệu đã đo, thư viện parse trả về một trăm bảy mươi mục và adapter giữ lại một trăm năm mươi chín.
Mười một mục biến mất im lặng, thuộc ba loại rất khác nhau về mức độ:

| Loại | Số | Đánh giá |
|---|---|---|
| Chú thích hình | 9 | **Đúng** — bỏ có chủ đích, quay lại qua tiền tố ngữ cảnh |
| Mục lục | 1 | **May** — ta không muốn mục lục thành chunk, nhưng ta bỏ nó vì nội dung tình cờ rỗng, không vì có luật |
| Công thức | 1 | **Mất nội dung** — một công thức trong giáo trình học máy là nội dung, không phải trang trí |

Ticket này chỉ **đếm và báo**. Việc trích lại nội dung công thức nằm ngoài phạm vi đợt này.

**Blocked by:** 01 — không có phiên bản adapter thì bản sửa bị cây parse cũ che mất. 02 — cần khung test nuôi
bằng kết quả parse thật.

**Status:** completed

- [x] Adapter trả về, cùng với cây tài liệu, một bảng thống kê: tổng số mục thư viện trả về, số node giữ lại,
      và số node bị bỏ theo **từng nhãn**
- [x] Thống kê được ghi vào manifest của tầng parse
- [x] Node bị bỏ vì nội dung rỗng cũng ghi một lý do cảnh báo, riêng loại công thức
- [x] Lệnh dòng lệnh in ra dòng tóm tắt: giữ bao nhiêu trên bao nhiêu, bỏ những loại gì
- [x] Tăng phiên bản adapter
- [x] Có test trên fixture parse thật: thống kê ghi đúng chín chú thích, một mục lục, một công thức
- [x] Có test: tổng số giữ lại cộng tổng số bỏ bằng tổng số mục thư viện trả về — không mục nào biến mất khỏi
      cả hai cột
