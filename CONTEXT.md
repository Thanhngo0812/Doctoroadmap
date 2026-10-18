# doc2roadmap

Biến một tài liệu học thuật (PDF/DOCX) thành lộ trình học: trích khái niệm, dựng đồ thị tiên quyết, xếp thành
các giai đoạn học tuần tự.

## Language

### Ingestion (B0)

**Document tree**:
Cây các khối nội dung mà parser trả về từ một tài liệu, đã có thứ tự đọc toàn cục và cấp heading.
_Tránh dùng_: markdown, plain text, parse output

**Cây khai báo**:
Phân cấp heading lấy trực tiếp từ level/style mà nguồn hoặc parser cung cấp. Khi có từ hai level phân biệt trở
lên, đây là dữ liệu được tin sau đánh số tường minh trong text.
_Tránh dùng_: cây DOCX, level đúng mặc định, cây suy diễn

**Cây thoái hoá**:
Cây khai báo không còn biểu diễn phân cấp, thường vì mọi heading cùng level hoặc không có level. Chỉ trường hợp
này mới rơi về luật suy cấp từ text.
_Tránh dùng_: cây phẳng đúng, PDF tree, cây lỗi chung chung

**Run định dạng**:
Mảnh text riêng do thay đổi định dạng nội tuyến như chữ đậm, tên mã hoặc font trong cùng một câu. Với dòng chảy
không có bbox, các run liền nhau được nối trước khi tách câu/chunk nếu không chạm guard liệt kê.
_Tránh dùng_: đoạn văn, dòng, page fragment

**Khối phi ngôn ngữ**:
Leaf block đủ dài nhưng có tỉ lệ chữ cái Unicode quá thấp, như dòng kẻ toàn dấu chấm. Khối bị loại khỏi text
chunk kèm cảnh báo và đoạn đầu để audit; node gốc vẫn ở parse artifact.
_Tránh dùng_: block rác im lặng, ký hiệu ngắn, công thức

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
riêng để các bước sau ráp ngữ cảnh lúc chạy. Section mang vai trò vùng; chunk kế thừa vai trò này.
_Tránh dùng_: mục, chương, heading

**Vai trò vùng**:
Nhãn `noi_dung`, `bai_tap`, `de_cuong`, `mo_dau`, `hanh_chinh` hoặc `cuoi_sach` của section/chunk (v3 R1).
Lớp cấu trúc nhận chuỗi chương, mục lục và phần cuối từ bằng chứng trong tài liệu; một lượt mô hình gán các section còn lại.
Vùng kéo tới section kế tiếp cùng cấp hoặc cao hơn. Artifact nhãn là version chunks mới, giữ ID/text/offset; A10 đọc nhãn
tương thích với version chunk mà đồ thị A8 đã ghim.
_Tránh dùng_: trạng thái dạy (đó là thuộc tính của khái niệm), loại chunk, loại khái niệm

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

**Thực thể**:
Một đơn vị trong đồ thị: khái niệm, hình, bảng, hoặc bất kỳ kiểu nào mô hình tự đặt như `theorem`, `tool`,
`protocol`. Kiểu là nhãn mở; mọi luật hợp nhất và mô tả áp cho thực thể nói chung, không riêng khái niệm.
_Tránh dùng_: concept (khi ý là mọi kiểu), entity

**Ứng viên**:
Một thực thể do bước trích xuất sinh ra từ đúng một window, chưa qua kiểm định trùng lặp.
_Tránh dùng_: candidate concept, concept thô

**Node canonical**:
Một thực thể đã chốt danh tính sau khi hợp nhất các ứng viên trùng — có tên chuẩn, tập alias, mô tả hợp nhất.
_Tránh dùng_: concept, entity, node

**Cặp nghi trùng**:
Hai nhóm ứng viên mang tên khác nhau nhưng bị nghi là cùng một thực thể, nên được đưa cho mô hình phán ở A4.
Nguồn đề cử (ADR 0016): chung alias, tên gần giống, tên gần nghĩa theo vector tên, tên hoặc alias trùng sau chuẩn
hoá, viết tắt theo chữ đầu, và hai tên khác nhau đúng một tiền tố chung chung. Mô tả nháp và câu bằng chứng trùng
nhau không còn là nguồn đề cử. Ngoài các nhóm trùng tên sau chuẩn hoá, chỉ cặp nghi trùng mới có cơ hội được gộp.
_Tránh dùng_: cặp ứng viên, cặp trùng, candidate pair

**Tên chuẩn**:
Tên hiển thị của một node canonical — tên gọi đầy đủ mà chính tài liệu dùng nhiều nhất trong số tên của các
ứng viên thuộc node; alias không tranh làm tên chuẩn. Chữ viết tắt chỉ làm tên chuẩn khi các ứng viên không
có tên gọi đầy đủ nào. Đếm không chồng lấn: một lần xuất hiện của tên dài không được tính cho tên ngắn nằm trong nó.
_Tránh dùng_: tên chính, primary name, label

**Alias**:
Tên gọi khác mà chính tài liệu dùng cho cùng một thực thể, kể cả tên ở ngôn ngữ khác và chữ viết tắt tài
liệu thật sự dùng; luôn kèm câu bằng chứng. Alias là lý do để đem hai ứng viên ra phán trùng, không phải bằng
chứng rằng chúng đã trùng.
_Tránh dùng_: bí danh tự sinh, từ đồng nghĩa

**Ký hiệu**:
Dạng viết toán học không chứa từ ngữ nào mà tài liệu dùng thay cho một thực thể — `μ`, `x`, `t α`,
`P(A|B)`, một chữ cái đơn. Khác alias: không dùng để đề cử hay gộp ứng viên, không làm tên chuẩn, không dùng
để khớp mention, và `F` khác `f`. Chữ viết tắt như `ML`, `JWT` là alias, không phải ký hiệu.
_Tránh dùng_: alias ký hiệu, biến, notation

**Provenance**:
Tập chunk nơi một khái niệm được **dạy** hoặc **định nghĩa**. Chỗ chỉ nêu tên — kể cả khi bước trích xuất lấy
ứng viên từ đó, như một câu liệt kê — không phải provenance. Trong chuỗi gộp (ADR 0016), provenance là
`defining_chunk_ids`: các chunk A5 chọn khi viết mô tả, cộng chunk chứa câu neo. Stage `provenance` riêng chỉ còn ở
artifact chuỗi v3.
_Tránh dùng_: nguồn, xuất xứ, evidence, mọi chunk đã trích ra ứng viên

**Câu neo**:
Câu nguyên văn mà A5 chọn làm chỗ tài liệu dạy hoặc định nghĩa một khái niệm. Mô hình chỉ được chọn trong tối đa 6
câu ứng viên do mã dựng, lấy từ vùng nội dung: chunk nguồn, chunk có bằng chứng A3, chunk khớp tên hoặc alias, chunk
nhắc ký hiệu, chunk có tiêu đề mang tên. Mã bác mã câu không có trong danh sách và câu trích nằm ngoài ngữ cảnh
của ứng viên. Vị trí câu neo là vị trí dạy, dùng để xếp dãy học. Câu neo cùng tối đa hai câu sau nó trong chunk là
cửa sổ định nghĩa của A8.
_Tránh dùng_: câu bằng chứng (của A3), định nghĩa, anchor

**Trạng thái dạy**:
Kết luận trên cả tài liệu về việc khái niệm có được dạy ở đây hay không. A5 quyết trạng thái này cùng câu neo, mỗi
khái niệm một lời gọi, theo luật của C8. Mô hình chọn một trong sáu giá trị: `defined_here`, `introduced_by_example`,
`mentioned_only`, `prior_knowledge`, `not_subject_matter`, `uncertain`. Trên node, hai giá trị đầu được ghi là
`taught`.
- Khái niệm không có câu ứng viên trong vùng nội dung thì mã tự xếp `mentioned_only` hoặc `unchecked`, không gọi
  mô hình.
- `prior_knowledge` phải qua một lời xác minh độc lập. Không được xác nhận thì hạ xuống `uncertain`.
- `taught` và `uncertain` vào dãy học. `mentioned_only` và `unchecked` thành mục nhắc tới. `prior_knowledge` và
  `not_subject_matter` bị loại khỏi lộ trình.
_Tránh dùng_: cờ taught, độ tin, confidence

**Mention**:
Một chỗ trong tài liệu nơi khái niệm được **nhắc tới**, kể cả chỉ gọi tên hoặc diễn đạt lại. Rộng hơn
provenance và không trùng nó; chunk trích ra ứng viên mà không dạy khái niệm đó là mention.
_Tránh dùng_: occurrence, xuất hiện

**Mention map**:
Ánh xạ từ chunk sang các khái niệm được nhắc tới tại đó, dựng bằng hai kênh: khớp tên chính xác và độ gần
ngữ nghĩa.
_Tránh dùng_: index, bảng tra

**Cụm ứng viên**:
Nhóm các ứng viên **nghi là cùng một thực thể**, gom từ các cặp nghi trùng để mô hình phán trong một lượt.
Sau kiểm định ra một hoặc nhiều node canonical.
_Tránh dùng_: cụm, cluster

**Cụm chủ đề**:
Nhóm các khái niệm **khác nhau nhưng liên quan**, gom trên bảng node canonical. Dùng làm đơn vị phân vùng
khi suy luận quan hệ tiên quyết và khi gom giai đoạn.
_Tránh dùng_: cụm, cluster, topic

> Hai khái niệm trên **khác hẳn nhau** và đều hay bị gọi tắt là "cụm". Cụm ứng viên là *cùng một khái niệm,
> nhiều tên*; cụm chủ đề là *nhiều khái niệm, cùng một mảng*.

**Quan hệ đề xuất**:
Cạnh giữa hai node mà A3 hoặc mô hình phán cụm (2a) nêu kèm câu bằng chứng, chưa được kiểm lại. Kiểu cạnh để mở;
`subtype_of` (là một loại của) chỉ là một kiểu trong đó. Trường `origins` ghi nguồn đã nêu cạnh. Chỉ `requires` do 2b
duyệt mới tham gia lộ trình.
_Tránh dùng_: cạnh xác nhận, quan hệ chắc chắn

**Đầu ra tự mâu thuẫn**:
Câu trả lời phán cụm vừa gộp hai nhóm vào một node, vừa ghi một quan hệ giữa chúng; hoặc ghi quan hệ đồng nhất giữa hai
node mà nó để riêng. Mô hình phải phán lại cụm đó.
_Tránh dùng_: lỗi định dạng

**Siêu section**:
Nhiều section ngắn liền kề được gộp lại cho vừa một lời gọi mô hình.
_Tránh dùng_: super section, batch section

**Cặp chạm**:
Một cặp khái niệm thuộc hai cụm chủ đề khác nhau cùng được nhắc tới trong một chunk — giả thuyết rằng giữa
chúng có thể có quan hệ tiên quyết. Vô hướng: chỉ là lý do để đem cặp ra phán; chiều do 2b chốt.
_Tránh dùng_: cặp ứng viên, co-occurrence pair

**Viện dẫn**:
Khái niệm B được nhắc tới trong provenance của khái niệm A — tức lúc dạy A, tài liệu dựa vào B. Có hướng; là
bằng chứng rẻ rằng B có thể cần biết trước A, chưa phải quan hệ tiên quyết.
_Tránh dùng_: tham chiếu (đã dành cho hình, bảng, công thức), cặp chạm, reference

**Cặp nghi tiên quyết**:
Hai khái niệm học được mà ít nhất một nguồn đề cử — cặp chạm, viện dẫn hoặc quan hệ đề xuất — cho là có thể có
quan hệ tiên quyết. Vô hướng. Trong pass phụ, chỉ cặp nghi tiên quyết mới có cơ hội thành `requires`.
_Tránh dùng_: cặp ứng viên, candidate pair, cặp chạm (cặp chạm chỉ là một nguồn đề cử)

**Định tuyến**:
Luật chọn trục cho pass chính theo cấu trúc tài liệu: theo chương khi chương mục rõ, theo cụm chủ đề khi tài liệu
phẳng, một phiên duy nhất khi tài liệu có ít khái niệm học được. Ngưỡng tính theo số khái niệm, không theo số trang.
_Tránh dùng_: routing, luật 50 trang

**Pass chính**:
Lượt suy luận tiên quyết đi theo trục do định tuyến chọn — từng section của chương, hoặc từng cụm chủ đề. Mô hình tự
đề xuất cạnh giữa các khái niệm trong danh sách của phiên, kèm bằng chứng.
_Tránh dùng_: main pass, lượt mở

**Pass phụ**:
Lượt đi theo trục còn lại để bù điểm mù của pass chính. Chỉ phán các cặp nghi tiên quyết, không tự đề xuất cạnh.
Mặc định phán bằng mô hình học đóng băng (chế độ `ml`, ADR 0015), chỉ tạo cạnh cứng có câu trích; chế độ `llm` hỏi LLM từng cặp
vẫn chọn được.
_Tránh dùng_: secondary pass, lượt kiểm

**Khái niệm đích**:
Khái niệm được dạy trong đoạn văn mà một phiên của pass chính đang đọc; phiên hỏi cần biết gì trước để hiểu nó như
đoạn đó trình bày. Khái niệm được dạy ở nhiều nơi là khái niệm đích ở mọi nơi đó.
_Tránh dùng_: target, node nguồn

**Boundary concept**:
Khái niệm có góp mặt trong ít nhất một cặp chạm, tức nằm ở rìa giao giữa hai cụm chủ đề.
_Tránh dùng_: khái niệm biên, bridge node

**Requires**:
Loại quan hệ duy nhất tham gia lộ trình. `A requires B` nghĩa là muốn hiểu A phải biết B trước.
_Tránh dùng_: prerequisite, depends on, tiên quyết

### Lộ trình

**Dãy học**:
Thứ tự học đầy đủ của mọi khái niệm trên lộ trình: một phép sắp topo đồ thị `requires`, luôn lấy khái niệm sẵn sàng
đứng sớm nhất theo thứ tự dạy của tài liệu (ADR 0010). Lỗi thứ tự Q6 được chấm trên dãy này.
_Tránh dùng_: thứ tự tầng, layer order

**Cạnh mềm**:
Quan hệ `requires` còn giữ căn cứ nhưng không ép dãy học hay đóng tiên quyết, ví dụ chỉ có căn cứ ở bài tập hoặc đi ngược
thứ tự dạy trong sách. Cạnh vẫn ở artifact với `soft: true` và lý do để người kiểm có thể đọc.

**Nhắc tới**:
Khái niệm `mentioned_only` hoặc `unchecked` không thuộc dãy học; A10 đặt ở mục phụ của module nơi được nhắc đầu tiên,
hoặc tổng quan nếu không xuất hiện trong vùng dạy. Không được âm thầm tính là khái niệm đã dạy.

**Tiên quyết hiển thị**:
Các cạnh trực tiếp sau rút gọn bắc cầu, tối đa ba tên mỗi dòng; `prerequisites` đầy đủ và đồ thị gốc không bị sửa.
Phụ thuộc module cũng rút gọn bắc cầu; `roadmap-target` giữ trọn module cần học.

**Tên hiển thị**:
`display_name` là nhãn ngắn có căn cứ để đọc lộ trình, không thay `name` gốc hoặc `node_id` của khái niệm.
Nhãn đánh số chỉ được đổi khi câu neo có đủ từ cho tên mới; không dùng tên chung không có nội dung.

**Module**:
Đơn vị của lộ trình: một đoạn liền mạch của dãy học, tối đa 8 khái niệm, **có thứ tự bên trong** — một buổi học. Cạnh
`requires` được phép nằm trong một module (tiên quyết đứng trước trong module). Pha B mở khoá, làm quiz và lọc RAG
theo module.
_Tránh dùng_: stage (nghĩa cũ khác hẳn), bài, chặng

**Bản đồ danh tính**:
Ánh xạ `khái niệm → khái niệm đại diện` cho các khái niệm được phán là cùng một ý (vé v2-05). Chỉ gộp nhóm mà mọi
cặp đều được phán `same`; không sửa canonical. Lộ trình và bộ chấm áp cùng một bản đồ.
**Chỉ còn ở artifact chuỗi v3.** Chuỗi gộp gộp ngay ở A4 nên không có bản đồ này; thiếu `identity_map` được hiểu là
bản đồ rỗng (ADR 0016).
_Tránh dùng_: dedup, gộp alias (alias chung chỉ là lý do đưa ra xét)

**Ứng viên danh tính mở rộng**:
Cặp node canonical đưa ra phán vì tên/alias chuẩn hoá trùng, viết tắt theo chữ đầu, tiền tố chung chung, cùng câu
neo, hoặc top-3 độ gần mô tả bằng vector A6 với cosine ≥ 0,85 (v3 R8). Vector chỉ đề cử; mô tả và câu neo của cả
hai node đi vào lời phán. `same` vẫn phải kiểm đủ mọi cặp trong nhóm; gộp chạm vàng vẫn cần người duyệt.
**Chỉ còn ở artifact chuỗi v3.** Chuỗi gộp đưa ba nguồn tên đầu vào làm nguồn đề cử cặp nghi trùng ở A4. Hai nguồn
cùng câu neo và độ gần mô tả bị bỏ.
_Tránh dùng_: gộp bằng embedding, alias tự động

**Xác minh cặp gộp khác tên** *(trước gọi là "xác minh danh tính")*:
Lời gọi độc lập ở A4 cho mỗi cặp nhóm vừa được phán gộp mà không chung tên hay alias sau chuẩn hoá. Lời gọi chỉ thấy
hai hồ sơ (tên, alias, câu bằng chứng, mô tả nháp), không thấy lời phán trước. Chỉ quan hệ `dong_nhat` giữ gộp.
Các quan hệ trường hợp riêng, bằng nhau theo mệnh đề, mệnh đề khác, đối tượng khác loại và `khac` thành ràng buộc
"khác" khi dựng thành phần gộp. Quyết định của người duyệt (`a4 --merge-review`) thắng.
Ở artifact chuỗi v3, lượt này chạy sau phán danh tính (v3 R8b), trên câu neo thay cho câu bằng chứng. Đại diện ưu
tiên khái niệm `taught` sớm nhất; alias từ thành viên ghi nguồn `identity`. Cạnh đổi đầu mút được tính lại chiều
theo vị trí đại diện, giữ `order_relation_before_merge` để audit.
_Tránh dùng_: xác minh danh tính (tên cũ), coi bằng nhau là đồng nhất, xác minh là duyệt người

**Dự toán chạy thử**:
`roadmap --dry-run` chỉ đọc artifact và checkpoint đúng cấu hình, báo từng stage `tái dùng` / `sẽ chạy` / `chưa biết`.
Tổng USD chỉ cộng phần đã biết, không phải trần ngân sách. Không gọi mô hình, không ghi artifact hay checkpoint;
stage phụ thuộc đầu ra chưa có không được nhận một artifact cũ để làm giả dự toán đầy đủ.
_Tránh dùng_: chi phí thật, cam kết giá, chạy không có cờ (lệnh đó chỉ dừng ở lần chi đầu)

**Đường gọi mô hình**:
`developer_api` và `vertex` là hai đường vận chuyển cùng hợp đồng Gemini, không phải hai phương pháp trích xuất.
Đổi đường gọi không đổi `model_id`, prompt hash hay khóa cache; manifest và sổ chi ghi đường đã dùng.
Vertex lấy token qua Application Default Credentials và chuẩn hóa L2 embedding trước khi lưu.

**Stage** *(không còn là đơn vị của lộ trình)*:
Một tầng của phép xếp Coffman–Graham: các khái niệm học song song được, không cạnh `requires` nào nằm trong một
tầng. Chỉ còn trong biến thể đối chứng và artifact cũ. Tên stage pipeline `stages` của artifact graph giữ nguyên.
_Tránh dùng_ cho đơn vị lộ trình mới — dùng **Module**

**Cây mục khai báo (`declared-v1`, v4-14 R14c)**:
Hợp đồng API chunking khi bên cung cấp đã quyết định tập heading và cây cha–con.
`DocumentNode.level` là độ sâu nguyên thực của cây (gốc 1, không nhảy thiếu cấp);
heading rỗng, thiếu level, boolean hoặc số thực bị bác. Chunker giữ tập heading
và cha–con đã khai báo, không chạy luật bác heading hoặc ghi đè cấp mục.
Scheme tách khoá chunk nhưng tái dùng parse. Không bật ở CLI hoặc mặc định
Docling; không dùng cho cây level phẳng chưa xác minh. Đây là hợp đồng truyền
cây, **không** phải chứng nhận chất lượng bộ phân tầng nhẹ.

### Pha B (spec Pha B, 2026-10-15)

**Mô tả module**:
1–2 câu "học gì, cần gì trước" do LLM viết ở khâu tên; mỗi câu kèm `node_ids` mà mã kiểm. Hỏng thì dùng mô tả khuôn dựng từ đồ thị.
Số mục sách nằm ở `section_code`, không nằm trong tên.

**Bài giảng**:
Nội dung học của **một khái niệm**, mở khi người học bấm vào khái niệm đó (ADR 0011). Nút bấm và công cụ `get_lecture` của trợ lý trả cùng một bài.
- Phần do mã dựng hiện ngay.
- Phần LLM viết chỉ hiện dần sau cổng 2 ý giải thích đạt (ADR 0018, hợp đồng `lecture-2`).
- Bài hỏng hẳn vẫn giữ phần mã dựng, kèm lời nhắn; không bao giờ hiện bản lùi trích câu.

_Tránh dùng_: bài giảng của module, bài (theo nghĩa module), bản lùi (theo nghĩa thứ hiện cho người học)

**Ngữ cảnh đã lắp**:
JSON chuẩn hoá của mọi khối gửi mô hình cho một lần sinh. Băm của nó (`context_hash`) nằm trong khoá cache; đổi phiên bản đồ thị mà ngữ cảnh không
đổi thì không sinh lại.
_Tránh dùng_: khoá theo phiên bản đồ thị

**Nhãn nguồn**:
Mã ngắn thay cho `chunk_id` trong ngữ cảnh gửi mô hình. Mã giữ bảng tra nhãn → chunk, trang, vị trí. Các họ nhãn:
- `S#` đoạn, `N#` câu neo tiên quyết, `Q#` câu trích cạnh `requires`;
- `R#` cạnh mở, `H#` hình/bảng, `B#` bài tập, `CT#` công thức;
- `K#` khái niệm, `D#` ứng viên câu nhiễu.

**Nội dung ngoài sách**:
Ví dụ hay diễn giải không có trong tài liệu. Được phép khi có nhãn `outside_document` và khung riêng, không gắn trích dẫn. Định nghĩa, công thức và
khẳng định về nội dung sách không bao giờ thuộc loại này.

**Ngân hàng câu**:
Câu trắc nghiệm 3 phương án của **một khái niệm**: 2 câu ở hai mức Bloom, cache chung cho mọi người học. Mỗi câu đã qua luật mã và lời gọi kiểm giải mù.
_Tránh dùng_: quiz của module (quiz là một lần làm, rút từ ngân hàng)

**Lần làm**:
Một quiz cụ thể của một người học, rút từ ngân hàng của các khái niệm trong phạm vi; `origin` ∈ {`module_button`, `assistant`}. Lần làm chỉ để tự
kiểm tra, không khoá module, không tính trình độ.

**Giải mù**:
Lời gọi kiểm sau khi sinh câu hỏi. Mô hình nhận câu hỏi đã xáo phương án, không đánh dấu đáp án, rồi tự chọn phương án và phán từng phương án theo nguồn.

**Trợ lý**:
Agent gọi công cụ trên đồ thị học và chỉ mục, chỉ trong tài liệu đã tải lên (ADR 0012). Tối đa 5 vòng công cụ mỗi tin nhắn. Module đang mở là ưu tiên,
không phải ranh giới.

**Ngữ cảnh mồi**:
Phần mã lắp trước lời gọi đầu của trợ lý, gồm thẻ module đang mở, khái niệm liên kết được, và vài đoạn truy hồi có ưu tiên module.

**Khối nhắc khái niệm nền**:
Dòng do mã sinh ở cuối câu trả lời. Từ 2026-10-18:
- chỉ có ở phạm vi module;
- nhắc tối đa 3 tiên quyết Hasse **chưa đánh dấu đã học**, kèm câu trích;
- không lặp lại trong một phiên;
- không có ở câu từ chối.

**Tài liệu theo yêu cầu**:
Markdown có trích dẫn do công cụ `make_document` tạo theo yêu cầu tự do của một người học. Lưu theo người học, không cache chung.

**Lớp gán module**:
Đầu ra của A12 (ADR 0013): `module_id`, `all_module_ids` và `module_source` cho mỗi chunk của chỉ mục, không ghi lại vector. `module_source` có
ba giá trị:
- `chunk_module_map`;
- `hint` (module của chunk dạy đứng trước);
- `none`.

**Ảnh công thức**:
Ảnh cắt từ trang PDF theo `bbox` của nút công thức, làm sẵn ở bước tải tài liệu. Web thay nhãn `[CTk]` bằng ảnh này; LLM không tự viết công thức.

**Sổ chi Pha B**:
Dòng ghi cho mỗi lời gọi mô hình hay embedding ở Pha B: mục đích, token, USD, TTFT, tổng ms, `context_hash`, và `learner_id` với chi riêng của người
học. Trần ngày tính từ sổ này:
- 0,20 USD mỗi người cho trợ lý và tài liệu;
- khoảng 5 USD cho nội dung dùng chung.

### Pha B2 (spec Pha B2, 2026-10-18)

**Phạm vi** (của phiên, tài liệu, lần làm quiz):
Cả lộ trình, hoặc một module. Phạm vi chỉ quyết nơi lưu và nơi trợ lý ưu tiên tìm, không giới hạn chỗ tìm (ADR 0017).
- Phạm vi module lưu `node_ids` lúc tạo, rồi được giải sang module hiện hành có Jaccard cao nhất.
- Dưới 0,5 thì phạm vi **đã cũ** và chạy như phạm vi lộ trình.

_Tránh dùng_: ranh giới module; mã module như danh tính

**Phiên toàn lộ trình / phiên module**:
Phiên chat có phạm vi tương ứng. Phiên lưu đủ mọi lượt; mô hình chỉ nhận 3 lượt cuối. Tiêu đề do luật đặt; người học sửa và xoá được.

**Thư viện**:
Danh sách tài liệu và lần làm quiz của một phạm vi.
- Thư viện module gồm nội dung tạo ở đó (`here`), cộng nội dung tạo nơi khác có khái niệm thuộc module (`elsewhere`, nhãn "tạo ở nơi khác").
- Module của một nội dung được suy lúc liệt kê.

**Tiến độ** (đã học):
Đánh dấu theo khái niệm, không chặn gì (ADR 0019). Người học bấm, hoặc hệ thống đánh dấu khi làm đúng quiz; lựa chọn của người học thắng.
_Tránh dùng_: trình độ, mastery, mở khoá

**Gợi lại tiên quyết** (`recall`):
Phần mã dựng ở đầu bài giảng cho mỗi tiên quyết: tên, module, câu định nghĩa gập sẵn.

**Câu nối** (`bridge`):
Một câu trung tính do LLM viết, nói khái niệm đang học dùng tiên quyết ra sao, chỉ dựa câu trích cạnh `Q#`. Kiểm bằng K10–K12. Đồ thị không có câu trích
cạnh thì không có câu nối.

**Khối "Tiếp theo"** (`next_up`):
1–2 khái niệm sau cần khái niệm này, theo cạnh `requires` đi ra, kèm module và câu trích. Mã dựng, 0 USD.
_Tránh dùng_: `used_later`

**Nhãn theo người học** (`learner_status`):
Nhãn "đã học / chưa học, module m" cho tiên quyết và khối "Tiếp theo". Gắn lúc trả bài; không vào cache, khoá hay prompt.

**Cổng (stream sau cổng)**:
Mốc 2 ý giải thích đạt. Trước cổng, ý được giữ lại; sau cổng, ý hiện dần và bài không còn hỏng được.

**Bản ghi hỏng**:
Ghi nhớ một bài hỏng hẳn để lần bấm sau không gọi lại mô hình:
- hỏng vì luật kiểm: 24 giờ;
- hỏng vì mạng: 60 giây;
- chạm trần hệ thống: tới hết ngày.

Không phải bài trong cache.

### Web WayFinder (spec web, 2026-10-18)

**Khoá học**:
Đơn vị người dùng tạo, chia sẻ và tham gia. Trỏ tới đúng một `doc_id` và ghim `published_graph_version` (ADR 0020). Có đúng một chủ khoá.
_Tránh dùng_: lớp, khoá như một nhóm nhiều tài liệu

**Thành viên** (`owner` / `learner`):
Tài khoản đã tham gia khoá học, qua link mời, lời mời email, hay khoá mẫu. Người ngoài khoá nhận `not_found`.

**Dữ liệu học theo người × cuốn**:
Phiên, lượt, tiến độ, tài liệu, lần làm quiz khoá theo (`user_id`, `doc_id`), không theo khoá học. Hai khoá cùng cuốn dùng chung dữ liệu học của một người.

**Bản dựng** (`build`):
Một lần chạy Pha A cộng chuẩn bị Pha B trên một tệp tải lên, qua bốn bước `doc_reading`, `concepts`, `graph`, `learning_prep`. Dùng lại khi cùng SHA-256 và
cùng `pipeline_version`.
_Tránh dùng_: job, pipeline run (trong giao diện)

**Link mời / lời mời**:
Link mời: token trong URL, có hạn và số lượt, thu hồi được. Lời mời: theo email, chờ người được mời chấp nhận. Cả hai chỉ lưu băm token.

**Khoá mẫu**:
Khoá học admin đánh dấu, mọi tài khoản tham gia được không cần link. Chỉ tạo từ sáu cuốn phát triển.

**Mức dùng**:
Phần trần ngày của người học đã dùng (hiện tỉ lệ, không hiện USD), cộng số lượt dựng còn lại trong tháng.

**Tài sản** (`asset_key`):
Ảnh công thức, media, ảnh trang trên Cloudinary, riêng tư (ADR 0023). Cache chỉ chứa khoá tài sản; máy chủ chuyển ảnh, trình duyệt không cầm link
Cloudinary.

## Lệnh bậc 1–3 của lượt tập giữ lại (T10a; chỉ chạy sau khi khoá T10)

> **Chỉ chạy được với mã trước vé 19n.** Từ 19n, `roadmap --stop-after identity` và `--identity-review` đã gỡ, và `roadmap` từ chối canonical
> chuỗi v3. Muốn tái lập T10 đúng như đã khoá, dùng checkout sạch của commit `2c93c5a` (hoặc cũ hơn), như cách ghim mã của cổng 19l. Hai bậc
> `label-roles` vẫn chạy được với mã hiện tại, nhưng luật vai trò đã đổi ở vé 05a, nên kết quả sẽ khác bản đã khoá. Lượt đo mới trên tập giữ lại
> (T-01) đi theo chuỗi gộp, không theo khuôn này.

Các lệnh dưới đây là khuôn thao tác, **không phải lệnh cho phép mở vàng hay chạy tập giữ lại ngay**. Thay `<pdf-da-khoa>` và `<v-cay-moi>` bằng đường dẫn/version ghi trong bảng khoá; giữ chunk cũ xstk v2, doc-4 v3. Chạy riêng từng `DOC` (`xstk-ch3-1`, rồi `doc-4`), không sửa cấu hình giữa các bậc.

```powershell
$env:UV_CACHE_DIR='.uv-cache-local'
$DOC='xstk-ch3-1'; $OLD=2
.\.tools\uv.exe run doc2roadmap ingest <pdf-da-khoa> --doc-id $DOC --a1 docling --pdf-backend docling-parse --pdf-text-policy legacy --allow-text-quality-reason "Tái lập T10 trên văn bản xstk đã khóa; chấp nhận lỗi chữ VNI đã ghi nhận ở trang 3, không làm sạch hoặc đổi bộ đọc"
.\.tools\uv.exe run doc2roadmap label-roles --doc-id $DOC --dry-run --allow-text-quality-reason "Tái lập T10 trên văn bản xstk đã khóa; chấp nhận lỗi chữ VNI đã ghi nhận ở trang 3, không làm sạch hoặc đổi bộ đọc"
.\.tools\uv.exe run doc2roadmap label-roles --doc-id $DOC --allow-spend --allow-text-quality-reason "Tái lập T10 trên văn bản xstk đã khóa; chấp nhận lỗi chữ VNI đã ghi nhận ở trang 3, không làm sạch hoặc đổi bộ đọc"
.\.tools\uv.exe run doc2roadmap label-roles --doc-id $DOC --chunks-version $OLD --transfer-from-chunks-version <v-cay-moi> --dry-run --allow-text-quality-reason "Tái lập T10 trên văn bản xstk đã khóa; chấp nhận lỗi chữ VNI đã ghi nhận ở trang 3, không làm sạch hoặc đổi bộ đọc"
.\.tools\uv.exe run doc2roadmap label-roles --doc-id $DOC --chunks-version $OLD --transfer-from-chunks-version <v-cay-moi> --allow-spend --allow-text-quality-reason "Tái lập T10 trên văn bản xstk đã khóa; chấp nhận lỗi chữ VNI đã ghi nhận ở trang 3, không làm sạch hoặc đổi bộ đọc"
.\.tools\uv.exe run doc2roadmap roadmap --doc-id $DOC --dry-run --stop-after identity --allow-text-quality-reason "Tái lập T10 trên văn bản xstk đã khóa; chấp nhận lỗi chữ VNI đã ghi nhận ở trang 3, không làm sạch hoặc đổi bộ đọc"
.\.tools\uv.exe run doc2roadmap roadmap --doc-id $DOC --allow-spend --stop-after identity --allow-text-quality-reason "Tái lập T10 trên văn bản xstk đã khóa; chấp nhận lỗi chữ VNI đã ghi nhận ở trang 3, không làm sạch hoặc đổi bộ đọc"
.\.tools\uv.exe run python scripts/duyet-danh-tinh/tao_bang.py $DOC <v-identity> --no-gold --output-dir tmp/duyet-danh-tinh-giu-lai
```

Lệnh `ingest` phải mang đúng cột "cờ `ingest` bậc 1" của bảng khoá (`T10-cau-hinh-khoa.md`): xstk thêm `--a1 docling --pdf-backend docling-parse --pdf-text-policy legacy` và cờ lý do như khuôn trên cho ingest, label-roles, roadmap; doc-4 thêm `--a1 docling --pdf-backend pypdfium2 --heading-scheme vn-textbook`, giống chunks gắn A3 (doc-4 v3), để văn bản khớp khi chuyển vai trò. Từ v4-13, mặc định mới là pypdfium2; tái lập tài liệu cũ phải chỉ rõ bộ đọc đã khoá. Từ v4-14 R2-P, **cả hai lệnh tái lập cũ thêm `--pdf-text-policy legacy`** (adapter 11); không thay mặc định giữa các bậc của một lượt đã khoá.

Ingest mới mặc định `--pdf-text-policy preserve` (adapter 13): không xoá chuỗi chữ lặp như `G G G`/`x x x` chỉ dựa trên regex. Bản 13 thêm `parse_stats.caption_provenance`: chữ, tất cả bbox/charspan/gốc tọa độ và liên kết hình/bảng của caption nguồn, ghi rõ nhãn Docling chưa xác minh; không nhân đôi caption trong chunk. Phiên bản adapter nằm trong khoá cache; không dùng nhầm parse v11/v12. Cache/artifact cũ không bị ghi đè hay tự chuyển đổi. `legacy` giữ chính xác cleanup và khoá v11 khi các tham số khác không đổi; không có cờ tái lập adapter 12. `preserve` chưa phải khử glyph chồng dựa trên toạ độ: lỗi lặp từ bộ đọc nguồn có thể vẫn còn. Đây là sửa bảo toàn ký tự/provenance, không phải thay Docling bằng mô hình heading nhẹ.

Ở bậc 2b, chủ dự án duyệt **mọi** cặp trong bảng không vàng rồi xuất JSON quyết định T14. Chạy lại `roadmap --doc-id $DOC --identity-review <json-t14> --allow-spend --stop-after identity` và xác nhận artifact danh tính mới trước khi sang bậc 3. Bậc 3: `roadmap --doc-id $DOC --identity-review <json-t14> --dry-run` để lấy dự toán A8 thật; sau khi được duyệt chi mới chạy cùng lệnh với `--allow-spend` thay `--dry-run`. Bảng danh tính ở `tmp/` không chứa/chạm tệp vàng; nhãn vàng chỉ mở ở bậc 5 theo giao thức T10/07 v2.


Từ v4-16, `ingest` mặc định `--a1 nhe` (R2 full, PDF gốc). Cờ PDF/pipeline chỉ dùng với `--a1 docling`; mọi lượt tái lập cũ giữ `--a1 docling`. Bản nhẹ nhanh hơn nhưng không đạt luật chất lượng pha 4 của vé 15; đây là đánh đổi đã được chủ dự án duyệt, không phải kết luận chất lượng tương đương Docling.
