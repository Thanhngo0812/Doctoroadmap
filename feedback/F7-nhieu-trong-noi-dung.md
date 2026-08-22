# F13–F15 🟠 — Rác lọt vào `text`, heading giả, và công thức toán bị nhân bản

Vòng review 2 · 2026-08-15 · Dữ liệu: `artifacts/chunks/nhap-mon-ml/v1`

Ba mục này khác F11/F12 ở chỗ: chúng **không phá cấu trúc**, chúng **làm bẩn nội dung**. Mà nội dung là thứ
sẽ đi thẳng vào embedding và vào prompt trích khái niệm ở T1.

---

## F13 🟠 — Thông báo lỗi của Docling nằm trong `text` của 9 chunk

### Bằng chứng

```
p9  tok=25  context_prefix=None
    '<!-- 🖼️❌ Image not available. Please use `PdfPipelineOptions(generate_picture_images=True)` -->'
```

Chunk này **không có gì ngoài thông báo lỗi**. Nó đã được lưu, đã được đếm token, và nếu bạn đã embed thì nó
đã trở thành một vector.

8 chunk còn lại có caption thật, nhưng vẫn kéo theo placeholder:

```
'Hình 4: Quy trình xây dựng một hệ thống dựa trên học máy.
<!-- 🖼️❌ Image not available. Please use `PdfPipelineOptions(generate_picture_images=True)` -->'
```

**Tổng: 9/132 chunk, 409/9195 token = 4.4% ngân sách token là thông báo lỗi.**

### Nguyên nhân

```python
# infrastructure/parsing/docling_parser.py:104
text = str(item.export_to_markdown(**kwargs))
```

Với `picture`, `export_to_markdown()` trả **caption + placeholder ảnh**. Code lấy nguyên khối. Nhánh dự phòng
ở dòng 108–109 (`if not text.strip(): text = self._caption(...)`) không bao giờ chạy, vì placeholder khiến
chuỗi luôn khác rỗng.

### Kèm theo: caption bị lặp hai lần

Dòng 124 gán `context_prefix=self._caption(item, document)` cho **mọi** node. Với figure, caption vì thế nằm
ở **cả hai** chỗ:

```
text           = 'Hình 1: Ví dụ về một email.\n<!-- ... -->'
context_prefix = 'Hình 1: Ví dụ về một email.'
```

8/132 chunk có `context_prefix`, và cả 8 đều là figure có caption trùng phần đầu `text`. Nếu B0.5 ghép
`context_prefix + text` trước khi embed — đúng như §13.3 dự tính — thì caption vào vector **hai lần**.

### Sửa

Đảo thứ tự ưu tiên cho `picture`/`figure`: lấy `_caption()` **trước**, chỉ dùng `export_to_markdown()` khi
không có caption, và luôn strip HTML comment `<!--…-->`. Figure không caption và không nội dung ⇒ **bỏ node**,
đừng tạo chunk rỗng nghĩa.

Riêng ba figure ở trang 7 — `'lychee-inspired spherical chair'`, `'a girl giving cat a gentle hug'`,
`'a small hedgehog holding a piece of watermelon'` — là **prompt DALL·E** minh hoạ, không phải caption mô tả
nội dung. Chúng đúng về mặt trích xuất nhưng vô nghĩa khi đứng một mình làm chunk. Đây là lý do nên chốt sớm
§13.2 (*block_type nào đủ tư cách làm evidence*): `figure` gần như chắc chắn **không** đủ.

---

## F14 🟠 — Heading giả nuốt nội dung thật

### `'trong đó:'` là một section có 4 chunk

Docling gán nhãn `section_header` cho cụm `trong đó:` ở trang 7 — đây là chữ "trong đó:" đứng sau một công
thức để liệt kê ý nghĩa các ký hiệu, **không phải tiêu đề mục**.

Kết quả:

```
section 'trong đó:'  path=['trong đó:']  → 4 chunk / 257 token
    p7  47tok [list_item] 'x x x là một quan sát (observation)…'
    p7  24tok [list_item] 'y có thể là tri thức mới hoặc kinh nghiệm mới…'
    p7 153tok [text]      'Trong thực tế, chúng ta thường không biết hàm y ∗…'
    p7  33tok [figure]    'a girl giving cat a gentle hug…'
```

Hai điều hỏng cùng lúc:

1. **257 token nội dung thật bị gán vào một section vô nghĩa.** `section_path = ['trong đó:']` là ngữ cảnh
   rỗng — nó không nói được chunk này thuộc mục nào của giáo trình.
2. **Nó cắt đôi window của mục thật.** `1.1.1 Vài quan điểm về ML` bắt đầu ở reading order 21; `trong đó:` xen
   vào ở 43; `1.1.2` bắt đầu ở 48. Nghĩa là phần cuối của mục 1.1.1 **bị tách khỏi** window của 1.1.1.

Cùng chuỗi `'trong đó:'` xuất hiện lại ở trang 8 và lần đó Docling gán `text` — thành chunk 3 token, nhỏ nhất
tài liệu. **Cùng một cụm từ, hai nhãn khác nhau, cách nhau một trang.** Đó là bản chất của model layout: nó
đoán theo hình dạng trình bày, không theo ngữ nghĩa.

Các heading đáng ngờ khác: `'Làm sạch dữ liệu'` (trang 20 — có thể là tiêu đề in đậm thật),
`'a) Chọn kiểu mô hình:'` và `'b) Chọn giải thuật học:'` (nhiều khả năng **hợp lệ**, là mục con của 1.2.2).

### Sửa: lọc ứng viên heading trong domain

Sau khi có luật suy level từ đánh số (F11), heading **không khớp mẫu số nào** phải qua một cửa kiểm:

- Kết thúc bằng `:` **và** không đánh số **và** bắt đầu bằng chữ thường → **không phải heading**, hạ xuống `text`
- Quá dài (> ~15 từ) → không phải heading
- Trùng một cụm đã từng xuất hiện với nhãn `text` ở nơi khác → đáng ngờ, bật `structure_warning`

Điều kiện đầu tiên một mình đã loại được `trong đó:` và giữ lại `a) Chọn kiểu mô hình:` (có đánh số `a)`).

Khi hạ một heading giả xuống `text`, nội dung của nó **quay về** đúng section cha — window của `1.1.1` liền
lại.

---

## F15 🟠 — Ký hiệu toán bị nhân bản glyph: 22% chunk dính

### Bằng chứng

```
p5  'cải thiện bản thân nó theo tiêu chí P P P khi giải quyết một nhiệm vụ T T T…'
p6  'T T T : Cần phán đoán một email cho trước có phải là thư rác hay không'
p6  'P P P : Độ chính xác của mô tả'
p7  'thu thập được một số quan sát { x x x 1 , x x x 2 , ..., x x xN } về đầu vào'
```

**29/132 chunk = 22%.**

Nguyên nhân: PDF vẽ chữ đậm toán học (`\mathbf{x}`) bằng cách **chồng cùng một glyph 3 lần** lệch nhau vài
phần trăm point. Docling đọc trung thực cả 3 lần. Đây là hành vi đã biết của trình trích xuất text PDF, không
phải lỗi Docling.

### Vì sao nghiêm trọng với **tài liệu này**

Đây là giáo trình học máy. `x`, `y`, `P`, `T`, `E`, `D` là **khái niệm trung tâm** — chúng chính là thứ T1
phải trích ra làm node của DAG. `x x xN` sẽ được tokenizer cắt thành mảnh vô nghĩa, và mọi truy vấn RAG về
"tập huấn luyện D" sẽ không khớp được với `D D D`.

### Kèm theo: node `formula` bị bỏ im lặng

Docling nhận **đúng 1 node `formula`** trong cả 20 trang, và node đó có `text` **rỗng**:

```
BỎ (text rỗng): {'document_index': 1, 'formula': 1}
```

Nó bị `if not text.strip(): continue` (`docling_parser.py:114`) loại bỏ, không để lại dấu vết. Một công thức
trong giáo trình ML **là nội dung**, không phải trang trí.

Ký hiệu toán còn sót trong text (đây là phần **may mắn giữ được**):
`∗`: 18 chunk · `∈`: 8 · `→`: 4 · `⊆`: 1 · `≥`: 1

### Sửa

Thêm một bước vào `normalize_text`: gộp glyph lặp liền kề.

```python
text = re.sub(r"\b(\w{1,2})( \1){1,}\b", r"\1", text)
```

Chính regex này đã tìm ra 29 chunk ở trên, nên tôi biết nó khớp đúng thứ cần khớp trên tài liệu này.

**Nhưng phải cẩn thận, và phải ghi vào ADR.** Đây là bước đầu tiên trong `normalize_text` **thay đổi nội
dung**, không chỉ chuẩn hoá hình thức. Mọi bước hiện có (NFC, gộp khoảng trắng, gỡ dấu nối, dịch dấu câu) đều
bảo toàn nghĩa. Bước này thì không — nó **xoá chữ**. Rủi ro dương tính giả:

- `"ha ha ha"` → `"ha"`   ❌ sai nghĩa
- `"xã xã"` (tên riêng lặp)  ❌
- `"1 1 1"` trong một bảng số  ❌

Giới hạn `\w{1,2}` giảm rủi ro nhưng không xoá được. Hai lựa chọn an toàn hơn, nên cân nhắc trước khi chọn
regex:

| Cách | Được | Mất |
|---|---|---|
| Regex trong `normalize_text` | Đơn giản, tất định, sửa được ngay | Có dương tính giả; đổi mọi `chunk_id` |
| Gộp glyph theo **bbox** ở adapter | Chính xác — chỉ gộp khi glyph **chồng nhau về toạ độ** | Cần chạm tới tầng glyph của Docling, phức tạp hơn nhiều |

Nghiêng về **regex, nhưng chỉ áp dụng cho chuỗi 1 ký tự viết hoa hoặc chữ cái Latin đơn** (`P P P`, `x x x`,
`D D D`) — đó là toàn bộ những ca thật trong tài liệu này, và `"ha ha ha"` thoát được.

Và **bắt buộc có test** cho cả hai chiều: gộp đúng ca toán, **không** gộp `"ha ha ha"`.
