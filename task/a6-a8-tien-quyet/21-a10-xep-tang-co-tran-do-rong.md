# 21 — A10 v2: xếp tầng có trần độ rộng, bỏ phép giao cụm

**Nguồn chân lý:** [`doc/va-a9-a10-do-thi-tot-va-lo-trinh-dung-duoc-spec.md`](../../doc/va-a9-a10-do-thi-tot-va-lo-trinh-dung-duoc-spec.md)
V7, V8, V10, V12

**What to build:** lộ trình có hình dạng dùng được — chặng đủ lớn để thành một buổi học, số chặng ở mức đọc hết
được, và chặng đầu không chứa một phần ba cuốn sách.

**Blocked by:** vé 20 — A10 chỉ đúng khi A9 giao cho nó một DAG thật.

**Status:** implemented-and-measured (2026-09-22) — **stage vẫn là nhóm học song song được.**

## Đo được gì

`stage = tầng ∩ cụm chủ đề` là **giao của hai phân hoạch**, và giao của hai phân hoạch hợp lý vẫn ra phân hoạch vụn:

| tài liệu | khái niệm | stage hiện tại | stage chỉ có 1 khái niệm | cỡ stage lớn nhất |
|---|---|---|---|---|
| `xstk-ch3-1` | 98 | **63** | **39** | 5 |
| `nhap-mon-ml` | 75 | 43 | 24 | 5 |
| `naive-bayes` | 34 | 16 | 7 | 4 |
| `baocao-canhan` | 36 | 22 | 14 | 4 |

**Trần 5–8 chưa bao giờ bị chạm.** Và từng phân hoạch riêng lẻ đều hợp lý — `xstk-ch3-1` có 12 cụm cho 98 khái
niệm, trung bình 8 mỗi cụm, đúng khoảng spec muốn. Chỉ phép giao là hỏng: 13 tầng × 12 cụm = 156 ô lưới.

Mô phỏng trên chính artifact (báo cáo vòng 36 mục 2.7), trần 8:

| | số stage | stage 1 khái niệm | cận dưới lý thuyết | tầng 1 |
|---|---|---|---|---|
| hiện tại (tầng ∩ cụm) | 63 | 39 | 13 | 12 khái niệm |
| bỏ giao cụm | 19 | 3 | 13 | 12 |
| **+ trần độ rộng** | **16** | 3 | 13 | **8** |

Bỏ phép giao cụm **không mất gì đo được**: τ so thứ tự sách đi từ 0,11 xuống 0,08 rồi 0,10 — nằm trong nhiễu.

## Việc phải làm

- [x] **V7 — Coffman–Graham có trần độ rộng `W`** thay cho xếp tầng theo đường dài nhất. Báo cáo phải **nêu tên bài
      toán** (xếp tầng độ rộng tối thiểu, tương đương lập lịch có ràng buộc thứ tự với việc dài một đơn vị; NP-khó,
      không xấp xỉ dưới 4/3) và **dẫn cận (2 − 2/W)** — không trình bày như heuristic tự nghĩ.
- [x] **Giữ nguyên bất biến:** không cạnh `requires` nào nối hai khái niệm trong cùng một stage.
- [x] Thêm bước **cân bằng** sau khi xếp tầng: khái niệm có nhiều tầng khả thi thì đẩy sang tầng ít khái niệm hơn.
      Không đổi tính hợp lệ, chạy tuyến tính.
- [x] **Assertion:** số stage ≥ `max(độ dài xích dài nhất, ⌈n / W⌉)`. Vi phạm là lỗi cài đặt, phải dừng.
- [x] **V8 — bỏ phép giao cụm.** `stage = một tầng` (cắt lát khi vượt trần). Cụm chủ đề chuyển vai: **đặt tên stage**
      và **sắp thứ tự khái niệm bên trong stage**.
- [x] Thêm **sàn** cỡ stage. Tầng nhỏ hơn sàn được gộp với tầng kề **chỉ khi** phép gộp không đưa hai đầu của một
      cạnh `requires` vào cùng stage; không gộp được thì để nguyên và ghi nhận.
- [x] `W` và sàn là **tham số**, mặc định trần 8. **Không viện tâm lý học** cho con số: "7±2" đã bị chính tác giả
      của nó gọi là trùng hợp tai hại, và không có nguồn sơ cấp nào khuyến nghị cỡ mô-đun theo số khái niệm. Con số
      được bảo vệ bằng bảng ablation ở vé 22.
- [x] **Thứ tự giữa các stage ngang hàng không được phá hoà bằng vị trí chương.** Dùng số khái niệm hậu duệ giảm
      dần rồi khoá stage. Lý do: thứ tự chương là **đối chứng đánh giá**; dùng nó để phá hoà rồi lại dùng nó để
      chấm là nhiễm đối chứng.
- [x] Bước co thành phần liên thông mạnh trở thành **assertion**, không còn là phép biến đổi: sau vé 20, còn thành
      phần nào lớn hơn một node là lỗi của A9 và phải dừng.
- [x] **V10** — đổi "độ khó" thành **"độ sâu tiên quyết"** ở mọi chỗ nhắc tới nó.
- [x] **V12** — ba thứ spec mô tả mà mã không có: gắn media vào stage, lượt LLM đặt tên stage, trường độ khó. **Gỡ
      khỏi spec hoặc cắt vé** — không để spec mô tả hệ thống không tồn tại. Giữ phần media thì ghi rõ là heuristic
      kỹ thuật: không có nguồn ủng hộ lẫn phản bác.
- [x] Chạy lại A10 cho bốn tài liệu, **dán bảng trước/sau**: số stage, phân bố cỡ stage, tầng 1, số tầng.
- [x] Test ở seam đã có (`tests/unit/domain/test_roadmap.py`).

## Ca test phải có

- Không tầng nào vượt trần.
- Không cạnh `requires` nào nối hai khái niệm cùng stage.
- Số stage không nhỏ hơn cận dưới.
- **Hai khái niệm khác cụm nhưng cùng tầng nằm CÙNG một stage** — ca này đỏ với luật giao cụm hiện tại.
- Tầng nhỏ hơn sàn được gộp, **trừ khi** phép gộp phá bất biến.
- **Đổi thứ tự chương của đầu vào không làm đổi thứ tự stage** — ca này giữ cho đối chứng đánh giá khỏi nhiễm.
- Bỏ bước cân bằng thì một ca có tầng lệch hẳn phải đỏ.

Đột biến tối thiểu: quay lại xếp tầng đường dài nhất; bỏ trần; đưa phép giao cụm trở lại; phá hoà bằng
`first_order_index`; bỏ assertion cận dưới; gộp tầng nhỏ bất chấp bất biến.

## Kết quả chạy thật (2026-09-22)

`W=8`, sàn `3`. Bảng so artifact A10 cũ → `a10-coffman-graham-stage-v7`, đều nhận DAG từ A9 v9.
Phân bố viết `cỡ stage × số stage`; “tầng 1” là tổng node ở tầng đầu, không phải stage đầu tiên của bản cũ.

| Tài liệu | Phiên bản cũ → mới | Stage | Phân bố cũ → mới | Tầng 1 | Số tầng |
|---|---|---:|---|---:|---:|
| `naive-bayes` | v19 → v27 | 16 → **6** | `1×7, 2×2, 3×5, 4×2` → `3×1, 4×1, 6×1, 7×3` | 18 → **7** | 6 → 6 |
| `nhap-mon-ml` | v19 → v27 | 43 → **10** | `1×24, 2×11, 3×4, 4×3, 5×1` → `7×5, 8×5` | 16 → **8** | 9 → 10 |
| `baocao-canhan` | v89 → v97 | 22 → **5** | `1×14, 2×4, 3×2, 4×2` → `7×4, 8×1` | 17 → **7** | 6 → 5 |
| `xstk-ch3-1` | v19 → v27 | 63 → **13** | `1×39, 2×18, 3×3, 4×1, 5×2` → `5×1, 7×3, 8×9` | 12 → **8** | 13 → 13 |

Trên cả bốn artifact mới: không stage quá 8 node; không cạnh `requires` cùng stage hoặc đi ngược thứ tự;
không còn SCC để co; số stage đều ≥ cận dưới; không còn stage dưới sàn. Tên stage lấy một tên khái niệm ngắn
thuộc cụm xuất hiện nhiều nhất trong stage, hoàn toàn tất định, không gọi LLM. Tham số nằm ở
`DOC2ROADMAP_ROADMAP_STAGE_CAP` và `DOC2ROADMAP_ROADMAP_STAGE_FLOOR` (mặc định 8/3).

Tên bài toán là xếp tầng độ rộng tối thiểu, hay `P|prec, p_j=1|C_max` (lập lịch các việc một đơn vị có
ràng buộc thứ tự); NP-khó, không xấp xỉ dưới 4/3. Thuật toán Coffman–Graham có cận `(2 − 2/W)`.
Nguồn sơ cấp và lưu ý về bản sửa chứng minh nằm ở [báo cáo nghiên cứu, mục 3.2 và tài liệu 30–35](../../report/nghien-cuu-a9-a10-kiem-dinh-va-lo-trinh.md).

### Ba tài liệu mới sau A8 thật

Chỉ chạy A9/A10 sau khi edge artifact cuối của từng tài liệu đã lưu; cả ba dùng A9 v9
và A10 v7. A9 đều giao DAG (SCC lớn nhất = 1) và cổng cấu trúc mở.

| Tài liệu | Learnable node / cạnh `requires` | Cạnh không thừa | Stage | Cỡ stage lớn nhất | Node có trong stage | Cờ phủ cần duyệt |
|---|---:|---:|---:|---:|---:|---:|
| `doc-3` | 58 / 41 | 39 | 8 | 8 | 58/58 | 4 |
| `doc-1` mới | 225 / 337 | 278 | 29 | 8 | 225/225 | 0 |
| `doc-2` | 438 / 864 | 602 | 55 | 8 | 438/438 | 0 |

Số stage của `doc-1` và `doc-2` lần lượt đúng cận dưới `ceil(225/8)=29` và
`ceil(438/8)=55`; không stage dưới sàn 3. Bốn cờ doc-3 không làm rơi node khỏi stage.
Phát lại cả ba khi proxy trỏ địa chỉ không kết nối trả `reused=true` trên graph v7,
không tốn lời gọi mô hình.
