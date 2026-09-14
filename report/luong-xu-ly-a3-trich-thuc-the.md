# Báo cáo triển khai và luồng xử lý A3 / A3′

**Ngày chốt:** 2026-09-04  
**Phạm vi:** `doc/A3-trich-thuc-the-spec.md` và 15 ticket trong `task/a3-trich-thuc-the/`  
**Mô hình sinh:** `gemini-3.1-flash-lite`  
**Mô hình embedding:** `gemini-embedding-001`, 768 chiều

## 1. Kết quả cuối

A3 hiện nhận artifact B0, trích ứng viên theo section bằng hội thoại ba giai đoạn, xác minh bằng chứng
bằng code, tạo node media tất định từ ref, gắn nhãn `confirmed` cho tập con cạnh media, rồi chỉ đóng
băng artifact khi toàn bộ section và mô tả media đều đầy đủ. A3′ độc lập embed 233 chunk, dựng BM25 và
truy hồi lai RRF. Hai nhánh có thể chạy song song bằng lệnh `a3`.

Kết quả thật trên bốn tài liệu:

| Tài liệu | Node tổng | Learnable | /1000 token | Lượt LLM | Section rỗng | Lỗi cuối |
|---|---:|---:|---:|---:|---:|---:|
| `nhap-mon-ml` | 114 | 105 | 11,76 | 68 | 3 | 0 |
| `xstk-ch3-1` | 209 | 156 | 5,13 | 130 | 2 | 0 |
| `baocao-canhan` | 75 | 72 | 19,70 | 76 | 6 | 0 |
| `naive-bayes` | 76 | 62 | 10,72 | 89 | 2 | 0 |
| **Tổng** | **474** | **395** | **8,10** | **363** | **13** | **0** |

Media cuối cùng có đúng **19 figure + 60 table**, không node nào thiếu mô tả. Phân bố nguồn cuối:

- Figure: 8 `original` + 11 `generated_multimodal`.
- Table: 4 `original` + 56 `generated_from_content` = 60 node table.
- Con số “60 bảng được mô hình mô tả + 4 giữ chú thích” trong ticket là hai phép đếm chồng nhau:
  mô hình vẫn trả mô tả trong lượt trích cho bảng có caption, nhưng final state ưu tiên 4 caption gốc;
  vì vậy final source hợp lệ là 56 generated + 4 original, không phải 64 node.
- 474 node có vector: 395 learnable + 79 media. Bản chạy này không giữ node bối cảnh phi-media;
  `learnable=false` vẫn được code loại khỏi embedding nếu xuất hiện; không có `caption_source: none`.

## 2. Sơ đồ luồng tổng thể

```text
artifacts/chunks/{doc}/vN
          │
          ├────────────────────────── A3′ ──────────────────────────┐
          │  ghép section_path lúc embed                            │
          │  Gemini embedding 233 chunk                             │
          │  lưu retrieval + dựng BM25                              │
          │                                                         ▼
          │                                                HybridRetriever
          │                                             dense + BM25 → RRF
          │
          └────────────────────────── A3 ───────────────────────────┐
             dựng SectionContext                                   │
             ├─ chunk text + section_path                           │
             ├─ formula raw theo ref                                │
             └─ ảnh bytes + media ref/caption status                │
                         │                                          │
                         ▼                                          │
             mỗi section, cùng một conversation                     │
             1) extract → 2) glean 0..5 → 3) validate               │
                         │                                          │
                         ▼                                          │
             code xác minh evidence/alias/edge                      │
                         │                                          │
                         ▼                                          │
             media từ image_refs/table_refs                         │
             + mọi cạnh đồng-vị-trí (recall floor)                  │
             + gắn confirmed lên tập con cạnh có sẵn                │
                         │                                          │
                         ▼                                          │
             retry lỗi/thiếu mô tả ở cuối                           │
             gate section rỗng >40%                                 │
             hàng rào đủ toàn tài liệu                              │
                         │                                          │
                         ▼                                          │
             embed description_draft + media description            │
                         │                                          │
                         ▼                                          │
             candidates/{doc}/vN + manifest/hash/metrics/Jaccard ───┘
```

## 3. Luồng A3 chi tiết từng bước

### Bước 1 — Nạp cấu hình và fail-fast bí mật

`src/doc2roadmap/config.py` khai báo mọi biến cấu hình bằng `Settings`. API key là `SecretStr`, đọc từ
`DOC2ROADMAP_GEMINI_API_KEY`; model sinh mặc định là `gemini-3.1-flash-lite`, embedding là
`gemini-embedding-001:768`, concurrency mặc định 4. `.env.example` có đủ tên biến nhưng để key rỗng;
`.env` thật bị `.gitignore` loại.

`src/doc2roadmap/composition.py` là composition root. `_a3_dependencies()` giải mã key đúng một lần để
dựng adapter. Thiếu key thì dừng ngay lúc dựng, trước khi một section nào chạy. `build_extract()`,
`build_index()`, `build_search()` và `build_a3()` nối các cổng với adapter thật; không có service locator
hay dependency container riêng.

### Bước 2 — Đọc artifact B0 và dựng ngữ cảnh section

`ExtractEntities.execute()` gọi `ArtifactStore.load_latest_chunks(doc_id)`. `_build_contexts()` lấy
`parse_version` từ manifest chunk rồi đọc đúng parse tree tương ứng, không lấy “latest parse” mơ hồ.

Với mỗi section có chunk trực tiếp, code tạo `SectionContext` gồm:

- `section_id`, title và toàn bộ `section_path`;
- chỉ chunk trực tiếp của section đó, không đưa nội dung section láng giềng;
- raw formula được ánh xạ bằng `formula_id`, kèm `chunk_id` và `char_start`;
- bytes ảnh được đọc bằng ID SHA-256 từ thư mục parse tree;
- caption khai báo trong parse tree cho figure/table.

Raw formula chỉ tồn tại trong prompt. Nó không ghi ngược vào `Chunk.text`, không đổi `chunk_id`, và
không đi vào đầu vào embedding. Số thật được bơm: `nhap-mon-ml` 1 formula/12 token, `xstk` 263/7.270,
`naive-bayes` 32/968, DOCX 0.

### Bước 3 — Tạo prompt có thể băm và đa phương thức

`src/doc2roadmap/application/prompts/` chứa bốn khối hướng dẫn và few-shot dạng UTF-8;
`extraction_prompt.py` chỉ còn loader, schema và logic dựng/băm. Các hướng dẫn dùng tiếng Anh, còn hai
đoạn corpus minh hoạ giữ tiếng Việt. Có thể ghi đè few-shot bằng Settings/CLI mà không sửa Python.
`prompt_hash()` băm sáu nhóm dữ liệu ảnh hưởng output: template, few-shot, model ID, tham số sinh, schema
và seed types. Hàm không nhận key nên key không thể lọt vào hash.

Sau feedback F45/F48, schema bắt buộc mỗi entity trả `learnable`; prompt hỏi mục đó phải được người học
hoàn thành hay chỉ là bối cảnh. `edge_type` cũng được khai mở và mồi năm quan hệ ngoài `requires`.
Nếu cùng một node type nhận hai cờ trái nhau, code lấy đa số và chỉ ưu tiên `true` khi hoà. Cùng tên
khác kiểu mà cờ trái nhau được ghi warning cho 2a; media vẫn bị code ép `false`.

`section_prompt()` ghi tường minh từng media ref:

```text
type=<figure|table> id=<sha256> chunk=<chunk_id>
char_start=<tọa độ tài liệu> caption_status=<original|missing>
```

Điều này cần thiết vì ảnh có caption không còn dấu `[figure]` trong text. Ảnh thật được gửi kèm ngay
sau nhãn `MEDIA_ID` tương ứng; bảng không gửi ảnh vì markdown đã nằm trong chunk.

Prompt yêu cầu mô tả thuộc tính nhìn thấy (trục, nhãn, số đường, hình dạng), không hỏi “ý nghĩa hình”.
Mỗi media trả `description` và `confirmed_entities`, trong đó tập xác nhận có thể rỗng, một hoặc nhiều.

### Bước 4 — Gọi Gemini trong một conversation ba giai đoạn

`src/doc2roadmap/infrastructure/llm/gemini.py` dùng `urllib.request` của standard library. Key chỉ nằm
trong header `x-goog-api-key`, không nằm URL. Request bật structured JSON, temperature 0 và schema cụ
thể. Mã lỗi tạm thời 408/429/5xx lùi theo cấp số nhân; lỗi vĩnh viễn báo mã HTTP mà không đưa response
body/key vào thông báo. Cổng embedding dùng cùng số lần retry cấu hình; guard này được thêm sau khi hai
lần chạy thật hoàn tất sinh nhưng gặp lỗi kết nối tạm thời ở bước embed.

`extract_section()` giữ một `ExtractionSession` duy nhất:

1. **Extract:** gửi text, ancestor path, formula raw, danh sách media ref và ảnh.
2. **Glean:** gửi lại tên đã có; dừng ngay khi thêm 0 node, tối đa 5 vòng. Chuỗi node mới mỗi vòng được
   ghi trong stats; chạm trần có cờ riêng.
3. **Validate:** gửi toàn bộ candidate node/edge và nhận danh sách ID cần loại.

Nếu JSON sai, session gửi đúng một lượt sửa trong cùng conversation, nêu lỗi dòng/cột. Sai lần hai làm
section thất bại. Bốn lần chạy cuối có 0 JSON repair và 0 section lỗi dai dẳng.

### Bước 5 — Xác minh bằng chứng bằng code

`src/doc2roadmap/domain/entities.py` chứa logic thuần:

- `locate_evidence()` tái dùng `normalize_text()` của B0, không so mờ; chỉ nới hoa thường và khoảng
  trắng, sau đó trả span tuyệt đối `chunk.char_start + offset`.
- `verify_alias()` yêu cầu alias thật sự xuất hiện bên trong câu evidence đã xác minh.
- `_add_edge()` chỉ nhận edge khi hai endpoint đã tồn tại và evidence khớp một chunk trong section.
- `figure`/`table` do LLM trả bị từ chối vì là type dành riêng; alias của `requires` như
  `depends_on` cũng bị từ chối.

Khái niệm chỉ có trong ảnh là ngoại lệ có căn cứ rõ: model phải trả `media_evidence_id` trùng một ảnh
được đính kèm. Code đổi nó thành `SourceRef(chunk_id, char_start)` của image ref; ID lạ vẫn bị loại.
Như vậy yêu cầu “hình dạy mà text không nói” không phá nguyên tắc provenance.

### Bước 6 — Sinh media và recall-floor edges

`build_media_candidates()` không hỏi LLM để phát hiện media. Nó đọc `image_refs`/`table_refs`, tạo ID
`media:{doc}:{type}:{media_id}` và khử trùng lặp bằng đúng content hash. Cùng media xuất hiện ở hai
chunk vẫn chỉ là một node nhưng giữ hai `SourceRef`.

Mỗi media nối tới **mọi** learnable entity chung chunk bằng `illustrates` hoặc `tabulates`. Đây là sàn
recall, nên phần xác nhận phía sau không có quyền xóa hay tạo cạnh.

Nếu media không có cạnh, `orphan_reason` là:

- `cover_art` nếu toàn bộ ref ở trang 1;
- `no_concept_in_chunk` nếu chunk không có learnable entity;
- `unknown` cho trường hợp còn lại; chỉ loại này sinh warning.

### Bước 7 — Chốt mô tả và nhãn `confirmed`

Caption khai báo từ parse tree luôn thắng mô tả sinh. Figure thiếu caption dùng
`generated_multimodal`; table thiếu caption dùng `generated_from_content`. Model trả tập
`confirmed_entities`; code chỉ tìm cạnh đồng-vị-trí đã có rồi đổi `confirmed=true`. Tên không thuộc
chunk bị đếm `rejected_confirmation_labels`; số cạnh trước/sau không đổi.

Một lần chạy `xstk` đầu tiên thiếu hai mô tả bảng. Artifact đã bị chặn. Sau khi thêm yêu cầu một entry
cho mỗi media ID và retry section thiếu mô tả ở cuối, lần chạy sau có 0 thiếu. Đây là kiểm chứng thật
cho guard, không chỉ test happy path.

### Bước 8 — Song song, retry cuối và cổng chất lượng

`_run_contexts()` dùng `ThreadPoolExecutor` với concurrency cấu hình được. Section lỗi hoặc section trả
thiếu media description được đưa vào hàng retry tuần tự ở cuối. Nếu vẫn lỗi, kết quả mang
`coverage_incomplete` và `JsonArtifactStore.save_candidates()` từ chối ghi.

`SectionExtraction.empty` chỉ đúng khi section không tạo bất kỳ node nào; section media-only là hợp lệ
và không làm tăng empty rate. Nếu số section thật sự rỗng vượt **40%**, pipeline dừng ngay. Warning
trùng được `_collapse_warnings()` gộp theo dạng `×N`.

### Bước 9 — Hàng rào toàn tài liệu và embed description

Chỉ sau khi toàn bộ section đã hoàn tất, `_dedupe_document_candidates()` mới hợp nhất candidate trùng
ID và `ExtractEntities` mới gọi cổng embedding. Learnable node embed `description_draft`; media embed
mô tả đã chốt. Node bối cảnh `learnable=false` được giữ để review nhưng không embed và không đi vào
layering. Node thiếu mô tả nháp được bỏ qua kèm warning; media thiếu mô tả làm artifact không hoàn chỉnh
và bị chặn.

Kết quả cuối: 395 vector learnable + 79 vector media = **474 vector**. Vector nằm trong artifact
`candidates`, manifest ghi `vector_stage: description_draft` và `embedding_model_id`.

### Bước 10 — Phiên bản artifact, cache và độ ổn định

`src/doc2roadmap/infrastructure/artifacts/json_store.py` mở rộng khuôn B0 cho `candidates`, `canonical`,
`graph`, `retrieval`. Mỗi tầng có source hash, config hash, upstream version và manifest riêng. Ghi file
qua file `.tmp` rồi `os.replace()` để tránh artifact nửa chừng.

Chạy cùng hash mặc định trả cache và không gọi model. `extract --force` là đường tường minh duy nhất để
tạo phiên bản thứ hai cùng cấu hình nhằm đo stochastic stability. Trước khi lưu vN mới, manifest ghi
Jaccard với phiên bản trước.

Hai lần chạy lịch sử v2/v3 của `nhap-mon-ml` cùng model/prompt cho:

- node Jaccard = **1,0000**;
- edge Jaccard = **0,2698**.

Node được ghép bằng tên chuẩn hóa hoặc giao alias theo maximum one-to-one matching, không dùng vector.
Edge được so sau khi ánh xạ endpoint qua phép ghép node. Kết quả cho thấy node ổn định nhưng edge đề
xuất vẫn nhiễu cao, đúng lý do A3 chỉ xem edge là ứng viên cho tầng duyệt sau.

## 4. Luồng A3′ và truy hồi lai

`src/doc2roadmap/application/use_cases/index_document.py` đọc 233 chunk và gọi `embedding_text()` để
ghép `section_path + "\n\n" + text` **chỉ tại thời điểm embed**. Payload lưu text/chunk ID gốc cùng
vector; đổi model hoặc số chiều đổi config hash và sinh retrieval version mới.

`src/doc2roadmap/domain/retrieval.py` dùng hai nhánh:

- dense cosine trên vector đã chuẩn hóa;
- BM25 từ token NFC/casefold bằng standard library, không thêm bộ tách từ tiếng Việt;
- RRF cộng `1/(60+rank)` từ hai nhánh. `allowed_stage_ids` được áp trước khi chấm ở cả dense và BM25.

`SearchDocument` kiểm model query trùng model của index, embed query với task
`RETRIEVAL_QUERY`, rồi gọi hybrid retriever.

Benchmark năm truy vấn:

| Truy vấn | Dense | BM25 | Hybrid |
|---|---:|---:|---:|
| `overfitting` | 4 | 1 | 2 |
| `học từ dữ liệu đã có nhãn` | 2 | 1 | 2 |
| `hệ số tương quan mẫu` | 1 | 1 | 1 |
| `P(A\|B)` | 3 | 1 | 1 |
| `lỗi tranh chấp khi nhiều luồng cùng ghi dữ liệu` | 10 | 6 | 6 |

Ca `overfitting` xác nhận F44: bỏ cặp ngoặc bao ngoài đưa BM25 từ không khớp lên hạng 1, trong khi
`P(A|B)` vẫn giữ nguyên token và tiếp tục đưa target từ hạng dense 3 lên hạng hybrid 1.

## 5. Hai seam replay, không gọi mạng trong test

`src/doc2roadmap/infrastructure/llm/replay.py` ghi nhật ký conversation có thứ tự. Fixture
`tests/fixtures/llm/a3-section-with-image.json` có 3 lượt, chứa ảnh base64, model ID và prompt hash;
kích thước thật **81.095 byte**. Replay yêu cầu prompt/schema/ảnh của lượt n khớp tuyệt đối.

`src/doc2roadmap/infrastructure/embedding/replay.py` dùng cấu trúc khác: từ điển
`sha256(task_type + text) → vector`. Fixture `tests/fixtures/embedding/a3-chunks.json` chứa 233 vector
768 chiều, kích thước thật **3.817.219 byte**, và bị vô hiệu khi embedding model ID đổi.

Hai fixture đã được quét và không chứa `AIza`, tên biến key hay header key. Unit test dùng replay hoặc
fake adapter; chỉ hai script `record_*` và lệnh vận hành thật được phép chạm mạng.

## 6. Bộ vàng và kết luận đường leo công thức

`tests/fixtures/a3/gold-entities.json` được hoàn thành trước lần gọi A3 đầu tiên. Phạm vi:

- `nhap-mon-ml`: 19 section chấm, 71 gold entity; section 1.1.1 chỉ hiệu chỉnh.
- `xstk-ch3-1`: 9 section chấm, 40 gold entity; section 1.1 chỉ hiệu chỉnh.

Kết quả:

| Chương | Gold | Predicted | Match | Recall | Excess | Evidence |
|---|---:|---:|---:|---:|---:|---:|
| văn xuôi ML | 71 | 74 | 59 | **83,10%** | 20,27% | 100% |
| công thức XSTK | 40 | 34 | 23 | **57,50%** | 32,35% | 100% |

Sau feedback, recall gold của XSTK thấp hơn ML **25,60 điểm phần trăm** dù raw formula đã được bơm.
Kết luận không đổi: thiếu sót tập trung rõ ở chương công thức. Đường leo hợp lý là ticket B0 lưu ảnh cắt
formula theo bbox; không nên tiếp tục làm prompt chung mịn hơn vì DOCX ở 19,70/1000 (quá mịn), còn
XSTK ở 5,13/1000 (quá thô). Đây là tồn đọng F47 có số, không phải lý do nới prompt chung.

## 7. Vai trò từng file code A3

| File | Trách nhiệm |
|---|---|
| `config.py` | Cấu hình model, key, concurrency, timeout, retry, số chiều và đường dẫn few-shot. |
| `composition.py` | Dựng adapter/use case thật; fail-fast key; không chứa logic nghiệp vụ. |
| `application/prompts/*.txt` | Scaffolding tiếng Anh và corpus few-shot tiếng Việt. |
| `application/extraction_prompt.py` | Nạp prompt, dựng nội dung, JSON schema và `prompt_hash`. |
| `application/ports/extraction.py` | Protocol session/extractor và kiểu ảnh/turn/reply. |
| `application/ports/embedding.py` | Một cổng embedding dùng chung cho chunk/entity/media. |
| `application/ports/artifacts.py` | Hợp đồng version/load/save cho bốn tầng artifact mới. |
| `application/use_cases/extract_entities.py` | Điều phối context, conversation, validation, retry, gate, barrier, embedding và save. |
| `application/use_cases/index_document.py` | Dựng/reuse retrieval index và thực thi search query. |
| `application/use_cases/report_a3.py` | Báo cáo corpus, chấm gold và so Jaccard phiên bản. |
| `domain/entities.py` | Evidence exact, alias/type guards, media edges, metrics, recall/Jaccard. |
| `domain/retrieval.py` | Ghép context lúc embed, BM25, cosine, RRF và stage filter. |
| `infrastructure/llm/gemini.py` | Gemini structured multimodal REST, retry và JSON repair. |
| `infrastructure/llm/replay.py` | Record/replay conversation có thứ tự. |
| `infrastructure/embedding/gemini.py` | Batch embedding REST và chuẩn hóa vector. |
| `infrastructure/embedding/replay.py` | Record/replay dictionary request-hash → vector. |
| `infrastructure/artifacts/json_store.py` | Lưu JSON nguyên tử, version/cache và chặn incomplete. |
| `presentation/cli/main.py` | Các lệnh A3; `extract`/`a3` nhận `--few-shot`. |
| `scripts/record_a3_fixture.py` | Điểm mạng tường minh để ghi một section đa phương thức. |
| `scripts/record_embedding_fixture.py` | Điểm mạng tường minh để ghi 233 vector. |
| `scripts/benchmark_a3_retrieval.py` | Chạy lại năm truy vấn benchmark. |

## 8. Lệnh vận hành và tái lập

```powershell
doc2roadmap index --doc-id nhap-mon-ml
doc2roadmap extract --doc-id nhap-mon-ml
doc2roadmap a3 --doc-id nhap-mon-ml
doc2roadmap search "P(A|B)" --doc-id naive-bayes --top-k 10
doc2roadmap extract --doc-id nhap-mon-ml --force
doc2roadmap a3-compare --doc-id nhap-mon-ml --first 2 --second 3
doc2roadmap a3-evaluate --doc-id nhap-mon-ml --gold tests/fixtures/a3/gold-entities.json
doc2roadmap a3-report --doc-id nhap-mon-ml --doc-id xstk-ch3-1
python scripts/record_a3_fixture.py
python scripts/record_embedding_fixture.py
python scripts/benchmark_a3_retrieval.py
```

`--force` chỉ dùng khi chủ động đo Jaccard; vận hành bình thường giữ cache để không trả tiền lần hai.

## 9. Kiểm chứng

- Test regression mới được chạy đỏ trên hành vi cũ trước khi sửa: report module, search application,
  `confirmed`, visual-only evidence, media-only empty gate, missing-description retry, force version và
  payload embedding 768 chiều.
- Bộ kiểm thử cuối: **186 test passed**, gồm cả integration Docling; chỉ còn warning deprecation từ
  dependency Docling/Swig.
- Fixture số đo đã khóa tại `tests/fixtures/a3/four-document-metrics.json`.
- ADR `doc/adr/0004-doi-embedding-la-doi-tap-node.md` ghi rõ đổi embedding sẽ đổi blocking và tập node,
  không chỉ đổi thứ hạng tìm kiếm.

## 10. Quyết định Ponytail

Không thêm SDK Gemini, vector database, tokenizer tiếng Việt, framework retry hay DI framework.
Adapter dùng standard library; BM25/cosine/RRF là logic nhỏ thuần; scan O(N) được giữ vì corpus chỉ 233
chunk. Điểm nâng cấp được hoãn có chủ đích: chuyển retrieval vào PostgreSQL/pgvector khi profiler cho
thấy scan O(N) là nút thắt, và thêm formula crop chỉ khi ticket B0 mới được phê duyệt.
