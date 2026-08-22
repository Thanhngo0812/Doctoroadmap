# 02 — Khung test nuôi bằng kết quả parse thật

**What to build:** Người phát triển viết một test cho adapter parse, chạy nó, và có kết quả sau **một phần
mười giây** — trong khi vẫn đối chiếu với **output thật** của thư viện parse trên một giáo trình thật, không
phải với một object giả lập.

Đây là ticket **prefactor**: nó không sửa lỗi nào, nó làm ba ticket sau (`06`, `07`, `08`) trở nên dễ viết và
đáng tin. *Make the change easy, then make the easy change.*

Vì sao không dùng object giả lập: lỗi F13 — thông báo lỗi của thư viện lọt vào nội dung chunk — sinh ra vì
**ta đoán sai giao diện của thư viện**. Một object giả lập chỉ kiểm mã của ta so với niềm tin của ta, nên nó
sẽ không bao giờ bắt được loại lỗi đó. Vì sao không chạy thư viện thật mỗi lần: parse tài liệu này mất **141
giây**.

Fixture đã có sẵn trong repo kèm ghi chú nguồn gốc, và vòng ghi–đọc đã được kiểm: 170 mục ra 170 mục, không
một khác biệt, chín trên chín hình giữ nguyên thông báo lỗi.

**Blocked by:** Không — bắt đầu ngay.

**Status:** completed

- [x] Có một chỗ dùng chung để nạp fixture kết quả parse đã ghi lại và trả về đối tượng tài liệu
- [x] Có test chạy adapter trên fixture đó và khẳng định số node thu được
- [x] Có **bài đặc tả hiện trạng** ghi nhận đúng những gì đang sai, để ba ticket sau lật nó: chín node hình
      đang chứa thông báo lỗi trong nội dung, hai mươi bảy heading đều ở cấp một, một node công thức bị bỏ vì
      rỗng nội dung
- [x] Test này chạy trong nhóm test nhanh, không nằm trong nhóm test tích hợp cần chạy thư viện parse thật
- [x] Thời gian chạy cả tệp test dưới một giây
- [x] Test tích hợp chạy thư viện parse thật trên PDF **vẫn giữ**, nhưng chỉ để bảo đảm đường ống còn nối được
- [x] Có ghi chú nêu rõ fixture phải được sinh lại khi nâng phiên bản thư viện parse, kèm cách sinh
