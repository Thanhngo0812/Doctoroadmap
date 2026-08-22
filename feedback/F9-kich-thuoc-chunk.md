# F19–F20 🟠 — Chunk nhỏ hơn ngân sách 8 lần, và ba tham số cắt đều vô hiệu

Vòng review 2 · 2026-08-15 · Trả lời trực tiếp câu *"1 chunk có mấy chục token à?"*

**Đúng.** Trung vị **62,5 token**, trung bình 69,7 — trong khi `max_tokens = 512`.

---

## F19 🟠 — `max_tokens` là trần không bao giờ chạm; không có sàn, không có đích

### Số thật

```
132 chunk · 9195 token
trung vị 62,5 · trung bình 69,7 · min 3 · max 242

chunk chạm trần 512 :  0        ← luật cắt câu CHƯA BAO GIỜ chạy
split_index distinct: [0]       ← không block nào bị cắt
dùng ngân sách      : 14%
so với gemini-embedding-2 (8192 token): 0,9% sức chứa
```

### Vì sao

Kích thước chunk **không do ta chọn**. Luật là *"1 leaf block = 1 chunk"* (D2), nên kích thước chunk =
kích thước đoạn văn mà **tác giả giáo trình** viết ra. `max_tokens` chỉ can thiệp khi một khối vượt 512 — và
khối dài nhất tài liệu này là 242.

Độ dài khối gốc theo loại:

| Loại | n | Trung vị | Trung bình | Max |
|---|---:|---:|---:|---:|
| `text` | 85 | 79 | 81 | 242 |
| `list_item` | 35 | 42 | 52 | 156 |
| `figure` | 9 | 36 | 45 | 78 |
| `footnote` | 3 | 18 | 40 | 83 |

Một đoạn văn giáo trình tiếng Việt ≈ 80 token. Một gạch đầu dòng ≈ 42. Đó là toàn bộ câu chuyện.

### Ba tham số cắt hiện đều không có tác dụng

| Tham số | Giá trị | Thực tế |
|---|---|---|
| `max_tokens` | 512 | **Không bao giờ chạm** (max 242) |
| `min_tokens` | 32 | `del min_tokens` — không có hành vi (F18) |
| `sentence_overlap` | 1 | Chỉ dùng bên trong `_sentence_groups`, mà hàm đó không chạy |

Nhưng **cả ba đều nằm trong `config_hash`**. Nghĩa là: đổi `max_tokens` từ 512 xuống 384 sẽ sinh `config_hash`
mới → artifact bị coi là hết hạn → chunk lại toàn bộ → và cho ra **kết quả giống hệt từng byte**. Manifest đang
hứa một điều nó không làm được: rằng các tham số này ảnh hưởng tới đầu ra.

Đây cũng là lý do test I12 (*"đổi `max_tokens` 512→384, chỉ id của block bị cắt lại được đổi"*) **luôn xanh
một cách tầm thường** trên tài liệu thật: không block nào bị cắt ở cả hai giá trị.

### Đây chính là §13.1 mà spec bảo phải đo

`B0-ingestion-spec.md:400` viết:

> **Granularity chunk** — cùng tập chunk này làm cột ma trận node×chunk ở bước M. Quá to ⇒ nhiễu mention map;
> quá nhỏ ⇒ ma trận phình. **Cần đo trên corpus thật trước khi khoá `max_tokens`.**

Kế hoạch xếp §13.1 vào "ngoài phạm vi, hoãn". Bạn vừa ingest tài liệu thật — **giờ nó trong phạm vi.**

Và `spec-preview.md:77` nói con số khác hẳn:

> Chunk theo ranh giới section, **300–800 token**, overlap 10–15%.

Thực tế: **70 token, không overlap.** Nhỏ hơn cận dưới của spec-preview **4,3 lần**.

D2 đã chốt *"`B0-ingestion-spec` thắng"*, nên về mặt quy trình không ai làm sai. Nhưng D2 chốt lúc chưa có số
thật. Số thật đã có.

### Mô phỏng: nếu gộp khối liền kề trong cùng section

Không gộp qua ranh giới section, trần vẫn 512:

| Đích | #chunk | Trung vị | Trung bình | Max | <32 tok |
|---|---:|---:|---:|---:|---:|
| **hiện tại** | **132** | **62** | **70** | 242 | **27** |
| 128 | 61 | 154 | 151 | 366 | 4 |
| 200 | 46 | 223 | 200 | 366 | 4 |
| **256** | **39** | **270** | **236** | 398 | **4** |
| 384 | 34 | 298 | 270 | 503 | 4 |
| 512 | 31 | 316 | 297 | 511 | 3 |

Gộp cả section thành một chunk thì **7/23 section vượt 512** (`MỞĐẦU` 939, `1.1.2` 934, `1.1.3` 914) — nên
"một section = một chunk" không dùng được, phải có luật gộp thật sự.

### Khuyến nghị: đích 256, trần 512

Bốn consumer phía sau, xét từng cái với chunk 70 token so với 250 token:

| Consumer | 70 token | 250 token |
|---|---|---|
| **T1** trích khái niệm (đọc **window**, không đọc chunk lẻ) | không ảnh hưởng | không ảnh hưởng |
| **Bước M** ma trận node×chunk | ❌ cosine giữa mô tả node (~50 tok) và chunk 3–20 tok là **nhiễu** — vector văn bản ngắn rất kém ổn định | ✅ tín hiệu sạch |
| **T2b** hiện `evidence_chunk_ids` cho người học | ❌ mảnh cụt, 11% chunk mở đầu bằng *"Trong đó"*, *"Do đó"* — đọc một mình không hiểu | ✅ một đoạn đọc được |
| **Nhánh RAG** truy hồi | ❌ quá ngắn, khớp bừa vì mang ít thông tin | ✅ đúng dải 200–500 token thông dụng |

**Không consumer nào thực sự muốn chunk 70 token.** Nỗi lo *"quá nhỏ ⇒ ma trận phình"* trong spec hoá ra là nỗi
lo sai chỗ: 132 chunk × 250 node = 33k ô, mili-giây, phình không phải vấn đề. Vấn đề thật là **chất lượng
vector của văn bản ngắn**.

Vì sao 256 chứ không 512: ở đích 512 thì max chạm 511, tức là bắt đầu có chunk nuốt gần trọn một section — mất
khả năng định vị bằng chứng. 256 giữ được 39 đơn vị trên 20 trang (≈ 2 đơn vị/trang), đủ mịn để trích dẫn.

### Về overlap

`spec-preview` đề xuất overlap 10–15%. **Tôi không khuyến nghị.** Lý do: ranh giới ở đây là ranh giới **đoạn
văn**, vốn đã là ranh giới ngữ nghĩa — khác hẳn cửa sổ trượt cố định nơi overlap tồn tại để cứu câu bị cắt
giữa. Overlap sẽ nhân đôi text qua các chunk, làm hỏng tính không chồng lấn của `char_span`, và tạo cột gần
trùng nhau trong ma trận bước M.

Cần ngữ cảnh rộng hơn thì đã có sẵn cơ chế đúng: **window theo `parent_section_id`**, nới ra lúc truy vấn.
Giữ `sentence_overlap` cho đúng việc của nó — cắt một khối quá dài — và để mặc định 1.

### Nhắc lại cảnh báo định danh

Đổi luật gộp làm đổi **mọi `chunk_id`**. Phải nằm cùng đợt với F11 + F14 + F15 + F18, bump `algorithm_id`
`section-id-v2` → `v3` **một lần duy nhất**.

---

## F20 🟠 — Bảng bỏ qua `max_tokens` hoàn toàn

```python
# domain/chunking.py:162-166
spans = (
    [TextSpan(0, len(text))]        # ← bảng: luôn MỘT span, bất kể dài bao nhiêu
    if node.node_type == "table"
    else _sentence_groups(text, max_tokens, sentence_overlap, counter, splitter)
)
```

Bảng **không bao giờ được cắt**. Một bảng 60 dòng trong giáo trình sẽ thành một chunk vài nghìn token, vượt
`max_tokens` mà không có gì báo.

Tài liệu này **không có bảng nào** nên lỗi chưa lộ. Fixture (f) *"bảng + caption"* trong D11 có bảng, nhưng
bảng nhỏ.

Và không có bất biến nào chặn: I1–I12 **không có bài nào khẳng định `token_count <= max_tokens`**. Kiểm lại
danh sách I1–I10 trong spec — không có. Nghĩa là lời hứa cốt lõi của tham số `max_tokens` chưa từng được bảo
vệ bằng test.

**Sửa:**

1. Thêm **I15**: `all(c.token_count <= max_tokens for c in chunks)` — trừ ngoại lệ được khai báo tường minh.
2. Quyết định bảng: cắt theo **hàng** (giữ dòng header lặp lại ở mỗi mảnh, đúng kiểu markdown), hay chấp nhận
   vượt trần và ghi ngoại lệ vào chunk (`oversize: true`). Cắt theo hàng đúng hơn — một bảng 60 dòng nhét vào
   một vector là vô dụng cho truy hồi dù model có nhận nổi.

Bảng bị cắt thì I7 (*không cắt ngang câu*) không áp dụng — ranh giới bảng là ranh giới **hàng**, không phải
câu. Cần ghi rõ ngoại lệ này khi viết I15.
