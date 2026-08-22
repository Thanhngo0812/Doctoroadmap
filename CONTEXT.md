# doc2roadmap

Biến một tài liệu học thuật (PDF/DOCX) thành lộ trình học: trích khái niệm, dựng đồ thị tiên quyết, xếp thành
các giai đoạn học tuần tự.

## Language

### Ingestion (B0)

**Document tree**:
Cây các khối nội dung mà parser trả về từ một tài liệu, đã có thứ tự đọc toàn cục và cấp heading.
_Tránh dùng_: markdown, plain text, parse output

**Leaf block**:
Khối nội dung nhỏ nhất mà parser nhận diện — một đoạn văn, một bảng, một công thức, một caption.
Đây là đơn vị gốc để cắt chunk.
_Tránh dùng_: element, node lá, đoạn

**Chunk**:
Một nhóm leaf block liền kề trong cùng một section sau khi chuẩn hoá; nhóm có thể chứa văn bản, hình, bảng và
công thức.
Chunk khai tất cả loại khối bằng `block_types`, tham chiếu hình bằng `image_refs`, tham chiếu bảng bằng
`table_refs`, tham chiếu công thức bằng `formula_refs`, mang định danh tất định riêng và là đơn vị nhỏ nhất được
embed hoặc trích dẫn làm bằng chứng.
_Tránh dùng_: passage, segment, đoạn văn

**Ba trần token**:
Ba giới hạn có vai trò riêng: trần văn xuôi `max_tokens` giữ đơn vị truy hồi gọn; trần bảng
`max_table_tokens` cho phép giữ bảng nguyên khối lâu hơn; trần cứng `hard_cap_tokens` là giới hạn tuyệt đối cho
mọi chunk. Hai trần đầu là trần theo loại nội dung, trần cuối luôn thắng.
_Tránh dùng_: một trần chung, trần cứng cho `max_tokens`, giới hạn model

**Hình**:
Tài sản PNG được trích trong lúc parse, định danh bằng SHA-256 của chính byte ảnh và lưu cùng version parse tree
đã sinh ra nó. Document tree chỉ giữ `image_id`, không giữ byte ảnh.
_Tránh dùng_: node ảnh, ảnh đồ thị, base64 trong cây

**Tham chiếu hình**:
Cặp `image_id` và `char_start` trên chunk, chỉ ra hình nào xuất hiện ở vị trí nào trong văn bản đầy đủ. Tham
chiếu không chứa đường dẫn và không tham gia khoá băm định danh chunk.
_Tránh dùng_: đường dẫn ảnh, image path, URL ảnh

**Bảng**:
Khối hàng cột trong document tree, định danh bằng SHA-256 của ma trận ô đã chuẩn hoá. Nội dung đọc được nằm
trong chunk dưới dạng markdown; cấu trúc hàng cột ở nguyên trong parse tree.
_Tránh dùng_: node bảng đồ thị, file bảng, markdown table ID

**Tham chiếu bảng**:
Cặp `table_id` và `char_start` trên chunk, chỉ ra bảng nào xuất hiện ở vị trí nào trong văn bản đầy đủ. Tham
chiếu không chứa đường dẫn, không sao chép hàng cột và không tham gia khoá băm định danh chunk.
_Tránh dùng_: bản sao bảng, table path, chỉ số bảng theo trang

**Công thức**:
Khối toán học giữ nội dung thô và `formula_id` SHA-256 trong document tree. Text chunk chỉ nhận marker
`[formula]`, vì raw PDF có thể đúng glyph nhưng sai reading order và chưa đủ tin cậy để embed như văn xuôi.
_Tránh dùng_: LaTeX, phương trình đã nhận dạng, text công thức trong chunk

**Tham chiếu công thức**:
Cặp `formula_id` và `char_start` trên chunk, trỏ tới marker công thức trong văn bản đầy đủ. Tham chiếu không
chứa raw công thức và không tham gia khoá băm định danh chunk.
_Tránh dùng_: nội dung công thức, formula text, chỉ số công thức theo trang

**Chú thích mồ côi**:
Caption do parser trả về nhưng không được bất kỳ hình hoặc khối nổi nào tham chiếu. Nó được giữ thành text tại
đúng reading order thay vì bị bỏ hoặc được gán ghép lại bằng bbox.
_Tránh dùng_: caption rác, caption mất, chú thích suy đoán

**Section**:
Một heading cùng vị trí của nó trong cây phân cấp. Section **không** được embed — nó chỉ sống trong bảng
riêng để các bước sau ráp ngữ cảnh lúc chạy.
_Tránh dùng_: mục, chương, heading

**Preamble**:
Các block nằm giữa một heading và heading con đầu tiên của nó. Đây là nội dung *trực tiếp* của section đó,
**không** phải toàn bộ subtree.
_Tránh dùng_: intro, phần mở đầu

**Window**:
Tập các chunk có cùng section cha trực tiếp. Là đơn vị đầu vào của bước trích khái niệm. Mỗi chunk thuộc
đúng một window — phân hoạch phủ hết và không chồng lấn.
_Tránh dùng_: batch, nhóm chunk, context window

**Reading order**:
Thứ tự đọc tự nhiên của con người trên toàn tài liệu, đánh số tăng dần toàn cục. Nguồn của mọi tín hiệu
"cái gì xuất hiện trước cái gì".
_Tránh dùng_: thứ tự trang, index

**Small-to-big**:
Cách truy hồi: tìm khớp trên chunk nhỏ để chính xác, rồi ráp cả window làm ngữ cảnh đưa cho mô hình.
_Tránh dùng_: parent retrieval, hierarchical search

**Artifact**:
Một tầng kết quả trung gian được đóng băng và đánh version độc lập. Ảnh là sản phẩm bên trong parse artifact,
không phải một tầng thứ tư. Các tầng tách rời nhau nên đổi tầng sau không phải chạy lại tầng trước.
_Tránh dùng_: cache, snapshot, output

### Khái niệm và đồ thị

**Ứng viên**:
Một khái niệm do bước trích xuất đề xuất từ đúng một window, chưa qua kiểm định trùng lặp.
_Tránh dùng_: candidate concept, concept thô

**Node canonical**:
Một khái niệm đã chốt danh tính sau khi hợp nhất các ứng viên trùng — có tên chuẩn, tập alias, mô tả hợp nhất.
_Tránh dùng_: concept, entity, node

**Provenance**:
Tập chunk nơi một khái niệm được **dạy** hoặc **định nghĩa**.
_Tránh dùng_: nguồn, xuất xứ, evidence

**Mention**:
Một chỗ trong tài liệu nơi khái niệm được **nhắc tới**, kể cả chỉ gọi tên hoặc diễn đạt lại. Rộng hơn
provenance và không trùng nó.
_Tránh dùng_: occurrence, xuất hiện

**Mention map**:
Ánh xạ từ chunk sang các khái niệm được nhắc tới tại đó, dựng bằng hai kênh: khớp tên chính xác và độ gần
ngữ nghĩa.
_Tránh dùng_: index, bảng tra

**Cụm ứng viên**:
Nhóm các ứng viên **nghi là cùng một khái niệm**, gom theo độ giống ngữ nghĩa để đem đi kiểm định trùng lặp.
Sau kiểm định thì co về một node.
_Tránh dùng_: cụm, cluster

**Cụm chủ đề**:
Nhóm các khái niệm **khác nhau nhưng liên quan**, gom trên bảng node canonical. Dùng làm đơn vị phân vùng
khi suy luận quan hệ tiên quyết và khi gom giai đoạn.
_Tránh dùng_: cụm, cluster, topic

> Hai khái niệm trên **khác hẳn nhau** và đều hay bị gọi tắt là "cụm". Cụm ứng viên là *cùng một khái niệm,
> nhiều tên*; cụm chủ đề là *nhiều khái niệm, cùng một mảng*.

**Siêu section**:
Nhiều section ngắn liền kề được gộp lại cho vừa một lời gọi mô hình.
_Tránh dùng_: super section, batch section

**Cặp chạm**:
Một cặp khái niệm thuộc hai cụm chủ đề khác nhau cùng được nhắc tới trong một chunk — giả thuyết rằng giữa
chúng có thể có quan hệ tiên quyết.
_Tránh dùng_: cặp ứng viên, co-occurrence pair

**Boundary concept**:
Khái niệm có góp mặt trong ít nhất một cặp chạm, tức nằm ở rìa giao giữa hai cụm chủ đề.
_Tránh dùng_: khái niệm biên, bridge node

**Requires**:
Loại quan hệ duy nhất tham gia lộ trình. `A requires B` nghĩa là muốn hiểu A phải biết B trước.
_Tránh dùng_: prerequisite, depends on, tiên quyết

### Lộ trình

**Stage**:
Một bậc trong lộ trình học — giao của một tầng topological với một cụm chủ đề, giới hạn số khái niệm để học
được trong một lần.
_Tránh dùng_: level, bước, module, bài
