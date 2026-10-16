# 17g — Xác minh cặp gộp khác tên và quyết định người duyệt ở A4

**Nguồn chân lý:** [spec gộp khâu trước A8](../../doc/gop-khau-truoc-a8-spec.md), mục 3.4, 3.5, 3.6 và 3.7.
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD (test bằng mô hình giả) · **Chặn bởi:** 17e · **Trạng thái:** chờ 17e

## Vì sao

Lúc phán ở A4 chỉ có câu bằng chứng A3 và mô tả nháp, không có câu neo hay mô tả cuối. Một lượt xác minh độc lập cho cặp gộp khác tên giữ lại "ý
kiến thứ hai" của danh tính, để chặn gộp sai. Người duyệt cũng cần một chỗ để nạp quyết định, vì `--identity-review` không còn dùng trong chuỗi gộp.

## Cần làm

Chỉ áp ở chuỗi `gop`.

**Xác minh**
- Đối tượng: mỗi cặp nhóm được phán cùng mà không chung tên hay alias sau chuẩn hoá. Cặp chung tên hay alias không cần xác minh.
- Mỗi cặp qua một lời gọi xác minh **độc lập**:
  - lời gọi chỉ thấy hai hồ sơ: tên, alias, câu bằng chứng, mô tả nháp;
  - lời gọi không thấy lời phán lượt trước;
  - dùng lại prompt và hàm kiểm của lượt xác minh danh tính khi được.
- Chỉ quan hệ `dong_nhat` giữ gộp. Quan hệ khác trở thành ràng buộc "khác" khi dựng thành phần gộp, bằng cơ chế ràng buộc cùng/khác sẵn có. Mâu thuẫn
  bắc cầu xử lý như hiện nay.

**Người duyệt**
- `a4` nhận một tệp duyệt với các trường `left`, `right`, `decision`. Dùng lại bộ nạp và luật từ chối tệp của tài liệu khác của `--identity-review`.
- Id trong tệp là id node của canonical mà người duyệt đã xem.
  - Id đã chuyển hướng thì quy về id hiện hành qua bảng chuyển hướng.
  - Sau đó quy về các nhóm ứng viên qua thành viên của node.
- Quyết định của người (cùng hoặc khác) thắng phán của mô hình, dưới dạng ràng buộc khi dựng thành phần gộp.
- Tệp duyệt nằm trong khoá cache.

**Đầu ra**
- Danh sách các lần gộp khác tên, kèm câu bằng chứng của hai bên, để người duyệt dùng khi cần.
- Nhật ký từng cặp có thêm kết quả xác minh.
- Số liệu: số lời xác minh, số gộp khác tên, số gộp bị bác. Lời gọi và token tính vào phần "xác minh gộp" của `cost_summary`.
- Id node theo ADR 0005. Id biến mất được ghi vào bảng chuyển hướng và không bao giờ cấp lại cho khái niệm khác. Tên của các nhóm thành viên thành
  alias kèm câu bằng chứng.

## Nghiệm thu

- [ ] Test trên fixture tài liệu thật, với mô hình giả:
  - cặp gộp khác tên trượt xác minh thì không gộp;
  - cặp chung tên không sinh lời xác minh;
  - đầu vào của lời xác minh không chứa lời phán lượt trước;
  - quyết định người duyệt thắng mô hình ở cả hai chiều, kể cả khi tệp dùng id đã chuyển hướng;
  - tệp duyệt của tài liệu khác bị từ chối;
  - id biến mất được ghi vào bảng chuyển hướng và không bị cấp lại.
- [ ] Danh sách gộp khác tên có đủ câu bằng chứng hai bên.
- [ ] Đổi tệp duyệt thì khoá cache đổi.
- [ ] Mỗi luật chặn có ít nhất một test thấy nó trượt khi luật bị bỏ. Toàn bộ test qua.
