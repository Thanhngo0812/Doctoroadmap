# Luồng chi tiết tầng 2b — từ chunk tới cạnh tiên quyết

Ngày đối chiếu: 2026-09-22 · Nguồn chuẩn: `doc/A6-A8-cum-chu-de-mention-map-va-tien-quyet-spec.md`,
`doc/va-provenance-sau-mention-map-spec.md`, và **mã hiện hành** trong `use_cases/build_clusters.py`,
`build_mentions.py`, `build_provenance.py`, `build_main_edges.py`, `build_secondary_edges.py`,
`validate_graph.py`, `build_roadmap.py`.

**Đây là bản nháp (vé 15).** Vé 15 chặn bởi vé 13 về số của lượt chạy thật cuối, nên mọi con số dưới đây lấy từ
**bốn tài liệu phát triển** — `baocao-canhan/v89`, `naive-bayes/v19`, `nhap-mon-ml/v19`, `xstk-ch3-1/v19` — chứ
không phải từ ba tài liệu mới. Và **hai mục cuối (A9, A10) cố ý để trống**: vé 20 và 21 đang thay phần lớn hành vi
của chúng, nên mô tả bây giờ sẽ chết yểu. Xem `doc/va-a9-a10-do-thi-tot-va-lo-trinh-dung-duoc-spec.md`.

Khác vé 14: vé 14 là **báo cáo thực nghiệm** (E1–E8, khoảng tin cậy, đóng góp). Bản này là **báo cáo luồng** — đi
từ một chunk tới một cạnh `requires` qua đúng những bước mã thật chạy, để người sau sửa được hệ thống.

---

## 1. Kết luận ngắn

Tầng 2b **không** hỏi mô hình "A có phải tiên quyết của B không" cho mọi cặp. Nó làm hai lượt khác hẳn nhau:

- **Pass chính — trích mở.** Mô hình nhận một *phiên* (một chương hoặc một cụm chủ đề) kèm hồ sơ khái niệm và văn
  bản, rồi **tự đề xuất** quan hệ nào nó thấy. Rẻ, sản lượng cao, nhưng chỉ thấy được trong phạm vi phiên.
- **Pass phụ — kiểm cặp.** Chỉ chạy trên các **cặp nghi** mà mention map và sổ cặp chạm chỉ ra, mỗi cặp hai hồ sơ
  đảo chiều để chống thiên lệch vị trí. Đắt, sản lượng rất thấp.

Giữa hai lượt là một chuỗi **bốn stage tất định, không gọi mô hình**: cụm chủ đề, mention map, provenance, và
executor. Executor là chỗ mọi thứ mô hình nói phải đi qua trước khi thành cạnh.

Số nói ngay điều đáng chú ý nhất: trên bốn tài liệu, **pass chính 101 lời gọi cho 267 cạnh** (2,64 cạnh/lời gọi),
còn **pass phụ 892 lời gọi cho 64 cạnh** (0,072) — kém hơn **37 lần** trên mỗi lời gọi. Trên `baocao-canhan`, pass
phụ gọi mô hình **72 lần và trả về 0 cạnh**. Điều này *chưa* kết luận pass phụ là thừa — giá trị của nó là **recall**
trên những cặp pass chính không thấy, và chỉ đo được trên bộ vàng. Đó đúng là việc của thí nghiệm E6.

---

## 2. Ranh giới trách nhiệm

| Ai | Làm gì | Không làm gì |
|---|---|---|
| **Code** | chia cụm, dựng mention map, chọn provenance, cắt phiên, định tuyến, kiểm mọi thao tác, gỡ chu trình, xếp tầng | không phán quan hệ ngữ nghĩa |
| **Mô hình, pass chính** | đọc một phiên, đề xuất cạnh kèm bằng chứng trích dẫn | không quyết cạnh nào được vào đồ thị, không tự khai điểm tin cậy được dùng làm quyết định |
| **Mô hình, pass phụ** | phán đúng một cặp khái niệm, hai lần với hai thứ tự | không được tạo cạnh ngoài cặp được hỏi |
| **Người** | duyệt cờ, gán bộ vàng, chốt hướng thiết kế | không sửa tay artifact |

---

## 3. Sơ đồ toàn luồng

Chuỗi stage thật, đọc từ `upstream_version` của `xstk-ch3-1`:

```text
canonical (A4/A5) ─┐
chunks (A1/A2) ────┴─> v13 clusters    a6-a7-topic-graph-v3        (không gọi mô hình)
                        └─> v14 mentions    mention-map-v3          (không gọi mô hình)
                             └─> v15 provenance provenance-refinement-v1 (không gọi mô hình)
                                  └─> v16 edges  a8-main-pass-v4     ← pass chính, GỌI MÔ HÌNH
                                       └─> v17 edges a8-secondary-pass-v3 ← pass phụ, GỌI MÔ HÌNH
                                            └─> v18 validated a9-global-validation-v4
                                                 └─> v19 stages   a10-kahn-stage-v5
```

Mỗi stage là một artifact riêng có `config_hash` và `source_hash`, nên **cache theo từng bước**: đổi một tham số
của mention map thì clusters được dùng lại, chỉ từ mentions trở đi mới chạy lại.

---

## 4. Đầu vào bắt buộc

Tầng 2b **không đọc PDF**. Nó đọc hai artifact:

- `canonical` — node đã hợp nhất, có `name`, `aliases`, `symbols`, `description`, `learnable`,
  `defining_chunk_ids`, `first_order_index`, và vector mô tả.
- `chunks` — văn bản, `section_id`, `page`, `order_index`.

Hệ quả: **mọi lỗi của A3/A4/A5 đi thẳng vào 2b mà 2b không phát hiện được.** Ví dụ đang có: `doc-1` cũ hỏng lớp
text nhưng `canonical` vẫn dựng xong, và 2b sẽ chạy vui vẻ trên đó.

---

## 5. Stage `clusters` — đồ thị chủ đề và chia cụm (A6, A7)

Tất định, không gọi mô hình. Khoá cấu hình: `channel_weights`, `edge_quantile`, cộng hash của `canonical` và
`chunks`.

Dựng đồ thị chủ đề giữa các node học được bằng nhiều kênh có trọng số, cắt cạnh theo **phân vị** chứ không theo
ngưỡng tuyệt đối, rồi chia cụm bằng Leiden. Số đo thật, số cụm có node học được: 7 · 6 · 12 · 12 cho bốn tài liệu,
cỡ cụm lớn nhất 8 · 10 · 9 · 12 — tức trung bình 5–8 khái niệm mỗi cụm.

*(Ghi chú cho vé 21: chính những cụm này, dùng riêng, cho cỡ nhóm đúng khoảng spec muốn. Chỉ khi **giao** chúng với
tầng tô-pô mới sinh ra 63 stage vụn.)*

---

## 6. Stage `mentions` — mention map

Tất định. Khoá cấu hình: `common_names`, `dense_centering`, cộng hash của `clusters`.

Với mỗi node học được, tìm những chunk **nhắc tới nó mà không phải chunk định nghĩa nó**, qua hai kênh: khớp tên
chính xác, và độ tương tự vector. `dense_centering` xử lý chuyện chunk "hub" (tổng quan, tóm tắt) gần với mọi thứ.
`common_names` chặn những tên quá phổ thông tạo nhiễu.

Mention map là thứ sinh ra **sổ cặp chạm** (`contact_pairs`) — đầu vào để chọn cặp cho pass phụ.

---

## 7. Stage `provenance` — vá nơi dạy (vé 16, F105)

Tất định. Khoá cấu hình: `candidate_channels`, `candidate_limit`, `definition_signals`, `definition_proximity`.

Lý do tồn tại: gán thử cho thấy provenance gốc từ A3/A4 trỏ vào **chunk mở đề** chứ không phải chunk định nghĩa ở
**4 trên 26** khái niệm, nên người gán bị chỉ sai chỗ. Stage này tìm thêm ứng viên từ kênh khớp chính xác và kênh
vector, lọc theo tín hiệu định nghĩa nằm **cùng câu** với tên khái niệm, và **chỉ thêm, không bao giờ xoá**
(`defining_chunk_ids_source` được giữ lại nguyên vẹn).

Số đo khi nhận vé 16: thêm 9 chunk, 0 trích dẫn sai, và trong bảng E1 có **2 trên 52 cạnh** chuyển sang lớp vị trí
"cùng chunk" sau khi vá.

---

## 8. Định tuyến — chương hay cụm chủ đề

Trước pass chính, code chọn **cách cắt phiên**, tất định, ghi vào `routing`:

| tài liệu | tuyến | lý do | cutoff |
|---|---|---|---|
| `baocao-canhan` | `chapter` | `declarative_tree_has_real_hierarchy` | 0,424 |
| `naive-bayes` | **`topic_cluster`** | **`declarative_tree_is_degenerate`** | 0,667 |
| `nhap-mon-ml` | `chapter` | `declarative_tree_has_real_hierarchy` | 0,079 |
| `xstk-ch3-1` | `chapter` | `declarative_tree_has_real_hierarchy` | 0,056 |

Cả hai nhánh **đều đã chạy thật** trên corpus — nhánh cụm chủ đề nổ trên `naive-bayes`, tài liệu có cây heading
suy biến. `single_session_limit = 20` cho cả bốn.

---

## 9. Pass chính — trích mở

Mô hình nhận một phiên và trả về một danh sách **thao tác**, mỗi thao tác đề nghị một cạnh kèm: `source`, `target`,
`edge_type`, `evidence_kind`, `chunk_ids`, `reason` (trích dẫn), `order_relation`, `confidence`.

Số thật:

| tài liệu | phiên | lời gọi (+ vá) | thao tác | cạnh pass chính | token |
|---|---|---|---|---|---|
| `baocao-canhan` | 16 | 16 (+5) | 48 | 29 | 62.712 |
| `naive-bayes` | 6 | 6 (+2) | 49 | 23 | 44.129 |
| `nhap-mon-ml` | 19 | 19 (+6) | 141 | 64 | 163.044 |
| `xstk-ch3-1` | 38 | 38 (+9) | 246 | 151 | 407.373 |

Lượt "vá" là lượt gọi lại khi đầu ra không hợp hợp đồng — **22 lượt trên tổng 79, tức 27,8%**. Hơn một phần tư số
lời gọi pass chính phải gọi lại; con số này đáng theo dõi.

### Một thao tác thật, nguyên văn

Từ `xstk-ch3-1`, phiên `main_section_s_db657132c6...`, thao tác số 1:

```
Mẫu tương quan cặp  →  Mẫu hai chiều
  edge_type         = requires
  evidence_kind     = noi_ro
  order_relation    = cùng chunk
  confidence        = 0.9
  evidence_hard     = true
  explicit_evidence = true
  chunk_ids         = ['c_93564e061185d72414bd6acb']
  reason            = "Mẫu hai chiều được xác định bằng cách sắp xếp lại mẫu tương quan cặp."
```

Executor nhận thao tác này vì: kiểu quan hệ là `requires`; cả hai node nằm trong phiên và đều học được; chunk bằng
chứng có thật; `evidence_kind` hợp lệ; câu trích dẫn có mặt trong chunk ấy; không trùng thao tác trước. Cạnh vào
`main_edges`, rồi đi tiếp tới A9.

---

## 10. Executor — nơi mọi thứ mô hình nói phải đi qua

Mã có **mười hai mã lỗi**, không phải bảy như bản giao việc vé 15 ghi *(chênh lệch này cần đối chiếu lại với D9 khi
chốt bản cuối)*:

`dropped_self` · `dropped_duplicate` · `evidence_missing_both_endpoints` · `model_confidence_forbidden` ·
`non_learnable_node` · `outside_session` · `relation_type_must_be_requires` ·
`reverse_order_requires_explicit_evidence` · `speculative_evidence` · `unknown_evidence_chunk` ·
`unknown_evidence_kind` · `unknown_node`

Kết cục thật của từng thao tác:

| tài liệu | nhận | từ chối | trùng | hoãn sau khi thử lại | gắn cờ |
|---|---|---|---|---|---|
| `baocao-canhan` | 30 | 13 | 4 | — | 1 |
| `naive-bayes` | 38 | 11 | — | — | — |
| `nhap-mon-ml` | 84 | 26 | 16 | 15 | — |
| `xstk-ch3-1` | 180 | 19 | 39 | 8 | — |

Lý do từ chối, gộp cả bốn tài liệu:

| lý do | số lần | đọc ra gì |
|---|---|---|
| `relation_type_must_be_requires` | **48** | mô hình liên tục đề nghị kiểu quan hệ khác trong lượt trích mở |
| `evidence_missing_both_endpoints` | **39** | câu trích dẫn không chứa cả hai đầu — đây là luật F96 |
| `reverse_order_requires_explicit_evidence` | 5 | cạnh đi ngược thứ tự trình bày mà không có bằng chứng nói rõ |

`dropped_duplicate` **59 lần trên cả bốn tài liệu, trong đó 55 lần ở hai tài liệu lớn**, cho thấy lượt trích mở
**đề nghị lại cùng một cạnh qua nhiều phiên** — không sai, nhưng là chi phí.

---

## 11. Pass phụ — kiểm cặp

Cặp ứng viên đến từ sổ cặp chạm của mention map, không phải từ tích Descartes.

| tài liệu | cặp nghi | cặp đã xử | lời gọi | cạnh thu | token so với pass chính |
|---|---|---|---|---|---|
| `baocao-canhan` | 251 | 62 | 72 | **0** | 1,6× |
| `naive-bayes` | 177 | 124 | 281 | 15 | **9,1×** |
| `nhap-mon-ml` | 1.041 | 157 | 245 | 20 | 2,4× |
| `xstk-ch3-1` | 1.104 | 226 | 294 | 29 | 1,2× |

Quyết định của pass phụ trên `xstk-ch3-1`: 72 `no_direct_relation`, 38 `defer`, còn lại sinh cạnh. Lý do hoãn:
`inconsistent_orders` 29 (hai hồ sơ đảo chiều cho hai câu trả lời khác nhau — đúng cơ chế chống thiên lệch vị trí
đang làm việc của nó), `invalid_or_outside_dossier` 9.

**`inconsistent_orders` là con số đáng giá nhất ở đây**: 29 trên 226 cặp, tức **13%** số cặp cho câu trả lời khác
nhau chỉ vì đổi thứ tự trình bày trong prompt. Nó vừa biện minh cho cơ chế hai hồ sơ đảo, vừa là một số đo về độ
ổn định của mô hình đáng đưa vào báo cáo thực nghiệm.

---

## 12. Hồ sơ cạnh cuối cùng

| tài liệu | cạnh | `trong_dinh_nghia` | `noi_ro` | `mach_trinh_bay` | thuận | cùng chunk | ngược |
|---|---|---|---|---|---|---|---|
| `baocao-canhan` | 25 | 19 | 2 | 4 | 7 | 14 | 4 |
| `naive-bayes` | 38 | 32 | 5 | 1 | 14 | 15 | 9 |
| `nhap-mon-ml` | 84 | 60 | 3 | 21 | 33 | 42 | 9 |
| `xstk-ch3-1` | 180 | 159 | 13 | 8 | 118 | 46 | 16 |

Hai điều đọc được: `trong_dinh_nghia` chiếm **71–88%**, nên `evidence_kind` gần như không phân biệt được cạnh nào
với cạnh nào; và cạnh **ngược thứ tự trình bày** chiếm **9–24%**, tức giáo trình vi phạm thứ tự tiên quyết của
chính nó ở khoảng một phần mười số cạnh.

---

## 13. A9 và A10 — để trống có chủ đích

Vé 20 thay cách gỡ chu trình, cách xử cặp hai chiều, thứ tự các bước và cổng chất lượng. Vé 21 thay thuật toán xếp
tầng và định nghĩa stage. Mô tả hành vi hiện tại ở đây sẽ sai ngay sau khi hai vé ấy xong.

Phần đã đo về hành vi **hiện tại** nằm ở `report/nghien-cuu-a9-a10-kiem-dinh-va-lo-trinh.md` mục 2. Bản cuối của
báo cáo luồng này sẽ viết lại hai mục ấy theo hành vi mới.

---

## 14. Những chỗ đã biết là yếu

1. **Bằng chứng mềm.** Cạnh có `evidence_hard = false` được nhận nhưng đánh dấu riêng; luật siết cứu được 6 cạnh
   đang bị loại nhưng loại thêm 41 trong 344 — nên spec để ngỏ và đặt luật đổi **viết trước** (D9).
2. **Pass phụ đắt và sản lượng thấp**, tới mức 72 lời gọi cho 0 cạnh trên một tài liệu. Giá trị thật chỉ đo được
   trên bộ vàng, qua E6.
3. **Một phần tư số lời gọi pass chính phải gọi lại** vì đầu ra không hợp hợp đồng.
4. **`evidence_kind` gần suy biến**, nên thứ tự ưu tiên giữ cạnh của D11 thực chất do hai tiêu chí sau quyết định.
5. **2b không kiểm được chất lượng đầu vào.** Một `canonical` dựng từ văn bản hỏng vẫn chạy hết luồng mà không có
   cảnh báo nào — đúng ca `doc-1` cũ. Vé 19 vá chỗ này ở tầng ingest.
6. **Cờ rỗng `{}` lọt qua kiểm hợp đồng của pass phụ** và hiện lên trang duyệt dưới dạng không xử lý được (F113,
   đang sửa ở vé 20).

---

## 15. Cache, phiên bản và artifact

Mỗi stage lưu `config_hash` (băm của toàn bộ tham số, gồm hash của artifact thượng nguồn) và `source_hash` (băm của
payload đầu vào). Chạy lại với cùng hai giá trị thì trả artifact cũ và `reused=true`, **không gọi mô hình**.

Vì hash thượng nguồn nằm trong config của stage dưới, đổi một tham số ở giữa chuỗi chỉ chạy lại từ đó xuống. Đây là
lý do chuỗi bảy artifact `v13…v19` của `xstk-ch3-1` tồn tại song song thay vì bị ghi đè.

Hai pass gọi mô hình đều có `checkpoint`, nên một lượt chạy đứt giữa chừng nối lại được mà không mất tiền đã tiêu —
cơ chế này từng có lỗi phân kỳ và đã được sửa, kiểm ở vòng 32 (F99).
