# Nghiên cứu A9–A10 — Kiểm tra nhất quán đồ thị tiên quyết và sinh lộ trình học

Vòng 36 · 2026-09-21 · Đối tượng: `doc/spec-addendum.md` §513–§590 (A9, A10, A12), `doc/A6-A8-cum-chu-de-mention-map-va-tien-quyet-spec.md` D11–D12, và **mã đã chạy thật** (`domain/global_validation.py`, `domain/roadmap.py`, `use_cases/validate_graph.py`, `use_cases/build_roadmap.py`).

Đây là **đợt nghiên cứu riêng cho A10** mà chủ dự án đã hẹn khi chốt phạm vi ngày 2026-09-17 ("A10 chỉ là bản tối
thiểu, thiết kế chưa chốt, cần một đợt nghiên cứu riêng **sau** đợt này"). Nó gộp luôn A9 vì hai bước ràng nhau:
thứ tự thực hiện của A9 quyết định A10 có chạy được không.

Khác với vòng 29, lần này A9 và A10 **đã có mã và đã chạy trên bốn tài liệu phát triển**. Nên báo cáo có hai nửa
không trộn vào nhau: **nửa đo** là số lấy thẳng từ artifact trên đĩa, **nửa đọc** là văn liệu. Mọi đề xuất ở cuối
phải chỉ được về một trong hai nửa; đề xuất nào không chỉ được thì ghi rõ là suy đoán.

**Quy ước ba loại câu** (giữ từ các báo cáo trước): sự thật từ nguồn luôn kèm tên công trình, năm, nơi công bố và
số hiệu `[n]` trỏ về mục *Nguồn*; **số đo dự án** ghi rõ artifact nào, phiên bản nào; câu mở đầu bằng *Suy luận:*
là ý kiến người viết. Con số lấy từ toàn văn trừ chỗ ghi *(theo abstract)*. Không lời gọi API mô hình hay embedding
nào trong đợt này.

**Hai phụ lục** giữ nguyên văn bản khảo sát văn liệu chi tiết, để tra cứu trích dẫn và để kiểm lại khi viết bài
báo: [`nghien-cuu-a9-van-lieu-chi-tiet.md`](./nghien-cuu-a9-van-lieu-chi-tiet.md) (377 dòng, 29 nguồn) và
[`nghien-cuu-a10-van-lieu-chi-tiet.md`](./nghien-cuu-a10-van-lieu-chi-tiet.md) (593 dòng, 46 nguồn). Mỗi phụ lục
mở đầu bằng ghi chú biên tập nói rõ chỗ nào đã được đính chính sau khi đối chiếu với mã. **Báo cáo này là bản có
thẩm quyền; phụ lục là tư liệu** — chỗ nào hai bên khác nhau thì theo bản này.

---

## Tóm tắt

- **Trần 5–8 khái niệm mỗi stage chưa bao giờ bị chạm.** `xstk-ch3-1` có 98 khái niệm chia thành **63 stage, 39
  stage chỉ một khái niệm**; cỡ stage lớn nhất toàn corpus là 5. Nguyên nhân là cấu trúc: `stage = tầng ∩ cụm` là
  giao của hai phân hoạch (13 tầng × 12 cụm = 156 ô lưới cho 98 khái niệm). Từng phân hoạch riêng đều hợp lý — 12
  cụm cho 98 khái niệm là trung bình 8 mỗi cụm, đúng khoảng spec muốn. Chỉ phép giao là hỏng.
- **Bài toán A10 đang giải có tên và đã NP-khó từ 1975.** "Xếp tầng với trần W phần tử, tối thiểu số tầng" chính là
  `P|prec, p_j=1|C_max` [30][31]; không xấp xỉ được dưới 4/3 [31]. Thuật toán chuẩn là **Coffman–Graham 1972** với
  cận (2 − 2/W) [33][34], đã cài sẵn trong OGDF với tham số `width(int)` [35]. Cắt tầng theo cụm chủ đề **không có
  bảo đảm nào**, và **không tìm thấy nguồn nào** từng đề xuất hay đánh giá "giao của tầng với cụm cộng đồng" làm
  đơn vị mô-đun.
- **Bỏ phép giao cụm không mất gì đo được**: mô phỏng trên chính artifact cho τ gần như không đổi (0,11 → 0,08),
  số stage giảm 63 → 19. Thêm trần độ rộng: 63 → 16 stage, tầng 1 tụt từ 12 xuống 8 khái niệm, **vẫn giữ bất biến
  "không cạnh tiên quyết nào nằm gọn trong một stage"**.
- **Lộ trình hiện tại xáo trộn thứ tự giáo trình gần như toàn bộ**: trùng thứ tự sách ở 51,0% số cặp trên
  `baocao-canhan` — không phân biệt được với tung đồng xu. Dùng bộ vàng hội ý để tách nguyên nhân: trên cùng 37
  khái niệm, **cạnh vàng cho τ +0,803, cạnh máy cho τ +0,603**, và **11/62 cạnh vàng bị lộ trình máy xếp ngược**.
- **Chỉ số đánh giá đã có sẵn và có nền thực nghiệm**: Kendall τ so với thứ tự trình bày (Lapata 2006 [41]: τ tương
  quan r = 0,45 với phán đoán người, r = −0,48 với thời gian đọc, trong khi đồng thuận giữa người với người chỉ
  r = 0,56). **Không tìm thấy công trình nào** dùng τ để so lộ trình khái niệm do LLM sinh với mục lục giáo trình
  gốc — đây là chỗ đóng góp rõ nhất của dự án.
- **Một bẫy thí nghiệm dự án đang tự đặt**: D12 dùng thứ tự chương để phá thế hoà giữa các stage cùng tầng, rồi lại
  định dùng thứ tự chương làm đối chứng τ. Phải đổi tiêu chí phá thế hoà, nếu không đối chứng bị nhiễm.
- **Lý lẽ giữ chu trình hai cạnh dựa trên một tiền đề sai.** Con số ~4% là đúng (LectureBank 2.0 có 30 cặp hai
  chiều = 3,87% số cạnh [7][8]), nhưng tác giả **không** coi đó là quan hệ hợp lệ — họ viết rằng các cặp ấy gợi ý
  "we may combine these pairs into a single concept" [7]. KST nói mạnh hơn: A↔B kéo theo K_A = K_B, **đúng định
  nghĩa mất tính discriminative** [13], và thao tác chuẩn là gộp thành một *notion* [15].
- **Cổng chất lượng 0,5 cạnh/node và 60% cô lập không đứng được như một hằng số phổ quát**: mạng tiên quyết môn học
  của Johns Hopkins có **0,340 cạnh/node** [5] và **77,7% node cô lập**, tức kích hoạt cả hai cổng. Nhưng đó là đồ
  thị *môn học*, không phải đồ thị *khái niệm* — xem mục 5.2 để biết chỗ phản bác này áp được và chỗ không.
- **Confidence LLM tự khai nên bỏ hẳn, không chỉ xếp cuối.** Đo trên corpus: cả **327 cạnh** chỉ nhận ba giá trị
  0,7 · 0,8 · 0,9. Văn liệu khớp đúng: Xiong và cộng sự (ICLR 2024) [25] đo AUROC trung bình 51,3 / 52,5 / 56,4 /
  55,1 / 62,7 trên năm mô hình — ba mô hình đầu không phân biệt nổi đúng với sai, và giá trị dồn vào dải 80–100%.
- **Cách gọi tên phải sửa ở hai chỗ.** "Kiểm định" (validation) trong văn liệu nghĩa là kiểm định trên biểu hiện
  học viên [20]–[24]; A9 không làm thế, nên phải gọi là **kiểm tra nhất quán cấu trúc**. Và "learning path" trong
  KST có định nghĩa hình thức là **xích cực đại các trạng thái tri thức** [13], không phải một phân hoạch thành
  stage.

---

## 1. Hiện trạng: A9 và A10 thực sự đang làm gì

Bảng dưới đối chiếu **ba cột**: luật trong `spec-addendum` (bản B0 cũ), luật trong spec A6–A8 (D11/D12, mới hơn và
đã đè lên bản cũ), và **mã đang chạy**. Cột thứ ba có thẩm quyền về hành vi thật.

### 1.1 A9

| # | `spec-addendum` A9 | D11 (mới hơn) | Mã đang chạy | Khớp? |
|---|---|---|---|---|
| 1 | Cổng: cạnh < 0,5 × node học được **hoặc** > 60% cô lập → fallback | như cũ | `len(marked) >= 0.5 * len(learnable) and ratio <= 0.6` | ✅ |
| 2 | Gỡ chu trình: Tarjan SCC, **cắt cạnh `confidence` thấp nhất** | **vét cạn trong SCC**, ưu tiên giữ theo bằng chứng → thứ tự → số nguồn → confidence | `_feedback_edges`: vét cạn nếu ≤ **16 cạnh nội bộ**, ngược lại heuristic kiểu Eades–Lin–Smyth có trọng số | ⚠️ addendum **lỗi thời**; mã có một nhánh xấp xỉ mà **D11 không nhắc tới** |
| 3 | Transitive reduction: **xoá** cạnh dư | **chỉ đánh dấu** `redundant_via` | `_alternate_path` → gắn `redundant_via`, giữ cạnh | ⚠️ addendum **lỗi thời**; D11 và mã khớp |
| 4 | — | Chu trình hai cạnh được **giữ**, gắn cờ, không tính vào cổng | đúng vậy; SCC ≥ 3 node mới bị gỡ cạnh | ✅ |
| 5 | — | Chuẩn hoá sổ đăng ký kiểu, không tự quy về `requires` | `_type_registry` + cờ `singleton_edge_type` | ✅ |
| 6 | — | Xử lý tồn đọng | `backlog` + `apply_resolved_nodes` | ✅ |

### 1.2 A10

| # | `spec-addendum` A10 | D12 (mới hơn) | Mã đang chạy | Khớp? |
|---|---|---|---|---|
| 1 | Kahn, lớp 1 = in-degree 0 | Kahn **trên đồ thị co**, tầng theo **đường dài nhất** | `_kahn` dùng `max(layers[target], layers[source]+1)`; `_contracted_layers` co SCC | ✅ |
| 2 | Stage = layer ∩ cluster, trần 5–8 | như cũ | `grouped[(layer, cluster_id)]` rồi cắt lát; `stage_cap` ép `int` trong `[5, 8]` | ✅ |
| 3 | Media về stage của node học được sớm nhất | như cũ | **không có** — `build_roadmap` chỉ nhận node `learnable` | ❌ chưa làm |
| 4 | **Lượt LLM cuối** đặt tên stage | D12 không nhắc | **không có** — stage chỉ có `stage_id` băm | ❌ chưa làm |
| 5 | — | Phân biệt "đã xét, không thấy tiên quyết" với "chưa từng xét" | `coverage_status` ba giá trị + cờ `unreviewed_learnable_node` | ✅ |
| 6 | — | Trang xem tĩnh | `render_roadmap_html` | ✅ |
| 7 | Độ khó tính từ độ sâu DAG (§432) | — | **không có** trường độ khó nào | ❌ chưa làm |

**Ba chỗ spec nói mà mã chưa làm** (#3, #4, #7) không phải lỗi của ai — vé 09 cố ý làm bản tối thiểu. Nhưng chúng
phải được **gỡ khỏi spec hoặc cắt thành vé**, chứ không để spec mô tả một hệ thống không tồn tại. Xem Đ9 và Đ12.

**Hai chỗ `spec-addendum` lỗi thời** (A9 #2 và #3) nguy hiểm hơn: người đọc sẽ tin dự án cắt cạnh theo confidence
thấp nhất và xoá cạnh bắc cầu — cả hai đều **ngược** hành vi thật.

---

## 2. Số đo thật trên bốn tài liệu phát triển

Nguồn: artifact `graph` stage `stages` mới nhất của từng tài liệu — `baocao-canhan/v89`, `naive-bayes/v19`,
`nhap-mon-ml/v19`, `xstk-ch3-1/v19`. Chỉ đọc đĩa.

| tài liệu | node | cạnh | cạnh/node | cạnh thừa | cạnh/node trừ thừa | cô lập | tầng | tầng 1 | stage | stage 1 khái niệm | τ so sách |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `baocao-canhan` | 36 | 25 | 0,69 | 2 (8,0%) | 0,64 | 0,14 | 6 | **47%** | 22 | **14/22** | **0,02** |
| `naive-bayes` | 34 | 38 | 1,12 | 9 (23,7%) | 0,85 | 0,26 | 6 | **53%** | 16 | 7/16 | 0,16 |
| `nhap-mon-ml` | 75 | 84 | 1,12 | 11 (13,1%) | 0,97 | 0,11 | 9 | 21% | 43 | **24/43** | 0,53 |
| `xstk-ch3-1` | 98 | 180 | 1,84 | 51 (28,3%) | 1,32 | 0,06 | 13 | 12% | 63 | **39/63** | 0,11 |

### 2.1 Cổng chất lượng chưa bao giờ suýt đóng — và nó đếm cả cạnh thừa

Cả bốn qua cổng. Nhánh cô lập cách ngưỡng rất xa (cao nhất 0,26 so với trần 0,60). Nhánh mật độ sát hơn:
`baocao-canhan` ở 0,69 so với sàn 0,50.

Tử số của cổng là `len(marked)`, **tính cả cạnh đã đánh dấu `redundant_via`**. Trên `xstk-ch3-1`, 51/180 cạnh là
bắc cầu thừa. *Suy luận:* cổng đo "tài liệu này có cấu trúc tiên quyết không", mà một cạnh suy ra được từ hai cạnh
khác **không thêm cấu trúc nào**. Một đồ thị gần đóng bắc cầu sẽ qua cổng dễ dàng dù cấu trúc thật rất mỏng.

### 2.2 Chu trình hiếm, và nhánh xấp xỉ chưa bao giờ chạy

Chỉ `baocao-canhan` có chu trình: **2 SCC** (3 node và 4 node), gỡ **4 cạnh**, cả hai giải bằng nhánh **vét cạn**.
Nhánh heuristic `eades_priority` **chưa bao giờ chạy trên dữ liệu thật**.

Một cờ `two_way_requires`: cặp **ERD ↔ Thiết kế Cơ sở dữ liệu**, bằng chứng `trong_dinh_nghia` cả hai chiều, được
co lại và cùng nằm ở tầng 1. *Suy luận:* đúng là ca "bộ phận–toàn thể bị đoán ngược" mà F88 mô tả — ERD là một
phần của thiết kế CSDL, không phải tiên quyết của nó. Cơ chế giữ cạnh hai chiều đang **bảo vệ một cặp sai**, và
cái nó bảo vệ là **lỗi kiểu quan hệ**, không phải "mâu thuẫn hợp lệ". Xem mục 5.3.

### 2.3 Stage vỡ vụn — trần 5–8 chưa bao giờ chạm tới

Phát hiện nặng nhất của phần đo, và nó **ngược hẳn** nỗi lo trong spec.

Spec sợ tầng quá lớn nên đặt trần 5–8 và cắt theo cụm. Thực tế trần **chưa bao giờ bị chạm**: `xstk-ch3-1` có 98
khái niệm → **63 stage**, **39 stage một khái niệm**; `nhap-mon-ml` 75 → 43 stage, 24 đơn lẻ. Cỡ stage lớn nhất
toàn corpus là **5**.

Lý do cấu trúc: `stage = tầng ∩ cụm` là **giao của hai phân hoạch**, và giao của hai phân hoạch hợp lý vẫn ra một
phân hoạch vụn. Trên `xstk-ch3-1`: 13 tầng × 12 cụm = **156 ô lưới** cho 98 khái niệm, 63 ô có người ở.

Từng phân hoạch riêng lẻ **đều hợp lý**. Cỡ cụm của bốn tài liệu: 8/6/6/5/4/4 · 10/6/6/5/4/3 · 9/8/8/7/7/6 ·
12/12/12/11/9/9 — tức trung bình 6–8 khái niệm mỗi cụm, **đúng ngay khoảng spec muốn**. Chỉ phép giao là hỏng.

*Suy luận:* "lộ trình 63 chặng cho 98 khái niệm" không phải lộ trình học, nó là danh sách khái niệm có đánh số.
Trần 5–8 hiện là **trần trên một thứ không bao giờ đạt tới**; thứ thiếu là **sàn**, hoặc một thuật toán gom có
ràng buộc độ rộng thay vì phép giao.

### 2.4 "Tầng 1 phình" có thật, nhưng chỉ ở tài liệu nhỏ

47% và 53% khái niệm rơi vào tầng 1 ở hai tài liệu nhỏ; 21% và 12% ở hai tài liệu lớn. *Suy luận:* tương quan
nghịch với mật độ cạnh cho thấy đây là **triệu chứng của độ phủ cạnh thấp**, không phải của thuật toán xếp tầng.
Với `baocao-canhan`, 15/17 node tầng 1 mang `coverage_status = reviewed_no_prerequisite` — **đã xét và không tìm
thấy**, chứ không phải bỏ sót. Cơ chế phân biệt của D12 hoạt động đúng và trả lời được câu hỏi này; đó là một điểm
thiết kế đứng vững (xem mục 6.6).

### 2.5 Lộ trình sinh ra gần như không liên quan tới thứ tự của chính giáo trình

Chỉ số: với mọi cặp khái niệm ở **hai stage khác nhau** và có **thứ tự trình bày khác nhau**, đếm xem thứ tự lộ
trình có trùng thứ tự sách không (τ Kendall trên các cặp so được; cặp hoà bị loại).

| tài liệu | cặp so được | thuận | nghịch | tỉ lệ thuận | τ |
|---|---|---|---|---|---|
| `baocao-canhan` | 578 | 295 | 283 | **0,510** | 0,021 |
| `naive-bayes` | 517 | 300 | 217 | 0,580 | 0,161 |
| `nhap-mon-ml` | 2 626 | 2 003 | 623 | 0,763 | 0,526 |
| `xstk-ch3-1` | 4 640 | 2 575 | 2 065 | 0,555 | 0,110 |

Trên `baocao-canhan`, lộ trình trùng thứ tự sách ở **51,0%** số cặp — không phân biệt được với tung đồng xu.

**Cảnh báo bắt buộc khi đọc con số này:** thứ tự stage hiện được sắp theo `(tầng, first_order_index, cụm, phần)`,
tức **trong một tầng thì thứ tự sách đã được chép sẵn vào kết quả**. τ ở trên vì vậy **thiên về phía đồng thuận**;
phần bất đồng thật còn lớn hơn. Đây chính là cái bẫy mà mục 6.4 nói tới, và nó phải được sửa trước khi τ thành chỉ
số chính thức.

Nói cho đúng: **thứ tự sách không phải chân lý**. Một giáo trình có thể trình bày theo mạch sư phạm khác mạch tiên
quyết. Nên con số thấp **không chứng minh lộ trình sai** — nhưng nó chứng minh lộ trình là một **xáo trộn gần như
toàn bộ**, và chưa ai kiểm xáo trộn ấy.

### 2.6 Độ tin cậy mô hình tự khai chỉ có ba giá trị

Trên cả **327 cạnh** của bốn tài liệu, `confidence` chỉ nhận **0,7 · 0,8 · 0,9**; không cạnh nào dưới 0,7 hay trên
0,9; 0,9 chiếm 68% · 74% · 64% · 87%.

`evidence_kind` cũng gần suy biến theo hướng khác: `trong_dinh_nghia` chiếm 76% · 84% · 71% · 88%; `noi_ro` chỉ có
2 · 5 · 3 · 13 cạnh.

*Suy luận:* D11 quyết định **không** lấy confidence làm tiêu chí đầu, và số đo ủng hộ mạnh hơn cả lý lẽ ban đầu.
Nhưng nó cũng cho thấy tiêu chí **đầu tiên** của D11 (`evidence_kind`) cũng gần suy biến — thứ thật sự phân biệt là
tiêu chí thứ hai và thứ ba (`order_relation`, số nguồn độc lập).

Một con số phụ: cạnh **ngược thứ tự trình bày** chiếm 16% · 24% · 11% · 9%. Giáo trình vi phạm thứ tự tiên quyết
của chính nó ở khoảng một phần mười số cạnh — có thật, nhưng **không đủ** để giải thích τ ở mục 2.5.

### 2.7 Mô phỏng: bốn cách gom stage trên cùng dữ liệu

Bốn cách, cùng artifact, cùng bước co SCC, trần 8 khái niệm:

- **A** — hiện tại: tầng theo đường dài nhất ∩ cụm chủ đề.
- **B** — bỏ phép giao cụm: stage = tầng, trong tầng sắp theo thứ tự sách rồi cắt lát.
- **C** — xếp tầng **có trần độ rộng** (duyệt tô-pô, đặt vào tầng sớm nhất còn chỗ), stage = tầng. *Đây là list
  scheduling ưu tiên theo độ sâu, **không phải** Coffman–Graham đầy đủ — xem Đ2.*
- **D** — **bỏ tầng**: sắp tô-pô tham lam **ưu tiên thứ tự sách**, chỉ dời khi có cạnh buộc dời; cắt lát 8.

| | số stage | stage 1 khái niệm | cỡ trung bình | τ so sách | cạnh nằm gọn trong stage |
|---|---|---|---|---|---|
| **`xstk-ch3-1`** (98 khái niệm, 180 cạnh) | | | | | |
| A hiện tại | 63 | 39 (62%) | 1,6 | 0,11 | 0 |
| B bỏ giao cụm | 19 | 3 (16%) | 5,2 | 0,08 | — |
| C tầng có trần độ rộng | **16** | 3 (19%) | 6,1 | 0,10 | **0** |
| D theo sách trước | **13** | **0** | 7,5 | **0,98** | **62 (34%)** |
| **`nhap-mon-ml`** (75, 84) | | | | | |
| A | 43 | 24 (56%) | 1,7 | 0,53 | 0 |
| C | 12 | 3 (25%) | 6,2 | 0,56 | 0 |
| D | 10 | 0 | 7,5 | 0,83 | 33 (39%) |
| **`naive-bayes`** (34, 38) | | | | | |
| A | 16 | 7 (44%) | 2,1 | 0,16 | 0 |
| C | 7 | 2 (29%) | 4,9 | 0,19 | 0 |
| D | 5 | 0 | 6,8 | 0,83 | 24 (63%) |
| **`baocao-canhan`** (36, 25) | | | | | |
| A | 22 | 14 (64%) | 1,6 | 0,02 | 2 |
| C | 7 | 1 (14%) | 5,1 | 0,06 | 2 |
| D | 5 | 0 | 7,2 | 0,63 | 16 (64%) |

Ba điều đọc được, không cần văn liệu nào:

1. **Bỏ phép giao cụm không mất gì đo được.** τ gần như không đổi (0,11 → 0,08 → 0,10), số stage giảm ba đến bốn
   lần, stage đơn lẻ gần hết. Phép giao với cụm chủ đề đang **chỉ làm vụn**.
2. **Trần độ rộng giải đúng bài "tầng 1 phình".** Tầng 1 tụt 17→8, 18→8, 16→8, 12→8 khái niệm; tổng số tầng tăng
   nhẹ (6→7, 6→7, 9→12, 13→16); **vẫn giữ bất biến "không cạnh tiên quyết nào nằm gọn trong một stage"**.
3. **Thứ tự sách và phân tầng là đánh đổi thật, đo được cả hai phía.** D đạt τ 0,98 trên `xstk-ch3-1` nhưng **34%
   đến 64% cạnh tiên quyết rơi gọn vào trong một stage** — stage không còn là "nhóm học song song được". A và C giữ
   bất biến ấy gần như tuyệt đối.

Một kiểm tra cận dưới (mục 6.2 cho nguồn): mọi xếp tầng hợp lệ đều cần ít nhất `max(xích dài nhất, ⌈n/W⌉)` stage.
Với `xstk-ch3-1`: `max(13, ⌈98/8⌉ = 13) = 13`. **D đạt đúng 13 — tối ưu.** C cho 16, nằm trong cận (2 − 2/8)×13 =
22,75 của Coffman–Graham. **A cho 63, tức gấp gần năm lần cận dưới.**

*Suy luận:* **C là nâng cấp an toàn** — giữ mọi bất biến hiện có, sửa cả vụn stage lẫn tầng 1 phình, không mất gì.
**D là quyết định của chủ dự án**: nó đổi định nghĩa "stage" từ "nhóm độc lập" sang "chặng đọc tuần tự", và đó là
câu hỏi sư phạm chứ không phải câu hỏi kỹ thuật.

### 2.8 Cạnh vàng và cạnh máy dựng lộ trình trên cùng tập khái niệm

Bộ vàng dùng ở đây là **bộ vàng thử nghiệm** sau hội ý trên chương 10–13 của `xstk-ch3-1` (62 cạnh, hai người gán
độc lập rồi hội ý) — một **tài liệu phát triển**, không phải bộ vàng chính thức của đợt. Kết quả là **dấu hiệu,
không phải kết luận**.

Cùng 37 khái niệm, cùng thuật toán xếp tầng, chỉ đổi tập cạnh:

| tập cạnh | số cạnh | số tầng | tầng 1 | τ so thứ tự sách |
|---|---|---|---|---|
| **vàng (người gán)** | 62 | 10 | 14/37 | **+0,803** |
| **máy (A8 hiện tại)** | 59 | 7 | 10/37 | **+0,603** |

1. **Lộ trình dựng từ cạnh người gán vẫn bám khá sát thứ tự giáo trình** (τ 0,80) nhưng không trùng khít — giáo
   trình thật sự vi phạm thứ tự tiên quyết của chính nó, chỉ là ít.
2. **Lộ trình máy lệch xa gấp đôi** trên cùng phạm vi.
3. **11/62 cạnh vàng (18%) bị lộ trình máy xếp ngược** — máy đặt khái niệm tiên quyết **sau** khái niệm cần nó.
   Ví dụ: cần *Phân phối chuẩn* trước *Độ tin cậy của ước lượng*, máy xếp ngược.

Đếm thô mức trùng cạnh: 24 chung, 38 chỉ vàng có, 35 chỉ máy có. **Đây không phải số P/R của E3** — E3 chấm có tính
bắc cầu và theo kênh bằng chứng; con số thô này chỉ để định cỡ.

Và về chính giáo trình: trong 62 cạnh vàng, **44 (71,0%) thuận thứ tự trình bày, 9 (14,5%) cùng vị trí, 9 (14,5%)
đi ngược**. *Cảnh báo:* `first_order_index` ở mức chunk, và một phần "ngược" có thể đến từ chỗ provenance chọn làm
nơi dạy chứ không phải nơi khái niệm xuất hiện lần đầu.

### 2.9 Một lỗi nhỏ tìm thấy khi đo: cờ rỗng lọt vào trang duyệt

`nhap-mon-ml` có **hai cờ rỗng `{}`** trong `secondary_flags`. Chúng đi qua A9 thành `{"status": "unresolved"}`
không `kind`, không `node_id`, không lý do, rồi vào `display_flags` của trang xem. Không ai xử lý được một cờ như
vậy, và chúng làm phồng `validation_flag_count`.

Gốc: `domain/secondary.py:139` kiểm `isinstance(value.get("flags"), list)` — kiểm cái hộp, không kiểm cái bên
trong. → **F113**.

---

## 3. Gỡ chu trình: bài toán có tên, và chỗ mã của ta thật sự yếu

### 3.1 Đây là minimum feedback arc set, và nó NP-đầy đủ

Feedback arc set nằm trong danh sách 21 bài toán NP-đầy đủ của Karp [2]. Nó **APX-hard**: trừ khi P = NP không có
PTAS, và dưới giả thuyết Unique Games, với mọi C > 0 việc tìm xấp xỉ hệ số C là NP-hard [1] §1.1. Cận trên đơn
giản là m/2; Eades–Lin–Smyth cải thiện thành **m/2 − n/6** với thời gian và bộ nhớ tuyến tính [3].

Baharev và cộng sự [1] §1.1 định nghĩa tường minh bản **có trọng số**, và công thức quy hoạch nguyên của họ (biểu
thức (4), §3.2) nhận hệ số `c_ij` là trọng số cạnh. Thư viện `igraph` cài sẵn cả hai: `feedback_arc_set(graph,
weights, algo = "exact_ip" | "approx_eades")`, trong đó `exact_ip` "guarantees that the total weight of the removed
edges is as small as possible" [4]. **NetworkX không có hàm feedback arc set nào** — chỉ `simple_cycles`,
`condensation`, `transitive_reduction`, `is_directed_acyclic_graph`.

### 3.2 Chỗ phải đính chính về mã của ta

Khảo sát văn liệu kết luận rằng "vét cạn chết ở SCC 7 node / 21 cạnh" (đo bằng cách duyệt mọi tập con cạnh theo cỡ
tăng dần, ngân sách 10 giây). **Kết luận đó không mô tả đúng mã của dự án**, và tôi đã kiểm lại:
`_feedback_edges(component, internal, *, exhaustive_limit=16)` chặn theo **số cạnh nội bộ**, không theo số node.
Trên máy này:

| SCC | phương pháp mã chọn | thời gian |
|---|---|---|
| 4 node · 12 cạnh (đầy đủ) · gỡ 6 | `exhaustive` | 12,7 ms |
| 5 node · 16 cạnh · gỡ 8 | `exhaustive` | **216,9 ms** |
| 5 node · 20 cạnh (đầy đủ) · gỡ 10 | `eades_priority` | 0,2 ms |

Trần 16 cạnh chặn số tập con ở `2¹⁶ = 65 536`, nên vét cạn **không thể treo**. Vấn đề thật khác hẳn và vẫn nghiêm
trọng: **trên 16 cạnh, mã lặng lẽ chuyển sang nghiệm xấp xỉ**, và **D11 không hề nhắc tới nhánh đó**. Một báo cáo
khoa học nói "giải chu trình bằng tìm kiếm vét cạn" trong khi hệ thống có thể đang chạy heuristic là một tuyên bố
sai — kể cả khi trên corpus hiện tại nhánh ấy chưa bao giờ chạy.

### 3.3 Và chỗ văn liệu chỉ ra một cải tiến thật

Khoảng cách giữa hai đại lượng mới là điều đáng giá. SCC lớn nhất trong đồ thị khái niệm LectureBank 2.0 là **27
node / 60 cạnh** — vét cạn phải duyệt 2⁶⁰ tập con. Nhưng chính SCC đó chỉ có **177 chu trình đơn**, nên công thức
phủ tập hợp bằng ILP của [1] §3.2 chỉ cần 177 ràng buộc và giải **chính xác** trong mili giây. Baharev và cộng sự
liệt kê chu trình "in a lazy fashion" và trên 11/12 đồ thị kiểm thử "the initial loop set was sufficient to prove
that the solution found is optimal" [1] §5.1.

Bảng 1 của [1] cho thấy vì sao vét cạn theo tập con là sai đại lượng: đồ thị đầy đủ **10 node / 90 cạnh** có
**1 112 073 chu trình đơn**; đồ thị 2700 node / 3419 cạnh có hơn 10⁷.

*Suy luận:* số **chu trình** trong SCC tiên quyết thực tế nhỏ; số **tập con cạnh** thì không. Đổi sang liệt kê chu
trình + ILP giữ nguyên tính chính xác mà chạy được ở mọi cỡ — đây **không** phải đánh đổi chất lượng lấy tốc độ,
nên nó hợp với nguyên tắc "chất lượng trên hạn chót" của dự án.

[1] §2 cũng nêu các bước đơn giản hoá nên làm **trước**: tách SCC, bỏ SCC tầm thường, "breaking two-cycles
appropriately". Dự án đã làm bước tách SCC.

---

## 4. Rút gọn bắc cầu: quyết định "đánh dấu, không xoá" được xác nhận mạnh

Aho, Garey & Ullman [17] đặt nền: rút gọn bắc cầu là đồ thị ít cạnh nhất có cùng quan hệ khả đạt. Nó **chỉ xác định
duy nhất trên DAG**; NetworkX thi hành điều đó ở mức mã — `transitive_reduction` ném `NetworkXError` nếu đầu vào có
chu trình [18].

**Tác hại định lượng của một cạnh sai.** Thêm đúng **một** cạnh sai ngẫu nhiên (giữ phi chu trình) rồi đếm xem rút
gọn bắc cầu làm mất bao nhiêu cạnh đúng, 300–400 lần thử mỗi bộ:

| Đồ thị | cạnh/node | % lần mất cạnh đúng | TB khi mất | tệ nhất |
|---|---|---|---|---|
| CPN Caltech | 1,00 | 4,5% | 1,22 | 5 |
| AL-CPL data mining | 2,43 | 12,0% | 1,78 | 8 |
| AL-CPL precalculus | 3,12 | 16,3% | 1,16 | 3 |
| AL-CPL physics | 3,18 | 13,7% | 1,54 | 5 |
| **LectureBank 2.0** | **4,71** | **37,7%** | **3,81** | **25** |
| AL-CPL geometry | 5,89 | 30,7% | 1,32 | 4 |

Tác hại tăng theo mật độ. Ở chế độ 4–5 cạnh/node, cứ ~3 cạnh sai thì hơn 1 cạnh làm biến mất cạnh đúng.

**Một cơ chế thiên lệch mà dự án chưa biết.** Clough và cộng sự [19] rút gọn bắc cầu mạng trích dẫn: arXiv hep-th
xoá 82,3% cạnh, US Supreme Court 72,7%, US patents 15,2% (Bảng 1); một bài cụ thể mất **99,8%** trích dẫn. Sau khi
xáo trộn ngẫu nhiên 10 triệu lần mạng hep-th, họ kết luận: *"randomly rewired edges are less likely to be implied
by transitivity than those edges representing true citation behaviour"*.

*Suy luận:* đọc ngược lại, rút gọn bắc cầu **thiên lệch có hệ thống — ưu tiên xoá cạnh thật, ưu tiên giữ cạnh
nhiễu**. Nếu A9 xoá cạnh thừa, đúng những cạnh mô hình bịa ra sẽ **sống sót** còn cạnh đúng bị dọn đi: một đồ thị
bị làm giàu nhiễu. Đây là lý lẽ **mạnh hơn** lý lẽ quy trình mà D11 đang dùng, và nên vào spec.

**Không tìm thấy công trình nào khuyến nghị tường minh "đánh dấu thay vì xoá".** Lý lẽ ủng hộ là gián tiếp (thiên
lệch nhiễu + phép đo ở trên). Đây có thể là **một đóng góp nhỏ nhưng thật** của dự án — và nên nói thẳng như vậy.

**Một ràng buộc thứ tự cứng:** vì rút gọn bắc cầu không xác định trên đồ thị có chu trình, bước gỡ chu trình **phải**
xong trước bước đánh dấu. D11 hiện giữ chu trình hai cạnh (điểm 4) rồi mới đánh dấu bắc cầu (điểm 6) — hai điểm
**mâu thuẫn nhau** trên đúng những đồ thị có chu trình. Mã lách được vì `_alternate_path` tự cài chứ không gọi
NetworkX, nhưng spec vẫn phải cố định thứ tự.

---

## 5. Cổng chất lượng và chu trình hai cạnh

### 5.1 Mật độ đồ thị tiên quyết thật

| Bộ dữ liệu | #node | #cạnh | cạnh/node | % cô lập | cặp hai chiều | nguồn |
|---|---|---|---|---|---|---|
| LectureBank 1.0 NLP | 208 | 921 | 4,43 | 3,4% | 12 cặp | [7] |
| LectureBank 2.0 NLP | 322 | 1 551 | 4,82 | 1,6% | **30 cặp = 3,87% cạnh** | [8] |
| AL-CPL data mining | 120 | 292 | 2,43 | 25,0% | 0 | [9] |
| AL-CPL geometry | 89 | 524 | 5,89 | 1,1% | 0 | [9] |
| AL-CPL physics | 153 | 487 | 3,18 | 19,0% | 0 | [9] |
| AL-CPL precalculus | 224 | 699 | 3,12 | 12,5% | 0 | [9] |
| CPN Caltech (thô) | 771 | 772 | 1,00 | 39,3% | 0 | [6] |
| CPN Caltech (sau TR) | 771 | 640 | 0,83 | 39,3% | 0 | [5] Bảng I |
| CPN CUT (sau TR) | 416 | 319 | 0,77 | — | — | [5] Bảng I |
| **CPN JHU (sau TR)** | 10 291 | 3 499 | **0,34** | **77,7%** | 0 | [5] Bảng I |
| **bốn tài liệu của dự án** | 34–98 | 25–180 | **0,69–1,84** | **6–26%** | 1 cặp | số đo mục 2 |

Một cảnh báo về tính so sánh được: các bộ AL-CPL đã được **mở rộng bắc cầu** khi tiền xử lý — chính tác giả thêm
(A,C) làm mẫu dương khi có (A,B) và (B,C) [9]. Rút gọn bắc cầu loại 61,6% / 79,0% / 63,2% / 64,9% số cạnh bốn miền,
còn **0,93–1,24 cạnh/node**.

### 5.2 Cổng bị phản bác tới đâu, và tới đâu thì không

JHU có **0,340 cạnh/node** [5] và **77,7% node cô lập** (10 087 môn trong danh mục, chỉ 2 261 có văn bản tiên
quyết) — **kích hoạt cả hai cổng của dự án**. Caltech ở 39,3% cô lập, chỉ cách ngưỡng 60% có 1,5 lần.

*Suy luận — và đây là chỗ tôi không theo khảo sát hoàn toàn:* CPN là đồ thị **môn học** toàn trường, doc2roadmap
làm đồ thị **khái niệm trong một giáo trình**. Hai mức chi tiết khác nhau, và cổng của ta chỉ phải đúng ở mức thứ
hai. Ở mức ấy, số liệu lại **ủng hộ** ngưỡng hiện tại: AL-CPL sau rút gọn cho 0,93–1,24 cạnh/node, bốn tài liệu
của ta cho 0,64–1,32 (trừ cạnh thừa) — đều trên 0,5. Nên phản bác đúng của khảo sát không phải "0,5 là sai số" mà
là mạnh hơn về nguyên tắc: **dải hợp lệ đã quan sát được trải từ 0,34 đến 5,89 cạnh/node và từ 1,1% đến 77,7% cô
lập, nên không hằng số đơn nào phân tách "có cấu trúc" khỏi "không có cấu trúc" qua dải đó.** Hai đại lượng này đo
**mức chi tiết của node và quy ước gán nhãn**, không đo chất lượng.

Và **không tìm thấy nguồn nào** dùng ngưỡng mật độ để kích hoạt phương án dự phòng. Các khảo sát chất lượng KG dùng
accuracy, completeness, consistency, timeliness, trustworthiness, availability [10] *(theo abstract)* và các chỉ số
cấu trúc theo schema [11] — **không có chỉ số nào là ngưỡng mật độ kích hoạt fallback**. Câu "không tìm thấy nguồn"
này có giá trị: nó nói đây là chỗ dự án phải tự đo trên chính corpus của mình.

### 5.3 Chu trình hai cạnh: con số đúng, tiền đề sai

Con số nền của D11 **đúng**: LectureBank 2.0 có 30 cặp hai chiều = **3,87% số cạnh** [8]; LectureBank 1.0 ghi rõ
"We found 12 such pairs" trên 208 node / 921 cạnh [7], tức 2,6%.

Nhưng phần còn lại thì không. Trích nguyên văn [7]: các cặp hai chiều "consist of very closely related topics such
as *Domain Adaptation* and *Transfer Learning* ... suggesting that **in the future we may combine these pairs into
a single concept**."

Tác giả **không** coi đó là quan hệ hợp lệ — họ coi là dấu hiệu **hai nhãn đang mô tả một khái niệm** và nói rõ
định gộp lại. Xu hướng chung còn ngược hơn: AL-CPL kiểm định mọi quan hệ theo **thứ tự bộ phận chặt**, nếu (A,B)
dương thì (B,A) thành **mẫu âm**, và cả bốn miền có **0 cặp hai chiều** [9]; công cụ gán nhãn PRAT chặn hẳn ở mức
giao diện "undesired relations such as self-prerequisites and cycles" [12].

**KST nói mạnh hơn.** Quan hệ surmise (tiên quyết) là một **quasi-order**, tức *không* đòi phản đối xứng [13]. Một
cấu trúc tri thức là *discriminative* khi "for any two items q and r ... we have K_q = K_r only if q = r" (Định
nghĩa 1 của [13]). Định lý 10 (Birkhoff 1937) cho song ánh `qQr ⟺ K_q ⊇ K_r`. Ghép lại: A↔B kéo theo K_A = K_B,
**đúng định nghĩa mất tính discriminative**. Gói tham chiếu `kst` gọi tập item tương đương ấy là một **notion** và
thao tác chuẩn là `reduction(operation = "discrimination")` — **gộp thành một item** [15].

Nặng hơn nữa: Định lý 7 của [13] cho learning space ⟺ **well-graded** knowledge space, và well-graded đòi giữa hai
trạng thái bất kỳ có dãy mà mỗi bước đổi **đúng một item**. Nếu A và B tương đương thì không trạng thái nào chứa A
mà không chứa B, nên **notion chưa gộp phá vỡ tính well-graded** — đúng thứ A10 cần để sinh lộ trình từng bước.

*Suy luận — và đây là chỗ tôi tách khỏi khuyến nghị của khảo sát.* Khảo sát đề nghị gộp mọi SCC thành một node.
Điều đó đúng **khi hai nhãn là đồng nghĩa**. Nhưng ca thật duy nhất trên corpus của ta — **ERD ↔ Thiết kế Cơ sở dữ
liệu** — không phải đồng nghĩa: ERD là **bộ phận** của thiết kế CSDL. Gộp chúng sẽ giấu một lỗi **kiểu quan hệ**
dưới một thao tác danh tính. Hướng đúng cho ta là hướng thứ ba: **không giữ như tiên quyết, cũng không gộp — gắn cờ
là nghi lỗi kiểu quan hệ và loại khỏi đồ thị con `requires` cho tới khi người duyệt phán**, đồng thời ghi lại để
A13 xử lý. Về mặt vận hành nó gần với hiện tại (A10 đang co cặp ấy vào một khối), nhưng nó **nói đúng chuyện đang
xảy ra** thay vì gọi một lỗi là "mâu thuẫn hợp lệ".

Dù chọn hướng nào, **lý lẽ trong D11 điểm 4 phải viết lại**: nó đang dẫn một bộ dữ liệu để nói điều ngược với điều
tác giả bộ dữ liệu viết.

### 5.4 Hai điểm thiết kế không bị phản bác, và nền lý thuyết của chúng

**Sổ đăng ký kiểu quan hệ (D11 điểm 5).** Graphusion [29] xây dựng đồ thị tri thức khoa học zero-shot bằng LLM với
một **mô-đun hợp nhất** làm "entity merging, conflict resolution, and novel triplet discovery" ở góc nhìn toàn cục
thay vì trích cục bộ từng câu. Cùng ý với D11 điểm 5, nên điểm này nằm trong thông lệ. Và việc dự án **không** tự
quy tên nghi đồng nghĩa về `requires` là thận trọng đúng: Graphusion coi hợp nhất và giải xung đột là **bước riêng
có kiểm soát**, không phải gộp ngầm. **Không tìm thấy nguồn nào phản bác** điểm này.

**Cờ `learnable` (D11 điểm 1).** Mở rộng competence-based KST (CbKST) [16] *(theo abstract và tài liệu gói CRAN)*
tách hai tầng: tầng **biểu hiện** (bài tập, item quan sát được) và tầng **năng lực** (kỹ năng), nối bằng skill
function và problem function. *Suy luận:* đó chính là việc phân biệt node ở tầng năng lực — học được, vào lộ trình
— với node chỉ là thuật ngữ. Cờ `learnable` **có nền lý thuyết**, dự án chỉ chưa gọi tên nó. Nền gốc của toàn bộ
hình thức luận này là Doignon & Falmagne 1985 [14].

---

## 6. Sinh lộ trình: bài toán đã có tên, và chỉ số đánh giá đã có sẵn

### 6.1 Xếp tầng theo đường dài nhất làm đúng thứ nó được thiết kế để làm

Xếp tầng theo đường dài nhất tối thiểu **số tầng** nhưng không kiểm soát **độ rộng**, và **theo thiết kế** đẩy mọi
node in-degree 0 vào tầng 1 [36]. Nghĩa là "tầng 1 phình" không phải lỗi cài đặt — nó là tính chất của thuật toán,
cộng với việc đồ thị thiếu cạnh.

### 6.2 Bài toán "trần W phần tử mỗi tầng" là `P|prec, p=1|C_max`

Mallach [30] §2 viết thẳng, sau khi định nghĩa Minimum Width Directed Layering Problem: *"DLP-W is equivalent to
the precedence-constrained multiprocessor scheduling problem (when ignoring dummy vertices), and thus as well
NP-hard"*. Ánh xạ: khái niệm ↔ việc dài 1 đơn vị · cạnh `requires` ↔ ràng buộc thứ tự · trần W ↔ W máy · số tầng ↔
makespan.

*Elements of Scheduling* [31] — sách do chính những người dựng ra ngành viết, toàn văn mở:
- **Định lý 2.21**: *"The problem P|prec, p_j = 1|C_max is NP-complete."* (quy dẫn từ CLIQUE; chứng minh gốc là
  Ullman 1975 [32]).
- **Định lý 2.27**: *"There can be no α-approximation algorithm for P|prec, p_j = 1|C_max with α < 4/3 unless
  P = NP."*
- Với **m = 3** độ phức tạp **vẫn đang mở** — bài toán cuối còn lại từ sách Garey & Johnson [37].

**Thuật toán chuẩn đã có, có cận, có mã nguồn.** Coffman–Graham 1972 [33] *(theo abstract)* gán node vào tầng với
trần cho trước, đồng thời xấp xỉ tối thiểu số tầng. Cận `l ≤ (2 − 2/W)·l_opt` của Lam & Sethi 1977 *(theo mô tả thứ
cấp; không tiếp cận được toàn văn — phải kiểm lại nếu đưa vào bài báo)*; Braschi & Trystram 1994 [34] chỉ ra phân
tích Lam–Sethi **sai một phần**, sửa và siết thành `≤ (2 − 2/m)·ω_opt − (m−3)/m` *(theo abstract)*. OGDF cài sẵn
`CoffmanGrahamRanking` với `width(int)` [35].

**Cận dưới dự án chưa tính tới:** mọi xếp tầng hợp lệ cần ≥ `max(xích dài nhất, ⌈n/W⌉)` tầng. Một giáo trình 300
khái niệm với trần 8 sẽ cần **ít nhất 38 stage**, bất kể đồ thị nông đến đâu. Đây là một assertion rẻ và kiểm được
ngay (xem Đ4).

*Suy luận:* khoảng giữa ngưỡng cứng 4/3 và cận 1,6–1,75 của Coffman–Graham là toàn bộ dư địa cải tiến — rất hẹp.
Không đáng đầu tư thêm vào phần thuật toán; lấy Coffman–Graham, trích nguồn, và chuyển ngân sách nghiên cứu sang
phần **đánh giá**.

**Và có một cách chữa "tầng 1 phình" rẻ hơn mà dự án chưa làm.** Network simplex của Graphviz [38] §2.2 tối thiểu
tổng độ dài cạnh có trọng số và **không có ràng buộc nào về số node mỗi tầng**; thứ duy nhất chạm tới độ rộng là
bước `balance()` ở §2.3: *"Nodes having equal in- and out-edge weights and multiple feasible ranks are moved to a
feasible rank with the fewest nodes."* Mã nguồn khớp bài báo — `lib/common/ns.c`, `TB_balance()`, comment *"find
nodes that are not tight and move to less populated ranks"*. Tuyến tính, không đổi tính hợp lệ của thứ tự.

Văn liệu tối thiểu độ rộng cho thấy đây là cách tiếp cận thực dụng chuẩn: Healy & Nikolov đặt bài toán có cận trên
cho cả độ rộng lẫn chiều cao và giải bằng ILP, và bài toán là NP-khó [39] *(theo abstract)*; các heuristic
MinWidth / StretchWidth [40] và Promote Layering đều là **hậu xử lý xếp tầng đường dài nhất**, không phải phân hoạch
lại theo cụm ngữ nghĩa.

### 6.3 "Stage = tầng ∩ cụm" không có tiền lệ nào

**Không tìm thấy nguồn sơ cấp nào** đề xuất, phân tích hay đánh giá "giao của một tầng tô-pô với một cụm cộng đồng"
làm đơn vị mô-đun học. Thứ gần nhất là một quan sát ngoài ngành giáo dục: trong sắp thứ tự câu, "topically related
sentences seem to appear together" trong các thứ tự được người chấp nhận (dẫn trong [41] §5).

Điều đó **không** làm nó sai — nhưng có hai hệ quả: không được trình bày như "theo văn liệu", và vì chưa ai kiểm,
dự án phải tự kiểm. Mục 2.7 đã là phép kiểm ấy, và kết quả không ủng hộ nó.

### 6.4 Chỉ số đánh giá: Kendall τ, và cái bẫy đối chứng

Lapata [41] định nghĩa `τ = 1 − 2S(π,σ)/(N(N−1)/2)` và **kiểm chứng nó bằng người**:
- Thực nghiệm 1: 189 tình nguyện viên (giữ 179), chấm mạch lạc thang 1–7. Tương quan τ ↔ điểm người chấm
  **r = 0,45 (p < 0,01, N = 64)**; đồng thuận giữa người với người (leave-one-out, 178 phân tích) **r = 0,56**.
  Tác giả kết luận: *"τ's agreement with the human data is not far from the average human agreement."*
- Thực nghiệm 2: 32 người, đo **thời gian đọc**. τ ↔ thời gian đọc **r = −0,48**; điểm chấm ↔ thời gian đọc
  **r = −0,47**.
- Lý do chọn τ thay vì Spearman ρ (§2): phân phối của τ tiến về chuẩn nhanh hơn, "offering an advantage for small
  to moderate sample studies with 30 or fewer data points", và ρ là **ước lượng thiên lệch** còn τ thì không.
- Cảnh báo của chính tác giả (§5): các đánh giá dùng **một** văn bản tham chiếu duy nhất, trong khi "there may be
  many acceptable orders". Với nhiều tham chiếu: tính τ N lần rồi lấy trung bình.

**Không tìm thấy chỉ số chuẩn riêng của ngành giáo dục** cho việc so một lộ trình sinh tự động với mục lục gốc, và
**không tìm thấy công trình nào** dùng τ để so lộ trình khái niệm do LLM sinh với thứ tự trong giáo trình. Mượn
thẳng từ NLP là phòng thủ được, và khoảng trống ấy là **chỗ đóng góp rõ nhất**.

**Cái bẫy.** D12 nói "thứ tự giữa các stage con cùng tầng là tuỳ ý, chọn theo thứ tự chương". Nếu dùng thứ tự chương
để phá thế hoà **và** làm đối chứng τ thì đối chứng bị nhiễm — một phần điểm số đến từ việc đã chép sẵn đáp án. Số
τ ở mục 2.5 đang mang đúng vết nhiễm này. Phải chọn một trong hai: (a) phá thế hoà bằng tiêu chí **không** dùng vị
trí chương (số khái niệm hậu duệ giảm dần, hoặc ID ổn định), hoặc (b) báo cáo hai con số — τ toàn phần và τ chỉ
trên các cặp mà thứ tự **không** do quy tắc phá thế hoà quyết định. (a) sạch hơn và rẻ hơn.

### 6.5 Trần 5–8 không có nguồn sơ cấp nào

Miller 1956 [42] **tự nghi ngờ con số của mình**, kết bài rằng sự lặp lại của số bảy có lẽ chỉ là *"a pernicious,
Pythagorean coincidence"*, và tách rõ hai giới hạn khác nhau: *"The span of absolute judgment and the span of
immediate memory are quite different kinds of limitations"*. Cơ chế ông thật sự muốn nói là **recoding**.

Cowan 2001 [43] hạ xuống **3–5 chunk** *(theo abstract)*, và nói rõ con số của Miller "was meant more as a rough
estimate and rhetorical device than as a real capacity limit".

Bằng chứng định lượng gần nhất về chia nhỏ nội dung là meta-analysis segmenting của Rey và cộng sự [44], Bảng 3:

| Kết quả đo | k | n | d | KTC 95% |
|---|---|---|---|---|
| Retention (tổng) | 67 | 6 100 | 0,32*** | [0,20, 0,43] |
| Transfer (tổng) | 56 | 4 754 | 0,36*** | [0,24, 0,48] |
| Cognitive load | 20 | 1 687 | 0,23** | [0,06, 0,39] |
| **Learning time** | 19 | 1 625 | **−0,92*** | [−1,64, −0,20] |

Bài chỉ ghi độ dài đoạn trung bình **75,49 giây**; **không có phân tích moderator nào về kích thước đoạn tính theo
số khái niệm**, và không có khuyến nghị nào về "bao nhiêu khái niệm một mô-đun".

**Không tìm thấy nguồn sơ cấp nào** khuyến nghị cỡ mô-đun học cụ thể tính bằng số khái niệm. Các khuyến nghị "3–5
khái niệm" chỉ nằm trong blog ngành đào tạo, đều dẫn về Miller 1956 — tức dẫn về đúng con số Miller và Cowan đã bác.

*Suy luận:* đừng bảo vệ 5–8 bằng tâm lý học. Bảo vệ bằng **thuật toán**: W là tham số của bài toán xếp tầng có trần
độ rộng, mặc định 8, kèm ablation `W ∈ {4, 6, 8, 12}` báo cáo số stage và τ. Như vậy 5–8 thành một lựa chọn kỹ
thuật minh bạch thay vì một tuyên bố tâm lý học sai.

### 6.6 Xen kẽ, giãn cách, và giới hạn phải công bố

Xen kẽ có bằng chứng mạnh nhưng **không phản bác trực tiếp** "stage = tầng ∩ cụm": Rohrer và cộng sự 2014 (n = 140
lớp 7, 9 tuần, 72% vs 38%, d = 1,05) đo **lịch luyện tập**, không đo **thứ tự trình bày lần đầu** [45]. Nói "stage
= tầng ∩ cụm đi ngược bằng chứng" là suy rộng quá nguồn. Nhưng hai điều vẫn đúng: nếu sau này sinh bài tập theo
stage thì đó đúng là blocked practice; và distributed practice có nền mạnh hơn hẳn (Donoghue & Hattie 2021:
d = 0,85 trên 152 952 người, so với interleaving d = 0,47 trên 972 người, I² = 88) [46], trong khi "mỗi khái niệm
xuất hiện đúng một lần" là massed practice.

**Ba giới hạn phải vào phần Limitations, có trích dẫn:**

1. **"Learning path" đã có định nghĩa hình thức khác.** KST Định nghĩa 45 [13]: learning path là **xích cực đại
   các trạng thái**; một gradation có đúng `1 + |Q|` trạng thái. Cái A10 sinh ra là **một** linear extension được
   gom cụm, không phải "lộ trình học" theo nghĩa đã có sẵn 40 năm.
2. **Hai người sáng lập KST bác trực diện nền mô hình.** Ngay sau Định lý 10 (Birkhoff 1937, thứ tự bộ phận ↔ quasi
   ordinal space), [13] viết: *"Note in passing that the closure under intersection does not make good pedagogical
   sense."* Learning space chỉ đóng dưới **hợp** (Định lý 7). Dự án **không bắt buộc** chuyển sang learning space —
   không có dữ liệu học viên thì không ước lượng được — nhưng **bắt buộc phải nêu**.
3. **Thứ học tiếp là một tập, không phải một tầng.** Fringe Theorem [13]: outer fringe của trạng thái "tells us
   exactly what the student is ready to learn"; ALEKS đo trung vị **0,93** xác suất học thành công trên **1 940 473**
   lượt học. A10 xuất một danh sách stage toàn cục, giống nhau cho mọi người — một **giản lược có chủ ý** vì thiếu
   dữ liệu tương tác. Chấp nhận được, nhưng phải viết ra.

Và một tiền lệ phải thừa nhận: dùng sắp xếp tô-pô để lập kế hoạch chương trình học đã được công bố ở ACM từ thập
niên 1970 (Meinke & Bauer, có mã FORTRAN tên TOPSORT) *(chỉ tiếp cận được tiêu đề và mô tả thứ cấp)*; thuật toán
Kahn là 1962 [47]. Không thể trình bày ý tưởng ấy như đóng góp mới.

### 6.7 Độ khó theo độ sâu DAG: không ai kiểm

Zuev & Stavrinides [5] §IV **phát biểu** rằng các tầng tô-pô có "approximately the same level of difficulty" nhưng
toàn bài chỉ có đúng một lần xuất hiện chữ "difficulty" và không có hệ số nào. **Không tìm thấy nguồn nào** kiểm
chứng tương quan giữa độ sâu DAG tiên quyết và độ khó cảm nhận hay tỉ lệ sai của người học. Chuẩn đo độ khó hiện
nay dùng điểm số / latent trait.

*Suy luận:* `spec-addendum` §432 nói "độ khó được tính từ độ sâu DAG sau A10". Chưa cài, và may là chưa — nên đổi
tên thành **"độ sâu tiên quyết"** và bỏ mọi câu hàm ý độ khó nhận thức.

### 6.8 Mặt bằng ngành, để hạ kỳ vọng đúng chỗ

Tổng quan hệ thống metaheuristic cho curriculum sequencing phủ 61 công trình 2005–2018; chính nhóm tác giả thừa
nhận *"lack of available datasets or benchmarks"* và các công trình *"do not provide sufficient data to
reproduce"*; bộ dữ liệu thật duy nhất của họ có **61 học viên**. Công trình 2025 mạnh nhất (GPT-4o + RL) vẫn
**không có người học thật, không có nhóm đối chứng** — chấm bằng mô phỏng DKT do chính nhóm dựng.

*Suy luận:* doc2roadmap **không cần đánh bại ai** ở phần A10. Đóng góp phải nằm ở **cách đo**, không ở việc sinh ra
được lộ trình.

### 6.9 LLM đổi thứ tự giữa các lượt — khoá phạm vi là đúng, nhưng chưa đủ chặt

Chỉ đảo thứ tự đầu vào đã làm Kendall τ giữa hai đầu ra của **cùng mô hình, cùng prompt** rơi còn **0,6358 /
0,6986** [48] (Bảng 1, K = 25, zero-shot). Quyết định của `spec-addendum` A10 — LLM **không** được đổi thứ tự giữa
các stage — được **xác nhận mạnh**.

*Suy luận:* nên chặt thêm: nạp khái niệm theo **thứ tự chuẩn tắc**, hoặc chạy k hoán vị + tổng hợp Kemeny và **báo
cáo chỉ số ổn định**. Rẻ, không cần dữ liệu học viên, và gần như không ai trong ngành giáo dục báo cáo.

---

## 7. Kiểm định bằng dữ liệu học viên — và cách gọi tên phải sửa

Dự án **không có** dữ liệu học viên. Phần này khảo sát mất gì và còn dùng được gì.

- **Vuong, Nixon & Towle** (EDM 2011) [20]: với mỗi cặp phụ thuộc khả dĩ, so kết quả học của học viên **đã** học
  đơn vị tiên quyết tiềm năng với học viên **chưa** học. Mẫu: 1/5 số trường dùng Carnegie Learning Cognitive Tutor
  năm 2008–2009, quy mô "hàng trăm nghìn học viên tại hơn hai nghìn năm trăm trường".
- **Scheines, Silver & Goldin** (EDM 2014) [21]: coi knowledge component là **biến ẩn**, dùng **khám phá cấu trúc
  nhân quả** — quan hệ tiên quyết và quan hệ nhân quả sinh ra cùng kiểu độc lập có điều kiện. Ca nghiên cứu:
  **~120 học viên**, đo tại **một thời điểm**.
- **Brunskill** (EDM 2011) [22] *(theo abstract)*: so log-likelihood giữa mô hình "có điều kiện tiên quyết" và mô
  hình phẳng trên từng cặp kỹ năng.
- **POKS** [23]: học cấu trúc item-to-item chỉ từ đáp án bài kiểm tra, khung naive Bayes + kiểm định thống kê; nền
  tảng là chính KST.
- **Käser và cộng sự** (IEEE TLT 2017) [24]: BKT "makes it impossible to represent the hierarchy and relationships
  between different skills"; dùng DBN để biểu diễn nhiều kỹ năng trong một mô hình.

*Suy luận:* **không dòng nào chuyển được sang doc2roadmap**. Nhưng chúng cho hai thứ dùng được ngay:

1. **Một giới hạn phải công bố, và một chữ phải đổi.** Cả năm coi "kiểm định" nghĩa là kiểm định *tiên đoán* trên
   hành vi học viên. A9 không làm thế, nên **không được dùng chữ "kiểm định" mà không định tính**. Cái A9 làm là
   **kiểm tra tính nhất quán cấu trúc**.
2. **Một đường nâng cấp rẻ.** Scheines và cộng sự làm được với ~120 học viên tại một thời điểm [21] — ngưỡng thấp
   hơn Vuong rất nhiều. Nếu sau này có dù chỉ một đợt kiểm tra nhỏ, khung của [21] là con đường rẻ nhất để có kiểm
   định thật.

Không có dữ liệu học viên, thứ thay thế duy nhất văn liệu ủng hộ là **thoả thuận giữa người gán nhãn**. LectureBank
báo cáo **Cohen's κ = 0,7** với hai nghiên cứu sinh gán nhãn nhị phân, và nói rõ bản ba mức trước đó chỉ đạt
**κ = 0,3** trên **cùng các cặp khái niệm** [7].

*Suy luận:* κ nhảy 0,3 → 0,7 chỉ do đổi nhị phân/ba mức và làm rõ tiêu chí. Đây là mốc đối chiếu tốt cho bộ vàng
PREAP: nếu κ của hai người gán thấp hơn ~0,7 thì vấn đề nhiều khả năng ở **định nghĩa nhiệm vụ**, không ở người
gán. Và [7] chỉ đích danh nguồn bất đồng: "long dependencies" — A tiên quyết B, B tiên quyết C, có tính A tiên quyết
C không. **Giao thức PREAP phải trả lời dứt khoát câu đó.**

---

## 8. Độ tin cậy mô hình tự khai: bỏ hẳn, không chỉ xếp cuối

Xiong và cộng sự (ICLR 2024) [25] đánh giá 5 mô hình × 8 bộ dữ liệu. Bảng 2, confidence tự khai dạng thuần, trung
bình trên 8 bộ (đơn vị ×10⁻²):

| Mô hình | ECE ↓ | AUROC ↑ |
|---|---|---|
| GPT-3 | 52,0 | **51,3** |
| Vicuna 13B | 46,1 | **52,5** |
| LLaMA-2 70B | 43,6 | 56,4 |
| GPT-3.5 | 37,7 | 55,1 |
| GPT-4 | 18,0 | 62,7 |

AUROC ≈ 50 là tung đồng xu. §5.1 và Hình 2: "the confidence levels primarily range between 80% and 100%, often in
multiples of 5; the accuracy within each bin is much lower than its corresponding confidence, indicating
**significant overconfidence**" — tác giả cho rằng mô hình đang **bắt chước cách con người nói về độ tự tin**, chứ
không báo cáo trạng thái nội tại. Phát hiện lặp lại rộng rãi [26].

**Số đo của ta khớp đúng mô tả đó**: 327 cạnh, ba giá trị 0,7 / 0,8 / 0,9, bội số của 0,05, dồn về đầu cao.

*Suy luận:* với `gemini-3.1-flash-lite` ở temperature 0, tình hình tệ hơn các con số trên: hiệu chỉnh xấu đi khi
năng lực mô hình giảm, và temperature 0 **làm mất luôn** self-consistency — tín hiệu thay thế tốt nhất. Dự án ở
đúng góc tệ nhất của không gian thiết kế đối với confidence.

**Không tìm thấy nghiên cứu hiệu chỉnh nào chạy riêng trên bài toán suy quan hệ tiên quyết** — mọi số trên đến từ
QA/suy luận. Đây là khoảng trống dự án phải tự đo nếu muốn dùng confidence.

Hướng dài hạn có đảm bảo hình thức: **conformal prediction** cho cạnh đồ thị [27][28] — cho **tập cạnh kèm đảm bảo
phủ** thay vì một điểm số cần tin tưởng, dùng bộ vàng PREAP làm tập hiệu chuẩn, và **không cần dữ liệu học viên**.
Ngoài phạm vi đợt này, nhưng là con đường đúng.

---

## 9. Đề xuất điều chỉnh

Đánh số `Đ` để đợt `/to-spec` sau chuyển thành quyết định spec. Mỗi mục ghi rõ nó chạm điểm nào.

### Phải sửa — A9

| | Đang làm | Căn cứ | Đề xuất |
|---|---|---|---|
| **Đ1** | D11 nói gỡ chu trình bằng "tìm kiếm vét cạn" | Mã có nhánh xấp xỉ `eades_priority` khi > 16 cạnh nội bộ mà **D11 không nhắc**; văn liệu cho cách giải **chính xác ở mọi cỡ**: liệt kê chu trình đơn (Johnson) + phủ tập hợp có trọng số bằng ILP [1] §3.2; `igraph.feedback_arc_set(algo="exact_ip")` có sẵn [4], NetworkX không có gì | Gọi đúng tên: **MFAS có trọng số**. Định nghĩa trọng số tường minh từ thứ tự ưu tiên hiện có. Đổi sang chu trình + ILP; chỉ rơi về Eades–Lin–Smyth [3] ở bước cuối và **ghi nhãn nghiệm xấp xỉ** vào artifact (trường `method` đã có — spec phải nói về nó). Đặt ngân sách theo **số chu trình đơn**, không theo số node |
| **Đ2** | Cổng: 0,5 cạnh/node **hoặc** 60% cô lập → fallback | JHU: 0,340 cạnh/node [5] và 77,7% cô lập — kích hoạt cả hai. Dải hợp lệ quan sát được 0,34–5,89 và 1,1–77,7%. **Không tìm thấy nguồn nào** dùng ngưỡng mật độ kích hoạt fallback [10][11]. Số đo của ta: cổng chưa bao giờ suýt đóng, và tử số **đếm cả cạnh thừa** | (i) Tính mật độ **sau khi trừ cạnh `redundant_via`**; (ii) hạ cổng thành **bộ bắt lỗi pipeline chết** (đề xuất 0,15 cạnh/node, 85% cô lập) thay vì phán xét chất lượng tài liệu; (iii) **luôn ghi số đo ra manifest** và cảnh báo cho người duyệt thay vì im lặng rơi fallback; (iv) ghi trong bài rằng đây là chỗ không có nguồn |
| **Đ3** | Giữ chu trình hai cạnh, gắn cờ; lý lẽ là "tác giả bộ dữ liệu coi ~4% cạnh hai chiều là hợp lệ" | Con số **đúng** (3,87% [8]) nhưng **tiền đề sai**: tác giả viết "we may combine these pairs into a single concept" [7]. AL-CPL có 0 cặp hai chiều [9]; PRAT chặn ở giao diện [12]. KST: A↔B ⇒ K_A = K_B ⇒ mất tính discriminative [13]; thao tác chuẩn là gộp notion [15]; notion chưa gộp **phá vỡ tính well-graded** mà A10 cần [13] Đ.lý 7 | **Viết lại toàn bộ lý lẽ của D11 điểm 4.** Về hành vi, đề xuất hướng thứ ba (không giữ như tiên quyết, không gộp): **gắn cờ nghi lỗi kiểu quan hệ, loại khỏi đồ thị con `requires` cho tới khi người duyệt phán** — vì ca thật duy nhất của ta (ERD ↔ Thiết kế CSDL) là lỗi bộ phận–toàn thể, không phải cặp đồng nghĩa. Chủ dự án chọn giữa hướng này và hướng gộp notion |
| **Đ4** | D11 điểm 4 (giữ chu trình) đứng trước D11 điểm 6 (đánh dấu bắc cầu) | Rút gọn bắc cầu **không xác định** trên đồ thị có chu trình; NetworkX ném lỗi [18]; định nghĩa gốc dựa trên quan hệ khả đạt [17] | Cố định thứ tự trong spec: gỡ chu trình / xử lý SCC **trước**, đánh dấu bắc cầu **sau**. Đ3 xử lý luôn |
| **Đ5** | `confidence` là tiêu chí thứ tư khi giữ cạnh | Số đo: 327 cạnh, **ba giá trị**. Văn liệu: AUROC 51,3–62,7 [25]; quá tự tin có hệ thống; hiệu chỉnh xấu hơn ở mô hình nhỏ; temperature 0 mất self-consistency | **Bỏ hẳn confidence** khỏi thứ tự ưu tiên; phá hoà cuối bằng **thứ tự từ điển của ID cạnh** để tái lập được. Ghi [25][26] làm căn cứ. Cũng ghi rằng `evidence_kind` gần suy biến (71–88% một giá trị), nên thứ tự bốn tiêu chí thực tế do `order_relation` và số nguồn quyết định |
| **Đ6** | Gọi A9 là "kiểm định đồ thị" | Trong văn liệu, kiểm định quan hệ tiên quyết nghĩa là kiểm định trên **biểu hiện học viên** [20]–[24] | Đổi thành **"kiểm tra tính nhất quán cấu trúc"**. Nêu "không có dữ liệu học viên" là giới hạn đã biết kèm [20]–[24], và nêu [21] (~120 học viên) là đường nâng cấp rẻ nhất |
| **Đ7** | `spec-addendum` A9 §2 và §3 | Lỗi thời, nói **ngược** hành vi thật (cắt theo confidence thấp nhất; xoá cạnh bắc cầu) | Xoá hai luật cũ, trỏ sang D11 |
| **Đ8** | Lý lẽ giữ `redundant_via` dựa trên quy trình duyệt | Xác nhận mạnh: một cạnh sai làm mất cạnh đúng **37,7%** số lần trên LectureBank 2.0, tệ nhất **25 cạnh**; và Clough và cộng sự [19] cho thấy rút gọn bắc cầu **thiên lệch: ưu tiên xoá cạnh thật, giữ cạnh nhiễu** | **Giữ nguyên quyết định.** Thêm lý lẽ thống kê [19] vào spec. Ghi rằng **không tìm thấy công trình nào** khuyến nghị tường minh "đánh dấu thay vì xoá" — đây có thể là đóng góp nhỏ nhưng thật |
| **Đ9** | Cờ rỗng `{}` lọt từ pass phụ vào trang duyệt | Số đo: 2 cờ trên `nhap-mon-ml`; gốc ở `domain/secondary.py:139` | **F113** — kiểm hợp đồng phải kiểm từng phần tử của `flags`, không chỉ kiểu của danh sách |

### Phải sửa — A10

| | Đang làm | Căn cứ | Đề xuất |
|---|---|---|---|
| **Đ10** | `stage = tầng ∩ cụm chủ đề`, ép trần bằng cách cắt theo cụm | **Không tìm thấy tiền lệ nào.** Số đo: 63 stage cho 98 khái niệm, 39 stage đơn lẻ, gấp ~5 lần cận dưới; bỏ phép giao không mất τ | **Bỏ phép giao cụm khỏi định nghĩa stage.** Giữ cụm chủ đề làm tiêu chí **phá thế hoà và đặt tên**, không làm cơ chế chính |
| **Đ11** | Xếp tầng theo đường dài nhất, "tầng 1 phình" coi là vấn đề chưa giải | Bài toán là `P\|prec,p=1\|C_max` [30][31], NP-khó [32], không xấp xỉ dưới 4/3 [31]; thuật toán chuẩn là **Coffman–Graham** [33] cận (2−2/W) [34], cài sẵn trong OGDF [35]. Mô phỏng: trần độ rộng đưa tầng 1 từ 17/18/16/12 xuống 8 mà **không mất bất biến nào** | Thay bằng **xếp tầng có trần độ rộng**, ưu tiên Coffman–Graham vì có cận chứng minh được. Nếu muốn rẻ hơn: thêm bước `balance()` kiểu Graphviz [38] — đẩy node có slack sang tầng ít node hơn, tuyến tính, không đổi tính hợp lệ. **Nêu tên bài toán và trích nguồn trong bài báo** |
| **Đ12** | Không có assertion về số stage | Cận dưới: mọi xếp tầng hợp lệ cần ≥ `max(xích dài nhất, ⌈n/W⌉)` stage | Thêm assertion. Kiểm ngay: `xstk-ch3-1` cận dưới 13, hiện cho 63 |
| **Đ13** | Thứ tự chương vừa dùng phá thế hoà vừa (dự kiến) làm đối chứng τ | Nhiễm đối chứng — lỗi thiết kế thí nghiệm, không có nguồn nào cần | Phá thế hoà bằng tiêu chí **không** dùng vị trí chương (số hậu duệ giảm dần, hoặc ID ổn định). τ ở mục 2.5 phải đo lại sau khi sửa |
| **Đ14** | Chưa có chỉ số đánh giá lộ trình | Lapata [41]: τ ↔ phán đoán người r = 0,45; τ ↔ thời gian đọc r = −0,48; đồng thuận người–người r = 0,56; τ không thiên lệch ở mẫu nhỏ. **Không tìm thấy** công trình nào dùng τ so lộ trình LLM với mục lục giáo trình | Lấy **hai** chỉ số chính: (i) **Kendall τ** so thứ tự xuất hiện đầu tiên trong giáo trình, kèm cảnh báo "single reference" của [41] §5; (ii) **tỉ lệ vi phạm cạnh vàng** — số cạnh vàng mà lộ trình xếp ngược (hiện 11/62 = 18%). Chỉ số (ii) không tốn thêm lượt gán nhãn nào |
| **Đ15** | Trần 5–8, ngầm dựa vào 7±2 | Miller tự gọi số bảy là *"a pernicious, Pythagorean coincidence"* [42]; Cowan hạ xuống 3–5 [43]; segmenting meta-analysis không có moderator nào theo số khái niệm và kèm **learning time d = −0,92** [44]. **Không tìm thấy nguồn sơ cấp nào** khuyến nghị cỡ mô-đun theo số khái niệm | **Không viện tâm lý học.** W là tham số của bài toán xếp tầng, mặc định 8, kèm ablation `W ∈ {4, 6, 8, 12}` báo số stage và τ. Thêm **sàn** cỡ stage, vì số đo cho thấy vấn đề là quá nhỏ chứ không quá to |
| **Đ16** | `spec-addendum` §432: độ khó từ độ sâu DAG | **Không tìm thấy nguồn nào** kiểm chứng; [5] §IV chỉ phát biểu, không kiểm | Đổi tên thành **"độ sâu tiên quyết"**, xoá mọi câu hàm ý độ khó nhận thức. (Chưa cài, nên rẻ) |
| **Đ17** | Gọi sản phẩm là "lộ trình học / learning path" | KST Đ.nghĩa 45 [13]: learning path = xích cực đại các trạng thái, `1+\|Q\|` trạng thái | Giữ tên tiếng Việt nhưng trong bài báo nói rõ đây là **một gradation được đóng gói thành stage**, kèm trích [13] |
| **Đ18** | Spec mô tả ba thứ chưa cài: media → stage, lượt LLM đặt tên stage, độ khó | Số đo mục 1.2 | Gỡ khỏi spec **hoặc** cắt vé, không để spec mô tả hệ thống không tồn tại. Media → stage: **không có nguồn ủng hộ lẫn phản bác**, giữ làm heuristic và ghi rõ |
| **Đ19** | — | Fringe Theorem + ALEKS (trung vị 0,93 trên 1 940 473 lượt) [13]; Birkhoff + *"closure under intersection does not make good pedagogical sense"* [13]; tiền lệ sắp xếp tô-pô cho lộ trình học có từ thập niên 1970 [47] | **Thêm mục Limitations** với ba điều này. Không đổi mô hình (thiếu dữ liệu học viên), nhưng không thừa nhận thì là bỏ qua phản chứng đã công bố |
| **Đ20** | LLM không được đổi thứ tự giữa các stage | Xác nhận mạnh: đảo thứ tự đầu vào làm τ giữa hai đầu ra tụt còn 0,6358 / 0,6986 [48] | Giữ. Thêm: nạp khái niệm theo **thứ tự chuẩn tắc**, hoặc k hoán vị + tổng hợp Kemeny, và **báo cáo chỉ số ổn định** |
| **Đ21** | Phân biệt node "đã xét, không thấy tiên quyết" / "chưa từng xét" | **Không tìm thấy tiền lệ** trong văn liệu giáo dục | **Giữ — đây là thực hành đúng.** Nâng thành đóng góp nhỏ bằng cách **báo con số** (hiện: 0 node chưa xét trên cả bốn tài liệu) |
| **Đ22** | SCC được co vào một tầng | Gansner và cộng sự [38] §2.1 nói rõ họ **cố ý không** "placing the nodes in a cycle on the same rank" — nhưng lý do là chất lượng bản vẽ, không phải sư phạm | Phản chứng yếu, **giữ được**. Nhưng: (i) xử lý tường minh SCC lớn hơn trần W; (ii) **báo cáo phân bố kích thước SCC** sau A9 |

### Quyết định của chủ dự án, không phải của reviewer

| | Câu hỏi | Số đo hai phía |
|---|---|---|
| **Đ23** | **"Stage" là nhóm học song song được, hay chặng đọc tuần tự?** | Giữ nhóm độc lập (A/C): 0 cạnh tiên quyết nằm trong stage, nhưng τ 0,06–0,56 — xáo trộn sách mạnh. Chuyển sang chặng đọc (D): τ 0,63–0,98, 0 stage đơn lẻ, số stage đạt **đúng cận dưới lý thuyết**, nhưng **34–64% cạnh tiên quyết rơi vào trong một stage** |

---

## 10. Thí nghiệm phải thêm

Đăng ký trước, trước khi mở bộ vàng chính thức.

- **E9 — Lộ trình so mục lục.** Kendall τ giữa thứ tự A10 và thứ tự xuất hiện đầu tiên trong giáo trình, **sau khi
  sửa Đ13**. Báo cả τ toàn phần lẫn τ trên các cặp không do phá thế hoà quyết định. Trích [41].
- **E10 — Tỉ lệ vi phạm cạnh vàng.** Trên chương vàng: tỉ lệ cạnh vàng mà lộ trình xếp tiên quyết **sau** khái niệm
  đích. Chạy trên hai lộ trình — dựng từ cạnh vàng và dựng từ cạnh máy — để tách "sách sai" khỏi "máy sai". Hiện
  trên bộ vàng thử nghiệm: vàng τ +0,803 · máy τ +0,603 · vi phạm 11/62.
- **E11 — Ablation cách gom stage.** Bốn biến thể A/B/C/D × `W ∈ {4, 6, 8, 12}`, báo số stage, phân bố cỡ stage,
  τ, tỉ lệ vi phạm cạnh vàng, và số cạnh nằm trong stage. Thay cho mọi viện dẫn tâm lý học ở Đ15.
- **E12 — Ổn định thứ tự của lượt LLM cuối** (nếu Đ18 quyết định cài): k hoán vị đầu vào, báo τ giữa các đầu ra.
  Trích [48].

---

## 11. Việc phải cắt vé

1. **Vé mới — A9 nhất quán cấu trúc v2**: Đ1 (MFAS có trọng số bằng chu trình + ILP), Đ3 (hành vi chu trình hai
   cạnh, sau khi chủ dự án chọn hướng), Đ4 (thứ tự), Đ5 (bỏ confidence), Đ2 (cổng tính trên cạnh không thừa).
2. **Vé mới — A10 xếp tầng có trần độ rộng**: Đ10, Đ11, Đ12, Đ13, Đ15.
3. **Vé mới — chỉ số đánh giá lộ trình**: E9, E10, E11 trong bộ chấm (`gold_scoring.py` + `a8_score.py`).
4. **Ghép vào vé đang chạy**: Đ9 (F113).
5. **Việc spec thuần, không cần vé**: Đ6, Đ7, Đ16, Đ17, Đ18, Đ19, Đ21, Đ22.

*Suy luận về thứ tự:* Đ13 phải làm **trước** E9, nếu không mọi số τ đo được đều mang vết nhiễm đối chứng. Và Đ3 cần
chủ dự án chọn hướng trước khi cắt vé, vì nó đổi hành vi đã chốt ở F88.

---

## Nguồn

### Gỡ chu trình và rút gọn bắc cầu

1. Baharev, A., Schichl, H., Neumaier, A., & Achterberg, T. (2021). *An Exact Method for the Minimum Feedback Arc Set Problem*. ACM Journal of Experimental Algorithmics 26, Article 1.4. https://dl.acm.org/doi/10.1145/3446429 · toàn văn: https://arnold-neumaier.at/ms/minimum_feedback_arc_set.pdf
2. Karp, R. M. (1972). *Reducibility Among Combinatorial Problems*. Complexity of Computer Computations, Plenum Press, 85–103. (Dẫn qua [1] §1.1.)
3. Eades, P., Lin, X., & Smyth, W. F. (1993). *A fast and effective heuristic for the feedback arc set problem*. Information Processing Letters 47(6):319–323.
4. igraph. `feedback_arc_set` — `exact_ip` và `approx_eades`. https://r.igraph.org/reference/feedback_arc_set.html
17. Aho, A. V., Garey, M. R., & Ullman, J. D. (1972). *The Transitive Reduction of a Directed Graph*. SIAM J. Computing 1(2):131–137. DOI 10.1137/0201008
18. NetworkX. `transitive_reduction` — yêu cầu DAG. https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.dag.transitive_reduction.html
19. Clough, J. R., Gollings, J., Loach, T. V., & Evans, T. S. (2015). *Transitive reduction of citation networks*. Journal of Complex Networks 3(2):189–203. arXiv:1310.8224

### Dữ liệu tiên quyết và mật độ đồ thị

5. Zuev, K., & Stavrinides, P. (2025). *Breadth, depth, and flux of course-prerequisite networks*. Network Science. arXiv:2506.23510
6. Stavrinides, P. *Course-Prerequisite-Networks* (dữ liệu CUT, CIT, JHU). https://github.com/pstavrin/Course-Prerequisite-Networks
7. Li, I., Fabbri, A. R., Tung, R. R., & Radev, D. R. (2019). *What Should I Learn First: Introducing LectureBank for NLP Education and Prerequisite Chain Learning*. AAAI-19. arXiv:1811.12181
8. Yale-LILY. *LectureBank* (1.0 / 2.0 / CD). https://github.com/Yale-LILY/LectureBank
9. Liang, C., Ye, J., Wang, S., Pursel, B., & Giles, C. L. (2018). *Investigating Active Learning for Concept Prerequisite Learning*. EAAI-18 / AAAI. Dữ liệu: https://github.com/harrylclc/AL-CPL-dataset
12. Alzetta, C., và cộng sự (2025). *Prerequisite Relations Annotation Tool*. JASIST. https://asistdl.onlinelibrary.wiley.com/doi/10.1002/asi.24992

### Chất lượng đồ thị tri thức

10. Xue, B., & Zou, L. (2022). *Knowledge Graph Quality Management: A Comprehensive Survey*. IEEE TKDE. *(theo abstract — sau tường lửa IEEE)*
11. Seo, S., và cộng sự (2022). *Structural Quality Metrics to Evaluate Knowledge Graphs*. arXiv:2211.10011
29. Yang, R., và cộng sự (2024/2025). *Graphusion: Leveraging Large Language Models for Scientific Knowledge Graph Fusion and Construction in NLP Education*. arXiv:2407.10794; WWW 2025 Companion, DOI 10.1145/3701716.3717821

### Lý thuyết không gian tri thức

13. Falmagne, J.-C., & Doignon, J.-P. (2015). *Knowledge Spaces and Learning Spaces*. arXiv:1511.06757; chương 5, New Handbook of Mathematical Psychology, Cambridge UP.
14. Doignon, J.-P., & Falmagne, J.-C. (1985). *Spaces for the assessment of knowledge*. Int. J. Man-Machine Studies 23:175–196.
15. Stahl, C., & Hockemeyer, C. *kst: Knowledge Space Theory* (gói R, vignette). CRAN. https://cran.r-project.org/web/packages/kst/vignettes/kst.pdf
16. Heller, J., Steiner, C., Hockemeyer, C., & Albert, D. *Competence-Based Knowledge Structures for Personalised Learning* (CbKST). *(theo abstract và tài liệu gói CRAN)*

### Kiểm định bằng dữ liệu học viên

20. Vuong, A., Nixon, T., & Towle, B. (2011). *A Method for Finding Prerequisites Within a Curriculum*. EDM 2011.
21. Scheines, R., Silver, E., & Goldin, I. (2014). *Discovering Prerequisite Relationships among Knowledge Components*. EDM 2014, 355–356.
22. Brunskill, E. (2011). *Estimating Prerequisite Structure From Noisy Data*. EDM 2011. *(theo abstract)*
23. Desmarais, M. C., Meshkinfam, P., & Gagnon, M. (2006). *Learned Student Models with Item to Item Knowledge Structures* (POKS). UMUAI 16:403–434.
24. Käser, T., Klingler, S., Schwing, A. G., & Gross, M. (2017). *Dynamic Bayesian Networks for Student Modeling*. IEEE TLT 10(4):450–462.

### Hiệu chỉnh độ tin cậy của mô hình

25. Xiong, M., và cộng sự (2024). *Can LLMs Express Their Uncertainty? An Empirical Evaluation of Confidence Elicitation in LLMs*. ICLR 2024. arXiv:2306.13063
26. Groot, T., & Valdenegro-Toro, M. (2024). *Overconfidence is Key: Verbalized Uncertainty Evaluation in Large Language and Vision-Language Models*. arXiv:2405.02917
27. Zhao, T., Kang, J., & Tong, H. (2024). *Conformalized Link Prediction on Graph Neural Networks*. KDD 2024. arXiv:2406.18763
28. *Predicate-Conditional Conformalized Answer Sets for Knowledge Graph Embeddings* (CondKGCP). arXiv:2505.16877

### Xếp tầng, lập lịch, và vẽ đồ thị

30. Mallach, S. (2019). *A Natural Quadratic Approach to the Generalized Graph Layering Problem*. GD 2019. arXiv:1908.04104
31. Lawler, E., Lenstra, J. K., Rinnooy Kan, A., Shmoys, D., và cộng sự (2020). *Elements of Scheduling*. arXiv:2001.06005. (Đ.lý 2.21, Đ.lý 2.27)
32. Ullman, J. D. (1975). *NP-complete scheduling problems*. J. Computer and System Sciences 10(3):384–393.
33. Coffman, E. G. Jr., & Graham, R. L. (1972). *Optimal scheduling for two-processor systems*. Acta Informatica 1:200–213. *(theo abstract)*
34. Braschi, B., & Trystram, D. (1994). *A New Insight into the Coffman–Graham Algorithm*. SIAM J. Computing 23(3):662–669. *(theo abstract)* — sửa phân tích của Lam & Sethi (1977), SIAM J. Computing 6(3):518–536 *(chỉ có mô tả thứ cấp; phải kiểm lại toàn văn nếu trích trong bài báo)*
35. OGDF. `include/ogdf/layered/CoffmanGrahamRanking.h` (nhánh `master`, tải 2026-09-21).
36. Rüegg, U., và cộng sự (2016) §2 về xếp tầng đường dài nhất và độ rộng; NetworkX `topological_generations`.
37. Nederlof, J., Swennenhuis, C., & Węgrzycki, K. (2023). *A Subexponential Time Algorithm for Makespan Scheduling of Unit Jobs with Precedence Constraints*. arXiv:2312.03495
38. Gansner, E. R., Koutsofios, E., North, S. C., & Vo, K.-P. (1993). *A Technique for Drawing Directed Graphs*. IEEE TSE 19(3):214–230. https://www.graphviz.org/documentation/TSE93.pdf · mã: Graphviz `lib/common/ns.c`, `TB_balance()`
39. Healy, P., & Nikolov, N. S. (2001/2002). *How to Layer a Directed Acyclic Graph*, GD'01, LNCS 2265; và *A Branch-and-Cut Approach to the DAG Layering Problem*, GD'02, LNCS 2528:98–109. *(theo abstract)*
40. Nikolov, N. S., Tarassov, A., & Branke, J. (2005). *In search for efficient heuristics for minimum-width graph layering with consideration of dummy nodes*. ACM JEA 10. DOI 10.1145/1064546.1180618 *(theo abstract)*
47. Kahn, A. B. (1962). *Topological sorting of large networks*. CACM 5(11):558–562. · Meinke, J. G., & Bauer, C. R. *Topological sorting as a tool in curriculum planning*. ACM DOI 10.1145/800144.804757 *(chỉ tiếp cận được tiêu đề và mô tả thứ cấp)*

### Đánh giá thứ tự, thiết kế mô-đun, và tính ổn định của mô hình

41. Lapata, M. (2006). *Automatic Evaluation of Information Ordering: Kendall's Tau*. Computational Linguistics 32(4):471–484. https://aclanthology.org/J06-4002/
42. Miller, G. A. (1956). *The Magical Number Seven, Plus or Minus Two*. Psychological Review 63(2):81–97. https://psychclassics.yorku.ca/Miller/
43. Cowan, N. (2001). *The magical number 4 in short-term memory*. Behavioral and Brain Sciences 24(1):87–114. *(theo abstract)*
44. Rey, G. D., Beege, M., Nebel, S., Wirzberger, M., Schmitt, T. H., & Schneider, S. (2019). *A Meta-analysis of the Segmenting Effect*. Educational Psychology Review 31:389–419.
45. Rohrer, D., Dedrick, R. F., & Burgess, K. (2014). Thí nghiệm xen kẽ bài tập toán lớp 7 (n = 140, 9 tuần).
46. Donoghue, G. M., & Hattie, J. A. C. (2021). Tổng hợp meta về distributed practice (d = 0,85, N = 152 952) so với interleaving (d = 0,47, N = 972, I² = 88).
48. *Position bias trong sắp thứ tự bằng LLM* (2026). arXiv:2608.03091, Bảng 1 (K = 25, zero-shot).

---

## Phụ lục — cách tái lập số đo

Mọi số ở mục 2 và mục 3.2 lấy từ artifact trên đĩa, không gọi API. Script đo nằm trong thư mục nháp của phiên
(`do_a9_a10_v2.py` — bảng mục 2; `mo_phong_stage.py` — mô phỏng mục 2.7; `vang_vs_may.py` — mục 2.8). Chúng đọc
`artifacts/graph/<doc>/<v>/graph.json` và `artifacts/a8-gold/vang-hoi-y.json`. Khi cắt vé cho E9–E11, các phép đo
này phải chuyển vào `src/doc2roadmap/domain/gold_scoring.py` để có test và để tái lập được ngoài phiên.
