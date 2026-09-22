# 20 — A9 v2: kiểm tra tính nhất quán cấu trúc

**Nguồn chân lý:** [`doc/va-a9-a10-do-thi-tot-va-lo-trinh-dung-duoc-spec.md`](../../doc/va-a9-a10-do-thi-tot-va-lo-trinh-dung-duoc-spec.md)
V3, V4, V5, V6, V10, V11 (F113)

**What to build:** A9 làm đúng việc nó nói: gỡ chu trình bằng nghiệm **chính xác** ở mọi cỡ, đưa cặp hai chiều ra
khỏi đồ thị tiên quyết, và một cổng chất lượng không còn phán xét chất lượng tài liệu bằng hai hằng số không nguồn.

**Blocked by:** None — chạy được song song với vé 19. **Chặn:** vé 21, vì A10 chỉ đúng khi A9 giao cho nó một DAG thật.

**Status:** implemented-and-measured (2026-09-22; A10 dùng DAG của A9 v9)

## Vì sao sửa

Ba điều đã đo hoặc đã tra được, chi tiết ở báo cáo vòng 36:

1. **Mã hiện tại lặng lẽ chuyển sang xấp xỉ.** `_feedback_edges` vét cạn khi SCC có ≤ 16 cạnh nội bộ (đo: 16 cạnh
   hết 217 ms) và **rơi sang heuristic khi nhiều hơn** — D11 không nhắc tới nhánh đó. Viết "giải bằng vét cạn"
   trong báo cáo là câu sai. Nhánh xấp xỉ chưa từng chạy trên corpus hiện tại, nhưng nó tồn tại.
2. **Lý lẽ giữ chu trình hai cạnh dựa trên tiền đề sai.** Con số ~4% là đúng, nhưng tác giả bộ dữ liệu viết rằng
   các cặp ấy gợi ý nên **gộp thành một khái niệm** — không phải "quan hệ hợp lệ". Ca thật duy nhất của ta là
   **ERD ↔ Thiết kế Cơ sở dữ liệu**, một quan hệ bộ phận–toàn thể bị đoán ngược, nên gộp cũng sai.
3. **`confidence` gần như vô nghĩa.** Trên cả **327 cạnh** của bốn tài liệu nó chỉ nhận **ba giá trị** 0,7 · 0,8 ·
   0,9. Văn liệu đo AUROC của độ tin cậy mô hình tự khai ở mức 51,3–62,7 trên năm mô hình.

## Việc phải làm

- [x] **V3 — MFAS có trọng số, giải chính xác.** Liệt kê chu trình đơn trong SCC → giải phủ tập hợp có trọng số →
      chỉ rơi về heuristic tuyến tính khi vượt ngân sách, và **artifact ghi nghiệm là `approximate`**.
- [x] **Ngân sách đặt theo số chu trình đơn, không theo số node hay số cạnh.** Một SCC 27 node / 60 cạnh có 2⁶⁰
      tập con cạnh nhưng chỉ 177 chu trình đơn — khoảng cách ấy chính là lý do đổi thuật toán.
- [x] **Trọng số giữ cạnh:** loại bằng chứng → thuận thứ tự trình bày → số nguồn độc lập, mã hoá theo bậc cơ số để
      tiêu chí trước luôn trội. **Bỏ `confidence`.** Phá hoà cuối bằng khoá cạnh theo thứ tự từ điển.
- [x] Artifact ghi thêm cho mỗi SCC đã xử lý: số chu trình đơn, phương pháp (`exact` / `approximate`), tổng trọng
      số đã gỡ.
- [x] **V4 — cặp hai chiều.** Đưa **ra khỏi** đồ thị con `requires`; sinh cờ `suspected_relation_type_error` mang
      hai node, cả hai cạnh, bằng chứng từng chiều và lý do. Không tính vào cổng, không tính vào mật độ, không vào
      lộ trình. Người duyệt phán một chiều đúng thì chiều ấy quay lại qua đường xử lý tồn đọng đã có.
- [x] **V5 — cố định thứ tự tám bước** và ghi thành assertion. Đánh dấu bắc cầu **phải** chạy sau khi hết chu trình.
      Giữ nguyên **đánh dấu, không xoá**; bổ sung lý do thống kê vào phần biện minh (cạnh nhiễu ít bị bắc cầu hàm ý
      hơn cạnh thật, nên xoá cạnh thừa sẽ ưu tiên xoá cạnh đúng).
- [x] **V6 — cổng chất lượng.** Tử số đếm cạnh **không mang `redundant_via`**. Hạ ngưỡng xuống mức chỉ bắt lỗi
      pipeline chết (đề xuất 0,15 cạnh/node và 85% cô lập; vé chốt con số và ghi lý do). Manifest **luôn** ghi đủ
      số đo kể cả khi cổng mở. Cổng đóng thì sinh cảnh báo đọc được, **không** im lặng đổi chế độ.
- [x] **V10 — đổi cách gọi tên** trong spec, artifact và thông điệp: A9 là **kiểm tra tính nhất quán cấu trúc**.
- [x] **V11/F113** — kiểm hợp đồng của pass phụ phải kiểm **từng phần tử** của danh sách cờ. Hiện hai cờ rỗng `{}`
      trên `nhap-mon-ml` lọt vào trang duyệt thành `{"status": "unresolved"}` không ai xử lý được.
- [x] Chạy lại A9 cho bốn tài liệu phát triển, **dán số trước/sau**: số cạnh, số cạnh thừa, cờ, kết quả cổng.
- [x] Test ở seam đã có (`tests/unit/domain/test_global_validation.py`).

## Ca test phải có

- Một SCC mà nghiệm tối ưu là gỡ **hai cạnh rẻ** thay vì **một cạnh đắt** phải cho ra hai cạnh rẻ. Đây là ca phân
  biệt MFAS **có trọng số** với MFAS **đếm cạnh**, và luật hiện tại sẽ đỏ ở ca này.
- Vượt ngân sách chu trình → artifact ghi `approximate`.
- Cùng đầu vào cho cùng đầu ra qua nhiều lượt.
- Cặp hai chiều không có trong cạnh `requires` đầu ra; cờ mang đủ hai cạnh và bằng chứng; cổng không đổi vì nó.
- Sau A9, đồ thị con `requires` **không còn SCC nào lớn hơn một node**.
- Đồ thị mà **mọi** cạnh đều thừa thì **không** qua cổng.
- Manifest có đủ số đo cổng kể cả khi cổng mở.

Đột biến tối thiểu: quay về đếm cạnh thay vì tổng trọng số; đưa `confidence` trở lại trọng số; giữ cặp hai chiều
trong `requires`; đảo thứ tự bước 5 và 6; đếm cả cạnh thừa vào tử số cổng; bỏ cảnh báo khi cổng đóng; bỏ nhãn
`approximate`.

## Kết quả triển khai — 2026-09-22

- A9 `a9-structural-consistency-v8`: chu trình đơn được liệt kê tới ngân sách **1.000 chu trình/SCC** (không có
  ngưỡng theo số node/cạnh). Với số chu trình trong ngân sách, thuật toán phủ chu trình tối thiểu **tổng trọng số**
  chạy chính xác; vượt ngân sách mới dùng heuristic và ghi `method=approximate`, số chu trình đã thấy là cận dưới
  (`simple_cycle_count_capped=true`). Mỗi SCC ghi `removed_weight`. Trọng số là bậc cơ số theo loại bằng chứng,
  chiều trình bày, số nguồn; `confidence` không tham gia. Phá hoà theo khoá cạnh.
- Tất cả cặp hai chiều, kể cả nằm trong SCC lớn hơn hai node, được tách trước khi gỡ chu trình còn lại; cờ giữ
  nguyên hai cạnh và bằng chứng từng chiều. `assert _acyclic(...)` chạy **trước** đánh dấu bắc cầu. Node mới chỉ
  được gán cụm sau kiểm tra cấu trúc và cổng, với test quan sát đúng thứ tự. Cạnh bắc cầu chỉ bị đánh dấu vì
  phép xoá dễ ưu tiên xoá cạnh thật được hàm ý, giữ cạnh nhiễu không được hàm ý.
- Chốt ngưỡng cổng **0,15 cạnh không thừa/node học được** và **tối đa 85% node cô lập**. Đây là ngưỡng cảnh báo
  pipeline gần chết, **không phải** phép chấm chất lượng tài liệu: nguồn nghiên cứu không cho một cutoff chung,
  trong khi corpus cũ dao động 0,34–5,89 cạnh/node. Manifest luôn có tử số, mẫu số, mật độ, cô lập và trạng thái.
  Cổng đóng sinh thêm `structural_consistency_gate_closed` trong cờ duyệt, kèm số đo và lý do.
- F113: `validate_secondary_response` từ chối từng cờ không có `kind` không rỗng. Hai `{}` đã đóng băng trong
  edge artifact `nhap-mon-ml` được cách ly khỏi `validation_flags`, thay bằng một cờ chẩn đoán
  `invalid_upstream_flags(count=2)`; không cần gọi lại mô hình chỉ để sửa trang duyệt.

Đo A9 trên **chính edge artifact cũ**, không gọi mô hình; định dạng ô: số cạnh `requires` / cạnh thừa / cờ duyệt /
cổng. Cổng đều mở; trong A9 v8 mọi thành phần liên thông mạnh còn lại đều cỡ 1 (DAG).

| Tài liệu | Trước | Sau A9 v8 | Khác biệt quan trọng |
|---|---|---|---|
| `naive-bayes` | v18: 38 / 9 / 24 / mở | v23: 38 / 9 / 24 / mở | 29 cạnh không thừa; 34 SCC đơn |
| `nhap-mon-ml` | v18: 84 / 11 / 9 / mở | v23: 84 / 11 / 8 / mở | 73 cạnh không thừa; hai cờ rỗng cũ được thay bằng một cảnh báo; 75 SCC đơn |
| `baocao-canhan` | v88: 25 / 2 / 7 / mở | v93: 20 / 1 / 10 / mở | 4 cặp hai chiều thành cờ, 1 cạnh gỡ `exact` ở SCC ba node; 19 cạnh không thừa; 36 SCC đơn |
| `xstk-ch3-1` | v18: 180 / 51 / 19 / mở | v23: 180 / 51 / 19 / mở | 129 cạnh không thừa; 98 SCC đơn |

Chạy lại bốn doc-id trả `reused=True` trên đúng v23/v23/v93/v23. Phép đo chỉ thay A9; A10 cũ không được dùng
để chấm các graph này.

**Test và đột biến:** 26 test A9/F113/architecture xanh. Test mới đã đỏ trên mã cũ hoặc biến thể sai tương ứng:
`test_weighted_feedback_removes_two_cheap_edges_instead_of_one_expensive_edge` (đếm cạnh),
`test_confidence_does_not_break_equal_priority_cycle_tie` (đưa `confidence` lại),
`test_two_edge_cycle_is_flagged_removed_and_does_not_count_toward_quality_gate` (giữ hai chiều),
`test_redundancy_is_marked_only_after_cycle_edge_is_removed` (đảo bước 5–6),
`test_gate_ignores_redundant_edges_even_if_raw_density_passes` (đếm cạnh thừa),
`test_closed_quality_gate_is_a_visible_review_flag` (bỏ cảnh báo),
`test_cycle_count_budget_records_approximation_and_keeps_a_dag` (bỏ `approximate`).

### Sửa tiếp sau review F117–F118

Review phát hiện 1.000 chu trình vẫn có thể làm bộ giải chính xác tốn 14,72 giây trên SCC đầy đủ 6 node.
`a9-structural-consistency-v9` giữ trần 1.000 chu trình nhưng thêm **ngân sách 10.000 lượt gọi bộ giải**;
chạm một trong hai trần thì rơi về `approximate`. Hai lý do được ghi tách biệt bằng
`simple_cycle_count_capped` và `work_budget_exceeded`. Ca đầy đủ 6 node/409 chu trình hiện rơi về xấp xỉ
trong 0,126 giây; ca >16 cạnh chỉ có một chu trình vẫn giải `exact`.

`assert _acyclic(...)` đã đổi thành kiểm tra có `raise ValueError` thật, không mất đi dưới `python -O`.
Hai test mới đều đỏ trên bản v8: ép ngân sách công việc chạm với số chu trình còn dưới trần, và giả lập
bộ giải trả thiếu cạnh để buộc cổng DAG phát hiện. A9 v9 chạy lại bốn artifact cũ, không gọi mô hình:
`naive-bayes` v26, `nhap-mon-ml` v26, `baocao-canhan` v96, `xstk-ch3-1` v26; các số cạnh/cờ/cổng
không đổi so với bảng v8. A10 v7 được dựng lại từ đúng bốn DAG v9.

### A9 v9 trên ba tài liệu mới sau A8 thật

| Tài liệu | Node học được | Cạnh `requires` | Cạnh không thừa | SCC lớn nhất | Cổng cấu trúc | Cờ duyệt |
|---|---:|---:|---:|---:|---|---:|
| `doc-3` | 58 | 41 | 39 | 1 | mở | 21 |
| `doc-1` mới | 225 | 337 | 278 | 1 | mở | 19 |
| `doc-2` | 438 | 864 | 602 | 1 | mở | 95 |

A9 chạy sau edge artifact cuối của từng tài liệu (`doc-3`/`doc-1`/`doc-2` đều v5),
không gọi mô hình. A10 v7 đã được chạy từ đúng ba DAG này; kết quả ở [vé 21](21-a10-xep-tang-co-tran-do-rong.md).
