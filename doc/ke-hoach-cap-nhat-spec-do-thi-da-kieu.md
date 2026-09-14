# Kế hoạch cập nhật `spec-addendum.md` cho đồ thị đa kiểu node

2026-08-29 · Nguồn: [nghiên cứu A3](../report/nghien-cuu-a3-trich-xuat-thuc-the.md) mục 5c
Trạng thái: **kế hoạch, chưa thực hiện** — chờ chốt ba quyết định ở mục 1

---

## 0. Vì sao phải sửa spec chứ không chỉ ghi trong report

Ý định đồ thị đa kiểu node đã nêu ba lần trong quá trình thiết kế, nhưng trong repo nó chỉ tồn tại
dưới dạng **một dòng hoãn quyết định** ở ADR 0002. `spec-addendum.md` — tài liệu người triển khai sẽ
đọc — **mô tả một đồ thị chỉ có khái niệm** từ đầu đến cuối.

Hậu quả nếu không sửa: người làm A3 dựng đúng theo spec, và **hai bước sau đó vỡ âm thầm** (mục 2).
Đây không phải rủi ro giả định — nó là hệ quả số học trực tiếp của việc thêm node vào một đồ thị mà
các công thức phía sau giả định mọi node đều là khái niệm.

---

## 1. Ba quyết định phải chốt trước khi sửa

Kế hoạch dưới đây giả định câu trả lời **A** cho cả ba. Đổi câu trả lời thì đổi phạm vi sửa.

| # | Câu hỏi | Phương án A (giả định) | Phương án B |
|---|---|---|---|
| Q1 | Loại nào thành node? | **Hình (19) + bảng (60)**; công thức (258) là thuộc tính | Cả ba thành node |
| Q2 | Một đồ thị hay hai? | **Một đồ thị, node mang `node_type`**, lọc **chỉ ở nơi thuật toán coi cạnh là thứ tự** (xem 5.0) | Hai đồ thị tách biệt, hội tụ ở tầng trình bày |
| Q3 | Ảnh không chú thích? | **Mô hình thị giác sinh mô tả + tầng kiểm định chéo** (khuôn VaLiK) | Chỉ marker, không mô tả — node rỗng nghĩa |

Q1 dựa trên số đo: 258 công thức sẽ chiếm khoảng nửa đồ thị, và nội dung thô của chúng đã biết là lộn
xộn thứ tự (vòng 8). Q2 dựa trên tiền lệ có sẵn trong chính spec: A8 đã dùng khuôn "cạnh phụ trợ không
tham gia topo" cho `relates_to` — chỉ mở rộng từ cạnh sang node.

---

## 2. Hai chỗ sẽ thành lỗi câm — ưu tiên cao nhất

Đây là lý do kế hoạch này không thể hoãn tới lúc viết A3.

### 2.1 🔴 A9a — cổng chất lượng đếm nhầm mẫu số, gây fallback oan

Spec hiện tại:

> *"nếu số edge `requires` < ~0.5 × **số node**, hoặc > 60% node cô lập → tài liệu không có cấu trúc
> tiên quyết rõ → chuyển sang fallback thứ tự chương"*

Thêm 79 node hình+bảng vào mẫu số mà tử số (`requires`) **không đổi** — vì hình không thể là tiên quyết
của gì. Ví dụ số: 200 khái niệm, 150 cạnh `requires` ⇒ tỉ lệ 0,75, qua cổng. Thêm 79 node media ⇒
mẫu số 279, tỉ lệ tụt còn **0,54** — sát ngưỡng; tài liệu nhiều hình sẽ **rơi xuống dưới 0,5 và bị
tuyên là "không có cấu trúc tiên quyết"** dù đồ thị khái niệm hoàn toàn lành.

Tương tự vế thứ hai: node media **không có cạnh `requires` nào** nên chúng luôn được đếm là "node cô
lập" theo phép đo hiện tại — 79/279 = 28% cô lập **miễn phí**, ăn gần nửa ngưỡng 60%.

Hậu quả: cả tài liệu bị đẩy sang lộ trình fallback theo thứ tự chương. **Không có gì báo lỗi** — pipeline
chạy xong, ra kết quả tệ hơn, và không ai biết vì sao.

**Sửa:** mọi phép đo ở A9a tính trên **đồ thị con `node_type = concept`**. Ghi rõ trong spec.

### 2.2 🔴 A10 — Kahn layering dồn toàn bộ hình vào giai đoạn 1

Spec hiện tại:

> *"lớp 1 = mọi node **in-degree 0**; gỡ lớp 1, node nào lộ ra in-degree 0 thành lớp 2..."*

Node media không có cạnh `requires` trỏ vào ⇒ **in-degree 0** ⇒ **toàn bộ 79 hình và bảng rơi vào
lớp 1**. Giai đoạn học đầu tiên của người dùng trở thành một đống mọi hình ảnh trong sách.

Đây là lỗi nhìn thấy ngay khi mở UI, nhưng chỉ nhìn thấy **sau khi đã chạy hết pipeline** — muộn và tốn.

**Sửa:** Kahn chạy trên đồ thị con `concept`. Node media **không có `layer` riêng**; chúng được gắn vào
stage theo khái niệm mà chúng nối tới (`stage = stage của khái niệm sớm nhất mà nó minh hoạ`).

---

## 3. Bảng đầy đủ các chỗ phải sửa

Đánh dấu mức: 🔴 lỗi câm nếu bỏ qua · 🟡 mô tả sai gây hiểu nhầm · 🟢 bổ sung để tận dụng cơ hội

| # | Mục | Mức | Nội dung sửa |
|---|---|:---:|---|
| 1 | **§0 Kiến trúc tổng thể** | 🟡 | Sơ đồ ASCII ghi *"A3. Extract concepts"* → đổi thành *"Extract concepts + thực thể media"*. Thêm một dòng ở phần mô tả: đồ thị có nhiều `node_type`, chỉ `concept` tham gia DAG tiên quyết |
| 2 | **A3 Extract** | 🔴 | Thêm `node_type` vào schema output. Thêm luật trích thực thể media từ `image_refs`/`table_refs` của chunk. Thêm luật ảnh-không-chú-thích (Q3). Bổ sung: **bắt buộc bằng chứng cho concept**, không chỉ cho edge |
| 3 | **A4 Merge** | 🟢 | Ghi rõ: **media không đi qua ba lớp lọc**. Hai hình giống hệt đã có **cùng `image_id`** (băm nội dung từ B0) ⇒ khử trùng bằng code, **không tốn lời gọi LLM nào**. Đây là món quà B0 để lại mà spec chưa dùng |
| 4 | **A5 Description** | 🟡 | Đường sinh mô tả cho media khác concept: caption nếu có, mô tả thị giác nếu không, **kèm tầng kiểm định** — không đọc `source_chunk_ids` như concept |
| 5 | **A6 Semantic graph** | 🟢 | Co-occurrence với media **không cần suy ra từ văn bản** — `image_refs` của chunk đã cho biết chính xác hình nào nằm cùng chunk với khái niệm nào. Bằng chứng mạnh hơn co-occurrence văn bản, và **tất định**. Quan trọng hơn: loại cạnh `relates_to` (đề xuất ở `spec-preview.md` §8.1) **chưa có nguồn dữ liệu nào được chỉ định** — nguồn sẵn có duy nhất là cạnh phụ trợ của A6 (cosine + co-occurrence), tức quan hệ **suy ra từ mô hình**. Liên kết qua media cho nguồn thứ hai **có căn cứ trong tài liệu** và không trôi khi đổi mô hình embedding. Đây là chỗ nên chốt nguồn cho `relates_to` |
| 6 | **A7 Cluster** | 🟢 | Leiden chạy trên **đồ thị đầy đủ** — media tham gia và nhận `cluster_id` của riêng nó. Media là **tín hiệu gom cụm có căn cứ**: tác giả đặt các khái niệm vào chung một hình. Đo trên corpus: 79 media, **bậc tối đa 2**, 94% bậc 1, **0 hub** ⇒ không có rủi ro gộp nhầm cụm. Thêm **dây bẫy**: media bậc ≥ 5 phát cảnh báo và bị hạ trọng số theo `1/(bậc−1)` — chưa cần hôm nay, cần khi corpus lớn |
| 7 | **A8a Prerequisite** | 🔴 | Ghi tường minh: `requires` **chỉ được nối concept↔concept**. Thêm bảng loại cạnh mới: `illustrates`, `tabulates` (media→concept) — **không tham gia topo sort**, cùng khuôn `relates_to` đã có |
| 7b | **A8b Liên cụm** | 🟢 | Boundary concept hiện phải **tính** (*"concept có co-occurrence với chunk thuộc cluster khác"*). Một media được tham chiếu từ hai cụm khác nhau **tự nó là boundary object** — biết ngay từ refs, tất định, không cần suy. Đây là nguồn ứng viên liên cụm miễn phí mà spec chưa dùng |
| 8 | **A9a Quality gate** | 🔴 | Mẫu số và phép đếm cô lập tính trên đồ thị con `concept` — xem mục 2.1 |
| 9 | **A9b Remove cycle** | 🔴 | Tarjan chạy trên đồ thị con `requires`. **Không phải chuyện hình thức**: chạy trên đồ thị đầy đủ thì `A requires B` + `B illustrated_by F` + `F illustrates A` thành **chu trình giả**, và A9b sẽ cắt một cạnh `requires` thật để gỡ nó. Thuật toán không phân biệt kiểu cạnh nếu không ai bảo nó |
| 10 | **A9c Transitive reduction** | 🔴 | Chạy trên đồ thị con `requires`. Nếu chạy trên đồ thị đầy đủ, cạnh `illustrates` có thể bị xoá nhầm vì "đã có đường khác" |
| 11 | **A10 Layering** | 🔴 | Kahn trên đồ thị con `concept` — xem mục 2.2. Thêm luật gắn media vào stage. Schema stage thêm trường `media_ids` bên cạnh `concept_ids` |
| 12 | **A11 Stage enrichment** | 🟢 | Hình và bảng của stage là nguyên liệu cho `summary` và `quiz` — câu hỏi có hình minh hoạ. Ghi vào để không bỏ phí |
| 13 | **A12 Gắn stage_id** | 🟡 | Media cũng cần `stage_id` để gia sư ở pha B lọc theo phạm vi — không thì agent sẽ khoe hình của chương chưa học |
| 14 | **A13 Human review** | 🟢 | Thêm mục soát: liên kết media↔concept sai là loại lỗi dễ thấy bằng mắt nhất, nên đưa lên đầu danh sách review |
| 15 | **Tầng 1 (biến thể)** | 🔴 | *"Output CÔ ĐỌNG: candidate concepts + edge đề xuất"* → thêm ứng viên media. Ghi rõ media lấy từ refs của chunk chứ **không phải** do LLM tự nhận ra |
| 16 | **Tầng 2a Merge cụm** | 🟢 | Media **bỏ qua hoàn toàn** tầng agent — promote thẳng như "cụm một ứng viên". Tiết kiệm chi phí, và tất định hơn |
| 17 | **Hợp đồng tool 2b** | 🔴 | `add_edge` phía executor phải **từ chối** `requires` khi một đầu không phải `concept` — đúng chỗ spec đã đặt các kiểm tra cấu trúc khác. Tool `search_similar_node` cần lọc theo `node_type` |
| 18 | **Tầng 3 Validate** | 🟡 | Check cycle toàn cục trên đồ thị con `requires`. Self-review thêm mục: media mồ côi (không nối khái niệm nào) |
| 19 | **B1 UI graph** | 🟢 | *"node = concept"* → media node render khác (thumbnail cho hình). Đây là chỗ tính năng **lộ ra cho người dùng** |
| 20 | **B2 Tutor agent** | 🔴 | Bộ tool hiện có `search_stage_content`, `lookup_concept`, `get_stage_info` — **không tool nào lấy được hình**. Thêm `get_media_for_concept(concept_id)`. **Không có tool này thì toàn bộ tính năng vô nghĩa** — đồ thị có hình mà agent không lấy ra được |
| 21 | **B3 Assessment** | 🟢 | Quiz có hình: câu hỏi tham chiếu `media_id`, UI render kèm |
| 22 | **Công nghệ đề xuất** | 🟡 | Bảng node cần cột `node_type`; kho ảnh đã có sẵn từ B0 (lưu theo băm) — chỉ cần trỏ tới, không dựng mới |
| 23 | **Thứ tự triển khai MVP** | 🟡 | Chốt media node vào vòng nào. Đề nghị: **luật lọc `concept` cho A9/A10 vào MVP** (rẻ, chặn hai lỗi câm), **media node vào vòng 2** |

---

## 4. Thứ tự thực hiện

Chia ba đợt theo mức rủi ro, không theo thứ tự mục trong tài liệu.

### Đợt 1 — Chặn hai lỗi câm (làm được ngay, không cần chốt Q1–Q3)

Mục **8, 9, 10, 11, 17** cộng một câu ở mục **7**, và luật ngữ nghĩa ở **5.0**.

Nội dung: ghi tường minh rằng **thuật toán nào coi cạnh là quan hệ thứ tự thì chạy trên đồ thị con
`concept`** (A9a, A9b, A9c, A10), và `requires` chỉ nối concept↔concept. **Không** viết luật này thành
danh sách vị trí — viết thành tiêu chí, kèm bốn ví dụ.

Đợt này **có giá trị kể cả khi không bao giờ làm media node** — `spec-preview.md` §8.1 đã có ba loại
cạnh phụ trợ (similarity, co-occurrence, mention) cộng loại `relates_to` đề xuất, và **cùng loại lỗi
mẫu số sẽ xảy ra** nếu ai đó đếm cả cạnh phụ trợ khi đo mật độ hoặc chạy Tarjan. Đây là lý do đợt này
đi trước và không phụ thuộc quyết định nào.

> **Lưu ý tài liệu:** `relates_to` và ngữ nghĩa cạnh nằm ở `spec-preview.md` §8.1, **không** ở
> `spec-addendum.md`. Hai tài liệu đang mô tả cùng một hệ thống bằng hai hệ nhãn khác nhau (A1–A13 vs
> T1–T4). Khi sửa phải sửa **cả hai** hoặc chốt một tài liệu làm nguồn chân lý — nếu không sẽ lặp lại
> đúng mâu thuẫn A2 vừa gỡ.

### Đợt 2 — Đưa media node vào luồng chính (sau khi chốt Q1–Q3)

Mục **1, 2, 3, 4, 5, 6, 15, 16, 22**.

Trọng tâm: A3 schema có `node_type`, và ghi rõ **hai món quà B0 để lại mà spec chưa dùng** —
khử trùng media miễn phí bằng băm nội dung (mục 3), và co-occurrence media tất định từ refs (mục 5).

### Đợt 3 — Đường ra tới người dùng

Mục **12, 13, 14, 19, 20, 21**.

Trọng tâm là mục **20**: thêm tool lấy media cho gia sư. Đây là **lý do tồn tại của cả tính năng** —
nếu chỉ làm đợt 1 và 2, đồ thị có node hình nhưng không ai nhìn thấy hình.

---

## 5. Nguyên tắc viết, để bản sửa không tự mâu thuẫn

### 5.0 Luật lọc phát biểu theo **ngữ nghĩa**, không theo danh sách

Bản đầu kế hoạch này liệt kê "lọc ở năm chỗ". Danh sách thì người sau áp sai chỗ — và chính tôi suýt
bỏ sót A9b khi viết theo danh sách. Luật đúng:

> **Lọc `concept` đúng ở nơi thuật toán diễn giải cạnh như quan hệ thứ tự** — A9a (đo mật độ cấu trúc
> tiên quyết), A9b (chu trình trong thứ tự), A9c (dư thừa trong thứ tự), A10 (phân tầng theo thứ tự).
> **Mọi nơi khác — A6, A7, A8b — càng nhiều kiểu càng tốt**, vì media là bằng chứng liên kết có căn cứ.

Phát biểu thế thì người triển khai gặp một thuật toán mới cũng tự trả lời được: *nó có coi cạnh là thứ
tự không?*

### 5.1 Vì sao thả lỏng ở 2b là an toàn

Không phải vì agent tự giác, mà vì spec đã đặt kiểm tra cấu trúc **ở executor phía code** trong
`add_edge` — agent cứ đề xuất, code từ chối `requires` có đầu không phải `concept`. Đúng triết lý spec
đã ghi: *"mọi kiểm tra cấu trúc nằm trong code của tool, không giao LLM tự giác"*. Giữ nguyên chỗ đặt
kiểm tra đó khi sửa; đừng chuyển sang dặn dò trong prompt.

### 5.2 Còn lại

1. **Một đồ thị, lọc khi dùng** — không mô tả "hai đồ thị". Mọi chỗ nói về thuật toán phải nêu rõ nó
   chạy trên đồ thị con nào.
2. **Đặt tên đồ thị con một lần, dùng lại xuyên suốt** — đề nghị: *"đồ thị tiên quyết"* (chỉ `concept`
   + cạnh `requires`) và *"đồ thị đầy đủ"*. Từ điển `CONTEXT.md` thêm hai mục này.
3. **Media không bao giờ đi đường agent nếu đi đường code được** — khử trùng bằng băm, co-occurrence
   bằng refs, gắn stage bằng luật. Chỉ dùng LLM cho việc duy nhất nó cần làm: mô tả ảnh không chú thích.
4. **Mỗi chỗ sửa nêu rõ nó chạm bất biến nào** — như B0 đã làm với I1–I25. Ứng viên bất biến mới:
   *"không cạnh `requires` nào có đầu không phải `concept`"* và *"mọi node media nối ít nhất một concept"*.
