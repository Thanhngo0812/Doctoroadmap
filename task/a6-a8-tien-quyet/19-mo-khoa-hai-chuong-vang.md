# 19 — Mở khoá hai chương vàng: tên ký hiệu (A3) và ngôn ngữ tài liệu (A5)

**Nguồn chân lý:** [`doc/va-a9-a10-do-thi-tot-va-lo-trinh-dung-duoc-spec.md`](../../doc/va-a9-a10-do-thi-tot-va-lo-trinh-dung-duoc-spec.md)
V1, V2, V11 (F115) · căn cứ ở [`report/nghien-cuu-a9-a10-kiem-dinh-va-lo-trinh.md`](../../report/nghien-cuu-a9-a10-kiem-dinh-va-lo-trinh.md)

**What to build:** hai chương vàng dùng được. `doc-2` mục 3C giữ được các khái niệm trung tâm của nó, và `doc-1`
được nhận đúng là tiếng Việt.

**Blocked by:** None. **Chặn:** vé 11 không gán nhãn được, và vé 12/13 không chạy được, cho tới khi vé này xong.
Đây là **đường găng duy nhất của cả đợt**, vì việc gán nhãn tốn người chứ không tốn máy.

**Status:** ready-for-agent — **chủ dự án chốt ngày 2026-09-22: sửa cả hai chặn, giữ nguyên hai chương đã chọn.**

## Đo được gì (vòng 36, đã kiểm lại độc lập)

| | số đo |
|---|---|
| `doc-2` A3 v2, tên ký hiệu bị loại | **47 lượt / 36 tên phân biệt** |
| Trong đó là khái niệm trung tâm của mục 3C | `ℒ(V,W)` · `ℒ(𝑉, 𝑊)` · `L(V, W)` · `ℒ(𝑉)` · `𝐅^{m,n}` · `F^m,n` · `F^n` · `𝒫(𝐅)` · `𝒫ₙ(𝐅)` · `ℳ` · `B(V, W)` |
| Guard alias-chữ của vé 18 cứu được | **3 ứng viên** — không đủ |
| `doc-1` **cũ**, chất lượng chữ | **24 ký tự có dấu / 42.087 ký tự chữ cái = 0,06%** — lớp text hỏng font, dấu bị nuốt (`Tính chất` → `T‰nh ch§t`) |
| `doc-1` **mới** (chủ dự án thay ngày 2026-09-22) | **25,46%** ký tự có dấu · 102 trang · **0** watermark · 1.442 ký tự PUA đều là mảnh ngoặc lớn font Symbol, vô hại |

> **Đã đổi tiền đề ngày 2026-09-22.** Bản giao việc đầu nói A5 "đoán sai ngôn ngữ" của `doc-1` và bảo sửa bộ đoán.
> **Sai** — bộ đoán đoán đúng, văn bản đưa cho nó không còn là tiếng Việt. Chủ dự án đã thay PDF. Phần V2 của vé
> này **không còn là sửa A5** mà là **thêm cổng chất lượng chữ ở ingest**, để lần sau một PDF hỏng font không đi
> hết A1→A5 mà không ai biết. Xem V2 trong spec.
>
> **Và `doc-1` mới là một cuốn khác** — *Bài giảng Đại số tuyến tính*, Đại học Hàng hải, 5 chương — nên **"Chương 5"
> đã chọn trước đây không còn nghĩa**; phải chọn lại chương vàng (xem mục cuối vé).

## Việc phải làm

- [ ] **V1 — luật ba nhánh cho tên ký hiệu.** Có alias chữ thì promote (đã có); không có alias chữ nhưng ký hiệu
      **có cấu trúc** thì **giữ entity, giữ tên ký hiệu**, đánh dấu `name_kind = "symbol"`; ký hiệu trơ thì loại
      như hiện nay và ghi vào danh sách đã có.
- [ ] Điều kiện nhận của V1, **đo trên `doc-2` thật**, không phải trên test tổng hợp:
      **phải có mặt** `ℒ(V,W)`, `𝐅^{m,n}`, `ℳ`, `𝒫ₙ(𝐅)`, `L(V, W)`, `B(V, W)`;
      **không được có mặt** `3.65`, `3.68`, `3.94`, `6.49`, `6.54`, `i`, `0`, `V`, `C`, `F`, `R`, `{0}`.
- [x] ~~Hai ca phải tự phán~~ — **chủ dự án đã phán ngày 2026-09-22: `V(2)`, `V(m)` và `𝛼𝑇` đều bị LOẠI.** Chúng
      là thể hiện ký hiệu, không phải khái niệm được định nghĩa. Ba tên này vào danh sách "phải loại" của điều
      kiện nhận bên trên.
- [ ] `ℳ` là ca khó nhất vì là ký tự đơn. Nếu predicate cú pháp không giữ được, được phép dùng **bằng chứng**
      (provenance ở chunk mang tín hiệu định nghĩa). Ghi rõ đã dùng cách nào.
- [ ] **V2 — cổng chất lượng chữ ở ingest.** Manifest ghi số ký tự chữ cái, tỉ lệ ký tự có dấu, tỉ lệ PUA và tỉ lệ
      ký tự thay thế. Cổng sinh **cảnh báo đọc được** khi lớp text có dấu hiệu hỏng font, nêu số đo, và nói rõ tài
      liệu không đủ chất lượng làm nguồn bộ vàng. **Không** tự ý dừng pipeline.
- [ ] Thêm lối **khai tường minh** ngôn ngữ; manifest ghi cả giá trị lẫn cách quyết định (`detected` / `declared`);
      giá trị khai vào config hash. `document_language` tính tỉ lệ dấu trên **ký tự chữ cái đọc được**.
- [ ] Điều kiện nhận của V2, đo trên dữ liệu thật: **`doc-1` mới qua cổng**; **`doc-1` cũ bị bắt** (chunk còn ở
      `artifacts/chunks/doc-1/v3`, 0,06% dấu); **`doc-2` và `doc-3` không bị báo nhầm** chỉ vì chúng là tiếng Anh;
      **không khai gì thì bốn tài liệu phát triển `reused=true`** ở đúng phiên bản hiện có.
- [ ] **Ingest lại `doc-1` mới.** Không cần `--strip-line` — bản mới đã đo là **0** watermark, **0** email. Dán số
      trang, chunk, section, window và cảnh báo parse.
- [ ] Chạy `doc-1` mới qua A3, A4, A5. **Kiểm bằng mắt vài chunk của chương sẽ chọn làm vàng** — số đo tỉ lệ dấu
      là điều kiện cần, không phải điều kiện đủ.
- [ ] **V11/F115** — bước bỏ dòng watermark hiện chỉ chạm `text` và `raw_text`, trong khi node còn có `table_rows`
      và `context_prefix`. Hoặc phủ đủ các trường văn bản, hoặc đổi tên `strip_line_algorithm` cho khỏi hứa quá
      (`normalized-substring-all-fields-v2` đang hứa nhiều hơn nó làm).
- [ ] Chạy lại A3 cho `doc-2`; chạy lại A3/A4/A5 cho `doc-1`. **Dán số ứng viên trước/sau, token, USD từng lượt.**
- [ ] Kiểm A4 vẫn hợp nhất được sau khi bảng ứng viên phình. Guard của vé 17 ra đời vì ký hiệu lọt A3 từng làm A4
      dừng — nếu A4 lại dừng thì **đó là thông tin, không phải thất bại**: nó nói vấn đề nằm ở A4.
- [ ] Test ở seam đã có (`test_a3_extract.py`, test quyết định canonical). Đột biến tối thiểu: bỏ nhánh "có cấu
      trúc", cho nhánh ấy nuốt cả ký hiệu trơ, bỏ lọc ký tự vùng dùng riêng, để phép đoán thắng khai báo tường minh,
      quên ghi cách quyết định vào manifest.
- [ ] Toàn bộ suite xanh khi chặn mạng.

## Chương vàng của `doc-1`: **Chương 3 — Không gian véc tơ** (chủ dự án chốt 2026-09-22)

`doc-1` mới có **102 trang, 5 chương**:

| Chương | Tên | Trang | Mục con | Nhận xét của reviewer |
|---|---|---|---|---|
| 1 | Tập hợp và ánh xạ | 11–16 | 3 | quá ngắn, gần như không có cấu trúc tiên quyết nội bộ |
| 2 | Ma trận, Định thức, Hệ phương trình tuyến tính | 17–43 | 5 | dày, nhưng thiên về thuật toán tính toán |
| **3** | **Không gian véc tơ** | **44–74** | **5** | **đề xuất** — đúng nghĩa "chương giữa", 31 trang, mạch tiên quyết nội bộ dày: độc lập tuyến tính → cơ sở → số chiều → không gian con → Euclid; tiên quyết bắc ngược về chương 1 (trường) và chương 2 (hạng ma trận), nên có cạnh xuyên chương vào bộ vàng đúng như D13 muốn |
| 4 | Ánh xạ tuyến tính | 75–87 | 3 | **phương án hai** — ngắn hơn (13 trang) nhưng **trùng chủ đề với mục 3C của `doc-2`** (ánh xạ tuyến tính, ma trận của ánh xạ). Đối chiếu song ngữ trên cùng chủ đề là điểm hấp dẫn, nhưng cũng là một biến gây nhiễu khi so hai ngôn ngữ |
| 5 | Trị riêng, véctơ riêng và dạng toàn phương | 88–102 | 2 (7 mục con) | chương **cuối**, không phải chương giữa như D13 yêu cầu |

**Chủ dự án chốt Chương 3 ngày 2026-09-22.** Nó là chương giữa thật, đủ dày để cho lượng khái niệm tương đương
lượt thử nghiệm (26 khái niệm đích, 87 dòng phải phán), và mạch tiên quyết của nó rõ.

**Vẫn phải dán số khái niệm đích thật vào vé** sau khi `doc-1` mới chạy xong A3–A5. Nếu Chương 3 cho **dưới 15
hoặc trên 45** khái niệm đích thì ghép thêm hoặc bớt một mục liền kề, đúng cơ chế dải mục của vé 04 — không đổi
chương, chỉ chỉnh phạm vi.

## Ghi chú

`algorithm_id` của A3 lại tăng một bậc. Bốn tài liệu phát triển **không** chạy lại. Corpus sẽ có nhiều cấu hình A3
cùng lúc — ghi vào vé tài liệu nào thuộc cấu hình nào, báo cáo sẽ cần bảng đó.

Ngân sách: lượt A3 `doc-2` gần nhất tốn 1,38 USD; tổng đã dùng tới nay khoảng 4,21 USD trên trần 50 USD.
