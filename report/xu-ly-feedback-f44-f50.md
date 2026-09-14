# Báo cáo xử lý feedback F44–F52

**Ngày hoàn tất:** 2026-09-04  
**Phạm vi:** `feedback/F17-a3-trich-thuc-the.md`  
**Bản thuật toán cuối:** `a3-section-conversation-v2`  
**Prompt hash F44–F50:** `38ce517a…`  
**Prompt hash sau F51–F52:** `8e7c14c3…`

## 1. Kết quả

| Feedback | Kết quả | Bằng chứng chính |
|---|---|---|
| F44 | Đã sửa | `overfitting`: BM25 từ không khớp lên hạng 1; `P(A\|B)` vẫn hạng 1 |
| F45 | Đã sửa | 4 CASIO, Buffered Channel và UCI dataset đều `learnable=false`; không còn node thuộc nhóm lỗi được nêu mang `true` |
| F46 | Đã sửa | A3 báo `cross_section_duplicate_name_ratio`; `single_chunk_ratio` chuyển sang 2a |
| F47 | Đã ghi tồn đọng | XSTK 4,77/1000, DOCX 18,06/1000; không nới prompt chung |
| F48 | Đã sửa | LLM sinh 6 loại cạnh thay vì chỉ `requires` |
| F49 | Đã sửa | Cả bốn artifact được chạy lại sau vá, cùng algorithm/prompt, 0 section lỗi |
| F50 | Đã sửa | Bỏ phiếu đa số theo kiểu; cảnh báo được `Database Transaction` khác kiểu/khác cờ |
| F51 | Đã sửa | Prompt ra tệp UTF-8; Settings/CLI chọn few-shot; hash theo nội dung |
| F52 | Đã sửa và đo | System prompt 522→401 token; recall gold tăng ở cả ML và XSTK |

## 2. F44 — BM25 và dấu ngoặc

### Nguyên nhân

Tokenizer cũ chỉ `strip` dấu câu thông thường. `(Overfitting)` thành token có ngoặc nên không thể khớp
query `overfitting`.

### Sửa tại điểm gốc

`domain/retrieval.py` dùng `_strip_outer_punctuation()`:

1. Gỡ dấu câu ngoài cùng.
2. Chỉ bóc cặp `(...)` hoặc `[...]` khi ký tự đầu và cuối là một cặp bao hoàn chỉnh.
3. Không gỡ dấu ngoặc chỉ nằm bên trong token.

Vì vậy `(Overfitting)` thành `overfitting`, còn `P(A|B)` giữ nguyên `p(a|b)`. Không dùng regex/tokenizer
mới và không thêm phụ thuộc.

### Kiểm chứng

| Query | Dense | BM25 | Hybrid |
|---|---:|---:|---:|
| `overfitting` | 4 | **1** | 2 |
| `P(A\|B)` | 3 | **1** | **1** |

Test hồi quy kiểm đồng thời hai vế để tránh sửa F44 rồi phá ký hiệu toán.

## 3. F45 — `learnable` thực sự đi từ model vào domain

### Hai lỗ ở luồng cũ

1. JSON schema không có `learnable`, nên model không được hỏi.
2. `_add_entity()` cũng không truyền cờ vào `EntityCandidate`; mặc định dataclass tiếp tục là `true`.
   Dòng `item.get("learnable", True)` trước đó chỉ dùng khi đọc artifact, không phải lúc nhận LLM.

### Luồng mới

```text
Gemini schema bắt buộc boolean learnable
  → prompt hỏi “phải học/hoàn thành hay chỉ là bối cảnh?”
  → _add_entity kiểm đúng kiểu bool
  → EntityCandidate.learnable
  → bỏ phiếu nhất quán theo node_type
  → metrics/layering chỉ đọc true
```

`dataset` bị bỏ khỏi seed types. Mặc định `true` chỉ còn ở đường đọc phản hồi/artifact cũ thiếu trường,
giữ bất đối xứng bảo toàn recall.

### Không còn đồng nhất `non-learnable == media`

F45 tạo ra node bối cảnh `learnable=false`, nên code phải phân biệt bằng `EntityCandidate.is_media`
(`figure`/`table`), không dùng phủ định của `learnable`. Kết quả:

- node bối cảnh không tăng media count;
- không bị kiểm `missing_media_description`;
- không bị tính orphan/caption;
- được giữ trong candidate artifact để A13 review;
- không được embed và không đi vào layering.

Kết quả cuối có 11 node bối cảnh không học được và 79 media. Vector vì vậy là 369 learnable + 79
media = 448, không phải tổng 459 entity.

### Đối chiếu đúng các ca feedback nêu

| Tài liệu | Entity | Kiểu | Sau sửa |
|---|---|---|---|
| XSTK | CASIO fx-500MS/570MS/500ES/570ES | `tool` | cả 4 `false` |
| DOCX | Buffered Channel | `tool` | `false` |
| Slide | UCI Letter-Recognition Data | `dataset` | `false` |

`Trường Đại học Sài Gòn`, PostgreSQL, technology và weather dataset không còn được model giữ trong bản
cuối. Số node thuộc đúng nhóm sai mà F45 liệt kê còn `learnable=true`: **0**.

## 4. F46 — thước đo có ý nghĩa trước merge

`single_chunk_ratio` bị bỏ khỏi `EntityMetrics`, `RecallMetrics`, gold output và fixture. Thước đo thay thế:

```text
cross_section_duplicate_name_ratio
= số ứng viên learnable có tên chuẩn hoá xuất hiện ở >= 2 section
  / tổng ứng viên learnable
```

Tên dùng cùng chuẩn hoá so node của A3: B0 + casefold, dấu câu đổi thành khoảng trắng. Cùng tên lặp hai
lần trong một section không được tính. Kết quả:

| Tài liệu | Tỉ lệ trùng tên xuyên section |
|---|---:|
| ML | 35,64% |
| XSTK | 60,00% |
| DOCX | 37,88% |
| Slide | 47,37% |
| Corpus | 47,43% |

`single_chunk_ratio` chỉ quay lại ở 2a, sau khi một node canonical đã hợp nhất provenance nhiều chunk.

## 5. F47 — tồn đọng được giữ nguyên, không chữa sai tầng

| Tài liệu | Learnable | Mật độ /1000 | Phân loại |
|---|---:|---:|---|
| ML | 101 | 11,31 | đích |
| XSTK | 145 | 4,77 | quá thô |
| DOCX | 66 | 18,06 | quá mịn |
| Slide | 57 | 9,86 | đích |

Gold cuối:

| Chương | Gold | Predicted | Match | Recall | Excess |
|---|---:|---:|---:|---:|---:|
| ML văn xuôi | 71 | 71 | 55 | 77,46% | 22,54% |
| XSTK công thức | 40 | 32 | 19 | 47,50% | 40,63% |

Khoảng recall là **29,96 điểm phần trăm**. Prompt chung vẫn không được nới: nó có thể tăng XSTK nhưng
làm DOCX mịn hơn. Đường tiếp theo vẫn là B0 cung cấp ảnh crop formula theo bbox hoặc một đợt few-shot
theo thể loại có bộ vàng riêng.

## 6. F48 — hệ cạnh mở hoạt động thật

Prompt nay nói đối xứng rằng `edge_type` là hệ mở và mồi `example_of`, `contrasts_with`,
`component_of`, `computed_by`, `uses`; `requires` chỉ dành cho tiên quyết. Schema vẫn là chuỗi tự do,
guard alias `requires` và allowlist A9/A10 không đổi.

Stats chỉ đếm cạnh có evidence từ model, không tính cạnh media do code sinh. Corpus cuối có:

| Loại cạnh | Số cạnh |
|---|---:|
| `component_of` | 29 |
| `computed_by` | 35 |
| `contrasts_with` | 4 |
| `example_of` | 32 |
| `requires` | 34 |
| `uses` | 42 |

Như vậy model sinh 6 loại/176 cạnh; `illustrates` và `tabulates` được báo riêng là cạnh code sinh.

## 7. F49 — artifact đã đồng bộ

| Tài liệu | Version | Total | Learnable | Vector | Lượt LLM | Lỗi section |
|---|---:|---:|---:|---:|---:|---:|
| ML | v6 | 110 | 101 | 110 | 67 | 0 |
| XSTK | v3 | 202 | 145 | 198 | 122 | 0 |
| DOCX | v5 | 75 | 66 | 69 | 75 | 0 |
| Slide | v4 | 72 | 57 | 71 | 87 | 0 |
| **Tổng** |  | **459** | **369** | **448** | **351** | **0** |

Cả bốn manifest cùng `algorithm_id=a3-section-conversation-v2`, prompt hash `38ce517a…`. Algorithm
được bump vì F50 thay đổi output dù prompt không đổi; nhờ đó cache cũ không thể được dùng im lặng.

Trong lúc chạy thật, hai lượt sinh đã gặp lỗi kết nối ở bước embedding. Adapter embedding trước đó
không retry dù config đã có `gemini_max_retries`. Đã tái dùng đúng config này, retry lỗi kết nối và HTTP
408/429/5xx bằng backoff stdlib; test tái hiện lỗi lần đầu rồi thành công lần hai.

## 8. F50 — nhất quán `learnable` theo kiểu và xuyên kiểu

### Trong cùng `node_type`

Mỗi kiểu bỏ phiếu theo số entity. Đa số quyết định; chỉ khi hoà mới chọn `true`. Stats lưu cả kiểu xung
đột và kết quả. Điều này chặn một phiếu `tool=true` lật bốn CASIO `false`.

Chạy thật:

- ML: `concept` → đa số `true`.
- DOCX: `component` → đa số **`false`**, sửa đúng điểm đáng ngờ của v4.

### Cùng tên nhưng khác `node_type`

Code nhóm tên chuẩn hoá, so tập kiểu và tập cờ. Nếu tên có nhiều kiểu nằm hai phía `learnable`, warning
và stats lưu tên cùng mapping kiểu→cờ. Bản cuối bắt được:

```text
Database Transaction: concept=true, mechanism=false
```

18/459 tên mang nhiều kiểu, nhưng sau bỏ phiếu chỉ một tên còn cờ trái nhau. Đây là hàng review, không
tự merge ở A3.

Spec 2a đã chốt: trong nhóm merge, kiểu canonical theo đa số; hoà thì agent phải chọn một kiểu đã xuất
hiện và ghi evidence. `learnable` bỏ phiếu lại trên ứng viên của kiểu canonical, hoà mới `true`.

## 9. Test và tính tối giản

Các nhánh mới đều có test từng thất bại trên hành vi cũ:

- ngoặc ngoài khớp `overfitting` nhưng không phá `P(A|B)`;
- schema/candidate thật sự nhận `learnable=false`;
- node bối cảnh không bị tính là media hay embed;
- trùng tên xuyên hai section, nhưng không tính lặp trong cùng section;
- cạnh model có nhiều loại và stats không trộn cạnh code;
- một phiếu `true` không lật đa số `false`;
- cùng tên khác kiểu/khác cờ phát warning;
- embedding lỗi kết nối một lần được retry.

Không thêm SDK, tokenizer, framework retry hay abstraction mới. Chỉ tái dùng stdlib, `Counter`, config
retry và các kiểu/domain sẵn có.

Kết quả suite ở mốc F44–F50: **186 passed**; chỉ còn warning từ Docling/Swig.

## 10. F51 — prompt là dữ liệu vận hành

Năm khối văn bản được đưa khỏi module Python vào `application/prompts/*.txt`. `ExtractionPrompts` được
nạp khi dựng `ExtractEntities`; schema và logic dựng/băm vẫn ở `extraction_prompt.py`.

Hai đường chọn few-shot cùng đi tới một loader:

```text
DOC2ROADMAP_EXTRACTION_FEW_SHOT=path/to/few-shot.txt
doc2roadmap extract --doc-id ... --few-shot path/to/few-shot.txt
doc2roadmap a3      --doc-id ... --few-shot path/to/few-shot.txt
```

`prompt_hash` băm nội dung đã đọc, không băm đường dẫn. Vì vậy đổi nội dung cùng tệp vẫn vô hiệu hoá
artifact, còn hai đường dẫn có nội dung giống nhau không tạo version giả. Script ghi fixture dùng đúng
cùng bundle để bản ghi và lượt phát lại không lệch hash.

Wheel đã được dựng và kiểm danh sách file: đủ `system.txt`, `few-shot.txt`, `section.txt`, `glean.txt`,
`validation.txt`; không có ca chỉ chạy được trong source tree.

## 11. F52 — kết quả A/B prompt Việt–Anh

Phần hướng dẫn được chuyển sang tiếng Anh. Hai đoạn `CHUNK_TEXT` và tên thực thể mẫu vẫn giữ nguyên
tiếng Việt; chỉ nhãn và lời giải thích bao quanh được dịch.

Đếm bằng tokenizer Gemma ghim trong repo:

| Khối | Trước | Sau | Chênh |
|---|---:|---:|---:|
| System prompt | 522 | **401** | **−23,2%** |
| Toàn scaffolding | 887 | **745** | **−16,0%** |

Với 363 lượt gọi của lần chạy mới, riêng system prompt bớt khoảng **43.923 token**; tính cả scaffolding
là khoảng **51.546 token**. Đây vẫn là chỉ báo Gemma, không phải số billing chính xác của Gemini.

Bốn artifact mới có cùng `prompt_hash=8e7c14c3…`, `algorithm_id=v2`, 0 section lỗi và
`missing_media_descriptions=0`:

| Tài liệu | Version | Lượt LLM | Learnable trước→sau | Mật độ trước→sau | Kết luận |
|---|---:|---:|---:|---:|---|
| ML | v7 | 68 | 101→105 | 11,31→**11,76** | trong đích |
| XSTK | v4 | 130 | 145→156 | 4,77→**5,13** | vẫn quá thô |
| DOCX | v6 | 76 | 66→72 | 18,06→**19,70** | vẫn quá mịn, xấu hơn |
| Slide | v5 | 89 | 57→62 | 9,86→**10,72** | trong đích |

Corpus tăng 369→395 node học được, mật độ 7,57→**8,10**, từ `coarse` vào `target`. Không dùng số corpus
để che F47: hai tài liệu biên vẫn lệch ngược chiều.

Bộ vàng quyết định giữ bản tiếng Anh:

| Chương | Recall trước→sau | Excess trước→sau | Evidence |
|---|---:|---:|---:|
| ML văn xuôi | 77,46%→**83,10%** | 22,54%→**20,27%** | 100% |
| XSTK công thức | 47,50%→**57,50%** | 40,63%→**32,35%** | 100% |

Recall tăng 5,64 và 10,00 điểm phần trăm, excess cùng giảm. Vì cả hai chương gold tốt lên rõ và chi phí
prompt giảm, bản tiếng Anh được giữ; mật độ DOCX tăng là tồn đọng F47, không phải lý do nới prompt chung.

Jaccard so với bản tiếng Việt trước đó xác nhận đây là đổi cấu hình thật:

| Tài liệu | Node Jaccard | Edge Jaccard |
|---|---:|---:|
| ML | 0,948 | 0,099 |
| XSTK | 0,795 | 0,116 |
| DOCX | 0,765 | 0,148 |
| Slide | 0,741 | 0,103 |

## 12. Kiểm chứng cuối

- Test F51/F52 đã được thấy đỏ trước sửa do thiếu `load_prompts`.
- **185 unit test pass**, 5 integration được tách khi chạy nhanh.
- **190/190 toàn suite pass**, gồm cả 5 integration test Docling.
- Wheel build thành công và chứa đủ năm prompt file.
- Bốn lần chạy thật: **363 lời gọi, 474 thực thể, 19 figure + 60 table, 0 section lỗi**.
