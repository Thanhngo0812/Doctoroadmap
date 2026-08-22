# 02 — Trần bảng và trần gộp

**What to build:** Một bảng mười một hàng nằm gọn trong **một** chunk, và câu giới thiệu nó nằm cùng chỗ với
nó thay vì bị bỏ lại thành một mẩu hai mươi hai token.

Hai nửa của cùng một vấn đề, và nửa thứ hai **không tự khỏi** khi làm nửa thứ nhất.

## Nửa một — trần cắt

Khối bảng dùng trần bảng; mọi khối khác dùng trần văn xuôi. Đo trên tokenizer thật, trần 512 hiện cắt một bảng
**mười một hàng** (6 cột) hoặc **hai mươi hàng** (4 cột). Với trần bảng 2048, bảng tới **45–79 hàng** giữ
nguyên cấu trúc trong một chunk — tức gần như mọi bảng trong giáo trình.

Bảng lớn hơn **vẫn cắt theo hàng** như hiện nay, và định danh bảng đã ghép các mảnh lại được từ đợt trước.

## Nửa hai — trần gộp

Luật gộp đóng nhóm khi vượt trần, nên hiện **bất kỳ bảng nào trên 512 token cũng không gộp được với gì cả**:

```
 22 token  ['text']            <- câu dẫn BỊ BỎ LẠI MỘT MÌNH
499 token  ['table']
217 token  ['table','text']
```

Khi nhóm ứng viên **có chứa** một khối bảng, trần đóng nhóm là trần bảng thay vì trần văn xuôi.

**Đích kích thước giữ nguyên.** Đây là lựa chọn có chủ ý và nó quyết định hành vi:

```
câu dẫn 22 token  -> nhóm 22, dưới đích, đi tiếp
bảng   700 token  -> ứng viên 722, dưới trần bảng 2048 -> GỘP
                     722 đã đạt đích 256 -> đóng nhóm
câu sau           -> mở nhóm mới, gộp tiếp với văn xuôi phía sau
```

Nếu nâng cả đích thì một bảng nhỏ sẽ hút hàng loạt đoạn văn không liên quan vào cùng chunk cho tới 2048. Nâng
trần mà giữ đích cứu được câu dẫn — vốn là khiếm khuyết đo được — mà không mở cửa cho chuyện đó.

## Giới hạn đã biết, chấp nhận, đừng sửa trong ticket này

Với bảng **vượt** trần bảng, câu dẫn vẫn bị bỏ lại, vì việc cắt bảng xảy ra sau khi gom nhóm. Chỉ xảy ra với
bảng trên 45–79 hàng. Ghi lại để khỏi trôi; sửa nó cần đảo thứ tự cắt và gom, tức phẫu thuật lớn hơn giá trị
thu được.

## Một bài test hiện có sẽ hỏng, và nguyên nhân trông không giống nguyên nhân

Bài kiểm cắt bảng hiện truyền trần văn xuôi rồi khẳng định số token dưới trần đó. Sau ticket này bảng dùng trần
riêng, nên **bài đó sẽ không còn cắt nữa** và khẳng định sẽ đỏ. Nó phải được truyền trần bảng thay vào. Không
biết trước thì người làm sẽ đi tìm lỗi logic ở chỗ không có lỗi.

**Blocked by:** 01 — cần hai tham số trần đã tồn tại và đã vào hash cấu hình.

**Status:** completed — 2026-08-21

- [x] Khối bảng dùng trần bảng khi quyết định có cắt hay không; khối khác dùng trần văn xuôi
- [x] Nhóm ứng viên **có chứa bảng** thì trần đóng nhóm là trần bảng
- [x] **Đích kích thước không đổi**, kể cả với nhóm có bảng
- [x] **I21** — chunk vượt trần áp dụng của nó ⇒ mang một lý do tường minh
- [x] Bài kiểm cắt bảng hiện có được sửa để truyền trần bảng
- [x] Có test: bảng **11 hàng, 6 cột** ⇒ **một** chunk, không cắt
- [x] Có test: câu dẫn + bảng 30 hàng ⇒ câu dẫn **nằm cùng chunk với bảng**
- [x] Có test: bảng nhỏ giữa nhiều đoạn văn ⇒ **không** hút thêm văn xuôi tới 2048, vì đích vẫn giữ
- [x] Có test: khối văn xuôi 700 token ⇒ vẫn cắt theo câu ở trần văn xuôi, **không** hưởng trần bảng
- [x] Có test: bảng vượt trần bảng ⇒ vẫn cắt theo hàng, mọi mảnh lặp dòng tiêu đề và **cùng định danh bảng**
- [x] Ingest lại tài liệu thử nghiệm: **tập định danh chunk không đổi** — tài liệu không có bảng nào
