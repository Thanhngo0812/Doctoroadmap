# 17d — Gom phần neo vào lời gọi A5

**Nguồn chân lý:** [spec gộp khâu trước A8](../../doc/gop-khau-truoc-a8-spec.md), mục 4.
**Ai:** nhân viên · **Chi phí mô hình:** 0 USD (test bằng mô hình giả) · **Chặn bởi:** 17b · **Trạng thái:** chờ 17b

## Vì sao

Phần lớn lời gọi trước A8 đến từ việc neo từng khái niệm một (C8 trên doc-4 tốn 618 lời). A5 vốn đã đọc chính các chunk và bằng chứng đó khi viết
mô tả, nên vé này gắn phần neo vào lời gọi A5 sẵn có. Kết quả là bớt lời gọi mà không bớt thông tin.

## Cần làm

**Cỡ lô của phần neo** thêm giá trị "theo lô A5", là mặc định đề xuất của chuỗi gộp. Giá trị "một khái niệm" của vé 17b vẫn giữ để đối chứng. Cỡ lô
nằm trong khoá cache.

**Ở chế độ "theo lô A5"**
- Câu ứng viên dựng trước lời gọi, theo đúng vùng tìm của vé 17b. Hai chế độ vì vậy dùng cùng một tập ứng viên.
- Câu ứng viên được gắn vào lời gọi A5 sẵn có của khái niệm:
  - node nhiều thành viên: lời gọi mô tả, mỗi node một lời gọi;
  - node một thành viên: lời gọi kiểm mô tả theo lô.
- Mỗi khái niệm trả thêm các trường của C8:
  - trạng thái, một trong 6 giá trị;
  - mã câu neo;
  - câu trích;
  - lý do.
- Prompt phần neo giữ đúng nội dung luật của prompt neo hiện nay.
- Khái niệm không có ứng viên thì không mang phần neo trong lời gọi. Nó đi nhánh mã như vé 17b (`mentioned_only` hoặc `unchecked`).

**Kiểm phản hồi**
- Phần mô tả và phần neo được kiểm tách nhau.
  - Phần neo trượt kiểm không làm phần mô tả hợp lệ bị gọi lại.
  - Phần mô tả trượt kiểm thì đi đường sửa mô tả như hiện nay.
- Phần neo kiểm theo từng khái niệm, đúng luật C8:
  - câu neo phải là một ứng viên có thật;
  - câu trích phải nằm trong ngữ cảnh của ứng viên đó;
  - không có trường `confidence`.
- Khái niệm có phần neo trượt kiểm được hỏi lại riêng bằng đường "một khái niệm" của vé 17b, tối đa 2 lần như C8. Vẫn hỏng thì nhận `uncertain`
  và được giữ.
- Node một thành viên mà lời kiểm mô tả bác bản nháp thì được viết lại mô tả. Nếu lời kiểm đã trả phần neo hợp lệ thì phần neo đó được giữ, không
  hỏi lại.
- Xác minh kiến thức nền vẫn là lời gọi độc lập riêng.

**Số liệu:** đếm khái niệm được quyết trong lô và khái niệm phải hỏi lại riêng. Lời gọi và token của phần neo tính vào phần "neo" của
`cost_summary`.

## Nghiệm thu

- [ ] Test qua `execute` của stage canonical, với mô hình giả:
  - ở chế độ "theo lô A5", số lời gọi riêng cho phần neo bằng 0 khi mọi phần neo hợp lệ;
  - một khái niệm hỏng phần neo trong lô chỉ làm khái niệm đó bị hỏi lại riêng; hỏng tiếp thì nhận `uncertain` và được giữ;
  - phần mô tả hợp lệ không bị gọi lại khi phần neo hỏng;
  - khái niệm không ứng viên không mang phần neo.
- [ ] Cùng phản hồi giả thì hai chế độ ghi cùng trường neo lên node. Tập ứng viên của hai chế độ trùng nhau.
- [ ] Đổi cỡ lô phần neo thì khoá cache đổi.
- [ ] Mỗi luật chặn có ít nhất một test thấy nó trượt khi luật bị bỏ. Toàn bộ test qua.
