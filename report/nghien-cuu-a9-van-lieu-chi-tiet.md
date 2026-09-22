# A9 — Kiểm định đồ thị tiên quyết: khảo sát văn liệu gốc

> **Ghi chú biên tập (reviewer, 2026-09-21).** Đây là **bản khảo sát văn liệu chi tiết** của vòng 36, giữ nguyên
> văn để tra cứu trích dẫn. Bản tổng hợp, có đối chiếu với số đo trên artifact thật và có các đề xuất đánh số
> Đ1–Đ23, nằm ở [`nghien-cuu-a9-a10-kiem-dinh-va-lo-trinh.md`](./nghien-cuu-a9-a10-kiem-dinh-va-lo-trinh.md) —
> **đọc bản đó trước**; bản này là phụ lục.
>
> **Một kết luận trong bản này đã được reviewer đính chính**, xem khung ở mục 1.3: nhận định "vét cạn chết ở SCC
> 7 node" **không mô tả đúng mã của dự án**, vì `_feedback_edges` chặn theo *số cạnh nội bộ* (16) chứ không theo
> số node. Luận điểm thay thế — liệt kê chu trình + ILP — vẫn đứng vững và đã thành Đ1.
>
> Script đo của phần này đã được đưa vào repo tại [`scripts/nghien-cuu-a9/`](../scripts/nghien-cuu-a9). Các PDF
> bài báo và bộ dữ liệu bên thứ ba **không** vào repo — đường dẫn tải nằm ở mục *Nguồn*.

Ngày khảo sát: 2026-09-21. Phạm vi: nguồn sơ cấp (bài báo toàn văn, mã nguồn thư viện, dữ liệu công bố).
Quy ước câu: **(a)** sự thật từ nguồn — kèm công trình + năm + nơi công bố + URL; **(b)** con số trích dẫn — ghi rõ bảng/mục; **(c)** ý kiến của tôi — mở đầu bằng "**Suy luận:**".

Ngoài đọc văn liệu, tôi đã **tải dữ liệu gốc và tự đo lại**. Mọi con số gắn nhãn **[tự đo]** là do tôi tính trong phiên này; script nằm ở [`scripts/nghien-cuu-a9/`](../scripts/nghien-cuu-a9) (`cit_stats.py`, `cut_jhu.py`, `ds_stats.py`, `scc_deep.py`, `tr_noise.py`, `tr_noise2.py`, `bf2.py`, `bf_cost.py`); chúng cần bộ dữ liệu bên thứ ba tải từ đường dẫn ở mục *Nguồn*, không kèm trong repo. Phép đo được kiểm chứng: dựng lại đồ thị Caltech từ danh mục môn cho ra **đúng 640 cạnh sau rút gọn bắc cầu**, khớp chính xác Bảng I của Zuev & Stavrinides (2025) — nên tôi tin các con số còn lại từ cùng pipeline.

---

## Tóm tắt điều hành

Sáu điểm thiết kế A9, sau khảo sát:

| # | Điểm thiết kế | Kết luận |
|---|---|---|
| 1 | Chỉ đọc `requires` trên node `learnable` | Không có gì phản bác; KST cho khung lý thuyết còn thiếu |
| 2 | Vét cạn trên SCC; confidence xếp cuối | **Vét cạn: nên thay** — xem đính chính ở mục 1.3 (mã dự án có chặn 16 cạnh nên không treo, nhưng trên trần thì lặng lẽ chuyển sang xấp xỉ). **Thứ tự ưu tiên: xác nhận mạnh** |
| 3 | Giữ chu trình hai cạnh, chỉ gắn cờ | Con số ~4% **có thật** (3,87%, LectureBank 2.0). Nhưng cách xử lý **sai khung**: KST bảo *gộp*, không phải *giữ* |
| 4 | Cổng 0,5 cạnh/node và 60% cô lập | **Bác bỏ bằng số thực nghiệm** — một chương trình học thật kích hoạt cả hai cổng |
| 5 | Chỉ đánh dấu cạnh bắc cầu, không xoá | **Xác nhận mạnh**, kể cả định lượng lẫn bằng một cơ chế thiên lệch mà dự án chưa biết |
| 6 | Chuẩn hoá sổ đăng ký kiểu quan hệ | Phù hợp thông lệ; không tìm thấy nguồn phản bác |

---

## 1. Gỡ chu trình là bài toán minimum feedback arc set (MFAS)

### 1.1 Độ khó

(a) Bài toán feedback arc set nằm trong danh sách 21 bài toán NP-đầy đủ của Karp, trong *Reducibility Among Combinatorial Problems* (Karp, 1972, Complexity of Computer Computations, Plenum Press) — Baharev và cộng sự dẫn lại đúng như vậy ở mục 1.1: "one of Richard M. Karp's 21 NP-complete problems" [1][2].

(a) Bài toán này **APX-hard**: trừ khi P = NP, nó không có lược đồ xấp xỉ thời gian đa thức (PTAS). Mạnh hơn, nó **kháng xấp xỉ** (*approximation resistant*): với giả thuyết Unique Games, với mọi C > 0 việc tìm một xấp xỉ hệ số C là NP-hard (Baharev, Schichl, Neumaier & Achterberg, 2021, *ACM Journal of Experimental Algorithmics* 26, mục 1.1, dẫn Kann 1992 và Guruswami và cộng sự) [1].

(b) Cận trên đơn giản: lấy tập cạnh xuôi hoặc ngược trong một thứ tự đỉnh bất kỳ cho một feedback arc set cỡ ≤ m/2; Eades–Lin–Smyth cải thiện thành **m/2 − n/6** bằng cách loại các cạnh kề nguồn/đích (mục 1.1 của [1], dẫn [11] = Eades, Lin & Smyth 1993). Thuật toán chạy **thời gian và bộ nhớ tuyến tính** (Eades, Lin & Smyth, 1993, *Information Processing Letters* 47(6):319–323) [3].

**Suy luận:** dự án gọi bước này là "tìm kiếm vét cạn" nhưng không nói rõ tối ưu hoá cái gì. Nếu mỗi cạnh có trọng số (mà thứ tự ưu tiên giữ cạnh ở điểm 2 chính là một trọng số ngầm), thì đây **đúng là MFAS có trọng số**, không phải MFAS không trọng số. Đó là hai bài toán khác nhau và cần nói rõ trong đặc tả.

### 1.2 Bản có trọng số tồn tại và đã được định nghĩa hình thức

(a) Baharev và cộng sự (2021) định nghĩa tường minh: "In the weighted feedback edge set problem, each edge has its associated weight; the unweighted version can be regarded as the weighted version with each edge having unit weight. The cost refers either to the cardinality... or to the total weight" (mục 1.1) [1]. Công thức quy hoạch nguyên của họ (biểu thức (4), mục 3.2) nhận hệ số `c_ij` = trọng số cạnh trực tiếp.

(a) Thư viện **igraph** cài sẵn cả hai: `feedback_arc_set(graph, weights, algo = c("approx_eades","exact_ip"))`. Tài liệu chính thức nói `exact_ip` "solves the feedback arc set problem with an exact integer programming algorithm that guarantees that the total weight of the removed edges is as small as possible"; `approx_eades` là thuật toán xấp xỉ tuyến tính của Eades–Lin–Smyth [4].

(a) **NetworkX thì không có gì cả.** [tự đo] Rà toàn bộ không gian tên `networkx` 3.6.1 không có hàm nào cho feedback arc set: chỉ có `simple_cycles`, `condensation`, `transitive_reduction`, `is_directed_acyclic_graph`. Dự án dùng NetworkX sẽ buộc phải tự cài MFAS.

> **Với doc2roadmap:** điểm 2 phải đổi tên thành "MFAS có trọng số", định nghĩa trọng số tường minh, và dùng `igraph.feedback_arc_set(algo="exact_ip")` thay vì tự viết vét cạn. Trọng số nên là hàm đơn điệu của thứ tự ưu tiên giữ cạnh đã có (loại bằng chứng → thuận thứ tự → số nguồn → confidence), ví dụ trọng số theo cơ số đủ lớn để tiêu chí trước luôn trội tiêu chí sau — như vậy "tối thiểu tổng trọng số cạnh bị gỡ" tái hiện đúng thứ tự từ điển mà dự án muốn.

### 1.3 Chi phí thực tế của vét cạn — điểm chết của thiết kế hiện tại

(a) Ngay cả đồ thị thưa cũng có thể có Ω(2ⁿ) chu trình đơn, và loại đồ thị đó xuất hiện trong thực tế (Baharev và cộng sự 2021, phần tóm tắt và mục 2) [1].

(b) Bảng 1 của [1] cho vài con số cụ thể đáng sợ: đồ thị đầy đủ **10 node / 90 cạnh** có **1.112.073 chu trình đơn**; đồ thị **109 node / 163 cạnh** có 13.746 chu trình; đồ thị 2700 node / 3419 cạnh có **hơn 10⁷** chu trình (Johnson's algorithm bỏ cuộc sau 10⁷+1).

(b) [tự đo] Tôi đo trực tiếp chi phí vét cạn — duyệt mọi tập con cạnh theo cỡ tăng dần cho tới khi đồ thị hết chu trình — trên các SCC ngẫu nhiên, ngân sách 10 giây mỗi ca (`bf2.py`):

| SCC: n node | m cạnh | #chu trình đơn | vét cạn xong trong 10s? |
|---|---|---|---|
| 5 | 8 | 4 | có (10 tập con) |
| 6 | 12 | 7 | có (152 tập con) |
| **7** | **21** | **44** | **KHÔNG** (bỏ cuộc sau 74.252 tập con) |
| 8 | 31 | 266 | không |
| 10 | 41 | 1.119 | không |
| 12 | 37 | 238 | không |

**Vét cạn chết ở SCC 7 node.** Không phải 50, không phải 20 — bảy.

> **Đính chính của reviewer (2026-09-21).** Kết luận trên đúng với *một* cách cài vét cạn, nhưng **không mô tả
> đúng mã của doc2roadmap**. `_feedback_edges(component, internal, *, exhaustive_limit=16)` chặn theo **số cạnh
> nội bộ**, không theo số node, nên số tập con bị chặn ở `2¹⁶ = 65 536` và vét cạn **không thể treo**. Đo trên máy
> dự án: SCC 5 node / 16 cạnh (gỡ 8) chạy `exhaustive` hết **216,9 ms**; SCC 5 node / 20 cạnh tự rơi sang
> `eades_priority` hết 0,2 ms.
>
> Vấn đề thật vẫn nghiêm trọng nhưng khác: **trên 16 cạnh, mã lặng lẽ chuyển sang nghiệm xấp xỉ, và D11 không hề
> nhắc tới nhánh đó.** Và cải tiến mà mục 1.3 đề xuất — liệt kê chu trình đơn rồi giải ILP — vẫn đúng và vẫn đáng
> làm, vì nó cho nghiệm **chính xác ở mọi cỡ** thay vì xấp xỉ. Xem Đ1 của bản tổng hợp.

(b) [tự đo] Trên dữ liệu thật thì tệ hơn. Đồ thị khái niệm LectureBank 2.0 (322 khái niệm, 1.551 cạnh tiên quyết) có **19 SCC không tầm thường**, lớn nhất là **27 node / 60 cạnh**. Vét cạn trên SCC đó phải duyệt 2⁶⁰ ≈ 1,15 × 10¹⁸ tập con — ở tốc độ 1 triệu phép kiểm tra phi chu trình mỗi giây là **khoảng 36.500 năm**.

(b) [tự đo] Nhưng chính SCC 27 node đó chỉ có **177 chu trình đơn**. Tức là công thức phủ tập hợp / quy hoạch nguyên của Baharev mục 3.2 chỉ cần 177 ràng buộc — giải trong mili giây, và giải **chính xác**.

(a) Đây đúng là điều Baharev và cộng sự khai thác: phương pháp của họ liệt kê chu trình đơn "in a lazy fashion", mở rộng dần ma trận chu trình chưa đầy đủ, và trên 11/12 đồ thị kiểm thử "the initial loop set was sufficient to prove that the solution found is optimal" — chỉ một chương trình nguyên phải giải, và nó được giải ngay ở pha presolve hoặc nút gốc (mục 5.1) [1].

**Suy luận:** khoảng cách giữa 2⁶⁰ và 177 là toàn bộ vấn đề. Số **chu trình** trong SCC tiên quyết thực tế nhỏ; số **tập con cạnh** thì không. Vét cạn tính sai đại lượng. Đổi sang liệt kê chu trình + phủ tập hợp ILP giữ nguyên tính chính xác (vẫn là nghiệm tối ưu, không phải heuristic) mà chạy được, nên đây không phải đánh đổi chất lượng học thuật lấy tốc độ — điều quan trọng với một dự án đặt chất lượng trên hạn chót.

(a) Baharev và cộng sự cũng nêu các bước đơn giản hoá nên làm **trước** khi gỡ cạnh: tách thành SCC, bỏ SCC tầm thường, "breaking two-cycles appropriately" (mục 2) [1]. Dự án đã làm bước tách SCC — đúng hướng.

> **Với doc2roadmap:** điểm 2 phải sửa. Thay vét cạn bằng: (i) tách SCC (giữ nguyên), (ii) liệt kê chu trình đơn trong SCC bằng Johnson, (iii) giải phủ tập hợp có trọng số bằng ILP, (iv) nếu số chu trình vượt ngân sách thì mở rộng ma trận chu trình kiểu lazy như [1], (v) chỉ khi vẫn không xong mới rơi về heuristic Eades–Lin–Smyth và **ghi nhận là nghiệm xấp xỉ**. Đặt ngân sách theo *số chu trình đơn*, không theo số node.

---

## 2. Cổng chất lượng 0,5 cạnh/node và 60% node cô lập

Đây là phần dự án nói rõ là không có nguồn. Tôi tìm được số thực nghiệm, và **cả hai hằng số đều sai hướng nguy hiểm**.

### 2.1 Mạng tiên quyết môn học thật

(a) Zuev & Stavrinides, *Breadth, depth, and flux of course-prerequisite networks* (2025, *Network Science*, Cambridge; bản arXiv 2506.23510) công bố mạng tiên quyết toàn trường của ba đại học kèm dữ liệu mở [5][6].

(b) Bảng I của [5]: số node n, số cạnh m **sau rút gọn bắc cầu**:

| Trường | n | m (sau TR) | cạnh/node |
|---|---|---|---|
| Cyprus University of Technology | 416 | 319 | **0,767** |
| Caltech (CIT) | 771 | 640 | **0,830** |
| Johns Hopkins (JHU) | 10.291 | 3.499 | **0,340** |

**JHU nằm DƯỚI ngưỡng 0,5 của dự án.** Một chương trình đào tạo thật, được biên tập tay, của đại học nghiên cứu lâu đời nhất nước Mỹ, sẽ bị cổng chất lượng A9 tuyên bố là "không có cấu trúc tiên quyết".

(b) [tự đo] Về node cô lập, tôi dựng lại từ dữ liệu gốc [6]:

- **Caltech**: 771 môn, 772 cạnh thô → **303 môn (39,3%) không có cạnh tiên quyết nào**, cả vào lẫn ra. Đồ thị là DAG, 0 chu trình. Sau rút gọn bắc cầu: 640 cạnh (khớp Bảng I).
- **JHU**: 10.087 môn trong danh mục; chỉ **2.261 môn (22,4%) có bất kỳ văn bản tiên quyết nào**. → **77,7% node cô lập.** (Kiểm tra độc lập từ Bảng I: với m = 3.499 cạnh, nhiều nhất 6.998 node được chạm, nên cô lập ≥ 3.293/10.291 = ≥ 32,0% — cận dưới chặt chẽ, và con số đo thực là 77,7%.)

**Cả hai cổng đều kích hoạt trên JHU: 0,34 < 0,5 và 77,7% > 60%.**

### 2.2 Đồ thị khái niệm (đúng mức chi tiết của doc2roadmap)

(b) [tự đo] và từ bài báo gốc:

| Bộ dữ liệu | #node | #cạnh | cạnh/node | % node cô lập | cạnh 2 chiều | nguồn |
|---|---|---|---|---|---|---|
| LectureBank 1.0 NLP | 208 | 921 | 4,43 | 7/208 = **3,4%** | 12 cặp | [7] mục Additional Annotation |
| LectureBank 2.0 NLP | 322 | 1.551 | 4,82 | 5 = **1,6%** | **30 cặp = 3,87% cạnh** | [8] [tự đo] |
| AL-CPL data mining | 120 | 292 | 2,43 | **25,0%** | 0 | [9] [tự đo] |
| AL-CPL geometry | 89 | 524 | 5,89 | **1,1%** | 0 | [9] [tự đo] |
| AL-CPL physics | 153 | 487 | 3,18 | **19,0%** | 0 | [9] [tự đo] |
| AL-CPL precalculus | 224 | 699 | 3,12 | **12,5%** | 0 | [9] [tự đo] |
| CPN Caltech (thô) | 771 | 772 | 1,00 | **39,3%** | 0 | [6] [tự đo] |
| CPN Caltech (sau TR) | 771 | 640 | 0,83 | 39,3% | 0 | [5] Bảng I |
| CPN CUT (sau TR) | 416 | 319 | 0,77 | không báo cáo | không báo cáo | [5] Bảng I |
| CPN JHU (sau TR) | 10.291 | 3.499 | **0,34** | **77,7%** | 0 | [5] Bảng I + [tự đo] |

(b) [tự đo] Một cảnh báo quan trọng về tính so sánh được: các bộ AL-CPL đã được **mở rộng bắc cầu** khi tiền xử lý, nên mật độ thô bị thổi phồng. Rút gọn bắc cầu loại bỏ **61,6% / 79,0% / 63,2% / 64,9%** số cạnh của bốn miền, còn lại **0,93–1,24 cạnh/node** — tức là cùng bậc độ lớn với mạng môn học, không phải 3–6 như con số thô gợi ý.

(a) Việc mở rộng bắc cầu này là do chính tác giả bộ dữ liệu làm: AL-CPL kiểm tra mọi quan hệ thoả tính chất thứ tự bộ phận chặt, thêm (B,A) làm mẫu âm khi (A,B) dương, và **thêm (A,C) làm mẫu dương khi có (A,B) và (B,C)** (README của [9]).

**Suy luận:** khoảng dao động là 0,34 đến 5,89 cạnh/node và 1,1% đến 77,7% node cô lập — **trên toàn bộ các đồ thị tiên quyết hợp lệ, đã công bố**. Không có hằng số đơn nào phân tách "có cấu trúc" khỏi "không có cấu trúc" qua dải đó. Hai đại lượng này đo **mức chi tiết của node và quy ước gán nhãn**, không đo chất lượng. Một danh mục toàn trường (node = môn học, thưa, nhiều môn độc lập) và một đồ thị khái niệm trong một giáo trình (node = khái niệm, dày, ít khái niệm trơ) nằm ở hai đầu dải — nhưng cả hai đều đúng.

(a) Tôi **không tìm thấy nguồn nào** trong văn liệu xây dựng đồ thị tri thức hay đồ thị tiên quyết dùng "ngưỡng mật độ để rơi về phương án dự phòng" như dự án đang làm. Các khảo sát chất lượng KG dùng các chiều accuracy, completeness, consistency, timeliness, trustworthiness, availability (Xue & Zou, 2022, *Knowledge graph quality management: a comprehensive survey*, IEEE TKDE) [10] và các chỉ số cấu trúc theo schema như Instantiated Class Ratio / Instantiated Property Ratio (Seo và cộng sự, 2022, *Structural Quality Metrics to Evaluate Knowledge Graphs*, arXiv:2211.10011) [11] — **không có chỉ số nào là ngưỡng mật độ kích hoạt fallback**. Câu "không tìm thấy nguồn" này có giá trị: nó nói rằng đây là chỗ dự án phải tự đo.

> **Với doc2roadmap:** điểm 4 bị bác bỏ bằng số thực nghiệm. Ngưỡng 0,5 cạnh/node loại nhầm JHU (0,34); ngưỡng 60% cô lập loại nhầm JHU (77,7%) và chỉ cách Caltech (39,3%) có 1,5 lần. Đề xuất cụ thể ở mục cuối.

---

## 3. Chu trình hai cạnh: con số 4% và khung lý thuyết đang thiếu

### 3.1 Con số ~4% là có thật — tôi xác minh được

(b) [tự đo] LectureBank 2.0 (322 khái niệm, 1.551 quan hệ tiên quyết dương, dựng lại từ kho dữ liệu chính thức [8]; số cạnh khớp đúng con số công bố 1.551): **30 cặp hai chiều A↔B, tức 60 cạnh = 3,87% tổng số cạnh.** Đây gần như chắc chắn là nguồn của con số "~4%" mà dự án đang dùng.

(b) Phiên bản trước, LectureBank 1.0: "We also observed some cycles between a pair of vertices within the concept graph. **We found 12 such pairs** in our labeled concept graph" trên đồ thị 208 node / 921 cạnh (Li và cộng sự, 2019, AAAI-19) [7]. Quy ra: 24/921 = 2,6% số cạnh.

**Vậy con số nền của dự án đứng vững.** Nhưng phần còn lại của câu chuyện thì không.

### 3.2 Chính tác giả bộ dữ liệu KHÔNG coi đó là quan hệ hợp lệ

(a) Trích nguyên văn Li và cộng sự (2019) [7]: các cặp hai chiều "consist of very closely related topics such as *Domain Adaptation* and *Transfer Learning* and *LDA* and *Topic Modeling*, suggesting that **in the future we may combine these pairs into a single concept**."

**Suy luận:** đây là phản chứng trực tiếp cho lý lẽ ở điểm 3. Dự án viện dẫn "một bộ dữ liệu có ~4% cạnh hai chiều mà tác giả coi là hợp lệ". Tác giả **không** coi là hợp lệ — họ coi là dấu hiệu hai nhãn đang mô tả **một** khái niệm và nói rõ định gộp lại. Giữ nguyên hai node rồi gắn cờ không phải điều họ khuyến nghị.

(a) Xu hướng chung còn ngược hơn: AL-CPL kiểm định mọi quan hệ theo tính chất **thứ tự bộ phận chặt** và nhờ chuyên gia sửa tay nhãn nào vi phạm; nếu (A,B) dương thì (B,A) được thêm làm **mẫu âm** [9]. [tự đo] xác nhận: cả bốn miền AL-CPL có **0 cặp hai chiều, 0 SCC không tầm thường, là DAG**. (a) Công cụ gán nhãn PRAT (Alzetta và cộng sự, 2025, *JASIST*) chặn hẳn ở mức giao diện "undesired relations such as self-prerequisites and cycles" [12].

### 3.3 Lý thuyết không gian tri thức: khung mà dự án đang thiếu

Đây là phần quan trọng nhất của khảo sát, vì nó cho A9 một nền lý thuyết thay vì một tập quy tắc rời rạc.

(a) Doignon & Falmagne, *Spaces for the assessment of knowledge* (1985, *International Journal of Man-Machine Studies* 23:175–196) khởi đầu Knowledge Space Theory; trình bày hiện đại ở Falmagne & Doignon, *Knowledge Spaces and Learning Spaces* (2015, arXiv:1511.06757; chương 5 của *New Handbook of Mathematical Psychology*, Cambridge) [13][14].

(a) Các định nghĩa hình thức, trích nguyên văn từ [13]:

- "a **quasi order** on Q is a reflexive and transitive relation on Q. A **partial order** on Q is a quasi order on Q which is an **antisymmetric** relation" (trước Định lý 10).
- **Quan hệ surmise (tiên quyết) chính là một quasi-order** — tức là **KHÔNG đòi hỏi phản đối xứng**.
- Một cấu trúc tri thức là **discriminative** khi "for any two items q and r in the domain, we have K_q = K_r only if q = r" (Định nghĩa 1).
- **Định lý 10 (Birkhoff, 1937)**: song ánh giữa các không gian tựa thứ tự trên Q và các quasi-order trên Q, cho bởi `qQr ⟺ K_q ⊇ K_r`. "Its restriction to **discriminative** spaces links partially ordinal spaces to **partial orders**."

**Suy luận — đây là điểm mấu chốt.** Ghép Định nghĩa 1 với công thức (4) của Định lý 10: nếu A→B và B→A cùng tồn tại thì K_A ⊇ K_B và K_B ⊇ K_A, nên K_A = K_B. Theo Định nghĩa 1, đó **chính xác là định nghĩa của việc cấu trúc mất tính discriminative**. Nói cách khác: **trong KST, một chu trình hai cạnh không phải một quan hệ — nó là một phát biểu rằng hai node là cùng một thứ.** Và điều này đúng cho **mọi SCC**, không riêng chu trình hai cạnh: do tính bắc cầu của quasi-order, mọi node trong một SCC đều tương đương đôi một.

(a) KST có sẵn tên gọi và thao tác chuẩn cho tình huống này. Gói R `kst` (Stahl & Hockemeyer, CRAN) — bản cài đặt tham chiếu của hình thức luận — định nghĩa: "**A notion is a set of items always jointly contained in all knowledge states. Consequently, these items carry the same information and may therefore be considered equivalent**", truy cập bằng hàm `knotions()`; và hàm `reduction(kst, operation="discrimination")` tính "**the discriminative reduction of a knowledge structure. Such a discriminative reduction is a knowledge structure in which each notion contains a single item**" [15].

Tức là: thao tác chuẩn của KST với một SCC là **gộp nó thành một node** — không cắt cạnh, cũng không giữ rồi gắn cờ.

(a) Còn với learning space — tiên đề hoá được ALEKS dùng — ràng buộc còn chặt hơn. Định nghĩa 3 của [13] nêu hai tiên đề: **[L1] Learning smoothness** và **[L2] Learning consistency**. Định lý 7 của [13]: "(i) (Q,K) is a learning space ⟺ (ii) antimatroid ⟺ (iii) **well-graded** knowledge space", trong đó well-graded (Định nghĩa 5) đòi hỏi giữa hai trạng thái bất kỳ tồn tại dãy trạng thái mà mỗi bước thay đổi **đúng một item**.

**Suy luận:** nếu A và B tương đương (tạo thành một notion), không có trạng thái tri thức nào chứa A mà không chứa B, nên không thể đi từ trạng thái này sang trạng thái kia bằng cách thêm từng item một. Vậy **một chu trình hai cạnh chưa gộp làm cấu trúc không còn well-graded, tức là không còn là learning space** — và learning space chính là thứ A10 cần để sinh lộ trình học từng bước. Giữ chu trình hai cạnh không chỉ là chọn lựa mô hình hoá; nó **phá vỡ điều kiện mà A10 dựa vào**.

(a) Mở rộng competence-based KST (CbKST — Heller, Steiner, Hockemeyer & Albert) tách hai tầng: tầng biểu hiện (bài tập) và tầng năng lực (kỹ năng), nối bằng skill function và problem function [16]. **Suy luận:** liên quan tới doc2roadmap ở chỗ nó hợp thức hoá cờ `learnable` ở điểm 1 — đó chính là việc phân biệt node ở tầng năng lực (học được, vào lộ trình) với node chỉ là thuật ngữ. Điểm 1 có nền lý thuyết, chỉ là dự án chưa gọi tên nó.

> **Với doc2roadmap:** điểm 3 phải sửa — nhưng theo hướng **nhẹ nhàng hơn** so với cắt cạnh. Thay "giữ và gắn cờ" bằng "gộp thành một notion": thay A và B bằng một node hợp nhất mang cả hai nhãn, chuyển hết cạnh vào/ra sang node đó. Việc này (i) đúng khung KST, (ii) đúng điều tác giả LectureBank khuyến nghị, (iii) giữ được tính well-graded cho A10, (iv) **tự động làm biến mất chu trình mà không mất thông tin nào** — khác hẳn cắt cạnh. Giữ lại `merged_from` để người duyệt tách ra được. Quan trọng: áp dụng cho **mọi SCC**, không riêng chu trình hai cạnh — SCC 27 node trong LectureBank 2.0 theo KST là 27 nhãn của cùng một notion (thực tế hơn: là dấu hiệu gán nhãn lỗi cần người xem), chứ không phải một bài toán MFAS.

---

## 4. Rút gọn bắc cầu: đánh dấu thay vì xoá

### 4.1 Cơ sở

(a) Aho, Garey & Ullman, *The Transitive Reduction of a Directed Graph* (1972, *SIAM Journal on Computing* 1(2):131–137, DOI 10.1137/0201008) đặt nền: rút gọn bắc cầu của G là đồ thị ít cạnh nhất có cùng quan hệ khả đạt; độ phức tạp tương đương nhân ma trận Boolean / bao đóng bắc cầu [17].

(a) Rút gọn bắc cầu **chỉ xác định duy nhất trên DAG**. NetworkX thi hành điều này ở mức mã: `transitive_reduction` ném `NetworkXError` với thông điệp "Directed Acyclic Graph required for transitive_reduction" nếu đầu vào có chu trình [18] — [tự đo] xác nhận trong docstring của `networkx` 3.6.1: "If G is not a directed acyclic graph (DAG) transitive reduction is not uniquely defined and a NetworkXError exception is raised."

**Suy luận:** ràng buộc thứ tự cho A9: bước gỡ chu trình (hoặc gộp notion) **phải** chạy xong trước bước đánh dấu bắc cầu. Nếu điểm 3 giữ lại chu trình hai cạnh mà điểm 5 lại cần DAG, thì hai điểm thiết kế **mâu thuẫn nhau** trên chính những đồ thị có chu trình. Đây là một lỗi phải sửa, và việc gộp notion ở mục 3 xử lý luôn nó.

### 4.2 Tác hại định lượng của một cạnh sai — tôi đo được

(b) [tự đo] Thí nghiệm (`tr_noise.py`, `tr_noise2.py`): lấy đồ thị tiên quyết thật, thêm **đúng một** cạnh sai ngẫu nhiên (giữ tính phi chu trình), rồi đếm xem rút gọn bắc cầu làm **mất bao nhiêu cạnh đúng** so với khi không có cạnh sai. 300–400 lần thử mỗi bộ:

| Đồ thị | cạnh/node | % lần mất cạnh đúng | TB khi mất | **tệ nhất** |
|---|---|---|---|---|
| CPN Caltech | 1,00 | 4,5% | 1,22 | 5 cạnh |
| AL-CPL data mining | 2,43 | 12,0% | 1,78 | 8 cạnh |
| AL-CPL precalculus | 3,12 | 16,3% | 1,16 | 3 cạnh |
| AL-CPL physics | 3,18 | 13,7% | 1,54 | 5 cạnh |
| **LectureBank 2.0** | **4,71** | **37,7%** | **3,81** | **25 cạnh** |
| AL-CPL geometry | 5,89 | 30,7% | 1,32 | 4 cạnh |

**Tác hại tăng theo mật độ.** Ở chế độ mật độ của đồ thị khái niệm sinh từ giáo trình (4–5 cạnh/node), **cứ ~3 cạnh sai thì hơn 1 cạnh làm biến mất cạnh đúng, trung bình gần 4 cạnh, và có trường hợp một cạnh sai xoá sạch 25 cạnh đúng.**

Đây chính xác là kịch bản mà lý lẽ của điểm 5 nêu ra, giờ đã có số.

### 4.3 Một cơ chế thiên lệch mà dự án chưa biết

(a) Clough, Gollings, Loach & Evans, *Transitive Reduction of Citation Networks* (2015, *Journal of Complex Networks* 3(2):189–203; arXiv:1310.8224) [19].

(b) Bảng 1 của [19]: arXiv hep-th N=27.383, E=351.237 → 62.257 sau rút gọn (**xoá 82,3%**); US Supreme Court N=25.376, E=216.198 → 59.032 (**xoá 72,7%**); US patents N=3.764.094, E=16.510.997 → 13.996.169 (**xoá 15,2%**). Một bài cụ thể (hep-th/9802109) mất **99,8%** số trích dẫn sau rút gọn; một bài khác mất 90,5% (mục 3).

(b) Và phát hiện quan trọng nhất, mục về mô hình null của [19] (sau khi xáo trộn ngẫu nhiên 10 triệu lần mạng hep-th): "**randomly rewired edges are less likely to be implied by transitivity than those edges representing true citation behaviour**."

**Suy luận:** đọc ngược lại, câu đó nói rút gọn bắc cầu **thiên lệch có hệ thống**: nó ưu tiên **xoá cạnh thật** và ưu tiên **giữ cạnh nhiễu**. Nếu A9 xoá cạnh thừa, thì đúng những cạnh LLM bịa ra — không được bắc cầu hàm ý, vì chúng không nằm trong cấu trúc thật — sẽ **sống sót**, còn cạnh đúng bị dọn đi. Kết quả là một đồ thị bị làm giàu nhiễu. Đây là một lý lẽ ủng hộ điểm 5 **mạnh hơn** lý lẽ dự án đang dùng (lý lẽ của dự án là về quy trình duyệt; lý lẽ này là về thống kê của chính phép toán) và nên được viết vào đặc tả.

> **Với doc2roadmap:** điểm 5 **được xác nhận mạnh**, cả định lượng (25 cạnh đúng mất vì 1 cạnh sai) lẫn cơ chế (rút gọn bắc cầu làm giàu nhiễu). Giữ nguyên `redundant_via`. Thêm hai việc: (i) ghi cơ chế thiên lệch của [19] vào phần biện minh; (ii) đảm bảo thứ tự gộp-notion → rồi mới đánh dấu bắc cầu, vì rút gọn bắc cầu không xác định trên đồ thị có chu trình.

---

## 5. Kiểm định bằng dữ liệu học viên — và phương án khi không có

Dự án **không có** dữ liệu học viên. Phần này khảo sát xem mất gì, và còn dùng được gì.

(a) **Vuong, Nixon & Towle (2011)**, *A Method for Finding Prerequisites Within a Curriculum*, EDM 2011 [20]. Phương pháp: với mỗi cặp phụ thuộc khả dĩ, **so sánh kết quả học của học viên đã học đơn vị tiên quyết tiềm năng với học viên chưa học**. Dữ liệu: mẫu ngẫu nhiên 1/5 số trường dùng Carnegie Learning Cognitive Tutor năm học 2008–2009 — tác giả nêu quy mô "hàng trăm nghìn học viên tại hơn hai nghìn năm trăm trường", và nói rõ mẫu này "far exceeds" quy mô các nghiên cứu trước, vốn gặp "problems relate to having small sample sizes".

(a) **Scheines, Silver & Goldin (2014)**, *Discovering Prerequisite Relationships among Knowledge Components*, EDM 2014, tr. 355–356 [21]. Coi các knowledge component là **biến ẩn** và dùng **thuật toán khám phá cấu trúc nhân quả**: trực giác là nếu học viên biết tiên quyết A cho kỹ năng B thì A giúp học B, và quan hệ tiên quyết với quan hệ nhân quả sinh ra **cùng kiểu độc lập có điều kiện** trong dữ liệu. Ca nghiên cứu: một bài kiểm tra cho **khoảng 120 học viên** trong một khoá toán bổ túc, đo tại **một thời điểm duy nhất**.

(a) **Brunskill (2011)**, *Estimating Prerequisite Structure From Noisy Data*, EDM 2011: tính log-likelihood của mô hình "có điều kiện tiên quyết" so với mô hình "phẳng" (các kỹ năng độc lập) trên từng cặp kỹ năng, chọn mô hình khớp dữ liệu học viên hơn [22].

(a) **Desmarais và cộng sự — POKS (Partial Order Knowledge Structures)**: học cấu trúc tri thức item-to-item **chỉ từ các node quan sát được** (đáp án bài kiểm tra), dùng khung naive Bayes và **kiểm định thống kê để suy ra thứ tự học**; tác giả nêu POKS vượt các thuật toán học cấu trúc mạng Bayes cổ điển cả về độ chính xác dự báo lẫn hiệu quả tính toán, và nói rõ nền tảng của nó là lý thuyết không gian tri thức (Desmarais, Meshkinfam & Gagnon, 2006, *User Modeling and User-Adapted Interaction* 16:403–434) [23].

(a) **Käser, Klingler, Schwing & Gross (2017)**, *Dynamic Bayesian Networks for Student Modeling*, *IEEE Transactions on Learning Technologies* 10(4) [24]: nêu rằng cấu trúc của Bayesian Knowledge Tracing "makes it impossible to represent the hierarchy and relationships between different skills", và dùng DBN để biểu diễn nhiều kỹ năng trong một mô hình, với thuật toán tối ưu có ràng buộc để học tham số.

**Suy luận:** cả năm dòng đều cần dữ liệu biểu hiện của học viên; **không dòng nào chuyển được sang doc2roadmap**. Nhưng chúng cho hai thứ dùng được ngay:

1. **Một giới hạn phải công bố.** Cả năm công trình đều coi "kiểm định" nghĩa là kiểm định *tiên đoán* trên hành vi học viên. A9 không làm điều đó và **không được dùng từ "kiểm định" (validation) mà không kèm định tính**. Cái A9 làm là **kiểm tra tính nhất quán cấu trúc** (consistency checking) — một khái niệm hẹp hơn hẳn. Đây là chuyện dùng từ trong bài báo, và với một dự án đặt chất lượng học thuật lên trước thì nó quan trọng.
2. **Một đường nâng cấp.** Scheines và cộng sự làm được với ~120 học viên tại một thời điểm [21] — ngưỡng thấp hơn nhiều so với Vuong. Nếu sau này có dù chỉ một đợt kiểm tra nhỏ, khung của [21] là con đường rẻ nhất để có kiểm định thật.

(a) Không có dữ liệu học viên, thứ thay thế khả dĩ duy nhất mà văn liệu ủng hộ là **thoả thuận giữa người gán nhãn**. LectureBank báo cáo **Cohen's kappa = 0,7** với hai nghiên cứu sinh gán nhãn nhị phân, và nói rõ họ chọn nhị phân vì bản ba mức trước đó (Fabbri và cộng sự 2018, TutorialBank) chỉ đạt **kappa = 0,3** trên **cùng các cặp khái niệm** [7].

**Suy luận:** kappa 0,3 → 0,7 chỉ do đổi nhị phân/ba mức và làm rõ tiêu chí, trên cùng dữ liệu. Đây là số đối chứng tốt cho bộ vàng PREAP của dự án: nếu kappa của hai người gán nhãn thấp hơn ~0,7 thì vấn đề nhiều khả năng nằm ở định nghĩa nhiệm vụ chứ không ở người gán. Và nó cảnh báo: "long dependencies" (A tiên quyết B, B tiên quyết C — có tính A tiên quyết C không?) là nguồn bất đồng đã được xác định tên, nên giao thức PREAP phải trả lời dứt khoát câu đó.

> **Với doc2roadmap:** điểm 1 không bị phản bác. Nhưng phải đổi cách gọi A9 từ "kiểm định" sang "kiểm tra nhất quán cấu trúc", và ghi rõ giới hạn "không có dữ liệu học viên" như một giới hạn đã biết của văn liệu, kèm [20][21][22][23][24].

---

## 6. Hiệu chỉnh độ tin cậy của LLM

Điều này quyết định xem confidence LLM tự khai có đáng làm tiêu chí gỡ cạnh không. Dự án đã cố ý xếp nó cuối — khảo sát **xác nhận mạnh** lựa chọn đó.

(a) Xiong và cộng sự, *Can LLMs Express Their Uncertainty? An Empirical Evaluation of Confidence Elicitation in LLMs* (ICLR 2024, arXiv:2306.13063) [25]. Đánh giá 5 mô hình × 8 bộ dữ liệu.

(b) Bảng 2 của [25], confidence tự khai dạng thuần (vanilla verbalized), trung bình trên 8 bộ dữ liệu (đơn vị ×10⁻²):

| Mô hình | ECE ↓ | AUROC ↑ |
|---|---|---|
| GPT-3 | 52,0 | **51,3** |
| Vicuna 13B | 46,1 | **52,5** |
| LLaMA-2 70B | 43,6 | 56,4 |
| GPT-3.5 | 37,7 | 55,1 |
| GPT-4 | 18,0 | 62,7 |

**AUROC ≈ 50 nghĩa là tung đồng xu.** Với ba mô hình đầu, confidence tự khai **không phân biệt nổi câu trả lời đúng với câu trả lời sai**. Ngay cả GPT-4 cũng chỉ 62,7.

(b) Mục 5.1 và Hình 2 của [25]: "the confidence levels primarily range between 80% and 100%, often in multiples of 5; the accuracy within each bin is much lower than its corresponding confidence, indicating **significant overconfidence**". Tác giả cho rằng mô hình đang **bắt chước cách con người nói về độ tự tin** trong dữ liệu huấn luyện, chứ không báo cáo trạng thái nội tại.

(a) Phát hiện này lặp lại rộng rãi: Groot & Valdenegro-Toro, *Overconfidence is Key: Verbalized Uncertainty Evaluation in Large Language and Vision-Language Models* (2024, arXiv:2405.02917) [26].

**Suy luận:** với `gemini-3.1-flash-lite` ở temperature 0, tình hình có phần tệ hơn các con số trên: (i) đây là hạng mô hình nhỏ/nhanh, mà [25] cho thấy hiệu chỉnh xấu đi khi năng lực giảm; (ii) temperature 0 làm **mất luôn** tín hiệu thay thế tốt nhất — self-consistency cần lấy mẫu nhiều lần. Dự án đang ở đúng góc tệ nhất của không gian thiết kế đối với confidence. Đây là lý do định lượng để giữ nguyên quyết định xếp confidence cuối bảng.

(a) Về các phương án thay thế, bằng chứng **không nhất quán** và tôi ghi rõ điều đó: một số nghiên cứu thấy self-consistency thắng confidence tự khai trên bài toán suy luận khó, số khác thấy ngược lại; tổng hợp gần đây cho rằng hai tín hiệu **bổ sung** cho nhau hơn là thay thế. Tôi **không tìm thấy nghiên cứu hiệu chỉnh nào chạy riêng trên bài toán suy quan hệ tiên quyết** — đây là khoảng trống, và là chỗ dự án phải tự đo.

(a) Có một hướng có đảm bảo hình thức: **conformal prediction** cho cạnh đồ thị. Zhao, Kang & Tong, *Conformalized Link Prediction on Graph Neural Networks* (KDD 2024, arXiv:2406.18763) đưa tiêu chuẩn bất biến hoán vị riêng cho bài toán dự báo liên kết, "guaranteeing precise coverage at test time" [27]; và có mở rộng cho knowledge graph embedding với đảm bảo theo từng vị từ (CondKGCP, arXiv:2505.16877) [28].

**Suy luận:** conformal prediction hợp với A9 hơn là hiệu chỉnh confidence, vì nó cho **tập cạnh kèm đảm bảo phủ** thay vì một điểm số cần tin tưởng. Cụ thể: dùng bộ vàng PREAP làm tập hiệu chuẩn, sinh tập dự đoán cạnh ở mức phủ 1−α, rồi cho A9 xử lý ba nhóm khác nhau (cạnh chắc chắn / cạnh biên cần người duyệt / cạnh loại). Đây là việc lớn hơn phạm vi A9 hiện tại nhưng là con đường đúng về mặt học thuật, và nó dùng được **đúng thứ dự án đã có** (bộ vàng), không cần dữ liệu học viên.

> **Với doc2roadmap:** điểm 2 phần "cố ý không dùng confidence làm tiêu chí đầu" được **xác nhận mạnh** bởi [25][26] — AUROC ≈ 0,5 nghĩa là dùng nó làm tiêu chí đầu sẽ gần như tung đồng xu. Nên đi xa hơn một bước: **bỏ hẳn** confidence khỏi thứ tự ưu tiên, thay bằng một tiêu chí quyết định được (ví dụ ID cạnh theo thứ tự từ điển) để phá hoà — như vậy kết quả tái lập được, còn confidence thì không đóng góp thông tin nào.

---

## 7. Chuẩn hoá sổ đăng ký kiểu quan hệ (điểm 6)

(a) Graphusion (Yang và cộng sự, 2024/2025, arXiv:2407.10794; bản RAG tại WWW 2025 Companion, DOI 10.1145/3701716.3717821) xây dựng KG khoa học zero-shot bằng LLM với một **mô-đun hợp nhất** thực hiện "entity merging, conflict resolution, and novel triplet discovery" ở góc nhìn toàn cục, thay vì chỉ trích xuất cục bộ từng câu/tài liệu [29].

**Suy luận:** đây là cùng một ý với điểm 6 và với pha hợp nhất thực thể của doc2roadmap, nên điểm 6 nằm trong thông lệ. Việc dự án **không** tự quy tên nghi đồng nghĩa về `requires` là thận trọng đúng: Graphusion coi hợp nhất thực thể và giải quyết xung đột là **bước riêng có kiểm soát**, không phải gộp ngầm. Tôi không tìm thấy nguồn nào phản bác điểm 6.

---

## Điểm phải sửa, xếp theo mức nặng

**1. (Nặng nhất) Vét cạn không mở rộng được — thay bằng ILP phủ chu trình.**
*Đang làm:* vét cạn chọn tập cạnh gỡ trong mỗi SCC, **và tự rơi sang heuristic Eades–Lin–Smyth khi SCC có hơn 16 cạnh nội bộ — nhánh này D11 không nhắc tới** *(bổ sung của reviewer sau khi đọc mã)*.
*Phản bác:* [tự đo] một cài đặt vét cạn không chặn sẽ vượt ngân sách 10 giây ngay ở **SCC 7 node / 21 cạnh**; SCC lớn nhất trong LectureBank 2.0 (27 node / 60 cạnh) cần ~2⁶⁰ ≈ 36.500 năm. Baharev và cộng sự 2021 [1] Bảng 1: đồ thị đầy đủ 10 node có 1.112.073 chu trình đơn. *(Reviewer đính chính: mã dự án **có** chặn ở 16 cạnh nên không treo — nhưng đúng vì thế mà nó im lặng trả nghiệm xấp xỉ, và một báo cáo khoa học viết "giải bằng vét cạn" sẽ sai.)*
*Đề xuất:* liệt kê chu trình đơn bằng Johnson → giải phủ tập hợp có trọng số bằng ILP (công thức (4), mục 3.2 của [1]); mở rộng ma trận chu trình kiểu lazy nếu quá ngân sách; chỉ rơi về Eades–Lin–Smyth [3] ở bước cuối và **ghi nhãn là nghiệm xấp xỉ**. [tự đo] SCC 27 node đó chỉ có **177 chu trình đơn** → ILP giải chính xác trong mili giây. Đặt ngân sách theo *số chu trình*, không theo số node. Cân nhắc `igraph.feedback_arc_set(algo="exact_ip")` [4] vì NetworkX không có hàm nào [tự đo].

**2. (Nặng) Hai hằng số cổng chất lượng loại nhầm chương trình học thật.**
*Đang làm:* fallback nếu cạnh/node < 0,5 **hoặc** > 60% node học được bị cô lập.
*Phản bác:* [5] Bảng I — JHU có **0,340 cạnh/node**, dưới ngưỡng 0,5. [tự đo] từ dữ liệu gốc [6] — JHU có **77,7% node cô lập** (10.087 môn, chỉ 2.261 có tiên quyết), trên ngưỡng 60%. **Cả hai cổng kích hoạt trên một chương trình đào tạo thật.** Caltech ở 39,3% cô lập, chỉ cách ngưỡng 1,5 lần. Dải hợp lệ đã quan sát: 0,34–5,89 cạnh/node và 1,1–77,7% cô lập.
*Đề xuất:* (i) bỏ ngưỡng tuyệt đối; (ii) chuẩn hoá theo mức chi tiết của node — tính cạnh/node **sau rút gọn bắc cầu** để so được giữa các bộ dữ liệu (AL-CPL rơi từ 2,43–5,89 xuống 0,93–1,24 sau rút gọn [tự đo]); (iii) nếu vẫn cần một cổng, hạ xuống **0,15 cạnh/node** (dưới JHU một khoảng an toàn) và **85% cô lập**, và coi đó là bắt lỗi pipeline chết chứ không phải phán xét chất lượng tài liệu; (iv) thay cổng nhị phân bằng **cảnh báo có ghi số đo** để người duyệt quyết. Ghi rõ trong bài: **không tìm thấy nguồn nào** dùng ngưỡng mật độ kích hoạt fallback trong văn liệu xây dựng KG [10][11] — đây là chỗ dự án phải tự đo trên chính corpus của mình.

**3. (Nặng) Chu trình hai cạnh: con số đúng, cách xử lý sai khung.**
*Đang làm:* giữ chu trình hai cạnh, chỉ gắn cờ; lý lẽ là "tác giả bộ dữ liệu coi ~4% cạnh hai chiều là hợp lệ".
*Phản bác:* con số **đúng** — [tự đo] LectureBank 2.0 có 30 cặp hai chiều = **3,87% số cạnh**. Nhưng tiền đề sai: Li và cộng sự 2019 [7] viết nguyên văn rằng các cặp đó "suggest... **we may combine these pairs into a single concept**" — tức coi là *một* khái niệm bị tách đôi, không phải quan hệ hợp lệ. AL-CPL cưỡng chế thứ tự bộ phận chặt và có **0 cặp hai chiều** [9][tự đo]. KST nói mạnh hơn: theo Định nghĩa 1 + Định lý 10 của [13], A↔B kéo theo K_A = K_B, **đúng định nghĩa mất tính discriminative**; gói tham chiếu `kst` gọi đó là một **notion** và thao tác chuẩn là **discriminative reduction** — gộp thành một item [15]. Và vì learning space ⟺ well-graded (Định lý 7 của [13]), notion chưa gộp **phá vỡ tính well-graded mà A10 cần** để sinh lộ trình từng bước.
*Đề xuất:* thay "giữ và gắn cờ" bằng **gộp thành một node** mang cả hai nhãn, giữ `merged_from` để tách lại được. Áp dụng cho **mọi SCC**, không riêng chu trình hai cạnh. Việc này xoá chu trình mà không mất thông tin, và làm nhẹ hẳn gánh nặng ở điểm sửa số 1.

**4. (Vừa) Mâu thuẫn thứ tự giữa điểm 3 và điểm 5.**
*Đang làm:* giữ chu trình hai cạnh (điểm 3) rồi đánh dấu cạnh bắc cầu (điểm 5).
*Phản bác:* rút gọn bắc cầu **không xác định duy nhất** trên đồ thị có chu trình; NetworkX ném `NetworkXError` [18][tự đo]; Aho, Garey & Ullman 1972 [17] định nghĩa nó trên quan hệ khả đạt.
*Đề xuất:* cố định thứ tự trong đặc tả: gộp notion / gỡ chu trình **trước**, đánh dấu bắc cầu **sau**. Điểm sửa số 3 xử lý luôn chuyện này.

**5. (Vừa) Bỏ hẳn confidence khỏi thứ tự ưu tiên, không chỉ xếp cuối.**
*Đang làm:* confidence LLM tự khai là tiêu chí thứ tư trong thứ tự giữ cạnh.
*Phản bác:* [25] Bảng 2 — AUROC trung bình của confidence tự khai là **51,3 / 52,5 / 56,4 / 55,1 / 62,7** trên năm mô hình; ba mô hình đầu **không phân biệt được đúng/sai**. Mục 5.1 của [25]: giá trị dồn vào dải 80–100%, quá tự tin có hệ thống. Hiệu chỉnh xấu đi khi mô hình yếu đi — mà dự án dùng `flash-lite`. Temperature 0 làm mất luôn self-consistency, tín hiệu thay thế.
*Đề xuất:* bỏ confidence khỏi thứ tự ưu tiên; thay tiêu chí phá hoà cuối cùng bằng thứ tự từ điển của ID cạnh để kết quả **tái lập được**. Ghi trong bài rằng lựa chọn này có [25][26] chống lưng. Hướng dài hạn: conformal prediction trên cạnh [27][28] dùng bộ vàng PREAP làm tập hiệu chuẩn — có đảm bảo phủ hình thức và **không cần dữ liệu học viên**.

**6. (Vừa, nhưng dễ) Củng cố điểm 5 bằng lý lẽ mạnh hơn lý lẽ đang dùng.**
*Đang làm:* chỉ đánh dấu `redundant_via`, lý lẽ dựa trên quy trình duyệt.
*Xác nhận:* [tự đo] trên LectureBank 2.0 (4,71 cạnh/node), **một** cạnh sai làm mất cạnh đúng trong **37,7%** số lần, trung bình 3,81 cạnh, **tệ nhất 25 cạnh**. Tác hại tăng đơn điệu theo mật độ (Caltech 1,00 cạnh/node → chỉ 4,5%).
*Đề xuất:* giữ nguyên quyết định; bổ sung vào phần biện minh phát hiện của Clough và cộng sự 2015 [19] rằng "randomly rewired edges are less likely to be implied by transitivity than those edges representing true citation behaviour" — tức rút gọn bắc cầu **thiên lệch: ưu tiên xoá cạnh thật, ưu tiên giữ cạnh nhiễu**. Đây là lý lẽ thống kê về chính phép toán, mạnh hơn lý lẽ quy trình.

**7. (Nhẹ, nhưng bắt buộc cho bài báo) Đổi cách gọi A9.**
*Đang làm:* gọi A9 là "kiểm định đồ thị".
*Phản bác:* trong văn liệu, kiểm định quan hệ tiên quyết nghĩa là kiểm định trên **biểu hiện của học viên** — Vuong và cộng sự 2011 [20] (hàng trăm nghìn học viên), Scheines và cộng sự 2014 [21] (~120 học viên, khám phá cấu trúc nhân quả), Brunskill 2011 [22], POKS [23], Käser và cộng sự 2017 [24]. A9 không làm điều đó.
*Đề xuất:* gọi là **"kiểm tra tính nhất quán cấu trúc"**; nêu "không có dữ liệu học viên" là giới hạn đã biết kèm [20]–[24]; nêu [21] (~120 học viên, một thời điểm) là đường nâng cấp rẻ nhất nếu sau này có dữ liệu. Dùng kappa của hai người gán nhãn làm tín hiệu chất lượng thay thế, lấy **0,7** của LectureBank làm mốc đối chiếu, và lưu ý kappa nhảy từ 0,3 lên 0,7 chỉ nhờ đổi nhãn ba mức sang nhị phân và làm rõ tiêu chí [7] — nên PREAP phải trả lời dứt khoát câu "long dependencies" (A→B, B→C thì có tính A→C không).

---

## Khoảng trống: chỗ không có nguồn, dự án phải tự đo

Ghi lại tường minh vì mỗi dòng có giá trị bằng một nguồn:

1. **Không tìm thấy nguồn nào** dùng ngưỡng mật độ đồ thị để kích hoạt phương án dự phòng, trong văn liệu xây dựng/đánh giá KG [10][11] hay văn liệu quan hệ tiên quyết.
2. **Không tìm thấy nghiên cứu hiệu chỉnh độ tin cậy nào** chạy riêng trên bài toán suy quan hệ tiên quyết khái niệm; mọi số ở mục 6 đến từ QA/suy luận.
3. **Không tìm thấy bộ dữ liệu tiên quyết nào báo cáo tỉ lệ node cô lập** như một chỉ số chuẩn — mọi con số cô lập trong bảng mục 2.2 là do tôi tự tính từ dữ liệu gốc, trừ LectureBank 1.0 (7 node, có nêu trong [7]).
4. **Không tìm thấy công trình nào khuyến nghị tường minh "đánh dấu thay vì xoá" cạnh bắc cầu.** Lý lẽ ủng hộ điểm 5 là gián tiếp (thiên lệch nhiễu [19] + phép đo của tôi), không phải một khuyến nghị trực tiếp. Đây có thể là một đóng góp nhỏ nhưng thật của dự án — nên nói thẳng như vậy trong bài.

---

## Nguồn

1. Baharev, A., Schichl, H., Neumaier, A., & Achterberg, T. (2021). *An Exact Method for the Minimum Feedback Arc Set Problem*. ACM Journal of Experimental Algorithmics, 26, Article 1.4. https://dl.acm.org/doi/10.1145/3446429 — bản toàn văn dùng để trích: https://arnold-neumaier.at/ms/minimum_feedback_arc_set.pdf
2. Karp, R. M. (1972). *Reducibility Among Combinatorial Problems*. In Miller & Thatcher (eds.), Complexity of Computer Computations, Plenum Press, 85–103. (Dẫn qua [1] mục 1.1.)
3. Eades, P., Lin, X., & Smyth, W. F. (1993). *A fast and effective heuristic for the feedback arc set problem*. Information Processing Letters, 47(6), 319–323. https://www.sciencedirect.com/science/article/abs/pii/002001909390079O
4. igraph. *Finding a feedback arc set in a graph* — `feedback_arc_set`, thuật toán `exact_ip` và `approx_eades`. https://r.igraph.org/reference/feedback_arc_set.html
5. Zuev, K., & Stavrinides, P. (2025). *Breadth, depth, and flux of course-prerequisite networks*. Network Science (Cambridge University Press). arXiv:2506.23510. https://arxiv.org/pdf/2506.23510
6. Stavrinides, P. *Course-Prerequisite-Networks* (dữ liệu CPN của CUT, CIT, JHU). https://github.com/pstavrin/Course-Prerequisite-Networks
7. Li, I., Fabbri, A. R., Tung, R. R., & Radev, D. R. (2019). *What Should I Learn First: Introducing LectureBank for NLP Education and Prerequisite Chain Learning*. AAAI-19. arXiv:1811.12181. https://arxiv.org/pdf/1811.12181
8. Yale-LILY. *LectureBank* (dữ liệu LectureBank 1.0 / 2.0 / CD). https://github.com/Yale-LILY/LectureBank
9. Liang, C., Ye, J., Wang, S., Pursel, B., & Giles, C. L. (2018). *Investigating Active Learning for Concept Prerequisite Learning*. EAAI-18 / AAAI. Dữ liệu: https://github.com/harrylclc/AL-CPL-dataset ; bài: https://ojs.aaai.org/index.php/AAAI/article/download/11396/11255
10. Xue, B., & Zou, L. (2022). *Knowledge Graph Quality Management: A Comprehensive Survey*. IEEE Transactions on Knowledge and Data Engineering. https://www.semanticscholar.org/paper/ae5b587fb5ff55c074a770acf81c27d9d3046748
11. Seo, S., và cộng sự (2022). *Structural Quality Metrics to Evaluate Knowledge Graphs*. arXiv:2211.10011. https://arxiv.org/pdf/2211.10011
12. Alzetta, C., và cộng sự (2025). *Prerequisite Relations Annotation Tool: Annotation and analysis of educational relations in texts*. Journal of the Association for Information Science and Technology. https://asistdl.onlinelibrary.wiley.com/doi/10.1002/asi.24992
13. Falmagne, J.-C., & Doignon, J.-P. (2015). *Knowledge Spaces and Learning Spaces*. arXiv:1511.06757; chương 5 của New Handbook of Mathematical Psychology, Cambridge University Press. https://arxiv.org/pdf/1511.06757
14. Doignon, J.-P., & Falmagne, J.-C. (1985). *Spaces for the assessment of knowledge*. International Journal of Man-Machine Studies, 23, 175–196.
15. Stahl, C., & Hockemeyer, C. *kst: Knowledge Space Theory* (gói R; vignette). CRAN. https://cran.r-project.org/web/packages/kst/vignettes/kst.pdf
16. Heller, J., Steiner, C., Hockemeyer, C., & Albert, D. *Competence-Based Knowledge Structures for Personalised Learning*. (CbKST; xem cả gói CRAN `CbKST`: https://cran.r-project.org/web/packages/CbKST/index.html)
17. Aho, A. V., Garey, M. R., & Ullman, J. D. (1972). *The Transitive Reduction of a Directed Graph*. SIAM Journal on Computing, 1(2), 131–137. DOI 10.1137/0201008. https://epubs.siam.org/doi/10.1137/0201008
18. NetworkX. `transitive_reduction` — yêu cầu DAG. https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.dag.transitive_reduction.html
19. Clough, J. R., Gollings, J., Loach, T. V., & Evans, T. S. (2015). *Transitive reduction of citation networks*. Journal of Complex Networks, 3(2), 189–203. arXiv:1310.8224. https://arxiv.org/pdf/1310.8224
20. Vuong, A., Nixon, T., & Towle, B. (2011). *A Method for Finding Prerequisites Within a Curriculum*. EDM 2011. https://educationaldatamining.org/EDM2011/wp-content/uploads/proc/edm2011_paper8_short_Vuong.pdf
21. Scheines, R., Silver, E., & Goldin, I. (2014). *Discovering Prerequisite Relationships among Knowledge Components*. EDM 2014, 355–356. https://www.stat.cmu.edu/~brian/nynke/726-2021/week06/HCI%20prereq%20discovery/ScheinesSilverGoldin-EDM2014.pdf
22. Brunskill, E. (2011). *Estimating Prerequisite Structure From Noisy Data*. EDM 2011.
23. Desmarais, M. C., Meshkinfam, P., & Gagnon, M. (2006). *Learned Student Models with Item to Item Knowledge Structures* (POKS). User Modeling and User-Adapted Interaction, 16, 403–434. https://link.springer.com/article/10.1007/s11257-006-9016-3
24. Käser, T., Klingler, S., Schwing, A. G., & Gross, M. (2017). *Dynamic Bayesian Networks for Student Modeling*. IEEE Transactions on Learning Technologies, 10(4), 450–462. https://cgl.ethz.ch/Downloads/Publications/Papers/2017/Kae17a/Kae17a.pdf
25. Xiong, M., Hu, Z., Lu, X., Li, Y., Fu, J., He, J., & Hooi, B. (2024). *Can LLMs Express Their Uncertainty? An Empirical Evaluation of Confidence Elicitation in LLMs*. ICLR 2024. arXiv:2306.13063. https://arxiv.org/pdf/2306.13063
26. Groot, T., & Valdenegro-Toro, M. (2024). *Overconfidence is Key: Verbalized Uncertainty Evaluation in Large Language and Vision-Language Models*. arXiv:2405.02917. https://arxiv.org/pdf/2405.02917
27. Zhao, T., Kang, J., & Tong, H. (2024). *Conformalized Link Prediction on Graph Neural Networks*. KDD 2024. arXiv:2406.18763. https://dl.acm.org/doi/10.1145/3637528.3672061
28. *Predicate-Conditional Conformalized Answer Sets for Knowledge Graph Embeddings* (CondKGCP). arXiv:2505.16877. https://arxiv.org/html/2505.16877
29. Yang, R., và cộng sự (2024/2025). *Graphusion: Leveraging Large Language Models for Scientific Knowledge Graph Fusion and Construction in NLP Education*. arXiv:2407.10794; bản RAG tại WWW 2025 Companion, DOI 10.1145/3701716.3717821. https://arxiv.org/pdf/2407.10794

### Nguồn chỉ tiếp cận được ở mức tóm tắt

- [22] Brunskill (2011) — *(theo abstract và theo mô tả trong các công trình dẫn lại)*: so sánh log-likelihood giữa mô hình có điều kiện tiên quyết và mô hình phẳng trên từng cặp kỹ năng. Tôi không lấy được toàn văn EDM 2011.
- [16] CbKST — *(theo abstract và tài liệu gói CRAN)*: cấu trúc hai tầng biểu hiện/năng lực nối bằng skill function và problem function. Tôi không lấy được toàn văn chương sách.
- [10] Xue & Zou (2022) — *(theo abstract)*: các chiều chất lượng accuracy, completeness, consistency, timeliness, trustworthiness, availability. Bài sau tường lửa IEEE.
