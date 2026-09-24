# Pipeline chuẩn: Biến tài liệu PDF/DOCX thành lộ trình học tương tác

Tài liệu này đặc tả luồng đi chuẩn, chi tiết từng bước, kèm input/output, kỹ thuật đề xuất và hợp đồng dữ liệu (JSON schema) giữa các module.

> **Tài liệu này là nguồn chân lý.** Khi nó mâu thuẫn với `spec-preview.md` (hệ nhãn T1–T4) hoặc bất kỳ
> bản nháp nào khác, bản này thắng. `spec-preview.md` giữ lại làm tham chiếu lịch sử và cho phần phụ lục
> nghiên cứu; mọi thay đổi thiết kế phải được ghi ở đây.

## 0. Kiến trúc tổng thể

Hệ thống gồm **2 pha** và **2 nhánh**:

- **Pha A — Ingestion (offline)**: chạy một lần khi tài liệu được upload. Sau bước chunking, pipeline tách thành 2 nhánh song song: **nhánh chỉ mục vector** (phục vụ RAG) và **nhánh đồ thị tri thức** (phục vụ sinh lộ trình). Hai nhánh hội tụ ở bước lắp ráp giai đoạn.
- **Pha B — Learning loop (online)**: chạy lặp lại mỗi khi user tương tác — hỏi đáp, làm quiz, mở khóa giai đoạn.

Nguyên tắc vận hành xuyên suốt: **mỗi bước ghi output trung gian ra storage** (bảng riêng hoặc file JSON có version). Các bước dùng LLM là đắt và dễ lỗi nhất — khi cần chỉnh prompt hay retry, chỉ chạy lại từ bước đó.

**Không chi tiêu ngầm** (spec v2, W1): mọi lời gọi mô hình trả tiền của chuỗi đồ thị đi qua một chốt chặn; lệnh
`roadmap` chỉ được gọi mô hình khi có `--allow-spend`, thiếu cờ thì dừng ở stage đầu tiên định chi và nói tên stage.
Stage có cache không cần cờ. Lý do: đổi thuật toán một stage (như F126 đổi pass phụ) làm mọi tài liệu chạy lại stage
đó khi gọi `roadmap`, và không ai được biết trước nếu lệnh không dừng lại.

```
PHA A (offline)

PDF/DOC
  |
A1. Parse layout-aware (giữ heading, trang, bảng)
  |
A2. Chunking theo cấu trúc
  |
  +--------------------------------------------+
  |                                            |
  | NHÁNH ĐỒ THỊ                               | NHÁNH CHỈ MỤC
  |                                            |
A3. Extract concepts + thực thể media          A3'. Embed chunks
  |   (kèm chunk_ids, vị trí xuất hiện)        |    -> Vector DB
A4. Merge duplicate concepts                   |    (metadata: section,
  |                                            |     page, order_index,
A5. Tổng hợp description hoàn chỉnh            |     module_id = null)
  |                                            |
A6. Semantic graph (co-occurrence + similarity)|
  |                                            |
A7. Cluster (Leiden)                           |
  |                                            |
A8. Suy luận prerequisite                      |
  |   8a. nội cluster (confidence + evidence)  |
  |   8b. liên cluster (boundary concepts)     |
  |                                            |
A9. Kiểm tra nhất quán [CHỈ cạnh requires]     |
  |   9a. Quality gate (lỗi pipeline chết)     |
  |   9b. Gỡ chu trình, giao DAG thật          |
  |   9c. Đánh dấu cạnh bắc cầu                 |
  |                                            |
A9'. Kiểm nguồn dạy (C8 v2, bản tạm)           |
  |                                            |
A9''. Danh tính: gộp khái niệm trùng (chưa bật)|
  |                                            |
A10. Dãy học neo sách -> chia module           |
  |    [CHỈ requires; chưa gắn media]          |
  |                                            |
A11. Module enrichment (objectives, quiz)      |
  |                                            |
A12. Gắn module_id ngược về chunk <------------+
  |
A13. (Tùy chọn) Human review + version hóa
  |
PHA B (online)
  |
B1. UI graph + progress store
B2. Tutor agent (scoped RAG theo giai đoạn)
B3. Assessment agent (quiz, chấm, unlock)
B4. Adaptive loop (mastery, ôn tập)
```

---

## 0.1. Hệ kiểu node và cạnh — luật nền cho toàn bộ pha A

Đồ thị **không chỉ có khái niệm**. Mục tiêu: ngoài lộ trình học, đồ thị còn phải phục vụ agent truy vấn
ở pha B — *"cho tôi xem hình minh hoạ khái niệm này"*, *"bảng nào chứa số liệu về X"*. Điều đó đòi
nhiều kiểu node, nhưng lộ trình học thì chỉ chạy trên khái niệm.

**Quyết định: một đồ thị duy nhất, hệ kiểu MỞ, chỉ đóng đúng phần lõi mà thuật toán cần.**
Không dựng hai đồ thị song song, và **không** ép LLM vào một danh sách kiểu cố định.

### Nguyên tắc: lõi đóng, vành mở

Đồ thị càng giàu kiểu càng phục vụ agent tốt — công trình gần nhất trong miền giáo dục dùng **tám loại
cạnh** (`component_of`, `uses`, `optimizes`, `computed_by`, `example_of`, `contrasts_with`, …) và hơn
SOTA trước 14–31%. Ép về bốn loại là tự bịt khả năng truy vấn của pha B.

Nhưng **topo sort là thuật toán có hợp đồng cứng**: nó phải biết cạnh nào mang nghĩa "thứ tự", và tập
đó phải hữu hạn, biết được lúc viết code. Nếu để LLM tự do sinh cả loại này, nó sẽ rải `requires`,
`prerequisite_of`, `depends_on`, `needs` — cùng nghĩa, và topo chỉ thấy một cái. **Mất im lặng phần lớn
số cạnh**, quality gate hiểu nhầm, tài liệu rơi xuống fallback mà không gì báo lỗi.

| Phần | Trạng thái | Ai quyết định |
|---|---|---|
| Cạnh `requires` | **ĐÓNG** — tên dành riêng, không đồng nghĩa | Code; agent chỉ đề xuất |
| Media `figure`/`table` | **ĐÓNG** — sinh từ refs của B0 | Code, tất định |
| Mọi `node_type` khác | **MỞ** | LLM tự đặt |
| Mọi loại cạnh khác | **MỞ** | LLM tự đặt |

LLM nghĩ ra `theorem`, `algorithm`, `definition`, `example`, `dataset` — cứ tạo. Nghĩ ra `contrasts_with`,
`generalizes`, `computed_by` — cứ tạo. Chúng được lưu, được lập chỉ mục, và **agent pha B đọc được**.

### Cạnh media: đồng vị trí là sàn, mô hình chỉ đánh dấu

`illustrates` (figure → node học được) và `tabulates` (table → node học được) **không do LLM tạo**.
Chúng sinh bằng **đồng vị trí**: media nối sang **mọi** node học được trích từ cùng chunk — tất định,
suy thẳng từ refs của B0, và là **sàn recall** không bao giờ sót.

Mô hình — vốn đang nhìn ảnh, hoặc đang đọc markdown của bảng nằm sẵn trong chunk — **xác nhận** một
**tập con** các node mà media thật sự minh hoạ; cạnh tương ứng mang `confirmed: true`. Tập con rỗng,
một, hay nhiều đều hợp lệ: một hình hoàn toàn có thể minh hoạ hai khái niệm thật, ép chọn một là bắt
mô hình nói dối.

**Người tiêu thụ của `confirmed` là `get_media_for_concept` ở pha B.** Không có nó thì người học hỏi về
một khái niệm sẽ nhận về bất kỳ hình nào tình cờ nằm cùng chunk — đo trên ca thật: 2 ảnh × 4 node =
8 cạnh, có nghĩa chắc 2. Nhiễu ở đây là **ảnh sai hiện ra trước mặt người học**, không phải nhiễu thống kê.

Xác nhận đặt ở bước trích chứ không để agent lọc lúc truy vấn, vì lúc trích mô hình **đang nhìn bức
ảnh**, còn lúc truy vấn agent chỉ có chuỗi mô tả — rẻ hơn, chính xác hơn, và trả tiền một lần.

**Không có đường nào để bước xác nhận làm mất cạnh**: xác nhận sai ⇒ thừa một nhãn; bỏ sót ⇒ cạnh vẫn
còn nguyên nhờ sàn đồng vị trí. Đúng bất đối xứng đã dùng cho ngưỡng blocking ở 2a.

Cạnh media **xuyên chunk** — hình ở chương 3 minh hoạ khái niệm chương 7 — **hoãn tới sau merge**:
khái niệm phải canonical trước, nếu không sẽ nối vào một biến thể sắp bị gộp mất.

### Luật an toàn: danh sách CHO PHÉP, không phải danh sách chặn

> **A9 và A10 chỉ đọc duy nhất tập cạnh `requires`.** Không phải "lọc bỏ các kiểu khác" — mà là
> **chỉ nhìn một kiểu**.

Khác biệt quyết định: với danh sách chặn, mỗi kiểu mới là một cơ hội làm hỏng topo và phải nhớ cập nhật.
Với danh sách cho phép, thêm năm mươi kiểu cạnh mới **không bao giờ chạm tới** topo — an toàn **theo
cấu trúc**, không theo kỷ luật của người viết.

| Bước | Đọc gì | Vì sao |
|---|---|---|
| A6 semantic graph | **mọi cạnh, mọi kiểu node** | Càng nhiều tín hiệu càng tốt |
| A7 cluster | **mọi cạnh, mọi kiểu node** | Media và kiểu mới đều mang tín hiệu gom cụm |
| A8b liên cụm | **mọi cạnh, mọi kiểu node** | Media và node lạ bắc cầu giữa các cụm |
| A9a quality gate | **chỉ `requires`**, mẫu số là node **học được** | Đo mật độ *cấu trúc tiên quyết* |
| A9b remove cycle | **chỉ `requires`** | Chu trình trong *thứ tự* |
| A9c transitive reduction | **chỉ `requires`** | Dư thừa trong *thứ tự* |
| A10 layering | **chỉ `requires`** | Phân tầng theo *thứ tự* |

Gặp một thuật toán không có trong bảng: *nó có coi cạnh là quan hệ thứ tự không?* Có thì chỉ đọc
`requires`; không thì đọc hết.

### Kiểu được gán lúc nào, và vì sao guard vẫn an toàn

| Quyết định | Bước | Ai |
|---|---|---|
| `node_type` của khái niệm và các kiểu LLM nghĩ ra | Extract (Tầng 1) | **LLM tự đặt**, chuỗi tự do, prompt không đưa danh sách |
| `node_type` của media | Extract (Tầng 1) | **Code** — đọc refs của B0; LLM không đụng tới |
| Chuẩn hoá tối thiểu chuỗi kiểu trước khi bỏ phiếu (casefold, ánh xạ sổ đã duyệt) | Tầng 2a | Code |
| Chuẩn hoá / gộp kiểu theo nghĩa | Tầng 3 | Code + gắn cờ cho người |
| `learnable` | Extract + sổ đăng ký | LLM bắt buộc khai cho entity · code ép `false` cho media · artifact cũ thiếu trường mặc định `true` |
| Cạnh `requires` **vào đồ thị** | Tầng 2b | **Executor duyệt**; agent chỉ đề xuất |

**Tính chất quan trọng: guard `requires` đúng bất kể LLM gán kiểu hay cờ dở thế nào.** Media do code tạo
luôn `false`; executor chỉ nhận `requires` khi cả hai đầu thật sự `learnable=true`. Gán sai có thể làm
thừa/thiếu mục học và phải được A13 sửa, nhưng không thể đưa đầu `false` vào DAG.

### Cờ `learnable` — thay cho việc liệt kê kiểu

Kiểu mở nghĩa là **không thể** viết luật "chỉ `concept` mới vào DAG": nếu LLM tạo `theorem` hoặc
`algorithm`, chúng **học được** và xứng đáng nằm trong lộ trình; loại chúng ra là mất nội dung thật.

Nên mỗi kiểu node mang một cờ trong **sổ đăng ký kiểu**:

- `learnable = false`: code cố định cho media; LLM khai cho entity chỉ là bối cảnh như tổ chức, công cụ
  hay dataset được nhắc.
- `learnable = true`: LLM khai khi người học phải học và hoàn thành node. Artifact cũ thiếu trường vẫn
  mặc định `true` để không âm thầm làm mất recall khi đọc lại.

Trong A3, cờ của cùng một `node_type` lấy đa số ứng viên, hoà mới chọn `true`. Cùng tên khác kiểu mà
cờ trái nhau chỉ được cảnh báo; luật 2a bên dưới quyết định kiểu canonical và cờ cuối, không lấy ngầm
ứng viên xuất hiện trước.
- Người review ở A13 đổi cờ cho các kiểu rõ ràng không học được (`person`, `citation`, `dataset`…).

Mẫu số của quality gate và tập node vào layering đếm theo **`learnable = true`**, không theo tên kiểu.

### Sổ đăng ký kiểu và pha chuẩn hoá — kiểu mở đòi chuẩn hoá, không phải tuỳ tiện

Kiểu mở **sẽ** trôi: bốn LLM cùng một corpus cho tuân thủ schema chỉ **57–84%**. Nên tự do đi kèm một
bước bắt buộc ở **tầng 3**, đúng khuôn "trích mở rồi chuẩn hoá" (EDC) nhưng áp cho **từ vựng kiểu**:

1. Gom các chuỗi tên kiểu theo độ giống (chuỗi + embedding): `example_of` / `is_example_of` / `vd_cho`
   về một kiểu chuẩn.
2. Kiểu dùng **≥ N lần** được ghi vào sổ đăng ký là kiểu đã biết; kiểu chỉ xuất hiện một lần bị gắn cờ
   cho người review — có thể là phát hiện hay, cũng có thể là rác.
3. **Không kiểu nào được phép chuẩn hoá về `requires`** bằng máy. Nếu LLM sinh `prerequisite_of` và nó
   thật sự nên là `requires`, việc nâng cấp đó phải do người quyết ở A13 — vì nó **thêm cạnh vào DAG
   lộ trình**, thứ đắt nhất khi sai.
4. Sổ đăng ký kiểu là artifact có phiên bản, ghi cùng manifest đồ thị.

### Ba bất biến

- **I-G1** — mọi cạnh `requires` có cả hai đầu là node `learnable = true`. Thi hành ở executor của
  `add_edge`, không dặn dò trong prompt.
- **I-G2** — mọi node `figure`/`table` có `description` khác rỗng, và **hoặc** nối ít nhất một node học
  được, **hoặc** mang `orphan_reason` giải thích vì sao không.

  > Media mồ côi là **trạng thái hợp lệ**, không phải lỗi: logo trường trên trang bìa không minh hoạ
  > khái niệm nào, và đó là đúng. Bắt nó luôn có cạnh thì người soát học cách bỏ qua cờ, rồi cờ thật
  > cũng bị bỏ qua theo — đúng lớp lỗi *"cảnh báo không đọc được thì bằng không có cảnh báo"*.
  > `orphan_reason` ∈ `cover_art` · `no_concept_in_chunk` · `unknown`; **chỉ `unknown` phát cảnh báo**.
  > Thứ đáng theo dõi là **tỉ lệ** mồ côi, không phải từng ca.
  >
  > Ngược lại, `description` rỗng **luôn là lỗi**: hình thì mô hình nhìn ảnh mà tả, bảng thì nội dung
  > markdown đã nằm sẵn trong chunk — không có ca hợp lệ nào cho việc không mô tả được.
- **I-G3** — mọi kiểu node và kiểu cạnh xuất hiện trong đồ thị đều có mặt trong sổ đăng ký kiểu, kèm
  số lần dùng. Kiểu không có trong sổ ⇒ lỗi, không phải cảnh báo.

### Công thức chưa thành node ở vòng này

Corpus tham chiếu bốn tài liệu có **258 công thức** so với 19 hình và 60 bảng — đưa vào sẽ chiếm khoảng
nửa đồ thị, và nội dung thô của chúng đã biết là lộn xộn thứ tự khi trích từ PDF. `formula_refs` vẫn
giữ nguyên trong chunk làm bằng chứng cho khái niệm; xét lại khi có cách đọc công thức đáng tin.

### Số đo neo quyết định (corpus bốn tài liệu, 2026-08-29)

```
thực thể duy nhất : 19 hình · 60 bảng · 258 công thức
bậc node media    : tối đa 2 · trung bình 1,05 · 94% bậc 1 · 0 hub
```

Bậc thấp là lý do media được thả vào A6/A7 mà không sợ gộp nhầm cụm. **Dây bẫy:** media bậc ≥ 5 phát
cảnh báo và bị hạ trọng số theo `1/(bậc−1)` trong đồ thị ngữ nghĩa — chưa cần với corpus hiện tại,
cần khi tài liệu có hình "tổng quan toàn chương" nối hàng chục khái niệm.

---

## PHA A — INGESTION

### A1. Parse tài liệu (layout-aware)

- **Mục đích**: tách nội dung nhưng giữ nguyên cấu trúc — heading phân cấp, số trang, bảng, caption hình. Cấu trúc này là tín hiệu quý nhất cho cả chunking lẫn suy luận tiên quyết (doc-order prior).
- **Input**: file PDF hoặc DOCX.
- **Kỹ thuật**: Docling hoặc Unstructured.io cho PDF (PyMuPDF nếu muốn nhẹ); python-docx cho DOCX (heading có sẵn trong XML). PDF scan → OCR fallback (Tesseract/PaddleOCR) trước khi parse.
- **Output**: cây tài liệu.

```json
{
  "doc_id": "doc_001",
  "title": "Giáo trình Machine Learning",
  "sections": [
    {
      "section_id": "s_3_2",
      "heading": "3.2 Overfitting và Regularization",
      "level": 2,
      "parent_id": "s_3",
      "page_start": 41,
      "blocks": [
        {"type": "paragraph", "text": "...", "page": 41},
        {"type": "table", "html": "...", "caption": "...", "page": 42}
      ]
    }
  ]
}
```

- **Lưu ý**: đừng dùng extract text thô (`page.extract_text()`) — mất heading là mất xương sống của toàn pipeline.
- **Bộ đọc PDF** *(2026-09-24)*: mặc định `docling-parse`. `ingest --pdf-backend pypdfium2` cho PDF dùng font tiếng
  Việt cũ mà `docling-parse` tách rời âm tiết ("Ph ươ ng pháp"): trên 5 trang của doc-4, `docling-parse` cho 34,5% token
  ngắn có dấu, `pypdfium2` 19,2% — mức của tiếng Việt bình thường (từ đơn "là", "và"). Lựa chọn nằm trong `adapter`
  của cấu hình parser nên đi vào hash; bộ đọc mặc định giữ nguyên identifier để hash của tài liệu cũ không đổi.
  **Kiểm trước khi chạy A3**: văn bản chunk có chữ liền (tỉ lệ token ngắn có dấu ≲ 20%), vì A3 trên chữ vỡ phí tiền
  và sinh tên khái niệm hỏng.
- **Thang tiêu đề** *(2026-09-24)*: `ingest --heading-scheme vn-textbook` cho giáo trình tiếng Việt đánh số lại từ đầu
  trong mỗi cấp (Phần → Chương → A./B. → I- → 1. → a), cấp 1–6). Luật mặc định đếm dấu chấm nên đặt "1." lên trên
  "Chương" và loại tiêu đề La Mã dài hơn 15 từ như văn bản; trên doc-4 điều đó để các mục của Chương VIII nằm ngoài
  chương. Chỉ ghi vào `config.chunk` khi bật, để hash của tài liệu cũ không đổi.

### A2. Chunking theo cấu trúc

- **Mục đích**: tạo đơn vị retrieval, mỗi chunk tự chứa ngữ nghĩa và mang đủ metadata để trích dẫn nguồn và gắn giai đoạn về sau.
> **Mục này mô tả pha B0 ĐÃ DỰNG** (`section-id-v8`, adapter 8). Bản trước của mục này ghi
> "mục tiêu 300–800 token, overlap 10–15%" — sai so với thứ đang chạy, và sai cả so với bằng chứng
> ngoài; xem [báo cáo đối chiếu chuẩn quốc tế](../report/doi-chieu-chuan-quoc-te-chunking.md).
> Ai tính toán trên số chunk hoặc cỡ chunk phải dùng số dưới đây.

- **Quy tắc**:
  - Cắt theo ranh giới section trước; trong section, **gộp** các leaf block liền nhau cùng section quanh
    mục tiêu **256 token**, và chỉ **tách** khi vượt trần.
  - **Ba trần token**: 512 cho văn xuôi · 2048 cho nhóm có chứa bảng · 6000 là trần cứng tuyệt đối,
    không ngoại lệ. Chunk vượt trần áp dụng cho nó phải khai `oversize_reason` (bất biến I25).
  - **Không overlap** giữa các chunk gộp. Overlap câu chỉ dùng khi **một khối đơn** dài quá trần phải
    cắt đôi. Lý do: cắt theo cấu trúc làm ranh chunk trùng ranh ngữ nghĩa nên không cần overlap bù;
    đo được rằng overlap cho lợi ích recall giảm dần trong khi precision giảm mạnh hơn.
  - Bảng giữ nguyên thành 1 chunk riêng (kèm caption), **không cắt ngang bảng** — đây là lý do trần
    bảng cao gấp bốn trần văn xuôi.
  - Nội dung không phải chữ đọc được (hình, bảng, công thức) để **dấu vết trong `text`** còn danh tính
    ở **danh sách tham chiếu riêng**, cố ý đứng ngoài khoá băm định danh chunk (ADR 0002).
  - `order_index` tăng dần theo thứ tự xuất hiện trong tài liệu — sẽ dùng làm prior ở bước A8.
  - Định danh băm theo **nội dung + đường dẫn section**, không theo vị trí (ADR 0001): chèn một đoạn ở
    đầu tài liệu không làm đổi định danh các chunk phía sau.
- **Output** (đúng hình dạng đang sinh; `section_path` là **mảng**, không phải chuỗi):

```json
{
  "chunk_id": "c_a3f19c2b8d40",
  "doc_id": "nhap-mon-ml",
  "order_index": 42,
  "split_index": 0,
  "page": 41,
  "char_start": 18342,
  "char_end": 19118,
  "parent_section_id": "s_7b1e04c9a2f5",
  "section_path": ["Chương 3", "3.2 Overfitting và Regularization"],
  "heading_level": 2,
  "block_types": ["text", "list_item"],
  "text": "...",
  "context_prefix": null,
  "token_count": 261,
  "tokenizer_id": "google-gemma-sentencepiece-v1:61a7b147390c",
  "image_refs": [],
  "table_refs": [],
  "formula_refs": [],
  "oversize_reason": null
}
```

> `stage_id` (sẽ đổi tên thành `module_id` khi triển khai A12 — ADR 0010) **không** nằm trong chunk artifact — A12 gắn nó ở tầng chỉ mục vector, đúng khuôn "tham
> chiếu đứng ngoài khoá băm" để cập nhật `stage_id` không phải embed lại. Xem A3'.

### A3'. Nhánh chỉ mục vector (chạy song song với A3–A11)

- **Mục đích**: nền tảng retrieval cho pha học. Không có bước này thì "user truy vấn từng giai đoạn" không hoạt động.
- **Kỹ thuật**: embedding đa ngữ nếu tài liệu tiếng Việt (`bge-m3` hoặc `multilingual-e5-large`); lưu vào Postgres + pgvector (đơn giản) hoặc Qdrant/Weaviate (nếu cần scale).
- **Metadata bắt buộc trên mỗi vector**: `doc_id, chunk_id, section_id, page, order_index, stage_id` (tạm null, điền ở A12; đổi tên thành `module_id` khi triển khai A12 — ADR 0010).

### A3. Extract concepts + thực thể media theo section

- **Mục đích**: biến nội dung phẳng thành danh sách thực thể có nguồn gốc rõ ràng — khái niệm trích từ
  văn bản, media lấy từ tham chiếu B0 đã sinh.

#### A3.1 Khái niệm — ba giai đoạn trong cùng hội thoại

Một lượt trích là **thiếu**: khái niệm bỏ sót ở A3 không bao giờ xuất hiện lại ở bất kỳ tầng nào sau —
A4 chỉ gộp cái đã có, A8 chỉ nối cái đã có. **Recall của A3 là trần cứng cho toàn bộ lộ trình.** Khái
niệm thừa thì tầng sau lọc được; khái niệm thiếu thì mất vĩnh viễn.

| Giai đoạn | Nhắm | Nội dung |
|---|---|---|
| **1 — trích** | **Recall** | Trích node/cạnh/media ban đầu của section. |
| **2 — quét lại** | **Recall** | Hỏi *"còn khái niệm nào được giảng trong đoạn này chưa liệt kê?"*; dừng khi thêm 0, trần 5 vòng. |
| **3 — kiểm định** | **Precision** | Soát theo lô node và cạnh đề xuất trong cùng hội thoại. |

- **Bắt buộc bằng chứng cho khái niệm**, không chỉ cho cạnh. Khái niệm không trích được câu bằng chứng
  trong chunk nguồn ⇒ loại. Khái niệm bịa sinh ra node mà mọi thứ khác bám vào, nguy hiểm hơn cạnh bịa.
- Schema A3 có `description_draft` nhưng **không có `difficulty`**. Độ sâu tiên quyết của DAG là một
  chỉ số cấu trúc, không phải độ khó của khái niệm.
- Chạy song song theo section; không ghép nội dung section láng giềng vì evidence chỉ được dò trong
  đúng section hiện tại.

#### A3.2 Media — lấy từ tham chiếu, không để LLM tự nhận

Node `figure` và `table` **không do LLM phát hiện**. Chúng lấy thẳng từ `image_refs` và `table_refs`
của chunk — B0 đã sinh sẵn, có định danh băm nội dung và vị trí ký tự. Đây là đường **tất định**.

Việc duy nhất cần LLM là **mô tả ảnh không có chú thích**:

- Ảnh **có** chú thích ⇒ dùng chú thích làm `description`, nhưng vẫn đưa ảnh vào lượt trích chung.
- Ảnh **không** chú thích ⇒ **ảnh đi thẳng vào prompt trích** cùng văn bản (chỉ 13/129 section mang
  ảnh nên chi phí nhỏ). Mô hình vừa nhìn vừa đọc, nên neo ngữ cảnh xảy ra **trong lúc** mô tả thay vì
  kiểm sau — không cho ảo giác sinh ra, thay vì sinh ra rồi lọc. Prompt hỏi **cái nhìn thấy được**
  (trục ghi gì, mấy đường, nhãn nào), **không** hỏi ý nghĩa, để mô hình không chép lại văn bản xung
  quanh rồi gọi đó là mô tả ảnh.
- **Bảng không chú thích đi đường khác**: markdown của bảng **đã nằm trong `text` chunk**, mô hình đang
  đọc rồi — mô tả sinh từ nội dung đó, **không tốn lời gọi nào và không cần ảnh**. Đo được: 4/64 bảng
  có chú thích, 8/19 hình có.
- `caption_source` ∈ `original` · `generated_multimodal` (hình) · `generated_from_content` (bảng) ·
  `none` (**trạng thái hỏng**, phải đếm và báo).
- Cạnh `illustrates` / `tabulates` sinh bằng **đồng vị trí** — xem mục *Cạnh media* ở §0.1.
- Mô hình chỉ trả tập con cạnh đồng-vị-trí được xác nhận; code gắn `confirmed: true`, không tạo hoặc
  xóa cạnh.

#### Output

```json
{
  "raw_entity_id": "rc_017",
  "node_type": "concept",
  "name": "L2 Regularization",
  "aliases": ["Ridge", "weight decay"],
  "description_draft": "Kỹ thuật phạt bình phương trọng số để giảm overfitting...",
  "evidence": "L2 regularization thêm số hạng phạt λ‖w‖² vào hàm mất mát",
  "source_chunk_ids": ["c_0042", "c_0043"],
  "first_order_index": 42
}
```

```json
{
  "raw_entity_id": "rf_004",
  "node_type": "figure",
  "media_id": "a3f19c2b8d40e7b1",
  "name": "Hình 3.4 — Đường cong học của mô hình quá khớp",
  "description": "chú thích gốc, hoặc mô tả do mô hình thị giác sinh đã qua kiểm định",
  "caption_source": "original",
  "source_chunk_ids": ["c_0042"],
  "first_order_index": 42
}
```

`caption_source` nhận `original` (chú thích của tài liệu) hoặc `generated` (mô hình sinh, đã qua kiểm
định) — để tầng sau và người review biết mức tin của mô tả.

### A4. Merge duplicate concepts

- **Mục đích**: cùng một thực thể xuất hiện ở nhiều section (định nghĩa ở chương 2, ví dụ ở chương 5) phải gộp thành 1 node duy nhất. Mapping section ↔ thực thể là many-to-many.
- **Thiết kế: một, dùng chung cho cả pipeline cố định lẫn biến thể** — chính là Tầng 2a (xem mục đó). Khác biệt
  giữa hai biến thể nằm ở suy luận cạnh, không ở merge. Tóm tắt:
  1. Code **chỉ** gộp ứng viên trùng tên khít sau chuẩn hoá (kể cả vị trí dấu thanh `hoá`/`hóa`).
  2. Alias, tên gần giống (n-gram) và tên gần nghĩa (embedding **tên**) chỉ **đề cử** cặp nghi trùng — không có
     ngưỡng cosine nào được gộp thẳng (ADR 0006).
  3. Cặp nghi trùng gom thành cụm ứng viên nhỏ; mỗi cụm một lời gọi mô hình phán theo câu bằng chứng nguyên văn.
- Khi merge: hợp `chunk_ids` bằng chứng; `first_order_index` lấy từ chunk định nghĩa/giảng mà A5 chỉ ra (giữ thêm
  `first_mention_index`); tên chuẩn là tên gọi đầy đủ tài liệu dùng nhiều nhất trong tên các ứng viên; id theo ứng
  viên neo (ADR 0005).
- Spec chi tiết: [`A4-A5-hop-nhat-thuc-the-spec.md`](./A4-A5-hop-nhat-thuc-the-spec.md).

> Bản trước ghi *"≥ 0.90 merge tự động"* trên embedding `description_draft`. Đo trên bốn tài liệu: cosine giữa hai
> thực thể bất kỳ đã là 0,80; trong 62 cặp khác tên vượt 0,95 chỉ 8 cặp là trùng thật; ngưỡng 0,90 làm một node nuốt
> 125/153 ứng viên. Xem `report/nghien-cuu-a4-a5-hop-nhat-thuc-the.md` mục 2.

**Media không đi qua các lớp trên.** Hai hình giống hệt nhau **đã có cùng `media_id`** — B0 băm theo
nội dung, nên khử trùng lặp là phép so chuỗi bằng code, **không tốn một lời gọi LLM nào** và tất định
tuyệt đối. Đây là thứ B0 để lại sẵn; đừng dựng lại bằng embedding.

### A5. Tổng hợp description hoàn chỉnh

- **Lời gọi riêng**, chạy sau khi bảng node canonical đã chốt — bước phán merge không viết mô tả. Cùng tầng
  artifact `canonical`.
- Mọi node trừ media, mọi kiểu. Node nhiều ứng viên ⇒ tổng hợp. Node một ứng viên ⇒ kiểm `description_draft` với
  câu bằng chứng; chỉ viết lại khi draft không được bằng chứng hỗ trợ hoặc sai ngôn ngữ.
- Đầu vào: toàn văn chunk bằng chứng theo **thứ tự tài liệu** (trần ~4k token). Đầu ra: **1–4 câu theo lượng bằng
  chứng**, mỗi câu kết thúc bằng `chunk_id` trích dẫn — code từ chối id không thuộc node; được ghi *"tài liệu không
  nói thêm"*. Ép 4 câu khi tài liệu chỉ nói 1 câu là mời mô hình bịa.
- Nguồn mâu thuẫn ⇒ **không hoà giải**, gắn cờ `nghi_gop_nham` cho tầng 3/A13 — mô tả mâu thuẫn là triệu chứng của
  gộp nhầm.
- A5 chỉ ra chunk **định nghĩa/giảng** (`defining_chunk_ids`) ⇒ nguồn của `first_order_index`.
- Ngôn ngữ mô tả = ngôn ngữ chủ đạo của tài liệu (code đo, ghi manifest).
- Độ sâu tiên quyết là chỉ số cấu trúc của DAG, không phải trường `difficulty`. Description dùng cho hiển thị UI, ngữ cảnh suy luận edge và
  sinh quiz — nhưng luật *"Y trong định nghĩa X"* của 2b đọc **câu bằng chứng nguyên văn**, không đọc mô tả này.
- **Media đi đường khác**: mô tả đã chốt ở A3.2 (chú thích gốc hoặc mô tả đã qua kiểm định). **Không**
  đọc `source_chunk_ids` để viết lại — làm thế là để mô hình suy diễn về nội dung ảnh từ văn bản xung
  quanh, đúng loại ảo giác tầng kiểm định vừa chặn.

### A6. Semantic graph (đồ thị chủ đề thô)

> **Chi tiết A6–A10 nằm ở [`A6-A8-cum-chu-de-mention-map-va-tien-quyet-spec.md`](./A6-A8-cum-chu-de-mention-map-va-tien-quyet-spec.md)** (2026-09-16).
> Spec đó **sửa ba chỗ** của mục này và các mục A7, A8, Tầng 2b dưới đây: bỏ ngưỡng cosine tuyệt đối khi dựng
> cạnh (dùng mutual-kNN và đồng xuất hiện có chuẩn hoá); trần cỡ cụm là ràng buộc cứng đếm theo khái niệm thay
> cho lượt chẻ đệ quy; và luật "dưới 50 trang thì một phiên" đổi thành ngưỡng theo số khái niệm học được. Nó
> cũng **hẹp hơn** một chỗ: 2b chỉ sinh `requires`, không đặt thêm kiểu cạnh mới. Khi hai tài liệu lệch nhau,
> theo spec A6–A8.

- **Mục đích**: tạo input cho bước cluster. Đây KHÔNG phải đồ thị tiên quyết — chỉ là đồ thị "liên quan".
- **Chạy trên đồ thị đầy đủ** (mọi `node_type`) — xem §0.1.
- **Edge thô** gồm 3 nguồn, có trọng số:
  - Co-occurrence: 2 concept cùng xuất hiện trong 1 chunk (trọng số cao) hoặc cùng section (trọng số thấp hơn).
  - Similarity: cosine của embedding description ≥ ngưỡng (vd 0.75).
  - **Media**: `image_refs`/`table_refs` của chunk cho biết **chính xác** media nào nằm cùng chunk với
    khái niệm nào — không phải suy, và **không phụ thuộc mô hình embedding**.
- **Vì sao nguồn thứ ba đáng giá**: hai nguồn đầu là quan hệ **suy ra** — cosine trôi khi đổi mô hình
  embedding. Liên kết qua media là quan hệ **có căn cứ trong tài liệu**: tác giả tự tay đặt mấy khái
  niệm đó vào chung một hình. Đây cũng là **nguồn dữ liệu cho loại cạnh `relates_to`** dùng hiển thị
  "liên quan" trên UI ở pha B.
- **Hạ trọng số media bậc cao**: media nối nhiều khái niệm thì mỗi liên kết ít mang tin hơn — trọng số
  `1/(bậc−1)`, và bậc ≥ 5 phát cảnh báo. Corpus hiện tại bậc tối đa 2 nên luật này chưa kích hoạt;
  nó là dây bẫy cho tài liệu có hình "tổng quan toàn chương".

### A7. Cluster

- **Kỹ thuật**: Leiden (hoặc Louvain) trên semantic graph, **chạy trên đồ thị đầy đủ**. Media tham gia
  gom cụm và **nhận `cluster_id` của riêng nó** — media là tín hiệu gom cụm có căn cứ, loại nó ra là
  vứt bằng chứng. Fallback: nếu edge thô quá thưa, dùng HDBSCAN/K-means trực tiếp trên embedding của description.
- **Output**: mỗi node có `cluster_id`. Tinh chỉnh: cluster > 12 concept thì chạy lại Leiden bên trong cluster đó; cluster 1–2 concept thì sáp nhập vào cluster gần nhất.
- Ngưỡng cỡ cluster đếm theo **số concept**, không đếm media — nếu không, một cụm 5 khái niệm kèm 8
  hình sẽ bị chẻ nhỏ oan.

### A8. Suy luận quan hệ tiên quyết (bước quan trọng nhất)

**8a. Nội cluster.** Với mỗi cluster, một LLM call nhận: danh sách concept (tên + description + `first_order_index`) và các đoạn evidence tiêu biểu. Yêu cầu output các edge `A requires B` kèm confidence và bằng chứng:

```json
{
  "edge_id": "e_105",
  "from_concept": "cpt_regularization_l2",
  "to_concept": "cpt_overfitting",
  "relation": "requires",
  "confidence": 0.9,
  "evidence_chunk_ids": ["c_0042"],
  "rationale": "Section 3.2 định nghĩa L2 như giải pháp cho overfitting, giả định người đọc đã hiểu overfitting."
}
```

Quy tắc prompt bắt buộc:
- Đưa `first_order_index` làm **doc-order prior**: khái niệm xuất hiện sớm hơn trong tài liệu thường là tiên quyết — LLM chỉ được tạo edge ngược thứ tự tài liệu khi có bằng chứng rõ.
- Mỗi edge phải chỉ ra được evidence chunk. Không bằng chứng → không tạo edge (chống bịa quan hệ).
- Chỉ tạo edge tiên quyết trực tiếp, không tạo edge suy diễn xa (giảm việc cho bước transitive reduction).
- **`requires` là tên dành riêng**, chỉ nối hai node `learnable = true` (bất biến I-G1). Media không thể
  là tiên quyết của gì — "Hình 3.4" không phải thứ phải học trước. Luật thi hành ở **executor phía
  code**, không dặn dò trong prompt: `add_edge` từ chối op vi phạm và trả lỗi cụ thể.
- **Loại cạnh khác thì mở**: agent được tự đặt tên cho quan hệ nó thấy — `example_of`, `contrasts_with`,
  `component_of`, `computed_by`… Chúng được lưu, lập chỉ mục, và phục vụ agent pha B. Chúng **không**
  vào topo sort, nên tạo thoải mái không rủi ro.
- **Không được** dùng tên đồng nghĩa với `requires` (`prerequisite_of`, `depends_on`…). Nếu agent lỡ
  sinh, tầng 3 gắn cờ cho người xử lý — **không** tự động quy về `requires`, vì việc đó thêm cạnh vào
  DAG lộ trình, thứ đắt nhất khi sai.
- Cạnh `illustrates`/`tabulates` **không sinh ở đây** — chúng suy trực tiếp từ refs ở A3.2.

**8b. Liên cluster.** KHÔNG so mọi cặp concept (sẽ quay lại O(n²)). **Chạy trên đồ thị đầy đủ.**
Chỉ suy luận trên:
- Boundary concepts: concept có co-occurrence với chunk thuộc cluster khác.
- **Media bắc cầu**: một `figure`/`table` được tham chiếu từ chunk thuộc **hai cluster khác nhau** thì
  **tự nó là boundary object** — biết ngay từ refs, tất định, không phải tính. Các khái niệm nó nối tới
  là ứng viên cặp liên cụm chất lượng cao, vì tác giả đã đặt chúng cạnh nhau trong cùng một hình.
- Các cặp cluster có tổng trọng số liên kết ngữ nghĩa đủ mạnh.

LLM nhận tóm tắt 2 cluster + các boundary concept, output edge cùng schema trên. Edge sinh ra ở đây
vẫn phải tuân I-G1 — chỉ `requires` giữa hai concept.

### A8'. Pass cạnh ngầm *(vé v2-06; có mã, chưa vào chuỗi mặc định)*

> Quy tắc: [spec v2, W20](v2-do-thi-va-lo-trinh-neo-van-ban-spec.md). Stage `implicit`, sau `teaching`/`identity`.

- Ngoại lệ có kiểm soát của luật "chunk căn cứ nhắc cả hai đầu" (A8): căn cứ của cạnh ngầm là **một cụm nguyên văn
  trong đoạn dạy khái niệm đích** mà việc hiểu nó cần tiên quyết; mã kiểm chuỗi. Tiên quyết chỉ lấy trong K = 30
  khái niệm dạy ngay trước và chưa là tổ tiên; không đề xuất ngược thứ tự dạy.
- Cạnh mang `evidence_kind="ngam"`, `origin="implicit_pass"`, độ tin 0,6; gỡ chu trình bằng hàm của A9, cạnh ngầm hạng
  thấp nhất nên bị gỡ trước. A10 nhận stage `implicit`.

### A9. Kiểm tra tính nhất quán cấu trúc *(trước gọi là "Validate graph")*

> **Đổi tên ngày 2026-09-22 (V10).** Trong văn liệu, "kiểm định quan hệ tiên quyết" nghĩa là kiểm định trên **biểu
> hiện của học viên** — thứ dự án không có dữ liệu để làm. Cái A9 làm hẹp hơn hẳn: kiểm tính nhất quán **cấu trúc**
> của đồ thị. Bài báo phải dùng đúng chữ này.
>
> **Ba luật dưới đây đã bị vá.** Luật 1 bị V6 thay ngưỡng và cách đếm; luật 2 và 3 **lỗi thời hoàn toàn** — xem ghi
> chú ngay trong từng luật. Nguồn chân lý hiện hành: D11 của `A6-A8-cum-chu-de-mention-map-va-tien-quyet-spec.md`
> và `va-a9-a10-do-thi-tot-va-lo-trinh-dung-duoc-spec.md`.

> **Toàn bộ A9 chỉ đọc cạnh `requires`**, trên node `learnable = true` — xem §0.1. Đây không phải chi
> tiết hình thức: đọc cả các kiểu cạnh khác gây hai lỗi câm mô tả ngay dưới. Vì là danh sách **cho
> phép** (chỉ nhìn `requires`) chứ không phải danh sách chặn, LLM thêm bao nhiêu kiểu cạnh mới cũng
> không chạm được vào A9.

Theo đúng thứ tự:

1. **Quality gate** — **chỉ đếm cạnh `requires`, mẫu số là node `learnable = true`**, và **chỉ đếm cạnh không mang
   `redundant_via`** *(sửa 2026-09-22, V6: một cạnh suy ra được từ hai cạnh khác không thêm cấu trúc nào)*. Cổng
   đóng → **fallback**: lộ trình theo thứ tự chương gốc; graph chỉ dùng để hiển thị liên quan, không dùng để
   khoá/mở; pipeline nhảy thẳng tới A11. Cổng **luôn** ghi số đo ra manifest kể cả khi mở, và khi đóng thì sinh
   **cảnh báo đọc được** chứ không im lặng đổi chế độ.

   > **Hai hằng số 0,5 cạnh/node và 60% cô lập đã bị hạ xuống mức chỉ còn bắt lỗi pipeline chết (V6).** Lý do:
   > dải mật độ của **mọi đồ thị tiên quyết hợp lệ đã công bố** trải từ 0,34 đến 5,89 cạnh/node và từ 1,1% đến
   > 77,7% node cô lập — mạng tiên quyết môn học của Johns Hopkins kích hoạt **cả hai** cổng cũ. Không hằng số
   > đơn nào phân tách "có cấu trúc" khỏi "không có cấu trúc" qua dải đó; hai đại lượng này đo **mức chi tiết của
   > node và quy ước gán nhãn**, không đo chất lượng. Và **không tìm thấy nguồn nào** dùng ngưỡng mật độ để kích
   > hoạt phương án dự phòng — đây là chỗ dự án phải tự đo.

   > **Vì sao phải giới hạn mẫu số:** media không bao giờ có cạnh `requires`, nên đưa chúng vào mẫu số
   > làm tỉ lệ tụt mà tử số không đổi, đồng thời chúng bị đếm là "node cô lập" **miễn phí**. Ví dụ: 200
   > node học được + 150 cạnh ⇒ 0,75 qua cổng; thêm 79 media ⇒ **0,54**, và 28% cô lập miễn phí. Tài
   > liệu nhiều hình sẽ bị tuyên oan là "không có cấu trúc tiên quyết" rồi rơi xuống fallback —
   > **không có gì báo lỗi**. Cùng lý do: chỉ đếm cạnh `requires`, vì đếm cả `example_of` hay
   > `relates_to` sẽ làm tử số phồng lên và cổng luôn mở dù DAG rỗng.

2. **Remove cycle** — ~~trong mỗi chu trình cắt edge có `confidence` thấp nhất~~ **LỖI THỜI, ĐỪNG THEO.**
   Luật hiện hành là D11 của `A6-A8-cum-chu-de-mention-map-va-tien-quyet-spec.md` và V3/V4 của
   `va-a9-a10-do-thi-tot-va-lo-trinh-dung-duoc-spec.md`: tách thành phần liên thông mạnh, đưa cặp hai chiều ra
   thành cờ, rồi giải **minimum feedback arc set có trọng số** bằng liệt kê chu trình đơn + phủ tập hợp.
   **`confidence` do mô hình tự khai không tham gia quyết định** — đo trên corpus nó chỉ nhận ba giá trị, và văn
   liệu đo AUROC của nó ở mức xấp xỉ 0,5 *(xem `report/nghien-cuu-a9-a10-kiem-dinh-va-lo-trinh.md` mục 8)*.

   > **Vì sao phải lọc:** Tarjan không phân biệt kiểu cạnh nếu không ai bảo nó. Chạy trên đồ thị đầy
   > đủ thì `A requires B` + `B illustrated_by F` + `F illustrates A` thành **chu trình giả**, và bước
   > này sẽ đi cắt một cạnh `requires` **thật** để gỡ nó.

3. **Transitive reduction** — ~~xóa edge dư~~ **LỖI THỜI, ĐỪNG THEO.** Luật hiện hành: cạnh bắc cầu **chỉ được
   đánh dấu** `redundant_via`, **không bao giờ xoá** (D11 điểm 6, V5). Hai lý do: người duyệt gỡ một cạnh sai thì
   cạnh trực tiếp đúng đã biến mất và không tự quay lại; và đo được rằng **một** cạnh sai làm mất cạnh đúng trong
   **37,7%** số lần trên đồ thị mật độ tương đương, tệ nhất 25 cạnh. Thêm nữa, rút gọn bắc cầu **thiên lệch**: cạnh
   nhiễu ít bị bắc cầu hàm ý hơn cạnh thật, nên xoá cạnh thừa sẽ ưu tiên xoá cạnh đúng và giữ lại cạnh nhiễu.
   Và nó **không xác định** trên đồ thị còn chu trình, nên bắt buộc chạy sau bước 2.

   > **Vì sao phải lọc:** chạy trên đồ thị đầy đủ có thể xoá cạnh `illustrates` vì "đã có đường khác",
   > làm mất liên kết hình↔khái niệm mà pha B cần.

### A9''. Danh tính — gộp khái niệm trùng *(vé v2-05; đã có mã, chưa vào chuỗi mặc định)*

> Quy tắc: [spec v2, W14–W15](v2-do-thi-va-lo-trinh-neo-van-ban-spec.md). Stage `identity`, sau stage `teaching`.

- **Ứng viên** chỉ từ tín hiệu hẹp: chung tên hoặc alias, khác nhau đúng một tiền tố chung chung (`Hệ véc tơ …`),
  hoặc cùng câu neo. "Tên này chứa tên kia" **không** là ứng viên (`Ma trận` / `Ma trận nghịch đảo`).
- **Phán** mỗi cặp một lời gọi trên hai câu neo: `same` / `different` / `sense_split`. Tín hiệu chỉ là lý do đưa ra
  xét: một câu thường định nghĩa nhiều khái niệm khác nhau cùng lúc.
- **Gộp** chỉ nhóm mà **mọi cặp** đều `same` (a≈b và b≈c không đủ để gộp a với c); nhóm thiếu phán là nhóm mở và
  tính vào Q2. Đại diện là khái niệm được dạy sớm nhất. Khái niệm bị gộp rời `nodes` sang `merged_nodes`
  (`merged_into`); canonical và provenance không đổi.
- **Sau gộp gỡ chu trình lại** bằng đúng hàm gỡ của A9 (thuần, không gọi mô hình); cạnh bị gỡ ghi
  `identity_removed_edges`. A10 nhận stage `identity` như stage `teaching`.
- **Bộ chấm** áp cùng `identity_map` lên cạnh và đích của bộ vàng; tệp vàng không bị sửa. Cạnh vàng giữa hai khái
  niệm đã gộp thành tự nối, rời phép chấm, và được báo (`identity_dropped_gold_edges`).
- Mọi gộp chạm khái niệm của bộ vàng phải được chủ dự án duyệt (T5) trước khi bật.

### A10. Dãy học neo sách → chia module

> Quyết định kiến trúc: [ADR 0010](adr/0010-lo-trinh-la-day-hoc-chia-module.md). Quy tắc chi tiết:
> [spec v2, W2–W8](v2-do-thi-va-lo-trinh-neo-van-ban-spec.md). A10 chỉ đọc cạnh `requires` (kể cả cạnh co qua node bị
> loại ở A9') giữa node `learnable = true`; A9 phải giao DAG thật. Media chưa được gắn vào module.

- **Dãy học**: sắp topo bằng Kahn, hàng đợi ưu tiên theo vị trí dạy `(chỉ số chunk dạy, vị trí ký tự trong chunk)` —
  luôn lấy khái niệm sẵn sàng đứng sớm nhất trong tài liệu. Mọi cạnh đi trước ra sau; chỗ tài liệu đặt một khái niệm
  trước tiên quyết của nó thì dãy sửa lại.
- **Module**: chia dãy thành đoạn liền mạch ≤ 8 khái niệm bằng quy hoạch động kiểu ngắt dòng; chi phí ưu tiên module
  đầy và cân, không vắt qua mục hoặc chương, không dưới 3 khái niệm. Cấp "mục" và "chương" chọn theo từng tài liệu
  (trung vị số khái niệm mỗi mục ≥ 4); tài liệu phẳng thì chỉ chia theo cỡ.
- **Trong module có thứ tự**; không tuyên bố "học song song". Mỗi khái niệm mang `sequence_index`, `module_id` và
  danh sách tiên quyết trực tiếp.
- Tên module lấy từ tiêu đề mục chiếm nhiều khái niệm nhất; module vắt qua hai mục ghép hai tiêu đề bằng " · ".
- Coffman–Graham (stage song song) giữ ở tầng domain làm biến thể đối chứng, không nằm trong chuỗi sản phẩm.

```json
{
  "sequence": ["cpt_bias", "cpt_variance", "cpt_overfitting", "cpt_regularization_l2"],
  "modules": [
    {
      "module_id": "module_003",
      "index": 2,
      "title": "3.2 Overfitting",
      "node_ids": ["cpt_overfitting", "cpt_regularization_l2"],
      "section_ids": ["sec_3_2"],
      "first_order_index": 42
    }
  ]
}
```

Đánh giá: lỗi thứ tự Q6 = (ngược + thiếu đầu) / |vàng| trên dãy. τ so thứ tự dạy từ nay là **độ bám sách**, không
phải bằng chứng chất lượng, vì dãy dùng chính vị trí dạy để phá hoà.

### A11. Module enrichment (dự kiến, chưa triển khai)

Khi triển khai, sinh offline (không sinh on-the-fly lúc học) từ chunk thuộc module. `media_ids` chỉ dùng được
sau một vé riêng gắn media vào module; artifact A10 hiện không có trường đó.
- `objectives`: 3–5 mục tiêu học tập đo lường được.
- `summary`: tóm tắt 150–300 từ.
- `quiz`: 5–8 câu trắc nghiệm (kèm đáp án + giải thích + `concept_id` mà câu hỏi kiểm tra) + 1–2 câu tự luận ngắn (kèm rubric chấm). Câu hỏi được phép tham chiếu `media_id` của module — *"nhìn Hình 3.4, đường cong nào thể hiện quá khớp?"*; UI render kèm ảnh.
- `estimated_minutes`: ước lượng thời gian học.

Hình và bảng chỉ trở thành nguyên liệu của module sau khi có phép gắn media đã kiểm chứng.

### A12. Gắn module_id ngược về chunk (kế hoạch pha B)

- A10 sinh `chunk_module_map` trong artifact: chunk dạy khái niệm của nhiều module được gán module sớm nhất, kèm
  `all_module_ids`. Chưa đồng bộ sang vector DB; trường chỉ mục hiện tên `stage_id` và chưa có dữ liệu — đổi thành
  `module_id` khi triển khai bước này (ADR 0010).
- Media hiện chưa nhận `module_id`. Pha B phải chặn media chưa được gắn module cho đến khi có luật gắn riêng.
- Từ đây scoped RAG hoạt động được: filter `module_index <= current_module_index` — module có thứ tự toàn phần.
- `module_id` **không** nằm trong bất kỳ khoá băm nào (chunk hay node), nên cập nhật nó là ghi cột thường — **không phải embed lại**. Đây là hệ quả trực tiếp của ADR 0002.

### A13. Human review (tùy chọn nhưng rất nên có)

- Admin xem graph + danh sách module, sửa tay: thêm/xóa edge, đổi tên, chuyển concept giữa module (A10 kiểm lại
  mọi cạnh vẫn đi trước ra sau). Mọi bản sinh ra đều version hóa (`graph_version`) — user đang học version cũ không bị vỡ tiến độ khi admin sửa.

**Bốn việc riêng của hệ kiểu mở, xếp theo độ dễ soát bằng mắt:**

1. **Liên kết media↔khái niệm** — sai kiểu này nhìn phát hiện ngay (hình về cây quyết định gắn vào
   khái niệm hồi quy), nên đưa lên đầu danh sách review.
2. **Mô tả ảnh do mô hình sinh** (`caption_source: generated`) — hiển thị kèm ảnh gốc để người soát
   đối chiếu; đây là chỗ ảo giác thị giác lọt qua tầng kiểm định.
3. **Sổ đăng ký kiểu** — duyệt các kiểu mới LLM nghĩ ra: giữ, gộp vào kiểu đã có, hay bỏ. **Đặt cờ
   `learnable`** cho kiểu rõ ràng không học được (`person`, `citation`, `dataset`).
4. **Kiểu bị nghi là đồng nghĩa của `requires`** (`prerequisite_of`, `depends_on`…) do tầng 3 gắn cờ —
   chỉ người mới được quyết định nâng cấp thành `requires`, vì việc đó thêm cạnh vào DAG lộ trình.

---

## BIẾN THỂ PHA A (thiết kế cuối, khuyến nghị): Extract song song + Agent loop tích hợp

Nguyên tắc phân vùng: **agent hóa đúng chỗ khó** (merge + suy luận tiên quyết — nơi dễ sai và cần ngữ cảnh linh hoạt), **giữ thuật toán cố định ở chỗ rẻ và deterministic** (extract thô, cluster, topo sort, layering). Kiến trúc gồm 3 tầng:

```
TẦNG 1 — EXTRACT (cố định, stateless, SONG SONG toàn bộ)
  A1 Parse -> A2 Chunk -> A3' Embed (như cũ)
  A3 Extract ứng viên: mỗi section 1 lời gọi độc lập, chạy song song,
     dùng model rẻ. Output CÔ ĐỌNG: candidate concepts + edge đề xuất
     kèm evidence — KHÔNG phải văn bản thô.
        |
TẦNG 2a — MERGE THEO CỤM (trục phân vùng: ĐỘ GIỐNG CỦA TÊN)
  Pool toàn bộ ứng viên -> gộp trùng tên khít -> đồ thị đề cử (alias,
  n-gram tên, kNN embedding tên) -> Louvain, trần 9 nhóm -> mỗi CỤM
  1 lời gọi kiểm định, SONG SONG -> vá cặp bị chia hai cụm.
  Nhóm không có cặp nghi trùng: promote thẳng. Sau đó A5 viết mô tả.
  Output: BẢNG NODE CHUẨN (canonical) của cả tài liệu.
        |
TẦNG 2b — SUY LUẬN EDGE (ĐỊNH TUYẾN theo cấu trúc tài liệu:
  có chương/heading rõ -> pass chính theo CHƯƠNG;
  tài liệu phẳng/phi tuyến -> pass chính theo CỤM CHỦ ĐỀ)
  + pass phụ bù điểm mù của pass chính,
  làm việc trên bảng node chuẩn — không tạo node giữa chừng.
        |
TẦNG 3 — VALIDATE TOÀN CỤC + THUẬT TOÁN CỐ ĐỊNH
  Xử lý deferred/flags -> self-review 1 pass -> check cycle toàn cục
  -> A9a quality gate -> A9c transitive reduction
  -> gán cluster cho node mới (incremental — A7 đã chạy sau 2a,
     tái sử dụng) -> A10 layering -> A11 -> A12 (như cũ)
```

**Vì sao tách 2a/2b**: merge và suy luận tiên quyết cần hai trục phân vùng khác nhau. Merge cần gom theo độ giống ngữ nghĩa (mọi lần xuất hiện của cùng khái niệm ở chương 3, 5, 8 phải nằm trong cùng một cụm để một agent nhìn thấy hết); suy luận edge cần gom theo vị trí tài liệu (mạch trình bày và thứ tự chương quyết định chiều edge). Ép cả hai vào một trục "chương" khiến merge liên chương bị dồn về pass hợp nhất cuối, thành điểm nghẽn khi khái niệm lặp lại rộng.

**Bảng ánh xạ nhãn pipeline gốc ↔ vị trí trong biến thể** (các nhãn A3–A9 bị tháo rời và lắp lại, tra bảng này để khỏi lạc):

| Nhãn pipeline gốc | Vị trí trong biến thể |
|---|---|
| A3 extract concepts | Tầng 1 (song song hóa) |
| A4 merge | Tầng 2a — thiết kế merge duy nhất, dùng chung cho cả pipeline cố định |
| A5 description | Lời gọi riêng ngay sau 2a, cùng tầng artifact `canonical` |
| A6 semantic graph | **Riêng**, sau A5 — đồ thị **liên quan** dựng từ mô tả A5. Không dùng chung với đồ thị đề cử của 2a: đồ thị đó đo **đồng nhất** (theo tên), còn embedding mô tả kéo các khái niệm anh em lại gần — sai cho merge, đúng cho chủ đề |
| A7 cluster | Chạy **một lần giữa 2a và 2b** trên bảng node canonical; dùng cho phân vùng/pass phụ của 2b và gom stage ở A10 |
| A8a/A8b suy luận tiên quyết | Tầng 2b (pass chính + pass phụ) |
| A9b remove cycle | Tách đôi: chặn đồng bộ **bên trong** `add_edge` của 2b + check cycle toàn cục ở tầng 3 |
| A9a quality gate, A9c transitive reduction | Tầng 3 (vẫn sau khi có edge — bắt buộc, vì gate đo mật độ edge) |
| A10–A12 | Giữ nguyên, chạy sau tầng 3 |

### Tầng 1 — Extract stateless song song

- Chính là bước A3 cũ, nhưng nhấn mạnh: vì stateless (không cần biết graph), toàn bộ section chạy **song song**, dùng model rẻ.
- Output mỗi section: danh sách **thực thể** ứng viên (tên, `node_type`, description sơ bộ, câu bằng chứng, chunk_ids) + edge đề xuất thô (kèm evidence). Đây là input duy nhất của agent loop — agent không đọc lại văn bản gốc trừ khi chủ động gọi tool.
- **Ứng viên media không do LLM sinh**: code đọc `image_refs`/`table_refs` của chunk và tạo thẳng ứng
  viên `figure`/`table`. Lời gọi mô hình thị giác chỉ dành cho ảnh **không có chú thích** (A3.2).
- **`node_type` để agent tự đặt** — chuỗi tự do, prompt **không** đưa danh sách kiểu để chọn. Chỉ hai
  tên dành riêng `figure`/`table` là do code giữ, agent không được dùng.
- **Tên cạnh cũng để agent tự đặt, trừ một ràng buộc phải nói ngay từ đây**: quan hệ tiên quyết
  ("muốn hiểu A phải biết B trước") **bắt buộc đặt tên là `requires`** — không `prerequisite_of`,
  không `depends_on`. Mọi quan hệ khác thì tuỳ agent.

  > Ràng buộc này phải có mặt ở **Tầng 1** chứ không chỉ ở 2b: nếu Tầng 1 đề xuất `prerequisite_of`,
  > agent 2b dễ tưởng đó là kiểu hợp lệ và phát lại, executor từ chối, mà agent chỉ có **một lượt
  > retry** — nó có thể bỏ luôn cạnh thay vì đổi tên. Mất một cạnh tiên quyết thật, và không ai biết.
  > Đặt tên đúng ngay từ đầu rẻ hơn sửa ở cuối.

- Gom các section ngắn thành **siêu section** (mục tiêu 1–2k token/đơn vị) để giảm số iteration ở tầng 2.

### Tầng 2a — Merge theo cụm (entity resolution: blocking rẻ, matching kỹ)

Quy trình (chạy trên **pool ứng viên toàn tài liệu**, không phân theo chương). Chi tiết, số đo và lý do từng
bước: [`A4-A5-hop-nhat-thuc-the-spec.md`](./A4-A5-hop-nhat-thuc-the-spec.md).

1. **Lớp tên**: ứng viên trùng tên khít sau chuẩn hoá (casefold, khoảng trắng, vị trí dấu thanh `hoá`/`hóa`) ⇒
   gộp bằng code thành **nhóm tên**. Đây là quyền gộp **duy nhất** của code — không có ngưỡng cosine nào được gộp
   thẳng (ADR 0006).
2. **Dựng đồ thị đề cử**: node = nhóm tên; cạnh = **cặp nghi trùng** từ ba kênh — alias chung (không tính **ký
   hiệu** như `μ`, `x`, `P(A|B)`), n-gram ký tự trên tên, mutual-kNN trên embedding **tên**. Dựng theo láng giềng
   gần nhất, không theo ngưỡng tuyệt đối: với `gemini-embedding-001`, cosine giữa hai thực thể bất kỳ đã là 0,80,
   nên đồ thị ngưỡng ~0,75 nối cả tài liệu thành một cụm. Mục tiêu vẫn là **recall**: cặp trùng lọt khỏi đồ thị
   thì không bao giờ được merge nữa, còn cặp thừa thì bước phán sẽ tách — sai loại hai sửa được, loại một thì không.
3. **Gom cụm**: Louvain có trọng số, seed cố định, trần **9 nhóm** mỗi cụm (quá thì chia lại). Không dùng connected
   components — nó là single-linkage, xích thành cụm chủ đề. (Lưu ý: đây là cluster trên *ứng viên* phục vụ merge —
   khác với A7 là cluster trên *khái niệm* phục vụ lắp stage; A7 vẫn chạy sau như cũ.)
4. **Kiểm định theo cụm**, các cụm chạy **song song**, mỗi cụm một lời gọi, không tool. Mô hình nhận tên, alias,
   ký hiệu, kiểu, `section_path` và câu bằng chứng nguyên văn của từng nhóm — **không** nhận `description_draft`,
   vì A3 hay viết cùng một câu mô tả cho mọi mục trong một danh sách; ứng viên có câu bằng chứng không nhắc tên
   thì code đính kèm toàn văn chunk. Mô hình chia cụm thành node. Giữa các node đã tách, nó ghi quan hệ kiểu mở kèm
   bằng chứng; cha–con là `subtype_of`, còn lại như `component_of`, `uses` (ADR 0007). Phân vân ⇒ `deferred`. Mô hình
   **không** chọn tên, **không** viết mô tả, **không** đề xuất `requires`. Đầu ra tự mâu thuẫn, như gộp hai nhóm rồi
   lại ghi quan hệ giữa chúng, thì phải phán lại.
5. **Vá cặp bị chia**: với cạnh nghi trùng có hai đầu rơi vào hai cụm, lấy đủ mọi nhóm thành viên của hai node đã
   phán để tạo một cụm nhỏ, rồi dùng lại đúng prompt/schema phân hoạch của bước 4. Chỉ gộp khi toàn bộ hai node được
   đặt chung; hoãn ở lượt này là hoãn theo cặp, không tháo lần gộp đúng trước đó. Gộp bắc cầu còn mâu thuẫn với một
   phán quyết đã có ⇒ không gộp thành phần đó, `deferred`.
6. **Nhóm không có cặp nghi trùng nào** (đa số thực thể chỉ xuất hiện một lần): promote thẳng thành node, không
   tốn lời gọi — vẫn qua A5.

Ứng viên cùng một thực thể có thể mang `node_type` khác nhau. Kiểu do **code** quyết: chuẩn hoá tối thiểu chuỗi
kiểu (casefold, khoảng trắng, ánh xạ theo sổ đăng ký đã duyệt) rồi bỏ phiếu đa số; hoà ⇒ kiểu cụ thể hơn
`concept`, rồi kiểu được dùng nhiều hơn trong tài liệu, rồi thứ tự chữ cái. Luật viết thành văn bản và ghi vào
nhật ký, nên không phải "ngầm lấy ứng viên đầu tiên". Gộp kiểu theo nghĩa (`example_of` / `is_example_of`) vẫn là
việc tầng 3. `learnable` được bỏ phiếu lại chỉ trên các ứng viên mang kiểu canonical, hoà mới chọn `true`. Mâu
thuẫn cùng tên nhưng khác kiểu nằm hai phía `learnable` phải được đưa vào hàng review, vì chọn kiểu đồng thời là
chọn khả năng vào lộ trình.

**Tên chuẩn** do code chọn: tên gọi đầy đủ tài liệu dùng nhiều nhất **trong tên các ứng viên** — alias không tranh,
viết tắt chỉ khi không còn tên gọi, ký hiệu không bao giờ; đếm không chồng lấn, luật đầy đủ ở D6 spec A4/A5. **Id node** theo ứng viên neo (ADR 0005). Mọi quyết định
vào **nhật ký gộp** — thành viên, nhãn, lý do, bằng chứng, mô hình, `prompt_hash` — đủ để A13 tách lại mà không
phải trích lại.

7. **Media bỏ qua toàn bộ quy trình trên.** Hai hình giống hệt đã có cùng `media_id` (băm nội dung từ
   B0) ⇒ khử trùng bằng phép so chuỗi, promote thẳng. Không blocking, không cụm, không agent — tất định
   và miễn phí.

Output: **bảng node chuẩn (canonical)** của cả tài liệu, mỗi node đã hợp nhất đủ `chunk_ids` từ mọi nơi nó xuất
hiện; cạnh đề xuất của tầng 1 đã ánh xạ về node (bỏ cạnh tự nối, gộp cạnh trùng); rồi A5 điền mô tả.

> Bước vá theo hai nhóm đơn lẻ trước đây đã bị bỏ: lần chạy đầu cho 3/6 quyết định *cùng* sai. Vá bằng cụm nhỏ đủ
> ngữ cảnh hai node đưa false positive gộp về 0 trên bộ vàng AI hiện tại; xem báo cáo A4/A5.

### Tầng 2b — Suy luận edge (định tuyến theo cấu trúc tài liệu)

> **Thiết kế hiện hành của tầng này nằm ở [`A6-A8-cum-chu-de-mention-map-va-tien-quyet-spec.md`](./A6-A8-cum-chu-de-mention-map-va-tien-quyet-spec.md)** (2026-09-16): pass chính trích mở, pass phụ chỉ kiểm cặp nghi tiên quyết, không tool, chu trình giải ở tầng 3 (ADR 0008). Mục dưới đây giữ làm hồ sơ.

Đơn vị phân vùng **không cố định** — chọn theo cấu trúc tài liệu, quyết định bằng heuristic ngay sau A1 (có heading phân cấp rõ hay không):

**Nhánh 1 — tài liệu có chương/heading rõ → pass chính theo CHƯƠNG.** Mỗi chương một agent loop độc lập chạy song song; heading lộn xộn thì gom section liên tiếp thành partition ~10–20k token. Ưu thế: giữ mạch trình bày, evidence theo section, doc-order prior mạnh. **Pass phụ**: quét theo cụm chủ đề — chạy A7 trên bảng node canonical, chỉ xét các cặp node cùng cụm chưa có đường nối — để vớt edge giữa các khái niệm liên quan nằm xa nhau trong tài liệu.

**Nhánh 2 — tài liệu phẳng/phi tuyến, không chương mục → pass chính theo CỤM CHỦ ĐỀ.** Chạy A7 sớm trên bảng node canonical; mỗi cụm một lời gọi suy luận edge — **stateless hoàn toàn, song song tuyệt đối**, không cần loop tuần tự. Ba điều kiện bắt buộc để agent không suy luận "chay" từ kiến thức nền: (1) bơm kèm evidence chunks của các node trong cụm (node canonical từ 2a đã mang sẵn `chunk_ids`), (2) truyền `first_order_index` của từng node để giữ doc-order prior, (3) không evidence thì không tạo edge. **Pass phụ**: suy luận liên cụm trên boundary concepts (đúng logic A8b) để vớt edge xuyên cụm.

Tài liệu ngắn (< 50 trang): một lời gọi/loop duy nhất, khỏi phân vùng và khỏi pass phụ.

Hai nhánh là ảnh gương của nhau — mỗi pass chính có một điểm mù, và pass phụ của nhánh đó bù đúng điểm mù ấy: theo chương hụt edge cùng chủ đề nằm xa nhau trong tài liệu; theo cụm hụt edge xuyên cụm mà tài liệu dạy tường minh.

**Lưu ý tránh nhầm — cụm ở đây là cụm CHỦ ĐỀ, không phải cụm của 2a**: cụm 2a là cụm *ứng viên nghi trùng* — một họ tên gần nhau, sau kiểm định ra một hoặc nhiều node canonical (bản sao gộp lại, anh em tách ra). Nó gom theo độ giống của **tên**, không theo chủ đề hay vị trí trong tài liệu, nên không dùng làm đơn vị phân vùng cho 2b được.

Agent làm việc trên **bảng node chuẩn đã chốt từ 2a** — không tạo node giữa chừng, chỉ suy luận edge. Bộ tool (mọi kiểm tra cấu trúc nằm trong code của tool, không giao LLM tự giác):

| Tool | Bản chất | Ghi chú |
|---|---|---|
| `search_similar_node(name, desc)` | Embedding search trên bảng node chuẩn — code deterministic | Resolve ứng viên trong section về node canonical |
| `add_edge(from, to, confidence, evidence_chunk_ids)` | Giữ nguyên hợp đồng dữ liệu A8; edge không evidence → từ chối | `check_cycle` chạy **đồng bộ bên trong**: cạnh tạo cycle bị chặn ngay, trả thông tin cycle để agent chọn bỏ cạnh mới hoặc đề xuất thay cạnh cũ confidence thấp hơn |
| `update_description(node, append, evidence)` | Bổ sung mô tả khi section làm rõ thêm khái niệm | Không sửa đè, chỉ bổ sung có evidence |
| `read_source_chunk(chunk_id)` | Đọc văn bản gốc khi tham chiếu ngầm / mơ hồ | Ngân sách tối đa 2 lần/iteration |
| `flag_missing_node(name, evidence)` | Van an toàn: báo khái niệm 2a bỏ sót | Không tự tạo node — đưa vào hàng chờ, xử lý ở self-review |

Mỗi iteration = 1 (siêu) section:

1. Agent nhận: **output cô đọng của section** (từ tầng 1, đã map ứng viên → node canonical) + danh sách edge đã có liên quan đến các node trong section. Phần lặp lại dùng **prompt caching**.
2. Xác minh các edge đề xuất từ tầng 1 và suy luận edge mới giữa các node canonical.
3. Phát ra **một batch thao tác cho cả section** — không tool-call từng quyết định lẻ (~5–10 lần ít lời gọi hơn).
4. Commit **checkpoint** sau mỗi iteration — crash thì resume.

Điều kiện dừng: hết section của chương — bounded tự nhiên, không có rủi ro loop vô hạn.

### Giao thức giao việc cho agent (prompt contract)

Cả hai loại agent đều được định vai là **người kiểm định/tích hợp, không phải người sáng tác**: chỉ làm việc trên ứng viên + evidence từ tầng 1, không tự bịa khái niệm hay quan hệ ngoài văn bản.

**Kiểm định cụm (2a)** — mỗi cụm một lời gọi, không tool, output một batch quyết định:

1. Rubric năm nhãn cho mỗi cặp nhóm trong cụm:
   - **cùng** — cùng một thực thể dù khác tên (alias, viết tắt, cách dịch, dạng ký hiệu khác nhau) ⇒ chung node;
   - **cha–con** — rộng vs hẹp (vd "Regularization" vs "L2 Regularization") ⇒ hai node + quan hệ `subtype_of` con →
     cha, kèm bằng chứng;
   - **anh em / liên quan** — đồng cấp hoặc chỉ liên quan (L1 vs L2, Mutex vs Pessimistic Locking) ⇒ hai node. Câu
     trích nêu quan hệ thì kèm quan hệ kiểu mở (`component_of`, `uses`, `statistic_of`…) *(ADR 0007)*;
   - **khác** ⇒ hai node;
   - **không chắc** ⇒ không gộp, `deferred` kèm lý do, chốt ở self-review tầng 3.

   Phân vân thì không gộp. Không đề xuất `requires` — tiên quyết là việc của 2b.
2. Mô hình **không** chọn tên chuẩn, **không** gộp alias, **không** viết mô tả — code lắp node, A5 viết mô tả.
3. Code kiểm, ba lớp (D4 spec A4/A5):
   - **Nhóm:** mọi nhóm xuất hiện đúng một lần.
   - **Nhất quán:** quan hệ nối hai nhóm chung một node (R1), hoặc quan hệ đồng nhất nối hai node tách riêng (R2), là
     mâu thuẫn.

     Hai lớp trên sai thì thử lại một lần kèm lỗi; vẫn sai thì cả cụm `deferred`.
   - **Từng quan hệ:** hai đầu là hai node khác nhau, bằng chứng thuộc một trong hai, có lý do, kiểu hợp lệ (không
     `requires`, không kiểu media). Sai thì chỉ loại quan hệ đó (`relation_rejected`).
   - **Sau khi ánh xạ cạnh A3:** quan hệ trùng bộ ba với cạnh A3 thành một cạnh, `origins: ["2a", "a3"]`. Riêng
     `subtype_of` trùng cặp với một cạnh A3 mang nghĩa khác "là một loại" vẫn được giữ, và được ghi
     `subtype_conflicts_a3` (F75, luật ở D7 spec A4/A5).

Ví dụ một cụm: `Overfitting` (g_07), `Quá khớp` (g_12), `L2 Regularization` (g_09), `Regularization` (g_15),
`Weight decay` (g_20 — tài liệu chỉ nhắc một lần, không đủ bằng chứng):

```json
{
  "nodes": [
    {"groups": ["g_07", "g_12"], "reason": "Quá khớp là cách dịch của Overfitting"},
    {"groups": ["g_09"], "reason": "…"},
    {"groups": ["g_15"], "reason": "…"}
  ],
  "relations": [
    {"source": "g_09", "target": "g_15", "edge_type": "subtype_of", "chunk_ids": ["c_0042"],
     "reason": "L2 Regularization là một dạng Regularization"},
    {"source": "g_15", "target": "g_07", "edge_type": "prevents", "chunk_ids": ["c_0043"],
     "reason": "Regularization được dùng để tránh overfitting"}
  ],
  "deferred": [{"group_id": "g_20", "reason": "chỉ được nhắc tên, không có câu nào nói nó là gì"}]
}
```

**Agent suy luận edge (2b)** — quy trình bắt buộc mỗi iteration:

1. Edge đề xuất từ tầng 1 phải được **xác minh lại**, không copy nguyên — extractor tầng 1 không có bối cảnh graph. Quan hệ kiểu mở của 2a, kể cả `subtype_of`, cũng chỉ là đề xuất: precision `subtype_of` đo trên bộ vàng là 0,658, và các quan hệ khác đúng khoảng 70% trên mẫu (D7 spec A4/A5). Cạnh có `origins` gồm cả `2a` lẫn `a3` là đề xuất được hai nguồn độc lập cùng nêu. Chỉ tạo edge tiên quyết **trực tiếp**; edge suy diễn xa để transitive reduction lo.
2. Rubric confidence: **0.9+** khi văn bản nói rõ ("để hiểu X cần nắm Y") hoặc Y xuất hiện trong **câu định nghĩa nguyên văn** của X — câu bằng chứng hoặc chunk định nghĩa, **không** phải mô tả A5: mô tả do mô hình viết có thể mang kiến thức nền của mô hình, mà đây là luật cho confidence cao nhất; **0.7** khi suy luận mạnh từ mạch trình bày; **0.5** khi suy đoán; **dưới 0.5 thì không tạo edge**. Edge ngược thứ tự tài liệu chỉ được tạo khi có evidence tường minh, và trừ 0.1 confidence.
3. Gặp khái niệm không có trong bảng node chuẩn → `flag_missing_node`, không tự tạo.
4. Kết thúc iteration bằng **một batch JSON duy nhất**:

```json
{
  "ops": [
    {"op": "add_edge", "from": "cpt_l2_regularization", "to": "cpt_overfitting",
     "confidence": 0.9, "evidence_chunk_ids": ["c_0042"],
     "rationale": "L2 được giới thiệu như giải pháp cho overfitting"},
    {"op": "update_description", "node": "cpt_overfitting", "append": "...",
     "evidence": "c_0043"}
  ],
  "flags": [{"missing_node": "Bias-Variance Tradeoff", "evidence": "c_0044"}]
}
```

**Phía executor (code), chung cho cả hai:** thực thi ops theo thứ tự; mỗi op lỗi trả lỗi cụ thể theo op;
agent được **1 lượt retry duy nhất** để sửa các op lỗi, op đã thành công không chạy lại.

Danh sách kiểm tra của executor — **đây là nơi hệ kiểu mở được giữ an toàn**, không phải trong prompt:

| Kiểm tra | Hành động khi vi phạm |
|---|---|
| Chu trình trong `requires` | Từ chối op |
| Evidence chunk không tồn tại | Từ chối op |
| Node id sai | Từ chối op |
| **`requires` có đầu `learnable = false`** | **Từ chối op** (I-G1) |
| **Tên cạnh đồng nghĩa `requires`** (`prerequisite_of`, `depends_on`, `needs`…) | **Từ chối op**, báo agent dùng `requires` hoặc đặt tên khác hẳn |
| Kiểu node/cạnh mới chưa có trong sổ đăng ký | **Chấp nhận**, ghi vào sổ, tăng bộ đếm |

Hàng cuối là điểm mấu chốt: kiểu mới **không phải lỗi**. Agent cứ đặt tên quan hệ nó thấy; sổ đăng ký
ghi lại, tầng 3 chuẩn hoá, A13 duyệt.

`search_similar_node` nhận thêm tham số lọc `node_type` để agent tra trong đúng nhóm khi cần, nhưng
**mặc định tìm mọi kiểu** — thu hẹp là lựa chọn của agent, không phải mặc định của tool.

### Tầng 3 — Validate toàn cục

1. **Xử lý tồn đọng**: chốt các cụm `deferred` từ 2a (giờ đã có toàn cảnh graph) và các `flag_missing_node` từ 2b (tạo node bổ sung nếu có evidence, hoặc bỏ).
2. **Self-review 1 pass** trên graph tổng: duplicate sót, edge thiếu evidence, mô tả mâu thuẫn, **media
   mồ côi** (bất biến I-G2).
3. **Chuẩn hoá sổ đăng ký kiểu** — bước bắt buộc của hệ kiểu mở:
   - Gom tên kiểu theo độ giống (chuỗi + embedding): `example_of` / `is_example_of` / `vd_cho` về một kiểu.
   - Kiểu dùng **≥ N lần** ⇒ ghi là kiểu đã biết; kiểu xuất hiện **một lần** ⇒ gắn cờ cho A13 duyệt.
   - Kiểu nghi là đồng nghĩa `requires` ⇒ **gắn cờ, không tự động quy đổi** — chỉ người mới được nâng
     cấp, vì việc đó thêm cạnh vào DAG lộ trình.
   - Ghi sổ đăng ký vào manifest đồ thị (bất biến I-G3).
4. **Check cycle toàn cục** chạy lại một lần **chỉ trên cạnh `requires`**: trong chương cycle đã bị chặn tại `add_edge`, nhưng edge từ các chương khác nhau ghép lại có thể tạo cycle xuyên chương.
5. Tiếp tục A9a → A9c → **tái sử dụng kết quả A7 đã chạy sau 2a** (cluster dựa trên ngữ nghĩa node, không phụ thuộc edge, nên việc tầng 3 cắt/chỉnh edge không làm cluster lệch; chỉ gán incremental các node mới thêm ở bước 1 vào cluster gần nhất theo embedding) → A10–A12 như pipeline gốc.

### Hiệu năng và UX cho tài liệu dài

- Ước lượng: giáo trình 500 trang, chạy tuần tự thuần ~30–60 phút; với tầng 1 song song + tầng 2 song song theo chương → **~10–15 phút**, chi phí token gần như không đổi.
- Đây là pha offline chạy 1 lần khi upload → xử lý async + progress bar theo chương.
- **Mở dần giai đoạn**: vì edge tiên quyết hầu như trỏ ngược về trước, các stage đầu ổn định ngay khi các chương đầu hoàn tất — cho user bắt đầu học stage 1 (đánh dấu `graph_version: partial`) trong khi các chương sau còn xử lý, rồi cập nhật lên bản đầy đủ.

### Kiểm soát tính tái lập (điểm yếu lớn nhất của agent loop)

- `temperature = 0` cho mọi lời gọi trong loop.
- Log **mọi tool call thành event log** → replay toàn bộ quá trình xây graph để debug và so sánh giữa 2 lần chạy.
- Kiểm tra cấu trúc (cycle, trùng tên, evidence hợp lệ) nằm trong code của tool.

### Khi nào dùng biến thể nào

| Tình huống | Lựa chọn |
|---|---|
| Giáo trình tuyến tính chuẩn, chương mục rõ | Pipeline cố định (rẻ hơn, đủ tốt) |
| Tài liệu tham chiếu chéo dày, phi tuyến, phụ lục lộn xộn | Biến thể này (extract song song + agent tích hợp) |
| Tài liệu dài (> 200 trang) | Biến thể này, bắt buộc bật song song theo chương |
| Đề tài nghiên cứu | Làm cả hai, benchmark chất lượng graph + chi phí + độ tái lập — bản thân phép so sánh là một đóng góp thực nghiệm |

---

## PHA B — LEARNING LOOP

### B1. State và UI

- Bảng tiến độ:

```json
{
  "user_id": "u_9",
  "doc_id": "doc_001",
  "current_module": "module_003",
  "concept_mastery": {"cpt_overfitting": 0.85, "cpt_regularization_l2": 0.4},
  "quiz_history": [{"module_id": "module_002", "score": 0.8, "ts": "..."}]
}
```

- UI graph: node **học được** vẽ theo trạng thái (khóa / đang học / hoàn thành); module là một buổi học có thứ tự bên
  trong; click node mở panel học, kèm "vì sao đứng ở đây" (tiên quyết trực tiếp). Render bằng React Flow hoặc Cytoscape.js.
- **Node media vẽ khác**: `figure` hiện thumbnail, `table` hiện biểu tượng bảng — không tô màu trạng
  thái vì chúng không phải thứ để "hoàn thành". Cạnh `illustrates`/`tabulates` vẽ nét đứt để phân biệt
  với `requires` nét liền.
- **Kiểu do LLM nghĩ ra phải render được mà không cần sửa code**: node kiểu lạ dùng hình dạng mặc định
  kèm nhãn tên kiểu; cạnh kiểu lạ dùng nét mảnh kèm nhãn. Hệ kiểu mở mà UI phải cập nhật theo từng kiểu
  mới thì mở cũng bằng không.
- Bật/tắt lớp hiển thị theo kiểu cạnh — người học muốn nhìn lộ trình thuần thì tắt hết trừ `requires`.
- Cho phép xem trước module sau ở chế độ read-only (đừng khóa cứng gây ức chế), và **test-out**: làm quiz để nhảy cóc module.
- **Lộ trình tới mục tiêu** (spec v2, W9): người học chọn khái niệm đích, nhận đúng đích và tổ tiên của nó theo thứ tự
  dãy học, chia module.

### B2. Tutor agent (scoped RAG)

Luồng xử lý mỗi câu hỏi:
1. Graph lookup: câu hỏi chạm concept nào (match tên/alias + embedding trên description).
2. Xác định phạm vi: concept thuộc module ≤ hiện tại → retrieval bình thường. Thuộc module tương lai → trả lời khái quát 1–2 câu + "phần này sẽ học kỹ ở module N" (graph cho biết chính xác N).
3. Vector search top-k với filter `module_index <= current_module_index`, ưu tiên chunk thuộc module hiện tại.
4. Trả lời kèm trích dẫn trang/section (metadata chunk có sẵn) để user tra lại tài liệu gốc.
5. **Kèm hình khi hình nói tốt hơn chữ**: nếu khái niệm được hỏi có node `figure`/`table` nối tới trong
   phạm vi module cho phép, agent chèn nó vào câu trả lời. Đây là lý do tồn tại của node media.

Tools của agent:

| Tool | Việc |
|---|---|
| `search_module_content(query, module_scope)` | Vector search có lọc phạm vi |
| `lookup_concept(name)` | Resolve tên/alias về node |
| `get_module_info(module_id)` | Mục tiêu, tóm tắt, danh sách node theo thứ tự của module |
| **`get_media_for_concept(concept_id, module_scope)`** | **Trả hình/bảng nối tới khái niệm, kèm mô tả và `caption_source`. Lọc theo `module_index <= current`** |
| **`traverse(node_id, edge_type, direction)`** | **Đi theo bất kỳ loại cạnh nào — `example_of`, `contrasts_with`, kiểu LLM tự đặt. Đây là chỗ hệ kiểu mở trả lương** |

Hai tool cuối là điều kiện cần để đồ thị giàu kiểu có ý nghĩa: **không có chúng thì đồ thị có node hình
và cạnh nhiều kiểu mà agent không lấy ra được** — công sức A3 đổ sông.

`traverse` nhận tên kiểu cạnh dạng chuỗi tự do và đọc **sổ đăng ký kiểu** để biết kiểu nào tồn tại,
nên kiểu mới dùng được ngay không cần sửa code tool.

### B3. Assessment agent

- Quiz cuối module lấy từ bộ đã sinh ở A11 (xáo trộn, chọn ngẫu nhiên). Tự luận chấm bằng LLM theo rubric.
- Điểm được quy về **mastery theo từng concept** (mỗi câu hỏi đã gắn `concept_id`). Đạt ngưỡng tổng (vd ≥ 70%) và không concept nào < 40% → unlock module kế.
- Rớt concept cụ thể → điều hướng ôn đúng concept đó (tutor agent sinh giải thích bổ sung từ evidence chunks), không bắt học lại cả module.

### B4. Adaptive loop

- Cập nhật `concept_mastery` sau mỗi quiz và cả từ tín hiệu hội thoại (user hỏi lại nhiều lần về 1 concept → mastery giảm).
- Tùy chọn nâng cao: spaced repetition — chèn câu ôn tập concept cũ vào quiz của module mới.

---

## Công nghệ đề xuất (mặc định đơn giản)

| Thành phần | Lựa chọn mặc định | Nâng cấp khi cần |
|---|---|---|
| Parse | Docling / Unstructured | + OCR cho scan |
| Vector DB | Postgres + pgvector | Qdrant/Weaviate |
| Graph store + thuật toán | Postgres (bảng `nodes` có cột `node_type` + `learnable`, bảng `edges` có cột `edge_type`, bảng `type_registry`) + NetworkX | Neo4j (đồ thị > chục nghìn node) |
| Kho ảnh | **Đã có từ B0** — lưu theo băm nội dung; chỉ cần trỏ tới, không dựng mới | CDN nếu cần phục vụ nhiều người |
| Mô hình thị giác | Chỉ dùng cho ảnh **không có chú thích**, kèm tầng kiểm định chéo | |
| Orchestration pha A | Script tuần tự + checkpoint JSON | LangGraph / Temporal |
| Agent pha B | 1 tutor + 1 assessment, orchestrator giữ state | |
| Frontend graph | React Flow | Cytoscape.js |

## Thứ tự triển khai MVP → đầy đủ

1. **MVP (chạy được end-to-end)**: A1, A2, A3', A3 (khái niệm, hai lượt), A4 (lớp tên + đồ thị đề cử + kiểm định theo cụm — embedding chỉ đề cử, không tự gộp: ADR 0006), A5, A8a, A9b, A10 (layering thuần), B1 tối giản, B2.
   **Kèm ngay từ MVP — rẻ và chặn hai lỗi câm**: luật *"A9/A10 chỉ đọc cạnh `requires`"*, cờ `learnable`,
   và executor từ chối `requires` sai kiểu. Không phụ thuộc media node, và cần **kể cả khi** chỉ có
   khái niệm — vì cạnh `relates_to`/`example_of` cũng sẽ làm tử số phồng nếu ai đó đếm nhầm.
2. **Vòng 2**: A6–A7 (cluster), A8b, A9a + A9c, A11 (quiz), B3.
   **Media node vào đây**: A3.2, cạnh `illustrates`/`tabulates`, media trong A6/A7, gắn media vào stage
   ở A10, `get_media_for_concept` ở B2. Đây là lúc tính năng "agent xuất ảnh cho người học" chạy được.
3. **Vòng 3**: A13 (admin review + duyệt sổ đăng ký kiểu), B4, test-out, version hóa graph.
   **Hệ kiểu mở chín ở đây**: pha chuẩn hoá kiểu ở tầng 3, tool `traverse`, UI render kiểu lạ.

> **Sổ đăng ký kiểu nên có từ MVP** dù lúc đó chỉ chứa vài kiểu — thêm sau nghĩa là phải hồi tố mọi
> node và cạnh đã sinh. Rẻ lúc đầu, đắt lúc sau.

Nguyên tắc chung: đo chất lượng graph bằng mắt người trên 2–3 tài liệu thật **trước khi** đầu tư vào phần adaptive — graph sai thì mọi thứ phía sau sai theo.
