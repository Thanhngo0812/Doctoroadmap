# Nghiên cứu A6–A8 — Cụm chủ đề và suy luận tiên quyết (2b): kiểm tính mới của phân nhánh và mention map

Vòng 29 · 2026-09-15 · Đối tượng: doc/spec-preview.md §6–§8 (C, M, T2b) và doc/spec-addendum.md A6–A9, Tầng 2b

Chưa viết dòng mã nào cho A6–A8. Đây là khảo sát trước khi spec, nối tiếp
`report/nghien-cuu-a4-a5-hop-nhat-thuc-the.md` — phần GraphRAG, LightRAG, Graphiti, KGGen, Neo4j LLM Graph Builder
đã khảo ở đó, không làm lại. Việc chính: **kiểm** — không phải xác nhận — niềm tin rằng hai thứ trong
`spec-preview.md` là tính mới khoa học: **phân nhánh/định tuyến** của 2b (preview §202–§239) và **mention map**
(preview §163–§192).

Ký hiệu: `preview §N` = dòng N của `doc/spec-preview.md`; `addendum §N` = dòng N của `doc/spec-addendum.md` (bản
hiện tại). Ba loại câu được tách: sự thật từ nguồn luôn đi kèm tên công trình (đường dẫn ở mục *Nguồn*); **số đo dự
án** ghi rõ lấy từ artifact hay báo cáo nào; câu mở đầu bằng *Suy luận:* là ý kiến của người viết. Con số lấy từ toàn
văn hoặc mã nguồn, trừ chỗ ghi *(theo abstract)*. Phần đo offline trên corpus đã bỏ theo chỉ đạo đổi ưu tiên: báo
cáo này không có số đo mới, không gọi API mô hình hay embedding nào.

Nguồn: văn liệu học tiên quyết khái niệm (CPRP) 2012–2025 (BEA, EMNLP, CIKM, ACL, AAAI, NAACL, COLING, EDM, JEDM,
EVALITA, Technology Knowledge and Learning), công trình dùng LLM cho tiên quyết 2024–2026, entity resolution và
blocking (SIGMOD 1995 và 2013, KDD 2000, TKDE 2014), entity linking (CIKM 2007–2010, ACL/EMNLP 2020), gom cụm đồ thị
(PNAS 2007, PRE 2010–2011, Scientific Reports 2012/2019, Statistics and Computing 2007, NIPS 2008, TCS 2009), và
**mã nguồn** GraphRAG 3.1.2, graspologic-native 1.2.5/1.3.1, leidenalg 0.12.0, QuickUMLS, NetworkX 3.6.1.

---

## Tóm tắt

- **Không thành phần nào là cơ chế mới.** "Hai nhánh là ảnh gương" chính là multi-pass blocking của Hernández &
  Stolfo (SIGMOD 1995): nhiều lượt độc lập, mỗi lượt một khoá, hợp kết quả. Mention map ghép entity linking lai từ
  vựng + ngữ nghĩa (BioSyn, BLINK — 2020), phân biệt provenance/mention đã có trong văn liệu giáo trình (Wang et al.
  2016; Study Navigator 2014), sổ cặp chạm là meta-blocking (TKDE 2014), tỉa theo reachability là crowdsourced join
  (SIGMOD 2013) và ACE (JEDM 2024). Chưa thấy ai **ghép** chúng cho suy tiên quyết bằng LLM trên giáo trình — đó là
  "kết hợp mới", chưa phải "cơ chế mới".
- **Phần bảo vệ được là một phép đo chưa ai làm**: cạnh tiên quyết của một giáo trình nằm ở đâu — cùng chunk, cùng
  chương, cùng cụm, nối qua một lần nhắc tên, hay ngầm. Với quan hệ thường, DocRED có con số 40,7% cạnh xuyên câu;
  với tiên quyết, không tìm được con số tương đương. Đo được bằng code thuần, không một lời gọi LLM — khi có nhãn vàng.
- **Nhãn vàng phải bám văn bản.** Các bộ CPRP phổ biến được gán bằng kiến thức nền; GPT-4 không đọc văn bản nào đã
  thắng baseline có giám sát trên chúng (F1 0,777). PREAP (2023) gán trong lúc đọc giáo trình: κ 0,45–0,71, so với
  0,16–0,60 khi gán mọi cặp theo kiến thức nền. Bộ vàng kiểu PREAP trên giáo trình tiếng Việt là phần có thể mới thật.
- **Tiền không phải lý do chính cho mention map.** Hỏi mọi cặp của 250 node học được bằng flash-lite ước ≈ 4–9 USD
  một lượt. Lý do đứng được là bám bằng chứng và độ chính xác: gán theo cặp sinh thừa quan hệ (PREAP), LLM trích mở
  nghiêng về `Prerequisite_of` (Graphusion) — nhưng phải đo, không suy.
- **A7 theo mã nguồn:** GraphRAG 3.1.2 gom bằng Leiden phân cấp với `max_cluster_size = 10`, nhưng trần **không
  cứng** — cụm không chẻ được thì giữ nguyên; mặc định **bỏ mọi nút ngoài thành phần liên thông lớn nhất**; và ghim
  graspologic-native < 1.3 vì bản mới đổi kết quả cụm. leidenalg có `max_comm_size` + `node_sizes`: trần cứng tính
  theo khái niệm, media cỡ 0.
- **A6:** bỏ ngưỡng cosine 0,75 (addendum §444). kNN là lựa chọn đầu tiên (von Luxburg 2007); loại đồ thị quyết định
  kết quả gom cụm (Maier et al. 2008); đường dựng đồ thị không-LLM của GraphRAG dùng đồng xuất hiện chuẩn hoá PMI và
  cắt theo phân vị — không có ngưỡng tuyệt đối nào.
- **Kênh dense của mention map đang so hai không gian khác nhau:** vector chunk trong kho truy hồi embed
  `RETRIEVAL_DOCUMENT`, vector mô tả embed `SEMANTIC_SIMILARITY`. Z-score theo hàng chỉ chuẩn hoá một phía; chunk
  "hub" (tổng quan, tóm tắt) cần chuẩn hoá hai phía kiểu CSLS. Kênh exact không nên bỏ dấu tiếng Việt.
- **Mention map nên có hướng và phục vụ cả nhánh chương.** "A được dạy ở chunk có nhắc B" là tín hiệu B → A — chính
  là RefD/LOrd. Và cạnh xuyên chương của nhánh 1 cần đúng "concept references" của Study Navigator — hai nhánh không
  đối xứng như spec vẽ.
- **Nhất quán toàn cục:** 4% cạnh của TutorialBank là hai chiều — chu trình không luôn là lỗi; confidence LLM tự khai
  thiên về quá tự tin nên "cắt cạnh confidence thấp nhất" dễ cắt nhầm; transitive reduction và tỉa reachability trên
  cạnh nhiễu làm lỗi lan — học thứ tự bộ phận với oracle nhiễu vẫn là câu hỏi mở (Liang et al. 2019).
- **Doc-order prior có thật nhưng yếu** (bỏ đặc trưng vị trí chỉ mất 2,4 F1 ở Pan et al. 2017) và bị chính giáo
  trình vi phạm (comprehension burden, KDD 2012). Dùng thứ tự provenance; hiệu chỉnh mức trừ trên vàng thay vì 0,1 cố
  định.

---

## 1. Phát hiện quan trọng nhất: hai "tính mới" đều đã có tên — thứ chưa ai làm là **phép đo**, và phép đo đó cần một bộ vàng khác hẳn bộ vàng CPRP hiện có

Mỗi mảnh của hai đóng góp đều có tiền lệ gần:

| Mảnh trong spec-preview | Tiền lệ gần nhất | Giống | Khác |
|---|---|---|---|
| "Hai nhánh là ảnh gương" — pass phụ đi theo trục còn lại để bù điểm mù (preview §210; addendum §731) | Multi-pass sorted neighborhood (Hernández & Stolfo, SIGMOD 1995): *"cải thiện độ chính xác bằng cách tiếp cận nhiều lượt … lấy bao đóng bắc cầu trên kết quả của các lượt độc lập, mỗi lượt dùng một thuộc tính khoá khác"* *(theo abstract)*. Canopy (McCallum, Nigam & Ungar, KDD 2000): phân vùng **chồng lấn** nên *"chịu được sai số của phép đo rẻ"*, khác blocking cứng | Hai khoá phân vùng khác nhau; hợp kết quả để lượt này vớt cái lượt kia bỏ sót | Khoá là cấu trúc tài liệu và cụm chủ đề; bộ so khớp là LLM; quan hệ **có hướng** thay vì đồng nhất |
| Định tuyến: chọn khoá chính theo cấu trúc tài liệu (preview §204–§208) | Không tìm được tiền lệ trong CPRP | — | Có thể mới, nhưng là quyết định vận hành; chỉ thành đóng góp nếu đo được nó rẻ hơn mà không kém việc chạy cả hai khoá |
| Kênh exact + kênh dense (preview §167–§174) | Từ điển kiểu MetaMap/QuickUMLS; BLINK (EMNLP 2020, bi-encoder dense); BioSyn (ACL 2020): điểm = dense + λ·sparse trên n-gram ký tự | Hai kênh, từ vựng + ngữ nghĩa | Không có |
| Provenance ≠ mention (preview §165) | Wang et al. (CIKM 2016): key concept là khái niệm *"không chỉ được nhắc mà được bàn và học"* trong mục. Study Navigator (JEDM 2014): cặp *(khái niệm dùng ở mục s, mục t nơi nó được giảng)* | Đúng phân biệt đó | Tên gọi |
| Sổ cặp chạm cộng dồn theo chunk (preview §178–§186) | Meta-blocking (Papadakis et al., TKDE 2014): đồ thị blocking, trọng số theo số khối chung (CBS) hoặc nghịch đảo cỡ khối (ARCS), cắt bằng ngưỡng hoặc top-k. Distant supervision (Mintz et al., ACL-IJCNLP 2009): *"câu chứa một cặp thực thể có quan hệ đã biết có khả năng diễn đạt quan hệ đó"* | Chunk = khối; cặp cùng khối = ứng viên có trọng số | Cộng dồn lên **cặp cụm** để quyết định mở phiên — không tìm được tiền lệ |
| Tỉa theo reachability (preview §228–§231, §319) | Wang et al. (SIGMOD 2013): suy nhãn bằng bắc cầu để khỏi hỏi đám đông, có thứ tự hỏi tối ưu. ACE (JEDM 2024): cặp suy được từ đồ thị hiện tại bị gỡ khỏi danh sách hỏi chuyên gia | Không hỏi oracle cặp đã suy được | Oracle là LLM có nhiễu — tình huống Liang et al. (EDM 2019) để ngỏ |

*Cơ chế* không mới. *Tổ hợp* cho suy tiên quyết bằng LLM trên giáo trình thì chưa thấy ai làm. Nhưng tổ hợp chỉ
thành đóng góp khi có số cho thấy nó hơn các lựa chọn đơn giản hơn — và ở đây văn liệu để trống đúng một câu hỏi:

> **Cạnh tiên quyết của một giáo trình nằm ở đâu so với cấu trúc của nó?** Bao nhiêu phần trăm nằm trong cùng chunk,
> cùng mục, cùng chương, cùng cụm chủ đề; bao nhiêu phần trăm nối qua một chunk nhắc cả hai; bao nhiêu phần trăm là
> ngầm — không chunk nào nhắc cả hai?

DocRED (ACL 2019) trả lời câu hỏi cùng hình dạng cho quan hệ thường: *"ít nhất 40,7% sự kiện quan hệ chỉ trích được
từ nhiều câu"* — con số đó biện minh cho cả một hướng nghiên cứu. Với tiên quyết, không tìm được con số tương đương.
Mà nó quyết định mọi thứ phía sau. *Suy luận:* nếu gần hết cạnh nằm trong chương, pass phụ của nhánh 1 gần như vô
ích; nếu phần lớn cạnh xuyên cụm có chunk nhắc cả hai, mention map là đủ; nếu nhiều cạnh ngầm, không pass nào bắt
được và chỉ còn bắc cầu.

Câu hỏi này trả lời được **bằng code thuần**, không cần lời gọi LLM nào — *khi có nhãn vàng*. Và đây là vế thứ hai
của phát hiện: **bộ vàng CPRP hiện có không đo được thứ dự án cần.**

- Pan et al. (ACL 2017) cho người gán dùng *"kiến thức nền của mình và sách tham khảo"*; LectureBank (AAAI 2019) cho
  tra *"chương trình đại học chuẩn"* khi không chắc.
- PREAP (Alzetta, Torre & Koceva, Technology, Knowledge and Learning 2023) tổng kết: người gán các bộ dữ liệu
  *"thường dựa vào kiến thức miền có sẵn … không dựa vào một văn bản cụ thể"*.
- Rubric 2b đòi bằng chứng **trong tài liệu** (addendum §806). Chấm 2b bằng bộ vàng kiến thức nền là thưởng cho đúng
  thứ 2b cố chặn. Yang et al. (arXiv 2402.14293) cho GPT-4 zero-shot, **không kèm văn bản**, đạt F1 0,777 trên
  LectureBankCD — hơn baseline có giám sát tốt nhất (Node2vec, 0,747); còn thêm tài liệu bài giảng vào prompt thì kết
  quả **giảm**.

PREAP cho luôn lời giải: gán tiên quyết *trong lúc đọc* văn bản ("textbook-driven in-context annotation") đạt κ
0,45–0,71, so với 0,16–0,60 khi gán mọi cặp theo kiến thức nền và 0,01–0,27 khi gán mọi cặp có kèm văn bản; thời
gian gán giảm 43% và 29%. Bộ vàng kiểu PREAP trên giáo trình tiếng Việt dài, cộng phép "điều tra vị trí" cạnh ở
trên, là phần **có thể mới thật** — và nó đứng được kể cả khi cuối cùng dự án không chọn luồng của spec-preview.

---

## 2. Cụm chủ đề (A6 + A7)

### 2.1 Leiden, không Louvain; CPM hay modularity là chọn *ý nghĩa* của tham số

- Traag, Waltman & van Eck (Scientific Reports 9:5233, 2019): Louvain có thể cho cộng đồng *"liên thông kém tuỳ ý"*,
  thậm chí không liên thông, nặng hơn khi chạy lặp; trong thí nghiệm của họ tới 25% cộng đồng liên thông kém và tới
  16% không liên thông. Leiden bảo đảm mọi cộng đồng liên thông (γ-connected) và, khi lặp, hội tụ tới phân hoạch mà
  mọi tập con của mọi cộng đồng được gán tối ưu cục bộ.
- Giới hạn phân giải: tối ưu modularity có thể không thấy mô-đun nhỏ hơn một thang phụ thuộc tổng số cạnh L; nguy cơ
  cao nhất khi số cạnh trong mô-đun cỡ √(2L) trở xuống (Fortunato & Barthélemy, PNAS 2007).
- CPM (Constant Potts Model) không mắc giới hạn phân giải (Traag, Van Dooren & Nesterov, PRE 2011). Tham số dễ đọc:
  cộng đồng phải có mật độ trong ≥ γ, mật độ giữa các cộng đồng < γ (Traag et al. 2019, phương trình 2).
- Modularity suy biến: thường có số mũ lời giải điểm cao khác nhau về cơ bản, không có cực đại toàn cục rõ (Good, de
  Montjoye & Clauset, PRE 2010). Phụ thuộc seed là hệ quả trực tiếp. **Số đo dự án** (spec A4/A5, D3): cùng đồ thị
  đề cử, số cạnh bị cắt dao động 36–42 giữa bảy seed.
- Lancichinetti & Fortunato (Scientific Reports 2012): đa số phương pháp không tất định — kết quả phụ thuộc seed,
  điều kiện đầu và luật phá hoà; đồng thuận nhiều lượt (consensus clustering) tăng cả độ ổn định lẫn độ đúng.

*Suy luận:* A7 cần hai quyết định mà spec chưa ghi. (1) Leiden, không Louvain — addendum §457 đang viết *"Leiden
(hoặc Louvain)"*. (2) Hàm mục tiêu. Khi đệ quy trên đồ thị con, modularity dùng mô hình rỗng của **đồ thị con**, tức
chạy lại ở độ phân giải hiệu dụng khác; CPM thì γ giữ nguyên nghĩa ở mọi cấp, nên viết được thành luật trong spec.

### 2.2 Mã nguồn GraphRAG: trần cỡ cụm **không cứng**, nút ngoài thành phần lớn nhất **mất cụm**

GraphRAG 3.1.2 (commit `f40e9a2`) — đọc mã, không đọc tài liệu giới thiệu:

| Chỗ | Hành vi | Mã |
|---|---|---|
| Mặc định | `max_cluster_size = 10`, `use_lcc = True`, `seed = 0xDEADBEEF` | `config/defaults.py` L67–73 |
| Gọi Leiden | `graspologic_native.hierarchical_leiden(..., resolution=1.0, randomness=0.001, use_modularity=True, iterations=1)` | `graphs/hierarchical_leiden.py` L11–26 |
| Trước khi gom | chuẩn hoá chiều cạnh, bỏ cạnh trùng, **lọc về thành phần liên thông lớn nhất**, **sắp xếp danh sách cạnh** rồi mới gọi Leiden | `index/operations/cluster_graph.py` L58–88; `graphs/stable_lcc.py` L22–70 |
| Phân cấp | mỗi cụm có `level` và `parent_cluster`; giữ **mọi cấp** | `cluster_graph.py` L34–47, L89–99 |
| Ghim phiên bản | `graspologic-native>=1.2,<1.3`, chú thích: *"1.3.x thay đổi đầu ra Leiden (số cộng đồng/cấp), làm hỏng test hồi quy đã ghim và dữ liệu cộng đồng vàng"* | `packages/graphrag/pyproject.toml` L46–49 |

Phần đệ quy nằm trong Rust của graspologic-native. Đã đọc cả 1.2.5 (`3c98966`, bản GraphRAG dùng) lẫn 1.3.1
(`7731814`); logic đệ quy giống hệt, chỉ khác tham số `max_local_moving_iterations`:

- Chạy Leiden một lần; cụm vượt `max_cluster_size` được tách thành mạng con cô lập và chạy Leiden lại; lặp theo cấp
  tới khi hết việc (`hierarchical.rs` L133–216).
- **Nếu Leiden trên mạng con chỉ trả một cụm, cụm đó được giữ nguyên** — chú thích trong mã: *"we couldn't break
  this cluster down any further"* — và không bao giờ bị xét lại (L179–181, L207–208).
- Mặc định của thư viện là `max_cluster_size = 1000` (pyo3 `lib.rs` L157, L177). Con số 10 là của GraphRAG.

Ba hệ quả cho luật addendum §460 (*"cluster > 12 concept thì chạy lại Leiden bên trong; cluster 1–2 concept thì
sáp nhập vào cluster gần nhất"*):

1. **Trần không cứng.** Một cụm dày đặc — cả họ khái niệm kiểm định giả thuyết chẳng hạn — có thể không chẻ được bằng
   modularity ở độ phân giải đang dùng. Spec phải nói làm gì lúc đó. *Suy luận:* preview §158 gọi trần là *"điều
   kiện để 'mỗi cụm 1 phiên' khả thi"* — vậy nó phải là bất biến có kiểm, không phải hy vọng.
2. **LCC là mặc định nguy hiểm.** GraphRAG bỏ mọi nút ngoài thành phần lớn nhất trước khi gom. A7 thì mọi node phải
   có `cluster_id` (addendum §460), kể cả khái niệm lẻ và media mồ côi.
3. **Phiên bản thư viện là một phần của kết quả.** Chính GraphRAG phải ghim phiên bản vì cộng đồng đổi. Cùng tinh
   thần ADR 0004: tên thư viện Leiden, phiên bản, hàm mục tiêu, độ phân giải, seed và **thứ tự cạnh** (GraphRAG sắp
   xếp cạnh trước khi gọi, `cluster_graph.py` L77–84) phải vào manifest A7.

### 2.3 leidenalg có sẵn đúng thứ spec cần: trần cứng tính theo **khái niệm**

leidenalg 0.12.0 (commit `368a99e`, do tác giả thuật toán Leiden duy trì):

- `find_partition(graph, partition_type, ..., n_iterations=2, max_comm_size=0, seed=None)`. `max_comm_size` là
  *"tổng cỡ tối đa của các nút trong một cộng đồng"*, 0 là không giới hạn (`functions.py` L21, L52–54, L86) — ràng
  buộc **trong lúc tối ưu**, không phải lượt chẻ hậu kỳ. `n_iterations` âm = chạy tới khi một lượt không cải thiện.
- `CPMVertexPartition(..., node_sizes=..., resolution_parameter=1.0)`: cỡ cộng đồng = tổng `node_sizes`, mặc định
  mọi nút cỡ 1 (`VertexPartition.py` L849–910). `ModularityVertexPartition` không nhận `node_sizes`.

*Suy luận:* đặt `node_sizes` = 1 cho node học được, 0 cho media, rồi `max_comm_size = 12` — luật *"đếm theo số
concept, không đếm media"* của addendum §461–462 thành một tham số, không cần lượt đệ quy. Luật *"cụm 1–2 concept
sáp nhập vào cluster gần nhất"* thì vẫn cần định nghĩa "gần nhất" (tổng trọng số cạnh sang cụm kia, phá hoà bằng tâm
embedding, rồi thứ tự tài liệu) — spec hiện chưa có.

Còn `networkx.community.leiden_communities` (NetworkX 3.6.1) *"không có cài đặt NetworkX mặc định"*, phải có
backend như cugraph — khớp ghi chú ở spec A4/A5, D3.

### 2.4 Dựng cạnh (A6): láng giềng gần nhất và đồng xuất hiện có chuẩn hoá — không ngưỡng tuyệt đối

Addendum §444 vẫn ghi *"cosine của embedding description ≥ ngưỡng (vd 0.75)"*. **Số đo dự án** (báo cáo A4/A5 mục
2.3): với `gemini-embedding-001` 768 chiều, cosine giữa hai thực thể bất kỳ đã khoảng 0,80; 92,5% cặp vượt 0,75; mỗi
tài liệu thành một thành phần liên thông. Văn liệu dựng đồ thị nói cùng chiều:

- von Luxburg (Statistics and Computing 2007, mục 8.1): đồ thị ε *"khó chọn ε"* khi dữ liệu có nhiều thang; kNN nối
  được điểm ở các thang khác nhau; mutual kNN nối trong vùng cùng mật độ, không nối vùng khác mật độ, và ít cạnh hơn
  nhiều nên cần k lớn hơn. *"Khuyến nghị chung: dùng đồ thị kNN làm lựa chọn đầu tiên"* — ít nhạy với tham số hơn.
- Maier, von Luxburg & Hein (NIPS 2008): *"Ncut trên đồ thị kNN làm một việc khác hẳn một cách có hệ thống so với
  Ncut trên đồ thị r-neighborhood"* — tiêu chí gom cụm không thể xét tách khỏi loại đồ thị. Maier, Hein & von Luxburg
  (TCS 2009): muốn nhận ra cụm trong dữ liệu nhiễu, k phải lớn *"đáng ngạc nhiên — cỡ n hơn là cỡ log n"* *(theo
  abstract)*.
- Radovanović et al. (JMLR 2010): ở chiều cao, số lần một điểm lọt vào kNN của điểm khác phân bố lệch mạnh, sinh
  "hub". *Suy luận:* kNN một chiều trên vector 768 chiều sẽ có hub — khái niệm tổng quát kiểu "mô hình", "dữ liệu";
  mutual kNN hoặc chuẩn hoá hai phía (mục 4.2) giảm tác động đó.
- Đường dựng đồ thị **không cần LLM** của GraphRAG rất gần A6: nối hai cụm danh từ cùng xuất hiện trong một text
  unit, trọng số = số text unit chung, chuẩn hoá bằng biến thể PMI `p(x,y)·log2(p(x,y)/(p(x)p(y)))`
  (`build_noun_graph.py` L99–143; `edge_weights.py` L10–62); rồi cắt cạnh theo **phân vị** (mặc định bỏ 40% cạnh nhẹ
  nhất), bỏ nút tần suất < 2 và **bỏ nút bậc cao nhất** (`remove_ego_nodes = True`) trước khi gom (`prune_graph.py`
  L44–95; `defaults.py` L281–291). Mọi ngưỡng ở đây đều tương đối.
- CPRL (Jia et al., NAACL 2021) dựng cạnh khái niệm–khái niệm bằng PMI trên cửa sổ trượt và cạnh khái niệm–chương bằng
  tf-idf.

Đề xuất cho A6 (mục 5): hợp ba kênh, mỗi kênh tự chuẩn hoá — (i) đồng xuất hiện của **provenance** theo chunk và theo
mục, trọng số PMI/NPMI; (ii) mutual-kNN trên vector mô tả A5, k nhỏ, không sàn cosine; (iii) media đồng vị trí như
addendum §445–453. Luật hạ trọng số media bậc cao `1/(bậc−1)` (addendum §451) cùng họ với ARCS của meta-blocking
(mục 4.2) — nên áp luôn cho **chunk** nhắc quá nhiều khái niệm.

### 2.5 Fallback HDBSCAN/BERTopic thêm một bước, không bớt

BERTopic (Grootendorst, arXiv 2203.05794) là embed → gom cụm → biểu diễn chủ đề bằng c-TF-IDF *(theo abstract)*.
Tài liệu BERTopic ghi HDBSCAN sinh tài liệu ngoại lai nhãn −1 và cung cấp `reduce_outliers` với bốn chiến lược gán
lại. RAPTOR (ICLR 2024) gom **mềm** bằng GMM trên embedding đã giảm chiều bằng UMAP — một đoạn thuộc được nhiều cụm —
vì *"đoạn văn thường mang thông tin liên quan tới nhiều chủ đề"*.

*Suy luận:* addendum §459 dùng HDBSCAN khi *"edge thô quá thưa"*. Đồ thị kNN không bao giờ thưa tới mức đó; còn
HDBSCAN buộc thêm bước gán ngoại lai, vì A7 bắt mọi node có `cluster_id`. Nên bỏ fallback, giữ một đường Leiden trên
kNN. Ý của RAPTOR đáng giữ theo cách khác: cho **node biên** thuộc tối đa hai cụm là một thay thế trực tiếp cho sổ
cặp cụm (mục 4.2) — đáng một ablation.

### 2.6 Đánh giá cụm khi không có nhãn; cụm và stage

- Chọn số cụm theo độ ổn định (qua seed, qua lấy mẫu con) là cách phổ biến (von Luxburg, Foundations and Trends in ML
  2010 *(theo abstract)*); không ổn định thì đồng thuận nhiều lượt (Lancichinetti & Fortunato 2012).
- Section làm nhãn yếu có cơ sở: Wang et al. (CIKM 2016) giải thích đặc trưng khoảng cách mục lục mang cả chênh độ khó
  lẫn độ liên quan, vì tác giả *"thường đặt khái niệm liên quan ở các mục kề nhau"*.
- *Suy luận — điểm dễ bỏ qua:* **cụm trùng khít chương thì nhánh cụm vô dụng.** Giá trị của "ảnh gương" tỉ lệ với độ
  **lệch** giữa phân hoạch chương và phân hoạch chủ đề. Nên đo NMI/ARI giữa cụm và chương không để tối đa hoá, mà để
  biết pass phụ đáng tiền tới đâu: NMI ≈ 1 ⇒ pass phụ gần như không thêm cặp; NMI thấp ⇒ nhiều cặp cùng chủ đề nằm xa
  nhau. Con số này có trước mọi lời gọi LLM.
- Stage = layer ∩ cluster (addendum §544): không tìm được tiền lệ trực tiếp. Hai lưu ý. (1) Kahn xếp mọi node không
  có tiên quyết vào lớp 1 — khi `requires` thưa, lớp 1 phình và "stage" chủ yếu còn là cụm. (2) Trần 5–8
  concept/stage là bài toán phân lớp có trần bề rộng, họ bài toán lập lịch kinh điển kiểu Coffman–Graham (Acta
  Informatica 1972) *(chỉ kiểm siêu dữ liệu; áp vào stage là suy luận)*. PREAP ghi nhận nhận xét của chuyên gia sư
  phạm: đồ thị lớn khó dùng trực tiếp, nên chia thành đồ thị con.

---

## 3. Suy luận tiên quyết (A8 / 2b)

### 3.1 Bản đồ văn liệu CPRP — trước LLM

Bài toán đã có khảo sát riêng: Bai et al. (ACM Computing Surveys 2025) tách hai hạt — khái niệm (KC) và đơn vị học
liệu (LO) — và xếp phương pháp theo loại đặc trưng *(theo abstract)*. Bảng dưới lần về từng bài gốc.

| Công trình | Năm · nơi đăng | Dữ liệu | Tín hiệu chính | Kết quả báo cáo | Nhãn: ai gán · đồng thuận |
|---|---|---|---|---|---|
| Talukdar & Cohen | 2012 · BEA | Wikipedia, 5 miền, chỉ cặp **có liên kết** | MaxEnt: RWR, PageRank, lịch sử sửa, nội dung trang | accuracy 58,8 so với ngẫu nhiên 50,2 (trung bình, huấn luyện ngoài miền) | Mechanical Turk; κ trung bình 0,54 (0,47–0,63); tổng chi 278 USD |
| RefD — Liang et al. | 2015 · EMNLP | CrowdComp; Course (CS, MATH) | các khái niệm liên quan của A tham chiếu B nhiều hơn chiều ngược; r(c, A) *"có thể là liên kết Wikipedia, lần nhắc trong sách, trích dẫn"* | Course: F1 74,7/75,1 (CS), 71,9/66,7 (MATH); θ tốt 0,02–0,1 | Course: 2 chuyên gia lọc nhãn |
| Wang et al. | 2016 · CIKM | 6 giáo trình | key concept (được bàn, không chỉ nhắc) và tiên quyết tối ưu đồng thời; khoảng cách mục lục (TOC) | F1 0,55–0,71 | 3 nghiên cứu sinh, bỏ phiếu; "tương quan trung bình 83%" |
| Gordon et al. | 2016 · ACL | chủ đề LDA trên ACL Anthology | đo thông tin (cross-entropy, information flow) | P@20 tới 0,85 | 8 người; tương quan Pearson 0,357 cho câu hỏi phụ thuộc |
| CPR-Recover — Liang et al. | 2017 · AAAI | 654 môn CS, 11 trường | khôi phục tiên quyết khái niệm từ tiên quyết môn học | P@50 0,54 | 13 sinh viên, 3 người/cặp; Fleiss κ 0,42; 1.008/3.544 cặp dương |
| Pan et al. | 2017 · ACL | Coursera: ML, DSA, CAL | biểu diễn khái niệm + 7 đặc trưng: tham chiếu (video/câu/Wikipedia), vị trí trung bình (Apd), bất đối xứng phân bố, chênh độ phức tạp | F1 71,1–72,6 | 3 người/cặp theo *"kiến thức nền và sách tham khảo"*; κ 0,59–0,65 |
| AL-CPL — Liang et al. | 2018 · AAAI (EAAI) | concept map từ giáo trình của Wang et al., 4 miền, mở rộng bằng bắc cầu | học chủ động + đặc trưng đồ thị/văn bản | khảo chiến lược truy vấn | chuyên gia sửa nhãn vi phạm thứ tự bộ phận |
| TutorialBank — Fabbri et al. | 2018 · ACL | 200 chủ đề NLP | bộ dữ liệu | 794 cạnh một chiều + 33 hai chiều | Fleiss κ 0,30 |
| LectureBank — Li et al. | 2019 · AAAI | 208 khái niệm, 921 cạnh | embedding + GAE/VGAE | F1 ≈ 0,68–0,73 (tập kiểm tra cân bằng) | 2 nghiên cứu sinh; Cohen κ 0,70 |
| Liang et al. | 2019 · EDM | như AL-CPL | học chủ động + suy bao đóng cho thứ tự bộ phận | cải thiện ở cùng ngân sách truy vấn *(theo abstract)* | giả định oracle hoàn hảo; oracle nhiễu để ngỏ |
| PREREQ — Roy et al. | 2019 · IAAI | UCD, MOOC | pairwise-link LDA + mạng Siamese | UCD: F1 59,7 (theo bảng của ACE) | — |
| Adorni et al. | 2019 · AIED | giáo trình | burst analysis + đồng xuất hiện, không cần tri thức ngoài | — | *không đọc được toàn văn; mô tả theo PREAP* |
| MOOCCube — Yu et al. | 2020 · ACL | 706 môn, 106.056 khái niệm | chỉ ghép khái niệm **cùng môn**; giám sát xa nhiều vòng | PREREQ-S F1 0,688 | 3.500 cặp gán tay; *"chỉ 6% cặp có tiên quyết"* |
| R-VGAE — Li et al. | 2020 · COLING | LectureBank mở rộng | tự giám sát trên đồ thị tài nguyên–khái niệm | — | Cohen κ 0,63 cho cặp bổ sung |
| PRELEARN — Alzetta et al. | 2020 · EVALITA | ITA-PREREQ (từ AL-CPL, tiếng Ý) | nhiệm vụ chung | accuracy tốt nhất 0,887 (Italian BERT) | tập kiểm tra cân bằng 50/50 |
| Pal, Arora & Goyal | 2020 · arXiv | 3 miền của AL-CPL | vị trí trong giáo trình; tần suất = 1 là "tham chiếu", > 1 là "được bàn"; luật thứ tự cứng | AUPRC tăng rõ khi áp luật thứ tự | — |
| CPRL — Jia et al. | 2021 · NAACL | 4 bộ, gồm 6 giáo trình × 3 miền (tiếng Trung) | R-GCN trên đồ thị khái niệm–chương + LOrd (RefD trên chương) + khoảng cách TOC | F1 0,63–0,86 | âm = cặp ngẫu nhiên + cặp đảo chiều |
| MOOCCubeX — Yu et al. | 2021 · CIKM | 4.216 môn, 637.572 khái niệm | khai phá đồ thị khái niệm có giám sát yếu *(theo abstract)* | — | — |
| PREAP — Alzetta, Torre & Koceva | 2023 · Technology, Knowledge and Learning 29 | đoạn giáo trình, 5 miền | giao thức gán **trong lúc đọc** | — | κ 0,45–0,71 (PREAP) · 0,16–0,60 (mọi cặp, kiến thức nền) · 0,01–0,27 (mọi cặp, có văn bản) |

Ba điều rút ra:

1. **Số F1 công bố không mang sang được.** Gần như mọi bộ đánh giá lấy âm bằng cặp ngẫu nhiên cộng cặp đảo chiều rồi
   cân bằng lớp (Jia et al. 2021; LectureBank); PRELEARN xếp hạng bằng accuracy vì tập kiểm tra cân bằng. Trong một
   giáo trình thật, dương hiếm: LectureBank có 921 cạnh trên 208·207 cặp có hướng ≈ 2,1% (tính từ số của bài); đồ thị
   chuyên gia của ACE có 5–15% cặp vô hướng là cạnh trực tiếp; MOOCCube 6%. Precision trên phân bố thật sẽ thấp hơn
   nhiều. Cách dựng tập đánh giá còn có thể làm ngẫu nhiên trông mạnh: ở Gordon et al., baseline ngẫu nhiên đạt P@20
   0,659 vì tập chấm được lấy từ top của các hệ.
2. **Tín hiệu đối xứng dùng để đề cử; tín hiệu bất đối xứng dùng để quyết.** AL-CPL: đặc trưng đối xứng như độ giống
   và PMI *"không quan trọng"* trong phân loại cùng miền; đứng đầu là chênh PageRank, RefD, *số lần A được nhắc trong
   B*. Pan et al.: độ liên quan ngữ nghĩa là đặc trưng đơn yếu nhất (bỏ đi mất 1,4 F1), chênh độ phức tạp mạnh nhất
   (mất 7,4). Wang et al.: nhóm "chênh độ phức tạp" hơn nhóm "liên quan chủ đề".
3. **Hạn chế cặp ứng viên bằng đồng xuất hiện là thói quen khi làm dữ liệu — chưa ai đo nó làm mất bao nhiêu.**
   Talukdar & Cohen chỉ xét cặp có liên kết Wikipedia; CPR-Recover chỉ gán cặp "cùng xuất hiện" trong cặp môn có tiên
   quyết (3.544 cặp); MOOCCube chỉ lấy khái niệm cùng môn. Talukdar & Cohen có quan sát sơ bộ: phần lớn trang trong
   cấu trúc tiên quyết nối với trang gốc qua *"nhiều đường liên kết ngắn"*.

### 3.2 LLM cho tiên quyết, 2024–2026

| Công trình | Năm · nơi đăng | Thiết lập | Kết quả | Điều đáng giữ |
|---|---|---|---|---|
| Yang et al., *Leveraging LLMs for Concept Graph Recovery…* | 2024 · arXiv 2402.14293 | hỏi từng cặp YES/NO, zero-shot, không văn bản; biến thể CoT, RAG, thêm tài liệu | GPT-4 zero-shot F1 0,777 (3 miền LectureBankCD) > Node2vec có giám sát 0,747; CoT kéo F1 miền CV từ 0,763 xuống 0,416 | thêm tài liệu bài giảng **giảm** kết quả (*"nhiễu và nội dung quá dài"*); thêm đoạn mở đầu Wikipedia thì tăng; RAG không tăng đều, tác giả nghi mô hình đã thấy dữ liệu; phải lấy mẫu cạnh vì số cặp tăng bậc hai và chi phí API |
| Graphusion — Yang et al. | 2024 · arXiv 2407.10794; WWW 2025 Companion | trích bộ ba cục bộ rồi **hợp nhất toàn cục** (gộp thực thể, giải xung đột, suy bộ ba mới) | LectureBankCD-NLP: GPT-4o zero-shot F1 0,796; + RAG 0,818; chuyên gia chấm quan hệ 2,37/3 (κ 0,65–0,67) | bỏ bước hợp nhất thì chất lượng giảm rõ; mọi mô hình **nghiêng về** `Prerequisite_of` và `Used_for` — 25–45% quan hệ trích ra là `Prerequisite_of` |
| ACE — Aytekin & Saygın | 2024 · JEDM 16(2) | xếp hạng mọi cặp theo "tham chiếu ngữ nghĩa" giữa mô tả khái niệm; chuyên gia duyệt từ trên xuống; cặp suy được từ đường đi bị gỡ | UCD: GPT-4o-mini zero-shot P 86,7 R 35,8 F1 50,7; + RAG Wikipedia P 87,2 R 61,1 F1 71,9; LLaMA 3 F1 67,0 | hỏi từng cặp: **precision cao, recall thấp**; hai mô tả nhắc nhau thì chiều do chuyên gia chọn |
| Aytekin & Saygın | 2024 · Interactive Learning Environments | tinh chỉnh LLM để phát hiện tiên quyết kèm giải thích | *"LLM đã tinh chỉnh là mô hình hiệu quả để phát hiện tiên quyết"* *(theo abstract)* | — |
| AutoPRE — Li et al. | 2025 · NLPCC (LNCS) | đa agent Explainer/Determiner/Criticizer; chiến lược Decomposition, Voting, Confrontation | +13,04% accuracy trên hai bộ công khai *(theo abstract, đọc gián tiếp qua công cụ tìm kiếm)* | — |
| Zhao et al., *Evidence-Linked Curriculum KGs* | 2026 · AIED (LNCS) | LLM trích cạnh mô-đun–kỹ năng; mỗi quan hệ nối với đoạn bằng chứng có offset | 86,2% của 265 cạnh kỹ năng được người duyệt là đúng; tiên quyết mô-đun–mô-đun suy ra: precision 71,1% *(theo abstract, đọc gián tiếp)* | bằng chứng có offset làm cả quy trình **kiểm được** |
| K12-KGraph — Liang et al. | 2026 · arXiv 2605.09635 | đồ thị theo chương trình từ sách giáo khoa: 9 kiểu node, 14 kiểu quan hệ, có chuỗi tiên quyết | benchmark 23.640 câu, có nhóm "Prereq" *(theo abstract)* | — |

Edu-Graph RAG (arXiv 2506.22303) đã khảo ở báo cáo A3 §5b.2.

**Lỗi đặc trưng — theo nguồn:**

- **Kiến thức nền đủ để thắng bộ vàng kiến thức nền**, và văn bản có khi làm giảm (Yang et al.). Hệ quả cho dự án đã
  nêu ở mục 1: cần đo tỉ lệ cạnh LLM khẳng định được **khi không có văn bản** (thí nghiệm E4).
- **Hai hành vi ngược nhau tuỳ cách hỏi.** Hỏi từng cặp có/không: dè dặt — precision cao, recall thấp (ACE). Trích
  mở: rải `Prerequisite_of` (Graphusion). *Suy luận:* 2b nên giữ vai **kiểm định cặp ứng viên**, không trích mở; và
  phải đo cả hai phía P/R.
- **CoT làm thiên về "không"** trong bài toán này (Yang et al.). Không mặc định bật suy luận dài; báo cáo A4/A5 mục
  4.7 đã ghi tác dụng của suy luận đổi theo họ mô hình.
- **Chiều mơ hồ khi hai khái niệm nhắc nhau**: ACE gặp *linked list* và *tree* tham chiếu lẫn nhau với điểm gần bằng
  nhau, nên để chuyên gia chọn chiều.
- **Thiên vị vị trí khi so cặp**: MT-Bench (NeurIPS 2023) đổi chỗ hai câu trả lời thì GPT-4 chỉ nhất quán 65% số ca,
  GPT-3.5 46,2%, Claude-v1 23,8%, đa số nghiêng về vị trí đầu. PRP (NAACL 2024) hỏi hai lần với hai thứ tự, chỉ nhận
  kết luận khi hai lần khớp.
- **Confidence tự khai quá tự tin**: *"khi nói ra độ tự tin, LLM có xu hướng quá tự tin"* (Xiong et al., ICLR 2024).
- **Nhắc trong định nghĩa ≠ tiên quyết**: lỗi chính mà giáo viên tìm thấy trong bộ vàng PREAP là *"khái niệm được
  nhắc khi giải thích khái niệm khác nhưng chỉ là giải thích bổ sung"* — kèm lỗi chiều (câu *"Đại số sơ cấp khác số
  học ở việc dùng trừu tượng như dùng chữ thay cho số"* bị gán thành đại số sơ cấp là tiên quyết của "chữ", "số").
  Đây đúng là luật 0,9 của addendum §806.

**Ép dẫn chứng.** A3 đã có câu bằng chứng định vị tất định; báo cáo A4/A5 mục 5.4 đã khảo CAMS và ALCE. Thêm cho 2b:
*Suy luận:* executor kiểm **chunk bằng chứng có nhắc cả hai đầu cạnh** — tra trong mention map, không tốn lời gọi —
để chặn cạnh dẫn một chunk chẳng liên quan.

### 3.3 Nhãn vàng và trần chất lượng

| Bộ / nghiên cứu | Cách gán | Đồng thuận |
|---|---|---|
| CrowdComp (Talukdar & Cohen 2012) | Mechanical Turk, chỉ cặp có liên kết | κ 0,54 (trung bình 5 miền) |
| Gordon et al. 2016 | 8 người, thang ba bậc | Pearson 0,357 (câu hỏi phụ thuộc) |
| UCD (Liang et al. 2017) | 3 trong 13 sinh viên mỗi cặp | Fleiss κ 0,42 |
| Pan et al. 2017 | 3 người, kiến thức nền + sách | κ 0,59–0,65 |
| TutorialBank (Fabbri et al. 2018) | 3 nhãn (có/không/phần nào) | Fleiss κ 0,30 |
| LectureBank (Li et al. 2019) | 2 nghiên cứu sinh, nhị phân | Cohen κ 0,70 |
| R-VGAE (Li et al. 2020) | cặp bổ sung | Cohen κ 0,63 |
| PREAP (Alzetta et al. 2023) | gán trong lúc đọc; κ tính cả **đồng thuận ngầm qua bắc cầu** | 0,45–0,71; ca thực tế 0,60, lên 0,62 sau lượt rà soát |
| Graphusion 2024 (chấm đầu ra LLM) | 2 chuyên gia, thang 1–3 | κ 0,51–0,67 |

*Suy luận:* hai người gán thường chỉ đồng thuận κ 0,3–0,7. Không hệ nào "vượt" được trần đó một cách có nghĩa; nên
chấm LLM như **người gán thứ ba** — κ(LLM, từng người) so với κ(người, người) — bên cạnh P/R/F1. Và vì 2b chỉ tạo cạnh
trực tiếp rồi transitive reduction, cách tính đồng thuận có xét bắc cầu của PREAP là cách chấm đúng cho đầu ra dạng DAG.

### 3.4 Sinh cặp ứng viên

| Bộ sinh | Bằng chứng từ văn liệu | Đánh đổi |
|---|---|---|
| Mọi cặp | recall = trần của bộ phán | tiền thấp ở quy mô giáo trình (mục 7), nhưng gán theo cặp sinh thừa quan hệ và κ thấp (PREAP: bộ MMP có 73–287 quan hệ so với 22–29 của PREAP trên cùng văn bản); Yang et al. phải lấy mẫu cạnh |
| Đồng xuất hiện (chunk/mục/môn) | cách làm dữ liệu của MOOCCube, CPR-Recover; Talukdar & Cohen chỉ xét cặp có liên kết | chưa ai đo phần cạnh mất; bỏ sót cạnh ngầm — Pal et al.: *"Đại số tuyến tính"* không được nhắc mà vẫn là tiên quyết của *"Mạng nơ-ron"* (chỉ *"nhân ma trận"* được nhắc) |
| Mention có hướng (RefD, LOrd) | Pan et al.: RefD precision 73–78, recall 43–45 trên tập con Wikipedia; Jia et al.: RefD *"precision cao hơn, recall thấp hơn"* | tốt để **xếp hạng và đoán chiều**, kém để đề cử một mình |
| kNN embedding mô tả | độ giống là đặc trưng yếu để quyết (AL-CPL; Pan et al.) | đề cử cặp cùng chủ đề, không bám văn bản |
| GNN link prediction (GAE/VGAE, CPRL) | cần nhãn huấn luyện; đánh giá trên tập cân bằng; Jia et al.: huấn luyện ở một miền rồi dùng cho miền khác thì *"thất bại"* | không dùng được cho tài liệu mới chưa có nhãn; chỉ là baseline khi có vàng |
| Theo chương / theo cụm | nhánh 1/2 của preview; A8a của addendum | mù cặp vắt ngang phân vùng — lý do tồn tại của pass phụ |

**Chi phí của "mọi cặp" — tính với giá thật.** Giá niêm yết `gemini-3.1-flash-lite` (trang giá cập nhật 2026-09-11):
0,25 USD/triệu token vào, 1,50 USD/triệu token ra; Batch API bằng nửa. Giả định (ghi rõ là giả định): 250 node học
được — quy mô tham chiếu ở preview §317 —, mỗi lời gọi một khái niệm neo + 30 ứng viên, mỗi ứng viên kèm ≈ 300 token
văn bản định nghĩa, mỗi phán quyết ≈ 40 token ra. Hỏi cả hai thứ tự (chống thiên vị vị trí): 62.250 phán quyết ≈
2.075 lời gọi ≈ 19,7 triệu token vào + 2,5 triệu token ra ≈ **8,7 USD** (≈ 4,3 USD với Batch API). Chi tiết ở mục 7.

*Suy luận:* ở quy mô giáo trình, tiền **không** là ràng buộc chính; độ trễ (hàng nghìn lời gọi) và độ chính xác mới
là. Nên lập luận cho mention map phải là: bộ sinh bám văn bản cho **precision** và **bằng chứng** tốt hơn hỏi mọi cặp,
với recall không kém nhiều — hai vế đều phải đo (E2, E3). Văn liệu blocking ủng hộ **hợp** nhiều bộ sinh rồi tỉa theo
ngân sách (mục 4.2); thứ tự ưu tiên giữa chúng phải đến từ đo recall@ngân sách, không từ lập luận.

Một chi tiết thiết kế đáng lấy từ báo cáo A4/A5 (ComEM, mục 3.2 ở đó): hỏi theo **khái niệm đích với danh sách ứng
viên** — *"trong các khái niệm này, cái nào là tiên quyết trực tiếp của X như tài liệu trình bày?"* — thay vì từng cặp
độc lập. *Suy luận:* thấy các lựa chọn cạnh nhau, mô hình dễ chọn cái **trực tiếp** hơn, bớt cạnh bắc cầu thừa.

### 3.5 Chiều cạnh và doc-order prior

- Wang et al. (CIKM 2016): *"khái niệm thường được trình bày bằng cách giới thiệu tiên quyết của nó trước; nên thứ
  tự hai khái niệm xuất hiện trong tài liệu giúp nhận ra quan hệ tiên quyết"*; đặc trưng giáo trình (đồng xuất hiện
  trong chương, khoảng cách TOC) hơn có ý nghĩa thống kê so với đặc trưng Wikipedia ở một số miền.
- Pan et al. (ACL 2017): Apd (khoảng cách vị trí xuất hiện trung bình) dựa trên đúng giả thuyết đó — nhưng bỏ nó chỉ mất
  2,4 F1, yếu nhất trong nhóm cấu trúc, vì *"giảng viên đôi khi nhắc lại khái niệm tiên quyết **sau** khi giới thiệu
  khái niệm kế tiếp"*.
- Pal et al. (arXiv 2020): luật thứ tự **cứng** — khái niệm xuất hiện trước không bao giờ nhận khái niệm sau làm tiên
  quyết — làm AUPRC tăng rõ trên dữ liệu giáo trình. Cái giá là cấm hẳn mọi cạnh ngược.
- Agrawal et al. (KDD 2012) dựng hẳn công cụ đo *"gánh nặng hiểu do trình bày khái niệm không tuần tự"* trên sách giáo
  khoa — tức giáo trình thật **có** vi phạm thứ tự. Study Navigator (JEDM 2014) còn cố ý trỏ tới mục **sau** cho người
  đọc "tò mò".
- Báo cáo A4/A5 mục 6.3 đã đề xuất lấy thứ tự từ **provenance**, không từ lần nhắc đầu; addendum §406 đã theo:
  `first_order_index` từ chunk định nghĩa, giữ thêm `first_mention_index`.

*Suy luận:* không có nguồn nào ủng hộ con số "trừ 0,1" (addendum §806, preview §291). Nên (1) code ghi
`order_relation` ∈ {thuận, ngược, cùng chunk} theo thứ tự provenance cho mọi cạnh; (2) cho phép cạnh ngược khi có câu
tường minh; (3) hiệu chỉnh mức trừ trên vàng — đo tỉ lệ cạnh vàng ngược thứ tự provenance so với ngược thứ tự mention
(E8); (4) dùng tín hiệu chiều thứ hai rẻ và độc lập: **mention có hướng** (mục 4.2) — B được nhắc trong chunk định
nghĩa của A thì B → A.

### 3.6 Nhất quán toàn cục

**Chu trình không luôn là lỗi.** TutorialBank có 33 cạnh hai chiều trên 827 cạnh (≈ 4%); tác giả giải thích định
nghĩa tiên quyết của họ *"không cấm hai chiều — chủ đề này giúp giải thích chủ đề kia và ngược lại"*, cộng với độ
giống giữa chủ đề (BLEU–ROUGE; Backpropagation–Gradient descent), và đề xuất gộp các cặp đó để có DAG. *Suy luận:* một
2-chu trình ở 2b là tín hiệu (a) xem lại danh tính — cặp anh em hay nghi trùng theo rubric 2a (addendum §760–767) —
hoặc (b) đổi thành quan hệ kiểu mở đối xứng, **trước** khi nghĩ tới cắt cạnh.

**Cắt "cạnh confidence thấp nhất"** (addendum §525, preview §329) dựa vào confidence đã hiệu chỉnh. Confidence LLM tự
khai thiên về quá tự tin (Xiong et al. 2024) nên dồn về vài giá trị cao — nhiều ca hoà, và cạnh bị cắt có thể là cạnh
đúng. Minimum feedback arc set là bài toán NP-khó (Karp 1972) và heuristic nhanh kinh điển là Eades, Lin & Smyth (IPL
1993) *(cả hai chỉ kiểm siêu dữ liệu)*. *Suy luận:* SCC trong đồ thị `requires` của một tài liệu thường nhỏ; tìm vét
cạn trong từng SCC là khả thi, với thứ tự ưu tiên giữ cạnh: loại bằng chứng (tường minh > định nghĩa > mạch trình bày)
> thuận thứ tự provenance > số nguồn độc lập (`origins`) > confidence.

**Transitive reduction trên đồ thị nhiễu.** `networkx.transitive_reduction` đòi DAG (đồ thị có chu trình thì *"không
xác định duy nhất"*) và không giữ thuộc tính cạnh (tài liệu NetworkX 3.6.1). ACE cũng xoá cạnh thành bắc cầu mỗi khi
chuyên gia thêm cạnh — nhưng cạnh của ACE do chuyên gia duyệt. *Suy luận:* layering Kahn chỉ phụ thuộc tính đến được,
nên transitive reduction **không đổi lớp**; nó chỉ đổi cái hiển thị và cái gọi là "tiên quyết trực tiếp". Trên đồ thị
nhiễu, một cạnh sai tạo đường vòng sẽ xoá một cạnh trực tiếp đúng; khi A13 gỡ cạnh sai, cạnh đúng không tự quay lại.
Nên giữ transitive reduction như một **khung nhìn** (đánh dấu `redundant_via`), không xoá.

**Tỉa theo reachability với oracle nhiễu.** Crowdsourced join (Wang et al., SIGMOD 2013): suy bằng bắc cầu *"tiết kiệm
nhiều tiền và thời gian hơn, đổi lại mất một ít chất lượng"*. Liang et al. (EDM 2019) chứng minh số truy vấn tối thiểu
bằng cỡ transitive reduction — với oracle **hoàn hảo** — và để *"học thứ tự bộ phận từ oracle nhiễu"* làm việc tương
lai. Lý do preview §231 đưa ra — *"edge trực tiếp đằng nào cũng bị transitive reduction xóa"* — chỉ đúng khi đường gián
tiếp đúng. *Suy luận:* chỉ tỉa khi mọi cạnh trên đường đều có bằng chứng tường minh; còn lại đưa đường đi vào hồ sơ
(`existing_edges`) để agent xét; ghi log cặp bị tỉa để kiểm mẫu.

**Nhiều phiên cùng ghi.** `add_edge` chặn chu trình đồng bộ (addendum §740) nghĩa là *cạnh nào đến trước thì thắng* —
kết quả phụ thuộc thứ tự section trong vòng lặp chương và thứ tự commit giữa các phiên song song. Temperature 0 không
bảo đảm tất định: Atil et al. (arXiv 2408.04667) đo được accuracy dao động tới 15% giữa các lượt chạy cấu hình "tất
định". **Số đo dự án** (lượt chạy A4/A5): 217/217 quyết định giống hệt qua ba lượt — tốt, nhưng gắn với mô hình và hạ
tầng lúc đó. *Suy luận:* các phiên nên ghi **đề xuất** vào log chỉ-thêm; một bộ gộp tất định áp theo khoá (phiên, thứ
tự op); chu trình giải ở tầng 3 theo SCC, với đủ bằng chứng của mọi phía.

### 3.7 Thiết kế agent/executor — phần báo cáo A4/A5 chưa có

1. **Chống thiên vị vị trí**: hỏi hai thứ tự như PRP, hoặc một thứ tự chuẩn + kiểm nhất quán; hai lần lệch nhau ⇒
   `deferred`.
2. **Mô hình trả loại bằng chứng, code quy ra số**: {nói tường minh, nằm trong định nghĩa, mạch trình bày, suy đoán}
   → 0,9/0,7/0,5/không tạo. Không lấy con số confidence mô hình tự khai (Xiong et al. 2024).
3. **Hỏi theo khái niệm đích với danh sách ứng viên** thay vì từng cặp (mục 3.4).
4. **Bám văn bản như PREAP**: đưa đoạn văn đang giảng khái niệm và hỏi *"cần biết gì để hiểu X như đoạn này trình
   bày?"*. Nhánh chương làm việc này tự nhiên; gói của nhánh cụm phải chứa **chunk định nghĩa** của từng node.
5. **Executor kiểm chunk bằng chứng nhắc cả hai đầu** (mục 3.2).
6. **Luật "Y trong câu định nghĩa X ⇒ 0,9"** (addendum §806) cần thêm điều kiện *"cần để hiểu định nghĩa"* và kiểm
   chiều — đúng lỗi chính của PREAP.
7. **Canh trần mật độ**, không chỉ canh sàn — báo cáo A3 §5b.2 đã nêu; Graphusion cho thêm lý do: LLM trích mở rải
   `Prerequisite_of`.

---

## 4. Kiểm tính mới

### 4.1 Phân nhánh

Tách thành từng mảnh:

- **Pass chính theo chương, loop tuần tự trong chương** (preview §206, §212–§214). Xử lý theo cấu trúc là mặc định:
  A3 đã chạy theo section; CPRP trên giáo trình dùng mục lục làm đặc trưng (Wang et al. 2016; khoảng cách TOC và
  LOrd theo chương ở Jia et al. 2021). BooookScore (ICLR 2024) so hai cách đọc sách dài: cập nhật dần một bản tóm tắt
  chạy *"cho BooookScore thấp hơn nhưng nhiều chi tiết hơn"* so với gộp phân cấp *(theo abstract)* — cùng đánh đổi
  giữa loop tuần tự và phiên song song. PREAP cho lý do học thuật để thích loop tuần tự: gán **trong lúc đọc** nhất
  quán hơn gán theo cặp.
- **Pass chính theo cụm chủ đề** (preview §207, §216–§237). Cụm làm đơn vị xử lý đã phổ biến: GraphRAG (cộng đồng
  Leiden để tóm tắt), RAPTOR (cụm để truy hồi), Graphusion (hợp nhất toàn cục sau trích cục bộ). Và chính **A8a của
  addendum** đã là "mỗi cụm một lời gọi" — nhánh 2 là pipeline gốc.
- **"Ảnh gương"** (preview §210; addendum §731). Mô tả chính xác bằng ngôn ngữ ER: *hai lượt blocking với hai khoá —
  vị trí trong tài liệu và chủ đề — trong đó lượt thứ hai được cắt tỉa kiểu meta-blocking, chỉ giữ phần rìa nghi
  ngờ.* Nguyên lý nhiều lượt nhiều khoá có từ Hernández & Stolfo (1995); phân vùng chồng lấn để chịu sai số từ canopy
  (2000); "redundancy-positive blocking" cố ý đặt mỗi thực thể vào nhiều khối để tăng recall (Papadakis et al. 2014).
  Không tìm được công trình CPRP nào dùng hai phân vùng bù nhau.
- **Định tuyến theo cấu trúc tài liệu** (preview §202–§208; addendum §723). Không tìm được tiền lệ trong CPRP.
  *Suy luận:* văn liệu blocking cho thấy độ chính xác đến từ **hợp** nhiều lượt; định tuyến là chọn **một** lượt
  chính. Vậy câu cần chứng minh là: *định tuyến đạt gần recall của chạy cả hai khoá với chi phí thấp hơn rõ*.
- **Luật "< 50 trang ⇒ một phiên, khỏi pass phụ"** (preview §208; addendum §729). *Suy luận:* không có cơ sở. Một tài
  liệu 50 trang có thể có ~100 node học được, tức ~4.950 cặp — không lời gọi nào xét hết; mô hình sẽ tự lấy mẫu những
  cặp nổi bật. Báo cáo A4/A5 mục 4.3 và 5.5 đã dẫn LLM-CER (độ chính xác sụt khi quá ~9 bản ghi mỗi lượt) và *Lost in
  the Middle*. Đơn vị phiên phải tính theo **tải quyết định** (số node, số cặp ứng viên mỗi lời gọi), không theo trang.
- **Tiên quyết trong chương và xuyên chương**: không tìm được công trình CPRP nào tách hai loại và đo recall riêng.
  Gần nhất là đặc trưng khoảng cách TOC (Wang et al.), Apd (Pan et al.), comprehension burden (Agrawal et al.) và
  Study Navigator. Đây chính là khoảng trống ở mục 1.

**Hai nhánh không đối xứng như spec vẽ.** Preview §210 viết: *"nhờ node canonical toàn cục, edge xuyên chương sinh tự
nhiên ngay pass chính (section chương 8 nhắc khái niệm chương 3 → resolve sẵn, evidence tại chỗ)"*. Nhưng input mỗi
iteration (preview §214) chỉ gồm *"nodes trong section đã resolve về canonical"* — tức node có **provenance** trong
section. Khái niệm chương 3 chỉ **được nhắc** ở chương 8 thì không có trong danh sách đó. *Suy luận:* muốn cạnh xuyên
chương "sinh tự nhiên", nhánh chương cần đúng thứ Study Navigator gọi là *concept references* — khái niệm dùng ở mục
này, được giảng ở mục khác — tức **cần mention map**. Mention map không phải hạ tầng riêng của nhánh cụm; nó là lớp
chung, và chỗ khác nhau giữa hai nhánh chỉ là cặp nào nằm trong cùng phiên.

### 4.2 Mention map

**Kênh exact** (preview §167–§169). Aho-Corasick (CACM 1975) là thuật toán chuẩn cho khớp nhiều mẫu. Từ điển khái niệm
là cách làm của MetaMap (JAMIA 2010) và QuickUMLS — bản sau khớp xấp xỉ bằng SimString, ngưỡng Jaccard mặc định 0,7,
và có `overlapping_criteria` chọn khớp **dài nhất** hoặc điểm cao nhất khi hai khớp chồng lấn (README @ `b8fed22`).

Hai điểm riêng của tiếng Việt:

- **Không bỏ dấu.** Pham, Pham & Le-Hong (arXiv 1709.07104) dẫn thống kê của Do et al. (IALP 2013): *"95% từ tiếng
  Việt mang dấu, và 80% trong số đó thành mơ hồ khi bỏ dấu"* *(số liệu gốc chưa đọc được, dẫn qua Pham et al.)*; ngay
  mô hình khôi phục dấu tốt nhất của họ cũng chỉ đúng 97,32%. Preview §168 đòi *"chuẩn hóa lowercase/bỏ dấu"*; spec
  A4/A5 thì chỉ chuẩn hoá **vị trí dấu thanh** (`hoá`/`hóa`, addendum §402). **Số đo dự án** (báo cáo A4/A5 mục 2.1):
  nới thêm bỏ dấu cho lớp tên chỉ gộp thêm đúng một nhóm. *Suy luận:* với mention, bỏ dấu gần như không thêm khớp
  đúng mà thêm khớp sai cho tên ngắn một–hai âm tiết (`biến`/`biên`/`biển` cùng thành `bien`).
- **Ranh giới từ là ranh giới âm tiết.** Chữ Việt cách nhau theo âm tiết, nên tên một âm tiết (`hàm`) khớp trong mọi
  tên dài chứa nó (`hàm số`, `hàm mật độ`). Cần luật khớp dài nhất bên trái và bỏ khớp lồng, như QuickUMLS.

**Kênh dense** (preview §171–§174). Truy hồi dense bằng bi-encoder là BLINK; trộn dense với sparse n-gram ký tự là
BioSyn (`S = S_dense + λ·S_sparse`). Lọc theo từng hàng thay cho ngưỡng tuyệt đối có cơ sở vững: Sparkly chọn top-k vì
ngưỡng không mang theo được (báo cáo A4/A5 mục 4.2). Nhưng có hai lỗ:

- **Hai không gian vector khác nhau.** Chunk trong kho truy hồi được embed với task type `RETRIEVAL_DOCUMENT` (kèm
  `section_path`; `index_document.py` L79–83); mô tả ứng viên embed `SEMANTIC_SIMILARITY` (`extract_entities.py`
  L1057–1058). Tài liệu Gemini mô tả mỗi task type là embedding *"được tối ưu"* cho một việc riêng. *Suy luận:* nhân
  ma trận hai loại vector đó (preview §172, *"cả hai đã có sẵn"*) là so hai thước đo khác nhau. Định nghĩa → đoạn văn
  là bài truy hồi bất đối xứng: embed mô tả node dạng `RETRIEVAL_QUERY` (vài trăm lượt, không đáng kể — nhưng vẫn là
  gọi embedding, cần chủ dự án duyệt).
- **Hub phía chunk.** Z-score theo hàng chuẩn hoá phía **node**. CSLS (Conneau et al., ICLR 2018) sinh ra để chữa
  hubness trong truy hồi láng giềng: `CSLS(x, y) = 2·cos(x, y) − r(x) − r(y)`, với r là cosine trung bình tới k láng
  giềng gần nhất — trừ cả hai phía. *Suy luận:* chunk tổng quan, tóm tắt, bảng ký hiệu gần mọi node một chút nên lọt
  top-k của rất nhiều hàng; chỉ chuẩn hoá theo hàng không chặn được. Cần chuẩn hoá hai phía.

**Provenance ≠ mention** (preview §165). Đã có trong văn liệu giáo trình từ trước LLM: key concept của Wang et al.
(được bàn) khác khái niệm chỉ xuất hiện; Study Navigator nối *"khái niệm dùng ở mục s"* với *"mục t nơi nó được
giảng"*; Agrawal et al. đo gánh nặng khi khái niệm được dùng trước khi được giảng; Pal et al. dùng tần suất (= 1 là
tham chiếu, > 1 là được bàn). Trong pipeline KG bằng LLM thì hiếm: GraphRAG và LightRAG gắn thực thể với text unit
**nơi trích ra** (provenance); chế độ noun graph của GraphRAG thì dựa trên mọi lần xuất hiện nhưng không phân biệt vai.
Còn một điều spec chưa tách: provenance có hai mức — chunk **định nghĩa** (A5, `defining_chunk_ids`, addendum §430)
và chunk **trích ra** (`source_chunk_ids` của A3). Báo cáo A4/A5 mục 2.7 cho thấy A3 có trích cả mục chỉ được nhắc
trong danh sách — nên "độ tin tuyệt đối" của preview §176 chỉ nên dành cho mức định nghĩa.

**Mention có hướng.** RefD định nghĩa chỉ số r(c, A) là *"liên kết Wikipedia, lần nhắc trong sách, trích dẫn…"*; LOrd
(Jia et al. 2021) là RefD trên các chương giáo trình với tần suất nhắc; AL-CPL xếp *"số lần A được nhắc trong B"* vào
nhóm đặc trưng quan trọng nhất. *Suy luận:* mention map đang cộng dồn cặp chạm **vô hướng** (preview §182, §264), bỏ
phí tín hiệu chiều rẻ nhất có sẵn: B được nhắc trong chunk định nghĩa của A là bằng chứng B → A; ngược lại là bằng
chứng A → B. Tính được từ đúng dữ liệu mention map đã có.

**Sổ cặp chạm** (preview §178–§186). Là meta-blocking: nút = khái niệm, khối = chunk, cạnh = cặp cùng khối. Papadakis
et al. (TKDE 2014) có sẵn các lựa chọn mà spec đang tự chế:

- ARCS: trọng số = tổng nghịch đảo cỡ các khối chung, dựa trên nhận xét *"khối càng chứa nhiều thực thể thì càng ít
  khả năng chúng khớp"*; ARCS cho kết quả tốt nhất trên bộ dữ liệu bẩn của họ. *Suy luận:* chunk nhắc 15 khái niệm
  không nên cộng cho mỗi cặp nhiều như chunk nhắc 2 — preview §182 (`w = min(w_n, w_m)`) chưa có chuẩn hoá này.
- Ngưỡng trọng số (WEP) dùng **trọng số trung bình** làm ngưỡng — tương đối, không tuyệt đối; ngưỡng số lượng (top-k
  toàn cục CEP hoặc top-k mỗi nút CNP) cần ít nhất một nửa, thường ít hơn một bậc số phép so, với precision cao hơn
  một bậc, đổi lại mất một phần recall. Preview §184 (*"sổ (X,Y) ≥ ngưỡng"*) chưa nói ngưỡng gì; một con số tuyệt đối
  sẽ lệch theo độ dài tài liệu.
- Trộn hai kênh bằng `min` trên hai thang khác nhau (hằng số cao cho exact, z-score cho dense) là cộng hai đơn vị
  khác nhau. *Suy luận:* giữ hai bộ đếm tách rời trong sổ.

Cộng dồn lên **cặp cụm** để quyết định mở phiên liên cụm là chỗ không tìm được tiền lệ. Gần nhất là CodRED (EMNLP
2021): trích quan hệ xuyên tài liệu qua *"đường văn bản"* — hai tài liệu chứa hai đầu, nối bằng **thực thể cầu**; và
chính addendum §498–500 coi media nằm ở hai cụm là *"boundary object"*.

**Tỉa theo reachability** — đã có với oracle người (Wang et al. 2013; ACE 2024); với oracle LLM nhiễu là câu hỏi mở
(Liang et al. 2019) — xem mục 3.6.

**Hồ sơ theo cặp, cấm cạnh ngoài hồ sơ** (preview §241–§267) là pha matching quen thuộc của ER. Hệ quả: recall của 2b
bị chặn bởi recall của bộ sinh. Preview §313 chỉ log cặp bị từ chối — đó là thước **precision** của bộ sinh; recall
thì phải kiểm bằng mẫu cặp **ngoài** bộ sinh, như spec A4/A5 đã làm với 100 cặp vàng lấy ngoài đồ thị đề cử.

**Tự giàu alias** (preview §190, §286) là một vòng bootstrapping: kết quả lượt này nuôi từ điển lượt sau. Văn liệu
bootstrapping gọi tên rủi ro: *"trôi ngữ nghĩa thường xảy ra khi thuật ngữ mơ hồ hoặc sai lọt vào rồi chi phối vòng
lặp"* (McIntosh & Curran, ACL-IJCNLP 2009). Báo cáo A4/A5 mục 4.8 đã có luật chặn cho alias: chỉ nhận khi câu bằng
chứng có dạng tương đương.

**`flag_missing_node` chạy ngược** (preview §192): cụm từ lặp nhiều không khớp node nào. Cùng hình dạng với mention
không liên kết được (NIL) trong entity linking và trích thuật ngữ; không có gì mới, nhưng rẻ và đáng làm.

### 4.3 Kết luận về tính mới

| Thành phần | Kết luận | Công trình gần nhất | Lý do |
|---|---|---|---|
| Pass chính theo chương, loop tuần tự | Chuẩn | Wang et al. 2016 (TOC); BooookScore 2024 (cập nhật dần); PREAP 2023 (gán trong lúc đọc) | Xử lý theo cấu trúc là mặc định trong tài liệu dài và trong CPRP trên giáo trình |
| Pass chính theo cụm chủ đề | Chuẩn | A8a của chính addendum; GraphRAG; RAPTOR | Cụm làm đơn vị xử lý đã phổ biến |
| "Ảnh gương" — pass phụ theo trục kia | Kết hợp mới | Hernández & Stolfo 1995; McCallum et al. 2000; Papadakis et al. 2014 | Nguyên lý nhiều lượt nhiều khoá có từ 1995; mới ở chỗ hai khoá là cấu trúc tài liệu và chủ đề, bộ so khớp là LLM, quan hệ có hướng |
| Định tuyến theo cấu trúc tài liệu | Có thể mới, nhưng yếu | không tìm được trong CPRP | Chỉ thành đóng góp nếu đo được: gần bằng recall của chạy cả hai khoá với chi phí thấp hơn rõ |
| Luật "< 50 trang ⇒ một phiên" | Không có cơ sở | LLM-CER; Lost in the Middle (qua báo cáo A4/A5) | Tải quyết định tính theo cặp, không theo trang |
| Kênh exact (Aho-Corasick, ranh giới từ) | Chuẩn | Aho & Corasick 1975; MetaMap; QuickUMLS | — |
| Kênh dense, lọc theo hàng | Chuẩn | BLINK 2020; BioSyn 2020; CSLS 2018; Sparkly | Z-score theo hàng là chuẩn hoá cục bộ một phía |
| Provenance ≠ mention | Đã có trong văn liệu giáo trình; hiếm trong pipeline KG bằng LLM | Wang et al. 2016; Study Navigator 2014; Agrawal et al. 2012; Pal et al. 2020 | GraphRAG, LightRAG chỉ lưu nơi trích |
| Mention có hướng làm tín hiệu chiều | Đã có | RefD 2015; LOrd (Jia et al. 2021); AL-CPL 2018 | spec-preview chưa dùng — nên thêm |
| Sổ cặp chạm theo chunk | Chuẩn | Meta-blocking 2014; Mintz et al. 2009; noun graph của GraphRAG | — |
| Cộng dồn lên cặp cụm để mở phiên liên cụm | Kết hợp mới | CodRED 2021; meta-blocking | Không thấy ai dùng cặp cụm làm đơn vị phiên LLM |
| Tỉa reachability trước khi hỏi oracle | Đã có với oracle người; mở với oracle LLM | Wang et al. 2013; ACE 2024; Liang et al. 2019 | Oracle nhiễu làm lỗi lan theo bắc cầu |
| Hồ sơ theo cặp, cấm cạnh ngoài hồ sơ | Chuẩn | Pha matching trong ER; ComEM | — |
| Tự giàu alias | Đã có; rủi ro đã biết | Bootstrapping, trôi ngữ nghĩa (McIntosh & Curran 2009) | — |
| `flag_missing_node` chạy ngược | Đã có | NIL trong entity linking; trích thuật ngữ | — |
| **Toàn bộ: mention map làm bộ sinh cặp bám văn bản, có kiểm soát chi phí, cho phán quyết LLM xuyên phân vùng, có tỉa reachability** | **Kết hợp mới** | ACE 2024 (gần nhất: xếp hạng theo tham chiếu ngữ nghĩa + suy bằng đường đi + oracle người); MOOCCube (ứng viên theo đồng xuất hiện) | ACE dùng mô tả Wikipedia/GPT-3, không dùng văn bản giáo trình, không phân vùng, oracle là người |
| **Điều tra vị trí cạnh tiên quyết trong giáo trình + bộ vàng kiểu PREAP tiếng Việt** | **Có thể mới** | DocRED 2019 (40,7% cho quan hệ thường); PREAP 2023 (giao thức) | Không tìm được con số tương đương cho tiên quyết; không có bộ vàng bám văn bản tiếng Việt |

### 4.4 Biến tổ hợp thành đóng góp bảo vệ được

Một đóng góp bảo vệ được cần bốn thứ. *Toàn bộ mục này là đề xuất, tức suy luận.*

**Dữ liệu.** Ít nhất một giáo trình tiếng Việt dài có chương rõ; nếu được thêm một tài liệu phẳng để thử nhánh 2. Nhãn
vàng tiên quyết do **người** gán theo PREAP — gán trong lúc đọc, hai người độc lập, rà soát, hợp nhất —, κ tính kiểu
PREAP (có đồng thuận ngầm qua bắc cầu). Thêm một mẫu chunk gán nhãn **mention** để chấm kênh exact/dense. Bộ vàng A4
(`tests/fixtures/a4/gold-blind.json`) không dùng được cho 2b: nó gán cùng/cha–con/liên quan/khác, và do Claude gán.
PRAT — công cụ gán theo PREAP — có mã trên GitHub nhưng repo **không có license** (`IntAIEdu/PRAT` @ `4ea5bc4`); giao
thức PREAP thì công bố CC BY 4.0, dùng được.

**Baseline.** (1) Mọi cặp trong ngân sách; (2) RefD/LOrd tính trên chunk; (3) chỉ đồng xuất hiện; (4) không pass phụ;
(5) phân vùng cố định — chỉ chương, chỉ cụm; (6) một phiên theo luật < 50 trang; (7) LLM không kèm văn bản (đo rò rỉ
kiến thức nền, kiểu Yang et al. 2024).

**Chỉ số.** P/R/F1 trên cạnh trực tiếp **và** trên bao đóng (precision/recall theo đường đi như ACE); recall trên mỗi
nghìn token và trên mỗi lời gọi; USD trên mỗi cạnh đúng; Jaccard cạnh giữa ba lượt chạy; tỉ lệ cạnh có chunk bằng
chứng nhắc cả hai đầu; κ(LLM, từng người) so với κ(người, người). Mọi recall tách theo **loại vị trí** của cạnh vàng:
cùng chunk · cùng mục · cùng chương · cùng cụm · xuyên cả hai nhưng có chunk nhắc cả hai (exact / chỉ dense) · ngầm.

**Ablation.** Exact có/không bỏ dấu; + dense (z hàng / hai phía); + disambiguation (preview §188); mention vô hướng /
có hướng; ngưỡng sổ tuyệt đối / tương đối / top-k; tỉa reachability bật/tắt; định tuyến / phân vùng cố định / hợp hai
khoá; node biên thuộc hai cụm (kiểu RAPTOR) thay cho sổ cặp cụm.

**Đối chiếu Phụ lục B của spec-preview** (preview §372–§375):

| Phụ lục B | Giữ / sửa |
|---|---|
| 1. So bộ sinh xuyên cụm: co-occurrence/mention map, RefD, GNN link prediction, hỏi LLM trực tiếp — recall trên đơn vị chi phí | **Giữ**, nhưng tách phần recall@ngân sách thành thí nghiệm **không gọi LLM** (E2); GNN chỉ là baseline khi có nhãn — chuyển miền thất bại (Jia et al. 2021); thêm RefD/LOrd **trên chunk** thay cho RefD trên Wikipedia |
| 2. So mention detection: exact / + dense / + disambiguation, đo recall mention với paraphrase tiếng Việt | **Giữ** (E5); thêm nhánh không bỏ dấu và chuẩn hoá hai phía; cần nhãn mention do người gán |
| 3. Pipeline cố định vs luồng agent: chất lượng, token, tái lập | **Giữ**, nhưng chỉ có nghĩa trên bộ vàng bám văn bản; thêm đo rò rỉ kiến thức nền (E4) và điều tra vị trí cạnh (E1) — hai thứ Phụ lục B chưa có |

---

## 5. Đề xuất sửa spec

### 5.1 Chỗ spec-preview đã lỗi thời so với addendum — ảnh hưởng tới C, M, T2b

| preview | Hiện ghi | Addendum / hiện trạng |
|---|---|---|
| §24, §137–§138, §147–§148 | 2a `suggest_edge` đề xuất `requires` cho 2b | 2a không đề xuất `requires`; ghi quan hệ kiểu mở kèm bằng chứng, `subtype_of` là một kiểu (addendum §687–§689, §769; ADR 0007) |
| §118–§122 | 2a: ≥ 0,95 gộp thẳng; đồ thị ~0,75; Leiden/connected components | Lớp tên + đồ thị đề cử kNN + Louvain trần 9 (addendum §673–§683; ADR 0006) |
| §85 | Embed chunk bằng `bge-m3`/`multilingual-e5`, tái dùng cho mention map | Dự án dùng `gemini-embedding-001` 768 chiều; chunk embed `RETRIEVAL_DOCUMENT` (mục 4.2) |
| §158 | Trần 12 **node** | Trần 12 **concept**, không đếm media (addendum §461–§462) |
| §176 | Provenance = `chunk_ids` từ 2a | `first_order_index` từ chunk định nghĩa của A5, giữ `first_mention_index` (addendum §406, §430) |
| §163–§192 | Mention map trên "node" chung chung | Hệ kiểu mở: `requires` chỉ nối hai node `learnable = true` (I-G1, addendum §196); A8b đọc mọi kiểu node, media làm cầu (addendum §137, §498–§500) |
| §283 | `add_edge` kiểm chu trình, bằng chứng | Executor còn kiểm `learnable` và tên đồng nghĩa `requires` (addendum §828–§835) |

### 5.2 Sửa cụ thể

| # | File · dòng | Hiện ghi | Đề xuất | Cơ sở |
|---|---|---|---|---|
| 1 | addendum §444 | cosine mô tả ≥ 0,75 | mutual-kNN trên vector mô tả A5, k nhỏ, không sàn cosine; đồng xuất hiện provenance theo chunk/mục có PMI/NPMI; cắt theo phân vị hoặc top-k | von Luxburg 2007; Maier et al. 2008/2009; GraphRAG `prune_graph`; số đo dự án (nền 0,80) |
| 2 | addendum §457 | "Leiden (hoặc Louvain)" | Leiden; manifest ghi thư viện, phiên bản, hàm mục tiêu, độ phân giải, seed, thứ tự cạnh | Traag et al. 2019; GraphRAG ghim graspologic-native < 1.3 |
| 3 | addendum §459 | fallback HDBSCAN/K-means khi edge thưa | bỏ; nếu giữ, bắt buộc bước gán ngoại lai | BERTopic `reduce_outliers`; mục 2.5 |
| 4 | addendum §460–§462; preview §158 | > 12 chạy lại Leiden; 1–2 sáp nhập "gần nhất" | CPM + `node_sizes` (học được = 1, media = 0) + `max_comm_size = 12`; định nghĩa "gần nhất"; không lọc LCC; nếu vẫn đệ quy thì ghi luật khi không chẻ được | graspologic-native `hierarchical.rs` L179–181; leidenalg 0.12.0 |
| 5 | addendum §495–§503; preview §163–§192 | boundary concepts; mention map | chấp nhận mention map làm bộ sinh cặp của A8b, với ba mức (định nghĩa / trích / nhắc) và **có hướng** | Study Navigator; RefD; LOrd; mục 4.2 |
| 6 | preview §168 | chuẩn hoá lowercase/bỏ dấu | không bỏ dấu; NFC + vị trí dấu thanh + biến thể i/y; khớp dài nhất bên trái, bỏ khớp lồng | Pham et al. 2017 (dẫn Do et al. 2013); QuickUMLS |
| 7 | preview §172–§173 | mô tả node × chunk; z-score theo hàng | embed mô tả node dạng `RETRIEVAL_QUERY` để cùng không gian với chunk; chuẩn hoá hai phía kiểu CSLS | tài liệu Gemini (task type); Conneau et al. 2018 |
| 8 | preview §182–§185 | `w = min(w_n, w_m)` cộng dồn; sổ ≥ ngưỡng | tách bộ đếm exact/dense; trọng số kiểu ARCS cho chunk nhắc nhiều khái niệm; ngưỡng tương đối (trung bình, như WEP) hoặc top-k mỗi cụm (như CNP); `requires` chỉ xét cặp học được–học được, media vẫn làm cầu | Papadakis et al. 2014; addendum §196, §451, §498 |
| 9 | preview §228–§231, §319 | loại cặp đã có đường gián tiếp | chỉ loại khi mọi cạnh trên đường có bằng chứng tường minh; còn lại đưa đường vào `existing_edges`; ghi log cặp bị loại để kiểm mẫu | Wang et al. 2013; Liang et al. 2019 |
| 10 | preview §264, §291; addendum §806 | cặp vô hướng; cạnh ngược thứ tự trừ 0,1 | hỏi hai thứ tự hoặc kiểm nhất quán; thứ tự = provenance; ghi `order_relation`; hiệu chỉnh mức trừ trên vàng | PRP; MT-Bench; Pan et al. 2017; Agrawal et al. 2012 |
| 11 | addendum §806 | Y trong câu định nghĩa X ⇒ 0,9 | thêm điều kiện "cần để hiểu" + kiểm chiều; mô hình trả loại bằng chứng, code quy ra số | PREAP (lỗi chính); Xiong et al. 2024 |
| 12 | addendum §729; preview §208 | < 50 trang ⇒ một phiên | đơn vị phiên theo tải quyết định: số node học được và số cặp ứng viên mỗi lời gọi | LLM-CER, Lost in the Middle (báo cáo A4/A5) |
| 13 | preview §214; addendum §747 | input iteration nhánh chương: node trong section | thêm "khái niệm được nhắc trong section, được giảng nơi khác" từ mention map | Study Navigator; mục 4.1 |
| 14 | preview §313 | tỉ lệ từ chối cao ⇒ siết ngưỡng mention map | tỉ lệ từ chối đo precision bộ sinh; thêm kiểm recall bằng mẫu cặp **ngoài** bộ sinh | cách spec A4/A5 lấy 100 cặp ngoài đồ thị |
| 15 | addendum §525; preview §329 | cắt cạnh confidence thấp nhất mỗi chu trình | xử lý theo SCC; 2-chu trình ⇒ xét anh em/trùng trước; ưu tiên giữ theo loại bằng chứng > thứ tự provenance > số nguồn > confidence | TutorialBank (4% hai chiều); Xiong et al. 2024 |
| 16 | addendum §531; preview §331 | transitive reduction xoá cạnh dư | giữ như khung nhìn: đánh dấu `redundant_via`, không xoá; chấm bằng chỉ số theo đường đi | tài liệu NetworkX; ACE; mục 3.6 |
| 17 | addendum §544; preview §337 | stage = layer ∩ cluster, trần 5–8 | ghi rõ cách xử lý node không có tiên quyết (không dồn hết vào lớp 1); xét phân lớp có trần bề rộng | mục 2.6 |
| 18 | preview §190, §286 | tự giàu alias | chỉ nhận alias khi câu bằng chứng có dạng tương đương, qua duyệt; không nạp lại trong cùng lượt | McIntosh & Curran 2009; báo cáo A4/A5 mục 4.8 |
| 19 | addendum §740 | `check_cycle` đồng bộ, chặn cạnh tạo chu trình | phiên ghi đề xuất vào log; bộ gộp tất định; chu trình giải ở tầng 3 theo SCC — tránh "đến trước thắng" | mục 3.6; Atil et al. |

---

## 6. Không nên làm

- **Giữ ngưỡng cosine tuyệt đối cho A6** (addendum §444). Nền cosine của dự án đã 0,80; văn liệu dựng đồ thị không
  ủng hộ; GraphRAG cũng không làm vậy.
- **Tin `max_cluster_size` của graspologic/GraphRAG là trần cứng**, hoặc bật `use_lcc` như mặc định GraphRAG — khái
  niệm lẻ sẽ mất cụm.
- **Bỏ dấu tiếng Việt ở kênh exact.**
- **So cosine giữa vector `SEMANTIC_SIMILARITY` và `RETRIEVAL_DOCUMENT`** như thể cùng thang.
- **Dùng confidence mô hình tự khai để cắt chu trình**, hay coi "trừ 0,1" là con số đã hiệu chỉnh.
- **Xoá cạnh bằng transitive reduction** trên đồ thị chưa kiểm; **tỉa reachability qua cạnh chưa có bằng chứng**.
- **Chấm trên cặp lấy mẫu cân bằng** như văn liệu CPRP, hay lấy F1 0,7–0,8 của văn liệu làm kỳ vọng — các bộ vàng đó
  đo kiến thức nền, và dương trong giáo trình thật chỉ 2–15%.
- **Dùng GNN link prediction làm bộ sinh chính** cho tài liệu mới — cần nhãn huấn luyện; chuyển miền thất bại.
- **Tuyên bố "ảnh gương" hay mention map là cơ chế mới.** Nguyên lý có từ 1995 và 2014; hội đồng nào đọc văn liệu ER
  cũng nhận ra. Tuyên bố **tổ hợp** và **phép đo**.
- **Để luật "< 50 trang" quyết định số phiên.**
- **Nạp alias do 2b đề xuất thẳng vào kênh exact** không qua duyệt.
- **Chép mã PRAT** — repo không có license. Dùng giao thức PREAP (CC BY 4.0).

---

## 7. Thí nghiệm đề xuất

Mọi lời gọi mô hình dùng `gemini-3.1-flash-lite`, temperature 0. Giá: 0,25 USD/triệu token vào, 1,50 USD/triệu token
ra; Batch API nửa giá (trang giá cập nhật 2026-09-11). Thứ tự làm quan trọng hơn danh sách: **E0 → E1, E2 (code thuần)
→ quyết có đầu tư mention map hay không → E3, E4 → E6–E8.**

**Giả định chi phí** (ghi rõ để sửa khi có số thật): 250 node học được; mỗi lời gọi một khái niệm neo + 30 ứng viên;
mỗi ứng viên ≈ 300 token văn bản định nghĩa; ≈ 40 token ra mỗi phán quyết.

| Cấu hình phán quyết | Phán quyết | Lời gọi | Token vào | Token ra | USD chuẩn | USD Batch |
|---|---:|---:|---:|---:|---:|---:|
| Mọi cặp, hai thứ tự | 62.250 | ≈ 2.075 | ≈ 19,7 tr | ≈ 2,5 tr | ≈ 8,7 | ≈ 4,3 |
| Mọi cặp, một thứ tự | 31.125 | ≈ 1.040 | ≈ 9,9 tr | ≈ 1,2 tr | ≈ 4,3 | ≈ 2,2 |
| Bộ sinh giữ 10% số cặp, hai thứ tự | 6.225 | ≈ 210 | ≈ 2,0 tr | ≈ 0,25 tr | ≈ 0,9 | ≈ 0,4 |
| Không kèm văn bản (đo rò rỉ), hai thứ tự, ≈ 80 token/ứng viên | 62.250 | ≈ 2.075 | ≈ 5,1 tr | ≈ 2,5 tr | ≈ 5,0 | ≈ 2,5 |

Với 1.000 node, số cặp gấp 16 lần: "mọi cặp, hai thứ tự" ≈ 140 USD một lượt. *Suy luận:* ở quy mô giáo trình, tiền
LLM của cả chương trình thí nghiệm dưới 100 USD; chi phí thật là **công người gán**.

| # | Thí nghiệm | Câu hỏi | Cách làm | Chi phí LLM |
|---|---|---|---|---|
| E0 | Bộ vàng PREAP tiếng Việt | Có bộ vàng bám văn bản không? | Thí điểm một chương với hai người gán để đo thời gian và κ, rồi mới quyết quy mô; gán mention trên một mẫu chunk | 0 |
| E1 | Điều tra vị trí cạnh | Cạnh tiên quyết nằm ở đâu? | Trên vàng: tỉ lệ cạnh theo sáu loại vị trí (mục 4.4); cộng NMI giữa cụm A7 và chương | 0 |
| E2 | Recall của bộ sinh theo ngân sách | Bộ sinh nào giữ được cạnh vàng với ít cặp nhất? | Mỗi bộ sinh: số cặp, recall cạnh vàng (trực tiếp, bao đóng). Bộ sinh: mọi cặp; nội chương; nội cụm; đồng xuất hiện chunk/mục; exact có/không bỏ dấu; + dense (z hàng / hai phía); mention có hướng; RefD/LOrd; kNN; hợp; định tuyến theo spec | 0 (embed mô tả node dạng `RETRIEVAL_QUERY` là vài trăm lượt embedding, cần duyệt riêng) |
| E3 | Phán quyết trên các bộ sinh chọn từ E2 | Bộ sinh bám văn bản có cho precision tốt hơn mọi cặp mà recall không kém nhiều? | Hai thứ tự; P/R/F1 trực tiếp và bao đóng; lời gọi, token, USD; ba lượt → Jaccard | ≈ 0,5–9 USD/lượt/cấu hình; 5–6 cấu hình × 3 lượt ≈ 30–60 USD |
| E4 | Rò rỉ kiến thức nền | LLM khẳng định bao nhiêu cạnh mà văn bản không dạy? | Cùng cặp, hỏi không văn bản vs có văn bản; đếm cạnh "không văn bản vẫn có" mà vàng PREAP không có | ≈ 2,5–5 USD |
| E5 | Mention detection | Exact đủ chưa, dense thêm được gì với tiếng Việt? | Exact (có/không bỏ dấu) / + dense / + disambiguation; P/R trên mẫu chunk có nhãn | 0 (disambiguation bằng embedding câu cần duyệt riêng) |
| E6 | Định tuyến | Định tuyến có gần recall của hợp hai khoá với chi phí thấp hơn? | Chương + phụ cụm / cụm + phụ liên cụm / hợp hai khoá / phân vùng cố định; recall trên nghìn token | nằm trong E3 |
| E7 | Nhất quán | Cắt chu trình, transitive reduction, tỉa reachability làm mất bao nhiêu cạnh đúng? | Trên đầu ra E3: SCC, cạnh bị cắt đúng/sai theo vàng; cạnh vàng trực tiếp bị transitive reduction xoá; cặp vàng bị tỉa | 0 |
| E8 | Doc-order prior | Bao nhiêu cạnh vàng ngược thứ tự provenance, ngược thứ tự mention? | Đếm trên vàng; hiệu chỉnh mức trừ | 0 |

E1 và E2 là hai thí nghiệm rẻ nhất và quyết định nhất: không tốn lời gọi LLM nào mà trả lời được mention map có đáng
làm không, pass phụ có đáng chạy không.

---

## 8. Giới hạn của báo cáo này

- Đánh giá thật cần tài liệu dài và nhãn vàng do người gán; báo cáo này không đo gì trên corpus.
- Chỉ đọc được abstract: Hernández & Stolfo 1995 (qua bản sao abstract của Semantic Scholar), Maier et al. 2009,
  von Luxburg 2010, BERTopic, Aytekin & Saygın (ILE 2024), Bai et al. 2025, MOOCCubeX. Đọc abstract gián tiếp qua
  công cụ tìm kiếm: AutoPRE 2025, Zhao et al. 2026. Chỉ kiểm siêu dữ liệu: Karp 1972, Aho–Garey–Ullman 1972, Eades et
  al. 1993, Coffman–Graham 1972. Không đọc được: Adorni et al. 2019 (mô tả theo PREAP), Hernández & Stolfo 1998, số liệu
  gốc của Do et al. 2013.
- Không tìm được nghiên cứu hệ thống về lỗi của LLM khi suy tiên quyết **bám văn bản giáo trình**; mục 3.2 ghép từ các
  bài gần. Khảo sát Bai et al. (ACM CSUR 2025) có thể liệt kê thêm công trình; chỉ đọc được abstract.
- Chi phí ở mục 3.4 và 7 là ước lượng theo giả định ghi rõ, giá niêm yết ngày 2026-09-11.

---

## 9. Kết luận

**Niềm tin về tính mới đúng một nửa.** Không thành phần nào của phân nhánh hay mention map là cơ chế chưa có:
"ảnh gương" là blocking nhiều lượt nhiều khoá, có từ 1995; mention map ghép entity linking lai, phân biệt
provenance/mention của văn liệu giáo trình, meta-blocking và tỉa theo bắc cầu. Nhưng chưa ai ghép chúng cho suy tiên
quyết bằng LLM trên giáo trình — một tổ hợp chính đáng, với điều kiện chứng minh được nó hơn các lựa chọn đơn giản.

**Thứ có thể mới thật nằm ở phép đo và dữ liệu, không nằm ở kiến trúc.** Văn liệu CPRP chưa trả lời cạnh tiên quyết
nằm ở đâu so với chương và chủ đề — câu hỏi quyết định cả hai đóng góp —, và các bộ vàng hiện có đo kiến thức nền,
thứ LLM có sẵn. Một bộ vàng kiểu PREAP trên giáo trình tiếng Việt dài, cộng hai thí nghiệm không tốn lời gọi LLM (E1,
E2), cho dự án câu trả lời và cho đề tài một đóng góp đứng được.

**Và vài chỗ spec cần sửa bất kể chọn luồng nào:** bỏ ngưỡng cosine tuyệt đối ở A6; trần cỡ cụm phải cứng và đếm theo
khái niệm; kênh dense đang so hai không gian vector khác nhau; không bỏ dấu tiếng Việt; mention map nên có hướng và
phục vụ cả nhánh chương; cắt chu trình, transitive reduction và tỉa reachability không nên tin vào confidence tự khai
hay cạnh chưa có bằng chứng.

---

## Nguồn

**Học tiên quyết khái niệm (CPRP) — trước LLM**
- [Crowdsourced Comprehension: Predicting Prerequisite Structure in Wikipedia — Talukdar & Cohen, BEA 2012](https://aclanthology.org/W12-2037/)
- [Measuring Prerequisite Relations Among Concepts (RefD) — Liang et al., EMNLP 2015](https://aclanthology.org/D15-1193/)
- [Using Prerequisites to Extract Concept Maps from Textbooks — Wang et al., CIKM 2016](https://clgiles.ist.psu.edu/pubs/CIKM2016-textbooks.pdf) · [DOI](https://doi.org/10.1145/2983323.2983725)
- [Modeling Concept Dependencies in a Scientific Corpus — Gordon et al., ACL 2016](https://aclanthology.org/P16-1082/)
- [Recovering Concept Prerequisite Relations from University Course Dependencies — Liang et al., AAAI 2017](https://ojs.aaai.org/index.php/AAAI/article/view/10550)
- [Prerequisite Relation Learning for Concepts in MOOCs — Pan et al., ACL 2017](https://aclanthology.org/P17-1133/)
- [Investigating Active Learning for Concept Prerequisite Learning (AL-CPL) — Liang et al., AAAI 2018](https://ojs.aaai.org/index.php/AAAI/article/view/11396)
- [TutorialBank — Fabbri et al., ACL 2018](https://aclanthology.org/P18-1057/)
- [What Should I Learn First: Introducing LectureBank — Li et al., AAAI 2019](https://arxiv.org/abs/1811.12181)
- [Active Learning of Strict Partial Orders: A Case Study on Concept Prerequisite Relations — Liang et al., EDM 2019](https://arxiv.org/abs/1801.06481)
- [Inferring Concept Prerequisite Relations from Online Educational Resources (PREREQ) — Roy et al., IAAI 2019](https://arxiv.org/abs/1811.12640)
- [Towards the Identification of Propaedeutic Relations in Textbooks — Adorni et al., AIED 2019](https://doi.org/10.1007/978-3-030-23204-7_1) *(không đọc được toàn văn)*
- [MOOCCube — Yu et al., ACL 2020](https://aclanthology.org/2020.acl-main.285/)
- [R-VGAE: Relational-variational Graph Autoencoder for Unsupervised Prerequisite Chain Learning — Li et al., COLING 2020](https://aclanthology.org/2020.coling-main.99/)
- [PRELEARN @ EVALITA 2020: Overview of the Prerequisite Relation Learning Task for Italian — Alzetta et al.](https://aclanthology.org/2020.evalita-1.54/)
- [Finding Prerequisite Relations between Concepts using Textbook — Pal, Arora & Goyal, arXiv 2011.10337](https://arxiv.org/abs/2011.10337)
- [Heterogeneous Graph Neural Networks for Concept Prerequisite Relation Learning in Educational Data (CPRL) — Jia et al., NAACL 2021](https://aclanthology.org/2021.naacl-main.164/)
- [MOOCCubeX — Yu et al., CIKM 2021](https://doi.org/10.1145/3459637.3482010) *(theo abstract)*
- [Prerequisite Relation Learning: A Survey and Outlook — Bai et al., ACM Computing Surveys 2025](https://doi.org/10.1145/3733593) *(theo abstract)*

**Nhãn vàng bám văn bản**
- [Annotation Protocol for Textbook Enrichment with Prerequisite Knowledge Graph (PREAP) — Alzetta, Torre & Koceva, Technology, Knowledge and Learning 29, 2023](https://doi.org/10.1007/s10758-023-09682-6)
- [Prerequisite Relations Annotation Tool (PRAT) — Alzetta & Torre, JASIST 76, 2025](https://doi.org/10.1002/asi.24992) · [mã PRAT @ `4ea5bc4` (không có license)](https://github.com/IntAIEdu/PRAT/tree/4ea5bc42ca1beb8e7f0f5c9948992059491c9b58)

**LLM cho tiên quyết**
- [Leveraging Large Language Models for Concept Graph Recovery and Question Answering in NLP Education — Yang et al., arXiv 2402.14293](https://arxiv.org/abs/2402.14293)
- [Graphusion — Yang et al., arXiv 2407.10794](https://arxiv.org/abs/2407.10794) · [WWW 2025 Companion](https://dl.acm.org/doi/10.1145/3701716.3717821)
- [ACE: AI-Assisted Construction of Educational Knowledge Graphs with Prerequisite Relations — Aytekin & Saygın, JEDM 16(2) 2024](https://jedm.educationaldatamining.org/index.php/JEDM/article/view/737)
- [Discovering prerequisite relations using large language models — Aytekin & Saygın, Interactive Learning Environments 2024](https://doi.org/10.1080/10494820.2024.2375338) *(theo abstract)*
- [AutoPRE: Discovering Concept Prerequisites with LLM Agents — Li et al., NLPCC 2025](https://doi.org/10.1007/978-981-95-3343-5_16) *(theo abstract, đọc gián tiếp)*
- [Building Evidence-Linked Curriculum Knowledge Graphs for Academic Pathway Planning — Zhao et al., AIED 2026](https://doi.org/10.1007/978-3-032-29744-0_32) *(theo abstract, đọc gián tiếp)*
- [K12-KGraph — Liang et al., arXiv 2605.09635](https://arxiv.org/abs/2605.09635) *(theo abstract)*
- Edu-Graph RAG, arXiv 2506.22303 — đã khảo ở `report/nghien-cuu-a3-trich-xuat-thuc-the.md` §5b.2

**Giáo trình: provenance, mention, thứ tự trình bày**
- [Study Navigator: An Algorithmically Generated Aid for Learning from Electronic Textbooks — Agrawal et al., JEDM 6(1) 2014](https://jedm.educationaldatamining.org/index.php/JEDM/article/view/41)
- [Empowering Authors to Diagnose Comprehension Burden in Textbooks — Agrawal et al., KDD 2012](https://www.microsoft.com/en-us/research/publication/empowering-authors-to-diagnose-comprehension-burden-in-textbooks/) *(theo abstract)*

**Gom cụm và dựng đồ thị**
- [From Louvain to Leiden: guaranteeing well-connected communities — Traag, Waltman & van Eck, Scientific Reports 2019](https://arxiv.org/abs/1810.08473)
- [Narrow scope for resolution-limit-free community detection — Traag, Van Dooren & Nesterov, PRE 2011](https://arxiv.org/abs/1104.3083)
- [Resolution limit in community detection — Fortunato & Barthélemy, PNAS 2007](https://arxiv.org/abs/physics/0607100)
- [The performance of modularity maximization in practical contexts — Good, de Montjoye & Clauset, PRE 2010](https://arxiv.org/abs/0910.0165)
- [Consensus clustering in complex networks — Lancichinetti & Fortunato, Scientific Reports 2012](https://arxiv.org/abs/1203.6093)
- [A tutorial on spectral clustering — von Luxburg, Statistics and Computing 2007](https://arxiv.org/abs/0711.0189)
- [Influence of graph construction on graph-based clustering measures — Maier, von Luxburg & Hein, NIPS 2008](https://papers.nips.cc/paper/3496-influence-of-graph-construction-on-graph-based-clustering-measures)
- [Optimal construction of k-nearest-neighbor graphs for identifying noisy clusters — Maier, Hein & von Luxburg, TCS 2009](https://arxiv.org/abs/0912.3408) *(theo abstract)*
- [Hubs in Space: Popular Nearest Neighbors in High-Dimensional Data — Radovanović et al., JMLR 2010](https://jmlr.org/papers/v11/radovanovic10a.html)
- [Clustering Stability: An Overview — von Luxburg, Foundations and Trends in ML 2010](https://arxiv.org/abs/1007.1075) *(theo abstract)*
- [BERTopic — Grootendorst, arXiv 2203.05794](https://arxiv.org/abs/2203.05794) *(theo abstract)* · [tài liệu outlier reduction](https://maartengr.github.io/BERTopic/getting_started/outlier_reduction/outlier_reduction.html)
- [RAPTOR — Sarthi et al., ICLR 2024](https://arxiv.org/abs/2401.18059)
- [From Local to Global: A Graph RAG Approach to Query-Focused Summarization — Edge et al., arXiv 2404.16130](https://arxiv.org/abs/2404.16130)
- [Optimal scheduling for two-processor systems — Coffman & Graham, Acta Informatica 1972](https://doi.org/10.1007/BF00288685) *(chỉ kiểm siêu dữ liệu)*

**Mã nguồn — đọc tại commit ghi dưới**
- GraphRAG 3.1.2 @ `f40e9a2`: [cluster_graph.py](https://github.com/microsoft/graphrag/blob/f40e9a26ce62ba0b3fef8837d24aafdcc6e6c704/packages/graphrag/graphrag/index/operations/cluster_graph.py#L51-L99) · [hierarchical_leiden.py](https://github.com/microsoft/graphrag/blob/f40e9a26ce62ba0b3fef8837d24aafdcc6e6c704/packages/graphrag/graphrag/graphs/hierarchical_leiden.py#L11-L26) · [stable_lcc.py](https://github.com/microsoft/graphrag/blob/f40e9a26ce62ba0b3fef8837d24aafdcc6e6c704/packages/graphrag/graphrag/graphs/stable_lcc.py#L22-L70) · [defaults: cluster](https://github.com/microsoft/graphrag/blob/f40e9a26ce62ba0b3fef8837d24aafdcc6e6c704/packages/graphrag/graphrag/config/defaults.py#L67-L73) · [defaults: prune](https://github.com/microsoft/graphrag/blob/f40e9a26ce62ba0b3fef8837d24aafdcc6e6c704/packages/graphrag/graphrag/config/defaults.py#L281-L291) · [pyproject: ghim graspologic-native](https://github.com/microsoft/graphrag/blob/f40e9a26ce62ba0b3fef8837d24aafdcc6e6c704/packages/graphrag/pyproject.toml#L46-L49) · [build_noun_graph.py](https://github.com/microsoft/graphrag/blob/f40e9a26ce62ba0b3fef8837d24aafdcc6e6c704/packages/graphrag/graphrag/index/operations/build_noun_graph/build_noun_graph.py#L99-L143) · [edge_weights.py (PMI)](https://github.com/microsoft/graphrag/blob/f40e9a26ce62ba0b3fef8837d24aafdcc6e6c704/packages/graphrag/graphrag/graphs/edge_weights.py#L10-L62) · [prune_graph.py](https://github.com/microsoft/graphrag/blob/f40e9a26ce62ba0b3fef8837d24aafdcc6e6c704/packages/graphrag/graphrag/index/operations/prune_graph.py#L14-L106)
- graspologic-native: [hierarchical.rs @ 1.3.1 `7731814`](https://github.com/graspologic-org/graspologic-native/blob/773181488b4e5b81925e302b972b294fd51f61a4/packages/network_partitions/src/leiden/hierarchical.rs#L119-L219) · [pyo3 lib.rs (mặc định 1000)](https://github.com/graspologic-org/graspologic-native/blob/773181488b4e5b81925e302b972b294fd51f61a4/packages/pyo3/src/lib.rs#L122-L177) · [hierarchical.rs @ 1.2.5 `3c98966`](https://github.com/graspologic-org/graspologic-native/blob/3c98966401effa0cbf766be4315ad956584bbdea/packages/network_partitions/src/leiden/hierarchical.rs)
- leidenalg 0.12.0 @ `368a99e`: [find_partition, max_comm_size](https://github.com/vtraag/leidenalg/blob/368a99e40bb60bae451a309e541c900920ad837c/src/leidenalg/functions.py#L21-L90) · [CPMVertexPartition, node_sizes](https://github.com/vtraag/leidenalg/blob/368a99e40bb60bae451a309e541c900920ad837c/src/leidenalg/VertexPartition.py#L849-L910)
- NetworkX 3.6.1: [transitive_reduction](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.dag.transitive_reduction.html) · [leiden_communities](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.community.leiden.leiden_communities.html)
- [QuickUMLS README @ `b8fed22`](https://github.com/Georgetown-IR-Lab/QuickUMLS/blob/b8fed224c125b245176ea250b0f056701c156219/README.md)
- Mã của dự án: `src/doc2roadmap/application/use_cases/index_document.py` L79–83 (chunk `RETRIEVAL_DOCUMENT`), `src/doc2roadmap/application/use_cases/extract_entities.py` L1057–1058 (mô tả `SEMANTIC_SIMILARITY`)

**Entity resolution, blocking, oracle**
- [The merge/purge problem for large databases — Hernández & Stolfo, SIGMOD 1995](https://doi.org/10.1145/223784.223807) *(theo abstract)*
- [Efficient clustering of high-dimensional data sets with application to reference matching (canopy) — McCallum, Nigam & Ungar, KDD 2000](http://www.kamalnigam.com/papers/canopy-kdd00.pdf)
- [Meta-Blocking: Taking Entity Resolution to the Next Level — Papadakis et al., TKDE 26(8) 2014](https://helios2.mi.parisdescartes.fr/~themisp/publications/tkde13-metablocking.pdf)
- [Leveraging transitive relations for crowdsourced joins — Wang et al., SIGMOD 2013](https://arxiv.org/abs/1408.6916) *(theo abstract)*

**Entity linking, nhận diện khái niệm, bootstrapping**
- [Efficient string matching: an aid to bibliographic search — Aho & Corasick, CACM 1975](https://doi.org/10.1145/360825.360855) *(chỉ kiểm siêu dữ liệu)*
- [An overview of MetaMap — Aronson & Lang, JAMIA 2010](https://doi.org/10.1136/jamia.2009.002733) *(chỉ kiểm siêu dữ liệu)*
- [Wikify! — Mihalcea & Csomai, CIKM 2007](https://doi.org/10.1145/1321440.1321475) · [Learning to link with Wikipedia — Milne & Witten, CIKM 2008](https://doi.org/10.1145/1458082.1458150) · [TAGME — Ferragina & Scaiella, CIKM 2010](https://doi.org/10.1145/1871437.1871689) *(cả ba chỉ kiểm siêu dữ liệu)*
- [Scalable Zero-shot Entity Linking with Dense Entity Retrieval (BLINK) — Wu et al., EMNLP 2020](https://aclanthology.org/2020.emnlp-main.519/)
- [Biomedical Entity Representations with Synonym Marginalization (BioSyn) — Sung et al., ACL 2020](https://aclanthology.org/2020.acl-main.335/)
- [Distant supervision for relation extraction without labeled data — Mintz et al., ACL-IJCNLP 2009](https://aclanthology.org/P09-1113/)
- [Word Translation Without Parallel Data (CSLS) — Conneau et al., ICLR 2018](https://arxiv.org/abs/1710.04087)
- [Reducing semantic drift with bagging and distributional similarity — McIntosh & Curran, ACL-IJCNLP 2009](https://aclanthology.org/P09-1045/)

**Tài liệu dài, quan hệ xuyên câu và xuyên tài liệu**
- [DocRED: A Large-Scale Document-Level Relation Extraction Dataset — Yao et al., ACL 2019](https://aclanthology.org/P19-1074/)
- [CodRED: A Cross-Document Relation Extraction Dataset — Yao et al., EMNLP 2021](https://aclanthology.org/2021.emnlp-main.366/)
- [BooookScore: A systematic exploration of book-length summarization in the era of LLMs — Chang et al., ICLR 2024](https://arxiv.org/abs/2310.00785)

**LLM làm giám khảo: vị trí, độ tin, tái lập**
- [Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena — Zheng et al., NeurIPS 2023 Datasets and Benchmarks](https://arxiv.org/abs/2306.05685)
- [Large Language Models are Effective Text Rankers with Pairwise Ranking Prompting — Qin et al., NAACL 2024](https://arxiv.org/abs/2306.17563)
- [Can LLMs Express Their Uncertainty? — Xiong et al., ICLR 2024](https://arxiv.org/abs/2306.13063)
- [Non-Determinism of "Deterministic" LLM Settings — Atil et al., arXiv 2408.04667](https://arxiv.org/abs/2408.04667)

**Thuật toán đồ thị cổ điển**
- [Reducibility among Combinatorial Problems — Karp 1972](https://doi.org/10.1007/978-1-4684-2001-2_9) · [A fast and effective heuristic for the feedback arc set problem — Eades, Lin & Smyth, IPL 1993](https://doi.org/10.1016/0020-0190(93)90079-O) · [The Transitive Reduction of a Directed Graph — Aho, Garey & Ullman, SIAM J. Comput. 1972](https://doi.org/10.1137/0201008) *(cả ba chỉ kiểm siêu dữ liệu)*

**Tiếng Việt**
- [On the Use of Machine Translation-Based Approaches for Vietnamese Diacritic Restoration — Pham, Pham & Le-Hong, arXiv 1709.07104](https://arxiv.org/abs/1709.07104) (dẫn Do et al., IALP 2013 — chưa đọc được bài gốc)

**Gemini**
- [Gemini API — Pricing (cập nhật 2026-09-11)](https://ai.google.dev/gemini-api/docs/pricing)
- [Gemini API — Embeddings, task types (cập nhật 2026-09-04)](https://ai.google.dev/gemini-api/docs/embeddings)
