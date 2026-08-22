# B0 — INGESTION CHUNG (bước cố định)

> Spec kỹ thuật cho bước nền của Pha A. B0 là bước **tất định, không agent**: cùng input + cùng config phải cho ra cùng output bit-for-bit.
> Phiên bản spec: `v1`. Trạng thái: draft để hiện thực.

---

## 1. Phạm vi

```
PDF/DOCX  ─▶ [B0.1 Normalize] ─▶ [B0.2 Parse layout-aware] ─▶ document tree
                                                                  │
                                        ┌─────────────────────────┘
                                        ▼
                              [B0.3 Gán parent] ─▶ [B0.4 Chunk] ─▶ sections + chunks
                                                                        │
                                              ┌─────────────────────────┴──────────────┐
                                              ▼                                        ▼
                                     [B0.5 Embed] ─▶ VECTOR DB              (chờ) extract concepts
```

**Trong phạm vi:** chuẩn hoá văn bản, parse layout-aware, dựng cây section, gán `parent_section_id`, cắt chunk, sinh `chunk_id` tất định, embed, persist.

**Ngoài phạm vi:** extract concept (tầng 1), merge cụm (2a), suy luận edge (2b), gán `stage_id` (backfill sau topological layering).

### 1.1 Hai consumer của B0

| Consumer | Dùng gì từ B0 | Yêu cầu riêng |
|---|---|---|
| Nhánh embed / RAG online | vector + `parent_section_id` + `order_index` | chunk đủ nhỏ để match chính xác |
| Nhánh extract concepts (tầng 1) | window gom theo `parent_section_id`, `chunk_id` làm evidence | ranh giới cấu trúc sạch, evidence trỏ đúng block |
| Bước M (mention map) | `chunk_id` làm cột ma trận node×chunk | `chunk_id` ổn định qua re-ingest |
| Tầng 2b (định tuyến edge) | `section_path`, `heading_level`, `first_order_index` | reading order toàn cục chính xác |

**Nguyên tắc chốt: STRUCTURAL-FIRST, MỘT BIỂU DIỄN.**
Chỉ tồn tại **một** tập chunk được embed (leaf block). Cây phân cấp **không** bị cắt thành chunk lớn và **không** được embed — nó sống trong bảng `sections`. Mọi granularity lớn hơn (mục, chương) được **ráp lúc chạy** từ `parent_section_id` + `order_index`.

---

## 2. B0.1 — Chuẩn hoá văn bản

Chạy **một lần** trên full text, **trước khi** cắt `char_span` và trước khi embed. Mọi bước xuôi dòng dùng chung đúng chuỗi normalized này.

| Phép | Bắt buộc | Lý do |
|---|---|---|
| Unicode **NFC** | ✅ | Tiếng Việt có cả dạng precomposed và tổ hợp dấu. Bước M dùng Aho-Corasick exact match — không NFC thì trượt mention chỉ khác dạng tổ hợp. |
| Chuẩn hoá whitespace (`\r\n`→`\n`, gộp space thừa, trim cuối dòng) | ✅ | Ổn định `chunk_id` hash |
| Gỡ soft hyphen (`\u00AD`), nối từ bị ngắt cuối dòng | ✅ | PDF hay chèn; phá vỡ exact match |
| Chuẩn hoá dấu nháy/gạch ngang (`"` `'` `–` `—`) | ✅ | Giảm nhiễu hash và match |
| Bỏ header/footer/số trang lặp | ✅ | Nhiễu embedding, sai `order_index` |
| Lowercase / bỏ dấu | ❌ **Không** | Huỷ ngữ nghĩa tiếng Việt; nếu cần thì làm ở **index phụ** của Aho-Corasick, không đụng text gốc |

> **Bất biến B0.1:** `char_span` của mọi chunk tính trên **normalized text**, không phải raw text.

---

## 3. B0.2 — Parse layout-aware

Output **không phải** markdown phẳng, mà là **document tree**:

```
DocumentNode {
  node_id, node_type,        # title | section_header | paragraph | table | figure
                             # | caption | list | formula | code | footnote
  level,                     # với heading: 1..6; với block thường: null
  text,
  page,
  bbox,                      # (x0, y0, x1, y1)
  reading_order              # số nguyên tăng dần TOÀN CỤC
}
```

### 3.1 Yêu cầu bắt buộc với parser

1. **Reading order đúng** — đặc biệt PDF đa cột. Đây là nguồn của `order_index` → `first_order_index` → tín hiệu của tầng 2b. Sai reading order làm hỏng cả pass theo chương lẫn pass theo cụm chủ đề.
2. **Phát hiện heading + level** — nguồn của `heading_level`, `section_path` và classifier "có cấu trúc / phẳng".
3. **Giữ cấu trúc bảng** — không flatten bảng thành dòng text rời.
4. **Bóc header/footer/số trang** ra khỏi luồng nội dung.

### 3.2 Lựa chọn adapter

| Adapter | Khi dùng |
|---|---|
| **Docling** (mặc định) | PDF/DOCX/PPTX số hoá; layout + table + reading order tốt, self-host, Apache-2.0 |
| **OCR-first** (MinerU / dots.ocr / PaddleOCR-VN) → Docling | PDF scan, không có text layer |
| **Unstructured** | Corpus sạch, ưu tiên throughput/chi phí |

Cả ba nằm sau **cùng một port** `DocumentParser`; đổi adapter không đụng use case.

---

## 4. B0.3 — Gán `parent_section_id` (phần dễ sai nhất)

### 4.1 Luật

> `parent_section_id` của một block = **heading đang mở gần nhất** bao quanh nó.

Hệ quả trực tiếp: **content trực tiếp của một section = các block từ ngay sau heading đó cho tới ngay trước heading con đầu tiên** (hoặc hết section nếu không có con). *Không* phải toàn bộ subtree.

### 4.2 Thuật toán (heading stack)

```python
ROOT = Section(id="s_root", level=0, title="<document>", parent=None)

def assign_parents(nodes):                 # nodes: đã sắp theo reading_order
    stack    = [ROOT]                      # sentinel, luôn ở đáy
    sections = [ROOT]
    chunks   = []
    counter  = 0

    for n in nodes:
        if n.node_type == "section_header":
            level = normalize_level(n.level, stack)     # xử lý nhảy cấp, §4.3

            # pop mọi heading có level >= level hiện tại
            while len(stack) > 1 and stack[-1].level >= level:
                stack.pop()

            sec = Section(
                id            = det_section_id(doc_id, n.reading_order, n.text),
                title         = n.text,
                level         = level,
                parent        = stack[-1].id,
                section_path  = stack[-1].section_path + [n.text],
                order_index   = counter,
            )
            sections.append(sec)
            stack.append(sec)               # PUSH sau khi pop
        else:
            chunks.append(Chunk(
                parent_section_id = stack[-1].id,        # ← đỉnh stack
                order_index       = counter,
                block_type        = n.node_type,
                ...
            ))
        counter += 1

    return sections, chunks
```

**Điểm bắt lỗi khi review code:** `stack[-1]` sau khi pop-rồi-push mới là parent. Nếu push trước khi pop, hoặc lấy `stack[0]`, mọi block sẽ trỏ về chương gốc → window phình thành cả chương → mất sạch cấu trúc.

### 4.3 Xử lý heading nhảy cấp

PDF parse thực tế hay cho level nhảy (level 1 → level 3, bỏ qua 2). Luật pop `level >= level_mới` vẫn chạy đúng và **không** cần chèn section ảo: heading level 3 sẽ nằm dưới heading level 1 đang mở. Ghi `heading_level_raw` bên cạnh `heading_level` để trace.

Từ `section-id-v3`, cấp hiệu lực được suy từ đánh số trong tiêu đề; cấp parser vẫn lưu ở
`heading_level_raw`. Nếu cây parse chứng minh heading thật sự lồng trong cha nhưng cấp suy ra không sâu hơn,
`normalize_level` kẹp về `stack[-1].level + 1` và thêm một lý do vào `structure_warnings`.

### 4.4 Bảng ca biên

| Tình huống | `parent_section_id` | Thành window extract? |
|---|---|---|
| Block trước heading đầu tiên (lời nói đầu, abstract) | `s_root` | ✅ window `s_root` |
| Block giữa "Chương 2" và "2.1" (preamble chương) | `s_2` | ✅ window `s_2` riêng |
| Block giữa "2.1" và "2.1.1" (preamble mục) | `s_21` | ✅ window `s_21` riêng |
| Block trong 2.1.1 | `s_211` | ✅ window `s_211` |
| Heading "Chương 2" mà ngay dưới đã là "2.1" | — | ❌ không có chunk trỏ về `s_2` → **không sinh window rỗng** |
| Tài liệu không heading | tất cả = `s_root` | ✅ một window lớn → cửa sổ trượt (§8.3) |
| Caption của hình/bảng | heading gần nhất | ✅ nằm trong window, `block_type=caption` |
| Footnote | heading gần nhất, `block_type=footnote` | ✅ (có thể loại khỏi evidence chính) |

### 4.5 Ví dụ đối chiếu

```
Chương 2: Mô hình ngôn ngữ                  s_2   (level 1)
   ¶ "Chương này trình bày…"                c_0001  parent = s_2
   ¶ "Ta bắt đầu từ kiến trúc nền tảng…"     c_0002  parent = s_2
   2.1 Kiến trúc Transformer                s_21  (level 2)
      ¶ "Transformer bỏ hồi quy…"            c_0003  parent = s_21
      ¶ "Gồm encoder và decoder…"            c_0004  parent = s_21
      2.1.1 Cơ chế Attention                s_211 (level 3)
         ¶ "Attention gán trọng số…"         c_0005  parent = s_211
         ¶ "Với scaled dot-product…"         c_0006  parent = s_211
         formula                             c_0007  parent = s_211
         table  "Ký hiệu Q,K,V,dₖ"           c_0008  parent = s_211
      2.1.2 Multi-head Attention            s_212 (level 3)
         ¶ "Multi-head chạy h phép…"         c_0009  parent = s_212
```

→ 4 window: `s_2`{c_0001,c_0002} · `s_21`{c_0003,c_0004} · `s_211`{c_0005..c_0008} · `s_212`{c_0009}.

Window `s_2` **chỉ** gồm 2 đoạn preamble, **không** gồm c_0003 hay c_0005.

---

## 5. B0.4 — Chunking

### 5.1 Luật cắt

1. **Đơn vị gốc = 1 leaf block** (paragraph / table / formula / list item group / caption / code).
2. Ưu tiên ranh giới câu và không bao giờ gộp hai block khác `parent_section_id`; chỉ cắt cưỡng bức khi cần giữ trần cứng tuyệt đối.
3. **Block văn xuôi quá dài** (> `MAX_TOKENS`, mặc định 512): cắt theo ranh giới câu, các mảnh **giữ nguyên** `parent_section_id`, đánh `split_index = 0,1,2…`, overlap 1 câu.
4. **Block quá ngắn** (< `MIN_TOKENS`, mặc định 32, ví dụ caption một dòng): **giữ nguyên, không merge**. Merge sẽ phá tính "một block = một evidence".
5. **Bảng**: text-hoá dạng markdown, dùng trần riêng 2048 token; bảng vượt trần cắt theo hàng và các mảnh giữ cùng `table_id`.
6. Sau mọi luật theo loại, mảnh vượt `HARD_CAP_TOKENS` (mặc định 6000) bị cắt cưỡng bức ở ranh giới cụm ký tự.

### 5.2 `chunk_id` tất định (bắt buộc)

```python
chunk_id = "c_" + blake2b(
    f"{doc_id}|{order_index}|{char_start}:{char_end}|{normalized_text}",
    digest_size=12
).hexdigest()
```

**Vì sao không dùng UUID ngẫu nhiên:** `chunk_id` là hạt giống provenance của bước M và là evidence reference xuyên suốt Pha A. Re-ingest với UUID ngẫu nhiên sẽ phá mọi tham chiếu đã lưu. Với hash tất định, block không đổi nội dung ⇒ giữ nguyên id ⇒ **re-ingestion idempotent**, evidence không gãy qua các version.

`section_id` cũng tất định theo cùng nguyên tắc.

---

## 6. Schema dữ liệu

### 6.1 `sections` (không có vector)

| Cột | Kiểu | Ghi chú |
|---|---|---|
| `section_id` | text PK | tất định |
| `doc_id` | text | |
| `title` | text | |
| `level` | int | 0 = `s_root` |
| `heading_level_raw` | int null | level parser trả về, để trace |
| `parent_section_id` | text FK → sections | null chỉ với `s_root` |
| `section_path` | text[] | `["Chương 2","2.1","2.1.1"]` |
| `order_index` | int | vị trí heading trong reading order |
| `has_direct_content` | bool | có ≥1 chunk trỏ về → là window extract |

### 6.2 `chunks` (có vector)

| Cột | Kiểu | Dùng ở đâu |
|---|---|---|
| `chunk_id` | text PK | evidence, cột ma trận bước M |
| `doc_id` | text | |
| `order_index` | int | → `first_order_index` (tầng 2b) |
| `split_index` | int | ≠0 nếu block bị cắt |
| `page` | int | trích dẫn cho user |
| `char_span` | int4range | trên **normalized** text |
| `parent_section_id` | text FK | **gom window extract + small-to-big** |
| `section_path` | text[] | denormalize để filter nhanh |
| `heading_level` | int | classifier "có cấu trúc / phẳng" |
| `block_type` | enum | lọc evidence, hint cho extractor |
| `text` | text | normalized |
| `embedding` | vector(d) | |
| `embedding_model_id` | text | re-embed chọn lọc |
| `token_count` | int | budget context window |

### 6.3 `chunk_stage` — many-to-many, **backfill sau**

```sql
CREATE TABLE chunk_stage (
  chunk_id text REFERENCES chunks,
  stage_id text REFERENCES stages,
  PRIMARY KEY (chunk_id, stage_id)
);
```

> Một chunk có thể chống lưng cho nhiều node thuộc **nhiều stage khác nhau** → quan hệ **không** phải 1-1. Cột `stage_id` nullable trên `chunks` chỉ là tiện tra cứu; **nguồn chân lý là bảng liên kết này**.
>
> Backfill sau topological layering, lan theo: `node → evidence_chunks → stage(node)`.
> Tutor agent online filter RAG theo stage qua chính bảng này.

---

## 7. B0.5 — Embedding

| Hạng mục | Quyết định |
|---|---|
| Model mặc định (VI) | dòng `dangvantuan/vietnamese-document-embedding` (gte-multilingual, long-context ~8k) |
| Phương án đa ngữ | `jina-embeddings-v4`, dòng `Qwen3-Embedding` — cần benchmark trên corpus thật |
| Word segmentation | **Kiểm tra model card**: một số model VI kỳ vọng input đã segment (VnCoreNLP / underthesea). Segment sai ⇒ tụt recall. |
| Matryoshka | ưu tiên, để cắt chiều mà không phải re-embed |
| Input embed | `text` (đã NFC) + tuỳ chọn prefix `section_path` để tăng ngữ cảnh |
| Version | ghi `embedding_model_id`; đổi model = tăng version artifact `embeddings`, **không** đụng `chunks`/`sections` |

Batch theo `doc_id`, retry idempotent theo `chunk_id`.

---

## 8. Hợp đồng với các bước xuôi dòng

### 8.1 Window extract (tầng 1) — gom theo `parent_section_id`

```python
for owner_id, window in group_by(chunks, key="parent_section_id"):
    window = sorted(window, key="order_index")
    candidates = extractor_llm(window)     # đọc cả mục, ghi evidence theo leaf
```

**Bất biến:** phân hoạch **total + disjoint** — mỗi chunk thuộc **đúng một** window. Không chunk nào bị extract hai lần, không chunk nào rơi.

Output tầng 1 ghi evidence ở mức **leaf**:

| concept candidate | evidence_chunk_ids | first_order_index |
|---|---|---|
| Scaled dot-product attention | `[c_0006, c_0007]` | 6 |
| Query/Key/Value | `[c_0007, c_0008]` | 7 |

`first_order_index = min(order_index)` trên tập evidence → vị trí xuất hiện lần đầu **chính xác tới block**, không bị làm tròn về đầu mục.

> **Over-fragment là chấp nhận được by design.** Concept giới thiệu ở preamble chương rồi khai triển ở 2.1.1 sẽ sinh candidate rời ở 2 window. Tầng 2a (pool toàn tài liệu → similarity graph ngưỡng thấp recall-first → Leiden → agent kiểm định cụm) hợp nhất. Cố gộp window to để "tránh fragment" sẽ dồn nhiều concept vào một candidate — tệ hơn.

### 8.2 Small-to-big (RAG online)

```python
hits = vector_search(embed(query), top_k=8)      # search trên LEAF
best = hits[0]

context = (chunks
           .where(parent_section_id == best.parent_section_id)
           .order_by(order_index))               # ráp "big" tại chỗ

# leo thêm 1 cấp nếu cần bối cảnh rộng:
# context = chunks_under(descendants_of(sections[best.parent_section_id].parent))
```

Match chính xác ở hạt nhỏ, context đưa vào LLM là cả mục. **Không tốn thêm vector nào.**

### 8.3 Tài liệu phẳng / không heading

Mọi chunk có `parent_section_id = s_root` → một window khổng lồ. Xử bằng **cửa sổ trượt** `WINDOW_TOKENS` (mặc định 2000, overlap 200) *chỉ tại lớp đọc của tầng 1*; `parent_section_id` trong DB **không đổi**. Cùng một luật gán parent, không có nhánh code riêng.

---

## 9. Artifact & versioning

Ba artifact **tách rời**, version độc lập:

| Artifact | Nội dung | Khi nào tăng version |
|---|---|---|
| `parse_tree/{doc_id}/v{n}` | document tree thô | đổi parser/adapter/config OCR |
| `chunks/{doc_id}/v{n}` | `sections` + `chunks` (chưa vector) | đổi luật chunk/normalize |
| `embeddings/{doc_id}/v{n}` | vector + `embedding_model_id` | đổi model/chiều embedding |

Nhờ tách 3 tầng: **re-embed không cần re-parse**; **re-chunk không cần re-parse**; nhờ `chunk_id` tất định, re-chunk giữ nguyên id cho block không đổi ⇒ evidence của các bước Pha A trước đó không gãy.

---

## 10. Kiến trúc (clean architecture)

```
application/use_cases/ingest_document.py
    IngestDocument  ─ điều phối, tất định, KHÔNG agent

domain/ports/
    DocumentParser   : bytes            -> DocumentTree
    Chunker          : DocumentTree     -> (Section[], Chunk[])
    Embedder         : str[]            -> Vector[]
    ChunkRepository  : upsert/get theo doc_id, version
    VectorStore      : upsert / search(filter)

infrastructure/adapters/
    docling_parser.py · unstructured_parser.py · ocr_parser.py
    structural_chunker.py
    vi_embedder.py · jina_embedder.py
    pgvector_store.py · qdrant_store.py
```

**Quy tắc phân tầng:** `small-to-big` và `window assembly` là **logic ứng dụng**, nằm ở use case — **không** lọt xuống adapter VectorStore. Adapter chỉ biết search vector + filter scalar.

**Vector store:** ưu tiên **pgvector** giai đoạn đầu (một nguồn chân lý cho vector + metadata + `chunk_stage`, transaction, filter theo section/stage dễ). Tách sang Qdrant/Milvus khi corpus đủ lớn — port đã có sẵn.

---

## 11. Bất biến & test chấp nhận

Mọi mục dưới đây nên có unit test:

| # | Bất biến | Test |
|---|---|---|
| I1 | Mỗi chunk thuộc **đúng một** window | `sum(len(w) for w in windows) == len(chunks)` và các set rời nhau |
| I2 | `parent_section_id` = heading gần nhất | fixture §4.5: `c_0001.parent == s_2`, `c_0003.parent == s_21`, `c_0005.parent == s_211` |
| I3 | Window của section cha **không** chứa chunk của section con | `window(s_2) == {c_0001, c_0002}` |
| I4 | Section không có content trực tiếp ⇒ không sinh window | không có window rỗng nào |
| I5 | Idempotent | ingest 2 lần cùng file ⇒ tập `chunk_id` **giống hệt** |
| I6 | `order_index` tăng đơn điệu theo reading order | `sorted(chunks, key=order_index)` khớp thứ tự đọc thủ công của fixture |
| I7 | Không cắt ngang câu | mọi chunk kết thúc ở ranh giới câu hoặc hết block |
| I8 | NFC | `unicodedata.is_normalized("NFC", chunk.text)` với mọi chunk |
| I9 | `char_span` khớp | `normalized_full_text[span] == chunk.text` |
| I10 | Tài liệu không heading vẫn hợp lệ | mọi chunk có `parent == s_root`, 1 window |
| I11 | Chèn nội dung không làm đổi ID của phần không đổi | so `section_id`, `parent_section_id`, `chunk_id` trước/sau khi chèn ở section khác |
| I12 | Đổi cấu hình chỉ đổi nhóm thật sự đổi ranh giới | block/nhóm không bị cắt hoặc gộp lại giữ ID; phần bị tác động có tập ID khác |
| I13 | Heading thô cùng cấp nhưng có đánh số vẫn dựng được cây ba cấp | `1` → `1.1` → `1.1.1`; `1.2` và `2` quay về đúng cấp |
| I14 | Cây heading phẳng đáng ngờ phải báo | từ 4 heading không đánh số cùng cấp ⇒ có lý do `flat_heading_tree` |
| I15 | Lý do vượt trần đúng loại | chunk vượt trần mềm phải ghi `table_row_exceeds_max_tokens` hoặc `sentence_splitter_no_boundary`; chunk trong trần áp dụng không có lý do |
| I16 | Gộp không vượt ranh giới section | mọi block trong một chunk gộp có cùng `parent_section_id` |
| I17 | Bộ tách bó tay phải cảnh báo | khối vượt trần chỉ có một span bao trọn ⇒ manifest có `sentence_splitter_no_boundary` kèm trang hoặc section |
| I20 | Trần cứng tuyệt đối | mọi `chunk.token_count <= hard_cap_tokens`, không có ngoại lệ |
| I21 | Lý do vượt trần áp dụng | chunk vượt trần văn xuôi/bảng phải có `oversize_reason`; mảnh cắt cứng dùng `hard_cap_forced_split` |

**Fixture bắt buộc:** (a) PDF có chương + preamble chương + preamble mục (đúng cây §4.5); (b) PDF 2 cột; (c) PDF heading nhảy cấp 1→3; (d) tài liệu phẳng không heading; (e) PDF scan (nhánh OCR); (f) tài liệu có bảng + caption.

---

## 12. Tham số cấu hình

```yaml
b0:
  normalize:      { unicode: NFC, strip_running_headers: true, dehyphenate: true }
  parser:         { adapter: docling, ocr_fallback: mineru, min_text_ratio: 0.1 }
  chunk:          { max_tokens: 512, max_table_tokens: 2048, hard_cap_tokens: 6000, target_tokens: 256, sentence_overlap: 1 }
  flat_document:  { window_tokens: 2000, overlap_tokens: 200 }
  embed:          { model_id: "...", dim: 768, batch_size: 64, segment_words: false }
  store:          { backend: pgvector }
```

---

## 13. Quyết định còn mở

1. **Granularity chunk** — cùng tập chunk này làm cột ma trận node×chunk ở bước M. Quá to ⇒ nhiễu mention map; quá nhỏ ⇒ ma trận phình. Cần đo trên corpus thật trước khi khoá `max_tokens`.
2. **`block_type` nào đủ tư cách làm evidence chính** — caption/footnote đứng một mình có nên bị loại khỏi `evidence_chunk_ids`?
3. **Prefix `section_path` khi embed** — tăng ngữ cảnh nhưng làm loãng tín hiệu với chunk ngắn; cần A/B.
4. **Ngưỡng cửa sổ trượt cho tài liệu phẳng** — phụ thuộc context window của model extract tầng 1.
