# Báo cáo chi tiết luồng xử lý tài liệu của `doc2roadmap`

**Ngày đối chiếu:** 2026-08-29
**Phạm vi code hiện có:** pha B0 — ingest PDF/DOCX, dựng cây section, tạo chunk, ráp window và lưu artifact JSON.  
**Ngoài phạm vi code hiện có:** embedding, trích khái niệm, hợp nhất khái niệm, đồ thị tiên quyết và xếp stage của roadmap.

## 1. Kết luận nhanh

Khi người dùng đưa một tài liệu vào bằng lệnh `doc2roadmap ingest`, hệ thống chạy theo chuỗi sau:

```text
CLI nhận đường dẫn + doc_id
        ↓
Đọc Settings và ghép các implementation thật
        ↓
Kiểm tra đầu vào, băm file và cấu hình
        ↓
Tìm parse_tree có thể tái sử dụng
        ↓ cache miss
Docling parse PDF/DOCX → DoclingDocument
        ↓
Docling adapter → ParsedDocument(DocumentTree + ảnh PNG)
        ↓
Chuẩn hóa text + dựng Section + tạo Chunk
        ↓
Ráp Window theo parent_section_id
        ↓
Lưu parse_tree + ảnh PNG và chunks thành artifact có version
        ↓
CLI in thống kê, cảnh báo và đường dẫn artifact
```

Hai định dạng đi chung luồng sau Docling nhưng khác ở adapter:

```text
PDF  → có page/bbox → sửa reading order trang một cột theo hàng → stitch đoạn đứt trang
DOCX → thứ tự block logic từ OOXML, thường page/bbox=None → nối run định dạng, không repair theo trang
```

Ba loại dữ liệu trung tâm:

| Dữ liệu | Ý nghĩa | Được lưu ở đâu |
|---|---|---|
| `DocumentTree` | Các block sau parse, có loại, text, reading order và provenance | `parse_tree/<doc_id>/vN/tree.json` |
| Ảnh PNG | Byte ảnh định danh bằng SHA-256, cùng version với cây parse | `parse_tree/<doc_id>/vN/images/<image_id>.png` |
| `Section` + `ChunkingResult` | Cây heading, chunk, full text chuẩn hóa và cảnh báo | `chunks/<doc_id>/vN/*.json` |
| Window | Các chunk có cùng section cha trực tiếp | Không lưu riêng; ráp lại từ `chunks.json` |

## 2. Kiến trúc và chiều phụ thuộc

Project chia thành bốn lớp:

```text
presentation ───────┐
                    ↓
composition → application → domain
                    ↑
              infrastructure
```

- `domain` chỉ dùng Python standard library. Đây là nơi giữ model và thuật toán chunk thuần.
- `application` điều phối use case qua `Protocol`; không import implementation infrastructure.
- `infrastructure` bọc Docling, SentencePiece và filesystem JSON.
- `presentation` là CLI mỏng.
- `composition.py` là composition root duy nhất biết cả use case lẫn implementation thật.

Hai test kiến trúc trong [`tests/unit/test_architecture.py`](../tests/unit/test_architecture.py) khóa chiều phụ thuộc này:

1. `domain` không được import package ngoài hoặc layer khác của project.
2. `application` không được import `infrastructure`.

## 3. Luồng `ingest` đầy đủ

Ví dụ lệnh:

```powershell
.\.venv\Scripts\doc2roadmap.exe ingest `
  "C:\Users\ngoco\Downloads\book.pdf" `
  --doc-id book
```

### Bước 1 — CLI phân tích tham số

File: [`src/doc2roadmap/presentation/cli/main.py`](../src/doc2roadmap/presentation/cli/main.py)

`_parser()` khai báo hai subcommand:

```text
ingest <file> --doc-id <id>
inspect --doc-id <id>
```

Với `ingest`, `_ingest()`:

1. kiểm tra đường dẫn là file;
2. gọi `build_ingest()`;
3. đọc toàn bộ file thành `bytes`;
4. truyền `bytes`, tên file, `doc_id` và cấu hình chunk vào use case;
5. in summary, parse statistics, warning và artifact path.

CLI bắt mọi exception ở `main()`, in `lỗi: ...` ra stderr và trả exit code `2`. Thành công trả `0`.

### Bước 2 — Đọc cấu hình và ghép dependency

Files:

- [`src/doc2roadmap/config.py`](../src/doc2roadmap/config.py)
- [`src/doc2roadmap/composition.py`](../src/doc2roadmap/composition.py)

`Settings` dùng `pydantic-settings`, đọc biến môi trường có tiền tố `DOC2ROADMAP_` và file `.env`:

| Setting | Mặc định | Vai trò |
|---|---:|---|
| `max_tokens` | 512 | Trần mềm cho chunk văn xuôi |
| `max_table_tokens` | 2048 | Trần mềm cho bảng và nhóm có chứa bảng |
| `hard_cap_tokens` | 6000 | Trần tuyệt đối cho mọi chunk, không có ngoại lệ |
| `target_tokens` | 256 | Mục tiêu đóng nhóm leaf block |
| `sentence_overlap` | 1 | Số câu overlap khi cắt một block dài |
| `artifact_dir` | `artifacts` | Thư mục artifact |
| `tokenizer_model` | `vendor/gemma/tokenizer.model` | SentencePiece model cục bộ |
| `tokenizer_id` | `google-gemma-sentencepiece-v1` | Tên logic của tokenizer |

`build_ingest()` tạo đúng bốn dependency của `IngestDocument`:

```text
DoclingParser
JsonArtifactStore
SentencePieceTokenCounter
UnicodeSentenceSplitter
```

Tokenizer được nạp ngay khi composition chạy. Nếu thiếu model, lệnh dừng trước khi parse.

### Bước 3 — Validate và tạo cache key

File: [`src/doc2roadmap/application/use_cases/ingest_document.py`](../src/doc2roadmap/application/use_cases/ingest_document.py)

`IngestDocument.execute()` kiểm tra:

- `doc_id` phải khớp `[A-Za-z0-9][A-Za-z0-9._-]{0,127}`;
- file chỉ được là `.pdf` hoặc `.docx`;
- source bytes không rỗng;
- `0 < target_tokens <= max_tokens` và cả hai trần mới đều dương;
- `sentence_overlap >= 0`.

Regex `doc_id` đồng thời chặn `../` và separator đường dẫn, tránh ghi artifact ra ngoài thư mục dự kiến.

Use case tạo ba hash/identifier quan trọng:

```text
source_hash         = SHA-256(bytes của file)
parser_config_hash  = SHA-256({Docling version, adapter version})
config_hash         = SHA-256(parser + normalization + chunk + tokenizer)
```

`parser_config` hiện gồm:

```json
{
  "adapter": "docling:2.114.0",
  "adapter_version": 8,
  "image_scale": 2.0
}
```

`config` đầy đủ còn chứa:

- khai báo normalization;
- `CHUNK_ALGORITHM_ID = "section-id-v8"`;
- `max_tokens`, `max_table_tokens`, `hard_cap_tokens`, `target_tokens`, `sentence_overlap`;
- identifier của tokenizer, gồm digest model.

### Bước 4 — Tìm parse tree đóng băng

Files:

- [`src/doc2roadmap/application/ports/artifacts.py`](../src/doc2roadmap/application/ports/artifacts.py)
- [`src/doc2roadmap/infrastructure/artifacts/json_store.py`](../src/doc2roadmap/infrastructure/artifacts/json_store.py)

Use case gọi:

```python
store.find_parse(doc_id, source_hash, parser_config_hash)
```

Store duyệt các version `parse_tree/<doc_id>/vN` từ mới về cũ. Parse tree được tái sử dụng khi cả hai giá trị khớp:

```text
source_hash
parser_config_hash
```

Do cache parse không phụ thuộc chunk config:

- đổi `target_tokens` không parse lại Docling;
- đổi tokenizer không parse lại Docling;
- đổi `CHUNK_ALGORITHM_ID` không parse lại Docling;
- đổi code adapter phải tăng `ADAPTER_VERSION`, khi đó parse lại;
- đổi `image_scale` làm parser config hash đổi và parse lại;
- đổi version Docling hoặc nội dung file cũng parse lại.

Nếu cache hit, luồng bỏ qua toàn bộ Docling và đi thẳng tới `chunk_document()`.

### Bước 5 — Docling parse source bytes

File: [`src/doc2roadmap/infrastructure/parsing/docling_parser.py`](../src/doc2roadmap/infrastructure/parsing/docling_parser.py)

`DoclingParser.parse()`:

1. kiểm tra suffix lần nữa ở boundary của adapter;
2. ghi source bytes vào temporary file giữ đúng `.pdf`/`.docx`;
3. lazy-create `DocumentConverter` ở lần gọi đầu; cấu hình PDF bật `generate_picture_images` và ghim `images_scale=2.0`;
4. gọi `converter.convert(temp_path).document`;
5. chuyển `DoclingDocument` qua `adapt()` thành `ParsedDocument`, gồm cây miền và dictionary byte ảnh;
6. với DOCX có `wordprocessingShape`, thêm `missing_image` hướng dẫn LibreOffice vào kênh cảnh báo hệ thống;
7. xóa temporary file trong `finally`, kể cả khi parse lỗi.

`DocumentConverter` được cache trong một instance `DoclingParser`. Nó được tái sử dụng nếu cùng process gọi parser nhiều lần; mỗi lần chạy CLI mới vẫn tạo process và converter mới.

### Bước 6 — Adapter chuyển Docling item thành `DocumentNode`

`adapt()` duyệt:

```python
for item, tree_level in document.iterate_items():
```

Ánh xạ label chính:

| Docling label | `DocumentNode.node_type` | Text lấy từ đâu |
|---|---|---|
| `title`, `section_header` | giữ nguyên | `item.text` |
| `table` | `table` | Markdown export của Docling |
| `picture`, `figure` | `figure` | caption, nếu không có thì marker `[figure]` |
| `formula` | `formula` | marker `[formula]`; raw ở `DocumentNode.raw_text` |
| `caption` có ref từ khối nổi | bị loại | nội dung đã nằm trên figure/table tương ứng |
| `caption` không có ref | `text` | `item.text`, giữ tại đúng reading order |
| label khác | label đó hoặc `text` | ưu tiên `item.text`, rơi về `item.orig` |

Các item bị loại có chủ đích:

```text
page_header
page_footer
page_number
caption đã được khối nổi lấy lại
```

Item chỉ bị loại khi cả `text` và `orig` rỗng sau clean, đồng thời sinh warning
`empty_node: dropped <label>`. Công thức băm SHA-256 raw đã chuẩn hoá thành `formula_id`; raw không đi vào text
được embed.

Mỗi node có thể mang:

- `level`: raw heading level;
- `page` và `bbox`: từ provenance đầu tiên;
- `context_prefix`: caption của non-figure item;
- `image_id`: SHA-256 của byte PNG với node figure ở mọi định dạng;
- `table_rows` và `table_id`: ma trận ô Docling cùng SHA-256 của các ô đã chuẩn hoá;
- `tree_depth`: depth khi Docling duyệt tree;
- `raw_text` và `formula_id`: raw parser cùng content ID của công thức;
- `reading_order`: ban đầu là thứ tự adapter nhận item.

Adapter không còn gọi Markdown export làm fallback cho figure, nên data URI base64 không thể lọt vào text. Với
PDF lẫn DOCX, mỗi hình lấy được byte sẽ được encode PNG, băm SHA-256 và đưa vào `ParsedDocument.images`; figure
không lấy được byte giữ marker và phát `missing_image` kèm lý do. Regex còn gộp artifact glyph như
`P P P` thành `P`, nhưng không gộp từ tự nhiên như `ha ha ha`; Unicode lookbehind giữ đúng ký hiệu trong
`các c c c`.

Với PDF, cùng pass cleaning còn tra toàn bộ Adobe Symbol entry có đích Unicode ngoài PUA từ
`U+F000–U+F0FF`; ô bảng và raw cũng đi qua pass này. `symbol_characters_mapped` ghi số lần thay thế. Glyph
corporate-use không có đích Unicode đọc được được giữ lại và tạo một warning `remaining_private_use: N` thay
vì bị đoán. Nhánh DOCX không áp bảng tra.

#### Nhánh PDF

PDF thường có `page` và `bbox`. Sau khi tạo node, adapter chạy hai repair pass:

```text
repair reading order
        ↓
stitch page-break fragment
```

**Repair reading order:**

- gom node theo page;
- chỉ tự sort khi mọi node có bbox và các content block không tạo những dải ngang tách rời;
- figure/formula/footnote/caption mồ côi không tham gia nhận diện số cột;
- trên trang chắc chắn một cột, các block chồng dọc quá nửa chiều cao block ngắn hơn được gom thành cùng một hàng;
- các hàng được đọc từ trên xuống, còn block trong cùng hàng được đọc từ trái sang phải;
- trang có dấu hiệu đa cột giữ reading order của Docling.

**Stitch page break:**

- bỏ qua figure/formula/footnote/caption mồ côi khi tìm fragment kế tiếp nhưng không xóa chúng;
- hai node phải thuộc `text`, `paragraph` hoặc `list_item`;
- node sau phải ở đúng trang kế tiếp;
- node trước không kết thúc bằng `. ! ? :` kể cả dấu đóng và số cước chú;
- node sau bắt đầu bằng chữ thường;
- nối hai text bằng một space và hấp thụ node sau vào node trước.

Sau repair, adapter đánh lại `reading_order = 0..N-1` và ghi:

```text
items_total
nodes_kept
dropped theo label
captions total/recovered/orphaned
images_extracted
pages_reordered
page_breaks_stitched
runs_stitched
symbol_characters_mapped
stripped_pua_bullets
```

**Giới hạn:** trang đa cột hiện tin Docling; stitch không nối continuation bắt đầu bằng chữ hoa; node stitch giữ page/bbox của fragment đầu.

#### Nhánh DOCX

Docling đọc thứ tự logic từ OOXML. Trong fixture DOCX thật của project, heading, paragraph và table đều có:

```text
page=None
bbox=None
```

Adapter không repair reading order và không stitch theo trang. Sau đó, pass không-bố-cục nối chuỗi text run
liền nhau khi cả hai không có bbox, run trước chưa kết câu và run sau không mở một mục liệt kê/đánh số mới.
Pass nối tiếp tục trên node vừa nối, nên ba mảnh `bằng` / `Docker Compose` / `, thực hiện` thành một câu; dấu
phẩy được gắn không thêm space. Dòng mục lục kết thúc bằng số trang và list item thật là guard không nối.

Ảnh raster DOCX đi cùng đường băm/lưu/tham chiếu của PDF. DrawingML shape không render được khi thiếu
LibreOffice tạo cảnh báo `missing_image` từ OOXML source. `runs_stitched` và `stripped_pua_bullets` ghi số lần
xử lý vào parse stats.

### Bước 7 — Lưu parse artifact

Khi parse cache miss, `save_parse()` tạo version kế tiếp:

```text
artifacts/
└── parse_tree/
    └── <doc_id>/
        └── vN/
            ├── images/
            │   └── <sha256>.png
            ├── tree.json
            └── manifest.json
```

`tree.json` chứa `DocumentTree` và chỉ giữ `image_id`; byte ảnh không nằm trong JSON miền. `images/` chỉ được
tạo khi parser trả ảnh. `manifest.json` chứa source hash, config/hash, parser config hash, parse stats, version
và timestamp UTC.

Mỗi JSON hoặc PNG được ghi qua file `.tmp` rồi `os.replace()`, nên riêng từng file được replace nguyên tử.

### Bước 8 — Chuẩn hóa và dựng cấu trúc

Files:

- [`src/doc2roadmap/domain/normalization.py`](../src/doc2roadmap/domain/normalization.py)
- [`src/doc2roadmap/domain/chunking.py`](../src/doc2roadmap/domain/chunking.py)

`chunk_document()` nhận `DocumentTree`, sort lại theo `reading_order`, rồi tạo root section:

```text
title = <document>
level = 0
order_index = -1
section_path = []
```

#### Chuẩn hóa text

`normalize_text()` chạy trên từng heading/leaf block:

- chuẩn hóa CRLF/CR về LF;
- xóa soft hyphen;
- nối từ bị hyphen hóa qua newline trong cùng block;
- đổi smart quote và các loại dash về ASCII;
- gộp horizontal whitespace, bỏ dòng rỗng;
- chuẩn hóa Unicode NFC;
- không lowercase và không bỏ dấu tiếng Việt.

#### Nhận heading thật và heading giả

Heading dùng chuỗi bằng chứng mạnh trước, yếu sau:

```text
1. đánh số tường minh trong text
   1 / 1.2 / 1.2.3                              → level 1 / 2 / 3
   A. / A) / Đ.                                  → sâu hơn numbered heading đang mở một cấp
   chuỗi chung tiền tố + số khác nhau, có heading chen giữa
     Kapitel 1 ... Kapitel 2 / 第1章 ... 第2章      → level 1
   chuỗi bao trùm lồng nhau                       → level ngoài + 1
2. raw level, nếu toàn cây khai ít nhất hai level phân biệt
3. suy diễn hiện hành, nếu cây khai phẳng hoặc thiếu level
```

Đánh số text thắng raw level khi mâu thuẫn. Heading không đánh số trong cây thoái hoá trước numbered heading
đầu tiên được coi là level 1; sau đó được coi là con của numbered level đang mở. Ba PDF corpus khai phẳng nên
giữ hành vi cũ; DOCX khai level 1/2 nên giữ đúng style Word.

Chuỗi chương tự hiệu chỉnh không dùng danh sách từ khoá ngôn ngữ. Từ hai heading trở lên chung tiền tố có chữ
đứng ngay trước chữ số/số La Mã khác nhau tạo một chuỗi và được miễn heuristic heading lặp. Chuỗi chỉ nhận cấp
chương khi giữa ít nhất một cặp thành viên liên tiếp có heading khác, nên `Bài tập 1 / Bài tập 2` đứng sát nhau
không thành chương; tiền tố chỉ có ký hiệu như `§` cũng không tham gia. Heading chương đơn lẻ và phụ lục không
đánh số là gap đã chấp nhận và đi luật thường.

Candidate heading bị hạ thành text nếu:

- kết thúc bằng `:` và bắt đầu bằng chữ thường, ví dụ `trong đó:`; hoặc
- dài hơn 15 từ;
- không đánh số và text của nó xuất hiện ít nhất hai lần trong body block của cùng tài liệu; hoặc
- bắt đầu bằng bullet/dash Unicode;
- ngoại lệ: heading có đánh số không bị hạ bởi các heuristic lặp/độ dài/dấu hai chấm.

Khi hạ heading, hệ thống thêm warning có lý do và raw (`rejected_heading...`) rồi tiếp tục cho nó vào dòng leaf
text, nên nội dung vẫn thuộc section cha.

#### Dựng cây section bằng stack

Mỗi heading thật:

1. flush nhóm text đang chờ;
2. suy level;
3. dùng `tree_depth` để clamp nếu raw nesting nói heading mới là con nhưng level suy ra không sâu hơn cha;
4. pop stack cho đến khi gặp cha có level thấp hơn;
5. tạo `section_path = parent.path + [title]`;
6. tạo `Section`, push lên stack;
7. tăng `result_order`.

Heading không đi vào `normalized_full_text` và không sinh chunk. Tuy nhiên heading và chunk dùng chung trục `result_order`, vì vậy `Chunk.order_index` có thể có khoảng trống. Khoảng trống là vị trí của section heading, không phải mất chunk.

Nếu có ít nhất bốn heading và mọi level suy ra đều giống nhau, hệ thống thêm warning `flat_heading_tree`.
Trước khi trả result, mọi warning giống hệt toàn chuỗi được gom ổn định theo lần xuất hiện đầu (`... ×N`). Hai
warning cùng loại nhưng khác raw/location vẫn là hai chuỗi và được giữ riêng. Chính danh sách result này được
ghi đồng thời vào document, manifest và CLI.

### Bước 9 — Chuyển leaf block thành full text và chunk

Mỗi non-heading node:

1. chuyển table rows thành Markdown nếu `table_rows` có dữ liệu;
2. normalize text;
3. loại block dài có tỉ lệ chữ cái dưới 10% và vùng mục lục gồm chuỗi dòng khớp đa số heading nội bộ; mỗi
   vùng bị loại phát `non_linguistic_block` hoặc `toc_block` kèm excerpt;
4. gán owner là section đang ở đỉnh stack;
5. đánh `owner.has_direct_content = True`;
6. nối leaf vào `normalized_full_text` bằng đúng một newline giữa các leaf;
7. ghi `char_start`/`char_end` tích lũy;
8. đưa `_LeafBlock` vào hàng đợi chunk.

Node bị lọc vẫn tồn tại trong parse tree đóng băng; chỉ text/chunk bỏ nó. Ngưỡng chiều dài 100 ký tự bảo vệ
khối kỹ thuật ngắn như `x = 5`. Vùng mục lục chỉ được nhận khi các dòng có số trang và có ít nhất hai ứng viên
liền nhau, nên một câu văn nhắc một heading không bị nuốt.

#### Gộp quanh mục tiêu 256 token

Sáu loại được gộp:

```text
text
paragraph
list_item
figure
table
formula
```

Luật hàng đợi:

```text
block không được gộp (footnote/...)
    → flush text đang chờ
    → block đặc biệt đứng một mình

text mới khác section hoặc làm candidate vượt trần áp dụng
    → flush nhóm cũ

text mới được thêm làm tổng >= target_tokens
    → flush nhóm mới
```

Candidate chỉ có văn xuôi dùng trần 512; candidate có bảng dùng trần 2048. Mục tiêu đóng nhóm vẫn là 256 cho
cả hai, nên bảng nhỏ không hút văn xuôi đến 2048. Nhóm cuối section có thể nhỏ hơn 256.

Ví dụ:

```text
110 token + 90 token = 200  → chờ
200 token + 70 token = 270  → đóng chunk
```

Không gộp qua section. Footnote vẫn luôn làm pending đóng lại. Figure đi qua luật văn xuôi; bảng dùng trần
riêng và bảng lớn tự bị `_table_parts()` cắt theo hàng trước khi đưa vào hàng đợi.

#### Cắt block văn bản dài

Nếu một block đơn lẻ vượt `max_tokens`, `_sentence_groups()` dùng `UnicodeSentenceSplitter` để ráp các câu vừa trần và overlap một số câu theo cấu hình.

Nếu splitter chỉ trả một span bao trọn block vượt trần, chunk ghi
`oversize_reason="sentence_splitter_no_boundary"`; chunk result đồng thời thêm warning kèm trang hoặc section.
Bộ tách bỏ qua dấu kết câu nếu ký tự chữ-số có nghĩa tiếp theo là chữ thường, nên không cắt nhầm ba dạng
`do dự… rồi`, `U.S.A. là` và `"tuyệt!" rồi`.

#### Cắt bảng

`_table_parts()`:

- giữ bảng ngắn nguyên khối;
- với Markdown table dài, lặp hai dòng header ở mỗi phần;
- thêm từng row cho đến khi phần kế tiếp vượt trần;
- row đơn lẻ vượt trần bảng tạm mang `oversize_reason="table_row_exceeds_max_tokens"` trước bước trần cứng.

Bảng giữ nguyên vượt trần văn xuôi 512 nhưng chưa vượt trần bảng 2048 mang
`oversize_reason="table_kept_whole_above_text_limit"`. Vì vậy bảng slide 513 token và bảng xstk 628 token
được phép tồn tại nhưng không còn vượt 512 im lặng. Văn xuôi vượt 512 không có ranh câu vẫn dùng
`sentence_splitter_no_boundary`; trong trần để `oversize_reason` rỗng.

Docling adapter giữ cả Markdown text, ma trận `DocumentNode.table_rows` và `table_id` băm từ ma trận đã chuẩn
hoá. Chunker dựng markdown từ ma trận; cấu trúc hàng cột không bị nhân đôi sang chunk artifact.

#### Trần cứng cuối luồng

Sau cắt câu/cắt hàng, `_hard_cap_spans()` kiểm từng mảnh. Mảnh trên 6000 token được cắt lùi tại khoảng trắng
trong 10% cuối trước trần; nếu không có thì cắt đúng trước trần tại ranh giới cụm ký tự, không tách dấu kết hợp
khỏi ký tự gốc. Mọi mảnh mang `oversize_reason="hard_cap_forced_split"`; span liền mạch và `table_id` được giữ.

#### Định danh tất định

ID dùng BLAKE2b digest 12 bytes:

```text
section_id = hash(doc_id, section_path, section_occurrence)
chunk_id   = hash(doc_id, parent_section_id, normalized_text,
                  split_index, chunk_occurrence)
```

`reading_order` và `char_span` không nằm trong hash, nên chèn một block ở đầu không làm đổi ID của nội dung không đổi phía sau. Counter occurrence xử lý section/chunk trùng nội dung.

#### Char span

Mỗi chunk lưu:

```text
char_start
char_end
```

Bất biến chính:

```python
normalized_full_text[char_start:char_end] == chunk.text
```

Với chunk gộp, span bao gồm các newline giữa leaf. Với sentence overlap, các span chunk có thể chồng lấn nhưng mỗi span vẫn cắt ra đúng text chunk.

Mỗi figure, table hoặc formula trong span sinh `image_ref`, `table_ref` hoặc `formula_ref` gồm content ID và
`char_start`. Vị trí dùng cùng hệ tọa độ của `normalized_full_text`; ba danh sách ref không được truyền vào
`_chunk_id()`, nên đổi riêng ID tham chiếu không đổi ID chunk. Mọi mảnh row-split của một table dùng lại
`table_id` của node gốc.

### Bước 10 — Đếm token và cắt câu

Files:

- [`src/doc2roadmap/infrastructure/text/tokenizer.py`](../src/doc2roadmap/infrastructure/text/tokenizer.py)
- [`src/doc2roadmap/infrastructure/text/sentence_splitter.py`](../src/doc2roadmap/infrastructure/text/sentence_splitter.py)

`SentencePieceTokenCounter`:

- yêu cầu model cục bộ tồn tại;
- băm model lấy 12 ký tự đầu của SHA-256;
- identifier có dạng `<model_id>:<digest>`;
- gọi SentencePiece encode và lấy độ dài danh sách token.

Digest làm thay đổi chunk config hash khi model file thay đổi dù tên logic giữ nguyên.

`UnicodeSentenceSplitter` trả `TextSpan`, không trả text copy. Nó tạm che:

- các bộ viết tắt dạng dữ liệu: common Latin và bộ tiếng Việt;
- dấu chấm thập phân giữa hai chữ số.

Sau đó nhận boundary có-space ở `.`, `!`, `?`, `…` và boundary không cần space ở `。`, `！`, `？`, danda,
dấu Ả Rập và Khmer, kể cả dấu đóng quote/bracket. Colon không phải sentence boundary; masking giữ nguyên độ dài
nên mọi offset vẫn trỏ vào chuỗi gốc.

### Bước 11 — Ráp window

File: [`src/doc2roadmap/application/windows.py`](../src/doc2roadmap/application/windows.py)

`assemble_windows()` sort chunk theo `order_index`, rồi group theo `parent_section_id`:

```python
windows[chunk.parent_section_id].append(chunk)
```

Window chỉ chứa nội dung trực tiếp của section. Chunk thuộc section con không được đưa ngược lên window của cha.

Section không có direct content vẫn tồn tại trong `sections.json`, nhưng không có key trong windows.

Windows không được lưu thành file riêng vì có thể ráp tất định, tuyến tính từ `chunks.json`.

### Bước 12 — Lưu chunk artifact

Store tìm artifact chunk cũ theo:

```text
source_hash + config_hash
```

Nếu không có, nó tạo:

```text
artifacts/
└── chunks/
    └── <doc_id>/
        └── vN/
            ├── sections.json
            ├── chunks.json
            ├── document.json
            └── manifest.json
```

| File | Nội dung |
|---|---|
| `sections.json` | Danh sách `Section` gồm tree relation/path/order/direct-content flag |
| `chunks.json` | Danh sách `Chunk` gồm ID, span, owner, text, refs, token và `oversize_reason` |
| `document.json` | `normalized_full_text` và structure warnings |
| `manifest.json` | version, hash, config, parse version, warning, timestamp |

Lưu ý: use case hiện vẫn chạy `chunk_document()` và `assemble_windows()` trước khi `save_chunks()` phát hiện chunk artifact cùng hash đã tồn tại. Re-ingest cache vì vậy bỏ được Docling đắt tiền nhưng vẫn chunk lại trong bộ nhớ.

### Bước 13 — Trả summary

`IngestSummary` chứa:

```text
doc_id
section_count
chunk_count
window_count
structure_warnings
parse_stats
source_seen_before
parse_version
chunk_version
artifact_path
```

CLI dùng summary này để in kết quả, không đọc artifact lần nữa.

## 4. Luồng `inspect`

Ví dụ:

```powershell
.\.venv\Scripts\doc2roadmap.exe inspect --doc-id book
```

Luồng:

```text
CLI
 ↓
build_inspect()
 ↓
InspectDocument.execute(doc_id)
 ↓
JsonArtifactStore.load_latest_chunks(doc_id)
 ↓
đọc manifest + sections + chunks + document
 ↓
assemble_windows(chunks)
 ↓
CLI in cây section và từng window
```

`load_latest_chunks()` chọn version số lớn nhất, không chọn theo source hash do người dùng truyền; `inspect` chỉ nhận `doc_id`.

CLI dựng `by_parent[parent_section_id]`, in cây đệ quy từ root, đánh dấu section không có nội dung trực tiếp, rồi in từng window cùng `order_index`, `chunk_id` và text một dòng.

## 5. Ma trận cache và version

| Thay đổi | Parse lại? | Chunk lại/new version? | Lý do |
|---|---|---|---|
| Không đổi gì | Không | Tính lại trong RAM, store tái dùng artifact | Hai hash khớp |
| Nội dung file đổi | Có | Có | `source_hash` đổi |
| Docling version đổi | Có | Có | parser identifier đổi |
| Adapter code đổi và bump version | Có | Có | `parser_config_hash` đổi |
| `target_tokens`/`max_tokens` đổi | Không | Có | chỉ `config_hash` đổi |
| `sentence_overlap` đổi | Không | Có | chỉ `config_hash` đổi |
| Tokenizer model đổi | Không | Có | tokenizer identifier đổi |
| Chunk/normalization code đổi và bump algorithm ID | Không | Có | chunk config đổi |

Kỷ luật version bắt buộc:

- sửa cách tạo `DocumentNode` → tăng `ADAPTER_VERSION`;
- sửa normalization/chunk semantics → tăng `CHUNK_ALGORITHM_ID` hoặc đưa version tương ứng vào config.

Nếu quên bump, artifact cũ có thể được tái sử dụng im lặng.

## 6. Giải thích từng file production

### Package root và wiring

| File | Vai trò |
|---|---|
| [`src/doc2roadmap/__init__.py`](../src/doc2roadmap/__init__.py) | Khai báo package và `__version__ = "0.1.0"`. Không tham gia trực tiếp luồng ingest. |
| [`src/doc2roadmap/config.py`](../src/doc2roadmap/config.py) | Định nghĩa `Settings`, validate giá trị môi trường và đường dẫn asset/artifact. |
| [`src/doc2roadmap/composition.py`](../src/doc2roadmap/composition.py) | Composition root: ghép use case với Docling, JSON store, tokenizer và splitter. `build_inspect()` chỉ cần store. |

### Presentation

| File | Vai trò |
|---|---|
| [`src/doc2roadmap/presentation/__init__.py`](../src/doc2roadmap/presentation/__init__.py) | Đánh dấu package giao diện; không có logic runtime. |
| [`src/doc2roadmap/presentation/cli/__init__.py`](../src/doc2roadmap/presentation/cli/__init__.py) | Đánh dấu package CLI; không có logic runtime. |
| [`src/doc2roadmap/presentation/cli/main.py`](../src/doc2roadmap/presentation/cli/main.py) | Entry point `doc2roadmap`; parse lệnh, đọc file, gọi use case, in summary/tree/window, chuyển exception thành exit code 2. |

### Application

| File | Vai trò |
|---|---|
| [`src/doc2roadmap/application/__init__.py`](../src/doc2roadmap/application/__init__.py) | Marker cho layer application. |
| [`src/doc2roadmap/application/ports/__init__.py`](../src/doc2roadmap/application/ports/__init__.py) | Re-export các port/wrapper, gồm `ParsedDocument`. |
| [`src/doc2roadmap/application/ports/parsing.py`](../src/doc2roadmap/application/ports/parsing.py) | Port parser trả `ParsedDocument(tree, images)` và công bố identifier, adapter version, image scale. |
| [`src/doc2roadmap/application/ports/artifacts.py`](../src/doc2roadmap/application/ports/artifacts.py) | Port lưu trữ và hai wrapper `StoredParse`/`StoredChunks`; định nghĩa các thao tác tìm, lưu và nạp artifact. |
| [`src/doc2roadmap/application/use_cases/__init__.py`](../src/doc2roadmap/application/use_cases/__init__.py) | Re-export `IngestDocument`, `IngestSummary`, `InspectDocument`. |
| [`src/doc2roadmap/application/use_cases/ingest_document.py`](../src/doc2roadmap/application/use_cases/ingest_document.py) | Use case trung tâm: validate, băm, cache parse, gọi parser/chunker/window/store và trả summary. |
| [`src/doc2roadmap/application/use_cases/inspect_document.py`](../src/doc2roadmap/application/use_cases/inspect_document.py) | Validate `doc_id`, tải chunk version mới nhất và ráp lại windows. |
| [`src/doc2roadmap/application/windows.py`](../src/doc2roadmap/application/windows.py) | Hàm thuần group chunk theo section cha trực tiếp, giữ thứ tự toàn cục. |

### Domain

| File | Vai trò |
|---|---|
| [`src/doc2roadmap/domain/__init__.py`](../src/doc2roadmap/domain/__init__.py) | Marker cho domain thuần. |
| [`src/doc2roadmap/domain/models.py`](../src/doc2roadmap/domain/models.py) | Dataclass node/tree/section/chunk và ba loại ref; nạp được artifact thiếu `formula_refs`/field formula. |
| [`src/doc2roadmap/domain/ports.py`](../src/doc2roadmap/domain/ports.py) | `TextSpan` và protocol thuần cho token counter/sentence splitter; domain không biết SentencePiece hay regex implementation. |
| [`src/doc2roadmap/domain/normalization.py`](../src/doc2roadmap/domain/normalization.py) | Chuẩn hóa Unicode, whitespace, soft hyphen, từ ngắt dòng và punctuation mà không hạ chữ/bỏ dấu. |
| [`src/doc2roadmap/domain/chunking.py`](../src/doc2roadmap/domain/chunking.py) | Dựng section/chunk, lọc heading, gom warning, ba loại ref, ID, full text/span, merge và split. |

### Infrastructure

| File | Vai trò |
|---|---|
| [`src/doc2roadmap/infrastructure/__init__.py`](../src/doc2roadmap/infrastructure/__init__.py) | Marker cho layer adapter. |
| [`src/doc2roadmap/infrastructure/parsing/__init__.py`](../src/doc2roadmap/infrastructure/parsing/__init__.py) | Re-export `DoclingParser`. |
| [`src/doc2roadmap/infrastructure/parsing/docling_parser.py`](../src/doc2roadmap/infrastructure/parsing/docling_parser.py) | Adapter Docling: PNG, Symbol map, raw/formula ID, caption, provenance, PDF order/stitch và parse stats. |
| [`src/doc2roadmap/infrastructure/artifacts/__init__.py`](../src/doc2roadmap/infrastructure/artifacts/__init__.py) | Re-export `JsonArtifactStore`. |
| [`src/doc2roadmap/infrastructure/artifacts/json_store.py`](../src/doc2roadmap/infrastructure/artifacts/json_store.py) | Lưu/nạp JSON, ghi PNG cạnh parse tree, đánh version/cache và replace file qua temporary. |
| [`src/doc2roadmap/infrastructure/text/__init__.py`](../src/doc2roadmap/infrastructure/text/__init__.py) | Re-export tokenizer và sentence splitter. |
| [`src/doc2roadmap/infrastructure/text/tokenizer.py`](../src/doc2roadmap/infrastructure/text/tokenizer.py) | Adapter SentencePiece offline và identifier gắn digest model. |
| [`src/doc2roadmap/infrastructure/text/sentence_splitter.py`](../src/doc2roadmap/infrastructure/text/sentence_splitter.py) | Regex splitter trả exact spans, bảo vệ một tập viết tắt và decimal. |

## 7. Model dữ liệu chi tiết

### `DocumentNode`

| Field | Ý nghĩa |
|---|---|
| `node_type` | `title`, `section_header`, `text`, `list_item`, `table`, `figure`, `footnote`, ... |
| `text` | Nội dung sau clean adapter, chưa qua domain normalization |
| `reading_order` | Thứ tự đọc toàn cục sau adapter repair |
| `level` | Heading level raw từ parser |
| `page` | Trang nguồn; thường có với PDF, thường `None` với DOCX |
| `bbox` | `(left, top, right, bottom)` của provenance đầu tiên |
| `table_rows` | Ma trận row/cell Docling; ở nguyên trong parse tree |
| `table_id` | SHA-256 của ma trận ô đã chuẩn hoá; `None` với node không phải bảng |
| `context_prefix` | Caption/ngữ cảnh phụ của non-figure item |
| `image_id` | SHA-256 byte PNG với figure đã trích; `None` nếu node không có ảnh |
| `tree_depth` | Depth trong cây Docling |
| `raw_text` | Nội dung `orig` đã clean; formula luôn giữ nguồn dùng để băm ở đây |
| `formula_id` | SHA-256 raw formula đã chuẩn hoá; `None` với node khác |

### `Section`

| Field | Ý nghĩa |
|---|---|
| `section_id` | ID tất định |
| `title`, `level` | Tiêu đề chuẩn hóa và level suy ra |
| `heading_level_raw` | Level parser gốc để audit |
| `parent_section_id` | Cạnh cha trực tiếp |
| `section_path` | Đường từ heading gốc xuống section |
| `order_index` | Vị trí heading trong trục kết quả |
| `has_direct_content` | Có leaf block trực tiếp hay không |

### `Chunk`

| Field | Ý nghĩa |
|---|---|
| `chunk_id` | ID tất định theo owner/text/split/occurrence |
| `order_index` | Vị trí trong trục heading + chunk |
| `split_index` | Thứ tự mảnh khi block dài bị sentence split hoặc hard-cap split |
| `page` | Trang bắt đầu của node đầu tiên |
| `char_start`, `char_end` | Span trong `normalized_full_text` |
| `parent_section_id`, `section_path`, `heading_level` | Provenance cấu trúc |
| `block_types` | Danh sách khử trùng lặp theo thứ tự xuất hiện của mọi loại block trong chunk |
| `text`, `context_prefix` | Nội dung embed/trích dẫn và ngữ cảnh caption |
| `image_refs` | Danh sách `{image_id, char_start}`; luôn có trường, rỗng nếu chunk không có hình |
| `table_refs` | Danh sách `{table_id, char_start}`; luôn có trường, rỗng nếu chunk không có bảng |
| `formula_refs` | Danh sách `{formula_id, char_start}`; luôn có trường, rỗng nếu chunk không có công thức |
| `token_count`, `tokenizer_id` | Số token và tokenizer đã dùng |
| `oversize_reason` | `None` trong trần áp dụng; nếu vượt thì nêu row bảng, splitter hoặc `hard_cap_forced_split` |

## 8. File test, fixture và script

### Test support và unit test

| File | Điều được bảo vệ |
|---|---|
| [`tests/conftest.py`](../tests/conftest.py) | `WordCounter` nhẹ cho domain test, reference tree và loader fixture Docling thật có cache. |
| [`tests/unit/test_architecture.py`](../tests/unit/test_architecture.py) | Chiều phụ thuộc domain/application. |
| [`tests/unit/application/test_ingest.py`](../tests/unit/application/test_ingest.py) | Cache/version, schema cũ, lưu/nạp image/table/formula refs và warning manifest. |
| [`tests/unit/domain/test_normalization.py`](../tests/unit/domain/test_normalization.py) | NFC, whitespace, soft hyphen, dehyphenation và punctuation. |
| [`tests/unit/domain/test_sentence_splitter.py`](../tests/unit/domain/test_sentence_splitter.py) | Mười ca đa chữ viết, abbreviation data, decimal và exact offset. |
| [`tests/unit/domain/test_chunking.py`](../tests/unit/domain/test_chunking.py) | Cây/window/ID/span, ba loại ref ngoài ID, formula merge, heading filter, warning và table split. |
| [`tests/unit/domain/test_docx_cleanup_chunking.py`](../tests/unit/domain/test_docx_cleanup_chunking.py) | Chuỗi ưu tiên heading, lọc dot/TOC, gom warning toàn chuỗi và I25. |
| [`tests/unit/infrastructure/test_docling_adapter.py`](../tests/unit/infrastructure/test_docling_adapter.py) | Ảnh/order/stitch cùng table ID độc lập markdown/vị trí. |
| [`tests/unit/infrastructure/test_docx_cleanup_adapter.py`](../tests/unit/infrastructure/test_docx_cleanup_adapter.py) | Ảnh/DrawingML DOCX, nối run và gỡ bullet PUA trên fixture mới. |
| [`tests/unit/infrastructure/test_symbol_formula_adapter.py`](../tests/unit/infrastructure/test_symbol_formula_adapter.py) | Fixture xstk, Symbol PDF/DOCX, raw fallback, formula và I22–I24. |
| [`tests/unit/test_four_document_regression.py`](../tests/unit/test_four_document_regression.py) | Số-vàng toàn pipeline và digest chunk ID của bốn tài liệu thật. |
| [`tests/unit/infrastructure/test_docling_parser_cache.py`](../tests/unit/infrastructure/test_docling_parser_cache.py) | Converter lazy và reuse trong cùng parser instance. |
| [`tests/unit/presentation/test_cli.py`](../tests/unit/presentation/test_cli.py) | Output tree/window/warning/parse stats của CLI. |

### Integration test

| File | Điều được bảo vệ |
|---|---|
| [`tests/integration/test_docling_parser.py`](../tests/integration/test_docling_parser.py) | Docling parse PDF, DOCX, table và reading order fixture hai cột thật. |
| [`tests/integration/test_ingest_real.py`](../tests/integration/test_ingest_real.py) | Ingest thật, reuse parse và ID của text không đổi khi source được chèn block mới. |
| [`tests/integration/test_tokenizer.py`](../tests/integration/test_tokenizer.py) | Tokenizer vendored nạp offline và identifier đúng. |

### Fixture

| File/thư mục | Vai trò |
|---|---|
| [`tests/fixtures/smoke.pdf`](../tests/fixtures/smoke.pdf) | PDF một cột tối thiểu. |
| [`tests/fixtures/smoke-updated.pdf`](../tests/fixtures/smoke-updated.pdf) | PDF có block chèn thêm để test ID ổn định. |
| [`tests/fixtures/two-column.pdf`](../tests/fixtures/two-column.pdf) | Bảo vệ output reading order hai cột end-to-end; Docling hiện xuất fixture thành một node nên nhánh guard `False` được bảo vệ bằng unit test trực tiếp. |
| [`tests/fixtures/smoke.docx`](../tests/fixtures/smoke.docx) | DOCX có heading, paragraph và table thật. |
| [`tests/fixtures/docling/nhap-mon-ml.json`](../tests/fixtures/docling/nhap-mon-ml.json) | Snapshot 170 item có 9 PNG nhúng ở scale 2.0, chạy adapter test không parse OCR lại. |
| [`tests/fixtures/docling/xstk-ch3-1.json`](../tests/fixtures/docling/xstk-ch3-1.json) | Snapshot 992 item có 264 formula, 51 bảng và glyph Symbol để test nhanh. |
| [`tests/fixtures/docling/baocao-canhan.json`](../tests/fixtures/docling/baocao-canhan.json) | Snapshot DOCX 396 item, 3 ảnh raster và level Word 1/2. |
| [`tests/fixtures/docling/naive-bayes.json`](../tests/fixtures/docling/naive-bayes.json) | Snapshot slide 224 item, 2 ảnh, 13 bảng, 32 công thức và bullet PUA. |
| [`tests/fixtures/docling/README.md`](../tests/fixtures/docling/README.md) | Nguồn, hash, cách sinh và điều kiện refresh snapshot. |

### Script

| File | Vai trò |
|---|---|
| [`scripts/create_smoke_pdf.py`](../scripts/create_smoke_pdf.py) | Sinh PDF/DOCX fixture bằng standard library; có PDF một cột, bản updated, hai cột và DOCX table. |
| [`scripts/smoke_docling.py`](../scripts/smoke_docling.py) | Smoke check tối thiểu rằng Docling parse được PDF và trả node. |

## 9. File cấu hình, tài liệu và asset

| File | Vai trò |
|---|---|
| [`pyproject.toml`](../pyproject.toml) | Metadata package, Python 3.12, dependency, CLI entry point và pytest config. |
| [`uv.lock`](../uv.lock) | Khóa dependency tree để tái lập môi trường. |
| [`.python-version`](../.python-version) | Ghim Python dùng bởi toolchain. |
| [`.env.example`](../.env.example) | Ví dụ override token/window/artifact settings. |
| [`.gitignore`](../.gitignore) | Bỏ môi trường, cache, bytecode, `.env` và output artifact. Có một lỗi pattern quan trọng ở mục 12. |
| [`README.md`](../README.md) | Hướng dẫn cài, test, ingest và inspect ngắn. |
| [`CONTEXT.md`](../CONTEXT.md) | Từ điển thuật ngữ thống nhất cho toàn dự án. |
| [`doc/B0-ingestion-spec.md`](../doc/B0-ingestion-spec.md) | Spec kiến trúc B0 và bất biến ban đầu. |
| [`doc/B0-chunking-spec.md`](../doc/B0-chunking-spec.md) | Spec đã chốt về normalization, ID và chunk. |
| [`doc/B0-va-cau-truc-spec.md`](../doc/B0-va-cau-truc-spec.md) | Spec vá theo dữ liệu thật: heading, warning, cleaning, target merge và table. |
| [`doc/B0-anh-va-tham-chieu-spec.md`](../doc/B0-anh-va-tham-chieu-spec.md) | Spec trích/lưu ảnh, caption mồ côi, block types và image refs. |
| [`doc/B0-symbol-va-cong-thuc-spec.md`](../doc/B0-symbol-va-cong-thuc-spec.md) | Spec Symbol map, raw/formula ref, warning grouping và heading filter. |
| [`doc/adr/0001-dinh-danh-tat-dinh.md`](../doc/adr/0001-dinh-danh-tat-dinh.md) | Quyết định công thức ID và trade-off ổn định. |
| [`doc/adr/0002-anh-va-tham-chieu-ngoai-dinh-danh-chunk.md`](../doc/adr/0002-anh-va-tham-chieu-ngoai-dinh-danh-chunk.md) | Khuôn marker + content/ref ngoài chunk ID cho hình, bảng và công thức. |
| [`feedback/`](../feedback/) | Kết quả review code/artifact, nguồn của các ticket sửa. Không tham gia runtime. |
| [`task/`](../task/) | Hồ sơ triển khai và trạng thái ticket. Không tham gia runtime. |
| `vendor/gemma/tokenizer.model` | Asset SentencePiece offline; digest của file tham gia tokenizer identifier. |

## 10. Đối chiếu trên tài liệu thật hiện tại

### 10.1 `nhap-mon-ml` — tập ID phải giữ nguyên

Nguồn đã dùng:

```text
C:\Users\ngoco\Downloads\nhap_mon_hoc_may_va_khai_pha_du_lieu_5944.pdf
SHA-256: d5a78c95b7603bffff77d6675c0286beaeb997f5633ac9e598bccb25305d3f71
```

Artifact hiện tại:

```text
artifacts/parse_tree/nhap-mon-ml/v2
artifacts/chunks/nhap-mon-ml/v2
```

Kết quả:

| Chỉ số | Giá trị |
|---|---:|
| Docling item | 170 |
| Node output | 156 |
| Item bị lọc | 9 |
| Ảnh PNG | 9 file / 821.359 byte |
| Image ref trong chunk | 9 |
| Table node / table ref | 0 / 0 |
| Formula node / formula ref | 1 / 1 |
| Caption lấy lại / mồ côi | 8 / 1 |
| Fragment được stitch | 5 |
| Trang được reorder | 1 |
| Section gồm root | 27 |
| Chunk | 41 |
| Window | 22 |
| Chunk có `list_item` | 14 |
| Token median | 261 |
| Token max | 400 |
| Chunk có `oversize_reason` | 0 |
| Warning splitter bó tay | 0 |
| Chunk chỉ chứa marker `[figure]` | 0 |
| Vi phạm char span | 0/41 |

Đối chiếu sạch ngày 2026-08-22 dùng adapter version 7, algorithm `section-id-v7` và ảnh scale 2.0. So với v1,
39/41 chunk ID giữ nguyên; đúng hai ID đổi: chunk nhận thêm một `[formula]`/`formula_ref`, và chunk đổi marker
không caption sang `[figure]`. Hash tập ID mới là
`14d7bcbf3eda0e070342408834b3d9218002cb3086cd151c8aa511768e961ccc`; baseline v1 là
`726dce8b6c9c1bc2452f9ff409cc9d83f9446421ac1e666fdc4557c6b3d3d7a5`. Cây vẫn sâu bốn level, đủ năm
stitch, 9 image ref resolve, không PUA, không chunk vượt trần và 0/41 span lỗi.

### 10.2 `xstk-ch3-1.pdf` — corpus bảng thật

PDF 59 trang, SHA-256 `c265d409800af5515ba6e71408a9998020b38670369dfec4a5c01246e07fd20c`, được ingest sạch
thành 43 section, 126 chunk và 40 window. Kết quả kiểm độc lập trên artifact v2:

| Chỉ số | Giá trị |
|---|---:|
| Docling item / node giữ | 992 / 987 |
| Table node / table ID phân biệt | 51 / 48 |
| Table ref / ID ref phân biệt | 51 / 48 |
| Formula node / formula ID phân biệt | 263 / 225 |
| Formula ref / ID ref phân biệt | 263 / 225 |
| Ref thiếu / ref treo | 0 / 0 |
| Chunk văn xuôi: số lượng / median / max | 87 / 261 / 401 |
| Chunk có bảng: số lượng / median / max | 39 / 273 / 628 |
| Chunk có formula ref | 84 |
| Chunk bảng vượt 512 nhưng không vượt 2048 | 1 |
| Chunk bảng có cả ngữ cảnh loại khác | 39/39 |
| Chunk vượt trần áp dụng / trần cứng | 0 / 0 |
| Vi phạm char span / formula ref | 0/126 · 0/263 |
| Ảnh / image ref | 5 / 5 |
| Symbol mapping / PUA trong chunk | 2.368 surface / 2 glyph extender có warning |
| Warning sau gom | 29 dòng |

Adapter giữ 263/264 formula bằng marker trung tính và raw ở parse tree; ca còn lại có cả `text`/`orig` rỗng nên
vẫn bị loại có warning. Có đúng 263 marker và 263 ref trỏ vào marker. 23 bullet heading cùng `Chú ý .` và
`Trong đó:` bị hạ về text, nên section giảm đúng 25; 51 table/ref vẫn nguyên.

Mapping sửa toàn bộ glyph Symbol có Unicode đọc được. Hai `U+F0E7` là extender corporate-use không có đích
Unicode tương đương, nên được giữ với warning `remaining_private_use: 78`; số 78 tính cả text/raw/table surface
lưu trong parse tree, còn text chunk có hai. Đây là trạng thái I22 hợp lệ, không phải lỗi im lặng. Hash tập 126
chunk ID ở đối chiếu v7 là `4ee6218d79b1d67e9d42a79fa958eed8842ee8e9a2c477157253123f03316040`;
số-vàng hiện tại với adapter 8/`section-id-v8` là
`f12e2c21bfbd1ccf303266e22a961233ca649e767793a880b87b741e16d4b9f9`.

Fixture thật `tests/fixtures/smoke.docx` vẫn ingest với đúng một `table_ref`, trỏ tới markdown bắt đầu bằng
`| Name | Value |`; bài integration tương ứng xanh.

Đối chiếu test tại thời điểm viết báo cáo:

```text
115 passed, 5 warnings
```

Năm warning là deprecation warning từ dependency Docling/RapidOCR/SWIG; không có test failure.

## 11. Bất biến quan trọng đang có test

| Bất biến | Ý nghĩa |
|---|---|
| Window partition | Mỗi chunk thuộc đúng một window trực tiếp, không đẩy chunk con lên cha |
| ID tất định | Cùng input/config cho cùng section/chunk ID |
| ID ổn định tương đối | Chèn block trước không làm đổi ID text không đổi phía sau |
| Reading order | Chunk order tăng theo trục kết quả |
| Unicode | Chunk text ở NFC |
| Char span | Slice full text bằng span đúng bằng chunk text |
| Image content ID | Tên mỗi PNG bằng SHA-256 nội dung file; cùng fixture cho cùng tập ID |
| Image ref resolution | Mọi ref trỏ tới PNG tồn tại và `char_start` nằm trong span chunk chứa nó |
| Image ref ngoài chunk ID | Đổi image ID nhưng giữ text/section không đổi `chunk_id` |
| Table content ID | Cùng ma trận ô sau chuẩn hoá cho cùng ID dù markdown/vị trí đổi; đổi ô làm ID đổi |
| Table ref resolution | Ref trỏ đúng dòng đầu markdown; mọi fragment row-split giữ cùng `table_id` |
| Table ref ngoài chunk ID | Đổi table ID nhưng giữ text/section không đổi `chunk_id` |
| Formula ref resolution | Mỗi ref trỏ đúng marker `[formula]` và `formula_id` tồn tại trong parse tree |
| Formula ref ngoài chunk ID (I24) | Đổi formula ID nhưng giữ text/section không đổi `chunk_id` |
| Raw fallback (I23) | `text` rỗng nhưng `orig` có chữ vẫn tạo node; chỉ cả hai rỗng mới bị loại |
| Symbol guard (I22) | PUA trong chunk chỉ được tồn tại khi result có warning `remaining_private_use` |
| Warning grouping | 300 warning trùng toàn chuỗi thành một dòng có count; raw khác nhau giữ từng ca và thứ tự |
| Block types | Chunk khai đủ loại block, khử trùng lặp theo thứ tự xuất hiện |
| Heading hierarchy | Đánh số thắng raw; cây khai 1/2 được tin; cây phẳng rơi về suy diễn |
| False heading | Nội dung bị nhận nhầm heading được hạ thành text, không mất |
| Merge boundary | Không merge qua section hoặc footnote ở domain chunker |
| Oversize reason (I25) | Bảng trên 512, row dài, splitter bó tay và hard cap đều gọi tên đường vượt; trong 512 để rỗng |
| Splitter failure warning | Block vượt trần chỉ có một span tạo warning manifest/CLI kèm trang hoặc section |
| Table semantics | Cắt theo row, lặp header |
| Global sentence boundary | Mười ca Việt/Anh/Trung/Nhật/Hindi/Ả Rập cùng punctuation Khmer/Arabic mở rộng |
| Lowercase continuation | Ba ca `… rồi`, `U.S.A. là`, `"tuyệt!" rồi` không bị cắt nhầm |
| Table soft cap | Bảng 11×6 giữ nguyên và khai lý do trên 512; lead + bảng cùng chunk; văn xuôi vẫn bị chặn ở 512 |
| Hard cap I20 | Prose không boundary và hàng bảng dị thường đều bị cắt dưới trần; span/Unicode/table ID giữ đúng |
| Adapter isolation | PDF repair không chạy với DOCX; nối run không-bbox không chạy trên node PDF có bbox |
| Multi-column guard | Hai text block ngang tách rời trả `False` và giữ order; side figure không tạo cột; thiếu bbox trả `False` |
| Same-row tolerance | Block cùng hàng được sort theo `left` dù độ lệch `top` đi ngược thứ tự trái-phải |
| Orphan caption | Caption không có ref được giữ đúng reading order và cảnh báo đúng một lần |
| Image parity | PDF/DOCX cùng trích byte và ref; marker thiếu byte hoặc DrawingML luôn có `missing_image` |
| DOCX cleanup | Run ba mảnh nối theo chuỗi; bullet mới không dính; dot/TOC bị lọc nhưng section còn nguyên |
| Corpus bốn tài liệu | Số section/chunk/ref/PUA/chữ cái, I9, ID trùng và digest chunk ID được ghim tự động |

## 12. Phát hiện và giới hạn cần lead biết

### Kết quả xử lý feedback F10

| Feedback | Trạng thái | Cách xử lý |
|---|---|---|
| F22 — regex glyph có thể xóa ký hiệu sau từ tiếng Việt | Đã sửa | Lookbehind dùng Unicode letter guard; các ca `các c c c`, `học c c c`, `lần n n n` giữ lại đúng một ký hiệu độc lập. |
| F23 — guard đa cột chưa được thực thi bởi fixture | Đã sửa | Thêm unit test gọi trực tiếp: hai text block ngang tách rời trả `False` và giữ order; side figure không tạo cột; thiếu bbox trả `False`. |
| F24 — sort cùng hàng thiếu dung sai dọc | Đã sửa | Gom hàng khi vertical overlap lớn hơn nửa chiều cao block ngắn hơn, rồi sort `left`; có ca độ lệch `top` ngược thứ tự trái-phải. |
| F25 — chunk stitch chỉ ghi trang đầu | Ghi nhận, hoãn | `page_end` sẽ đổi model/schema/artifact và chưa có consumer citation theo trang trong B0. |
| F26 — nhận diện cột O(n²) | Ghi nhận, giữ nguyên | Trang thật hiện tối đa 12 node; chưa có bằng chứng đây là bottleneck. Code có `ponytail` comment nêu điều kiện đổi sang sweep. |

F22–F24 từng làm `ADAPTER_VERSION` tăng `3 → 4` trong đợt reading-order. Đợt B0 ảnh tăng adapter `4 → 5` và
chunk algorithm `section-id-v3 → section-id-v4`; đợt bảng/tách câu tăng đúng một lần thành adapter 6 và
`section-id-v5`; đợt ba trần chỉ tăng chunk algorithm thành `section-id-v6`, adapter vẫn là 6; đợt
Symbol/formula tăng cả hai thành adapter 7 và `section-id-v7`. Phần kết luận F10 về artifact v3 vẫn là số liệu
lịch sử. Đợt DOCX/dọn dẹp tăng đúng một lần thành adapter 8 và `section-id-v8`; các thay đổi ảnh, nối run,
bullet PUA cùng dùng bump adapter này, còn cấp heading, lọc block, gom warning và I25 cùng dùng bump chunker.

### 12.1 F27 đã xử lý — `.gitignore` không còn che source code artifact store

Pattern output root hiện tại:

```gitignore
/artifacts/
```

chỉ ignore output root `artifacts/`. Sau khi sửa F27, Git xác nhận source không còn bị ignore:

```text
git check-ignore src/doc2roadmap/infrastructure/artifacts/json_store.py  # exit 1
git check-ignore artifacts/chunks/example/v1/chunks.json               # exit 0
```

Các pattern cache khác không được đổi vì không có bằng chứng chúng đang che source; thay đổi một ký tự này là
đủ đóng đúng lỗi được review.

### 12.2 Artifact nhiều file chưa atomic ở cấp thư mục

Từng JSON file được ghi an toàn qua `.tmp` + `os.replace`, nhưng một version gồm hai hoặc bốn file. Nếu process chết giữa chừng, thư mục `vN` có thể tồn tại thiếu file; `_versions()` vẫn nhìn thấy version đó và lần load sau có thể lỗi.

### 12.3 Chưa có khóa cho ingest đồng thời

Hai process cùng ingest một `doc_id` có thể cùng chọn version kế tiếp và ghi cùng thư mục. Hiện không có file lock hoặc transaction directory.

### 12.4 `inspect` luôn lấy version số lớn nhất

CLI inspect không nhận source/config/version. Nếu một `doc_id` có nhiều source/config, người dùng chỉ thấy version chunks mới nhất.

### 12.5 Cache chunk được kiểm tra muộn

Parse cache được kiểm tra trước công việc đắt tiền. Chunk cache chỉ được nhận ra trong `save_chunks()`, sau khi chunk/window đã được tính lại. Hiện chi phí nhỏ so với Docling, nhưng là phần có thể tối ưu nếu corpus lớn.

### 12.6 PDF layout repair có chủ đích bảo thủ

- Trang đa cột tin Docling.
- Nhận diện một cột dựa trên overlap ngang của bbox, không phải layout model đầy đủ.
- Gom hàng dùng block đầu hàng làm mốc và ngưỡng vertical overlap lớn hơn một nửa chiều cao block ngắn hơn; chưa phải layout clustering tổng quát.
- Kiểm tra mọi cặp content block là O(n²); chỉ nên đổi sang sweep nếu profiling trên trang dày cho thấy chi phí đáng kể.
- Stitch chỉ bắt continuation bắt đầu chữ thường.
- Figure/footnote được bảo toàn nhưng chưa suy figure anchor.
- Merged cross-page node chỉ giữ provenance của fragment đầu.

### 12.7 DOCX không có provenance trang trong luồng hiện tại

Chunk DOCX thường có `page=None`. Nếu consumer sau cần citation theo trang Word, phải có bước render/pagination riêng; OOXML order không tự cung cấp trang hiển thị ổn định.

### 12.8 Sentence splitter là heuristic hữu hạn

Splitter đã nhận các dấu kết câu chính và bộ viết tắt common Latin/tiếng Việt, nhưng vẫn là luật tất định hữu
hạn chứ không hiểu ngữ nghĩa. F28 đã bổ sung guard không cắt nếu ký tự có nghĩa tiếp theo là chữ thường. Ca
chữ cái đầu viết hoa đơn như `J. Smith` hoặc `T. P. E.` vẫn cố ý để ngỏ: một heuristic chung sẽ cắt sai câu
kết thúc thật như `Xem chương T.`. Một câu đơn lẻ quá dài trước hết mang lý do splitter, rồi bị trần cứng cắt
nếu cần.

### 12.9 Table row quá trần bảng có đường thoát ở trần cứng

Một row không thể cắt nhỏ theo semantics bảng hiện tại. Nó được giữ nguyên qua bước cắt hàng nhưng sẽ bị cắt
cưỡng bức nếu vượt 6000 token, nên I20 vẫn không có ngoại lệ. Việc cắt cưỡng bức chỉ chia đơn vị truy hồi;
ma trận hàng/cột và `table_id` trong parse tree không đổi.

### 12.10 Symbol mapping và raw công thức là dữ liệu suy đoán

Docling không trả font, nên việc đọc `U+F000–U+F0FF` như Adobe Symbol là heuristic có số đo và warning. Các
glyph corporate-use không có Unicode tương đương không bị thay bừa. Raw formula cũng chỉ là dữ liệu audit/tái
xử lý: reading order toán tử có thể sai, nên B0 không gọi nó là LaTeX và không đưa nó vào embedding.

### 12.11 Hai bài học khi đọc output thư viện

- Khi field chuẩn hoá trông rỗng hoặc lạ, kiểm các field raw/provenance trước khi kết luận nội dung không tồn tại.
- Một tài liệu chỉ cho biết một con số, và con số quyết định mức độ: lỗi formula từng có một ca ở tài liệu một,
  nhưng có 264 ca ở tài liệu hai. Fixture đa dạng là guard chất lượng, không chỉ là thêm coverage.

### 12.12 B0 chưa tạo roadmap

Tên project là `doc2roadmap`, nhưng code production hiện dừng ở artifact chunk/window. Các bước concept extraction, graph và stage mới chỉ nằm trong spec/context, chưa có module runtime.

## 13. Runbook kiểm tra nhanh

### Chạy toàn bộ test

```powershell
.\.venv\Scripts\python.exe -m pytest
```

### Ingest

```powershell
.\.venv\Scripts\doc2roadmap.exe ingest path\to\book.pdf --doc-id book
```

### Inspect

```powershell
.\.venv\Scripts\doc2roadmap.exe inspect --doc-id book
```

### Kiểm tra artifact

```text
artifacts/parse_tree/book/vN/manifest.json
artifacts/parse_tree/book/vN/tree.json
artifacts/chunks/book/vN/manifest.json
artifacts/chunks/book/vN/sections.json
artifacts/chunks/book/vN/chunks.json
artifacts/chunks/book/vN/document.json
```

### Khi sửa code

| Sửa gì | Cần nhớ |
|---|---|
| Mapping/cleaning/reading order của Docling adapter | Bump `ADAPTER_VERSION` |
| Normalization, heading, chunk, ID, table/sentence semantics | Bump `CHUNK_ALGORITHM_ID` hoặc config version tương ứng |
| Docling dependency hoặc image scale | Regenerate cả `nhap-mon-ml.json` và `xstk-ch3-1.json` |
| Artifact schema | Thêm migration/backward compatibility và test load artifact cũ |
| Multi-column repair | Giữ integration test trái-hết-rồi-phải và thêm fixture layout thật |

## 14. Tóm tắt trách nhiệm theo một tài liệu đi qua hệ thống

```text
main.py
  nhận lệnh, đọc bytes

config.py + composition.py
  lấy cấu hình, tạo parser/store/tokenizer/splitter/use case

ingest_document.py
  validate, băm, quyết định reuse parse, điều phối toàn luồng

docling_parser.py
  bytes → DoclingDocument → ParsedDocument(tree sạch + ảnh mọi định dạng + nối run + PUA stats)

json_store.py
  đóng băng/nạp parse tree và ghi images/<sha256>.png theo parser hash

normalization.py
  chuẩn hóa text từng block

chunking.py
  DocumentTree → lọc dot/TOC → Section theo explicit/declared/fallback
               → Chunk(block_types, image/table/formula refs, I25) + normalized_full_text

tokenizer.py + sentence_splitter.py
  đo ngân sách và cung cấp ranh giới cắt block dài

windows.py
  Chunk → các window theo section cha trực tiếp

json_store.py
  lưu sections/chunks/document/manifest theo source + full config hash

main.py
  in summary; hoặc inspect_document.py nạp version mới nhất để xem lại
```
