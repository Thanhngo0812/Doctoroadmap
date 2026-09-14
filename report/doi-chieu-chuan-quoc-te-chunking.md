# Đối chiếu pipeline index với chuẩn khoa học và thực hành quốc tế

Vòng 11 · 2026-08-29 · Đối tượng: pha B0 (parse → chuẩn hoá → cắt chunk) của `doc2roadmap`
Nguồn ngoài: báo cáo kỹ thuật Chroma, Anthropic Contextual Retrieval, Jina Late Chunking (arXiv 2409.04701),
tài liệu Docling, các khảo sát chunking 2025–2026.

## 1. Phán quyết

**Kiến trúc cắt chunk của dự án trùng khớp với thiết kế tham chiếu của ngành, và ở vài điểm vượt chuẩn.**
Nhưng phải nói rõ phạm vi: cái đang có là **nửa đầu** của một pipeline index — parse và cắt. Nửa sau
(embed, chỉ mục, truy hồi) chưa tồn tại, nên câu hỏi *"đã chuẩn chưa"* chỉ trả lời được cho nửa đầu.

| Trục | Kết luận |
|---|---|
| Thiết kế cắt chunk | ✅ **Trùng khuôn tham chiếu** — Docling HybridChunker |
| Cỡ chunk | ✅ **Đúng vùng tối ưu** — median 256 token trên toàn corpus |
| Xử lý bảng | ✅ **Đúng khuyến nghị** — nguyên khối, markdown, không cắt ngang |
| Overlap | ✅ **Đúng, và đúng vì lý do đúng** |
| Tính tất định, kỷ luật bất biến | 🟢 **Vượt chuẩn** — hiếm hệ thống nào làm |
| Ngữ cảnh khi embed | 🔴 **Khoảng trống lớn nhất** — đã hoãn, nhưng bằng chứng ngoài rất mạnh |
| Truy hồi lai (dense + BM25) | 🟡 Chưa có trong kế hoạch |
| **Đo lường chất lượng truy hồi** | 🔴 **Khoảng trống khoa học thật sự** — chưa có phép đo nào |
| Chunk quá nhỏ | 🟡 12% corpus < 50 token, riêng slide 32% |

---

## 2. Chỗ đã đúng chuẩn

### 2.1 Cấu trúc trước, token sau — đúng khuôn tham chiếu

Docling định nghĩa `HybridChunker` là *"tokenization-aware refinements on top of document-based
hierarchical chunking"*: xuất phát từ cắt theo cấu trúc tài liệu, rồi **một lượt tách** phần vượt token
và **một lượt gộp** các chunk nhỏ liền nhau **cùng heading**.

Đó chính xác là thuật toán của dự án: gộp leaf block cùng section quanh mục tiêu 256 token, tách khi
vượt trần. Dự án đến cùng thiết kế này qua chín vòng review từ dữ liệu thật, không phải sao chép — và
điều đó có giá trị riêng: mọi tham số đều có lý do đo được đứng sau.

Khảo sát 2025–2026 xác nhận hướng này: cắt theo cấu trúc/đệ quy đạt IoU trung bình 0,088 so với 0,067
của cắt cố định — **hơn 31%**, và khoảng cách giữ nguyên bất kể overlap.

Đáng chú ý ngược lại: **cắt theo ngữ nghĩa (semantic chunking) không phải là chuẩn vàng** như nhiều
bài blog nói. Nghiên cứu Vectara (NAACL 2025) thấy cắt cố định **thắng** cắt ngữ nghĩa trên dữ liệu
thực tế; một benchmark 2026 xếp cắt đệ quy 512 token đứng đầu (69%) còn cắt ngữ nghĩa 54%. Dự án
**không** đi đường ngữ nghĩa — và đó là lựa chọn đúng, không phải thiếu sót.

### 2.2 Cỡ chunk nằm đúng vùng tối ưu

Đo lại toàn corpus bốn tài liệu:

```
tai lieu         chunk  median   p10   p90   max  <50tok
nhap-mon-ml         41     261    27   338   400   17%
xstk-ch3-1         126     265    91   316   628    4%
baocao-canhan       26     154    52   240   263    7%
naive-bayes         40     104    24   340   513   32%
TOAN CORPUS        233     256    41   318            12%
```

**Median 256 token** — đúng con số mục tiêu, và đúng vùng khuyến nghị:

- Báo cáo Chroma: chunk **200 token** cho precision và IoU cao nhất; chunk quá lớn làm loãng thông tin.
- NVIDIA: **256–512** token cho câu hỏi dữ kiện.
- Chroma phê phán thẳng mặc định phổ biến của OpenAI — **800 token, overlap 400** — cho recall dưới
  trung bình và điểm thấp nhất ở mọi chỉ số còn lại.

Dự án ở 256, không ở 800. Đúng phía.

### 2.3 Bảng: nguyên khối, markdown — đúng khuyến nghị

Thực hành được khuyến nghị: *bảng là đơn vị ngữ nghĩa nguyên tử, không bao giờ cắt mà không giữ header*;
và *dựng markdown từ biểu diễn có cấu trúc* thay vì làm phẳng thành chữ. Dự án làm cả hai — quyết định
"không cắt bảng, chấp nhận vượt trần 2048" của bạn ở vòng 6 trùng khuyến nghị ngành, và Docling cũng
mở `repeat_table_header` cho cùng mối lo.

### 2.4 Overlap: không có, và đó là đúng

Dự án chỉ dùng `sentence_overlap` **khi một khối đơn bị tách vì quá dài** — chunk gộp không có overlap.
Nghe như thiếu, thực ra khớp bằng chứng:

- Recall chỉ nhích 0,711 → 0,724 khi overlap tăng 0% → 60%, đổi lại **precision giảm nhiều hơn**.
- Chroma: bỏ overlap **cải thiện** IoU.
- Khuyến nghị chung: overlap không nên vượt 25% cỡ chunk.

Lý do sâu hơn: overlap là **liều thuốc chữa triệu chứng** cho việc cắt mù làm gãy câu giữa chừng. Cắt
theo cấu trúc thì ranh giới đã trùng ranh ngữ nghĩa, nên bệnh không phát sinh. Dự án đã đi thẳng vào
nguyên nhân — nối câu qua trang, nối run định dạng — thay vì phủ overlap lên trên.

---

## 3. Chỗ vượt chuẩn ngành

**Tính tất định và định danh theo nội dung.** Hầu hết pipeline RAG sản xuất cắt lại là đổi hết ID, kéo
theo phải embed lại toàn bộ và mọi trích dẫn cũ gãy. Dự án băm ID theo *nội dung + đường dẫn*, đóng
băng cây parse thành artifact có phiên bản, `adapter_version` gác việc parse lại. Đây là kỷ luật của
**hệ thống lưu trữ theo nội dung**, không phải của pipeline RAG thông thường — tôi không tìm thấy tài
liệu ngành nào coi đây là thực hành phổ biến. Nó sẽ trả lương ở B0.5: sửa một chương chỉ phải embed lại
chunk của chương đó.

**Bộ bất biến I1–I25 và số vàng bốn tài liệu.** Ngành đo *chất lượng truy hồi* (mục 4.1 dưới), rất hiếm
khi đo *tính đúng đắn cấu trúc* của tầng cắt. Việc ghim `char_span` khớp toàn văn, không trùng định
danh, mọi vượt trần phải khai lý do — là mức kỹ thuật cao hơn mặt bằng.

**Marker + tham chiếu ngoài khoá băm (ADR 0002).** Đây là câu trả lời cho một bài toán ngành đang loay
hoay: khảo sát chunking đa phương thức khuyến nghị *"coi bảng, hình, chữ là node riêng có quan hệ phân
cấp"* thay vì làm phẳng. Dự án làm đúng thế, và còn tách được danh tính ra khỏi khoá băm nên thêm/bớt
tham chiếu không phá định danh chunk.

---

## 4. Khoảng trống thật

### 4.1 🔴 Chưa có phép đo chất lượng truy hồi nào — khoảng trống khoa học lớn nhất

Số vàng bốn tài liệu là **test hồi quy**: nó bắt thay đổi ngoài ý muốn. Nó **không** trả lời được câu
hỏi khoa học: *cách cắt này có làm truy hồi tốt hơn cách khác không?*

Toàn bộ nghiên cứu được dẫn ở trên đều dựa trên bộ câu hỏi vàng và các chỉ số **recall@k, precision,
IoU, Precision_Ω**. Không có chúng thì mọi khẳng định "chunk của chúng ta tốt" là niềm tin kỹ thuật,
không phải kết luận đo được. Ngay cả bài học ngành cũng nhấn: **benchmark end-to-end quan trọng hơn
benchmark chỉ đo truy hồi** — recall cao không bảo đảm câu trả lời đúng.

Cụ thể dự án đang thiếu: một bộ ~50 câu hỏi trên bốn tài liệu, mỗi câu ghim đoạn văn chứa đáp án; rồi
đo recall@k và IoU. Có nó thì mọi tranh luận sau này về cỡ chunk, ngữ cảnh, overlap **kết thúc bằng số**
thay vì bằng lý lẽ. Đây là việc đáng làm **trước** B0.5, vì nó là thước đo cho chính B0.5.

Có công cụ sẵn: gói `chunking_evaluation` của Chroma cài đặt đúng bộ chỉ số này.

### 4.2 🔴 Ngữ cảnh khi embed — đã hoãn, nhưng bằng chứng ngoài rất mạnh

Chunk mang `section_path` như siêu dữ liệu nhưng **văn bản đem embed không có tiêu đề**. Kế hoạch hoãn
quyết định này sang B0.5 với ghi chú *"cần A/B"* — hoãn là hợp lý, nhưng bằng chứng ngoài đã nghiêng hẳn:

- **Docling** đặt `contextualize()` làm mặc định của mọi chunker: *"serialization giàu siêu dữ liệu của
  chunk, dùng để nạp cho mô hình embedding"* — tức tiêu đề và chú thích **được ghép vào** trước khi embed.
  Dự án đang dùng Docling để parse nhưng **không** dùng khuôn contextualize của nó.
- **Anthropic Contextual Retrieval**: ghép 50–100 token ngữ cảnh vào mỗi chunk giảm **35%** tỉ lệ truy
  hồi hỏng (5,7% → 3,7%); cộng BM25 ngữ cảnh giảm **49%**; cộng rerank giảm tới **67%**.

Chi tiết đáng chú ý cho dự án: Anthropic ghi nhận *"thêm tóm tắt tài liệu chung vào chunk cho lợi ích
rất hạn chế"* — cái hiệu quả là **ngữ cảnh riêng của từng chunk**. `section_path` (`CHƯƠNG III > B. Bài
tập Kiểm soát Lưu lượng`) đúng là loại ngữ cảnh riêng đó, và dự án đã có sẵn — chỉ chưa ghép.

Lưu ý ngược: ghép tiêu đề làm **đổi văn bản chunk**, mà văn bản nằm trong khoá băm ⇒ đổi toàn bộ định
danh. Nên quyết định này phải chốt **trước** lần embed đầu tiên, không phải sau. Đây là ràng buộc do
chính thiết kế tất định sinh ra, và nó biến "hoãn để A/B" thành việc phải làm **ngay đầu B0.5**.

### 4.3 🟡 Truy hồi lai chưa có trong kế hoạch

`spec-preview` chỉ nói embed vào vector DB. Bằng chứng cho lai dense + BM25 khá nhất quán: NDCG tăng
**26–31%** so với dense đơn thuần; recall@1000 từ ~0,87 lên 0,98. Lý do khớp đúng loại tài liệu của dự
án: dense hỏng ở **thuật ngữ chính xác, ký hiệu, tên riêng** — mà giáo trình xác suất thống kê đầy
`P(A|B)`, `Naïve Bayes`, `sync.Mutex`. Hạ tầng cũng sẵn: nếu dùng Postgres thì `tsvector` có ngay.

Không phải việc của B0, nhưng nên ghi vào kế hoạch B0.5 để khỏi phải làm lại chỉ mục.

### 4.4 🟡 Chunk quá nhỏ — 12% corpus, riêng slide 32%

28/233 chunk dưới 50 token. Đây đúng là hình dạng lỗi mà nghiên cứu cảnh báo: FloTorch ghi nhận chunk
trung bình **43 token** *"truy hồi sạch nhưng cho LLM quá ít ngữ cảnh để trả lời đúng"*.

Với slide (32%) nguyên nhân đã biết và đã ghi: F37, mỗi slide một section, chưa có quyết định thể loại.
Với hai giáo trình, chunk nhỏ chủ yếu là tiêu đề đứng lẻ và mảnh cuối section. Cách chữa rẻ nhất chính
là 4.2 — ghép ngữ cảnh tiêu đề nâng luôn sàn token của chunk nhỏ. Hai vấn đề cùng một mũi tên.

### 4.5 🟢 Late chunking — ghi để biết, không áp dụng được

Late chunking (Jina, arXiv 2409.04701) chạy transformer trên **toàn văn trước**, rồi mean-pool theo
từng chunk, nên mỗi embedding mang ngữ cảnh cả tài liệu. Nó giải đúng bài toán 4.2 ở tầng kiến trúc.

**Không dùng được ở đây**: nó đòi mô hình embedding ngữ cảnh dài **dùng mean pooling và truy cập được
tầng token** — tức mô hình tự host. Gemini chỉ trả vector cuối qua API. Đây là hệ quả nữa của ràng buộc
đã ghi trong bộ nhớ dự án (Gemini không có tokenizer offline). Ghi lại để nếu sau này đổi sang mô hình
tự host thì biết có lựa chọn này.

---

## 5. Đề xuất, theo thứ tự

| # | Việc | Vì sao thứ tự này |
|---|---|---|
| 1 | **Bộ câu hỏi vàng + recall@k, IoU** trên bốn tài liệu | Không có thước đo thì mọi việc sau là đoán. Phải có **trước** B0.5 vì nó chấm điểm B0.5 |
| 2 | **Chốt ngữ cảnh khi embed** (ghép `section_path` vào văn bản) | Bằng chứng mạnh (−35% lỗi truy hồi); và **phải chốt trước lần embed đầu** vì nó đổi định danh chunk |
| 3 | Ghi **truy hồi lai** vào kế hoạch B0.5 | +26–31% NDCG; đổi chỉ mục sau tốn hơn nhiều |
| 4 | Quyết định thể loại slide (F37) | Nguồn chính của chunk quá nhỏ; đã treo từ vòng 9 |
| 5 | Ghi ADR cho ba lựa chọn đã đúng | Không cắt ngữ nghĩa, không overlap mù, bảng nguyên khối — có bằng chứng ngoài rồi, ghi lại để đợt sau khỏi bàn lại |

## 6. Kết luận thẳng

**Nửa đầu pipeline — parse và cắt — đạt chuẩn ngành, và ở tính tất định thì vượt.** Không có quyết định
thiết kế nào đi ngược bằng chứng ngoài; vài quyết định trông "thiếu" (không overlap, không cắt ngữ
nghĩa) thật ra là **đúng theo nghiên cứu mới nhất**, dù dự án đến đó bằng đường đo đạc riêng.

**Khoảng cách thật không nằm ở thuật toán mà ở phép đo.** Dự án có kỷ luật kỹ thuật hiếm thấy — 25 bất
biến, số vàng, mười vòng review — nhưng chưa có một con số nào nói *truy hồi tốt đến đâu*. Đó là ranh
giới giữa "kỹ thuật chặt chẽ" và "được xác thực khoa học". Bù khoảng cách đó là việc một đợt, và nên là
đợt kế tiếp.

---

## Nguồn

- [Evaluating Chunking Strategies for Retrieval — Chroma Technical Report](https://www.trychroma.com/research/evaluating-chunking) (Smith & Troynikov, 07/2024)
- [chunking_evaluation — bộ công cụ đi kèm báo cáo Chroma](https://github.com/brandonstarxel/chunking_evaluation)
- [Contextual Retrieval in AI Systems — Anthropic](https://www.anthropic.com/engineering/contextual-retrieval)
- [Late Chunking: Contextual Chunk Embeddings Using Long-Context Embedding Models — arXiv 2409.04701](https://arxiv.org/html/2409.04701v2)
- [Chunking — Docling documentation](https://docling-project.github.io/docling/concepts/chunking/)
- [Hybrid chunking — Docling](https://docling-project.github.io/docling/examples/hybrid_chunking/)
- [Finding the Best Chunking Strategy for Accurate AI Responses — NVIDIA](https://developer.nvidia.com/blog/finding-the-best-chunking-strategy-for-accurate-ai-responses/)
- [RAG Chunking Strategies: The 2026 Benchmark Guide — PremAI](https://www.premai.io/blog/rag-chunking-strategies-the-2026-benchmark-guide/)
- [Our Approach to Table Chunking — Ragie](https://www.ragie.ai/blog/our-approach-to-table-chunking)
- [Mastering RAG: Precision techniques for table-heavy documents — KX](https://kx.com/blog/mastering-rag-precision-techniques-for-table-heavy-documents/)
- [Hybrid Search for RAG: BM25, SPLADE, and Vector Search Combined — PremAI](https://www.premai.io/blog/hybrid-search-for-rag-bm25-splade-and-vector-search-combined/)
- [Best Practices in RAG Evaluation — Qdrant](https://qdrant.tech/blog/rag-evaluation-guide/)
- [Chunking Strategies for Multimodal AI Systems — arXiv 2512.00185](https://arxiv.org/pdf/2512.00185)
