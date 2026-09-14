# Nghiên cứu A3 / A3' — Trích xuất thực thể: đối chiếu spec với nghiên cứu khoa học

Vòng 12 · 2026-08-29 · Đối tượng: `doc/spec-addendum.md` mục A3 (trích khái niệm), A3' (nhánh vector),
và biến thể Tầng 1 / Tầng 2a. Chưa viết dòng mã nào — đây là khảo sát trước khi spec.

Nguồn: khảo sát ACM Computing Surveys 2025 về Prerequisite Relation Learning, khung EDC
(arXiv 2404.03868), Entity Resolution bằng in-context clustering (PACMMOD 2025), Microsoft GraphRAG /
LazyGraphRAG, GraphRAG-Bench và các nghiên cứu về structured output, self-verification.

---

## 1. Phát hiện quan trọng nhất: bài toán này **đã có tên và đã có cả một ngành nghiên cứu**

Spec gọi A3 là "trích khái niệm" và A8 là "suy luận quan hệ tiên quyết". Trong văn liệu, hai việc này
hợp thành **Prerequisite Relation Learning (PRL)** — một bài toán đã được nghiên cứu từ 2012, có
**khảo sát ACM Computing Surveys 2025** riêng, có bộ dữ liệu chuẩn và có bộ chỉ số đánh giá.

Ý nghĩa thực tế: **dự án không cần phát minh lại phương pháp, và quan trọng hơn — không cần phát minh
lại cách đo.** Có sẵn bộ dữ liệu có nhãn chuyên gia (TutorialBank, LectureBank, AL-CPL, LERECCI với 192
bài giảng Coursera có nhãn chuyên gia) để chấm điểm phương pháp trước khi tin nó.

Văn liệu PRL cũng cho một phân biệt spec **chưa chốt**, và nó quyết định mọi thứ phía sau:

|         | Knowledge Concept (KC)                              | Learning Object (LO)                    |
| ------- | --------------------------------------------------- | --------------------------------------- |
| Là gì   | Khái niệm nguyên tử: "Overfitting", "Định lý Bayes" | Đơn vị học liệu: một mục, một bài giảng |
| Đồ thị  | Node = khái niệm                                    | Node = section/bài                      |
| Hợp với | Đồ thị tri thức, quiz theo khái niệm                | Lộ trình theo tài liệu, ít nhiễu hơn    |

Spec chọn KC (node = concept). Đó là lựa chọn tham vọng hơn và **nhiễu hơn** — trích khái niệm là bước
dễ sai nhất trong toàn chuỗi, mà mọi bước sau đứng trên nó. Văn liệu ghi nhận cả hai hạt đều hợp lệ và
có công trình riêng. Đây là quyết định cần ghi thành ADR, không nên để ngầm.

---

## 2. Kiến trúc Tầng 1 → Tầng 2a của spec **trùng khớp hai khung nghiên cứu độc lập**

Đây là tin tốt, và nó không hiển nhiên.

### 2.1 Tách Extract khỏi Canonicalize — khung EDC

**EDC (Extract–Define–Canonicalize)**, arXiv 2404.03868, chốt rằng trích xuất KG bằng LLM nên chia ba
pha: **trích mở** (không ép schema, để tránh nhồi schema lớn vào cửa sổ ngữ cảnh) → **định nghĩa
schema** → **chuẩn hoá hậu kỳ** (gộp phần tử trùng/tương tự).

Spec làm đúng thế: Tầng 1 trích ứng viên tự do, Tầng 2a gộp thành **bảng node chuẩn (canonical)**.
Từ "canonical" trong spec trùng đúng thuật ngữ của khung này.

Lý do khung này tồn tại, và nó đúng với dự án: LLM **không đặt tên nhất quán**. Cùng một khái niệm, gọi
ở section 3 là "L2 Regularization", section 7 là "Ridge", section 9 là "weight decay". Văn liệu ghi:
*"thiếu nhất quán trong đặt tên thực thể/quan hệ, tổng quát hoá quá mức hoặc thiếu — đòi hỏi chuẩn hoá
hậu kỳ và gom cụm tường minh."* Không có pha canonicalize thì đồ thị vỡ vụn thành các node trùng nghĩa.

### 2.2 Gom cụm rồi để LLM phán trong cụm — đúng SOTA của Entity Resolution

Tầng 2a của spec: dựng đồ thị similarity ngưỡng thấp → gom cụm → **mỗi cụm một lời gọi agent**, thay vì
so từng cặp. Đây chính là **in-context clustering-based entity resolution**, công bố tại PACMMOD/SIGMOD
2025: thay vì so nhị phân từng cặp, đưa cả cụm ứng viên cho LLM và hỏi cái nào là một.

Nghiên cứu đó xác nhận lợi ích spec đang nhắm: **ít lời gọi hơn** và **chính xác hơn nhờ ngữ cảnh giàu
hơn** — agent nhìn thấy cả cụm nên phân biệt được sắc thái mà so cặp không thấy.

Nhưng nghiên cứu cũng cảnh báo ba biến spec **chưa nói tới**, và cả ba đều đo được:

| Biến | Phát hiện | Spec hiện tại |
|---|---|---|
| **Cỡ cụm** | Cụm lớn cho nhiều ngữ cảnh nhưng **giảm độ chính xác vì quá tải thông tin** | Không có trần cỡ cụm |
| **Độ đa dạng** | Cụm quá đồng nhất thiếu thông tin phân biệt; quá đa dạng làm mô hình rối | Không xét |
| **Thứ tự bản ghi** | Thứ tự trình bày **ảnh hưởng quyết định của LLM** | Không xét |

Đề nghị: đặt trần cỡ cụm (nếu cụm vượt ngưỡng thì chia nhỏ trước khi gọi agent) và **cố định thứ tự
trình bày ứng viên** — cái sau còn phục vụ tính tái lập, thứ mà spec đã coi là điểm yếu lớn nhất của
agent loop.

### 2.3 Ngưỡng blocking thiên về recall — đúng nguyên lý ER kinh điển

Spec chọn ngưỡng ~0.75 với lý do: *"cặp trùng lọt khỏi cụm thì không bao giờ được merge nữa, còn cặp
thừa trong cụm thì agent sẽ tách — sai loại hai sửa được, loại một thì không."*

Đây là nguyên lý **blocking** chuẩn của Entity Resolution, phát biểu đúng. Văn liệu ER 2025 gọi đây là
"semantic blocking" và cũng khuyến nghị dùng ANN/LSH trên vector — đúng thứ dự án sẽ có sau A3'.

---

## 3. Ba rủi ro thật trong A3, có bằng chứng

### 3.1 🔴 Một lượt trích là **thiếu** — GraphRAG dựng cả cơ chế riêng để chữa

Spec: *"một LLM call cho mỗi section"*. Đây là điểm yếu đã được ngành đo và đặt tên.

Microsoft GraphRAG có tính năng **gleaning** — trích **nhiều lượt** trên cùng đoạn văn — với lý do
tường minh: *"LLM không trích hết thông tin có sẵn trong một lượt"*. Cơ chế của họ: sau lượt đầu, hỏi
lại mô hình "còn thực thể nào chưa trích không", dùng logit bias để buộc trả lời có/không, lặp tới khi
mô hình nói hết.

Với dự án, hệ quả cụ thể: khái niệm bị bỏ sót ở A3 **không bao giờ xuất hiện lại** ở bất kỳ tầng nào
sau — Tầng 2a chỉ gộp cái đã có, Tầng 2b chỉ nối cái đã có. **Recall của A3 là trần cứng cho toàn bộ
lộ trình.** Đây là bất đối xứng nghiêm trọng: khái niệm thừa thì tầng sau lọc được, khái niệm thiếu thì
mất vĩnh viễn — cùng dạng lập luận spec đã dùng đúng cho ngưỡng blocking, nhưng chưa áp cho A3.

### 3.2 🔴 Không có lượt kiểm định — và trong đúng miền giáo dục thì điều này đã được đo

Spec đi thẳng từ trích sang gộp, không có bước tự kiểm.

Bằng chứng gần nhất với dự án đến từ chính miền giáo dục: nghiên cứu về gán nhãn học liệu bằng LLM ghi
nhận *"gán nhãn một lượt cho độ đồng thuận thấp với chuẩn vàng, nhưng tự kiểm định bằng cách để mô hình
đánh giá lại **cải thiện đáng kể** độ tin cậy"*.

Ở miền trích quan hệ nói chung, lượt kiểm định nâng F1 chủ yếu **bằng cách tăng precision**, đổi lại
giảm nhẹ recall (một nghiên cứu: F1 0,375 → 0,409).

Kết hợp 3.1 và 3.2 cho một thiết kế hai lượt bất đối xứng, và đây là đề xuất chính của báo cáo này:

```
Lượt 1 (gleaning)   — nhắm RECALL: "còn khái niệm nào được giảng trong đoạn này chưa liệt kê?"
Lượt 2 (verify)     — nhắm PRECISION: "khái niệm này có thật sự được ĐỊNH NGHĨA/GIẢNG ở đây,
                       hay chỉ được nhắc? Trích câu làm bằng chứng."
```

Lượt 2 làm được thêm một việc mà spec đang bỏ ngỏ: **buộc mỗi khái niệm phải có câu bằng chứng**.
Spec đã đòi điều này cho **edge** ở A8 (*"không bằng chứng → không tạo edge"*) nhưng **không đòi cho
concept** ở A3. Bất đối xứng này không có lý do — khái niệm bịa cũng nguy hiểm như quan hệ bịa, và còn
nguy hiểm hơn vì nó sinh ra node mà mọi thứ khác bám vào.

### 3.3 🟡 "JSON nghiêm ngặt" bảo đảm **hình thức**, không bảo đảm **nội dung**

Spec: *"yêu cầu output JSON nghiêm ngặt"*. Cần biết ba kết quả đo được:

- **Structured output bảo đảm schema, không bảo đảm chất lượng.** Đo trên tải sản xuất: lệch chất lượng
  ngữ nghĩa 0–3% với trích xuất thường, nhưng **10–15% với schema sâu**.
- **Ràng buộc định dạng làm giảm khả năng suy luận** của LLM (arXiv 2408.02442, "Let Me Speak Freely?").
- Benchmark 22 mô hình: **chiến lược prompt quan trọng hơn cỡ mô hình**, và **lỗi ngữ nghĩa vẫn tồn tại
  ngay cả khi cấu trúc hợp lệ**.

Hệ quả thiết kế: giữ schema **nông và ít trường** ở lượt trích (tên + câu bằng chứng + chunk_id), đẩy
description và difficulty sang lượt sau. Spec hiện gói cả năm trường vào một lượt — đúng vùng
10–15% suy giảm.

---

## 4. A3' và một mâu thuẫn giữa addendum với B0 đã dựng

### 4.1 Mâu thuẫn — ✅ đã sửa

Mục A2 của addendum ghi *"mục tiêu 300–800 token, overlap 10–15%"*, `section_path` là chuỗi. **B0 đã
dựng không như vậy**: mục tiêu 256, ba trần 512/2048/6000, **không overlap** giữa chunk gộp,
`section_path` là mảng.

Báo cáo vòng 11 cho thấy **cái đã dựng đúng hơn cái addendum viết**: Chroma đo chunk 200 token cho
precision/IoU cao nhất và phê phán thẳng cấu hình 800/overlap-400.

**Đã sửa mục A2 của addendum** (2026-08-29) cho khớp thực tế: ba trần token, không overlap kèm lý do,
JSON output đúng hình dạng đang sinh, và ghi rõ `stage_id` không nằm trong chunk artifact mà gắn ở
tầng vector — đúng khuôn ADR 0002 để cập nhật `stage_id` không phải embed lại.

### 4.2 A3' — không có gì gây tranh cãi, trừ ba điểm

- Spec đề xuất `bge-m3` / `multilingual-e5`. Bộ nhớ dự án ghi **Gemini là nhà cung cấp mô hình**. Cần
  chốt: nếu Gemini thì mất khả năng **late chunking** (đã ghi ở báo cáo vòng 11); nếu tự host `bge-m3`
  thì được late chunking nhưng thêm hạ tầng. Không có câu trả lời đúng chung — cần một quyết định.
- **Ngữ cảnh khi embed** (ghép `section_path` vào văn bản) vẫn là khoảng trống lớn nhất của nhánh vector,
  đã phân tích ở vòng 11: Anthropic đo giảm **35%** lỗi truy hồi. Phải chốt **trước lần embed đầu tiên**
  vì nó đổi định danh chunk.
- Spec ghi metadata bắt buộc gồm `stage_id` (tạm null, điền ở A12). Lưu ý kỹ thuật: cập nhật metadata
  hàng loạt sau khi đã embed là thao tác rẻ ở pgvector nhưng cần tránh embed lại — thiết kế sao cho
  `stage_id` là cột thường, không nằm trong bất kỳ khoá băm nào. Đây đúng khuôn ADR 0002 đã có
  (tham chiếu đứng ngoài khoá băm).

---

## 5. Một điều then chốt về chi phí mà phần lớn tranh luận ngoài kia **không áp dụng cho dự án này**

Văn liệu 2025–2026 phê phán GraphRAG khá nặng về chi phí: dựng chỉ mục ~**48 USD** với GPT-4o cho một
corpus vừa; Microsoft ra **LazyGraphRAG** hoãn trích xuất tới lúc truy vấn, giảm còn **~0,1%** chi phí.
GraphRAG-Bench còn cho thấy RAG thường **ngang hoặc hơn** GraphRAG ở truy hồi dữ kiện đơn giản
(F1 64,8 vs 63,0), chỉ thua ở suy luận nhiều bước (70,3 vs 67,0).

**Nhưng toàn bộ tranh luận đó là về việc dùng đồ thị để cải thiện truy hồi.** Ở dự án này, **đồ thị
chính là sản phẩm** — lộ trình học là đồ thị tiên quyết đã topo sort. Không có đồ thị thì không có gì
để giao cho người dùng. Nên:

- Lập luận "hoãn trích xuất tới lúc truy vấn" (LazyGraphRAG) **không áp dụng**: không thể hoãn cái mình
  phải hiển thị.
- Lập luận "RAG thường đủ tốt" **không áp dụng** cho A3; nó áp dụng cho **A3'** — và spec đã tách đúng
  hai nhánh cho hai mục đích khác nhau (đồ thị cho lộ trình, vector cho gia sư). **Sự tách đôi này là
  quyết định kiến trúc đúng**, và nên ghi rõ lý do vào ADR để sau này khỏi bị chất vấn bằng các bài
  viết "GraphRAG không đáng tiền".

Số thật của corpus hiện tại để định cỡ:

```
TONG: 129 section · 233 chunk · 48.694 token nội dung
  1 lời gọi/section          -> ~129 lời gọi
  gom siêu-section 1–2k token -> ~32 lời gọi
```

Bốn tài liệu chỉ ~49k token. Ở quy mô này chi phí A3 là **không đáng kể** kể cả khi chạy hai lượt
(gleaning + verify) — nghĩa là **không có lý do kinh tế nào để tiết kiệm ở đúng chỗ dễ sai nhất**.
Việc gom siêu-section 1–2k token mà spec đề xuất giảm 129 → 32 lời gọi, đủ dư ngân sách cho hai lượt.

---

## 5b. Bổ sung 2026 — hai công trình đổi cách nhìn

### 5b.1 🔴 Bốn LLM cùng một corpus cho ra bốn đồ thị khác nhau — Jaccard 0,06–0,11

Nghiên cứu Frontiers in Immunology 2026 (*"LLMs build inconsistent knowledge graphs from one corpus"*)
cho bốn LLM cùng đầu vào, cùng schema, rồi đo:

```
chênh lệch số cạnh sinh ra   : 2,3 lần
cạnh CHỈ một mô hình có      : 66–75%
Jaccard từng cặp             : 0,06–0,11   (1 trên 9 tới 1 trên 16 cạnh là chung)
tuân thủ schema              : 57% – 84%
```

Kết luận của họ nguyên văn: **"mô hình, chứ không phải tài liệu, đã viết ra phần lớn đồ thị."**

Đây là bằng chứng mạnh nhất tôi tìm được cho mối lo spec tự nêu — *"kiểm soát tính tái lập (điểm yếu
lớn nhất của agent loop)"*. Spec chữa bằng `temperature = 0` và event log. **Chưa đủ**: nhiệt độ 0 chỉ
giữ ổn định **giữa các lần chạy cùng mô hình**, không giúp gì khi đổi mô hình. Mà đổi mô hình là việc
sẽ xảy ra — nhà cung cấp cho model mới, model cũ bị khai tử.

Ba hệ quả cụ thể:

1. **Ghim phiên bản mô hình vào manifest như đã ghim `tokenizer_id`.** Dự án đã có đúng khuôn này ở B0
   (`adapter_version`, `tokenizer_id`, `config_hash` gác việc chạy lại). Đồ thị cần thứ tương đương:
   đổi mô hình ⇒ đồ thị là **phiên bản khác**, không phải cùng đồ thị.
2. **Đo Jaccard giữa hai lần chạy** như một chỉ số hạng nhất, không phải "nice to have".
3. **Ensemble không phải thuốc bổ miễn phí.** Họ đo được: chỉ **đồng thuận tuyệt đối cả bốn mô hình**
   mới vượt mô hình đơn tốt nhất (+12% precision) nhưng **chỉ giữ lại 4% số cạnh**; đồng thuận đa số
   ngây thơ thì **kém hơn** mô hình đơn. Khuyến nghị của họ: chọn một mô hình mạnh, chỉ dùng lọc đồng
   thuận ở nơi precision đáng giá hơn recall. Với dự án — recall A3 là trần cứng — **không nên** dùng
   lọc đồng thuận ở A3; nếu dùng thì chỉ ở A8 (edge), nơi thừa nguy hiểm hơn thiếu.

### 5b.2 🟢 Edu-Graph RAG — bài gần dự án nhất, và nó xác nhận đường đi

*Education-Oriented Graph RAG for Learning Path Recommendation* (arXiv 2506.22303) làm **đúng bài toán
của dự án**: sinh đồ thị tiên quyết giữa các khái niệm để gợi ý lộ trình học. Kết quả trên ba bộ dữ
liệu chuẩn của ngành giáo dục:

| Bộ dữ liệu | Cải thiện so với SOTA trước |
|---|---|
| Junyi | +14–28% |
| MOOCCubeX | +15–31% |
| ASSIST09 | +2–27% |

Bốn điều lấy được:

- **Hướng đi được xác nhận.** Dùng GraphRAG có tuỳ biến cho miền giáo dục **thắng** các phương pháp
  trước (GNN, học có giám sát) trên chính bộ dữ liệu chuẩn của ngành. Kiến trúc spec đang chọn không
  phải nước cờ mạo hiểm.
- **Hai loại quan hệ, không phải một.** Họ sinh **cả** quan hệ tiên quyết **và** quan hệ tương đồng —
  trùng đúng chỗ spec tách A6 (đồ thị "liên quan") khỏi A8 (đồ thị tiên quyết). Sự tách này là đúng
  chuẩn ngành chứ không phải chi tiết thừa.
- **Prompt tuỳ biến theo miền là điểm khác biệt chính** so với GraphRAG gốc — không phải kiến trúc.
  Củng cố kết luận mục 3: rủi ro của dự án nằm ở tầng prompt A3, không ở kiến trúc ba tầng.
- **Chống ảo giác bằng vòng lặp tinh chỉnh (TextGrad)**: sinh mô tả → một lượt LLM khác **chấm** →
  tinh chỉnh theo phản hồi → lặp tới khi đạt. Đây là biến thể mạnh hơn của lượt verify tôi đề xuất ở
  mục 3.2, và nó được đo là có tác dụng trên đúng miền này.

Một chi tiết đáng suy nghĩ cho A9: đồ thị họ sinh ra **dày hơn** đồ thị do người dựng tay. Spec đặt
quality gate *"edge < 0,5 × số node ⇒ tài liệu không có cấu trúc tiên quyết"* — ngưỡng đó canh trường
hợp **quá thưa**. Kinh nghiệm Edu-Graph RAG gợi ý rủi ro thực tế có thể ngược lại: LLM sinh **quá
nhiều** edge, và transitive reduction ở A9c sẽ phải gánh nặng hơn dự tính. Đáng thêm một chỉ số canh
**trần** mật độ, không chỉ canh sàn.

### 5b.3 Khảo sát 2026: schema-based vs schema-free — spec đang ở giữa mà chưa chọn

Khảo sát *LLM-empowered knowledge graph construction* (arXiv 2510.20345) chia hai trường phái:
**schema-based** (định trước kiểu thực thể/quan hệ — nhất quán, nhưng gò) và **schema-free** (trích mở
— linh hoạt, nhưng phải chuẩn hoá hậu kỳ).

Spec A3 đang **schema-based** (JSON cố định năm trường) nhưng Tầng 2a lại là **canonicalize hậu kỳ** —
thứ sinh ra để phục vụ schema-free. Không sai, nhưng nên chọn có ý thức: EDC lập luận trích **mở** rồi
chuẩn hoá cho kết quả tốt hơn, và điều đó khớp với đề xuất "schema nông ở lượt trích" ở mục 3.3.

Khảo sát cũng ghi nhận hướng **agentic** đang nổi lên đúng như spec dự tính: vòng lặp tinh chỉnh, nhiều
agent chia việc (tách agent trích thực thể khỏi agent trích quan hệ), và **kiểm định chéo**. Spec đang
đi đúng xu hướng 2026, không phải đuổi theo mốt cũ.

## 5c. Đồ thị đa kiểu node — phần bản báo cáo đầu **đã bỏ sót**

### 5c.1 Đính chính phạm vi

Bản đầu của báo cáo này phân tích A3 như **trích khái niệm thuần**, đóng khung toàn bộ qua văn liệu
Prerequisite Relation Learning và dựng bảng KC vs LO như thể đó là hai lựa chọn duy nhất. **Khung đó
sai phạm vi.** Ý định đã nêu ba lần trong quá trình thiết kế là **đồ thị đa kiểu node**: ngoài khái
niệm còn có node kiểu hình, bảng, và các kiểu khác, có cạnh nối sang khái niệm, để agent truy vấn về
sau **xuất được ảnh cho người dùng**.

Ý định này hiện chỉ tồn tại trong hội thoại và một dòng hoãn quyết định ở ADR 0002:

> *"Ingest không tạo thực thể đồ thị. Nó chỉ parse, lưu ảnh và sinh tham chiếu tất định; bước trích
> khái niệm tự quyết định sau này có dựng node/cạnh cho hình hoặc bảng hay không."*

Hạ tầng đã sẵn sàng cho nó — `image_refs`/`table_refs`/`formula_refs` mang định danh băm cộng
`char_start`, ảnh lưu theo băm nội dung. Nhưng **spec-addendum A3 không nhắc một chữ nào**. Đây là
khoảng trống tài liệu nghiêm trọng hơn mâu thuẫn A2 đã sửa: A2 sai số, còn chỗ này **thiếu hẳn một
chiều của bài toán**.

### 5c.2 Quy mô: thực thể phi văn bản **nhiều hơn** người ta tưởng

```
                 anh  bang  cthuc     (thực thể duy nhất, sau khử trùng)
nhap-mon-ml        9     0      1
xstk-ch3-1         5    48    225
baocao-canhan      3     0      0
naive-bayes        2    12     32
TỔNG              19    60    258   ->  337 thực thể phi văn bản
```

Đối chiếu: công trình gần nhất (mục 5c.3) sinh **172 khái niệm** từ ba bài giảng. Bốn tài liệu của dự
án ước chừng cùng bậc — vài trăm khái niệm. Nghĩa là **nếu đưa cả ba loại vào làm node, thực thể phi
văn bản chiếm khoảng một nửa đồ thị, mà riêng công thức đã 258.**

Đây là con số phải nhìn trước khi quyết định. Một đồ thị lộ trình học có 258 node công thức sẽ:
làm loãng mọi phép đo mật độ ở A9 (gate `edge < 0,5 × node` đổi ý nghĩa hoàn toàn), làm topological
layering vô nghĩa nếu công thức lọt vào DAG tiên quyết, và làm cluster ở A7 bị chi phối bởi thứ không
phải khái niệm. **Ba loại không nên đối xử như nhau.**

### 5c.3 Công trình gần nhất chọn hướng **ngược lại** — và lý do đáng cân nhắc

*Evidence-Grounded Multimodal KG Construction for Multi-Lecture Educational Reasoning*
(arXiv 2608.03161, 08/2026) làm đúng miền của dự án: dựng đồ thị tri thức từ bài giảng có hình, slide,
công thức. Nhưng thiết kế của họ:

- **Không tạo node riêng cho hình.** Họ dùng OCR + mô hình thị giác-ngôn ngữ để **rút chữ và ngữ nghĩa
  từ hình** (nhãn slide, chú thích sơ đồ, ký hiệu, phương trình), rồi nội dung đó nuôi các node **khái
  niệm**. Hình là **nguồn bằng chứng**, không phải thực thể.
- **Bù lại bằng cạnh giàu kiểu**: tám loại — `prerequisite_of`, `component_of`, `uses`, `optimizes`,
  `computed_by`, `example_of`, `contrasts_with`, `related_to`.
- **Mọi thứ phải có bằng chứng**: mỗi khái niệm và quan hệ mang câu trích dẫn, **phương thức nguồn**
  (lời giảng / OCR / thị giác), timestamp, và điểm tin cậy ≥ 0,55.
- Kết quả: 1.022 lần nhắc khái niệm hợp lệ → **172 khái niệm chuẩn, 282 cạnh**; OCR thành công 94,63%;
  truy hồi top-1 và top-3 đạt 100% trên bộ câu hỏi mồi.

Bài học họ ghi lại đáng giá: **chuẩn hoá vẫn chưa xong** — `weight` vs `weights`, `cost function` vs
`loss function` — *"căng thẳng giữa gộp trùng và giữ khái niệm phân biệt"*. Đúng thứ Tầng 2a của dự án
sẽ đối mặt.

**Vậy là hai thiết kế đối lập, cả hai đều có cơ sở:**

| | **Giàu kiểu node** (ý định của dự án) | **Giàu kiểu cạnh** (bài 2608.03161) |
|---|---|---|
| Hình | Node riêng, có cạnh sang khái niệm | Nguồn bằng chứng, nội dung rút vào khái niệm |
| Hỏi được | *"Hình này minh hoạ khái niệm nào?"* — duyệt hai chiều | Chỉ tra ngược qua bằng chứng |
| Một hình minh hoạ ba khái niệm | Tự nhiên: một node, ba cạnh | Lặp bằng chứng ở ba khái niệm |
| DAG tiên quyết | **Phải lọc** node phi khái niệm trước khi topo sort | Sạch sẵn |
| Mật độ đồ thị | Loãng bởi 337 thực thể phi văn bản | Tập trung |
| Xuất ảnh cho user | Trực tiếp | Qua thuộc tính khái niệm |

### 5c.4 Ý "không có chú thích thì quăng thẳng ảnh cho LLM" — **đã là một bài ICCV 2025**

Ý định của dự án: ảnh có chú thích thì dùng chú thích; **không có chú thích thì đưa thẳng ảnh cho mô
hình** để nó tự nhận quan hệ.

**VaLiK** (*Aligning Vision to Language: Annotation-Free Multimodal KG Construction*, ICCV 2025) làm
đúng thế và chứng minh nó chạy được: xâu chuỗi mô hình thị giác-ngôn ngữ để **dịch ảnh thành mô tả văn
bản**, rồi dựng đồ thị từ mô tả đó. Kết luận của họ: *"kể cả không có chú thích ảnh do người gán, chỉ
riêng các mô tả đã tinh chỉnh cũng đủ để dựng đồ thị đa phương thức."*

Và họ giữ được đúng thứ dự án muốn: **liên kết thực thể ↔ ảnh trực tiếp**, để về sau trỏ ngược ra ảnh.

**Nhưng có một mảnh dự án chưa nghĩ tới, và nó là mảnh làm cho VaLiK chạy được:** mô tả do mô hình thị
giác sinh ra **có ảo giác**, nên VaLiK thêm hẳn một tầng **kiểm định tương đồng chéo phương thức** —
đo độ nhất quán ngữ nghĩa giữa mô tả và ảnh gốc để **lọc nhiễu** trước khi cho vào đồ thị. Không có
tầng này thì đồ thị nhiễm mô tả bịa.

Nghĩa là ý tưởng của bạn đúng hướng và có công trình đứng sau, nhưng cần thêm **một bước kiểm định** —
đúng cùng hình dạng với lượt verify tôi đề xuất cho A3 văn bản ở mục 3.2.

### 5c.5 Khuyến nghị: tách **đồ thị lộ trình** khỏi **đồ thị truy vấn**

Điểm mấu chốt mà cả hai thiết kế trên đều không nói rõ, nhưng lộ ra khi đặt cạnh mục tiêu của dự án:
**dự án cần hai thứ khác nhau từ cùng một đồ thị.**

- **Lộ trình học** cần một DAG tiên quyết **chỉ gồm khái niệm**. "Hình 3.2" không thể là tiên quyết của
  cái gì. Topo sort, layering, chia stage — tất cả đòi node đồng nhất.
- **Agent truy vấn ở pha B** cần đồ thị **đa kiểu**, để trả lời *"cho tôi xem hình minh hoạ khái niệm
  này"*, *"bảng nào chứa số liệu về X"*.

Đề xuất cụ thể: **một đồ thị, mọi node mang trường `node_type`, và mọi thuật toán lộ trình lọc
`node_type = "concept"` trước khi chạy.** Cạnh cũng phân loại: `requires` chỉ được phép nối
concept↔concept; các loại như `illustrates`, `tabulates`, `defines` nối thực thể phi văn bản sang
khái niệm và **không tham gia topo sort**.

Điều này giữ được cả hai mục tiêu, và quan trọng: nó **không phải phát minh** — spec đã dùng đúng khuôn
này một lần rồi. Ở A8, spec ghi *"cạnh similarity, co-occurrence, mention là cấu trúc phụ trợ — không
nằm trong graph tiên quyết. Muốn hiển thị 'liên quan' trên UI: thêm loại `relates_to`, không tham gia
topo."* **Luật đã có sẵn; chỉ cần mở rộng từ cạnh sang node.**

Và ba loại nên đối xử khác nhau, theo đúng số đo ở 5c.2:

| Loại | Số lượng | Đề xuất |
|---|---:|---|
| **Hình** | 19 | **Node đầy đủ** — ít, giá trị cao, đúng mục tiêu "xuất ảnh cho user" |
| **Bảng** | 60 | **Node đầy đủ** — mang dữ liệu tra cứu được, agent hỏi thẳng |
| **Công thức** | 258 | **Không làm node ở vòng đầu.** Quá nhiều, và nội dung thô đã biết là lộn xộn về thứ tự (đo ở vòng 8). Giữ làm thuộc tính/bằng chứng của khái niệm; xét lại khi có cách đọc công thức đáng tin |

Đây cũng là câu trả lời cho lo ngại mật độ ở 5c.2: 79 node phi văn bản trên vài trăm khái niệm là tỉ lệ
lành mạnh; 337 thì không.

## 6. Khoảng trống lớn nhất, lặp lại từ vòng 11: **chưa có cách đo**

Vòng 11 kết luận B0 thiếu phép đo truy hồi. A3 thiếu điều tương tự, và ở đây khó hơn — vì
**"khái niệm đúng" là khái niệm gây tranh cãi**.

Văn liệu giáo dục nói thẳng: gán nhãn khái niệm cho mục sách giáo khoa là việc khó, *"phương pháp trích
keyphrase không giám sát có độ chính xác không đủ, nên gán nhãn chuyên gia thủ công vẫn là cách được ưa
dùng"*. Và khi nhiều người cùng gán nhãn, họ **bất đồng một cách có hệ thống** — bất đồng thường đến từ
*"mức nhấn khác nhau giữa bề rộng và chiều sâu"*: người này trích 5 khái niệm lớn, người kia trích 20
khái niệm chi tiết, **cả hai đều không sai**. Có nghiên cứu riêng về chuyện này
("Beyond Agreement: Rethinking Ground Truth in Educational AI Annotation").

Hệ quả cho dự án — và đây là điều cần chấp nhận sớm: **không thể có một "đáp án đúng" cho A3.** Cái làm
được là:

1. **Chốt độ hạt bằng ví dụ, không bằng định nghĩa.** Prompt kèm 5–10 ví dụ đã gán nhãn tay từ chính
   giáo trình của dự án, nói rõ mức nào là khái niệm, mức nào quá chi tiết. Văn liệu cho thấy độ hạt là
   nguồn bất đồng lớn nhất — mà ví dụ truyền đạt độ hạt tốt hơn mọi câu mô tả.
2. **Đo bằng những thứ đo được thay vì đo "đúng/sai":**
   - **Recall trên danh sách vàng nhỏ**: gán nhãn tay ~2 chương, xem A3 bỏ sót bao nhiêu. Đây là chỉ số
     quan trọng nhất vì recall A3 là trần cứng.
   - **Tỉ lệ có bằng chứng**: bao nhiêu % khái niệm trích ra có câu bằng chứng thật trong chunk nguồn
     (kiểm bằng code, không cần người) — bắt bịa đặt.
   - **Độ ổn định giữa các lần chạy**: chạy lại cùng đầu vào, đo % khái niệm trùng. Văn liệu 2025 coi
     **tính nhất quán là tín hiệu tin cậy bổ trợ cho độ chính xác**. Với dự án đã dựng cả một kiến trúc
     tất định cho B0, để A3 trôi nổi không đo là mâu thuẫn nội tại.
   - **Tỉ lệ merge ở Tầng 2a**: nếu quá cao thì A3 đang cắt vụn khái niệm; quá thấp thì blocking hụt.
3. **So với bộ dữ liệu chuẩn nếu muốn công bố**: LectureBank/AL-CPL có nhãn tiên quyết của chuyên gia,
   dùng được để chấm điểm A8 theo chuẩn ngành.

---

## 7. Đề xuất, xếp theo thứ tự

| #   | Việc                                                                                                                          | Vì sao thứ tự này                                                                                                    |
| --- | ----------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| 0   | **Đưa ý định đồ thị đa kiểu node vào spec A3** — `node_type`, cạnh phân loại, luật "chỉ concept vào DAG tiên quyết"           | Ý định nêu ba lần nhưng chỉ sống trong hội thoại + một dòng hoãn ở ADR 0002; thiếu nó thì spec A3 mô tả sai bài toán |
| 1   | **Chốt độ hạt khái niệm (KC) bằng ADR + 5–10 ví dụ gán tay**                                                                  | Mọi thứ sau đứng trên đây; văn liệu chỉ ra đây là nguồn bất đồng lớn nhất                                            |
| 2   | ~~Sửa mục A2 của addendum~~ ✅ **đã làm 2026-08-29**                                                                           | Mâu thuẫn tài liệu sẽ làm người sau tính sai                                                                         |
| 3   | **Ghim phiên bản mô hình vào manifest đồ thị**, như `tokenizer_id` ở B0                                                       | Frontiers 2026: đổi mô hình đổi 66–75% số cạnh — đồ thị khác mô hình là đồ thị khác                                  |
| 4   | **Thiết kế A3 hai lượt**: gleaning (recall) + verify có bằng chứng (precision)                                                | Recall A3 là trần cứng của toàn lộ trình; chi phí ở quy mô này không đáng kể                                         |
| 5   | **Bắt buộc bằng chứng cho concept**, không chỉ cho edge                                                                       | Bất đối xứng vô lý trong spec hiện tại                                                                               |
| 6   | **Danh sách vàng ~2 chương + 5 chỉ số** (recall, tỉ lệ có bằng chứng, độ ổn định, **Jaccard giữa hai lần chạy**, tỉ lệ merge) | Không đo thì không biết các việc trên có tác dụng không                                                              |
| 7   | Thêm **trần cỡ cụm và thứ tự trình bày cố định** ở Tầng 2a                                                                    | PACMMOD 2025 đo được cả ba biến ảnh hưởng kết quả                                                                    |
| 8   | Giữ **schema nông** ở lượt trích, đẩy description/difficulty sang lượt sau                                                    | Schema sâu gây lệch chất lượng 10–15%; và khớp trường phái schema-free + canonicalize                                |
| 9   | Thêm **trần mật độ edge** ở A9, không chỉ sàn                                                                                 | Edu-Graph RAG sinh đồ thị **dày hơn** người dựng tay — rủi ro thực tế có thể ngược chiều gate hiện tại               |
| 10  | Chốt **mô hình embedding** (Gemini vs tự host) và **ngữ cảnh khi embed**                                                      | Cả hai phải chốt trước lần embed đầu vì đổi định danh                                                                |
| 11  | ADR: **vì sao dự án này cần đồ thị dựng trước** dù ngành đang phê phán chi phí GraphRAG                                       | Đồ thị là sản phẩm, không phải phụ trợ truy hồi — phải ghi để khỏi bị chất vấn sai chỗ                               |
| 12  | **Tầng kiểm định chéo phương thức** cho ảnh không chú thích, trước khi mô tả vào đồ thị                                       | VaLiK cần đúng tầng này để chạy; mô tả do mô hình thị giác sinh ra có ảo giác                                        |
| 13  | **Hoãn công thức làm node** (giữ hình + bảng)                                                                                 | 258 công thức sẽ chiếm nửa đồ thị, và nội dung thô đã biết là lộn xộn thứ tự từ vòng 8                               |

**Không nên làm**: lọc đồng thuận nhiều mô hình ở A3. Frontiers 2026 đo được đồng thuận đa số **kém hơn**
mô hình đơn tốt nhất, và đồng thuận tuyệt đối chỉ giữ 4% số cạnh — thảm hoạ cho một bước mà recall là
trần cứng. Nếu muốn dùng, chỉ dùng ở A8 nơi edge thừa nguy hiểm hơn edge thiếu.

---

## 8. Kết luận

**Kiến trúc ba tầng trong spec là đúng, và đúng theo cách không hiển nhiên** — nó trùng độc lập với hai
khung nghiên cứu (EDC cho tách trích/chuẩn hoá, in-context clustering ER cho gộp theo cụm) mà spec
không viện dẫn. Việc tách trục phân vùng 2a (ngữ nghĩa) khỏi 2b (vị trí tài liệu) là quan sát sắc,
không thấy phát biểu tường minh trong văn liệu tôi đọc.

**Rủi ro tập trung ở A3, không ở kiến trúc.** Ba điểm: một lượt trích là thiếu (GraphRAG dựng gleaning
để chữa), không có lượt kiểm định (miền giáo dục đã đo là cần), và bằng chứng chỉ bắt buộc cho edge chứ
không cho concept. Cả ba đều sửa được ở tầng prompt và luồng gọi, không phải sửa kiến trúc. Edu-Graph
RAG củng cố điều này: cái làm nên +14–31% của họ so với GraphRAG gốc là **prompt tuỳ biến theo miền**,
không phải kiến trúc khác.

**Bài toán rộng hơn khung Prerequisite Relation Learning.** Bản đầu báo cáo này đóng khung A3 là trích
khái niệm thuần — sai phạm vi. Mục tiêu thật là **đồ thị đa kiểu node** phục vụ hai đầu ra khác nhau:
DAG tiên quyết chỉ-khái-niệm cho lộ trình, và đồ thị đa kiểu cho agent truy vấn. Cách gỡ không phải
chọn một trong hai mà là **một đồ thị có `node_type`, thuật toán lộ trình lọc trước khi chạy** — đúng
khuôn spec đã dùng cho cạnh `relates_to`, chỉ mở rộng từ cạnh sang node. Và ba loại thực thể phi văn
bản phải đối xử khác nhau: hình (19) và bảng (60) làm node; công thức (258) thì không, ít nhất ở vòng đầu.

**Và có một rủi ro mới mà spec chưa lường: định danh của mô hình.** Bốn LLM cùng corpus cho ra đồ thị
chồng lấn 6–11%. Dự án đã dựng cả một kiến trúc tất định cho B0 — ghim tokenizer, ghim adapter, băm
config để gác việc chạy lại — rồi sẽ đặt lên trên nó một tầng mà **đổi mô hình là đổi hai phần ba nội
dung**. Không thể làm cho tầng đó tất định, nhưng **bắt buộc phải làm cho nó khai báo được**: đồ thị
sinh bởi mô hình nào, lần chạy nào, ổn định bao nhiêu so với lần trước.

**Và khoảng trống lớn nhất vẫn là phép đo** — giống hệt kết luận vòng 11 cho B0. Khác biệt: ở A3 thì
"đáp án đúng" bản thân nó gây tranh cãi, nên cách làm không phải là tìm chuẩn vàng tuyệt đối mà là chốt
độ hạt bằng ví dụ rồi đo bốn thứ đo được. Dự án đã có kỷ luật hiếm thấy ở B0 — 25 bất biến, số vàng bốn
tài liệu. Để A3 chạy không có bất kỳ thước đo nào sẽ là bước lùi so với chính mình.

---

## Nguồn

**Đồ thị đa phương thức / đa kiểu node**
- [Evidence-Grounded Multimodal KG Construction for Multi-Lecture Educational Reasoning — arXiv 2608.03161](https://arxiv.org/html/2608.03161)
- [VaLiK — Aligning Vision to Language: Annotation-Free Multimodal KG Construction, ICCV 2025](https://openaccess.thecvf.com/content/ICCV2025/papers/Liu_Aligning_Vision_to_Language_Annotation-Free_Multimodal_Knowledge_Graph_Construction_for_ICCV_2025_paper.pdf) · [arXiv 2503.12972](https://arxiv.org/abs/2503.12972) · [mã nguồn](https://github.com/Wings-Of-Disaster/VaLiK)
- [Scaling Beyond Context: Multimodal RAG for Document Understanding — arXiv 2510.15253](https://arxiv.org/pdf/2510.15253)
- [Knowledge Graphs Meet Multi-Modal Learning: A Comprehensive Survey — arXiv 2402.05391](https://arxiv.org/pdf/2402.05391)
- [SAGE: Structure Aware Graph Expansion for Retrieval of Heterogeneous Data — arXiv 2602.16964](https://arxiv.org/pdf/2602.16964)
- [Think-on-Graph 3.0: LLM Reasoning on Heterogeneous Graphs — arXiv 2509.21710](https://arxiv.org/pdf/2509.21710)

**Bổ sung 2026**
- [LLMs build inconsistent knowledge graphs from one immune-checkpoint corpus: a five-axis benchmark and consensus precision–coverage protocol — Frontiers in Immunology 2026](https://www.frontiersin.org/journals/immunology/articles/10.3389/fimmu.2026.1937268/full)
- [Education-Oriented Graph RAG for Learning Path Recommendation — arXiv 2506.22303](https://arxiv.org/html/2506.22303v1)
- [LLM-empowered knowledge graph construction: A survey — arXiv 2510.20345](https://arxiv.org/pdf/2510.20345)
- [Hierarchical Knowledge Graph-Augmented LLM for Learning Path Generation — ACM 2026](https://dl.acm.org/doi/10.1145/3806262.3806285)
- [Performance evaluation of LLMs for automated knowledge graph generation — ScienceDirect 2026](https://www.sciencedirect.com/science/article/pii/S2666827026000885)
- [KARMA: Multi-Agent LLMs for Automated Knowledge Graph Enrichment — arXiv 2502.06472](https://arxiv.org/pdf/2502.06472)

**Prerequisite relation learning / giáo dục**
- [Prerequisite Relation Learning: A Survey and Outlook — ACM Computing Surveys 2025](https://dl.acm.org/doi/10.1145/3733593)
- [Concept Extraction and Prerequisite Relation Learning from Educational Data — AAAI](https://ojs.aaai.org/index.php/AAAI/article/view/5033)
- [TutorialBank: A Manually-Collected Corpus for Prerequisite Chains — arXiv 1805.04617](https://arxiv.org/pdf/1805.04617)
- [Core Concept Identification in Educational Resources via KG and LLMs — SN Computer Science](https://link.springer.com/article/10.1007/s42979-024-03341-y)
- [Beyond Agreement: Rethinking Ground Truth in Educational AI Annotation — arXiv 2508.00143](https://arxiv.org/pdf/2508.00143)
- [Concept Annotation for Intelligent Textbooks — arXiv 2005.11422](https://arxiv.org/pdf/2005.11422)
- [Data-Driven Evaluation of LLM-Based Ontology Concept Extraction — LAK26](https://doi.org/10.1145/3785022.3785106)

**Trích xuất KG bằng LLM**
- [Extract, Define, Canonicalize (EDC) — arXiv 2404.03868](https://arxiv.org/abs/2404.03868)
- [LazyGraphRAG sets a new standard for quality and cost — Microsoft Research](https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/)
- [When to use Graphs in RAG: A Comprehensive Analysis — arXiv 2506.05690](https://arxiv.org/html/2506.05690v2)
- [GraphRAG-Bench — arXiv 2506.02404](https://arxiv.org/pdf/2506.02404)
- [Stop graphing everything: When GraphRAG actually beats vector RAG — VentureBeat](https://venturebeat.com/orchestration/stop-graphing-everything-when-graphrag-actually-beats-vector-rag)

**Entity resolution**
- [In-context Clustering-based Entity Resolution with LLMs — PACMMOD 2025](https://dl.acm.org/doi/10.1145/3749170) · [bản arXiv](https://arxiv.org/pdf/2506.02509)
- [Cost-Efficient RAG for Entity Matching with LLMs: A Blocking-based Exploration](https://arxiv.org/pdf/2602.05708)

**Độ tin cậy trích xuất**
- [JSONSchemaBench — arXiv 2501.10868](https://arxiv.org/pdf/2501.10868)
- [Let Me Speak Freely? Impact of Format Restrictions on LLM Performance — arXiv 2408.02442](https://arxiv.org/pdf/2408.02442)
- [Consistency–accuracy correlation in hard-prompted LLMs for entity and relation extraction — Genomics & Informatics 2025](https://link.springer.com/article/10.1186/s44342-025-00063-2)
- [Enhancing Relation Extraction via Supervised Rationale Verification and Feedback — arXiv 2412.07289](https://arxiv.org/pdf/2412.07289)
