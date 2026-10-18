# SA-44 — Trang xem thử hai trang

**Nguồn chân lý:** [spec Pha B2](../../doc/pha-b2-spec.md), mục 11 và 10; vé [24](24-trang-xem-thu-pha-b.md) (an ninh, chế độ phát lại).
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD ở chế độ phát lại hay mô hình giả; khi bật `--allow-spend` thì tính trong trần ·
**Chặn bởi:** 33, 35, 36, 37, 41, 42 · **Trạng thái:** đạt theo duyệt của chủ dự án ngày 2026-10-18

**Quyết định nghiệm thu:** chủ dự án yêu cầu "44 thì bạn cho đạt luôn" ngày 2026-10-18. Ghi nhận đạt với 11 test HTTP đã qua và ví dụ hợp đồng đã có. Chủ dự án miễn phần bảy thao tác/ảnh trình duyệt; phần này chưa được thực hiện, không ghi thành kết quả thử tay. Trang ngoại tuyến hiện ở `http://127.0.0.1:8765/`.

## Vì sao

Chủ dự án muốn thử hai trang trên trình duyệt trước khi web của nhóm xong. Nhóm web cũng cần thấy các hợp đồng mới chạy thật.

## Cần làm

**Trang lộ trình:**
- module kèm tên, mô tả và "xong x/y";
- danh sách phiên theo `roadmap_page`, kèm bộ lọc "tất cả";
- tạo phiên toàn lộ trình;
- thư viện lộ trình;
- nút "Làm quiz" cả lộ trình;
- nút "Tạo tài liệu" có chọn tối đa 5 module.

**Trang học** (một module):
- khái niệm theo thứ tự, có nút "đã học";
- bài giảng `lecture-2`:
  - tiên quyết gập sẵn, có câu nối và nhãn theo người học;
  - khối "Tiếp theo";
  - cổng stream;
  - trạng thái hỏng, kèm nút "Đọc trang p", "Hỏi trợ lý", "Thử lại";
- danh sách phiên của module;
- thư viện module có hai nhóm `here` và `elsewhere`;
- nút tạo quiz và tài liệu.

**Chat:**
- thẻ "nội dung ở module N, mở module";
- ghi chú phạm vi đã cũ;
- thông báo hết trần ngày.

**An ninh giữ như vé 24:** chỉ localhost, kiểm Host và Origin, chỉ sáu cuốn phát triển, không lộ khoá hay cache.

**Nút "Đọc trang p"** mở PDF gốc, hoặc ảnh trang, đúng trang. Cuốn không có PDF gốc (nhap-mon-ml) thì nút báo rõ là không có.

## Tiêu chí nghiệm thu

- [ ] Test các điểm cuối với mô hình giả:
  - đúng JSON của hợp đồng mới;
  - sự kiện stream bài giảng chỉ có `item` sau cổng;
  - đề quiz không có đáp án;
  - `owner` khác bị từ chối.
- [ ] Danh sách thao tác thử tay, mỗi thao tác kèm ảnh chụp trong báo cáo vé:
  - mở trang lộ trình; tạo phiên toàn lộ trình và hỏi một câu về một module cụ thể, thấy thẻ module;
  - vào trang học một module; đánh dấu "đã học" một khái niệm, thấy "xong x/y" đổi;
  - mở bài giảng có tiên quyết, thấy nhãn đã học hay chưa học và câu nối;
  - mở một bài hỏng (kịch bản), thấy nút "Đọc trang p";
  - tạo tài liệu trong phiên module A về khái niệm của module B, thấy tài liệu ở thư viện A và ở thư viện B, nhóm "tạo ở nơi khác";
  - làm quiz cả lộ trình;
  - xoá một phiên, thấy nội dung vẫn ở thư viện.
- [ ] Ví dụ JSON thật của mọi hợp đồng mới (`session-1`, `turn-1`, `library-1`, `progress-1`, `lecture-2`, `answer-2`, `quiz-2`, `document-2`) gom vào một
  báo cáo cho nhóm web.
- [ ] Chạy được khi không có mạng, ở chế độ phát lại.
