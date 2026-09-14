# Luồng mới (bản đầy đủ): Extract song song → Agent merge theo cụm → Mention map → Agent edge định tuyến

> ⚠️ **KHÔNG PHẢI NGUỒN CHÂN LÝ.** Nguồn chân lý là [`spec-addendum.md`](./spec-addendum.md).
> Tài liệu này mô tả cùng một hệ thống bằng hệ nhãn khác (T1–T4 thay vì A1–A13) và **đã lỗi thời ở
> một số chỗ** — đáng kể nhất là hệ kiểu node/cạnh: bản chân lý nay dùng **hệ kiểu mở** với `node_type`
> và `edge_type` do LLM tự đặt, chỉ đóng cạnh `requires`; và mọi thuật toán thứ tự (§9 quality gate,
> §9 cycle, §10 layering ở đây) **chỉ được đọc cạnh `requires`** trên node `learnable = true`.
> Giữ lại tài liệu này làm tham chiếu lịch sử và cho phần phụ lục hướng nghiên cứu.

Tài liệu tự chứa, đặc tả chi tiết Pha A (ingestion) phiên bản cuối. Đầu vào: 1 tài liệu PDF/DOCX. Đầu ra: bảng node khái niệm canonical + đồ thị tiên quyết (DAG, mọi edge có confidence + evidence) + lộ trình học theo giai đoạn + chỉ mục vector đã gắn stage — sẵn sàng cho pha học online (tutor agent scoped RAG, quiz, unlock).

## 1. Nguyên tắc thiết kế và phân quyền

1. **Agent hóa đúng chỗ khó, code hóa chỗ rẻ.** LLM/agent chỉ đảm nhận 3 việc: extract ứng viên (T1), kiểm định merge (T2a), phán quyết edge (T2b). Mọi thứ còn lại — parse, chunk, embed, cluster, mention map, dò chạm, check cycle, topo sort, layering — là code deterministic.
2. **Hai trục phân vùng cho hai việc.** Merge phân vùng theo *độ giống ngữ nghĩa*; suy luận edge phân vùng theo *cấu trúc tài liệu* (chương) hoặc *cụm chủ đề*, chọn bằng định tuyến.
3. **Evidence bắt buộc.** Mọi edge `requires` phải kèm confidence + chunk bằng chứng trong tài liệu. Không evidence → không tạo. Đây là hàng rào chống LLM suy luận "chay" từ kiến thức nền.
4. **Kiểm tra cấu trúc nằm trong code**, không giao LLM tự giác: cycle chặn đồng bộ trong `add_edge`, evidence không tồn tại bị executor từ chối.
5. **Checkpoint mọi bước**, output trung gian có version — crash thì resume, chỉnh prompt thì chạy lại từ đúng tầng đó.

**Phân quyền (tóm tắt vai trò):**

| Ai | Được quyết | Không được quyết |
|---|---|---|
| Agent 2a | Danh tính khái niệm: merge / tách cha–con / tên chuẩn / description | Không tạo edge (chỉ đề xuất) |
| Agent 2b | Phán quyết từng cặp: tạo edge (chiều, confidence, evidence) / từ chối / treo | Không tạo node; không xét cặp ngoài hồ sơ được giao (chỉ flag) |
| Executor (code) | Tính hợp lệ cấu trúc lúc commit: cycle, evidence tồn tại, id hợp lệ | Không sửa nội dung phán quyết |
| T3 (code + 1 pass review) | Hợp lệ toàn cục, fallback | |

## 2. Sơ đồ toàn luồng

```
PDF/DOC
  |
B0. INGESTION CHUNG (cố định)
  Parse layout-aware -> Chunk theo cấu trúc ---------+
  |                                                  |
  |                                     Embed chunks -> VECTOR DB
  |                                     (metadata: section, page,
  |                                      order_index, stage_id=null)
T1. EXTRACT ỨNG VIÊN (cố định, stateless, SONG SONG toàn bộ)
  Mỗi (siêu) section 1 lời gọi model rẻ.
  Output cô đọng: candidates + edge đề xuất kèm evidence.
  |
T2a. MERGE THEO CỤM (trục: ĐỘ GIỐNG NGỮ NGHĨA)
  Lọc tự động >=0.95 -> đồ thị ứng viên (ngưỡng thấp, ưu recall)
  -> Leiden/connected components -> mỗi cụm 1 agent kiểm định,
  SONG SONG; cụm 1 ứng viên promote thẳng.
  Output: BẢNG NODE CANONICAL toàn tài liệu.
  |
C. CLUSTER CHỦ ĐỀ (cố định, chạy MỘT lần trên node canonical)
  Dùng cho: phân vùng/pass phụ của T2b + gom stage ở T4.
  |
M. MENTION MAP (cố định, code thuần, 2 kênh)
  Kênh exact (Aho-Corasick trên tên+alias)
  + kênh dense (ma trận cosine node x chunk, z-score, top-k)
  + hạt giống provenance (chunk_ids từ 2a).
  Output: chunk -> các node được nhắc; CẶP CHẠM xuyên cụm có trọng số.
  |
T2b. SUY LUẬN EDGE (ĐỊNH TUYẾN theo cấu trúc tài liệu)
  Có chương/heading rõ  -> pass chính theo CHƯƠNG (agent loop
                           tuần tự trong chương, các chương song song)
                           + pass phụ quét cụm chủ đề
  Phẳng/phi tuyến       -> pass chính theo CỤM CHỦ ĐỀ (mỗi cụm 1
                           phiên khép kín, song song tuyệt đối)
                           + pass phụ LIÊN CỤM trên cặp chạm
  Ngắn (<50 trang)      -> 1 phiên duy nhất, khỏi pass phụ
  Agent làm việc trên bảng node canonical — KHÔNG tạo node.
  Cycle chặn đồng bộ trong add_edge.
  |
T3. VALIDATE TOÀN CỤC (cố định + 1 pass self-review)
  Xử lý deferred/flags -> self-review -> check cycle toàn cục
  -> quality gate (thưa -> fallback thứ tự chương)
  -> transitive reduction -> gán cluster incremental cho node mới
  |
T4. LẮP LỘ TRÌNH (cố định)
  Layering Kahn -> stage = layer ∩ cluster (cap 5–8)
  -> enrichment (objectives, tóm tắt, quiz)
  -> gắn stage_id ngược về chunk -> (tùy chọn) human review
```

## 3. B0 — Ingestion chung (cố định)

- Parse layout-aware (Docling/Unstructured; python-docx cho DOCX; OCR fallback cho scan), giữ heading phân cấp, trang, bảng nguyên khối.
- Chunk theo ranh giới section, 300–800 token, overlap 10–15%. `order_index` tăng theo thứ tự xuất hiện — nền của doc-order prior.
- Embed (model đa ngữ: `bge-m3` / `multilingual-e5`) vào vector DB; embedding chunk này được **tái sử dụng** cho mention map ở bước M.

```json
{"chunk_id": "c_0042", "doc_id": "doc_001", "text": "...",
 "section_path": "Chương 3 > 3.2", "section_id": "s_3_2",
 "page": 41, "order_index": 42, "stage_id": null}
```

## 4. T1 — Extract ứng viên (cố định, song song)

- Stateless → mọi section chạy song song, model rẻ. Section ngắn gom thành **siêu section** (~1–2k token).
- Prompt: chỉ trích khái niệm được *giảng dạy/định nghĩa* trong section (không trích khái niệm nhắc thoáng qua — phần "nhắc" sẽ do mention map lo); output JSON nghiêm ngặt.
- Output là bộ khung input cho agent phía sau. Lưu ý: không phải thứ duy nhất agent nhìn thấy — mỗi lời gọi agent còn được bơm **nguyên văn các chunk liên quan** (mục 8.3, 8.4); `read_source_chunk` chỉ dành cho phần ngoài gói đã bơm.

```json
{
  "section_id": "s_3_2",
  "candidates": [
    {"candidate_id": "cand_s32_01", "name": "Overfitting",
     "aliases": ["quá khớp"], "description_draft": "...",
     "difficulty": 2, "chunk_ids": ["c_0040"], "first_order_index": 40}
  ],
  "proposed_edges": [
    {"from": "cand_s32_02", "to": "cand_s32_01",
     "evidence_chunk_ids": ["c_0042"], "note": "L2 giới thiệu như giải pháp cho overfitting"}
  ]
}
```

## 5. T2a — Merge theo cụm (entity resolution: blocking rẻ, matching kỹ)

Chạy trên **pool ứng viên toàn tài liệu**:

1. **Lọc tự động**: cặp similarity ≥ 0.95 (tên chuẩn hóa + embedding description) → merge thẳng bằng code.
2. **Đồ thị ứng viên**: edge = similarity ≥ ngưỡng thấp (~0.75) — thiên **recall**: cặp trùng lọt khỏi cụm thì không bao giờ được merge nữa; cặp thừa trong cụm agent sẽ tách — sai loại hai sửa được, loại một thì không.
3. **Gom cụm**: Leiden hoặc connected components.
4. **Agent kiểm định theo cụm**, song song, mỗi cụm một phiên.
5. **Cụm 1 ứng viên** (đa số): promote thẳng, không tốn agent.

**Rubric agent kiểm định** (system prompt): merge khi cùng khái niệm khác tên (alias/viết tắt/cách dịch), description tương thích; KHÔNG merge khi cha–con ("Regularization" vs "L2 Regularization" → tách node + đề xuất edge `requires`) hoặc trùng tên khác nghĩa (`read_source_chunk` kiểm tra, tối đa 2 lần/cụm); phân vân → `deferred`. Mỗi node chốt: tên chuẩn, gộp aliases, description hợp nhất, hợp `chunk_ids`, `first_order_index` nhỏ nhất.

**Ví dụ luồng một phiên 2a** (cụm 4 ứng viên):

```
INPUT: cand "Overfitting"(ch.3), "Quá khớp"(ch.5),
       "Regularization"(ch.3), "L2 Regularization"(ch.3)
       + description + trích đoạn evidence từng ứng viên
AGENT: Overfitting ≡ Quá khớp (bản dịch) → MERGE
       Regularization vs L2: nghi cha–con
       → read_source_chunk(c_0043): "L2 là một trong các kỹ thuật
         regularization" → xác nhận → TÁCH + suggest_edge
OUTPUT 1 batch: clusters_resolved [...], deferred [...]
EXECUTOR: tạo 3 node canonical; suggest_edge lưu làm ĐỀ XUẤT
          chuyển 2b xác minh (2a không tạo edge)
```

```json
{
  "clusters_resolved": [
    {"canonical_name": "Overfitting",
     "merge_candidates": ["cand_s32_01", "cand_s51_04"],
     "aliases": ["quá khớp"], "description": "...",
     "split_out": [{"candidate": "cand_s52_02", "reason": "L2 là khái niệm con",
                    "suggest_edge": {"from": "cand_s52_02", "to": "Overfitting"}}]}
  ],
  "deferred": [{"candidates": ["cand_s60_03", "cand_s61_01"], "reason": "..."}]
}
```

Output T2a: **bảng node canonical** — mỗi node đủ `chunk_ids` (provenance: nơi được *dạy*) từ mọi lần xuất hiện.

## 6. C — Cluster chủ đề (một lần chạy, ba chỗ dùng)

- Leiden trên node canonical (edge = co-occurrence cùng chunk/section + similarity description). Fallback HDBSCAN nếu edge thưa. Cụm > 12 node → Leiden đệ quy chia nhỏ; cụm 1–2 node → sáp nhập cụm gần nhất. **Cap kích thước này là điều kiện để "mỗi cụm 1 phiên" ở T2b khả thi** (input một cụm luôn vừa một prompt).
- **Ba chỗ dùng**: (1) đơn vị phân vùng pass chính nhánh 2; (2) pass phụ quét cụm của nhánh 1; (3) gom stage ở T4.
- Sau T3, node mới chỉ **gán incremental** vào cluster gần nhất theo embedding — không chạy lại Leiden (cluster dựa ngữ nghĩa node, không phụ thuộc edge; T3 chỉ đụng edge).
- **Tránh nhầm**: cụm ở đây là cụm *chủ đề* (các khái niệm khác nhau, liên quan). Cụm ở T2a là cụm *ứng viên nghi trùng* của cùng một khái niệm — sau kiểm định co về 1 node, không dùng suy luận edge được.

## 7. M — Mention map (code thuần, hai kênh)

**Vấn đề cần giải**: `chunk_ids` của node là **provenance** — trả lời "khái niệm được *dạy* ở đâu". Pass liên cụm cần **mention map** — "khái niệm được *nói đến* ở đâu", kể cả nơi chỉ nhắc tên hoặc diễn đạt lại. Cặp xuyên cụm bản chất là "dạy chỗ này, nhắc lại chỗ kia" — dùng provenance để dò chạm là tự bịt mắt.

**Kênh 1 — Exact match (precision cao, gần miễn phí):**
- Aho-Corasick trên toàn bộ tên chuẩn + aliases; chuẩn hóa lowercase/bỏ dấu; bắt buộc khớp trọn từ theo word-boundary ("gradient" lẻ không khớp "Gradient Descent"); loại node tên quá chung chung khỏi việc quét (stop-word khái niệm).
- Chạm do exact match được tin ở **trọng số cao**.

**Kênh 2 — Dense (cosine, recall cao — bắt paraphrase):**
- Tính **một phép nhân ma trận duy nhất**: embedding description của mọi node × embedding của mọi chunk (cả hai đã có sẵn: chunk từ B0, node embed một lần sau 2a). 250 node × 1.500 chunk ≈ 375k ô — mili-giây. Tính hết rồi lọc luôn rẻ hơn tính chọn lọc.
- Lọc **theo từng hàng (node)**: z-score nội bộ hàng + top-k (k≈10). Không dùng ngưỡng cosine tuyệt đối chung (scale lệch giữa node description dài/ngắn). Ô sống sót = mention mềm, trọng số = z-score.
- Vai trò: bắt các ca văn bản viết "quy tắc dây chuyền" thay vì "chain rule", "hàm chi phí" thay vì "hàm mất mát" — đặc biệt quan trọng với tiếng Việt (một khái niệm nhiều cách gọi). Cái giá: cosine đo *độ gần chủ đề* chứ không đo *sự nhắc tới* → có mention ảo; chấp nhận được vì agent phía sau đòi evidence sẽ lọc — false positive tốn một lần xét, false negative mất vĩnh viễn.

**Hạt giống provenance**: các cặp (node, chunk) trong `chunk_ids` ghi thẳng vào mention map với độ tin tuyệt đối, khỏi chấm điểm.

**Ghi cặp chạm** (một lượt quét, mọi cặp cụm cộng dồn đồng thời — cặp cụm là *đầu ra* của phép quét, không phải đầu vào):

```
với mỗi chunk c: xét các node sống sót có mặt tại c
  cặp (n cụm X, m cụm Y≠X) → cặp chạm, trọng số w = min(w_n, w_m)
  → cộng dồn w vào sổ cặp cụm (X, Y)
sổ (X,Y) ≥ ngưỡng → cặp cụm vào danh sách gọi agent
boundary concept = node góp mặt trong cặp chạm
```

**Nâng cấp học thuật (tùy chọn, theo khung entity linking):** tầng disambiguation cho tên đa nghĩa — so embedding *câu chứa mention* với description các node ứng viên, thay cho luật stop-word cứng (tham chiếu kiến trúc bi-encoder kiểu BLINK). Ưu tiên làm sau khi đo thấy cần.

**Tự giàu alias**: khi agent 2b xác nhận một cặp đến từ paraphrase, nó được đề xuất bổ sung alias cho node ("quy tắc dây chuyền" → alias của Chain Rule) — lần chạy sau kênh exact tự bắt được.

Mention map cũng là hạ tầng chạy chiều ngược cho `flag_missing_node` (cụm từ lặp nhiều không khớp node nào → nghi 2a sót) — viết thành module dùng chung.

## 8. T2b — Suy luận edge (định tuyến theo cấu trúc tài liệu)

### 8.1 Ngữ nghĩa edge

- Loại edge duy nhất tham gia lộ trình: `requires`. Quy ước chiều: `add_edge(from: A, to: B)` = "muốn hiểu A phải biết B trước" → topo sort xếp B tầng sớm hơn.
- Chỉ tạo edge tiên quyết **trực tiếp**; suy diễn xa để transitive reduction lo.
- Cạnh similarity (2a), co-occurrence (C), mention (M) là cấu trúc phụ trợ của code — không nằm trong graph tiên quyết. Muốn hiển thị "liên quan" trên UI: thêm loại `relates_to`, không tham gia topo.

### 8.2 Định tuyến (heuristic ngay sau parse)

| Cấu trúc tài liệu | Pass chính | Pass phụ (bù điểm mù) |
|---|---|---|
| Có chương/heading rõ | Theo **chương**: agent loop tuần tự trong chương, các chương song song; heading lộn xộn → gom partition ~10–20k token | Quét **cụm chủ đề**: cặp node cùng cụm chưa có đường nối |
| Phẳng/phi tuyến | Theo **cụm chủ đề**: mỗi cụm 1 phiên khép kín — stateless, song song tuyệt đối | **Liên cụm** trên cặp chạm từ mention map |
| Ngắn (< 50 trang) | 1 phiên duy nhất | Không cần |

Hai nhánh là ảnh gương: pass chính đi trục nào thì mù với quan hệ vắt ngang trục đó; pass phụ = đi lại một lượt theo trục còn lại, nhưng chỉ ở phần rìa nghi ngờ. Nhánh chương hụt edge cùng chủ đề nằm xa nhau; nhánh cụm hụt edge xuyên cụm mà tài liệu dạy tường minh. Lưu ý nhánh chương: nhờ node canonical toàn cục, edge *xuyên chương* sinh tự nhiên ngay pass chính (section chương 8 nhắc khái niệm chương 3 → resolve sẵn, evidence tại chỗ).

### 8.3 Nhánh chương — agent loop

Input mỗi iteration (= 1 siêu section), bơm sẵn: (1) **nguyên văn các chunk của section** (1–3 chunk — nhờ đó bắt được khái niệm văn bản nhắc mà bảng node thiếu → `flag_missing_node`); (2) nodes trong section đã resolve về canonical; (3) proposed edges từ T1 kèm evidence; (4) edge hiện có liên quan. Loop tuần tự vì graph chương lớn dần theo mạch đọc (state truyền iteration trước → sau); checkpoint mỗi iteration; dừng khi hết section — bounded tự nhiên.

### 8.4 Nhánh cụm — hai đợt sóng song song

```
ĐỢT 1 — NỘI CỤM (mỗi cụm 1 phiên, bắn song song):
  gói input cụm K = {node của K (desc, first_order_index),
                     nguyên văn evidence chunks của các node,
                     edge nội cụm đã có}
  → phiên khép kín: đọc gói → (read_source_chunk 0–2 lần)
    → 1 batch edge → executor commit (cycle nội batch, retry 1 lượt)
  Cụm nào xong commit cụm đó, không ai chờ ai.

GIỮA HAI ĐỢT — CODE THUẦN:
  mention map (bước M) đã có → chốt sổ cặp cụm, cặp ≥ ngưỡng
  → danh sách phiên liên cụm; lọc thêm bằng REACHABILITY:
  cặp chạm (n,m) đã có đường đi gián tiếp trong DAG → loại
  (edge trực tiếp đằng nào cũng bị transitive reduction xóa)

ĐỢT 2 — LIÊN CỤM (mỗi cặp cụm 1 phiên, bắn song song):
  input CHỈ gồm phần rìa — xem hồ sơ 8.5
  → executor commit → bàn giao T3 (cycle toàn cục bắt vòng
    xuyên vùng do các phiên song song vô tình tạo khi ghép)
```

LLM chỉ xuất hiện ở hai đợt sóng; mọi điều phối giữa chúng là code. Không agent nào "đi" giữa các cụm — thứ di chuyển là dữ liệu.

### 8.5 Hồ sơ phiên liên cụm (input theo CẶP, không phải hai danh sách rời)

Cặp chạm là *giả thuyết* code đã lập — đưa theo cặp để agent chỉ phán quyết từng hồ sơ, không phải tự tái ghép:

```json
{
  "cluster_pair": ["K1_toan_nen", "K2_toi_uu"],
  "node_profiles": {
    "cpt_daoham": {"desc": "...", "first_order_index": 12, "cluster": "K1"},
    "cpt_gd":     {"desc": "...", "first_order_index": 120, "cluster": "K2"},
    "cpt_lr":     {"desc": "...", "first_order_index": 125, "cluster": "K2"}
  },
  "suspected_pairs": [
    {"pair": ["cpt_gd", "cpt_daoham"], "weight": 2.4,
     "source": "exact+cosine", "evidence_chunks": ["c_0120"]},
    {"pair": ["cpt_lr", "cpt_daoham"], "weight": 1.2,
     "source": "cosine", "evidence_chunks": ["c_0125"]}
  ],
  "chunk_texts": {"c_0120": "nguyên văn...", "c_0125": "nguyên văn..."},
  "existing_edges": ["cpt_lr -> cpt_gd (0.7)"]
}
```

- Cặp đưa vào **vô hướng** — xác định chiều là việc của agent (câu chữ + `first_order_index`).
- `weight`/`source` cho agent biết chạm cứng (exact, đáng tin) vs chạm mềm (cosine, dễ nhiễu chủ đề) để phân bổ hoài nghi.
- `existing_edges` để từ chối edge trực tiếp khi đường gián tiếp đã có.
- **Kỷ luật hồ sơ**: agent không tạo edge ngoài `suspected_pairs`; thấy quan hệ ngoài danh sách → flag cho vòng review. Mọi edge sinh ra truy vết được về đúng một cặp chạm có nguồn gốc.

### 8.6 Bốn phán quyết của agent trên mỗi cặp

1. **Tạo edge** — bắt buộc kèm: chiều, confidence theo rubric, evidence chunk.
2. **Từ chối — không có quan hệ trực tiếp** (chỉ gần chủ đề; chunk không đặt quan hệ tiên quyết).
3. **Từ chối — đã có đường gián tiếp** (edge trực tiếp thừa).
4. **Treo (`deferred`)** — evidence mơ hồ, đẩy lên T3.

Agent là "sơ thẩm" tri thức từng cặp; executor và T3 giữ chung thẩm về cấu trúc.

### 8.7 Bộ tool

| Tool | Bản chất | Ghi chú |
|---|---|---|
| `search_similar_node(name, desc)` | Embedding search trên bảng node canonical | Resolve tham chiếu về node chuẩn |
| `add_edge(from, to, confidence, evidence_chunk_ids)` | Tạo cạnh `requires` | `check_cycle` đồng bộ bên trong; thiếu evidence → từ chối; cạnh tạo cycle → chặn kèm thông tin cycle để agent chọn bỏ/thay cạnh cũ confidence thấp hơn |
| `update_description(node, append, evidence)` | Bổ sung mô tả có evidence | Không sửa đè |
| `read_source_chunk(chunk_id)` | Đọc chunk **ngoài gói đã bơm** (tham chiếu "xem mục 2.1") | Ngân sách 2 lần/**iteration** (mỗi phiên/mỗi section — không phải cả pipeline) |
| `suggest_alias(node, alias, evidence)` | Đề xuất alias mới khi xác nhận paraphrase | Nuôi kênh exact match của lần chạy sau |
| `flag_missing_node(name, evidence)` | Van an toàn: báo khái niệm 2a sót | Không tự tạo node — hàng chờ T3 |

### 8.8 Rubric confidence

**0.9+**: văn bản nói rõ ("để hiểu X cần nắm Y") hoặc Y trong định nghĩa của X. **0.7**: suy luận mạnh từ mạch trình bày. **0.5**: suy đoán. **< 0.5: không tạo.** Edge ngược thứ tự tài liệu: chỉ khi evidence tường minh, trừ 0.1.

### 8.9 Giao thức batch + executor

Mỗi iteration/phiên kết thúc bằng **một batch JSON duy nhất**:

```json
{
  "ops": [
    {"op": "add_edge", "from": "cpt_backprop", "to": "cpt_chainrule",
     "confidence": 0.9, "evidence_chunk_ids": ["c_0232"],
     "rationale": "backprop áp dụng chain rule để lan truyền"},
    {"op": "suggest_alias", "node": "cpt_chainrule",
     "alias": "quy tắc dây chuyền", "evidence": "c_0232"}
  ],
  "rejected_pairs": [
    {"pair": ["cpt_lr", "cpt_daoham"], "verdict": "indirect_path_exists"}
  ],
  "flags": [{"missing_node": "Bias-Variance Tradeoff", "evidence": "c_0044"}]
}
```

Executor: thực thi tuần tự; op lỗi (cycle, evidence không tồn tại, id sai) trả lỗi đúng op; **1 lượt retry duy nhất**, op đã commit không chạy lại. Edge đề xuất từ T1/2a phải được **xác minh lại**, không copy nguyên. `rejected_pairs` được log — phục vụ đo đạc chất lượng bộ dò chạm (tỉ lệ từ chối cao → siết ngưỡng mention map).

### 8.10 Tối ưu chi phí pass liên cụm

Quy mô tham chiếu (giáo trình 500 trang, ~250 node, 25–35 cụm): sau lọc "liên kết đủ mạnh" còn ~30–60 phiên liên cụm ≈ 10–20% tổng lời gọi pipeline, mỗi phiên nhẹ (chỉ phần rìa). Ba chiêu ép thêm, theo độ đáng làm:

1. **Reachability pruning** (đã ghi ở 8.4): loại cặp chạm đã có đường gián tiếp — BFS trên graph vài trăm node, gần miễn phí, thường loại được phần lớn cặp.
2. **Gộp lô**: các cặp cụm chỉ có 1–2 cặp chạm lẻ → gom ~10 cặp chạm (từ nhiều cặp cụm) vào một lời gọi — bản chất câu hỏi là trên từng cặp node.
3. **Model rẻ cho pass này**: nhiệm vụ hẹp (xác nhận có/không + chiều, evidence trước mặt).

Chi phí pass này tỷ lệ với độ *đan xen* của tài liệu — tiền tiêu đúng chỗ tài liệu thật sự cần phân tích xuyên vùng.

## 9. T3 — Validate toàn cục

1. **Xử lý tồn đọng**: chốt `deferred` (2a + 2b) với toàn cảnh graph; xét `flag_missing_node` — tạo node bổ sung nếu evidence đủ; duyệt `suggest_alias`.
2. **Self-review 1 pass**: duplicate sót, edge thiếu evidence, mô tả mâu thuẫn.
3. **Check cycle toàn cục**: trong từng vùng cycle đã chặn tại `add_edge`, nhưng edge từ các vùng ghép lại có thể tạo vòng xuyên vùng → cắt edge confidence thấp nhất mỗi vòng, log cho human review.
4. **Quality gate**: edge `requires` < ~0.5 × số node hoặc > 60% node cô lập → tài liệu không có cấu trúc tiên quyết rõ → **fallback**: lộ trình theo thứ tự chương + cluster chủ đề; graph chỉ hiển thị liên quan, không khóa/mở.
5. **Transitive reduction** (NetworkX).
6. **Gán cluster incremental** cho node mới (tái sử dụng kết quả C).

## 10. T4 — Lắp lộ trình

1. **Topological layering (Kahn)**: lớp 1 = node in-degree 0; gỡ lớp, lặp. Node cùng lớp học song song được.
2. **Stage = layer ∩ cluster**, cap 5–8 concept/stage. LLM pass cuối đặt tên stage + sắp thứ tự concept bên trong — **không** đổi thứ tự giữa các stage.
3. **Enrichment** (offline, từ chunk_ids của stage): objectives, tóm tắt 150–300 từ, quiz 5–8 trắc nghiệm (đáp án + concept_id) + 1–2 tự luận có rubric, estimated_minutes.
4. **Gắn stage_id ngược về chunk** trong vector DB (chunk thuộc nhiều stage → stage sớm nhất + mảng `all_stage_ids`) — mắt xích cho scoped RAG pha học.
5. **(Tùy chọn) Human review**: sửa graph/stage, version hóa (`graph_version`).

## 11. Vận hành

- **Song song hóa**: T1 song song toàn bộ; 2a song song theo cụm; 2b song song theo chương hoặc hai đợt sóng cụm; chỉ loop trong một chương là tuần tự. Giáo trình 500 trang: ~10–15 phút (so ~30–60 phút tuần tự thuần), token gần như không đổi.
- **Mở dần giai đoạn**: edge hầu như trỏ ngược về trước → stage đầu ổn định sớm; cho user học stage 1 (`graph_version: partial`) khi phần sau còn chạy.
- **Tái lập**: temperature 0; log mọi tool call thành **event log** → replay để debug, so sánh 2 lần chạy; kiểm tra cấu trúc nằm trong code.
- **Ba tầng tiếp cận văn bản của agent**: gói bơm sẵn (chunk của đơn vị đang xử lý — luôn có) → van `read_source_chunk` (2 lần/iteration, với ra ngoài gói) → không có tầng "duyệt tự do".
- **Pha B (tham chiếu spec tổng)**: tutor agent scoped RAG (`stage_id <= current`), assessment agent mastery theo concept, unlock/test-out, adaptive.

## Phụ lục A — Ánh xạ nhãn pipeline gốc

| Nhãn gốc | Vị trí luồng mới |
|---|---|
| A1–A2, A3' | B0 |
| A3 extract | T1 |
| A4 merge + A5 description | T2a |
| A6 semantic graph | Đồ thị ứng viên của 2a + bước M |
| A7 cluster | Bước C (một lần, giữa 2a và 2b) |
| A8a/A8b | T2b (pass chính + pass phụ) |
| A9b remove cycle | Trong `add_edge` của 2b + cycle toàn cục ở T3 |
| A9a gate, A9c transitive reduction | T3 |
| A10–A12 | T4 |

## Phụ lục B — Khi nào dùng, và hướng nghiên cứu

| Tình huống | Lựa chọn |
|---|---|
| Giáo trình tuyến tính chuẩn, cần rẻ nhất | Pipeline tuyến tính gốc đủ tốt |
| Tài liệu dài, tham chiếu chéo dày, phi tuyến | Luồng này |
| Đề tài nghiên cứu | Chạy cả hai, benchmark graph + chi phí + tái lập |

**Các điểm thí nghiệm cho đề tài** (bám khung CPRP — concept prerequisite relation prediction, vốn được mô hình hóa thành link prediction trên đồ thị khái niệm):
1. So sánh candidate generator xuyên cụm: co-occurrence/mention map vs RefD vs GNN link prediction (GAE/VGAE, directed GNN) vs hỏi LLM trực tiếp — đo recall edge gold trên mỗi đơn vị chi phí, trên tài liệu tiếng Việt.
2. So sánh mention detection: exact match vs + dense (cosine) vs + disambiguation — đo recall mention, đặc biệt với paraphrase tiếng Việt.
3. Pipeline cố định vs luồng agent này: chất lượng graph, chi phí token, độ tái lập.
