# A10 — Sinh lộ trình học từ đồ thị tiên quyết: khảo sát văn liệu gốc

> **Ghi chú biên tập (reviewer, 2026-09-21).** Đây là **bản khảo sát văn liệu chi tiết** của vòng 36, giữ nguyên
> văn để tra cứu trích dẫn. Bản tổng hợp — có số đo trên artifact thật, có mô phỏng bốn cách gom stage, và có các
> đề xuất đánh số Đ1–Đ23 — nằm ở
> [`nghien-cuu-a9-a10-kiem-dinh-va-lo-trinh.md`](./nghien-cuu-a9-a10-kiem-dinh-va-lo-trinh.md); **đọc bản đó
> trước**, bản này là phụ lục.
>
> Hai chỗ reviewer đã kiểm lại và ghi vào bản tổng hợp thay vì sửa ở đây: (i) cận Lam & Sethi (1977) trong mục 1.3
> chỉ có **mô tả thứ cấp**, phải lấy toàn văn trước khi trích vào bài báo; (ii) khuyến nghị "phản bác điểm 2" của
> mục 1.3 được **số đo xác nhận** — bỏ phép giao cụm làm số stage của `xstk-ch3-1` tụt từ 63 xuống 19 mà τ không
> đổi. Xem mục 2.7 của bản tổng hợp.

Ngày khảo sát: 2026-09-21. Người khảo: trợ lý nghiên cứu `doc2roadmap`.
Quy ước trình bày: (a) sự thật từ nguồn ghi kèm tên công trình + năm + nơi công bố; (b) con số ghi rõ lấy ở bảng/mục nào, *(theo abstract)* nếu chỉ tiếp cận được tóm tắt; (c) ý kiến của người khảo mở đầu bằng **Suy luận:**.

---

## 0. Tóm tắt điều hành

Ba phát hiện nặng nhất:

1. **Bài toán A10 đang giải đã có tên, đã có thuật toán, và đã được chứng minh NP-khó từ 1975.** "Xếp tầng với trần W phần tử mỗi tầng, tối thiểu số tầng" chính là `P|prec, p_j=1|C_max` (lập lịch việc đơn vị thời gian, có ràng buộc thứ tự, trên W máy giống nhau). Thuật toán đúng cho bài này là **Coffman–Graham (1972)**, có cận đã chứng minh. Dự án đang tự chế cách cắt theo cụm chủ đề mà không hề gọi tên bài toán, và **không có bảo đảm gì về số tầng**.
2. **"Tầng 1 phình" (vấn đề số 7) là triệu chứng, không phải bệnh.** Với xếp tầng theo đường dài nhất, mọi node không có cạnh vào rơi hết vào tầng 1. Trong đồ thị tiên quyết do LLM suy, số node như vậy lớn chủ yếu vì **thiếu cạnh** (recall kém), chứ không vì đồ thị thực sự rộng. Không thuật toán xếp tầng nào chữa được thiếu cạnh. Bằng chứng: shared task PRELEARN@EVALITA 2020, F1 cross-domain tốt nhất chỉ **0.690** so với 0.887 in-domain.
3. **Chính hai tác giả sáng lập Knowledge Space Theory viết thẳng rằng mô hình "đồ thị tiên quyết = thứ tự bộ phận" là sai về mặt sư phạm.** Doignon & Falmagne (2015), sau Định lý 10 (Birkhoff 1937): *"Note in passing that the closure under intersection does not make good pedagogical sense."* Đồ thị tiên quyết tương ứng đúng với *quasi ordinal space* — trường hợp đặc biệt đóng dưới giao — mà họ bác bỏ.

---

## 1. Xếp tầng (layer assignment) trong vẽ đồ thị

### 1.1 Khung Sugiyama và vị trí của A10 trong đó

Sugiyama, Tagawa & Toda (1981), *Methods for Visual Understanding of Hierarchical System Structures*, IEEE Transactions on Systems, Man and Cybernetics 11(2):109–125 — đặt ra khung bốn pha cho vẽ đồ thị phân tầng: (1) phá chu trình, (2) gán tầng, (3) giảm giao cắt trong tầng, (4) gán toạ độ. *(tiếp cận qua mô tả trong Mallach 2019 §1 và Rüegg et al. 2016 §2; không đọc được toàn văn bản gốc 1981)*.

**Với doc2roadmap:** A10 điểm 1 (xếp tầng Kahn) đúng là pha 2 của Sugiyama; A10 điểm 5 (LLM sắp thứ tự trong stage) đúng là pha 3. Dự án đang tái phát minh khung Sugiyama trên đồ thị tiên quyết. Đây không phải lỗi — nhưng nghĩa là mọi kết quả của pha 2 trong 45 năm văn liệu đều áp dụng được, và cần được trích dẫn thay vì tự chế.

### 1.2 Xếp tầng theo đường dài nhất: tối thiểu số tầng, nhưng không kiểm soát được độ rộng

Rüegg, Ehlers, Spönemann & von Hanxleden (2016), *A Generalization of the Directed Graph Layering Problem*, GD'16, LNCS; bản arXiv:1608.07809, §2:

> "Eades and Sugiyama employ a longest path layering, which requires linear time, and the resulting number of layers equals the number of nodes of the graph's longest path"

và, quan trọng cho A10:

> "All of the previously mentioned layering methods have two major drawbacks. 1) They require the input graph to be acyclic upfront, and 2) they are bound to a minimum number of layers equal to the longest path of the graph. In particular this means that the bound on the number of layers in the methods of Nikolov et al. cannot be smaller than the longest path."

Đây là **định lý Mirsky** phát biểu lại: số tầng ít nhất bằng độ dài xích dài nhất. Xếp tầng theo đường dài nhất đạt đúng cận đó, nên nó **tối ưu về chiều cao** và **hoàn toàn không ràng buộc chiều rộng**.

Mã nguồn thật: NetworkX `networkx/algorithms/dag.py`, hàm `topological_generations` (bản `main`, tải 2026-09-21). Docstring:

> "Nodes are guaranteed to be in the earliest possible generation that they can belong to."

Thân hàm là bóc lớp Kahn thuần: `zero_indegree` → `this_generation` → giảm `indegree_map` → lớp kế. Không có tham số trần độ rộng nào. Cùng file có `antichain_width(G)` trả về độ rộng của thứ tự bộ phận (kích thước phản-xích lớn nhất) qua ghép cặp cực đại trên bao đóng bắc cầu — tức NetworkX *biết* khái niệm độ rộng nhưng không dùng nó để xếp tầng.

**Với doc2roadmap:** xác nhận điểm 1. Kahn + đường dài nhất trên đồ thị co đúng là `topological_generations` của NetworkX. Nhưng xác nhận luôn rằng thuật toán này **theo thiết kế** không kiểm soát được số phần tử mỗi tầng — nên vấn đề số 7 là hệ quả tất yếu, không phải bug.

### 1.3 Coffman–Graham: thuật toán đúng cho bài "trần 5–8 phần tử mỗi tầng"

Coffman, E.G. Jr. & Graham, R.L. (1972), *Optimal scheduling for two-processor systems*, Acta Informatica 1:200–213 — thuật toán gốc, tối ưu cho hai bộ xử lý *(theo abstract)*.

Trong vẽ đồ thị, thuật toán này được dùng đúng vào bài của dự án: gán node vào các tầng với **trần số node mỗi tầng cho trước**, đồng thời xấp xỉ tối thiểu số tầng.

Cận đã chứng minh:
- Lam, S. & Sethi, R. (1977), *Worst case analysis of two scheduling algorithms*, SIAM Journal on Computing 6(3):518–536: `l ≤ (2 − 2/W) · l_opt`, với `l_opt` là chiều cao nhỏ nhất trong mọi xếp tầng có độ rộng ≤ W *(theo mô tả thứ cấp trong kết quả tìm kiếm; không tiếp cận được toàn văn — cần kiểm lại nếu đưa vào bài báo)*.
- Braschi, B. & Trystram, D. (1994), *A New Insight into the Coffman–Graham Algorithm*, SIAM Journal on Computing 23(3):662–669: **phân tích của Lam–Sethi bị chỉ ra là sai một phần**; họ sửa và siết cận thành `≤ (2 − 2/m)·ω_opt − (m−3)/m` *(theo abstract)*.
- Coffman–Graham là **chính xác** khi W ≤ 2.

Mã nguồn thật: OGDF (Open Graph Drawing Framework), `include/ogdf/layered/CoffmanGrahamRanking.h` (nhánh `master`, tải 2026-09-21):

```cpp
//! The coffman graham ranking algorithm.
/**
 * The class CoffmanGrahamRanking implements a node ranking algorithmn based on
 * the coffman graham scheduling algorithm, which can be used as first phase
 * in SugiyamaLayout. The aim of the algorithm is to ensure that the height of
 * the ranking (the number of layers) is kept small.
 */
...
	//! Get for the with
	int width() const { return m_w; }
	//! Set for the with
	void width(int w) { m_w = w; }
```

Tức có sẵn một thư viện vẽ đồ thị công nghiệp, mã nguồn mở, cài đặt đúng "xếp tầng với trần W" — chỉ cần `setWidth(8)`.

**Số tầng bị trần ép lên bao nhiêu?** Với trần W, mọi xếp tầng hợp lệ đều phải có số tầng ≥ max(độ dài xích dài nhất, ⌈n/W⌉). Coffman–Graham bảo đảm không vượt quá (2 − 2/W) lần tối ưu: với W=5 là 1.6×, với W=8 là 1.75×.

**Suy luận:** cận dưới ⌈n/W⌉ là điều dự án chưa tính tới và nó rất nghiêm khắc. Một giáo trình với 300 khái niệm `learnable` và trần 8 sẽ cho **ít nhất 38 stage**, bất kể đồ thị nông đến đâu. Nếu A10 hiện cho ra ít hơn thế thì hoặc trần đang bị vi phạm, hoặc số khái niệm thực nhỏ hơn nhiều so với kỳ vọng. Đây là một bất biến kiểm thử được ngay, rẻ, và nên thành một assertion trong A10.

**Với doc2roadmap:** **phản bác điểm 2.** Cắt tầng theo cụm chủ đề không phải là thuật toán giải bài "trần 5–8", nó chỉ là một heuristic phân hoạch không có bảo đảm nào — tầng có thể vẫn vượt trần nếu một cụm chiếm hơn 8 khái niệm trong cùng một tầng, và số stage sinh ra không có cận so với tối ưu. Coffman–Graham giải đúng bài đó, có cận, và có cài đặt sẵn.

### 1.4 Network simplex của Graphviz: tối thiểu tổng độ dài cạnh, KHÔNG có ràng buộc độ rộng

Gansner, Koutsofios, North & Vo (1993), *A Technique for Drawing Directed Graphs*, IEEE Transactions on Software Engineering 19(3):214–230. Đọc toàn văn tại https://www.graphviz.org/documentation/TSE93.pdf.

§2.2 "Problem Definition" nêu đúng hàm mục tiêu:

> "So it is desirable to find an optimal node ranking, i.e., one for which the sum of all the weighted edge lengths is minimal.
> min Σ_(v,w)∈E ω(v,w)(λ(w) − λ(v))
> subject to: λ(w) − λ(v) ≥ δ(v,w) ∀(v,w) ∈ E"

**Không có ràng buộc nào về số node mỗi rank trong quy hoạch nguyên này.** Thứ duy nhất chạm tới độ rộng là bước 8 của thủ tục `rank()` ở Hình 2-1, tên là `balance()`, mô tả ở §2.3:

> "Nodes having equal in- and out-edge weights and multiple feasible ranks are moved to a feasible rank with the fewest nodes. The purpose is to reduce crowding and improve the aspect ratio of the drawing, following principle A4. The adjustment does not change the cost of the rank assignment. Nodes are adjusted in a greedy fashion, which works sufficiently well."

Mã nguồn thật khớp với bài báo: Graphviz `lib/common/ns.c`, hàm `TB_balance()`, dòng 681, comment:

```c
    /* find nodes that are not tight and move to less populated ranks */
```

**Với doc2roadmap:** đây là **cách chữa "tầng 1 phình" rẻ nhất mà dự án chưa làm**: với mỗi node có nhiều tầng khả thi (slack > 0), đẩy nó sang tầng ít node hơn. Không đổi tính hợp lệ của thứ tự tiên quyết, không đổi chi phí, chạy tuyến tính. Đây là heuristic chứ không phải thuật toán có bảo đảm — nhưng nó là tiêu chuẩn công nghiệp, đã ở trong Graphviz 33 năm, và giải đúng triệu chứng mà dự án đang than phiền.

### 1.5 Tối thiểu độ rộng: NP-khó, và các heuristic

- Healy, P. & Nikolov, N.S. (2001/2002), *How to Layer a Directed Acyclic Graph*, GD'01, LNCS 2265, Springer. Đặt bài toán gán tầng có **cận trên cho cả độ rộng lẫn chiều cao**, giải bằng ILP. *(chỉ tiếp cận được abstract và mô tả trong Rüegg et al. 2016 §2 — Springer chặn tải)*. Rüegg et al. tóm tắt: *"The problem is NP-hard, even without considering dummy nodes."*
- Healy & Nikolov (2002), *A Branch-and-Cut Approach to the Directed Acyclic Graph Layering Problem*, GD'02, LNCS 2528:98–109 *(theo abstract)*.
- Nikolov, N.S., Tarassov, A. & Branke, J. (2005), *In search for efficient heuristics for minimum-width graph layering with consideration of dummy nodes*, ACM Journal of Experimental Algorithmics 10, DOI 10.1145/1064546.1180618. Đề xuất hai heuristic **MinWidth** và **StretchWidth** *(theo abstract)*.
- Nikolov, N.S. & Tarassov, A. (2006), *Graph layering by promotion of nodes*, Discrete Applied Mathematics 154(5):848–860. Heuristic **Promote Layering (PL)**: chạy sau xếp tầng đường dài nhất, liên tục "thăng cấp" node lên tầng trên nếu việc đó giảm số dummy node *(theo abstract)*.

**Với doc2roadmap:** xác nhận rằng bài "tối thiểu độ rộng" khó, và rằng cách tiếp cận thực dụng trong văn liệu là **hậu xử lý xếp tầng đường dài nhất** (promotion / balance) chứ không phải phân hoạch lại theo cụm ngữ nghĩa. Dự án nên coi cụm chủ đề là tiêu chí *phụ* để tách stage, không phải cơ chế *chính* để ép trần.

---

## 2. Lập lịch có ràng buộc thứ tự — tương đương có thật

### 2.1 Tương đương được phát biểu tường minh

Mallach, S. (2019), *A Natural Quadratic Approach to the Generalized Graph Layering Problem*, GD 2019; bản arXiv:1908.04104, §2, sau khi định nghĩa Problem 3 (Minimum Width Directed Layering Problem, DLP-W):

> "Here, it should be mentioned that DLP-W is equivalent to the precedence-constrained multiprocessor scheduling problem (when ignoring dummy vertices), and thus as well NP-hard [10]."

với [10] = Ullman (1975).

**Tương đương ấy đúng.** Ánh xạ: khái niệm ↔ việc dài 1 đơn vị; cạnh `requires` ↔ ràng buộc thứ tự; trần W khái niệm/tầng ↔ W máy; số tầng ↔ makespan `C_max`.

### 2.2 Độ khó và ngưỡng xấp xỉ

Nguồn: Lawler, Lenstra, Rinnooy Kan, Shmoys và cộng sự, *Elements of Scheduling* (bản 2020, arXiv:2001.06005) — sách giáo khoa do chính những người dựng ra ngành viết, toàn văn mở.

- **Định lý 2.21** (Ch.2, tr. ~25): *"The problem P|prec, p_j = 1|C_max is NP-complete."* Chứng minh quy dẫn từ bài toán CLIQUE, với `B = 3`.
- Ghi chú thư mục (Ch.2, cuối chương): *"The first proof of the NP-completeness of P|prec, p_j = 1|C_max is due to Ullman [1975]. The proof we give in Theorem 2.21 is due to Lenstra and Rinnooy Kan [1978]."*
- **Định lý 2.27** (Ch.2, tr. ~30): *"There can be no α-approximation algorithm for P|prec, p_j = 1|C_max with α < 4/3 unless P = NP."* Lập luận: quy dẫn cho makespan hoặc 3 hoặc ≥ 4, nên một xấp xỉ tốt hơn 4/3 sẽ tách được hai trường hợp.
- Ullman, J.D. (1975), *NP-complete scheduling problems*, Journal of Computer and System Sciences 10(3):384–393.
- Lenstra, J.K. & Rinnooy Kan, A.H.G. (1978), *Complexity of scheduling under precedence constraints*, Operations Research 26(1):22–35.
- Svensson, O. (2010/2011), *Conditional hardness of precedence constrained scheduling on identical machines*, STOC 2010 / *Hardness of Precedence Constrained Scheduling on Identical Machines*, SIAM Journal on Computing 40(5). Không thể vượt tỉ số 2 của Graham, dưới một biến thể mạnh của Unique Games Conjecture do Bansal & Khot đưa ra *(theo abstract; epubs.siam.org trả 403)*.
- Nederlof, Swennenhuis & Węgrzycki (2023), *A Subexponential Time Algorithm for Makespan Scheduling of Unit Jobs with Precedence Constraints*, arXiv:2312.03495, §1: *"Settling the complexity of Pm|prec, p_j=1|C_max even for m=3 machines is the last open problem from the book of Garey and Johnson"*.

**Với doc2roadmap:** **bắt sửa điểm 2 và trực tiếp phục vụ điểm 7.**
- Bài dự án đang giải là NP-khó ngay cả khi W cố định lớn (W thay đổi theo input). Với W = 3 thì độ phức tạp **vẫn đang mở sau 47 năm** — nên việc dự án chưa giải tối ưu không phải thiếu sót, nhưng việc dự án **không nói ra rằng mình đang xấp xỉ** thì là thiếu sót.
- Có ngưỡng cứng 4/3: không thuật toán đa thức nào (trừ khi P=NP) cho số stage tốt hơn 4/3 lần tối ưu. Coffman–Graham cho (2 − 2/W) ∈ [1.6, 1.75] với W ∈ [5,8]. Khoảng cách giữa 4/3 và 1.6 là toàn bộ không gian cải tiến có thể — rất nhỏ. **Suy luận:** không đáng đầu tư thêm vào phần này; lấy Coffman–Graham, trích Lam–Sethi/Braschi–Trystram, và chuyển ngân sách nghiên cứu sang phần đánh giá.

---

## 3. Knowledge Space Theory — định nghĩa hình thức mà dự án đang thiếu

Nguồn chính đọc toàn văn: Doignon, J.-P. & Falmagne, J.-C. (2015), *Knowledge Spaces and Learning Spaces*, arXiv:1511.06757 (chương sách tổng thuật do chính hai tác giả sáng lập viết).

### 3.1 "Learning path" có định nghĩa hình thức, và nó không phải là xếp tầng

**Định nghĩa 45:**

> "Let (Q, K) be a finite knowledge structure. A learning path in K is a maximal chain of states. A gradation C is a learning path which is accessible (Definition 5), that is: for any nonempty state K in C there is some item q in K for which K \ {q} ∈ K."

> "A gradation always consists of 1 + |Q| states of respective sizes 0, 1, . . . , |Q|, and it forms itself a learning space on Q."

**Với doc2roadmap:** **phản bác cách dự án gọi tên sản phẩm của mình.** Trong KST, một *learning path* là một **xích cực đại các trạng thái tri thức** — tức một thứ tự tuyến tính toàn phần, học từng item một, `|Q|+1` trạng thái. Nó **không** là một phân hoạch thành các stage 5–8 khái niệm. Cái A10 sinh ra là *một* linear extension gom cụm của thứ tự bộ phận, tức *một* gradation được đóng gói lại — không phải "lộ trình học" theo nghĩa hình thức đã có sẵn 40 năm. Nếu bài báo dùng chữ "learning path" mà không phân biệt, reviewer biết KST sẽ bắt lỗi ngay.

### 3.2 Chỗ KST bác bỏ trực diện mô hình đồ thị tiên quyết

**Định nghĩa 9 + Định lý 10 (Birkhoff, 1937):**

> "Definition 9. A quasi ordinal space is a knowledge space closed under intersection."

> "Theorem 10 (Birkhoff, 1937). There exists a one-to-one correspondence between the collection of all quasi ordinal spaces K on a set Q and the collection of all quasi orders Q on Q."

Ngay sau đó, trong cùng đoạn:

> "**Note in passing that the closure under intersection does not make good pedagogical sense.**"

Và **Định lý 7** cho thấy learning space = antimatroid = knowledge space well-graded — tức đóng dưới **hợp** (union) và có tính well-graded, **không** đóng dưới giao.

**Với doc2roadmap:** đây là phản chứng mạnh nhất tìm được cho toàn bộ nền tảng A9+A10. Đồ thị tiên quyết (quan hệ tiền thứ tự trên khái niệm) tương ứng **chính xác và duy nhất** với quasi ordinal space qua Birkhoff. Hai người sáng lập lý thuyết viết rằng cấu trúc đó "không có ý nghĩa sư phạm tốt". Lý do: một quasi ordinal space bắt buộc rằng nếu có hai cách hiểu một chủ đề (hai trạng thái K, L), thì phần giao K∩L cũng phải là một trạng thái hợp lệ — trong khi thực tế học viên có thể đi hai đường khác nhau mà không có "đường chung nhỏ nhất". Learning space chỉ đòi đóng dưới hợp, nên cho phép **nhiều gradation song song**.

Dự án **không bắt buộc phải** chuyển sang learning space (đó là một công trình lớn, và không có dữ liệu học viên thì không ước lượng được). Nhưng dự án **bắt buộc phải nêu hạn chế này** trong phần Limitations, kèm trích dẫn — nếu không, đó là bỏ qua một phản chứng đã công bố.

### 3.3 Fringe: "sẵn sàng học tiếp cái gì" là một *tập*, không phải một *tầng*

**Định nghĩa 20 + Định lý 21 (Fringe Theorem):**

> "The outer fringe of a state K is the set of items K^O = {q ∈ Q \ K : K ∪ {q} ∈ K}"

> "Theorem 21. In a learning space, any state is specified by the pair formed of its inner fringe and its outer fringe."

> "The outer fringe is especially important because, assuming that the learning space is a faithful representation of the cognitive organization of the material, it tells us exactly what the student is ready to learn."

Bằng chứng thực nghiệm (§12.3), dẫn Cosyn et al. (2013):

> "For elementary school mathematics, the median of the distribution of the estimated (conditional) success probabilities was .93. This estimate was based on **1,940,473 learning occasions**."

Và §12.4, dẫn Ahlgren & Harper (2013) về xếp lớp bằng ALEKS ở University of Illinois — Bảng 7, phần trăm giảm số ca rút môn so với mốc Thu 2006:

| Môn | 2006→2007 | 2006→2008 |
|---|---|---|
| BusCalc | −57% | −19% |
| Calc | −49% | −81% |
| CalcExp | −67% | −42% |

So sánh chất lượng đo lường (§12.2): hệ số point-biserial của đánh giá ALEKS là **.67**, trong khi trung bình của 65 item bài Algebra I California Standards Test (ETS 2008, Bảng 7.2 tr. 397) là **.36**, trung vị **.38**, dải [.10, .53].

**Với doc2roadmap:** **bắt sửa quan niệm nền của điểm 1 và 2.** Trong hệ đã kiểm chứng trên gần 2 triệu lượt học, thứ học tiếp **không phải là "tầng kế"** mà là *outer fringe của trạng thái từng người*. A10 xuất ra một danh sách stage toàn cục, giống nhau cho mọi người học — đó là một **giản lược có chủ ý** vì dự án không có dữ liệu học viên. Điều này chấp nhận được, nhưng phải viết ra: "A10 sinh một gradation cố định; KST cho thấy lộ trình đúng là phụ thuộc trạng thái, và phần đó ngoài phạm vi vì thiếu dữ liệu tương tác." Không viết ra thì thành tuyên bố quá mức.

### 3.4 Tiền lệ cổ nhất

Meinke, J.G. & Bauer, C.R., *Topological sorting as a tool in curriculum planning*, ACM (DOI 10.1145/800144.804757) — dùng sắp xếp tô-pô để lập kế hoạch chương trình học, có mã FORTRAN tên TOPSORT *(chỉ tiếp cận được tiêu đề + mô tả thứ cấp; ACM DL trả 403)*.

Kahn, A.B. (1962), *Topological sorting of large networks*, Communications of the ACM 5(11):558–562 — nguồn gốc thuật toán Kahn.

**Với doc2roadmap:** ý tưởng "sắp xếp tô-pô để lập lộ trình học" đã được công bố ở ACM từ thập niên 1970. Dự án không thể trình bày nó như đóng góp mới.

---

## 4. Curriculum sequencing / learning path recommendation — phê phán chất lượng phương pháp

Nghi ngờ của chủ dự án ("phần lớn đánh giá yếu") **được xác nhận**, và xác nhận được bằng lời của chính người trong ngành.

### 4.1 Quy mô văn liệu

Vanderlei Freitas và cộng sự (2021), *Metaheuristic-based adaptive curriculum sequencing approaches: a systematic review and mapping of the literature*, Artificial Intelligence Review 54:711–754. Phạm vi: **61 công trình trong phần mapping, 58 trong phần review, khoảng 2005–2018** *(theo abstract + mô tả thứ cấp; Springer chặn toàn văn)*.

### 4.2 Lời thú nhận từ trong ngành

Cùng nhóm tác giả, *A comparative analysis of metaheuristics applied to adaptive curriculum sequencing*, Soft Computing (2021), bản mở PMC8099996, mục "Related works":

> "it is challenging to evaluate ACS approaches due to the lack of available datasets or benchmarks. Few studies indicate or make available the data used in the evaluation process."

> "in most cases the studies do not provide sufficient data to reproduce its experiments."

Và nhận xét rằng nhiều công trình *"only present the validity of using a metaheuristic considering that their proposed method converges"* — tức chỉ chứng minh thuật toán hội tụ, chứ không chứng minh lộ trình sinh ra tốt hơn.

Chính bài này, mục "Computational experiments", đánh giá trên: dữ liệu tổng hợp 50–1000 tài liệu học, 24 hồ sơ học viên, 5 lần chạy; **bộ dữ liệu thật duy nhất có 284 tài liệu học và 61 học viên**, từ một khoá năm 2017.

### 4.3 Hiện trạng 2025: vẫn không có người học thật

Cheng, Zhang, Wang, Fang, He, Guan, Pan & Luo (2025), *Education-Oriented Graph Retrieval-Augmented Generation for Learning Path Recommendation*, arXiv:2506.22303. Đây là công trình mới, dùng GPT-4o + TextGrad + RL đa tác tử — tức đại diện cho đỉnh của ngành hiện nay.

- Bộ dữ liệu: Junyi (835 KC, 525.061 người học), MOOCCubeX (443 KC, 629 người học), ASSIST09 (167 KC, 4.217 người học).
- **Không có người học thật trong vòng đánh giá.** Bài tự nêu: *"real-world data only contains static information, which cannot be directly used to analyze the exercise sequences"*, nên họ dùng một Knowledge Evolution-based Simulator dựa trên DKT.
- Không có nhóm đối chứng; baseline là các mô hình khác (KNN, GRU4Rec, RL-Tutor, CSEAL, SRC, GEHRL, DLPR).
- Chỉ số duy nhất: `E_p = (E_end − E_start)/(E_sup − E_start)` — mức cải thiện **do chính mô hình knowledge tracing ước lượng**. Bảng 1, step=20: Junyi 0.2758, MOOCCubeX 0.3589, ASSIST09 0.1455.

**Suy luận:** đây là vòng lặp khép kín. Mô hình sinh lộ trình được chấm bởi một mô phỏng học viên do chính nhóm dựng; "cải thiện" đo được là cải thiện trong mô phỏng, không phải trong người. Khi công trình 2025 dùng LLM mới nhất vẫn dừng ở đây, thì **không có chuẩn mực đánh giá nào trong ngành mà doc2roadmap phải đuổi kịp** — và ngược lại, một đánh giá đối chứng thật dù nhỏ cũng sẽ vượt mặt bằng.

### 4.4 Tổng kết bằng bảng

| Câu hỏi | Trả lời từ nguồn |
|---|---|
| Bao nhiêu công trình được tổng kết? | 61 mapping / 58 review, 2005–2018 (AI Review 2021) |
| Có benchmark chung không? | Không — *"lack of available datasets or benchmarks"* (Soft Computing 2021) |
| Có tái lập được không? | Phần lớn không — *"do not provide sufficient data to reproduce"* |
| Cỡ mẫu người học thật điển hình? | 61 học viên / 284 tài liệu (Soft Computing 2021, bộ thật duy nhất) |
| Công trình 2025 tốt nhất dùng người học thật? | Không — mô phỏng DKT (arXiv:2506.22303) |
| Có nhóm đối chứng không? | Không tìm thấy công trình nào trong số đọc được có RCT về lộ trình sinh tự động |

**Với doc2roadmap:** **không phản bác điểm nào**, nhưng **hạ trần kỳ vọng**: dự án không cần đánh bại ai. Đồng thời cảnh báo — vì mặt bằng thấp, việc chỉ "sinh ra được lộ trình" không phải đóng góp; đóng góp phải nằm ở **cách đo**.

---

## 5. Đánh giá một lộ trình sinh tự động — phần quan trọng nhất cho dự án

### 5.1 Có chỉ số chuẩn để so với mục lục gốc không? — Có, nhưng nó đến từ NLP, không từ giáo dục

Lapata, M. (2006), *Automatic Evaluation of Information Ordering: Kendall's Tau*, Computational Linguistics 32(4):471–484, https://aclanthology.org/J06-4002/. Đọc toàn văn.

Định nghĩa (§2, phương trình 1):

> "Let π and σ denote two distinct orderings of Y, and S(π, σ) the minimum number of adjacent transpositions needed to bring π to σ. Kendall's τ is defined as: τ = 1 − 2S(π,σ)/(N(N−1)/2)"

**Thực nghiệm 1** (§3): 189 tình nguyện viên, giữ lại 179 để phân tích (~22 người/văn bản), chấm mức dễ hiểu/mạch lạc theo thang 1–7.
- Tương quan giữa τ và điểm người chấm: **Pearson r = 0.45 (p < 0.01, N = 64)**.
- Đồng thuận giữa người với người (leave-one-out, 178 phân tích): **r = 0.56** (min 0.001, max 0.94, SD 0.25).
- Kết luận của tác giả: *"τ's agreement with the human data is not far from the average human agreement."*

**Thực nghiệm 2** (§4): 32 tình nguyện viên trong phòng thí nghiệm, đo **thời gian đọc**.
- Tương quan τ ↔ thời gian đọc: **Pearson r = −0.48 (p < 0.01)**.
- Tương quan điểm chấm ↔ thời gian đọc: **r = −0.47 (p < 0.01)**.

Lý do chọn τ thay vì Spearman ρ (§2), trích:

> "the statistical distribution of τ approaches the normal distribution faster than r_s ... thus offering an advantage for small to moderate sample studies with 30 or fewer data points."

> "Spearman's rank correlation coefficient is a biased statistic ... In contrast, Kendall's τ does not provide a biased estimate of the true correlation."

Cảnh báo của chính tác giả (§5):

> "The τ evaluations presented in this article used a single reference text. Previous work ... has shown that there may be many acceptable orders for a set of information-bearing items, although topically related sentences seem to appear together."

Đề xuất của tác giả cho nhiều tham chiếu: tính τ N lần, mỗi lần với một tham chiếu, rồi lấy trung bình.

**Với doc2roadmap:** **đây chính là chỉ số dự án cần, và dự án đã có sẵn đối chứng (thứ tự chương).** Kendall τ giữa thứ tự khái niệm do A10 sinh và thứ tự xuất hiện đầu tiên của khái niệm trong giáo trình là chỉ số **có nền tảng thực nghiệm** (tương quan với cả phán đoán người và với nỗ lực xử lý), **không thiên lệch ở cỡ mẫu nhỏ**, và **đã được ngành NLP dùng làm chuẩn 20 năm**. Không cần bịa chỉ số mới.

**Suy luận — một cái bẫy phương pháp mà A10 đang tự đặt ra cho mình.** Điểm 2 nói: *"thứ tự giữa các stage con cùng tầng là tuỳ ý, chọn theo thứ tự chương."* Nếu dùng thứ tự chương để phá thế hoà **và** dùng thứ tự chương làm đối chứng để tính τ, thì τ bị nhiễm: một phần điểm số đến từ việc đã chép sẵn đáp án. Phải làm một trong hai:
- (a) phá thế hoà bằng tiêu chí **không** dùng vị trí chương (ví dụ: số khái niệm hậu duệ giảm dần, hoặc ID ổn định), rồi τ là đo thật; **hoặc**
- (b) giữ cách phá thế hoà hiện tại nhưng báo cáo **hai** con số: τ toàn phần và τ chỉ tính trên các cặp mà thứ tự **không** do quy tắc phá thế hoà quyết định.
Lựa chọn (a) sạch hơn và rẻ hơn.

### 5.2 Các chỉ số khác trong ngành giáo dục

- Spearman's footrule: tổng trị tuyệt đối hiệu hai hạng. Dùng trong đánh giá xếp hạng; có ưu thế khi vị trí đầu quan trọng hơn *(mô tả thứ cấp, không tìm được công trình giáo dục nào dùng nó làm chuẩn cho lộ trình học)*.
- Độ chính xác theo cặp (pairwise precision/recall/F1) — chuẩn de facto của bài toán phân loại quan hệ tiên quyết; xem §5.3.
- Đồng thuận chuyên gia: trong văn liệu trích khái niệm tiên quyết, nhãn vàng được xây bằng chuyên gia lĩnh vực (xem §5.3).
- Kết quả học thật / thời gian học: chỉ tìm thấy ở KST/ALEKS (§3.3), **không** ở văn liệu learning-path recommendation.

**Không tìm thấy nguồn nào định nghĩa một chỉ số chuẩn riêng của ngành giáo dục để so lộ trình sinh tự động với mục lục giáo trình.** Câu này có giá trị bằng một nguồn: nghĩa là dự án có thể mượn thẳng Kendall τ của Lapata, trích đúng nguồn NLP, và đó là lựa chọn phòng thủ được.

### 5.3 Mặt bằng khó của bài toán tiên quyết — cần cho việc diễn giải A9/A10

Alzetta, Miaschi, Dell'Orletta, Koceva & Torre (2020), *PRELEARN @ EVALITA 2020: Overview of the Prerequisite Relation Learning Task for Italian*, EVALITA 2020, tr. 325–332, https://aclanthology.org/2020.evalita-1.54/. Đọc toàn văn.

Dữ liệu ITA-PREREQ, xây trên AL-CPL (Liang et al., 2018 — khái niệm rút từ giáo trình bốn lĩnh vực: data mining, geometry, physics, precalculus; **chuyên gia lĩnh vực gán nhãn thủ công** mọi cặp khái niệm). Ví dụ số từ Bảng 1: Data Mining có **76 khái niệm, 523 cặp có nhãn, 159 cặp dương (30,40%), 364 cặp âm (69,59%)**; tách 424 train / 99 test.

Bài báo ghi rõ về độ cân bằng:

> "regardless of the domain the dataset is strongly unbalanced since the majority of concept pairs do not show a prerequisite relation"

Kết quả (bảng xếp hạng, cột cuối = F1 trung bình 4 lĩnh vực):

| Kịch bản | Hệ tốt nhất | F1 | Baseline (occurrence) |
|---|---|---|---|
| In-domain, raw text | NLP-CIC BERT | **0.887** | 0.586 |
| In-domain, structured | NLP-CIC Complex+wd | 0.856 | 0.586 |
| **Cross-domain, raw text** | NLP-CIC BERT | **0.690** | 0.525 |
| Cross-domain, structured | NLP-CIC Complex+wd | 0.668 | 0.525 |

Chỉ 3 đội nộp bài trên 16 đội đăng ký, tổng 14 run.

**Với doc2roadmap:** **trực tiếp giải thích vấn đề số 7.** Khi chuyển lĩnh vực, F1 của hệ tốt nhất tụt từ 0.887 xuống 0.690 trên tập **test cân bằng 50/50**. A8 của dự án chạy cross-domain (giáo trình bất kỳ) với một LLM tổng quát, temperature 0, không fine-tune — hợp lý khi kỳ vọng recall ở quanh hoặc dưới mức đó. Recall thấp ⇒ thiếu cạnh ⇒ node không có cạnh vào ⇒ **tầng 1 phình**. Đây là nguyên nhân gốc, và nó nằm ở A8, không ở A10.

---

## 6. Gom nhóm thành "stage/module": tiền lệ và cơ sở cho con số 5–8

### 6.1 "Stage = tầng ∩ cụm chủ đề" — có tiền lệ không?

**Không tìm thấy nguồn sơ cấp nào đề xuất hay đánh giá cấu trúc "giao của một tầng tô-pô với một cụm cộng đồng" làm đơn vị mô-đun học.** Đã tìm với các tổ hợp: community detection + topological sort + curriculum module; clustering + layering + learning path; concept clustering + level intersection. Kết quả trả về chỉ gồm blog, issue GitHub, và các bài về community detection thuần.

Thứ gần nhất tìm được là một quan sát **không thuộc ngành giáo dục**: Lapata (2006) §5 dẫn Barzilay, Elhadad & McKeown (2002) rằng trong sắp thứ tự câu, *"topically related sentences seem to appear together"* trong các thứ tự được người chấp nhận.

**Với doc2roadmap:** điểm 2 là **thiết kế gốc, không có tiền lệ**. Điều đó không sai — nhưng nó có hai hệ quả: (i) không được trình bày như "theo văn liệu"; (ii) vì không ai đã kiểm nó, dự án phải tự kiểm, và cách kiểm rẻ nhất là ablation: so τ (so với mục lục) của ba biến thể — tầng thuần, tầng ∩ cụm, tầng ∩ cụm có ép trần Coffman–Graham.

### 6.2 Con số 5–8: truy tận gốc

**Miller, G.A. (1956)**, *The Magical Number Seven, Plus or Minus Two*, Psychological Review 63(2):81–97, bản toàn văn tại https://psychclassics.yorku.ca/Miller/.

Miller tự nghi ngờ con số của mình. Bài kết bằng ý rằng sự lặp lại của số bảy có lẽ chỉ là *"a pernicious, Pythagorean coincidence"*. Bài cũng tách bạch hai giới hạn khác nhau mà số bảy vô tình cùng xuất hiện: *"The span of absolute judgment and the span of immediate memory are quite different kinds of limitations"* — span of absolute judgment bị giới hạn bởi **lượng thông tin**, span of immediate memory bởi **số item**. Cơ chế Miller thực sự muốn nói là **recoding**: *"Recoding is an extremely powerful weapon for increasing the amount of information that we can deal with."*

**Cowan, N. (2001)**, *The magical number 4 in short-term memory: A reconsideration of mental storage capacity*, Behavioral and Brain Sciences 24(1):87–114. Từ abstract:

> "Miller (1956) summarized evidence that people can remember about seven chunks ... though that number was meant more as a rough estimate and rhetorical device than as a real capacity limit. Others have suggested a more precise capacity limit of only three to five chunks."

Cowan lập luận rằng giới hạn nhỏ hơn (3–5 chunk) là thật, khi kiểm soát được rehearsal và hỗ trợ từ trí nhớ dài hạn *(theo abstract)*.

**Mayer / segmenting principle** — chỗ gần nhất có bằng chứng định lượng về "chia nhỏ nội dung":

Rey, Beege, Nebel, Wirzberger, Schmitt & Schneider (2019), *A Meta-analysis of the Segmenting Effect*, Educational Psychology Review 31:389–419. Đọc toàn văn. **Bảng 3**:

| Kết quả đo | k (số so sánh) | n | d | KTC 95% |
|---|---|---|---|---|
| Retention (tổng) | 67 | 6100 | **0.32*** | [0.20, 0.43] |
| Transfer (tổng) | 56 | 4754 | **0.36*** | [0.24, 0.48] |
| Cognitive load | 20 | 1687 | 0.23** | [0.06, 0.39] |
| **Learning time** | 19 | 1625 | **−0.92*** | [−1.64, −0.20] |
| Retention, system-paced | 32 | 2578 | 0.42*** | [0.21, 0.63] |
| Retention, learner-paced | 21 | 2351 | 0.19 (n.s.) | [−0.04, 0.45] |
| Transfer, learner-paced | 16 | 1190 | 0.45*** | [0.24, 0.66] |

Về độ dài đoạn: bài chỉ ghi nhận **độ dài đoạn trung bình được báo cáo là 75,49 giây** (§Results, mô tả mẫu). **Không có phân tích moderator nào về kích thước đoạn tính theo số khái niệm**, và không có khuyến nghị nào về "bao nhiêu khái niệm một mô-đun".

**Không tìm thấy nguồn sơ cấp nào khuyến nghị một cỡ mô-đun học cụ thể tính bằng số khái niệm.** Các khuyến nghị "3–5 khái niệm mỗi mục tiêu" hay "5–9 mỗi màn hình" chỉ xuất hiện trong blog ngành đào tạo (eLearning Industry, TheeLearningCoach, trang trung tâm dạy-học của các trường), đều dẫn về Miller 1956 — tức dẫn về đúng con số mà Miller và Cowan đã bác.

**Với doc2roadmap:** **phản bác cơ sở của điểm 2.**
- Trần "5–8" **không** có nguồn sơ cấp. Nếu bài báo viện Miller 7±2 thì đó là viện dẫn sai: Miller nói giới hạn ấy là về **item trong trí nhớ tức thời khi thực hiện một tác vụ nhớ**, không phải về số chủ đề trong một bài học, và chính ông gọi số bảy là trùng hợp Pythagore tai hại.
- Bằng chứng gần nhất, segmenting principle, ủng hộ việc **chia nhỏ** (d ≈ 0.32–0.36) nhưng **không** nói chia thành bao nhiêu phần, và kèm một cái giá rõ ràng: **học lâu hơn đáng kể (d = −0.92)**.
- **Đề xuất cụ thể:** đừng bảo vệ con số 5–8 bằng tâm lý học. Bảo vệ nó bằng **thuật toán**: nói thẳng "trần W là tham số của bài toán width-constrained layering; ta đặt W = 8 mặc định; hiệu ứng của W lên số stage và lên τ được báo cáo ở bảng ablation W ∈ {4, 6, 8, 12}". Như vậy 5–8 trở thành một lựa chọn kỹ thuật minh bạch thay vì một tuyên bố tâm lý học sai.

---

## 7. Xen kẽ và giãn cách — "stage = tầng ∩ cụm" có đi ngược bằng chứng không?

### 7.1 Bằng chứng định lượng về xen kẽ

**Rohrer, D., Dedrick, R.F. & Burgess, K. (2014)**, *The benefit of interleaved mathematics practice is not limited to superficially similar kinds of problems*, Psychonomic Bulletin & Review 21:1323–1330. Đọc toàn văn.

Tóm tắt, nguyên văn:

> "In the classroom-based experiment reported here, grade 7 students (n = 140) received blocked or interleaved practice over a nine-week period, followed two weeks later by an unannounced test. The mean test scores were greater for material learned by interleaved practice rather than by blocked practice (**72 % vs. 38 %, d = 1.05**)."

Phần kết quả: `t(139) = 10.49, p < .001`; `d = 1.05, 95 % CI = [0.80, 1.30]`. Bài cũng dẫn một kết quả trước đó `d = 1.23` (Taylor & Rohrer, 2010).

Rohrer, D. & Taylor, K. (2007), *The shuffling of mathematics problems improves learning*, Instructional Science 35(6):481–498 — hiệu ứng: luyện theo khối cho kết quả tốt hơn **trong lúc luyện**, nhưng xen kẽ cho kết quả tốt hơn **ở bài kiểm tra trì hoãn** *(theo abstract; máy chủ USF từ chối kết nối, không đọc được toàn văn)*.

### 7.2 Nhưng mức độ ủng hộ của tổng quan lại khiêm tốn

Dunlosky, Rawson, Marsh, Nathan & Willingham (2013), *Improving Students' Learning With Effective Learning Techniques*, Psychological Science in the Public Interest 14(1):4–58: xếp **distributed practice** và **practice testing** là **high utility**; **interleaved practice** là **moderate utility**, lý do là nền bằng chứng còn mỏng *(tiếp cận qua trang tóm tắt APS + qua Donoghue & Hattie 2021; SAGE chặn toàn văn)*.

Donoghue, G.M. & Hattie, J.A.C. (2021), *A Meta-Analysis of Ten Learning Techniques*, Frontiers in Education 6:581216. Đọc toàn văn HTML. Tổng: 242 nghiên cứu, 1.619 effect size, 169.179 người tham gia duy nhất, d trung bình 0.56. Bảng tổng hợp:

| Kỹ thuật | Phân loại Dunlosky | Số ca | n duy nhất | d | SEM | I² (%) |
|---|---|---|---|---|---|---|
| Distributed practice | High | 150 | **152.952** | **0.85** | 0.053 | 83 |
| Practice testing | High | 374 | 6.033 | 0.74 | 0.04 | 86 |
| Elaborative interrogation | Moderate | 254 | 2.138 | 0.56 | 0.048 | 78 |
| Imagery | Moderate | 135 | 1.052 | 0.56 | 0.061 | 68 |
| Self explanation | Moderate | 93 | 804 | 0.54 | 0.092 | 77 |
| **Interleaved practice** | (bảng ghi "Low") | 104 | **972** | **0.47** | 0.089 | **88** |
| Re-reading | Low | 113 | 1.529 | 0.47 | 0.06 | 86 |
| Summarization | Low | 234 | 1.990 | 0.44 | 0.055 | 89 |

**Lưu ý về mâu thuẫn nội tại của nguồn này:** phần chữ của Donoghue & Hattie viết *"Categorised as 'moderate' support were Elaborative Interrogation, Self-Explanation and Interleaved Practice"*, nhưng cột phân loại trong bảng lại ghi Interleaved practice là "Low". Bản gốc Dunlosky et al. 2013 xếp interleaving là **moderate**. Khi trích, phải trích bản gốc.

Donoghue & Hattie cũng ghi nhận, về interleaving: *"The research evidence base is currently small, and it is not clear how to break tasks in an optimal manner so as to interleave them."*

### 7.3 Kết luận cho dự án — có nhưng phải nói cho đúng

**Suy luận, và đây là chỗ cần cẩn trọng nhất trong cả bản khảo sát này:** bằng chứng xen kẽ **không** phản bác trực tiếp điểm 2. Lý do: mọi nghiên cứu xen kẽ đã đọc đều đo **lịch luyện tập bài toán sau khi đã dạy**, không đo **thứ tự trình bày lần đầu của khái niệm**. Rohrer et al. 2014 so hai cách sắp bài tập về nhà trong 9 tuần, không so hai cách sắp chương sách. Nói "gom mọi khái niệm cùng chủ đề vào một khối liền là kém hơn xen kẽ" là **suy rộng quá nguồn**.

Điều bằng chứng **có** nói, và nói mạnh:
1. Nếu A10 (hoặc bất cứ thành phần hạ nguồn nào) sinh ra **bài luyện tập** kèm theo stage, và bài luyện tập ấy chỉ gồm khái niệm của chính stage đó, thì đó **đúng là blocked practice**, và ở đó Rohrer et al. 2014 (72% vs 38%, d = 1.05, n = 140, lớp học thật) là phản chứng trực tiếp.
2. **Distributed practice** có nền bằng chứng mạnh hơn interleaving một bậc (d = 0.85 trên 152.952 người, so với d = 0.47 trên 972 người). Một lộ trình mà mỗi khái niệm xuất hiện đúng một lần, trong đúng một stage, rồi không bao giờ quay lại, là **massed practice** — đi ngược kết quả vững nhất trong cả mục này.

**Với doc2roadmap:** **bắt sửa phạm vi tuyên bố của điểm 2, không bắt bỏ điểm 2.** Cụ thể: (i) không được viết rằng thiết kế stage có cơ sở tâm lý học nhận thức; (ii) nên thêm một câu Limitations nói rằng lộ trình sinh ra là **thứ tự trình bày**, không phải **lịch luyện tập**, và rằng văn liệu spacing/interleaving hàm ý một lớp ôn tập giãn cách nằm ngoài phạm vi A10; (iii) nếu sau này có thành phần sinh bài tập, phải xen kẽ chéo stage.

---

## 8. Độ khó theo độ sâu DAG

Zuev, K. & Stavrinides, P. (2025), *Breadth, Depth, and Flux of Course-Prerequisite Networks*, arXiv:2506.23510. Đọc toàn văn.

§IV định nghĩa **topological stratification** hoàn toàn trùng với cách A10 xếp tầng: S₁ = node in-degree 0; bỏ S₁ và cạnh ra của nó, S₂ = node in-degree 0 còn lại; lặp. Và §V.B định nghĩa depth của node ω ∈ Ω_t (Ω = tập node out-degree 0) là `d(ω) = t`, tức **số node trên đường có hướng dài nhất kết thúc ở ω**; depth của mạng là trung bình d(ω) trên Ω.

Tuyên bố đáng chú ý, §IV:

> "In the context of CPNs, the topological stratification produces subsets S₁, . . . , S_T of courses of approximately the same level of difficulty, with more advanced courses lying in higher strata."

**Bài không kiểm chứng tuyên bố này.** Tìm chuỗi "difficulty" trong toàn văn chỉ khớp đúng một lần — chính câu trên. Không có điểm số, không có tỉ lệ trượt, không có khảo sát độ khó cảm nhận, không có hệ số tương quan nào.

Đối chiếu với thực hành đo độ khó hiện nay: Baucks, F., Schmucker, R. & Wiskott, L. (2025), *The Course Difficulty Analysis Cookbook*, arXiv:2508.13218 — tổng quan và so sánh đầu tiên về các cách gán độ khó cho môn học, dựa trên **điểm trung bình (GPA) và mô hình latent trait**, nhấn mạnh phải đo độ khó **độc lập với thành tích của chính nhóm học viên đang học** để giảm thiên lệch *(theo abstract)*. **Abstract không nhắc tới vị trí trong đồ thị tiên quyết hay độ sâu như một cách đo độ khó.**

Paz, H.R. (2025), *The Topology of Hardship: Empirical Curriculum Graphs and Structural Bottlenecks in Engineering Degrees*, arXiv:2512.05561 — dựng đồ thị chương trình từ 29 chương trình kỹ thuật, tính density, longest path, bottleneck centrality, và liên hệ với tỉ lệ bỏ học và thời gian tốt nghiệp. **Abstract không báo cáo hệ số tương quan nào giữa độ sâu và khó khăn của từng người học** *(theo abstract)*.

**Không tìm thấy nguồn nào kiểm chứng rằng độ sâu trong đồ thị tiên quyết tương quan với độ khó cảm nhận hoặc tỉ lệ sai của người học.** Nói thẳng: giả thiết này được **phát biểu** trong văn liệu (Zuev & Stavrinides 2025) nhưng **chưa được ai kiểm**.

**Với doc2roadmap:** **bắt sửa điểm 6.** Có hai lựa chọn phòng thủ được:
- (a) Đổi tên: gọi đại lượng đó là **"độ sâu tiên quyết"** hoặc **"bậc phụ thuộc"** chứ không gọi là "độ khó". Đây là cách rẻ nhất, xoá hẳn một tuyên bố chưa có cơ sở, không đổi một dòng mã. Trích Zuev & Stavrinides 2025 §IV cho tên gọi và trích như một *giả thiết chưa kiểm*.
- (b) Nếu vẫn muốn gọi là độ khó, phải kiểm: lấy một đại lượng độ khó độc lập (ví dụ tần suất câu hỏi, độ hiếm của thuật ngữ, hoặc đánh giá chuyên gia trên mẫu) và báo Spearman ρ. Không có dữ liệu học viên thì (b) khó; nên chọn (a).

---

## 9. Sinh lộ trình bằng LLM (2024–2026) và tính bất ổn thứ tự

### 9.1 LLM sắp thứ tự nội dung học

Công trình đại diện đã phân tích ở §4.3 (Cheng et al. 2025, arXiv:2506.22303) — GPT-4o dựng đồ thị tiên quyết + RL sắp thứ tự, đánh giá bằng mô phỏng.

Các công trình liên quan khác tìm thấy (mức abstract): *LLM-Assisted Knowledge Graph Completion for Curriculum and Domain Modelling in Personalized Higher Education Recommendations* (arXiv:2501.12300) — đánh giá bằng "qualitative expert feedback and quantitative graph quality metrics", tức **không** có chỉ số thứ tự; *Leveraging LLMs for Automated Extraction and Structuring of Educational Concepts and Relationships* (MDPI MAKE 7(3), 2025) — so GPT-3.5 / GPT-4o-mini / GPT-4o trên ba tác vụ (sinh khái niệm, trích khái niệm, nhận quan hệ).

**Không tìm thấy công trình nào để LLM sắp thứ tự khái niệm học rồi đánh giá bằng Kendall τ so với thứ tự giáo trình gốc.** Đây là một khoảng trống thật, và là chỗ doc2roadmap có thể đóng góp.

### 9.2 Có ai cảnh báo LLM đổi thứ tự không ổn định giữa các lượt không? — Có, và đo được

*Position Bias Undermines Preference Consistency in Listwise LLM-Based Reranking*, arXiv:2608.03091. Mô hình thử: Llama-3.2-3B-Instruct, Mistral-7B-Instruct-v0.3, Qwen2.5-7B-Instruct. Dữ liệu: MovieLens-32M, Amazon Books. Phương pháp: M = 20 hoán vị thứ tự ứng viên cho mỗi truy vấn.

Bảng 1 (K = 25), chế độ zero-shot:

| Chỉ số | Ý nghĩa | MovieLens | Amazon Books |
|---|---|---|---|
| PPI — Pairwise Preference Instability | mức lật sở thích theo cặp khi đổi thứ tự đầu vào | 0.4775 | 0.3853 |
| GPI — Global Preference Inconsistency | bất nhất tổng hợp hạng kiểu Kemeny | 0.1149 | 0.0983 |
| **LOC — Listwise Output Consistency** | **Kendall τ giữa các hoán vị đầu vào khác nhau** | **0.6358** | **0.6986** |

Với biện pháp giảm nhiễu (SGS) của bài, LOC tăng lên 0.8268 / 0.8332.

Các công trình cùng hướng xác nhận hiện tượng: *One Pass, Any Order: Position-Invariant Listwise Reranking for LLM-Based Recommendation* (arXiv:2604.27599), *Ranked by Position: Order Sensitivity as an Exploitable Attack Surface in LLM Listwise Recommenders* (arXiv:2607.24869). Nguyên nhân được nêu: cross-candidate attention leakage và mã hoá vị trí phụ thuộc thứ tự dưới RoPE *(theo abstract)*.

**Với doc2roadmap:** **xác nhận mạnh điểm 5.** Khoá LLM chỉ được sắp **trong** stage, không được đổi thứ tự **giữa** các stage, là quyết định đúng và có nguồn. Con số đáng đưa vào bài: chỉ cần đảo thứ tự danh sách đầu vào, τ giữa hai đầu ra của cùng một mô hình, cùng prompt, rơi xuống **0.64–0.70** — tức LLM tự bất đồng với chính nó gần bằng mức bất đồng giữa hai người (so với r = 0.56 đồng thuận liên chủ thể của Lapata).

**Suy luận — nhưng điểm 5 vẫn chưa đủ chặt.** Khoá phạm vi mới chặn được một nửa rủi ro. Nửa còn lại: **bên trong** một stage 5–8 khái niệm, thứ tự do LLM sinh ra vẫn không ổn định dưới hoán vị đầu vào. Với temperature 0 thì lặp cùng đầu vào sẽ cho cùng đầu ra, nhưng **thứ tự đầu vào** lại do A10 quyết định (hiện là thứ tự nào?). Hai cách chữa, rẻ cả hai:
- Nạp khái niệm vào prompt theo **thứ tự chuẩn tắc** (ví dụ ID sắp xếp), để đầu ra là hàm xác định của tập chứ không của thứ tự ngẫu nhiên.
- Hoặc: chạy k hoán vị đầu vào, tổng hợp bằng Kemeny/Borda, và **báo cáo LOC** (τ trung bình giữa các lần) như một chỉ số ổn định của A10. Chỉ số này rẻ, không cần dữ liệu học viên, và là thứ ít công trình giáo dục nào báo cáo — một đóng góp thật.

---

## 10. Những chỗ không tìm thấy nguồn (mỗi câu ở đây có giá trị bằng một nguồn)

1. **Không tìm thấy nguồn sơ cấp nào** đề xuất, phân tích hay đánh giá "giao của một tầng tô-pô với một cụm cộng đồng" làm đơn vị mô-đun học (điểm 2).
2. **Không tìm thấy nguồn sơ cấp nào** khuyến nghị một cỡ mô-đun học cụ thể tính bằng số khái niệm; mọi khuyến nghị "5–9" / "3–5" gặp được đều nằm trong blog ngành và đều dẫn về Miller 1956, tức dẫn về đúng con số Miller và Cowan đã bác (điểm 2).
3. **Không tìm thấy nguồn nào** kiểm chứng tương quan giữa độ sâu DAG tiên quyết và độ khó cảm nhận hoặc tỉ lệ sai của người học; Zuev & Stavrinides (2025) §IV **phát biểu** quan hệ đó nhưng không kiểm (điểm 6).
4. **Không tìm thấy nguồn nào** bàn về việc gắn node phi-khái-niệm (hình, bảng) vào stage của khái niệm sớm nhất mà nó nối tới (điểm 4). Không có văn liệu ủng hộ lẫn phản bác — đây là quyết định kỹ thuật thuần, cứ ghi là heuristic và đi tiếp.
5. **Không tìm thấy nguồn nào** trong ngành giáo dục phân biệt tường minh "node đã xét mà không tìm thấy tiên quyết" với "node chưa từng được xét" trong pipeline trích quan hệ (điểm 3). Vấn đề gần nhất được văn liệu nói tới là **độ mất cân bằng và recall** của phân loại quan hệ tiên quyết (PRELEARN 2020, §5.3). **Suy luận:** điểm 3 là một thực hành kỹ thuật đúng mà ngành chưa đặt tên — nên A10 có thể trình bày nó như một đóng góp nhỏ về kỹ thuật (coverage accounting), miễn là kèm một con số: tỉ lệ node chưa từng nằm trong phiên suy luận nào.
6. **Không tìm thấy công trình nào** dùng Kendall τ để so lộ trình khái niệm do LLM sinh với thứ tự xuất hiện trong giáo trình gốc (§9.1) — khoảng trống, và là chỗ đóng góp rõ nhất.
7. **Không tìm thấy công trình learning-path recommendation nào** có nhóm đối chứng người học thật; tổng quan của chính ngành thừa nhận thiếu benchmark và thiếu khả năng tái lập (§4.2).

Ngoài ra, một phản bác trực tiếp cho điểm 1 mà chỉ tìm thấy ở nguồn kỹ thuật, không ở nguồn giáo dục: Gansner et al. (1993) §2.1, sau khi mô tả cách phá chu trình bằng đảo back edge, viết rằng cách đó cho bản vẽ nhiều thông tin hơn so với

> "collapsing all the nodes in a cycle into one node, or placing the nodes in a cycle on the same rank, or duplicating one of the nodes in the cycle, as various researchers have suggested"

Và cùng mục ghi nhận bài toán tập cung phản hồi tối thiểu: *"finding a minimal set (the 'feedback arc set' problem) is NP-complete"*.

**Với doc2roadmap:** điểm 1 (co SCC, cả khối vào một tầng) là **đúng cái mà Graphviz cố ý không làm**. Lý do của họ là chất lượng bản vẽ, không phải sư phạm — nên đây là phản chứng yếu, không phải phản chứng quyết định. Nhưng có hai hệ quả cứng: (i) một SCC lớn hơn trần 5–8 sẽ **phá vỡ bất biến trần**, cần xử lý tường minh; (ii) nên báo cáo phân bố kích thước SCC còn lại sau A9 — nếu tất cả đều là chu trình hai cạnh thì đơn giản, nếu có SCC lớn thì thiết kế hiện tại không đủ.

---

## Điểm phải sửa, xếp theo mức nặng

| # | Dự án đang làm | Nguồn phản bác / khoảng trống | Đề xuất cụ thể |
|---|---|---|---|
| 1 | Ép trần 5–8 bằng cách cắt tầng theo cụm chủ đề (điểm 2) | Bài toán này là `P\|prec,p=1\|C_max`, NP-khó (Ullman 1975; *Elements of Scheduling* Đ.2.21), không xấp xỉ dưới 4/3 (Đ.2.27), và **đã có thuật toán chuẩn**: Coffman–Graham 1972, cận (2−2/W) (Lam & Sethi 1977, sửa bởi Braschi & Trystram 1994), cài sẵn trong OGDF `CoffmanGrahamRanking` với `width(int)` | Thay cơ chế ép trần bằng Coffman–Graham (giữ cụm chủ đề làm tiêu chí phá thế hoà, không làm cơ chế chính). Nêu tên bài toán và trích 4 nguồn trên. Thêm assertion: số stage ≥ max(xích dài nhất, ⌈n/W⌉) |
| 2 | Gọi "độ sâu DAG" là **độ khó** (điểm 6) | Không tìm thấy nguồn nào kiểm chứng; Zuev & Stavrinides 2025 §IV chỉ phát biểu, không kiểm; chuẩn đo độ khó hiện nay (Baucks et al. 2025) dùng điểm số / latent trait, không dùng vị trí đồ thị | Đổi tên thành "độ sâu tiên quyết" / "bậc phụ thuộc". Xoá mọi câu hàm ý độ khó nhận thức. Trích Zuev & Stavrinides như một **giả thiết chưa kiểm** |
| 3 | Dùng thứ tự chương để phá thế hoà giữa các stage con cùng tầng (điểm 2) **và** (dự kiến) dùng thứ tự chương làm đối chứng đánh giá | Nhiễm đối chứng — không có nguồn, đây là lỗi thiết kế thí nghiệm | Phá thế hoà bằng tiêu chí không dùng vị trí chương (số hậu duệ giảm dần, hoặc ID ổn định). Hoặc báo cáo τ hai lần: toàn phần và chỉ trên cặp không do quy tắc phá thế hoà quyết định |
| 4 | Chưa có chỉ số đánh giá lộ trình | Lapata 2006 (CL 32(4)): Kendall τ tương quan r = 0.45 với phán đoán người (N=64, 179 người chấm) và r = −0.48 với thời gian đọc; đồng thuận liên chủ thể r = 0.56; τ không thiên lệch ở mẫu nhỏ. Không tìm thấy chỉ số chuẩn riêng của ngành giáo dục | Lấy Kendall τ giữa thứ tự A10 và thứ tự xuất hiện đầu tiên trong giáo trình làm chỉ số chính. Trích Lapata 2006. Kèm cảnh báo "single reference" của chính tác giả (§5) |
| 5 | Biện minh trần 5–8 (nếu có) bằng Miller 7±2 | Miller 1956 tự gọi số bảy là *"a pernicious, Pythagorean coincidence"* và tách rõ hai loại giới hạn; Cowan 2001 hạ xuống 3–5 chunk; segmenting meta-analysis (Rey et al. 2019, Bảng 3) không có moderator nào về cỡ đoạn theo số khái niệm | Không viện tâm lý học. Trình bày W là tham số thuật toán, mặc định 8, kèm ablation W ∈ {4,6,8,12} báo cáo số stage và τ |
| 6 | Trình bày stage như có cơ sở nhận thức; lộ trình cho mỗi khái niệm xuất hiện đúng một lần | Bằng chứng mạnh nhất trong mục này là **distributed practice** (Donoghue & Hattie 2021: d = 0.85, 152.952 người), không phải interleaving (d = 0.47, 972 người, I² = 88). Một lượt-một-lần là massed practice | Thêm Limitations: A10 sinh **thứ tự trình bày**, không phải **lịch luyện tập**; lớp ôn tập giãn cách nằm ngoài phạm vi. Nếu sau này sinh bài tập thì phải xen kẽ chéo stage (Rohrer et al. 2014: 72% vs 38%, d = 1.05, n = 140) |
| 7 | "Tầng 1 phình" bị coi là vấn đề của A10 | Xếp tầng đường dài nhất **theo thiết kế** đẩy mọi node in-degree 0 vào tầng 1 (Rüegg et al. 2016 §2; NetworkX `topological_generations`). Nguyên nhân thực là thiếu cạnh: PRELEARN 2020, F1 cross-domain tốt nhất 0.690 vs in-domain 0.887 | (a) Chữa triệu chứng ngay bằng bước `balance()` kiểu Graphviz (`ns.c: TB_balance`, "move to less populated ranks") — rẻ, không đổi tính hợp lệ. (b) Chữa gốc ở A8: đo recall trên một mẫu vàng, báo cáo nó, và quy tầng-1-phình về recall chứ không về A10 |
| 8 | Gọi sản phẩm là "learning path" | KST Định nghĩa 45 (Doignon & Falmagne 2015): learning path = **xích cực đại các trạng thái**, gradation có đúng `1+\|Q\|` trạng thái — không phải phân hoạch thành stage | Đổi tên sản phẩm (ví dụ "study plan" / "staged concept sequence"), hoặc giữ tên nhưng nêu rõ nó là **một** gradation được đóng gói, kèm trích Định nghĩa 45 |
| 9 | Nền mô hình: đồ thị tiên quyết = thứ tự bộ phận trên khái niệm | Birkhoff 1937 (qua Doignon & Falmagne 2015, Định lý 10): thứ tự bộ phận ↔ quasi ordinal space, và ngay sau đó: *"the closure under intersection does not make good pedagogical sense"*. Learning space chỉ đóng dưới hợp (Định lý 7). Bằng chứng ALEKS: outer fringe cho xác suất học thành công trung vị .93 trên 1.940.473 lượt | Thêm vào Limitations, có trích dẫn. Không cần đổi mô hình (thiếu dữ liệu học viên), nhưng phải thừa nhận, nếu không là bỏ qua phản chứng đã công bố |
| 10 | LLM chỉ được sắp trong stage (điểm 5) — đúng nhưng chưa đủ chặt | Position bias: đảo thứ tự đầu vào làm τ giữa hai đầu ra tụt còn 0.6358 / 0.6986 (arXiv:2608.03091, Bảng 1, K=25, zero-shot) | Giữ nguyên khoá phạm vi (có nguồn ủng hộ). Thêm: nạp khái niệm theo thứ tự chuẩn tắc, **hoặc** chạy k hoán vị + tổng hợp Kemeny và **báo cáo LOC** như chỉ số ổn định của A10 |
| 11 | Co SCC, cả khối vào một tầng (điểm 1) | Gansner et al. 1993 §2.1 nêu rõ họ **cố ý không** "placing the nodes in a cycle on the same rank"; feedback arc set là NP-complete | Phản chứng yếu (lý do của họ là bản vẽ, không phải sư phạm) — giữ được. Nhưng phải: (i) xử lý tường minh SCC lớn hơn trần W; (ii) báo cáo phân bố kích thước SCC sau A9 |
| 12 | Phân biệt node "đã xét, không thấy tiên quyết" với node "chưa từng xét" (điểm 3) | Không tìm thấy tiền lệ trong văn liệu giáo dục | Giữ — đây là thực hành đúng. Nâng lên thành đóng góp nhỏ bằng cách **báo cáo con số**: tỉ lệ node chưa từng nằm trong phiên suy luận nào, kèm ngưỡng chặn |
| 13 | Gắn node media vào stage của khái niệm sớm nhất (điểm 4) | Không có nguồn ủng hộ lẫn phản bác | Không sửa. Ghi là heuristic kỹ thuật, không tuyên bố gì thêm |

---

## Nguồn

### Vẽ đồ thị phân tầng và mã nguồn

1. Sugiyama, K., Tagawa, S., Toda, M. (1981). *Methods for Visual Understanding of Hierarchical System Structures*. IEEE Transactions on Systems, Man and Cybernetics 11(2):109–125. https://www.semanticscholar.org/paper/34c4e6af91b25f426fde84d1c4556256f07e6e81 *(chỉ tiếp cận được metadata + mô tả thứ cấp)*
2. Gansner, E.R., Koutsofios, E., North, S.C., Vo, K.-P. (1993). *A Technique for Drawing Directed Graphs*. IEEE Transactions on Software Engineering 19(3):214–230. https://www.graphviz.org/documentation/TSE93.pdf *(đọc toàn văn)*
3. Coffman, E.G. Jr., Graham, R.L. (1972). *Optimal scheduling for two-processor systems*. Acta Informatica 1:200–213. https://doi.org/10.1007/BF00288685 *(theo abstract)*
4. Lam, S., Sethi, R. (1977). *Worst Case Analysis of Two Scheduling Algorithms*. SIAM Journal on Computing 6(3):518–536. https://epubs.siam.org/doi/10.1137/0206037 *(theo mô tả thứ cấp; không tiếp cận được toàn văn)*
5. Braschi, B., Trystram, D. (1994). *A New Insight into the Coffman–Graham Algorithm*. SIAM Journal on Computing 23(3):662–669. https://epubs.siam.org/doi/10.1137/S0097539790181889 *(theo abstract)*
6. Healy, P., Nikolov, N.S. (2002). *How to Layer a Directed Acyclic Graph*. GD'01, LNCS 2265, Springer. https://link.springer.com/chapter/10.1007/3-540-45848-4_2 *(theo abstract + mô tả trong [8])*
7. Nikolov, N.S., Tarassov, A., Branke, J. (2005). *In search for efficient heuristics for minimum-width graph layering with consideration of dummy nodes*. ACM Journal of Experimental Algorithmics 10. https://doi.org/10.1145/1064546.1180618 *(theo abstract)*
8. Rüegg, U., Ehlers, T., Spönemann, M., von Hanxleden, R. (2016). *A Generalization of the Directed Graph Layering Problem*. GD'16, LNCS. arXiv:1608.07809. https://arxiv.org/pdf/1608.07809 *(đọc toàn văn)*
9. Mallach, S. (2019). *A Natural Quadratic Approach to the Generalized Graph Layering Problem*. GD 2019. arXiv:1908.04104. https://arxiv.org/pdf/1908.04104 *(đọc toàn văn)*
10. Nikolov, N.S., Tarassov, A. (2006). *Graph layering by promotion of nodes*. Discrete Applied Mathematics 154(5):848–860. https://www.sciencedirect.com/science/article/pii/S0166218X05003100 *(theo abstract)*
11. NetworkX, mã nguồn: `networkx/algorithms/dag.py`, hàm `topological_generations`, `antichain_width`. https://raw.githubusercontent.com/networkx/networkx/main/networkx/algorithms/dag.py *(đọc mã)*
12. OGDF, mã nguồn: `include/ogdf/layered/CoffmanGrahamRanking.h`. https://raw.githubusercontent.com/ogdf/ogdf/master/include/ogdf/layered/CoffmanGrahamRanking.h *(đọc mã)*
13. Graphviz, mã nguồn: `lib/common/ns.c`, hàm `TB_balance`. https://raw.githubusercontent.com/ellson/graphviz/master/lib/common/ns.c *(đọc mã)*
14. Kahn, A.B. (1962). *Topological sorting of large networks*. Communications of the ACM 5(11):558–562. https://dl.acm.org/doi/10.1145/368996.369025 *(theo metadata)*

### Lập lịch có ràng buộc thứ tự

15. Ullman, J.D. (1975). *NP-complete scheduling problems*. Journal of Computer and System Sciences 10(3):384–393. https://dl.acm.org/doi/10.1016/S0022-0000(75)80008-0 *(bản PDF tiếp cận được là ảnh quét, không trích được; dùng qua [17])*
16. Lenstra, J.K., Rinnooy Kan, A.H.G. (1978). *Complexity of scheduling under precedence constraints*. Operations Research 26(1):22–35. *(qua [17], thư mục Ch.2)*
17. Lawler, E.L., Lenstra, J.K., Rinnooy Kan, A.H.G., Shmoys, D.B. và cộng sự (2020). *Elements of Scheduling*. arXiv:2001.06005. https://arxiv.org/pdf/2001.06005 *(đọc toàn văn; Định lý 2.21, Định lý 2.27, thư mục Ch.2)*
18. Svensson, O. (2010). *Conditional hardness of precedence constrained scheduling on identical machines*. STOC 2010. https://dl.acm.org/doi/10.1145/1806689.1806791 — bản tạp chí: SIAM Journal on Computing 40(5). https://epubs.siam.org/doi/10.1137/100810502 *(theo abstract)*
19. Nederlof, J., Swennenhuis, C.M.F., Węgrzycki, K. (2023). *A Subexponential Time Algorithm for Makespan Scheduling of Unit Jobs with Precedence Constraints*. arXiv:2312.03495. https://arxiv.org/abs/2312.03495 *(theo abstract + §1)*

### Knowledge Space Theory

20. Doignon, J.-P., Falmagne, J.-C. (2015). *Knowledge Spaces and Learning Spaces*. arXiv:1511.06757. https://arxiv.org/pdf/1511.06757 *(đọc toàn văn; Đ.nghĩa 5, 9, 20, 45; Đ.lý 7, 10, 21, 46; §12.2–12.4)*
21. Birkhoff, G. (1937). *(qua [20], Định lý 10)*
22. Cosyn, E. và cộng sự (2013). *(qua [20], §12.3: trung vị .93 trên 1.940.473 lượt học)*
23. Ahlgren, A., Harper, M. (2013). *ALEKS-based Placement at the University of Illinois*. *(qua [20], §12.4, Bảng 7)*
24. Meinke, J.G., Bauer, C.R. *Topological sorting as a tool in curriculum planning*. ACM. https://dl.acm.org/doi/pdf/10.1145/800144.804757 *(ACM DL trả 403; chỉ tiếp cận được tiêu đề + mô tả thứ cấp)*

### Trích quan hệ tiên quyết và đánh giá thứ tự

25. Lapata, M. (2006). *Automatic Evaluation of Information Ordering: Kendall's Tau*. Computational Linguistics 32(4):471–484. https://aclanthology.org/J06-4002/ *(đọc toàn văn)*
26. Alzetta, C., Miaschi, A., Dell'Orletta, F., Koceva, F., Torre, I. (2020). *PRELEARN @ EVALITA 2020: Overview of the Prerequisite Relation Learning Task for Italian*. EVALITA 2020, tr. 325–332. https://aclanthology.org/2020.evalita-1.54/ *(đọc toàn văn)*
27. Liang, C. và cộng sự (2018). *Active Learning of Strict Partial Orders: A Case Study on Concept Prerequisite Relations* (bộ dữ liệu AL-CPL). arXiv:1801.06481. https://arxiv.org/pdf/1801.06481 *(qua [26]; tiếp cận được tiêu đề/abstract)*
28. *Prerequisite Relation Learning: A Survey and Outlook*. ACM Computing Surveys (2025). https://dl.acm.org/doi/10.1145/3733593 *(ACM DL trả 403; chỉ tiếp cận được mô tả thứ cấp)*

### Curriculum sequencing / learning path recommendation

29. Vanderlei Freitas và cộng sự (2021). *Metaheuristic-based adaptive curriculum sequencing approaches: a systematic review and mapping of the literature*. Artificial Intelligence Review 54:711–754. https://link.springer.com/article/10.1007/s10462-020-09864-z *(theo abstract + mô tả thứ cấp: 61 mapping / 58 review, 2005–2018)*
30. *A comparative analysis of metaheuristics applied to adaptive curriculum sequencing*. Soft Computing (2021). https://pmc.ncbi.nlm.nih.gov/articles/PMC8099996/ *(đọc toàn văn qua PMC)*
31. Rahayu, N.W., Ferdiana, R., Kusumawardani, S.S. (2023). *A systematic review of learning path recommender systems*. Education and Information Technologies 28:7437–7460. https://link.springer.com/article/10.1007/s10639-022-11460-3 *(Springer chặn; chỉ tiếp cận được mô tả thứ cấp)*
32. Cheng, X., Zhang, Z., Wang, J., Fang, L., He, C., Guan, Q., Pan, S., Luo, W. (2025). *Education-Oriented Graph Retrieval-Augmented Generation for Learning Path Recommendation*. arXiv:2506.22303. https://arxiv.org/html/2506.22303v1 *(đọc bản HTML)*
33. *LLM-Assisted Knowledge Graph Completion for Curriculum and Domain Modelling in Personalized Higher Education Recommendations*. arXiv:2501.12300. https://arxiv.org/abs/2501.12300 *(theo abstract)*

### Tâm lý học nhận thức và thiết kế mô-đun

34. Miller, G.A. (1956). *The Magical Number Seven, Plus or Minus Two*. Psychological Review 63(2):81–97. https://psychclassics.yorku.ca/Miller/
35. Cowan, N. (2001). *The magical number 4 in short-term memory: A reconsideration of mental storage capacity*. Behavioral and Brain Sciences 24(1):87–114. https://philpapers.org/rec/COWTMN *(theo abstract)*
36. Rey, G.D., Beege, M., Nebel, S., Wirzberger, M., Schmitt, T.H., Schneider, S. (2019). *A Meta-analysis of the Segmenting Effect*. Educational Psychology Review 31:389–419. https://link.springer.com/article/10.1007/s10648-018-9456-4 *(đọc toàn văn; Bảng 3)*
37. Rohrer, D., Dedrick, R.F., Burgess, K. (2014). *The benefit of interleaved mathematics practice is not limited to superficially similar kinds of problems*. Psychonomic Bulletin & Review 21:1323–1330. https://gwern.net/doc/psychology/spaced-repetition/2014-rohrer.pdf *(đọc toàn văn)*
38. Rohrer, D., Taylor, K. (2007). *The shuffling of mathematics problems improves learning*. Instructional Science 35(6):481–498. https://doi.org/10.1007/s11251-007-9015-8 *(theo abstract; máy chủ USF từ chối kết nối)*
39. Dunlosky, J., Rawson, K.A., Marsh, E.J., Nathan, M.J., Willingham, D.T. (2013). *Improving Students' Learning With Effective Learning Techniques: Promising Directions From Cognitive and Educational Psychology*. Psychological Science in the Public Interest 14(1):4–58. https://journals.sagepub.com/doi/10.1177/1529100612453266 *(theo trang tóm tắt APS + qua [40])*
40. Donoghue, G.M., Hattie, J.A.C. (2021). *A Meta-Analysis of Ten Learning Techniques*. Frontiers in Education 6:581216. https://www.frontiersin.org/journals/education/articles/10.3389/feduc.2021.581216/full *(đọc toàn văn HTML; bảng tổng hợp hiệu ứng)*

### Độ khó và cấu trúc chương trình

41. Zuev, K., Stavrinides, P. (2025). *Breadth, Depth, and Flux of Course-Prerequisite Networks*. arXiv:2506.23510. https://arxiv.org/pdf/2506.23510 *(đọc toàn văn; §IV, §V.B)*
42. Baucks, F., Schmucker, R., Wiskott, L. (2025). *The Course Difficulty Analysis Cookbook*. arXiv:2508.13218. https://arxiv.org/abs/2508.13218 *(theo abstract)*
43. Paz, H.R. (2025). *The Topology of Hardship: Empirical Curriculum Graphs and Structural Bottlenecks in Engineering Degrees*. arXiv:2512.05561. https://arxiv.org/abs/2512.05561 *(theo abstract)*

### Tính bất ổn thứ tự của LLM

44. *Position Bias Undermines Preference Consistency in Listwise LLM-Based Reranking*. arXiv:2608.03091. https://arxiv.org/html/2608.03091 *(đọc bản HTML; Bảng 1)*
45. *One Pass, Any Order: Position-Invariant Listwise Reranking for LLM-Based Recommendation*. arXiv:2604.27599. https://arxiv.org/pdf/2604.27599 *(theo abstract)*
46. *Ranked by Position: Order Sensitivity as an Exploitable Attack Surface in LLM Listwise Recommenders*. arXiv:2607.24869. https://arxiv.org/html/2607.24869v1 *(theo abstract)*
