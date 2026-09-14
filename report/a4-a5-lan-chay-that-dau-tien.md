# A4/A5 — Kết quả chạy thật: quan hệ kiểu mở ở 2a và luật kiểm nhất quán

Ngày chốt: 2026-09-14 (bản mặc định trước: 2026-09-12). Bộ đánh giá có 416 mục tại
`tests/fixtures/a4/gold-blind.json`, SHA-256
`1df2167ca2a9df5b97cdd232e5ed251f37840dd1f94d738143af72f11012cd55`.
Chủ dự án đã chấp nhận dùng bộ này; người gán là Claude, không phải người độc lập, nên các điểm dưới đây là mốc kỹ
thuật theo rubric hiện hành chứ chưa phải độ đúng khách quan. Nhãn vàng không xuất hiện trong prompt phán.

## Bản mặc định hiện hành (2026-09-14): `gemini-3.1-flash-lite`, prompt v3, luật nhất quán

Merge, vá cụm và A5 dùng temperature 0, tối đa 8.192 output token; concurrency 4 trong từng stage của một tài liệu.
Lượt vá dùng cùng prompt, schema và ba lớp kiểm với lượt cụm. 2a trả thêm quan hệ kiểu mở giữa các node đã tách (ADR
0007). A5 dùng luật ngôn ngữ `token-majority-prose-vi20-v2`.

Chạy thật vào kho chính ở commit `c418499`: 138 lời gọi flash-lite. Chạy lại khi chặn mạng thì cả bốn tài liệu
`reused=true`. Node, cạnh và cụm đề cử giống hệt hai lượt chạy ở kho thử.

| Tài liệu | Canonical | Precision | Recall | F1 | TP / FP / FN | Recall subtype | Subtype sai |
|---|---|---:|---:|---:|---|---:|---:|
| nhap-mon-ml | v7 | 0,875 | 0,700 | 0,778 | 7 / 1 / 3 | 0,545 | 3 |
| xstk-ch3-1 | v7 | 0,875 | 0,438 | 0,583 | 7 / 1 / 9 | 0,600 | 8 |
| baocao-canhan | v8 | 1,000 | 1,000 | 1,000 | 11 / 0 / 0 | 0,500 | 1 |
| naive-bayes | v7 | 1,000 | 1,000 | 1,000 | 10 / 0 / 0 | 0,556 | 1 |
| **Gộp bốn tài liệu** | | **0,946** | **0,745** | **0,833** | **35 / 2 / 12** | **27/47 = 0,574** | **13** |

Hai ca gộp sai: `Bài toán phân loại` / `Bài toán phân cụm` (bộ vàng: *liên quan*) và `Đường hồi quy mẫu Y theo X` /
`Đường hồi quy mẫu` (bộ vàng: cha–con). Cả hai không mang tín hiệu mâu thuẫn nên luật R1/R2 không bắt được. Luật bắt 8
lượt mâu thuẫn; cả 8 sửa được ở lần thử lại, không cụm nào bị hoãn.

| Tài liệu | Node text / media | Cạnh cuối | Nhóm/cặp hoãn | Cụm vá phán / gộp | Quan hệ loại | Quan hệ 2a (trùng A3) | A5 giữ | Viết lại ngôn ngữ / hỗ trợ | Tổng hợp | Fallback | Cờ mâu thuẫn |
|---|---|---:|---|---|---:|---:|---:|---|---:|---:|---:|
| nhap-mon-ml | 75 / 9 | 67 | 0 / 0 | 7 / 1 | 1 | 20 (3) | 55 | 0 / 1 | 19 | 0 | 0 |
| xstk-ch3-1 | 98 / 53 | 137 | 0 / 0 | 21 / 1 | 0 | 42 (1) | 69 | 2 / 1 | 26 | 0 | 0 |
| baocao-canhan | 36 / 3 | 25 | 0 / 0 | 6 / 1 | 1 | 8 (1) | 11 | 12 / 0 | 13 | 0 | 0 |
| naive-bayes | 34 / 14 | 57 | 0 / 0 | 4 / 0 | 3 | 10 (0) | 12 | 10 / 0 | 12 | 0 | 1 |

Lịch sử redirect tăng từ 7 / 7 / 9 / 7 lên 10 / 9 / 9 / 8 (báo cáo / slide / ML / XSTK), vì một số node đổi thành
viên. Id cũ luôn trỏ tới node còn sống (ADR 0005).

### Bản mặc định trước (2026-09-12): prompt v1, chỉ `subtype_of`

Các mục phía dưới (F73, F76, A/B F72, F75) được đo trên bản này.

| Tài liệu | Canonical | Precision | Recall | F1 | TP / FP / FN | Recall subtype | Subtype sai |
|---|---|---:|---:|---:|---|---:|---:|
| nhap-mon-ml | v6 | 1,000 | 0,700 | 0,824 | 7 / 0 / 3 | 0,818 | 5 |
| xstk-ch3-1 | v6 | 1,000 | 0,438 | 0,609 | 7 / 0 / 9 | 0,760 | 11 |
| baocao-canhan | v7 | 1,000 | 0,909 | 0,952 | 10 / 0 / 1 | 1,000 | 1 |
| naive-bayes | v6 | 1,000 | 0,700 | 0,824 | 7 / 0 / 3 | 0,556 | 2 |
| **Gộp bốn tài liệu** | | **1,000** | **0,660** | **0,795** | **31 / 0 / 16** | **35/47 = 0,745** | **19** |

So với lần chạy trước sửa F61–F69, kết quả đổi từ 26 TP / 3 FP / 21 FN thành 31 TP / 0 FP / 16 FN. Mức tăng ròng
5 TP gồm sáu cặp lấy lại — năm cặp của F61 và #99 `Bài toán phân loại` / `Phân loại` — trừ một cặp mất: #218
`Tiêu chuẩn kiểm định χ0^2` / `Tiêu chuẩn kiểm định χ 0 2`. F69 đưa ba FP về 0. Trong bốn repair merge còn có #260
`Ước lượng phương sai` / `Khoảng ước lượng của phương sai tổng thể`, nhưng nhãn vàng là *không chắc* nên cặp này
không vào TP/FP/FN. Bốn lượt chạy không có nhóm/cặp deferred hay mâu thuẫn bắc cầu; recall đề cử là 47/47.

| Tài liệu | Node text / media | Cạnh cuối | Nhóm/cặp hoãn | Cụm vá phán / gộp | Subtype loại | A5 giữ | Viết lại ngôn ngữ / hỗ trợ | Tổng hợp | Fallback | Cờ mâu thuẫn |
|---|---|---:|---|---|---:|---:|---|---:|---:|---:|
| nhap-mon-ml | 77 / 9 | 66 | 0 / 0 | 7 / 2 | 1 | 58 | 0 / 0 | 19 | 0 | 0 |
| xstk-ch3-1 | 99 / 53 | 129 | 0 / 0 | 21 / 1 | 4 | 67 | 2 / 3 | 27 | 0 | 1 |
| baocao-canhan | 37 / 3 | 22 | 0 / 0 | 6 / 1 | 0 | 13 | 12 / 0 | 12 | 0 | 0 |
| naive-bayes | 36 / 14 | 55 | 0 / 0 | 4 / 0 | 1 | 14 | 11 / 0 | 11 | 0 | 1 |

Mọi tài liệu có `document_language=vi`. Riêng `naive-bayes` trước đây bị bảng số và code kéo thành `en`; bỏ chunk
thuần bảng/code/công thức/hình đã sửa đúng ca này. Manifest mới cũng mang số cảnh báo A3, số nhóm gộp thêm,
`subtype_rejected`, `deferred_pairs` và metric viết lại draft không hợp lệ.

## Cập nhật luật tên chuẩn F73

`algorithm_id` đã đổi thành `a4-names-v2`: tên thuần chữ xếp trên tên có token ký hiệu và viết tắt; tên dài được
đếm rồi che trước để tên ngắn không đếm chồng lấn; hòa giữa hai tên lồng nhau chọn tên chứa tên kia. Chạy lại từ
các phiên bản trong bảng trước bằng luật mới đổi đúng tám tên:

| Tài liệu | Tên cũ | Tên mới |
|---|---|---|
| nhap-mon-ml | `Phân loại` | `Bài toán phân loại` |
| baocao-canhan | `Branching` | `Branching strategy` |
| baocao-canhan | `Transaction` | `Database Transaction` |
| baocao-canhan | `WebSockets` | `WebSocket` |
| naive-bayes | `Bernoulli Naive` | `Bernoulli Naive Bayes` |
| naive-bayes | `Maximum Likelihood` | `Maximum Likelihood Estimation` |
| naive-bayes | `Naïve Bayes` | `Naïve Bayes Classification` |
| naive-bayes | `Prior` | `Prior probability` |

XSTK không đổi tên. Tập node ID và membership của cả bốn tài liệu giữ nguyên; không phát sinh redirect mới, còn
lịch sử redirect 7 / 7 / 9 / 7 cũng được giữ nguyên. Tất cả 63 merge, 38 repair và 20 lô kiểm singleton dùng lại
cache; chỉ gọi A5 tám lần để viết lại description chịu ảnh hưởng bởi tên/alias mới: ML 1, báo cáo 3, slide 4. Điểm
bộ vàng vẫn là 31/0/16.

## Làm sạch alias F76

`algorithm_id` hiện là `a4-names-v3`. Alias không phải ký hiệu có cùng `name_key` với tên chuẩn không còn được đưa
vào node. Chạy thật lại bốn tài liệu cho kết quả:

- đúng bốn node bị ảnh hưởng: `Modeling`, `Giải thuật học`, `Concurrency`, `Race Condition`;
- loại sáu entry alias trên bốn node: hai node báo cáo mỗi node có hai entry cùng tên nhưng khác bằng chứng;
- tên, ID, thành viên, cạnh và lịch sử redirect giữ nguyên;
- dùng lại 63 quyết định merge, 38 repair và 20 lô kiểm singleton;
- chạy lại bốn A5 job. `Race Condition` bị từ chối validation một lần rồi retry thành công, nên chỉ số thực là năm
  lần gọi mô hình: ML 2, báo cáo 3;
- điểm bộ vàng giữ nguyên `31/0/16`.

## Xung đột `subtype_of`–A3 (F75)

Luật: nếu một cạnh `subtype_of` của 2a trùng cặp node với cạnh A3 mang nghĩa khác "là một loại", **giữ cả hai
cạnh**. Các kiểu A3 tính là xung đột: `component_of`, `uses`, `solves`, `prevents`, `causes`, `computed_by`,
`contrasts_with`, bất kể chiều. Xung đột được ghi dòng `subtype_conflicts_a3` vào nhật ký, kèm kiểu cạnh A3, và vào
chỉ số cùng tên. Config thêm `"subtype_rule": "a3-conflict-log-v1"`.

Bản đầu của luật thì **xoá** `subtype_of` khi có xung đột. Đo trên bộ vàng, bản đó có hại:

- trên bốn nhánh A/B, nó xoá 17 cạnh đúng và chỉ bắt được 2 cạnh sai;
- riêng mặc định, nó xoá 4 cạnh đúng, 2 cạnh sai và 1 cạnh ngoài nhãn (`Mutex ⊂ Race Condition`), làm precision
  subtype tụt từ 0,635 xuống 0,630;
- 17 cạnh đúng thuộc 5 cặp: 3 biến thể `Gaussian/Multinomial/Bernoulli Naive Bayes` mà A3 gắn `component_of` vào
  `Naïve Bayes`, và 2 bước `Làm sạch/Biến đổi dữ liệu` của `Tiền xử lý dữ liệu`. Hai bước này nằm ranh giới loại/bước;
  bộ vàng gán là loại.

Vì vậy luật chốt chỉ ghi xung đột, không xoá.

Chạy lại bằng CLI thật khi LLM bị bẫy (`start_session` ném lỗi) tạo ra báo cáo v7, slide v6, ML v6, XSTK v6.

| Tài liệu | Xung đột ghi nhận |
|---|---|
| baocao-canhan | `Mutex ⊂ Race Condition` (A3 `uses`) |
| naive-bayes | `Multinomial Naive Bayes`, `Gaussian Naive Bayes ⊂ Naïve Bayes Classification` (A3 `component_of`) |
| nhap-mon-ml | `Làm sạch dữ liệu`, `Biến đổi dữ liệu ⊂ Tiền xử lý dữ liệu` (A3 `component_of`); `Bài toán học máy ⊂ Học máy` (A3 `uses`) |
| xstk-ch3-1 | `Kiểm định giả thiết thống kê ⊂ Bài toán kiểm định giả thiết thống kê` (A3 `component_of`) |

- Kết quả: 0 lời gọi LLM. Dùng lại 63 merge, 38 vá, 20 lô kiểm singleton và 97 mô tả.
- Node, thành viên, cạnh và redirect giống hệt phiên bản trước. Nhật ký chỉ thêm 7 dòng xung đột, cộng dấu dùng lại
  trên 4 dòng A5 vốn được gọi mới ở lượt F76.
- Điểm bộ vàng giữ `31/0/16`.

**`subtype_of` mà 2b nhận**: 61 cạnh; trên cặp có nhãn, 33 cạnh đúng và 19 cạnh sai, tức precision 0,635.

Trong 19 cạnh sai:
- 8 cạnh nối hai tên bộ vàng gán *cùng*, ví dụ `Docker hóa ⊂ Container hóa`;
- 11 cạnh nối hai tên chỉ liên quan, ví dụ `Học máy ⊂ Học`, `Mạng nơron ⊂ Trí tuệ nhân tạo`.

2b phải coi `subtype_of` là đề xuất cần kiểm lại (spec D7).

## A/B model phán và prompt (F72)

A/B đổi model phán merge/vá và prompt phân hoạch; A5 luôn là flash-lite. Mọi nhánh dùng chung nguồn, đồ thị đề cử
(vector tên phát lại từ fixture), schema, generation config và bộ vàng. Luật chọn được viết **trước khi chạy**:

1. Precision gộp ≥ 0,95.
2. Precision `subtype_of` không thấp hơn mặc định.
3. Trong các nhánh qua hai cổng, F1 gộp cao nhất thắng.
4. Chênh F1 ≤ 0,02 coi là hoà: ưu tiên flash-lite, rồi prompt hiện hành.

| Nhánh | Model phán | Prompt | TP / FP / FN | Precision | Recall | F1 | Subtype đúng / 47 | Subtype sai | Precision subtype | Lượt thử hỏng phân hoạch |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| **A — mặc định** | flash-lite | v1 hiện hành | 31 / 0 / 16 | **1,000** | 0,660 | 0,795 | **35** | 19 | 0,635 | 0 |
| B | pro-preview | v1 | 26 / 1 / 21 | 0,963 | 0,553 | 0,703 | 19 | 0 | 1,000 | 1 |
| C0 | flash-lite | v2 (lỗi định dạng) | 31 / 2 / 16 | 0,939 | 0,660 | 0,775 | 26 | 0 | 1,000 | 48 |
| C | flash-lite | v2.1 | 38 / 3 / 9 | 0,927 | **0,809** | **0,864** | 27 | 0 | 1,000 | 0 |
| D | pro-preview | v2.1 | 38 / 7 / 9 | 0,844 | 0,809 | 0,826 | 13 | 0 | 1,000 | 0 |
| E — hậu kiểm | flash-lite | v1.1 | 25 / 0 / 22 | 1,000 | 0,532 | 0,694 | 33 | 10 | 0,756 | 22 |

Cách tính các cột subtype:
- *Subtype đúng / 47* đếm cặp cha–con của bộ vàng có cạnh đúng chiều.
- *Subtype sai* đếm cạnh nằm trên cặp có nhãn mà không phải cặp cha–con đúng chiều.
- *Precision subtype* = cạnh đúng / (cạnh đúng + cạnh sai), tính trên cạnh không lọc.

**Kết luận: giữ A (flash-lite + prompt hiện hành).**
- A và B qua cả hai cổng; A hơn B 0,092 F1.
- C và D trượt cổng precision gộp. v2.1 gộp tên chung với tên riêng mà bộ vàng gán cha–con:
  `Giá trị tới hạn t α` / `Giá trị tới hạn`, `Độ chính xác` / `Độ chính xác trong ước lượng tỉ lệ`,
  `Đường hồi quy mẫu Y theo X` / `Đường hồi quy mẫu`. Nguyên nhân là mệnh đề "tên cắt cụt, tên kèm ký hiệu là biến
  thể".
- Chủ dự án chốt thêm: dev chỉ dùng flash-lite cho mọi khâu LLM.

Các prompt đã thử:
- **v2** và **v2.1** viết một lần, không lấy ví dụ từ corpus hay bộ vàng.
- **v2** thiếu câu đòi dùng `group_id`. Flash-lite ghi tên nhóm thay id ở 48 lượt thử (báo cáo 8, slide 13, ML 11,
  XSTK 16), nên nhánh Pro + v2 bị dừng giữa chừng.
- **v2.1** chỉ thêm đúng câu đó; nội dung luật giữ nguyên.
- **v1.1** = v1 cộng riêng hai câu luật subtype của v2.1. Nhánh này chọn **sau khi** đã thấy điểm, nên được viết luật
  riêng trước khi chạy: precision gộp ≥ 0,95, F1 ≥ 0,775, precision subtype ≥ 0,90. Nó trượt hai cổng sau. Lượt
  thử hỏng quay lại: 20 lượt ghi tên nhóm thay id, 2 lượt thiếu/lặp nhóm. Hệ quả là 16 nhóm bị hoãn, recall tụt.

Không thử thêm biến thể nào trên bộ vàng này: làm tiếp là chỉnh prompt theo nhãn đã thấy.

Hai điều còn lại:
- Mặc định bỏ sót 16 cặp *cùng*; v2.1 cho thấy một phần do câu "chỉ bằng chứng nguyên văn".
- `subtype_of` của mặc định có 19 cạnh sai.

Biến thể prompt sau nên sửa riêng mệnh đề cắt cụt/ký hiệu, luôn giữ câu `group_id`, và đo trên **nhãn mới**.

Artifact các nhánh nằm ở `artifacts/a4-ab/`; `canonical/latest` là nhánh A. Lệnh tái lập một nhánh (gọi mô hình
thật):

```powershell
.\.venv\Scripts\python.exe scripts\run_a4_arm.py --partition-prompt scripts\a4_ab_prompts\v2.1.txt `
    --out artifacts/a4-ab/gemini-3.1-flash-lite-prompt-v2.1 --doc-id baocao-canhan --doc-id naive-bayes `
    --doc-id nhap-mon-ml --doc-id xstk-ch3-1
```

Không truyền `--judge-model` thì dùng `DOC2ROADMAP_MERGE_MODEL_ID`. Kiểm tái lập: chạy lại nhánh E khi chặn mạng
(`--partition-prompt scripts\a4_ab_prompts\v1.1.txt --out artifacts/a4-ab/gemini-3.1-flash-lite-prompt-v1.1`) cho
`reused=true` ở cả bốn tài liệu. Nhánh C0, C và D chạy trước khi luật F75 đổi sang chỉ ghi: cạnh xung đột của chúng nằm
trong nhật ký `subtype_conflicts_a3`, và bảng trên đã cộng lại.

## Quan hệ kiểu mở ở 2a (2026-09-14) — không nhận

Thiết kế: 2a đề xuất quan hệ kiểu mở giữa các node đã tách, `subtype_of` chỉ là một kiểu trong đó; prompt v3.
Kế hoạch và luật viết trước khi chạy nằm ở [`task/a4-quan-he-mo-2a/`](../task/a4-quan-he-mo-2a/). Chạy flash-lite trên
bốn tài liệu vào `artifacts/a4-ab/gemini-3.1-flash-lite-relations-v3/`.

| | Mặc định | v3 quan hệ mở |
|---|---:|---:|
| TP / FP / FN | 31 / 0 / 16 | 38 / 9 / 9 |
| Precision / F1 gộp | 1,000 / 0,795 | **0,809** / 0,809 |
| Precision `subtype_of` | 0,635 | 0,688 |
| Cặp cha–con bắt được | 35/47 | 24/47 |
| Quan hệ khác `subtype_of` | — | 34, với 18 tên kiểu; mẫu 30 cho 73% đúng |
| Lượt thử hỏng | 0 | 0 |

**Không nhận:** precision gộp dưới ngưỡng 0,95. Mô hình dùng node như nhóm chủ đề, ví dụ gộp `Bài toán phân loại` với
`Bài toán phân cụm` vì là *"specific types of machine learning problems"*. Nó còn ghi `subtype_of` giữa hai nhóm mà chính
nó đã gộp: 7/9 ca gộp sai nằm trong node có quan hệ tự mâu thuẫn như vậy.

Bản thân kênh quan hệ thì có ích: 6/11 cặp *liên quan* từng bị gắn `subtype_of` sai được gắn kiểu đúng hơn. Chi tiết,
mẫu kèm nhãn, và các hướng đi tiếp nằm ở ticket 07 và feedback F18, vòng 25.

**Đợt 2, thêm luật kiểm nhất quán (2026-09-14) — cũng không nhận.** Giữ prompt v3, thêm luật:
- quan hệ nối hai nhóm mà mô hình đã gộp chung node, hoặc quan hệ đồng nhất giữa hai node tách riêng, đều coi là đầu ra
  tự mâu thuẫn;
- gặp mâu thuẫn thì bắt mô hình phán lại một lần.

Kết quả trên một mẫu mới (138 lời gọi flash-lite):
- **gộp:** 35 / 2 / 12, precision 0,946, F1 0,833;
- **`subtype_of`:** precision 0,658;
- **quan hệ khác:** mẫu 30 cho 70% đúng;
- **luật bắt mâu thuẫn:** 8 lượt thử, cả 8 sửa được, 0 cụm bị hoãn.

Trượt ngưỡng precision gộp đúng một ca. Hai ca gộp sai còn lại không mang tín hiệu mâu thuẫn, và lặp lại đúng như ở lần
đầu. Lượt thử lại làm mất 4 cặp đúng vì mô hình tách cả node. Chi tiết ở ticket 14 và feedback F18, vòng 26.

**Chủ dự án chấp nhận bản này (2026-09-14),** đổi precision gộp 1,000 → 0,946 lấy recall, F1 và quan hệ kiểu mở.
Sau đó cả mẫu xác nhận lẫn lượt chạy kho chính đều qua ngưỡng xác nhận (precision gộp ≥ 0,93), nên bản này thành mặc
định; số của nó ở đầu báo cáo.

Lưu ý: với `temperature` 0, ba lượt chạy (ticket 13, mẫu xác nhận, kho chính) cho 217/217 quyết định giống hệt nhau.
Chúng chứng minh kết quả tái lập được, chứ không phải ba mẫu độc lập.

## Chốt đồ thị và kênh mô tả

Đã thử 13 cấu hình one-factor-at-a-time trên 47 cặp *cùng*. Cấu hình chốt giữ nguyên: k=3, ngưỡng n-gram=0,5,
resolution=2, seed=42, cap=9.

| Thay đổi | Cặp vàng bắt được | Cạnh đề cử | Trần lượt phán cụm + vá |
|---|---:|---:|---:|
| k=1 | 39/47 | 139 | 67 |
| k=2 | 44/47 | 192 | 68 |
| **k=3, ngưỡng 0,5, r=2, cap=9** | **47/47** | **256** | **101** |
| k=4 | 47/47 | 328 | 156 |
| k=5 | 47/47 | 412 | 195 |
| ngưỡng n-gram=0,6 hoặc 0,7 | 46/47 | 233 / 228 | 83 |
| ngưỡng n-gram=0,4 | 47/47 | 318 | 187 |
| cap=12 | 47/47 | 256 | 87, nhưng cụm lớn nhất 10 |

Resolution 1 / 1,5 / 2 / 2,5 đều giữ 47/47, với trần lượt phán lần lượt 134 / 119 / 101 / 108. Cap 12 giảm số call
ước tính nhưng vượt trần cụm đã kiểm chứng và chưa được chạy end-to-end; vì vậy chưa đổi. Số mốc chính thức là alias
9, n-gram 95, name 222, hợp 256; 63 cụm, lớn nhất 7; 38 cạnh cắt ở seed 42.

Trong 100 cặp ngẫu nhiên ngoài đồ thị không có nhãn *cùng*. Vì không có positive bị bỏ lỡ để kênh mô tả cứu, quyết
định hiện tại là **không thêm embedding mô tả vào A4**; đánh giá lại khi có bộ vàng người độc lập. Embedding mô tả
vẫn phù hợp cho relatedness/chủ đề ở A6/A7.

## Đề xuất prompt và giới hạn còn lại

- Giữ prompt merge hiện tại và dùng nguyên nó cho vá cụm: thay đổi ngữ cảnh/validator đã loại 3 false positive mà
  không cần thêm heuristic khó kiểm.
- Chưa đổi tham số đồ thị: cấu hình hiện hành là điểm duy nhất trong nhóm tốt đã được đo end-to-end bằng cả hai model.
- Luật "chỉ phát `subtype_of` khi bằng chứng nói là một loại" đã thử ở F72 (v2.1, v1.1) nhưng chưa nhận; xem mục
  A/B. Mặc định còn 19 cạnh subtype sai theo bộ AI. Hiện 2b coi `subtype_of` là đề xuất cần kiểm lại. Lần thử prompt
  sau cần nhãn mới hoặc mẫu người, không dùng lại bộ vàng này.
- 16 cặp bỏ sót còn lại nên được phân tích theo cụm/nhãn; không tự hạ guard hay tự gộp bằng cosine để nâng recall.

## Tái lập và kiểm thử

Bốn fixture contract v2 tại `tests/fixtures/a4/llm-v2/` gồm merge, vá cụm, A5 tổng hợp và A5 kiểm singleton. Bộ
fixture đời cũ ở `tests/fixtures/a4/llm/` đã được xóa theo F77 vì không còn consumer. Test
phát lại tính `prompt_hash` từ mã sản phẩm, cấm mạng và kiểm schema/citation/ID. Chạy lại bốn tài liệu với cấu hình
flash-lite ngay sau A/B đều trả `reused=true`, không tạo phiên bản hay lời gọi mới. Prompt mặc định không đổi qua
F72, nên fixture `llm-v2` vẫn hợp lệ. Sau F75: toàn bộ **265/265 test** qua khi chặn mạng, gồm test tích hợp Docling.

Lệnh chấm:

```powershell
doc2roadmap a4-evaluate --doc-id <doc> --gold tests/fixtures/a4/gold-blind.json --canonical-version <version>
```

Không báo Cohen's kappa: bộ bạc/phụ lục và bộ vàng cùng nguồn Claude, không phải hai người gán độc lập. Bảng HTML đã
được kiểm bằng DOM giả; browser tích hợp không có backend trong phiên chốt, nên thao tác UI trên browser thật vẫn là
kiểm chứng thủ công không chặn runtime.
