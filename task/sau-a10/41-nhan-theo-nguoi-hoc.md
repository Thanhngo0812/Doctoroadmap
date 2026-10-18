# SA-41 — Nhãn theo người học trong bài giảng

**Nguồn chân lý:** [spec Pha B2](../../doc/pha-b2-spec.md), mục 6.5; [ADR 0019](../../doc/adr/0019-tien-do-hoc-khong-chan-nhan-gan-luc-doc.md).
**Ai:** nhân viên · Claude kiểm · **Chi phí mô hình:** 0 USD · **Chặn bởi:** 34, 40 · **Trạng thái:** ready-for-agent

## Vì sao

Bài giảng được cache chung cho mọi người học, nên chữ do LLM viết không được nói về tiến độ của một người cụ thể. Người học vẫn cần biết tiên quyết nào
mình đã học và nên quay lại module nào.

## Cần làm

- **Bước gắn nhãn chạy lúc trả bài,** sau khi lấy nội dung từ cache hoặc sinh xong:
  - thêm `learner_status` cho mỗi mục `prerequisites[]` và `next_up[]`, từ tiến độ của `owner`;
  - giá trị là `learned` hay `not_learned`, kèm `module_index`; không có `owner` thì `unknown`.
- **Chạy ở cả hai đường:** nút bấm và công cụ `get_lecture` của trợ lý.
- **Nhãn không vào cache, không vào `lecture_key`, không bao giờ vào prompt.**
- **Sự kiện `skeleton`** cũng mang nhãn, để web hiện ngay.

## Tiêu chí nghiệm thu

- [ ] Test, mỗi cái thấy đỏ trước:
  - hai người học có tiến độ khác nhau mở cùng khái niệm thì nhận cùng `lecture_key`, nhãn khác nhau, và chỉ có 1 lời gọi mô hình;
  - nội dung trong cache không chứa `learner_status`. Một bản sai cố ý ghi nhãn vào cache phải làm test đỏ;
  - ngữ cảnh gửi mô hình không chứa tiến độ;
  - đường `get_lecture` có nhãn giống đường nút bấm;
  - đổi tiến độ rồi mở lại thì nhãn đổi, và 0 lời gọi mô hình.
