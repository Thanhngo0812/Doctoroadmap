# Nghiên cứu A4 / A5 — Hợp nhất ứng viên và tổng hợp mô tả: đối chiếu spec với nghiên cứu khoa học

Vòng 19 · 2026-09-11 · Đối tượng: `doc/spec-addendum.md` mục A4, A5 và Tầng 2a (biến thể)

Chưa viết dòng mã nào cho A4/A5 — đây là khảo sát trước khi spec, nối tiếp
`report/nghien-cuu-a3-trich-xuat-thuc-the.md`. Mục 2 là số đo trên artifact A3 của bốn tài liệu; các mục
còn lại là văn liệu. Ký hiệu `§N` = dòng N của `doc/spec-addendum.md` bản hiện tại.

Nguồn: entity resolution bằng LLM (EDBT 2025, COLING 2025, SIGMOD 2026, PAKDD), blocking và gom cụm
(PVLDB 2009/2021/2023, ACM CSUR 2020), ontology matching (OAEI Bio-ML, MILA 2025), **mã nguồn thật** của
GraphRAG, LightRAG, Graphiti, KGGen, Neo4j LLM Graph Builder, và văn liệu tóm tắt đa nguồn có dẫn chứng
(ACL 2020 → arXiv 2026). Con số lấy từ toàn văn hoặc mã nguồn, trừ chỗ ghi *(theo abstract)*.

---

## 1. Phát hiện quan trọng nhất: spec giao cho embedding quyền **quyết định danh tính** — văn liệu chỉ giao cho nó quyền **đề cử**

Spec để cosine tự gộp ứng viên ở ba chỗ:

- §401 (A4 gốc): `≥ 0,90` merge tự động.
- §650 (Tầng 2a): `≥ 0,95` *"merge thẳng bằng code, không cần agent"*.
- §881 (MVP): *"A4 (chỉ lớp lọc tên + embedding)"* — tức cấu hình **không có một lời gọi LLM nào** đứng giữa
  embedding và danh tính node. Cấu hình rủi ro nhất lại được xếp làm trước tiên.

Năm hệ thống đang chạy thật — đọc mã nguồn, không đọc bài giới thiệu — chia việc khác hẳn:

| Hệ thống | Code tự gộp khi | Embedding làm gì | Phần còn lại ai quyết |
|---|---|---|---|
| Microsoft GraphRAG 3.1.2 | tên **và** kiểu trùng khít | không tham gia gộp | không gộp |
| LightRAG 1.5.8 | tên đã làm sạch trùng khít | không tham gia gộp | không gộp |
| Graphiti (Zep) | tên chuẩn hoá trùng khít *và* chỉ có một ứng viên; hoặc Jaccard 3-gram ký tự của **tên** ≥ 0,9 | lấy tối đa 15 ứng viên theo cosine của **tên** (sàn 0,6) | LLM chọn; *"không chắc thì trả −1"* |
| KGGen (NeurIPS 2025) | SemHash ≥ 0,95 trên **tên** đã chuẩn hoá về số ít, embedding tĩnh Model2Vec | top-16, trộn 50/50 BM25 + embedding | LLM tìm trùng và chọn tên đại diện |
| Neo4j LLM Graph Builder | **không bao giờ** | cosine > 0,97 *hoặc* tên chứa nhau *hoặc* sửa < 3 ký tự, cùng nhãn | **người** bấm gộp |

Hai điều rút ra. Khi code tự quyết, nó quyết trên **chuỗi tên** — kể cả KGGen, vì embedding tĩnh trên tên
ngắn ở ngưỡng 0,95 gần với so chuỗi hơn so nghĩa. Và **không hệ nào trong năm hệ để embedding của mô tả
quyết định hai thứ là một** — trong khi đó đúng là thứ §650 định làm, vì A3 chỉ embed `description_draft`.
Những công trình tự gộp thẳng theo cosine đều là nguyên mẫu nghiên cứu — iText2KG (một ngưỡng cố định) và
DEG-RAG — và lý do DEG-RAG "chạy được" lại chính là lý do không nên chép nó (xem *Không nên làm*).

Lý do nằm ở bản chất phép đo: embedding đo **liên quan**, không đo **đồng nhất**.

- EDC (EMNLP 2024) ghi thẳng: chuẩn hoá bằng gom cụm embedding *"dễ tổng quát hoá quá mức"* — CESI gom
  *"is brother of"*, *"is son of"*, *"is main villain of"*, *"was professor of"* vào một cụm. EDC chữa bằng
  cách **để LLM xác minh** từng phép chuyển *"thay vì chỉ dựa vào độ giống embedding"*.
- ALIGN-SIM (Findings EMNLP 2024) thử 13 bộ mã hoá câu: không bộ nào đạt cả năm tiêu chí, và phần lớn
  **không tách được câu bị thay một từ trái nghĩa khỏi câu diễn đạt lại**.

Trong giáo trình, cặp nguy hiểm nhất có đúng hình dạng đó: Precision/Recall, L1/L2, sai lầm loại I/loại II,
biến ngẫu nhiên rời rạc/liên tục — hai định nghĩa trùng gần hết chữ, khác đúng một chỗ then chốt.

**Và lỗi gộp nhầm là lỗi câm.** Node gộp trông bình thường — đủ chunk, đủ alias, mô tả trôi chảy. Một khái
niệm học được biến mất khỏi lộ trình; không tầng nào sau báo. Ngược lại, tách sót (hai node "Overfitting")
nhìn là thấy, và tầng 3 đã có sẵn bước *"duplicate sót"* (§767) để vớt. Mục 4.1 phân tích bất đối xứng này.

Đề xuất rút gọn: **code chỉ tự gộp khi tên/alias chuẩn hoá trùng khít; embedding chỉ đề cử ứng viên
(blocking) — và là embedding của tên, không phải của mô tả.** Dữ liệu của chính dự án ở mục 2 chốt điều
này bằng số: luật ≥ 0,95 của §650 đúng 8/62 cặp; lớp tên đúng 56/58 nhóm.

---

## 2. Dữ liệu thật: A4/A5 sẽ gặp gì trên bốn tài liệu

Đo trên artifact A3 mới nhất — `nhap-mon-ml` v7, `xstk-ch3-1` v5, `baocao-canhan` v7, `naive-bayes` v5:
**377 ứng viên văn bản** + 79 media. Artifact đã lưu sẵn vector cho mọi ứng viên
(`gemini-embedding-001`, 768 chiều, `SEMANTIC_SIMILARITY`, **embed đúng `description_draft`, không có tên**),
nên phần lớn số dưới đây đọc thẳng từ file, không gọi API. Riêng thí nghiệm ở 2.4 gọi thêm 655 lượt
embed (tên, và "tên: description") cùng mô hình, cùng cấu hình. Nhãn trùng/khác là **một người gán
(phiên chính), chưa đối chiếu chéo** — đủ để thấy chiều, chưa đủ làm chuẩn vàng.

### 2.1 Lớp tên làm được gần hết việc, và làm đúng

Ứng viên A3 là **theo section** (`candidate_id` băm doc + section + tên), nên cùng một khái niệm ở ba
section là ba ứng viên. Chỉ riêng so khớp tên đã chuẩn hoá:

```
                ứng viên   tên y hệt   tên+alias   nhóm >1   đơn lẻ
nhap-mon-ml        105        84          81          15      66 (81%)
xstk-ch3-1         153       106         104          25      79 (76%)
baocao-canhan       57        46          43           9      34 (79%)
naive-bayes         62        43          41           9      32 (78%)
TỔNG               377       279         269          58     211 (78%)
```

- **Tên + alias gộp 29% số ứng viên** (377 → 269). Nới thêm (bỏ dấu, bỏ ký tự câu) chỉ thêm đúng
  **một** nhóm (`Giá trị tới hạn χα 2` / `χα^2`) — tầng chuẩn hoá chuỗi đã chạm trần.
- **Và gộp đúng.** Soát tay cả 58 nhóm: 56 nhóm là một khái niệm; 1 sai do alias (dưới đây); 1 mơ hồ —
  `Tiêu chuẩn kiểm định t` gom thống kê t của các phép kiểm định khác nhau (kiểm định tỉ lệ, kiểm định hai
  mẫu). Trong một tài liệu, đồng âm khác nghĩa hiếm; thứ sai là **draft**, không phải tên (2.6).
- **Alias trong ngoặc là tín hiệu xuyên ngôn ngữ chắc nhất** — cùng khái niệm mà một draft tiếng Anh, một
  draft tiếng Việt thì cosine mô tả chỉ 0,83–0,86, ngang nền tài liệu (mục 4.4):
  *"tranh chấp dữ liệu (Race Condition)"*, *"Lập trình đồng thời (Concurrency)"*, *"kiến trúc phân lớp
  (Layered Architecture)"*, *"Thu thập (data collection)"*, *"giai đoạn mô hình hoá (Modeling)"*.
  10 nhóm gộp nhờ alias: **7 đúng, 2 bàn được, 1 sai** — `"hàm mật độ xác suất f(x) ~ likelihood"`,
  dấu `~` (tương ứng với) bị A3 đọc thành bí danh, và phép hợp bắc cầu kéo cả ba ứng viên `Likelihood`
  vào `Hàm mật độ xác suất`. Alias có câu bằng chứng đi kèm nên kiểm được rẻ; không nên hợp mù.
- **Kiểu lệch là chuyện thường, không phải ngoại lệ**: 19/58 nhóm trùng tên mang hơn một `node_type`
  (`Cây quyết định` = algorithm/concept, `Độ tin cậy` = metric/concept), **11/58 nhóm hoà phiếu** — luật
  *"hoà thì agent chọn kèm evidence"* của Tầng 2a sẽ chạy ở khoảng một phần năm số nhóm. Chưa nhóm nào
  lệch `learnable`.

### 2.2 Embedding description **không phải tín hiệu đồng nhất**

```
cosine giữa hai ứng viên KHÁC tên (20.375 cặp) : p1 0,719 · p50 0,803 · p90 0,862 · p99 0,925
cosine giữa hai ứng viên CÙNG tên  (200 cặp)    : p0 0,770 · p50 0,901 · p90 0,974
                ≥ 0,95   ≥ 0,90   ≥ 0,85   ≥ 0,80   ≥ 0,75
khác tên          65      554    3.028   10.738   18.847
cùng tên       34/200  101/200  163/200  197/200  200/200
```

Nền đã 0,80: hai khái niệm bất kỳ trong cùng tài liệu đã "giống" nhau 0,80. Còn hai lần xuất hiện của
**cùng** khái niệm chỉ đạt trung vị 0,90, và chỉ 17% vượt 0,95. Hai phân bố chồng lên nhau gần hết.

**Có 31 cặp khác tên đạt ≥ 0,999 (29 ở `nhap-mon-ml`) — và cả 31 là description giống hệt từng chữ.** Khi
một section liệt kê, A3 viết cùng một câu chung cho mọi mục:

```
"Mô hình học máy dùng cho bài toán phân loại."   <- SVM · Naive Bayes · Cây quyết định · Rừng ngẫu nhiên
                                                    · K-NN · Mạng nơron nhân tạo · Mô hình xác suất
"Một phương pháp huấn luyện mô hình."            <- Bình phương tối thiểu · Ridge · LASSO
"Một vấn đề ... không đạt được khả năng tổng quát hóa cao."  <- Quá khớp · Kém khớp
"A variant of Naive Bayes used for discrete feature vectors." <- Multinomial NB · Bernoulli NB
```

Toàn corpus: 7 câu mô tả dùng chung cho 21 tên khác nhau. Và chiều ngược lại cũng đúng — cùng một khái
niệm, draft mô tả **vai trò tại chỗ được nhắc**, không phải định nghĩa: `Naïve Bayes` → *"Một thuật toán
được sử dụng để nhận dạng ký tự"*; `Quá khớp` → *"Vấn đề trong học máy cần kỹ thuật hiệu chỉnh để đối
diện"*. Hai đặc điểm đó cộng lại: **description đo "được nhắc trong bối cảnh nào", không đo "là cái gì".**

### 2.3 Mô phỏng đúng các luật spec đang ghi

**Tầng 2a bước 1 — "≥ 0,95 merge thẳng bằng code".** 62 cặp tên khác nhau vượt ngưỡng, gán nhãn tay:

| Loại | Số cặp | Ví dụ |
|---|---:|---|
| **Trùng thật** | **8 (13%)** | `Phương sai tổng thể σ 2` / `Phương sai tổng thể` · `WebSocket` / `WebSockets` |
| Cha–con / mơ hồ | 11 (18%) | `Giá trị tới hạn` / `Giá trị tới hạn t α` · `Hàm ước lượng` / `Trung bình mẫu` |
| **Khác hẳn** | **43 (69%)** | anh em `Ridge`/`LASSO` · đối nghịch `Quá khớp`/`Kém khớp`, `Học có`/`không giám sát` · đối xứng `Đường hồi quy mẫu Y theo X`/`X theo Y` · bù nhau `Độ tin cậy`/`Xác suất mắc sai lầm` |

Bỏ riêng các cặp description giống hệt ra, precision vẫn chỉ **7/31 = 23%**. Hợp bắc cầu như code sẽ làm:
269 → 228 node, trong đó **một node nuốt 11 ứng viên mang 9 tên** — SVM, Naive Bayes, Cây quyết định,
Rừng ngẫu nhiên, K-NN, Mạng nơron, Mô hình tuyến tính… Lỗi này **không có lượt gỡ nào phía sau**:
mọi tầng sau chỉ thấy một node.

**A4 gốc — "≥ 0,90 tự merge".** 269 → **115** node. Ở `xstk-ch3-1`, **một node nuốt 125/153 ứng viên** —
gần trọn chương ước lượng và kiểm định.

**Tầng 2a bước 2–3 — đồ thị ứng viên ngưỡng ~0,75, rồi Leiden hoặc connected components.** 92,5% số cặp
vượt 0,75, nên **mỗi tài liệu là đúng một thành phần liên thông** (105/105, 153/153, 57/57, 62/62). Nâng lên
0,85 vẫn còn 101/105 và 151/153. Louvain ở 0,75 chẻ mỗi tài liệu làm hai nửa (54+51, 88+65…). Nói cách
khác: đi đúng spec thì **cả tài liệu là một cụm, một lời gọi agent** — thứ spec sinh ra Tầng 2a để tránh.

Hai bộ ngưỡng này nhiều khả năng được mượn từ kinh nghiệm với một mô hình embedding khác. Với
`gemini-embedding-001` ở 768 chiều, trên văn bản cùng một miền, dải cosine bị nén vào 0,72–1,00;
ngưỡng tuyệt đối không mang được ý nghĩa mà spec gán cho nó.

### 2.4 Embed **cái gì** — thí nghiệm nhỏ

Ba biến thể, mỗi biến thể được chấm trên **chính top 38 cặp mà nó xếp cao nhất** (nhóm-với-nhóm, sau lớp
tên+alias; chấm như vậy để không thiên vị biến thể nào):

| Embed | Trùng thật | Cha–con / mơ hồ | Khác hẳn |
|---|---:|---:|---:|
| V1 `description` — **đang dùng** | 9 (24%) | 6 | **23 (61%)** |
| V2 **chỉ tên** | **22 (58%)** | 13 | 3 (8%) |
| V3 `tên: description` | 12 (32%) | 10 | 16 (42%) |

**Ghép description vào tên làm hỏng tín hiệu**, không làm giàu nó — đúng hệ quả của 2.2: câu mô tả
kéo các khái niệm anh em về cùng một chỗ. V2 còn lộ ra loại trùng mà V1 không thấy: biến thể chính tả
tiếng Việt (`Tỷ lệ tổng thể` / `Tỉ lệ tổng thể`, `Kiểm định giả thiết` / `giả thuyết`), định dạng ký hiệu
(`χ 0 2` / `χ0^2`), xuyên ngữ (`End-to-End testing` / `Kiểm thử End-to-End`), tên cụt (`Bernoulli Naive` /
`Bernoulli Naive Bayes`, `Maximum Likelihood` / `Maximum Likelihood Estimation`).

Nhưng **không biến thể nào cho phép quyết định bằng ngưỡng**: dải nền của cả ba đều nén (trung vị 0,76–0,83,
p99 0,90–0,95), và anh em có tên gần như trùng thì embedding tên cũng chịu —
`Đường hồi quy mẫu Y theo X` / `X theo Y` đạt 0,996 ở V2. Embedding chỉ dùng để **khoanh vùng**; quyết
định thuộc về thứ đọc được bằng chứng.

> **Một phân biệt spec đang gộp làm một.** Description embedding kéo bảy thuật toán phân loại lại gần
> nhau — **sai** cho A4 (chúng không phải một khái niệm) nhưng **đúng** cho A6/A7 (chúng thuộc một chủ
> đề). Spec dùng chung "embedding description" cho cả hai việc. Đồng nhất (identity) và liên quan
> (relatedness) cần hai tín hiệu khác nhau; vector đang lưu trong artifact A3 là tín hiệu thứ hai.

### 2.5 Một cấu hình khoanh vùng chạy được trên chính dữ liệu này

Gom bằng **connected components** thì luôn xích lại: kNN một chiều với k ≥ 3 nối **cả tài liệu** thành
một cụm; mutual-5NN vẫn ra cụm 56/81 và 55/104. Thay bằng **mutual-kNN + Louvain có trọng số**, đo độ
giữ trên một tập bạc 25 cặp trùng (phụ lục A):

| Embed | k | + n-gram tên | Louvain | Giữ cặp trùng | Cụm lớn nhất | Lời gọi agent (4 tài liệu) |
|---|---:|---|---|---:|---:|---:|
| tên | 3 | không | r = 1 | **25/25** | **13** | 56 |
| tên | 3 | có | r = 1 | **25/25** | **13** | 55 |
| tên | 3 | có | r = 2 | 24/25 | 10 | 61 |
| tên | 5 | có | r = 1 | 24/25 | 14 | 43 |
| description | 3 | không | r = 1 | 19/25 | 15 | 55 |
| description | 3 | có | r = 1 | 24/25 | 12 | 49 |

Tăng độ phân giải Louvain lên r = 2 đưa cụm lớn nhất về ≤ 10 — sát trần 9 mà LLM-CER đo được (mục 4.3) —
đổi lại mất 1/25 cặp. Cụm vượt trần vẫn phải chia thêm trước khi gọi agent.

Hai lưu ý trung thực: tập bạc được rút một phần từ chính top-list của V2 nên **thiên về kênh tên**; và 25
cặp là quá ít để chọn tham số — nó chỉ chứng minh **có tồn tại** cấu hình vừa giữ đủ cặp trùng vừa giữ cụm
≤ 13. Điều chắc chắn hơn: thêm cạnh n-gram tên kéo kênh description từ 76% lên 96% — trùng kiểu biến thể
tên là trùng **từ vựng**, và kênh từ vựng rẻ nhất.

Cụm ra trông đúng thứ agent cần thấy — ví dụ với mutual-5NN, r = 2: cụm "ước lượng" 11 nhóm chứa cặp trùng thật (`Khoảng ước lượng của
phương sai tổng thể` / `…của σ 2`) **cùng** các anh em dễ nhầm (`Ước lượng điểm`, `Ước lượng khoảng`,
`Hàm ước lượng`) — cặp trùng đứng cạnh thứ để đối chiếu.

### 2.6 A5 sẽ gặp gì

- **78% khái niệm là đơn lẻ** (211/269). Tầng 2a *"cụm 1 ứng viên: promote thẳng"* nghĩa là 78% khái niệm
  giữ nguyên draft — trung vị 82–108 ký tự, **khoảng một câu, và là câu vai trò chứ không phải định nghĩa**
  (2.2). A5 gốc lại đòi *mọi* concept có 2–4 câu viết từ toàn bộ chunk nguồn. Hai chỗ spec đang nói hai ý.
- **Draft sai ngay trong nhóm đúng tên.** Nhóm `Kém khớp` có một draft tả đúng… quá khớp (*"khả năng
  tổng quát hóa kém, thường liên quan đến độ phức tạp quá cao"*); nhóm `Prior probability` có draft
  *"The probability distribution on A, denoted as P(B)"*; nhóm `Evidence` có *"A fixed value or constant"*.
  Tổng hợp từ draft là chép lại lỗi, có khi chép cả lỗi trái nghĩa. A5 phải neo vào câu gốc.
- **Chi phí đọc toàn bộ chunk nguồn không đáng kể**: 86.668 token đầu vào cho cả 269 nhóm, gấp 1,8 lần
  corpus 48.763 token; nhóm nặng nhất 1.929 token. Không có lý do kinh tế nào để A5 chỉ đọc draft — mà đọc
  draft thì là tóm tắt lại các câu vai trò.
- **Ngôn ngữ trôi theo tên thuật ngữ, không theo tài liệu.** `baocao-canhan` có 82% từ mang dấu tiếng
  Việt, nhưng 32/57 draft viết tiếng Anh — 27 trong số đó là thực thể mang tên tiếng Anh; `naive-bayes`
  39/62. Trong nhóm trùng: **6/9 và 4/9 nhóm lẫn hai ngôn ngữ**. Description canonical buộc phải có luật
  ngôn ngữ — chọn theo ngôn ngữ chủ đạo của tài liệu (code đo được) hay theo đa số draft là **quyết định
  cần chốt**, không phải chi tiết cài đặt.
- **Tên canonical dính cùng vấn đề.** Luật §403 *"giữ tên phổ biến nhất"* chọn `Race Condition` (3 phiếu)
  thay `Tranh chấp dữ liệu` (2) trong một báo cáo tiếng Việt, và `Naïve Bayes Classification` (6) thay
  `Naïve Bayes` (2); `Modeling` / `Giai đoạn mô hình hoá` hoà 1–1. Luật chọn tên cần cùng một chính sách
  ngôn ngữ với mô tả, cộng một luật phá hoà tất định.

### 2.7 Một việc phải trả ngược về A3

Câu mô tả dùng chung cho các mục liệt kê là **lỗi của A3**, không phải của A4 — nhưng A4 là nơi nó nổ.
Chặn rẻ ở A3: cùng một section, hai thực thể khác tên mà description trùng từng chữ ⇒ cảnh báo (hoặc
bắt mô hình viết lại câu phân biệt). Nó cũng là dấu hiệu độ hạt ở F47: mục chỉ được *nhắc* trong một
danh sách thường không phải khái niệm được *giảng* ở đó.

---

## 3. Spec đúng ở đâu — theo văn liệu

### 3.1 Blocking rẻ, matching kỹ; blocking thiên về recall

Hai bước *đề cử → quyết định* là khung chuẩn của entity resolution (khảo sát Papadakis et al., ACM CSUR
2020). Lập luận ở §651 — *cặp trùng lọt khỏi cụm thì không bao giờ được gộp nữa, cặp thừa trong cụm thì
agent tách* — đúng nguyên lý, và Sparkly (PVLDB 2023) phát biểu cùng ý thành quy tắc vận hành: *"chọn k cho
đầu ra blocking lớn nhất mà bước matching gánh được, vì đầu ra càng lớn recall càng cao."* Chỗ cần sửa là
**cách** đạt recall (ngưỡng thấp + connected components), không phải mục tiêu — mục 4.3.

### 3.2 Quyết định theo cụm, không theo cặp

A4 gốc (§402) cho LLM xác nhận **từng cặp**; biến thể 2a (§653) cho agent xem **cả cụm**. Văn liệu 2024–2026
đứng hẳn về phía biến thể:

| Công trình | Phát hiện |
|---|---|
| *Match, Compare, or Select?* (COLING 2025) | Cho LLM **chọn** trong danh sách ứng viên: F1 81,60 so với 64,02 khi hỏi từng cặp (GPT-3.5). Khung ComEM (lọc bằng Flan-T5-XL, chọn bằng GPT-4o-mini) đạt 86,42 với chi phí 0,09 USD |
| LLM-CER (SIGMOD 2026) | Gom cụm trong ngữ cảnh (9 bản ghi mỗi lượt) so với hỏi từng cặp, cùng guardrail: độ chính xác ngang hoặc hơn, số lời gọi giảm 12–108 lần, chi phí giảm 3–22 lần. So với các phương pháp nền khác: độ chính xác cao hơn tới 150% |
| BatchER (arXiv 2312.03987) | Gộp nhiều câu hỏi vào một lời gọi: tiết kiệm 4–7 lần **và** precision cao hơn — vì mô hình tham chiếu được câu trả lời của các câu khác trong cùng lô |

ComEM nêu lý do sâu hơn: so cặp *"bỏ qua tính nhất quán toàn cục"* — A trùng B, B trùng C thì A phải trùng
C. Cho mô hình xem cả cụm là cách rẻ nhất để có tính bắc cầu. (Một sắc thái đáng ghi: với GPT-4o-mini,
chiến lược "so sánh" nhỉnh hơn "chọn" — 84,36 so với 82,26 — nhưng đắt gấp khoảng 7 lần.) Khảo sát 2025 về
dựng KG bằng LLM (arXiv 2510.20345) mô tả đúng quỹ đạo này ở phần hợp nhất thực thể: từ gom cụm heuristic
sang khung suy luận có cấu trúc — LLM-Align coi căn chỉnh là câu hỏi trắc nghiệm có ràng buộc, EntGPT sinh
ứng viên trước rồi mới suy luận để chọn.

### 3.3 Agent kiểm định được đọc nguồn

`read_source_chunk` (§653) khớp với cả ba hệ có bước kiểm định bằng LLM: Graphiti đưa **tin nhắn hiện tại
và các tin trước** vào prompt khử trùng; Graphusion *"truy hồi lại khái niệm từ văn bản gốc"* để phân xử
quan hệ mâu thuẫn; EDC đưa **câu nguồn** vào prompt chuẩn hoá. Không ai để LLM phán chỉ từ tên và mô tả.

### 3.4 Cha–con không gộp — và đề xuất `requires` cho cặp đó có cơ sở

- Wikidata, nơi gộp nhầm là sự cố vận hành thật: *"cây"* và *"cây sồi"* phải là hai mục vì sồi là
  *"subclass of"* cây.
- Ontology matching tách hẳn hai bài: **equivalence** và **subsumption** (Bio-ML, OAEI 2022, ISWC 2022).
- Prompt Graphiti: *"KHÔNG BAO GIỜ đánh dấu trùng nếu chúng liên quan nhưng khác nhau."*

Rubric §708 làm đúng. Còn việc đề xuất `requires` cho cặp cha–con: Pan et al. (ACL 2017) dùng chính luật
này — *"quan hệ tiên quyết thường tồn tại giữa cặp hạ danh–thượng danh"* — làm baseline trên dữ liệu MOOC:
precision **67–80%**, recall **15–27%**, vì *"khi A 'là một' B thì thường có tiên quyết từ B sang A, nhưng
rõ ràng không có chiều ngược lại."* Đây là tín hiệu **chính xác nhưng không chắc chắn**: 20–33% số cặp luật
hạ danh bắt được không phải tiên quyết (kể cả lỗi của chính mẫu trích). Đúng tư cách "đề xuất" mà spec gán,
và đúng lý do 2b phải *"xác minh lại, không copy nguyên"* (§726).

### 3.5 Phân vân thì hoãn

`deferred` (§710) khớp với Graphiti (*"trả −1 khi không có trùng **hoặc khi không chắc**"*) và Wikidata
(*"phải **tuyệt đối chắc chắn** chủ đề là một … không chắc thì hỏi"*). Spec chỉ thiếu một câu: **chiều mặc
định** khi phân vân — xem 4.1.

### 3.6 Kiểu theo đa số, hoà không lấy ngầm

§655 chặt hơn LightRAG: LightRAG cũng bỏ phiếu đa số (`Counter` các `entity_type`), nhưng hoà thì rơi về
**kiểu gặp trước** — đúng thứ spec cấm. Giữ nguyên luật của spec; lỗ hổng nằm ở chỗ khác (4.6).

### 3.7 Media đi đường tất định; cụm 2a tách khỏi cụm chủ đề

Khử trùng media bằng băm nội dung (§661) không cần văn liệu — nó tất định. Việc tách **cụm ứng viên** khỏi
**cụm chủ đề** (§652, `CONTEXT.md`) cũng đúng: GraphRAG dùng Leiden phân cấp để dựng **cộng đồng chủ đề**,
không bao giờ để khử trùng. Nhưng chính vì vậy, gợi ý dùng Leiden cho cụm ứng viên ở §652 đi ngược lý do
tách — mục 4.3.

### 3.8 …nhưng spec tự lệch ở tám chỗ

| # | Chỗ này | Lệch với |
|---|---|---|
| 1 | §401: `≥ 0,90` tự gộp, `0,80–0,90` hàng chờ | §650–651: `≥ 0,95` tự gộp, đồ thị `~0,75` |
| 2 | §402: LLM xác nhận **từng cặp** | §653: agent quyết **cả cụm** |
| 3 | §424 (A6): cosine mô tả `≥ 0,75` nghĩa là **liên quan** | §651 (2a): `~0,75` nghĩa là **nghi trùng** — một con số không thể mang cả hai nghĩa |
| 4 | §411 (A5): mọi khái niệm đã gộp đều qua LLM đọc toàn bộ chunk | §653, §660: agent 2a viết mô tả hợp nhất; cụm một ứng viên promote thẳng — singleton có qua A5 không, spec không nói |
| 5 | §708: cha–con là rộng/hẹp (*Regularization* / *L2 Regularization*) | Ví dụ JSON §717: *L2* là "khái niệm con" trong cụm *Overfitting* — L2 là **cách chữa** overfitting, không phải loại con của nó |
| 6 | §152: chuẩn hoá/gộp kiểu ở **tầng 3** | §655: bỏ phiếu kiểu canonical ở **2a**, tức trên chuỗi kiểu chưa chuẩn hoá |
| 7 | ADR 0004: vector mô tả *"quyết định cặp ứng viên nào lọt qua blocking"* — vai trò **đề cử** | §650, §881: embedding tự gộp — vai trò **quyết định** |
| 8 | §650: *"similarity ≥ 0,95 (tên chuẩn hoá + embedding description)"* | Không định nghĩa phép kết hợp — AND, OR hay trộn điểm? Hai đại lượng khác thang đo |

Tám chỗ này nên sửa **trước** khi viết spec A4 — spec lệch thì ticket lệch.

---

## 4. Rủi ro A4 có bằng chứng

### 4.1 🔴 Tự gộp bằng embedding đảo ngược bất đối xứng mà chính spec đã phát biểu đúng

Spec phát biểu đúng bất đối xứng cho **blocking**: lọt cặp trùng là mất vĩnh viễn, thừa cặp thì sửa được.
Nhưng ở bước **quyết định**, bất đối xứng quay chiều:

| Lỗi | Hậu quả trên lộ trình | Ai phát hiện |
|---|---|---|
| **Gộp nhầm** (L1 + L2 thành một) | Một khái niệm học được biến mất; bằng chứng, alias, tiên quyết của nó dồn vào node kia; quiz A11 hỏi lẫn | Không ai — node gộp trông bình thường |
| **Tách sót** (hai node "Overfitting") | Lộ trình có hai mục trùng; 2b có thể nối cạnh giữa chúng | Người nhìn thấy ngay; tầng 3 có bước *"duplicate sót"* (§767) |

Có một van an toàn gián tiếp: `flag_missing_node` của 2b (§689) có thể báo *"L1 Regularization"* bị thiếu.
Nhưng tầng 3 chỉ *"tạo node bổ sung"* (§766) — node gộp nhầm vẫn giữ bằng chứng và alias của L1. **Spec
không có thao tác tách.**

Các hệ trưởng thành đều chọn chiều thận trọng: Neo4j LLM Graph Builder, ngay cả ở cosine > 0,97, vẫn chỉ
**liệt kê** để người bấm gộp; Graphiti mặc định −1 khi không chắc; Wikidata đòi *"tuyệt đối chắc chắn"*.

Đề xuất:
1. Code chỉ tự gộp khi **tên hoặc alias chuẩn hoá trùng khít** và kiểu thuộc cùng nhóm (4.6). Bỏ tự gộp theo
   cosine ở §401 và §650; sửa §881 thành *"A4 = lớp tên + LLM"*.
2. **Không** dùng cosine mô tả làm quyền phủ quyết — trên dữ liệu thật nó báo động giả. Xếp 58 nhóm trùng
   tên theo cosine thấp nhất trong nhóm: nhóm alias sai (`Likelihood`) đứng thứ 3, nhưng hai nhóm thấp hơn
   đều đúng (draft tả hai ngữ cảnh khác nhau), còn nhóm mơ hồ `Tiêu chuẩn kiểm định t` đứng thứ 52. Thay
   vào đó, nhóm tự gộp theo tên vẫn đi vào lời gọi cụm dưới dạng **nhóm dựng sẵn — xác nhận hoặc tách**:
   cả corpus chỉ 58 nhóm nên gần như không tốn thêm, và agent bắt đồng âm (*bias* của mạng nơ-ron và *bias*
   của ước lượng) bằng bằng chứng thay vì bằng một con số.
3. Rubric ghi rõ chiều mặc định: **phân vân thì không gộp**, đánh `deferred`.
4. Thêm thao tác `split` cho tầng 3 và A13 (mục 6).

### 4.2 🔴 Ngưỡng cosine tuyệt đối không mang theo được — giữa mô hình, và cả giữa dữ liệu

Bốn con số 0,95 / 0,90 / 0,80 / 0,75 không gắn với mô hình nào. Văn liệu cho thấy chúng không thể gắn chung:

| Nguồn | Mô hình | Điều đo được |
|---|---|---|
| Model card `multilingual-e5-large` | E5 | Cosine *"phân bố quanh 0,7 tới 1,0"* do nhiệt độ InfoNCE thấp; *"thứ quan trọng là **thứ tự tương đối** của điểm, không phải giá trị tuyệt đối"* |
| iText2KG (arXiv 2409.03284) | `text-embedding-3-large` | Cặp thực thể **giống nhau** có cosine trung bình **0,6 ± 0,12**; họ chọn 0,7 làm ngưỡng precision cao |
| Zeakis et al. (PVLDB 2023) | S-GTR-T5 | Ngưỡng tối ưu cho matching dao động **0,55–0,70 giữa các bộ dữ liệu**, trung vị 0,625 — cùng một mô hình; *"chọn ngưỡng tối ưu là việc không tầm thường"* |
| HippoRAG (NeurIPS 2024) | Contriever / ColBERTv2 | Ngưỡng đồng nghĩa τ = 0,8 là **siêu tham số được tinh chỉnh** (HippoRAG 2, ICML 2025, giữ 0,8 cho bộ mã hoá của nó) |
| CESI (WWW 2018) | — | Ngưỡng gom cụm *"chọn trên tập validation giữ riêng"* |

Cơ chế nền đã được mô tả từ lâu: không gian biểu diễn của mô hình ngôn ngữ **không đẳng hướng** (Ethayarajh,
EMNLP 2019), nên mức cosine "nền" giữa hai văn bản bất kỳ khác nhau theo từng mô hình; Steck et al. (WWW 2024
Companion) còn chứng minh trên mô hình tuyến tính rằng cosine có thể cho độ giống *"tuỳ ý"*, phụ thuộc cách
điều chuẩn lúc huấn luyện.

Ghép lại: 0,75 với E5 nối gần như mọi cặp; 0,95 với `text-embedding-3-large` gần như không bao giờ kích
hoạt. Với `gemini-embedding-001` ở 768 chiều, `SEMANTIC_SIMILARITY`, trên mô tả tiếng Việt — mục 2 đã đo:
trung vị giữa hai khái niệm bất kỳ là **0,80**, ngưỡng 0,75 nối 92,5% số cặp, và 0,95 tự gộp đúng 13%.
Dự án rơi đúng vào trường hợp đầu (kiểu E5), không phải trường hợp sau.

Sparkly nói thẳng vì sao họ bỏ ngưỡng: *"chọn k dễ hơn chọn ngưỡng … dữ liệu thật nhiều nhiễu đến mức điểm
của nhiều cặp trùng khá thấp; ngưỡng cao giết recall, ngưỡng thấp làm đầu ra phình **không lường trước
được**; trong khi cặp trùng thường vẫn nằm trong top-k của nhau."* MILA (ontology matching, 2025) đi xa hơn:
chỉ chấp nhận không cần LLM khi hai phía là **top-1 của nhau** — điều kiện theo **thứ hạng**, không theo
ngưỡng — và ghi nhận nhánh đó cho precision cao, recall thấp.

Ba chi tiết riêng cho Gemini, từ tài liệu chính thức (cập nhật 2026-09-04):
- `gemini-embedding-001` ở số chiều khác 3072 **phải tự chuẩn hoá** vector. Tính cosine đầy đủ thì không sao;
  dùng tích vô hướng hay chỉ mục inner-product mà quên chuẩn hoá thì sai im lặng.
- `gemini-embedding-2` đã ra — đa phương thức, tự chuẩn hoá — nhưng **không nhận trường `task_type`**; tác vụ
  phải viết thành chỉ dẫn trong nội dung. Đổi sang đó là đổi hợp đồng gọi, không chỉ đổi tên mô hình, và
  theo ADR 0004 là đổi tập node.
- Google mô tả `SEMANTIC_SIMILARITY` cho *"duplicate detection"* — task type A3 đang dùng là đúng.

Đề xuất: blocking bằng **top-k theo từng kênh** (4.4). Nếu cần sàn tuyệt đối thì **hiệu chỉnh trên bộ vàng**
(mục 7) và ghi ngưỡng vào manifest cạnh `embedding_model_id` — đổi mô hình là hiệu chỉnh lại.

### 4.3 🔴 Connected components trên đồ thị ngưỡng thấp là single-linkage — sẽ xích thành cụm khổng lồ

Connected components trên đồ thị `cosine ≥ θ` **chính là** gom cụm single-linkage cắt ở θ: A giống B, B giống
C là đủ để A và C chung cụm dù A và C chẳng giống gì nhau.

- Hassanzadeh et al. (PVLDB 2009) so mười hai thuật toán gom cụm cho phát hiện trùng lặp. Kết luận về
  partitioning (bao đóng bắc cầu): *"xác nhận hiểu biết chung rằng cách tiếp cận có thể mở rộng này cho chất
  lượng nhóm trùng kém … kém ngay cả khi so với các thuật toán hiệu quả ngang nó"*; nó *"đặt nhiều bản ghi
  không giống nhau vào cùng cụm — recall cao nhưng precision thấp hẳn"*; và mọi thuật toán đều *"rất nhạy với
  ngưỡng"*.
- CESI chọn complete linkage *"vì nó cho cụm nhỏ hơn single và average linkage — hợp lý hơn cho bài toán chuẩn
  hoá, nơi cỡ cụm được kỳ vọng nhỏ."*
- Alper (arXiv 2605.25814, 2026) phê phán cả dây chuyền blocking → matching → clustering: lỗi của bước trước
  truyền sang bước sau, *"nhất là khi áp tính bắc cầu cứng trong gom cụm"* *(theo abstract)*.

Cộng thêm mâu thuẫn #3 ở mục 3.8: 0,75 là ngưỡng spec dùng cho **liên quan** ở A6. Nối các cặp liên quan rồi
lấy thành phần liên thông thì ra **cụm chủ đề** — cả mảng regularization, cả mảng kiểm định giả thuyết — đem
giao cho một lời gọi agent.

Mà cụm to là cụm LLM phán sai: LLM-CER đo được *"độ chính xác sụt rõ rệt khi cỡ tập vượt 9 hoặc 10"* (gán cho
*"tải nhận thức"*); cấu hình tối ưu của họ là **9 bản ghi** mỗi tập, thứ tự tuần tự, cân bằng.

Leiden cũng không phải lời giải: nó tối ưu modularity/CPM để tìm **cộng đồng** (đúng thứ A7 cần), có bước
ngẫu nhiên (phải cố định seed mới tái lập), và không có khái niệm "trần cỡ cụm" cho khử trùng.

Mục 2.3 và 2.5 xác nhận cả hai vế trên dữ liệu dự án. Ở 0,75, mỗi tài liệu là **một** thành phần; kNN một
chiều với k ≥ 3 cũng xích thành một cụm. Nhưng dùng Louvain làm **bước chia** — trên đồ thị mutual-kNN
(k = 3), có trọng số — thì cụm lớn nhất về 10–13 mà vẫn giữ 24–25/25 cặp trùng đã gán nhãn. Sai ở spec không
phải "Leiden" mà là **đồ thị đầu vào**: đồ thị ngưỡng tuyệt đối trên mô tả.

Đề xuất:
- Đồ thị ứng viên dựng từ **kNN** (mỗi ứng viên nối k láng giềng gần nhất theo từng kênh), không từ ngưỡng.
- Trần **~9 ứng viên mỗi lời gọi**. Thành phần vượt trần thì chia (Leiden có seed với CPM là một cách), rồi gộp
  tầng như bước Cluster Merge của LLM-CER: đại diện mỗi cụm con đi tiếp một lượt so.
- Hoặc bỏ gom cụm toàn cục, làm kiểu **neo + top-k** như KGGen: lấy một ứng viên, đưa nó cùng k láng giềng cho
  LLM chỉ ra cái nào trùng, gỡ cả nhóm khỏi hàng đợi, lặp lại. Đây chính là chiến lược "chọn" thắng rõ nhất
  ở ComEM.

### 4.4 🟠 Chỉ embed mô tả là thiếu kênh — và thiếu đúng ở ca spec lấy làm động cơ

Mục đích A4 theo §398: *"định nghĩa ở chương 2, ví dụ ở chương 5"* phải thành một node. Nhưng
`description_draft` sinh **theo section**: ở chương 2 nó tả định nghĩa, ở chương 5 nó tả cách dùng trong ví
dụ. Hai mô tả của cùng khái niệm có thể xa nhau — trong khi **tên** thì trùng. Kênh duy nhất A3 đang embed
lại là kênh yếu nhất ở đúng ca này.

Mọi hệ đã đọc đều dùng nhiều kênh:
- Graphiti: embedding **tên** + tìm toàn văn trên tên và tóm tắt (bài Zep, arXiv 2501.13956); mã hiện tại
  thêm so chuỗi khít và MinHash trên tên trước khi gọi LLM.
- KGGen: trộn BM25 và embedding.
- DeepBlocker (PVLDB 2021): **hợp** blocker học sâu tốt nhất với một blocker công nghiệp cho recall tốt hơn
  mà đầu ra tăng không đáng kể; Sparkly (TF-IDF top-k) còn thắng cả tổ hợp đó.
- Papadakis et al.: chạy nhiều lược đồ blocking trên cùng đầu vào *"để bền hơn với dữ liệu nhiều nhiễu."*

Ngược lại, mô tả **có** giá trị: trong DEG-RAG (arXiv 2510.14271), khử trùng gần như không cải thiện được
KG của HippoRAG trên hai bộ dữ liệu, và tác giả quy nguyên nhân cho việc KG đó *"chỉ có tên thực thể, không
có mô tả."* Ontology matching đi xa hơn theo cùng hướng: GenOM **sinh** định nghĩa cho khái niệm chỉ để làm
giàu biểu diễn trước khi truy hồi ứng viên, và ablation xác nhận bước đó có ích *(theo abstract)*.

Và một biến riêng của dự án: **ngôn ngữ**. Prompt viết tiếng Anh, không ép ngôn ngữ đầu ra; tài liệu tiếng
Việt kèm thuật ngữ tiếng Anh. Nếu `description_draft` lúc Việt lúc Anh giữa các section, cosine giữa hai mô
tả khác ngôn ngữ của **cùng** khái niệm sẽ bị kéo xuống. LAReQA (Google, 2020) gọi đúng tên yêu cầu: căn
chỉnh xuyên ngữ **"mạnh"** — cặp cùng nghĩa khác ngôn ngữ phải gần hơn cặp khác nghĩa cùng ngôn ngữ — và
cho thấy nó **không** có sẵn ở mBERT nguyên bản. Gemini Embedding vượt SOTA trước đó trên MMTEB (250+ ngôn
ngữ, có bitext mining — báo cáo kỹ thuật 03/2025) nên có thể tốt, nhưng phải đo trên đúng dữ liệu. Mục 2
đo được: cùng khái niệm, draft tiếng Anh với draft tiếng Việt chỉ đạt 0,83–0,86 (`Race Condition`,
`Database Transaction`, `Kiến trúc phân lớp`) — ngang nền của tài liệu — và 6/9 nhóm trùng của
`baocao-canhan` lẫn hai ngôn ngữ.

Đề xuất: blocking = **hợp** top-k của bốn kênh — tên/alias chuẩn hoá (khớp khít), 3-gram ký tự trên tên (bắt
*weight/weights*, *hồi quy tuyến tính / hồi quy tuyến tính đơn*), embedding **tên + alias**, embedding mô tả.

Mục 2.4 xếp hạng các kênh trên dữ liệu thật, và thứ hạng rõ: embedding **tên** cho 58% trùng thật ở top,
embedding mô tả 24%, ghép hai thứ vào một chuỗi 32% — mô tả **làm loãng** tín hiệu tên chứ không bổ sung.
Nên tên là kênh chính; kênh mô tả nếu giữ trong phép hợp thì k nhỏ (≤ 3), vì nó kéo cả họ anh em (bảy thuật
toán phân loại) vào một cụm. Kênh 3-gram thì đáng giá: nó kéo độ giữ của kênh mô tả từ 76% lên 96% (mục 2.5).

### 4.5 🟠 Bài toán là equivalence *và* subsumption — đừng để một cạnh xoá mất cái kia

Văn liệu gần nhất với "khử trùng khái niệm" không phải ER trên bản ghi mà là **ontology matching**: khái
niệm có nhãn, từ đồng nghĩa, định nghĩa — đúng hình dạng ứng viên A3 — và OAEI tách equivalence khỏi
subsumption thành hai bài riêng. LLMs4OM (ESWC 2024) đưa **khái niệm cha và con** vào ngữ cảnh khi hỏi LLM;
tương đương cho dự án là `section_path` của từng ứng viên.

Graphusion (miền giáo dục NLP) cho thấy cái giá của việc ép một cạnh mỗi cặp: luật fusion của họ là *"giữa
hai khái niệm chỉ cho phép một quan hệ"*; hình minh hoạ khung vẽ bước phân xử mâu thuẫn giữa các khái niệm dịch
máy với kết quả `HYPONYM_OF` ✗, `CONJUNCTION` ✗, `PREREQUISITE_OF` ✓. Quan hệ phân loại bị loại để giữ quan hệ
tiên quyết — và biến mất khỏi đồ thị.

Hệ kiểu mở của dự án không có ràng buộc đó. Đề xuất: khi agent 2a tách cha–con, ghi **hai** thứ — cạnh kiểu
mở `subtype_of` (có bằng chứng, phục vụ `traverse` ở pha B) **và** đề xuất `requires` con → cha kèm confidence
(Pan et al.: tín hiệu đúng khoảng 2/3–4/5 số lần). 2b xác minh cái sau; cái trước không vào DAG nên không cần.

Rubric nên có **bốn** nhánh chứ không phải hai: *cùng khái niệm* · *cha–con* · *anh em / liên quan* · *khác
hẳn*. ISO 704 dùng đúng bộ từ này — khái niệm cha, con, và *"khái niệm đồng cấp là anh em"*. Nhánh thứ ba
chính là chỗ ví dụ JSON §717 đang nhầm sang nhánh thứ hai.

### 4.6 🟠 Kiểu mở: làm khoá blocking thì tách nhầm, bỏ phiếu trên chuỗi thô thì chia phiếu

DEG-RAG đo được blocking **theo kiểu** là cách hiệu quả nhất trong ba cách họ thử — nhưng với tập kiểu cố
định. GraphRAG gộp theo cặp *(tên, kiểu)*, nên cùng tên khác kiểu là hai thực thể.

Với hệ kiểu mở, cả hai đều nguy hiểm: LLM có thể gọi cùng một khái niệm là `theorem` ở section này, `định lý`
ở section kia (tuân thủ schema chỉ 57–84% — báo cáo A3, mục 5b.1). Chặn cứng theo kiểu thì cặp trùng không
bao giờ gặp nhau. Và vì chuẩn hoá kiểu dời xuống tầng 3 (§152), phép bỏ phiếu ở §655 chạy trên chuỗi thô:
2 phiếu `định lý` + 1 `theorem` + 2 `concept` ⇒ `concept` thắng dù ba ứng viên nói "định lý".

Đề xuất: trước khi bỏ phiếu, chuẩn hoá **tối thiểu** chuỗi kiểu — casefold + ánh xạ từ sổ đăng ký đã được
người duyệt (`reviewed_node_types` mà A3 đã đọc). Kiểu là **tín hiệu mềm** trong prompt, không phải khoá blocking.

### 4.7 🟡 Thiết kế lời gọi trong cụm

- **Thứ tự.** ComEM: chiến lược nhiều bản ghi *"chịu thiên vị vị trí"* — độ chính xác thay đổi rõ khi bản ghi
  trùng dịch xuống danh sách. LLM-CER: đặt các bản ghi giống nhau **liền kề** tốt hơn. Cố định thứ tự còn phục
  vụ tái lập.
- **Guardrail bằng code sau mỗi quyết định.** LLM-CER kiểm từng phần tử: độ giống **nhỏ nhất** với cụm của nó
  thấp hơn độ giống **lớn nhất** với cụm khác ⇒ bị xếp nhầm ⇒ tạo lại tập. Thêm ~10% thời gian, FP-measure
  tăng tới 75%. Rẻ, tất định, không cần thêm lời gọi LLM.
- **Suy luận (thinking) không phải thuốc bổ chung.** Nghiên cứu 46 cấu hình trên ComEM (PAKDD, *theo
  abstract*): mức suy luận thấp là tối ưu cho GPT-5, mức cao giúp mô hình mở; Sonnet 4.5 tăng 10,13 F1 khi
  bật, Opus 4.5 giảm nhẹ với chi phí gấp 2,6. Phải đo trên đúng mô hình dự án dùng.
- **Ví dụ và luật không chắc giúp.** Peeters et al. (EDBT 2025): *"không có prompt tốt nhất chung — prompt tốt
  nhất phụ thuộc cặp mô hình/dữ liệu"*; ví dụ trong ngữ cảnh chỉ giúp khoảng 61% tổ hợp mô hình/dữ liệu, và
  *"lợi ích của in-context learning không thể mặc định mà phải đo cho từng tổ hợp"*; GPT-4 còn **mất 1–3 F1**
  trên mọi bộ dữ liệu khi thêm luật so khớp.
- **Schema đầu ra sâu.** Agent 2a phải cùng lúc: chia nhóm, chọn tên, gộp alias, viết mô tả, đề xuất cạnh,
  chọn kiểu. Báo cáo A3 (mục 3.3) đã dẫn mức suy giảm 10–15% với schema sâu. Tách **quyết định danh tính**
  khỏi **viết mô tả** (A5) hợp lý cả về chất lượng lẫn khả năng lưu vết. Hướng 2026 cũng vậy: CaRL-EM
  (arXiv 2609.01195) học cách chọn toán tử (so cặp / so sánh / chọn / quyết) theo độ khó của từng ca thay vì
  một khuôn cho mọi ca *(theo abstract)*.

### 4.8 🟡 Alias là đầu vào của mention map — alias sai lan ra toàn đồ thị

`CONTEXT.md` định nghĩa mention map dựng bằng **khớp tên chính xác** + độ gần ngữ nghĩa. Tên để khớp lấy từ
tên chuẩn + alias của node canonical. Một alias chung chung (*"mô hình"*, *"lỗi"*) gộp vào node sẽ khớp ở hàng
chục chunk — mention map phình, cặp chạm của 2b sai, co-occurrence của A6 sai.

Graphiti có đúng một cơ chế cho lớp lỗi này: tên **ngắn** (dưới 6 ký tự **và** chỉ một từ) hoặc **entropy ký
tự thấp** (< 1,5 bit) không được tự khớp mờ — đẩy cho LLM. Công trình dựng KG bài giảng đa phương thức gần dự
án nhất (arXiv 2608.03161) dùng **độ phủ đầu mút cạnh** (90,38% cạnh còn đầu mút sau khi gộp) làm chỉ số chẩn
đoán, và tự ghi nhận chưa giải xong *weight/weights, bias/biases, cost/loss function* — *"căng thẳng giữa gộp
quá tay và để alias vỡ vụn."*

Đề xuất: nửa đầu A3 đã làm — `verify_alias` bắt tên alias phải nằm trong câu bằng chứng định vị được
trong chunk. Lỗi còn lại ở mục 2.1 là lỗi **ngữ nghĩa**: câu *"hàm mật độ xác suất f(x) ~ likelihood"* chứa
chữ `likelihood` thật, nhưng `~` không có nghĩa "còn gọi là". Nên: alias chỉ được **tự gộp** khi câu bằng
chứng có dạng tương đương — ngoặc đơn sát tên, *"còn gọi là"*, *"hay"*, *"viết tắt"* — còn lại đưa agent
xét; tên/alias ngắn hoặc entropy thấp không bao giờ tự gộp.

---

## 5. A5 — Tổng hợp mô tả

### 5.1 🔴 GraphRAG và LightRAG tóm tắt **mô tả**, không đọc **nguồn** — và GraphRAG dạy LLM hoà giải mâu thuẫn

Đọc mã hai hệ phổ biến nhất:

| | GraphRAG 3.1.2 | LightRAG 1.5.8 |
|---|---|---|
| Đầu vào | danh sách **mô tả** do LLM viết ở bước trích | danh sách **mô tả** do LLM viết ở bước trích |
| Một mô tả | giữ nguyên, không gọi LLM | giữ nguyên, không gọi LLM |
| Vài mô tả | gọi LLM | **nối chuỗi, không gọi LLM** nếu < 8 mô tả và < 1.200 token |
| Nhiều mô tả | cuộn: vượt 4.000 token thì tóm tắt phần đầu rồi đưa bản tóm tắt vào lượt sau | map-reduce đệ quy |
| Thứ tự đưa vào | **sắp theo bảng chữ cái** | theo thời điểm, rồi mô tả dài trước |
| Khi mâu thuẫn | *"hãy giải quyết các mâu thuẫn và cho một bản tóm tắt nhất quán"* | *"trước hết xét xem mâu thuẫn có phải do **nhiều thực thể khác nhau trùng tên**; nếu có, tóm tắt **riêng từng cái**"* |
| Độ dài | tối đa 500 từ | khuyến nghị 600 token; ngôn ngữ đầu ra là **tham số khai báo** |

Ba điều đáng giữ lại:

- **Cả hai là "tóm tắt của tóm tắt".** Lỗi ở mô tả nháp truyền thẳng vào mô tả cuối; không lượt nào quay lại
  văn bản gốc. Spec A5 (§411) đòi đọc **chunk nguồn** — đúng hướng hơn cả hai, chỉ cần đúng liều (5.5).
- **GraphRAG sắp theo chữ cái** — xoá mất thứ tự trình bày, thứ giáo trình mang nhiều thông tin nhất (định
  nghĩa đến trước ví dụ). Với dự án, thứ tự đầu vào phải là thứ tự tài liệu.
- **LightRAG coi bước tổng hợp là chỗ phát hiện gộp nhầm** — mô tả mâu thuẫn là triệu chứng của hai khái niệm
  bị gom chung. Dự án nên đi xa hơn: mâu thuẫn **không được hoà giải** mà phải thành **cờ nghi gộp nhầm**, nối
  thẳng vào bước *"mô tả mâu thuẫn"* đã có ở tầng 3 (§767). Đây là van an toàn duy nhất cho lỗi câm ở 4.1.

### 5.2 🔴 Mô tả do LLM viết là đường rò kiến thức nền vào 2b

Rubric 2b (§727): *"0.9+ khi … Y xuất hiện trong định nghĩa của X."* Luật này có gốc vững trong văn liệu —
RefD (Liang et al., EMNLP 2015) đo quan hệ tiên quyết bằng chính cách hai khái niệm tham chiếu tới nhau — nhưng
nó chỉ đáng tin khi văn bản được đọc là **văn bản của tài liệu**. Nếu "định nghĩa" được đọc từ mô tả A5, thì
**kiến thức của mô hình** — không phải tài liệu — đang sinh ra cạnh có confidence cao nhất.

Rò rỉ này không phải giả thuyết:
- Maynez et al. (ACL 2020): ảo giác có mặt trong hơn 70% tóm tắt một câu, phần lớn là **ngoại lai** (thêm
  thông tin không suy ra được từ nguồn); và mô hình **tiền huấn luyện** là mô hình có tỉ lệ ảo giác ngoại lai
  **đúng sự thật** cao nhất. Mô hình càng giỏi, thứ nó thêm vào càng đúng — và càng khó nhận ra là không có
  trong tài liệu.
- Xie et al. (ICLR 2024): LLM tiếp nhận bằng chứng ngoài nếu nó mạch lạc, nhưng có **thiên vị xác nhận** mạnh
  khi bằng chứng lẫn thông tin khớp với trí nhớ tham số. Giáo trình định nghĩa khái niệm theo cách riêng (ký
  hiệu riêng, giản lược cho người mới) là đúng loại mà khảo sát của Xu et al. gọi là **xung đột ngữ cảnh–trí
  nhớ**; mô hình có xu hướng "sửa" về định nghĩa chuẩn.

Chính chuẩn viết định nghĩa tốt còn làm rò rỉ rõ hơn: ISO 704 yêu cầu định nghĩa nội hàm *"gồm khái niệm bao
trùm ngay trên nó, tiếp theo là các đặc trưng phân biệt."* Mô tả A5 viết đúng chuẩn sẽ **nêu tên khái niệm
cha** — và nếu cha đó do mô hình chọn chứ không phải tài liệu, luật 0,9 của 2b biến nó thành cạnh `requires`,
hoặc thành `flag_missing_node` nếu tài liệu không dạy khái niệm đó.

Đề xuất:
1. Luật *"Y trong định nghĩa X"* của 2b chạy trên **câu bằng chứng nguyên văn**, không trên mô tả A5.
2. Khái niệm cha nêu trong mô tả phải là **node có trong bảng canonical** hoặc trích được từ bằng chứng.
3. Đo trực tiếp: tỉ lệ mô tả A5 nhắc tới khái niệm **không có** trong bảng node và **không có** trong bằng
   chứng — đó là thước đo rò rỉ.

### 5.3 🟠 Ép "2–4 câu" khi nguồn mỏng là mời bịa

Belem et al. (NAACL 2025 Findings) đo ảo giác trong tóm tắt đa văn bản: tới **75%** nội dung tóm tắt là ảo
giác (trung bình trên năm LLM), dồn về **cuối** bản tóm tắt; khi được yêu cầu tóm tắt thông tin **không tồn
tại**, GPT-3.5-turbo vẫn viết 79,35% số lần, GPT-4o 44%. Lỗi chủ yếu: không theo chỉ dẫn, hoặc viết **chung
chung**.

Khái niệm chỉ có một câu bằng chứng mà bị đòi bốn câu thì ba câu sau lấy từ đâu? Từ trí nhớ mô hình — đúng
đường rò ở 5.2. Đề xuất: độ dài **tỉ lệ với lượng bằng chứng** — một câu nếu tài liệu chỉ nói một câu — và cho
phép ghi *"tài liệu không nói thêm"*.

### 5.4 🟠 "Có nguồn gốc theo cấu trúc" — A3 đã đi được nửa đường

CAMS (arXiv 2606.23989, 06/2026) là thiết kế gần nhất cho A5: bộ trích trả **mệnh đề + trích dẫn nguyên văn
+ id tài liệu** và **không bao giờ trả vị trí**; code định vị trích dẫn trong văn bản một cách tất định; mỗi
câu tóm tắt kết thúc bằng id mệnh đề trỏ về đúng khoảng ký tự. Họ phân biệt rạch ròi: **nguồn gốc là bất
biến** — đúng cho mọi câu, bất kể mô hình giỏi dở — còn **trung thực là mục tiêu** mà chọn lọc và kiểm định
chỉ khuyến khích. Kết quả *(theo abstract)*: độ chính xác quy nguồn đa văn bản 38% → 64%, thời gian người kiểm
mỗi mệnh đề giảm 3,4 lần.

A3 **đã có** nửa đầu: câu bằng chứng nguyên văn, định vị tất định vào chunk (`locate_evidence`). Nửa còn lại
cho A5: mỗi câu mô tả kết thúc bằng id bằng chứng; code kiểm id tồn tại và thuộc node — một **bất biến**, không
phải lời dặn trong prompt, đúng tinh thần executor của 2b.

Cỡ đơn vị trích dẫn: *Are Finer Citations Always Better?* (arXiv 2604.01432, 04/2026) đo được ép trích dẫn
**theo câu** làm chất lượng quy nguồn giảm 16–276% so với cỡ tốt nhất, và cỡ tốt nhất là **đoạn**
*(theo abstract)*. Chunk của dự án (mục tiêu 256 token) đúng cỡ đoạn: trích dẫn bằng `chunk_id`, không ép
xuống từng câu nguồn. ALCE (EMNLP 2023) nhắc rằng ngay cả khi có trích dẫn, mô hình tốt nhất vẫn thiếu hỗ trợ
đầy đủ khoảng **50%** số lần trên ELI5 — trích dẫn là điều kiện để **kiểm được**, chưa phải bảo đảm **đúng**.

### 5.5 🟠 Đọc gì: toàn bộ chunk, hay chỉ bằng chứng?

§411 đòi đọc toàn bộ `source_chunk_ids`. Với khái niệm lõi của giáo trình (xuất hiện ở hàng chục chunk) đó là
ngữ cảnh dài, và *Lost in the Middle* (TACL 2024) đo được mô hình dùng thông tin ở **giữa** ngữ cảnh dài kém
hẳn đầu và cuối. Còn chỉ đọc mô tả nháp thì thành tóm tắt của tóm tắt (5.1).

Điểm giữa có cơ sở: DEFT (LAW 2019) đo **28%** câu trong giáo trình mở cnx.org chứa định nghĩa — câu bằng
chứng A3 vốn dày thông tin định nghĩa. Đề xuất đầu vào A5: câu bằng chứng nguyên văn của mọi ứng viên theo
**thứ tự tài liệu**, cộng **toàn văn chunk định nghĩa** (chunk bằng chứng sớm nhất thuộc provenance) đặt **đầu**
ngữ cảnh; phần còn lại qua `read_source_chunk` khi cần. Ngôn ngữ đầu ra: không ép một ngôn ngữ cố định, nhưng
khai báo **quy tắc chọn** — theo ngôn ngữ của chunk định nghĩa — như LightRAG khai báo tham số ngôn ngữ tường
minh thay vì để mô hình tự đoán. Mục 2.6 cho thấy vì sao phải khai báo: ở `baocao-canhan`, 82% chữ trong tài
liệu là tiếng Việt mà 32/57 draft đang viết tiếng Anh — mô hình chọn ngôn ngữ theo **tên thuật ngữ**, không
theo tài liệu.

Và đầu vào phải là câu gốc chứ không phải draft, vì lý do mạnh hơn "tóm tắt của tóm tắt": mục 2.6 tìm được
draft **sai hẳn** nằm ngay trong nhóm đúng tên — một draft của `Kém khớp` tả quá khớp. Tổng hợp từ draft là
chép lại lỗi, kể cả lỗi trái nghĩa. Chi phí không phải lý do để tiết kiệm: đọc toàn bộ chunk nguồn của cả 269
nhóm chỉ 86.668 token, nhóm nặng nhất 1.929 token — ở quy mô bốn tài liệu hiện tại còn xa vùng "lost in the
middle". Giáo trình 500 trang thì khái niệm lõi mới chạm tới, và lúc đó cách xếp "bằng chứng + chunk định
nghĩa đặt đầu" ở trên mới thật sự cần.

### 5.6 🟡 Singleton: spec chưa quyết

GraphRAG và LightRAG đều **không gọi LLM** cho thực thể chỉ có một mô tả. Spec A5 gốc đòi mọi khái niệm; biến
thể promote singleton thẳng (§660) mà không nói có qua A5 không. Với singleton, `description_draft` của A3 đã
neo vào đúng một section, có câu bằng chứng — tổng hợp lại không thêm thông tin, chỉ thêm cơ hội rò rỉ.

Dữ liệu mục 2 buộc chỉnh lại đề xuất đó: **giữ draft không miễn phí.** Draft là câu *vai trò tại chỗ nhắc*
(`Naïve Bayes` → *"thuật toán dùng để nhận dạng ký tự"*), và có draft sai hẳn (`Prior probability` →
*"The probability distribution on A, denoted as P(B)"*). 78% khái niệm là singleton — giữ nguyên là giữ tỉ lệ
lỗi đó cho phần lớn đồ thị. Đề xuất: singleton đi một lượt **kiểm** rẻ theo lô — draft có được câu bằng chứng
hỗ trợ không; viết lại **chỉ khi** không được hỗ trợ, chỉ từ bằng chứng, cấm mở rộng thêm nội dung.

### 5.7 🟡 Kiểm định rẻ cho tiếng Việt chưa có sẵn

MiniCheck (EMNLP 2024) đạt mức GPT-4 trong kiểm tra câu có dựa trên tài liệu với chi phí **thấp hơn 400 lần**
— nhưng chính tác giả ghi: *"mô hình chỉ huấn luyện trên dữ liệu tiếng Anh … chưa đánh giá có hệ thống cho
ngôn ngữ khác."* Tài nguyên tiếng Việt có, nhưng thuộc miền tin tức: ViNLI (COLING 2022, hơn 30.000 cặp, hệ
tốt nhất còn cách người 14,2% độ chính xác) và ViFactCheck (AAAI 2025, 7.232 cặp) *(theo abstract)*. Chưa có bộ
kiểm nào được kiểm chứng cho câu định nghĩa giáo trình tiếng Việt.

Đề xuất: kiểm định = (1) code kiểm id trích dẫn hợp lệ — bất biến; (2) LLM chấm từng câu có được bằng chứng đã
dẫn hỗ trợ không; (3) lấy mẫu cho người ở A13. Không dùng mô hình NLI tiếng Anh làm cổng chặn khi chưa đo trên
dữ liệu dự án.

### 5.8 🟡 Hình dạng một mô tả tốt

- **Nội hàm, không vòng.** ISO 704: định nghĩa nội hàm (khái niệm bao trùm + đặc trưng phân biệt) *"nên dùng
  bất cứ khi nào có thể"*; định nghĩa vòng *"phải tránh."*
- **Đặc trưng phân biệt là thứ A4 cần.** ISO 704 viết định nghĩa phải *"phân biệt khái niệm với các khái niệm
  liên quan, **nhất là khái niệm đồng cấp**"* — tức đúng cặp anh em (L1/L2) làm embedding lẫn lộn ở mục 1. Mô
  tả nêu rõ đặc trưng phân biệt giúp cả người học lẫn lần gộp sau.
- **Độ cụ thể.** Văn liệu sinh định nghĩa gọi tên hai lỗi đối xứng: quá cụ thể (dính ngữ cảnh một ví dụ) và
  quá chung (Huang et al., EMNLP 2021 — *theo abstract*). Mô tả tổng hợp từ nhiều section dễ rơi vào lỗi thứ hai.
- **Hệ quả cho A6/A7.** Mô tả A5 sẽ được embed lại cho đồ thị liên quan. Mô tả viết theo một khuôn cố định
  (*"X là một … dùng để …"*) có thể kéo cosine giữa mọi cặp lên — ALIGN-SIM cho thấy chồng lấp từ ngữ bề mặt
  kéo điểm lên mạnh: câu bị xáo trật tự hay thay từ trái nghĩa vẫn được chấm gần câu gốc. Đo phân bố cosine
  trước và sau A5.

---

## 6. Định danh, nguồn gốc và gỡ merge

### 6.1 Gộp là thao tác khó đảo — ba tiền lệ

- **Wikidata:** *"ID mục được định là **định danh bền**. Vì vậy mục đã gộp phải được chuyển hướng. Không bao giờ
  dùng lại mục đã gộp cho thứ khác."* Gỡ một lần gộp phải khôi phục lịch sử theo đúng thứ tự; nếu bot đã thay
  các tham chiếu tới mục bị chuyển hướng thì phải nhờ người vận hành bot đảo lại.
- **Splink** (thư viện record linkage của Bộ Tư pháp Anh): gom cụm bằng connected components trên các cặp có
  **xác suất khớp** vượt ngưỡng; `cluster_id` là `unique_id` **nhỏ nhất** trong cụm — ổn định chỉ khi thành viên
  cụm không đổi. Người duy trì viết: *"không rõ có thể có cluster ID tất định hay không khi bất kỳ bản ghi mới
  nào cũng có thể nối hai cụm."*
- **Gruenheid et al. (PVLDB 2014):** liên kết tăng dần phải cho phép **dùng bằng chứng mới để sửa quyết định
  cũ** — không chỉ thêm bản ghi vào cụm có sẵn.

### 6.2 Đề xuất cho dự án — khớp ADR 0001

- **Id neo.** `candidate_id` đã là băm `(doc, section, tên)`. Id node canonical = hàm tất định của **ứng viên
  neo** — ứng viên sớm nhất trong provenance. Ổn định chừng nào ứng viên neo còn trong nhóm, cùng khuôn với
  Splink và "mục nhận" của Wikidata.
- **Bảng chuyển hướng.** Khi neo đổi (gộp hai nhóm, tách một nhóm), id cũ trỏ sang id mới — người đang học trên
  `graph_version` cũ không gãy tiến độ, đúng lời hứa của A13.
- **Nhật ký gộp.** Mỗi quyết định: thành viên, nhãn (cùng / cha–con / anh em / khác / hoãn), lý do, id bằng
  chứng, mô hình, `prompt_hash`. Hassanzadeh et al. kết luận đúng điều này: *"không thuật toán gom cụm nào cho
  kết quả hoàn hảo, nên giữ cả thông tin định lượng mà thuật toán sinh ra"* chứ không chỉ kết quả gom.
- **Thao tác `split`** cho tầng 3 và A13 — thứ spec hiện không có (4.1).
- **Cache quyết định theo băm đầu vào.** Cùng cụm, cùng prompt, cùng mô hình ⇒ dùng lại quyết định — đúng khuôn
  record–replay A3 đã có (`prompt_hash`); GraphRAG và LightRAG cũng cache lời gọi LLM ở bước này. Chạy lại A4
  sau khi sửa một section chỉ gọi lại những cụm thật sự đổi.

ADR 0004 vẫn đúng nhưng **hẹp phạm vi** đi: khi embedding chỉ đề cử, đổi mô hình chỉ đổi **recall của
blocking**, không trực tiếp đổi danh tính — vẫn phải chạy lại, nhưng sai số bị LLM chặn thay vì truyền thẳng
vào tập node.

### 6.3 Provenance khác mention — `first_order_index` phải lấy từ provenance

§403: *"lấy `first_order_index` nhỏ nhất"*. `CONTEXT.md` tách **provenance** (nơi khái niệm được **dạy / định
nghĩa**) khỏi **mention** (nơi chỉ được **nhắc**). Nếu một ứng viên đến từ phần tổng quan chương 1 chỉ nhắc
tên, min index kéo vị trí của khái niệm về chương 1 — và doc-order prior của 2b (*"edge ngược thứ tự tài liệu
… trừ 0.1 confidence"*, §727) tính sai chiều. Study Navigator (JEDM 2014) dựng cả hệ thống quanh đúng phân
biệt này: với mỗi section, chỉ ra khái niệm cần biết **và section nơi nó được giảng**.

Đề xuất: node giữ vai trò của từng lần xuất hiện; `first_order_index` lấy min trên provenance; lưu riêng
`first_mention_index`.

### 6.4 Nối lại cạnh A3 sau khi gộp

Cạnh A3 trỏ `candidate_id`; sau gộp phải ánh xạ về node canonical. Công trình KG bài giảng (2608.03161) ghi rõ
chỉ nối đầu mút **sau** khi khử trùng, và dùng tỉ lệ cạnh giữ được làm chỉ số chẩn đoán. Hai ca biên cần luật:
cạnh giữa hai ứng viên bị gộp làm một (thành vòng tự thân ⇒ bỏ, ghi đếm), và nhiều cạnh cùng kiểu giữa cùng cặp
node (gộp bằng chứng về một cạnh — cùng khuôn `_dedupe_document_candidates` đang làm trong phạm vi section).

---

## 7. Cách đo

Báo cáo A3 kết luận khoảng trống lớn nhất là phép đo. A4 đo được rõ hơn A3 nhiều, vì *"hai ứng viên có phải
một khái niệm không"* ít tranh cãi hơn *"đây có phải một khái niệm không"*.

**Bộ vàng cặp.** Lấy mẫu cặp từ đầu ra blocking, **phân tầng theo dải điểm** (cao / giữa / thấp) để có đủ ca
khó; nhãn bốn loại khớp rubric: *cùng* · *cha–con* · *anh em / liên quan* · *khác*. Khoảng 200 cặp cho sai số
precision cỡ ±4–6 điểm quanh mức 80–90% (khoảng tin cậy nhị thức 95%). Cặp **cùng tên** nên có một tầng riêng
— nơi đồng âm lộ ra. Hạt giống đã có sẵn ở **phụ lục A**: 25 cặp trùng thật mà lớp tên không bắt, 23 cặp âm khó,
11 cặp cha–con/mơ hồ, 1 alias sai — gán trong buổi đo của mục 2, cần người thứ hai gán độc lập trước khi dùng.

| Chỉ số | Đo gì | Cơ sở |
|---|---|---|
| Recall blocking (pairs completeness) | Cặp trùng thật có nằm chung cụm không — trần cứng của A4 | Papadakis; Zeakis; Sparkly |
| Pairwise P/R/F1 | Quyết định gộp từng cặp | chuẩn ER |
| B-cubed | Chất lượng phân cụm theo từng phần tử | Amigó et al. 2009: chỉ số duy nhất thoả mọi ràng buộc hình thức họ đặt ra *(theo abstract)* |
| GMD, chi phí gộp > chi phí tách | Mã hoá đúng bất đối xứng ở 4.1 | Menestrina et al. (PVLDB 2010): chi phí tách/gộp cấu hình được; các chỉ số ER quen dùng *"thường mâu thuẫn nhau khi xếp hạng thuật toán"* |
| Cỡ cụm lớn nhất, phân bố cỡ cụm | Hiện tượng xích; bao nhiêu cụm vượt trần 9 | Hassanzadeh; LLM-CER |
| Jaccard quyết định giữa hai lần chạy cùng prompt | Tính tái lập của A4 | cùng khuôn `a3-compare` (vòng 18: node 1,000 nhưng cạnh chỉ 0,321) |
| Độ phủ đầu mút | % cạnh A3 còn đầu mút sau gộp | arXiv 2608.03161 |
| Tỉ lệ gộp | Quá cao ⇒ A3 cắt vụn hoặc gộp nhầm; quá thấp ⇒ blocking hụt | báo cáo A3, mục 6 |

**A5:** tỉ lệ câu có id trích dẫn hợp lệ (code — phải là 100%); tỉ lệ câu được bằng chứng hỗ trợ (LLM chấm +
mẫu người); tỉ lệ mô tả nhắc khái niệm ngoài bảng node và ngoài bằng chứng (thước đo rò rỉ, 5.2); cosine trước
và sau A5 trên các cặp anh em đã gán nhãn (5.8).

---

## 8. Đề xuất, xếp theo thứ tự

| # | Việc | Vì sao thứ tự này |
|---|---|---|
| 0 | **Sửa tám chỗ spec tự lệch** (mục 3.8), trước hết #1, #3, #7 | Spec lệch thì ticket lệch; ba chỗ đó quyết định kiến trúc |
| 1 | **Code chỉ tự gộp khi tên/alias chuẩn hoá trùng khít**, kiểu cùng nhóm; alias chỉ tự gộp khi câu bằng chứng có dạng tương đương; nhóm tự gộp vẫn hiện cho agent để **xác nhận hoặc tách**; bỏ tự gộp theo cosine (§401, §650); sửa MVP §881 thành "lớp tên + LLM" | Gộp nhầm là lỗi câm; trên dữ liệu thật ≥ 0,95 đúng 8/62 cặp (2.3), lớp tên đúng 56/58 nhóm (2.1); không hệ thật nào để embedding mô tả quyết danh tính |
| 2 | **Blocking = hợp top-k các kênh, lấy tên làm chính**: tên/alias khớp khít, 3-gram ký tự, embedding **tên** (A4 tự embed — vector mô tả của A3 để lại cho A6/A7); kênh mô tả nếu giữ thì k ≤ 3. Khởi điểm đã đo: mutual-3NN + n-gram + Louvain có seed (2.5). Sàn tuyệt đối nếu có thì hiệu chỉnh theo `embedding_model_id`, ghi vào manifest | Ngưỡng không mang theo được; trên dữ liệu thật kênh tên cho 58% trùng thật ở top, kênh mô tả 24% (2.4) |
| 3 | **Bỏ connected components**; cụm từ đồ thị kNN, trần ~9, chia bằng Leiden có seed hoặc làm kiểu neo + top-k | Single-linkage xích thành cụm chủ đề; quá 9 thì LLM tụt chính xác |
| 4 | **Rubric bốn nhánh**; cha–con ghi cạnh mở `subtype_of` + đề xuất `requires` có confidence; sửa ví dụ JSON §717 | OAEI tách equivalence/subsumption; tín hiệu cha–con đúng 67–80% nên chỉ là đề xuất |
| 5 | **Mặc định khi phân vân: không gộp**, `deferred` | Gộp nhầm đắt hơn tách sót |
| 6 | **Nhật ký gộp + id neo + bảng chuyển hướng + thao tác `split`**; cache quyết định theo băm đầu vào | Gộp khó đảo; tái lập; A13 cần gỡ được |
| 7 | **Guardrail kiểu MDG bằng code** sau mỗi quyết định cụm | LLM-CER: +75% FP-measure với 10% thời gian, không thêm lời gọi |
| 8 | **Chuẩn hoá tối thiểu chuỗi kiểu trước khi bỏ phiếu** | Phiếu bị chia giữa `định lý` / `theorem` |
| 9 | **A5 có nguồn gốc theo cấu trúc**: đầu vào = bằng chứng nguyên văn theo thứ tự tài liệu + chunk định nghĩa; mỗi câu kết thúc bằng `chunk_id`, code kiểm; độ dài theo bằng chứng; mâu thuẫn ⇒ cờ nghi gộp nhầm | CAMS, ALCE, Belem et al.; A3 đã có nửa đầu |
| 10 | **Luật "Y trong định nghĩa X ⇒ 0,9" của 2b chạy trên bằng chứng nguyên văn** | Chặn kiến thức nền của mô hình sinh cạnh confidence cao nhất |
| 11 | **Singleton: kiểm draft với bằng chứng theo lô, viết lại chỉ khi không được hỗ trợ** | 78% khái niệm là singleton; draft là câu vai trò và có draft sai hẳn (2.6) — giữ nguyên là giữ lỗi, viết lại tự do là mở đường rò (5.2) |
| 12 | **Bộ vàng ~200 cặp** + recall blocking + B-cubed + GMD bất đối xứng + Jaccard hai lần chạy | Không đo thì không biết các việc trên có tác dụng không |
| 13 | **Tên/alias ngắn hoặc entropy thấp không tự gộp** (alias có mặt trong văn bản thì A3 đã kiểm; phần ngữ nghĩa nằm ở #1) | Alias nuôi mention map, sai là lan |
| 14 | **Đo mức suy luận và few-shot trên đúng mô hình** trước khi bật | Tác dụng đổi chiều theo họ mô hình (PAKDD; EDBT 2025) |
| 15 | **Chốt chính sách ngôn ngữ** cho mô tả và tên canonical, kèm luật phá hoà tất định — **trước** khi viết spec A5 | Draft lẫn Việt/Anh theo tên thuật ngữ; "tên phổ biến nhất" chọn `Race Condition` trong báo cáo tiếng Việt (2.6). Là quyết định sản phẩm, không phải chi tiết cài đặt |
| 16 | **Trả về A3**: cảnh báo khi hai thực thể khác tên cùng section có description trùng từng chữ | 29 cặp cosine 1,000 ở `nhap-mon-ml` đều do câu mô tả dùng chung cho mục liệt kê (2.2, 2.7); rẻ, chặn tận gốc |

**Không nên làm**

- **Bê độ mạnh tay của GraphRAG-QA sang đây.** DEG-RAG gộp tới 70% thực thể mà chất lượng hỏi đáp **không
  giảm** trên hai bộ dữ liệu — kể cả khi *"các thực thể chỉ giống nhau sơ sơ và chung láng giềng cũng bị hút
  vào một node"*. Điều đó nói về **thước đo QA** — nó không nhạy với gộp nhầm — chứ không nói gộp nhầm vô hại.
  Lộ trình học thì nhạy: mỗi node học được là một đơn vị người học phải hoàn thành.
- **Thay gộp bằng cạnh đồng nghĩa** (kiểu HippoRAG) cho node học được: topo vẫn thấy hai node, lộ trình vẫn
  trùng; DEG-RAG cũng đo được gộp trực tiếp tốt hơn chỉ nối đồng nghĩa.
- **Chép prompt tổng hợp của GraphRAG**: "hoà giải mâu thuẫn" giấu mất tín hiệu gộp nhầm; sắp theo chữ cái xoá
  thứ tự tài liệu.
- **Ép trích dẫn xuống từng câu nguồn**: cỡ đoạn cho quy nguồn tốt hơn; `chunk_id` là đủ.
- **Dùng mô hình NLI tiếng Anh làm cổng chặn** cho mô tả tiếng Việt khi chưa đo.
- **Chưng cất sang mô hình nhỏ** (Steiner & Bizer, arXiv 2606.28823): hợp khi có hàng triệu cặp. Dự án có
  vài trăm ứng viên mỗi tài liệu — chi phí LLM ở A4 không phải ràng buộc, độ đúng mới là.

---

## 9. Kết luận

**Tầng 2a đúng ở phần khó nhất.** Quyết định theo cụm thay vì theo cặp, cho agent đọc nguồn, hoãn khi phân
vân, tách cha–con, để media đi đường tất định — cả năm điều đều có văn liệu 2024–2026 đứng sau, và ở vài chỗ
(bỏ phiếu kiểu, cấm lấy ngầm ứng viên đầu) spec còn chặt hơn hệ thống đang chạy.

**Nhưng spec đặt nhầm chỗ quyền quyết định.** Nó giao cho embedding quyền nói hai ứng viên là một — ở ba chỗ,
kể cả cấu hình MVP. Văn liệu và mã nguồn đồng thuận hiếm thấy ở điểm ngược lại: embedding **đề cử**, còn
danh tính do chuỗi tên, LLM hoặc người quyết. Lý do không phải kỹ thuật vặt mà là bản chất phép đo — embedding
đo liên quan — cộng với một bất đối xứng mà chính spec đã phát biểu cho blocking nhưng quên áp cho bước quyết
định: gộp nhầm là lỗi câm, tách sót thì nhìn thấy. Các con số 0,95 / 0,90 / 0,75 thì không có nghĩa khi tách
khỏi mô hình và dữ liệu chúng được hiệu chỉnh; và riêng 0,75 đang được dùng cho hai nghĩa trái nhau.

**Dữ liệu của chính dự án nói cùng một điều, bằng con số.** Trên bốn tài liệu, nền cosine giữa hai khái niệm
bất kỳ là 0,80, nên ngưỡng 0,75 của Tầng 2a biến mỗi tài liệu thành một cụm duy nhất; luật ≥ 0,95 tự gộp đúng
8/62 cặp và nuốt bảy thuật toán phân loại vào một node; 31 cặp khác tên đạt cosine ≥ 0,999 chỉ vì A3 viết cùng
một câu cho các mục trong một danh sách. Ngược lại, lớp tên + alias gộp 29% số ứng viên và đúng 56/58 nhóm, và embedding
**tên** đề cử trùng thật tốt gấp đôi embedding mô tả. Văn liệu nói *nên* chia việc như vậy; dữ liệu nói *phải*.
Mô tả đo "được nhắc trong bối cảnh nào" — đúng tín hiệu cho A6/A7, sai tín hiệu cho A4.

**A5 là chỗ kiến thức của mô hình lọt vào đồ thị nhiều nhất** — không phải vì mô hình bịa sai, mà vì nó bịa
**đúng**: một định nghĩa chuẩn sách giáo khoa chung chung thay cho định nghĩa của chính tài liệu. Và 2b đọc mô
tả để suy tiên quyết với confidence cao nhất. Dự án có sẵn mảnh ghép khó nhất để chặn đường rò này: câu bằng
chứng nguyên văn, định vị tất định từ A3. CAMS 2026 cho thấy đó chính là nền của tóm tắt *"có nguồn gốc theo
cấu trúc"* — nguồn gốc là bất biến do code giữ, không phải lời dặn trong prompt.

**Và khoảng trống lớn nhất lặp lại lần thứ ba: phép đo.** Khác B0 và A3, ở A4 "đáp án đúng" ít tranh cãi — bộ
vàng 200 cặp bốn nhãn là làm được trong một buổi, và GMD cho phép mã hoá thẳng bất đối xứng gộp/tách vào con số.
Không có nó thì mọi ngưỡng trong spec — kể cả những ngưỡng báo cáo này đề xuất thay — vẫn là đoán.

---

## Phụ lục A — Tập bạc cho A4 (gán tay 2026-09-11, một người gán)

Hạt giống cho bộ vàng merge, cùng vai trò với `tests/fixtures/a3/gold-entities.json` ở A3. Chưa đối chiếu
chéo; trước khi dùng làm chuẩn cần người thứ hai gán độc lập.

**Trùng thật — lớp tên+alias không bắt được (25 cặp):**

| Tài liệu | Cặp | Loại trùng |
|---|---|---|
| nhap-mon-ml | `Mạng nơron nhân tạo` / `Mạng nơron` | tên cụt |
| nhap-mon-ml | `Không gian dữ liệu` / `Không gian dữ liệu X` | đuôi ký hiệu |
| nhap-mon-ml | `Kỹ thuật hiệu chỉnh` / `Hiệu chỉnh` | tiền tố thể loại |
| nhap-mon-ml | `Bài toán học máy` / `Bài toán học` | tên cụt |
| xstk-ch3-1 | `Khoảng ước lượng của phương sai tổng thể` / `Khoảng ước lượng của σ 2` | ký hiệu thay chữ |
| xstk-ch3-1 | `Phương sai tổng thể σ 2` / `Phương sai tổng thể` | đuôi ký hiệu |
| xstk-ch3-1 | `Ước lượng trung bình μ` / `Ước lượng trung bình` | đuôi ký hiệu |
| xstk-ch3-1 | `Giá trị tới hạn χα 2` / `Giá trị tới hạn χα^2` | định dạng ký hiệu |
| xstk-ch3-1 | `Ước lượng trung bình` / `Ước lượng trung bình tổng thể` | tên cụt |
| xstk-ch3-1 | `Tiêu chuẩn kiểm định χ 0 2` / `Tiêu chuẩn kiểm định χ0^2` | định dạng ký hiệu |
| xstk-ch3-1 | `Tỷ lệ tổng thể` / `Tỉ lệ tổng thể` | chính tả y/i |
| xstk-ch3-1 | `Đường hồi quy tuyến tính mẫu` / `Phương trình đường hồi quy tuyến tính mẫu` | đối tượng / phương trình của nó |
| xstk-ch3-1 | `Kiểm định giả thiết thống kê` / `Bài toán kiểm định giả thiết thống kê` | tiền tố thể loại |
| xstk-ch3-1 | `Kiểm định giả thiết thống kê` / `Kiểm định giả thuyết` | chính tả thiết/thuyết |
| baocao-canhan | `WebSocket` / `WebSockets` | số nhiều |
| baocao-canhan | `Container hóa` / `Docker hóa` | đồng nghĩa theo ngữ cảnh |
| baocao-canhan | `Kiến trúc Hub - Client` / `Mô hình Hub - Client` | tiền tố thể loại |
| baocao-canhan | `End-to-End testing` / `Kiểm thử End-to-End` | xuyên ngữ |
| baocao-canhan | `WebSockets` / `Giao thức WebSockets` | tiền tố thể loại |
| baocao-canhan | `Transaction` / `Database Transaction` | tên cụt (theo ngữ cảnh báo cáo) |
| naive-bayes | `Vấn đề xác suất bằng 0` / `Xác suất bằng 0` | tiền tố thể loại |
| naive-bayes | `Prior` / `Prior probability` | tên cụt |
| naive-bayes | `Maximum Likelihood Estimation` / `Maximum Likelihood` | tên cụt |
| naive-bayes | `Bernoulli Naive` / `Bernoulli Naive Bayes` | tên cụt |
| naive-bayes | `Bài toán phân loại mail` / `Phân loại email` | diễn đạt khác |

**Khác hẳn nhưng embedding xếp rất gần (23 cặp âm khó):**

- *Anh em*: `Ridge`/`LASSO` · `SVM`/`Naive Bayes` · `K-NN`/`Cây quyết định` · `Rừng ngẫu nhiên`/`Cây quyết định` ·
  `Mô hình tuyến tính`/`Mạng nơron` · `Kiểu mô hình`/`Giải thuật học` · `Multinomial Naive Bayes`/`Bernoulli Naive Bayes` ·
  `Bài toán tìm độ tin cậy`/`Bài toán tìm kích thước mẫu` · `Trung bình mẫu`/`Tỉ lệ mẫu tổng quát` ·
  `Trung bình mẫu`/`Phương sai mẫu hiệu chỉnh` · `Trung bình tổng thể`/`Phương sai tổng thể` ·
  `Ước lượng trung bình`/`Ước lượng phương sai` · `Ước lượng tỉ lệ`/`Xác định kích thước mẫu` ·
  `Kiểm định giả thiết về trung bình tổng thể`/`…về phương sai tổng thể` · `Độ lệch mẫu`/`Độ lệch mẫu hiệu chỉnh` ·
  `Quá trình học`/`Quá trình phân lớp` · `Maximum Likelihood Estimation`/`Maximum A Posteriori`
- *Đối nghịch*: `Quá khớp`/`Kém khớp` · `Học có giám sát`/`Học không giám sát` · `Prior probability`/`Posterior probability`
- *Đối xứng*: `Đường hồi quy mẫu Y theo X`/`X theo Y` · `Mẫu theo dấu hiệu X`/`Y`
- *Bù nhau*: `Độ tin cậy` (1−α) / `Xác suất mắc sai lầm` (α)

**Cha–con hoặc mơ hồ — đúng loại phải để agent phán, không cho code quyết:**
`Giá trị tới hạn`/`Giá trị tới hạn t α` · `Tiêu chuẩn kiểm định`/`Tiêu chuẩn kiểm định t` ·
`Hàm ước lượng`/`Trung bình mẫu` · `Xác định kích thước mẫu`/`…trong ước lượng trung bình` ·
`Khoảng ước lượng của tỉ lệ tổng thể`/`Ước lượng tỉ lệ` · `Mô hình sinh`/`Mô hình` ·
`Gaussian Naive Bayes`/`Naïve Bayes` · `Probabilistic Graphical Model`/`Bayesian network` ·
`Cơ chế đồng bộ hóa`/`Mutex` · `Thiết kế Cơ sở dữ liệu`/`ERD` · `Branching`/`Branching strategy`

**Alias sai đã lọt vào lớp tên:** `Likelihood` ← `Hàm mật độ xác suất`, từ câu *"hàm mật độ xác suất f(x) ~ likelihood"*.

Cách tái lập: đọc `artifacts/candidates/<doc>/v*/candidates.json` bản mới nhất, gom theo `ident(name) ∪
ident(alias)`, so `candidate_embeddings`; hai biến thể V2/V3 cần gọi `gemini-embedding-001` (768,
`SEMANTIC_SIMILARITY`) trên `name` và `name + ": " + description_draft`.

---

## Nguồn

**Entity resolution với LLM**
- [In-context Clustering-based Entity Resolution with LLMs: A Design Space Exploration (LLM-CER) — SIGMOD 2026 / PACMMOD](https://arxiv.org/abs/2506.02509) · [ACM DL](https://dl.acm.org/doi/10.1145/3749170)
- [Match, Compare, or Select? An Investigation of LLMs for Entity Matching (ComEM) — COLING 2025](https://arxiv.org/abs/2405.16884)
- [Entity Matching using Large Language Models — Peeters, Steiner, Bizer, EDBT 2025](https://arxiv.org/abs/2310.11244)
- [Cost-Effective In-Context Learning for Entity Resolution: A Design Space Exploration (BatchER) — arXiv 2312.03987](https://arxiv.org/abs/2312.03987)
- [Entity Matching with LLMs at Scale: Accuracy, Cost, and Reasoning Effects — PAKDD, Springer](https://link.springer.com/chapter/10.1007/978-981-92-2014-4_10) *(theo abstract)*
- [Adaptive Graph Refinement and Label Propagation with LLMs for Cost-Effective ER (Alper) — arXiv 2605.25814](https://arxiv.org/abs/2605.25814) *(theo abstract)*
- [CaRL-EM: Cost-Aware Reinforcement Learning for Entity Matching with LLMs — arXiv 2609.01195](https://arxiv.org/abs/2609.01195) *(theo abstract)*
- [Labeling Training Data for Entity Matching Using LLMs — Steiner & Bizer, arXiv 2606.28823](https://arxiv.org/abs/2606.28823) *(theo abstract)*

**Blocking, gom cụm, đánh giá ER**
- [A Survey of Blocking and Filtering Techniques for Entity Resolution — Papadakis et al., ACM CSUR 2020](https://arxiv.org/abs/1905.06167)
- [Sparkly: A Simple yet Surprisingly Strong TF/IDF Blocker for Entity Matching — PVLDB 16(6) 2023](https://pages.cs.wisc.edu/~anhai/papers1/sparkly-vldb2023.pdf)
- [Deep Learning for Blocking in Entity Matching: A Design Space Exploration (DeepBlocker) — PVLDB 14(11) 2021](https://doi.org/10.14778/3476249.3476294) — dẫn qua phần so sánh của Sparkly
- [Pre-trained Embeddings for Entity Resolution: An Experimental Analysis — Zeakis et al., PVLDB 16(9) 2023](https://arxiv.org/abs/2304.12329)
- [Framework for Evaluating Clustering Algorithms in Duplicate Detection — Hassanzadeh et al., PVLDB 2(1) 2009](http://www.vldb.org/pvldb/vol2/vldb09-1025.pdf)
- [From Louvain to Leiden: guaranteeing well-connected communities — Traag et al., Scientific Reports 2019](https://arxiv.org/abs/1810.08473)
- [Evaluating Entity Resolution Results (GMD) — Menestrina, Whang, Garcia-Molina, PVLDB 3 2010](https://vldb.org/pvldb/vol3/R18.pdf)
- [A comparison of extrinsic clustering evaluation metrics based on formal constraints — Amigó et al., Information Retrieval 2009](https://link.springer.com/article/10.1007/s10791-008-9066-8) *(theo abstract)*
- [Incremental Record Linkage — Gruenheid, Dong, Srivastava, PVLDB 7 2014](http://www.vldb.org/pvldb/vol7/p697-gruenheid.pdf)
- [Splink — Clustering API](https://moj-analytical-services.github.io/splink/api_docs/clustering.html) · [thảo luận về cluster_id tất định (#873)](https://github.com/moj-analytical-services/splink/discussions/873)

**Chuẩn hoá KG và hệ thống thật — mã nguồn đọc tại commit ghi dưới**
- [Extract, Define, Canonicalize (EDC) — EMNLP 2024](https://arxiv.org/abs/2404.03868)
- [CESI: Canonicalizing Open Knowledge Bases using Embeddings and Side Information — WWW 2018](https://arxiv.org/abs/1902.00172)
- Microsoft GraphRAG 3.1.2 @ `f40e9a2`: [gộp theo (title, type)](https://github.com/microsoft/graphrag/blob/f40e9a26ce62ba0b3fef8837d24aafdcc6e6c704/packages/graphrag/graphrag/index/operations/extract_graph/extract_graph.py#L104-L115) · [prompt tổng hợp mô tả](https://github.com/microsoft/graphrag/blob/f40e9a26ce62ba0b3fef8837d24aafdcc6e6c704/packages/graphrag/graphrag/prompts/index/summarize_descriptions.py) · [vòng tổng hợp cuộn, sắp chữ cái](https://github.com/microsoft/graphrag/blob/f40e9a26ce62ba0b3fef8837d24aafdcc6e6c704/packages/graphrag/graphrag/index/operations/summarize_descriptions/description_summary_extractor.py#L56-L134) · [mặc định 500 từ / 4.000 token](https://github.com/microsoft/graphrag/blob/f40e9a26ce62ba0b3fef8837d24aafdcc6e6c704/packages/graphrag/graphrag/config/defaults.py#L315-L323) · [tài liệu dataflow](https://github.com/microsoft/graphrag/blob/f40e9a26ce62ba0b3fef8837d24aafdcc6e6c704/docs/index/default_dataflow.md)
- LightRAG 1.5.8 @ `d964d92`: [map-reduce mô tả](https://github.com/HKUDS/LightRAG/blob/d964d92b1018c27983d1dcf6ca19ebbaebeb262e/lightrag/operate.py#L373-L470) · [gộp node, kiểu theo đa số](https://github.com/HKUDS/LightRAG/blob/d964d92b1018c27983d1dcf6ca19ebbaebeb262e/lightrag/operate.py#L2430-L2600) · [prompt tổng hợp](https://github.com/HKUDS/LightRAG/blob/d964d92b1018c27983d1dcf6ca19ebbaebeb262e/lightrag/prompt.py#L297-L333) · [ngưỡng mặc định](https://github.com/HKUDS/LightRAG/blob/d964d92b1018c27983d1dcf6ca19ebbaebeb262e/lightrag/constants.py#L30-L36)
- [Zep: A Temporal Knowledge Graph Architecture for Agent Memory — arXiv 2501.13956](https://arxiv.org/abs/2501.13956) · Graphiti @ `4bd7287`: [khớp tên khít, MinHash, cổng entropy](https://github.com/getzep/graphiti/blob/4bd728790e836950c3922e84f6f989f1380f54f2/graphiti_core/utils/maintenance/dedup_helpers.py#L31-L279) · [15 ứng viên, cosine tên ≥ 0,6](https://github.com/getzep/graphiti/blob/4bd728790e836950c3922e84f6f989f1380f54f2/graphiti_core/utils/maintenance/node_operations.py#L64-L65) · [prompt khử trùng](https://github.com/getzep/graphiti/blob/4bd728790e836950c3922e84f6f989f1380f54f2/graphiti_core/prompts/dedupe_nodes.py)
- [KGGen: Extracting Knowledge Graphs from Plain Text with Language Models — NeurIPS 2025](https://arxiv.org/abs/2502.09956) · mã @ `6259b4c`: [neo + top-16, LLM khử trùng](https://github.com/stair-lab/kg-gen/blob/6259b4c71523ceae75dafb4acec2eb833bef8f8e/src/kg_gen/utils/llm_deduplicate.py#L57-L258) · [SemHash 0,95 trên tên](https://github.com/stair-lab/kg-gen/blob/6259b4c71523ceae75dafb4acec2eb833bef8f8e/src/kg_gen/utils/deduplicate.py)
- Neo4j LLM Graph Builder @ `5ff7af3`: [liệt kê node nghi trùng, gộp khi người chọn](https://github.com/neo4j-labs/llm-graph-builder/blob/5ff7af3e9bb9226e1bbecd02f70f8d98697727a7/backend/src/graphDB_dataAccess.py#L470-L532)
- [HippoRAG — NeurIPS 2024](https://arxiv.org/abs/2405.14831) · [HippoRAG 2 (From RAG to Memory) — ICML 2025](https://arxiv.org/abs/2502.14802)
- [Less is More: Denoising Knowledge Graphs for RAG (DEG-RAG) — arXiv 2510.14271](https://arxiv.org/abs/2510.14271)
- [iText2KG: Incremental Knowledge Graphs Construction Using LLMs — arXiv 2409.03284](https://arxiv.org/abs/2409.03284)
- [Graphusion: LLMs for Scientific KG Fusion and Construction in NLP Education — arXiv 2407.10794](https://arxiv.org/abs/2407.10794) · [bản WWW 2025 Companion](https://dl.acm.org/doi/10.1145/3701716.3717821)
- [Evidence-Grounded Multimodal KG Construction for Multi-Lecture Educational Reasoning — arXiv 2608.03161](https://arxiv.org/abs/2608.03161)
- [LLM-empowered knowledge graph construction: A survey — arXiv 2510.20345](https://arxiv.org/abs/2510.20345)
- [Wikidata — Help:Merge](https://www.wikidata.org/wiki/Help:Merge)

**Ontology matching**
- [Machine Learning-Friendly Biomedical Datasets for Equivalence and Subsumption Ontology Matching (Bio-ML) — ISWC 2022](https://arxiv.org/abs/2205.03447)
- [Ontology Matching with LLMs and Prioritized Depth-First Search (MILA) — Information Fusion 2025](https://arxiv.org/abs/2501.11441)
- [LLMs4OM: Matching Ontologies with Large Language Models — ESWC 2024](https://arxiv.org/abs/2404.10317)
- [GenOM: Ontology Matching with Description Generation and LLM — World Wide Web 2026](https://arxiv.org/abs/2508.10703) *(theo abstract)*

**Embedding và ngưỡng**
- [Gemini API — Embeddings (cập nhật 2026-09-04)](https://ai.google.dev/gemini-api/docs/embeddings)
- [Gemini Embedding: Generalizable Embeddings from Gemini — arXiv 2503.07891](https://arxiv.org/abs/2503.07891)
- [intfloat/multilingual-e5-large — model card, FAQ 3](https://huggingface.co/intfloat/multilingual-e5-large)
- [ALIGN-SIM: A Task-Free Test Bed for Evaluating Sentence Embeddings — Findings EMNLP 2024](https://aclanthology.org/2024.findings-emnlp.436/)
- [LAReQA: Language-agnostic answer retrieval from a multilingual pool — arXiv 2004.05484](https://arxiv.org/abs/2004.05484)
- [How Contextual are Contextualized Word Representations? — Ethayarajh, EMNLP 2019](https://aclanthology.org/D19-1006/)
- [Is Cosine-Similarity of Embeddings Really About Similarity? — WWW 2024 Companion](https://arxiv.org/abs/2403.05440)

**Giáo dục, tiên quyết, định nghĩa**
- [Prerequisite Relation Learning for Concepts in MOOCs — Pan et al., ACL 2017](https://aclanthology.org/P17-1133/)
- [Measuring Prerequisite Relations Among Concepts (RefD) — Liang et al., EMNLP 2015](https://aclanthology.org/D15-1193/)
- [Study Navigator: An Algorithmically Generated Aid for Learning from Electronic Textbooks — JEDM 6(1) 2014](https://jedm.educationaldatamining.org/index.php/JEDM/article/view/41)
- [DEFT: A corpus for definition extraction in free- and semi-structured text — LAW 2019](https://aclanthology.org/W19-4015/)
- [ISO 704:2009 Terminology work — Principles and methods](https://www.iso.org/standard/38109.html) (bản hiện hành: ISO 704:2022)
- [Definition Modelling for Appropriate Specificity — Huang et al., EMNLP 2021](https://aclanthology.org/2021.emnlp-main.194/) *(theo abstract)*

**Tóm tắt đa nguồn, dẫn chứng, trung thực**
- [On Faithfulness and Factuality in Abstractive Summarization — Maynez et al., ACL 2020](https://aclanthology.org/2020.acl-main.173/)
- [From Single to Multi: How LLMs Hallucinate in Multi-Document Summarization — NAACL 2025 Findings](https://arxiv.org/abs/2410.13961)
- [Attributable by Construction: Claim-Anchored Provenance for Multi-Document Summarization (CAMS) — arXiv 2606.23989](https://arxiv.org/abs/2606.23989)
- [Are Finer Citations Always Better? Rethinking Granularity for Attributed Generation — arXiv 2604.01432](https://arxiv.org/abs/2604.01432)
- [Enabling Large Language Models to Generate Text with Citations (ALCE) — EMNLP 2023](https://arxiv.org/abs/2305.14627)
- [Lost in the Middle: How Language Models Use Long Contexts — TACL 2024](https://arxiv.org/abs/2307.03172)
- [Adaptive Chameleon or Stubborn Sloth: LLMs in Knowledge Conflicts — ICLR 2024](https://arxiv.org/abs/2305.13300)
- [Knowledge Conflicts for LLMs: A Survey — arXiv 2403.08319](https://arxiv.org/abs/2403.08319)
- [MiniCheck: Efficient Fact-Checking of LLMs on Grounding Documents — EMNLP 2024](https://arxiv.org/abs/2404.10774)
- [ViNLI: A Vietnamese Corpus for Open-Domain Natural Language Inference — COLING 2022](https://aclanthology.org/2022.coling-1.339/) *(theo abstract)*
- [ViFactCheck: Multi-Domain News Fact-Checking in Vietnamese — AAAI 2025](https://arxiv.org/abs/2412.15308) *(theo abstract)*
