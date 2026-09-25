# 02 — A10: dãy học neo sách và module

**Nguồn chân lý:** spec v2, W2–W8 · ADR 0010

**What to build:** A10 sinh một dãy học (sắp topo ưu tiên vị trí dạy) và chia nó thành module liền mạch có thứ tự; bộ
chấm và trang HTML đọc hợp đồng mới; spec tổng, `CONTEXT.md` và spec A9–A10 sửa cùng commit.

**Blocked by:** —

**Status:** done — 2026-09-23

## Cổng nhận (khoá trước khi chạy)

Trên artifact hiện hành của cả bảy tài liệu (lộ trình C8 v2: `doc-1` teaching v13, `doc-2` v8, `doc-3` v10, `baocao-canhan`
v98, `naive-bayes` v28, `nhap-mon-ml` v28, `xstk-ch3-1` v28), kiểm bằng assertion độc lập với mã sinh:

1. mọi khái niệm đủ điều kiện xuất hiện đúng một lần trong dãy và đúng một module; nối các module lại bằng đúng dãy;
2. 0 cạnh `requires` (kể cả cạnh co qua node bị loại) đi từ sau ra trước;
3. không module nào vượt `W`;
4. trên hai chương vàng, Q6 không tệ hơn U1 khắt khe của Coffman–Graham trên cùng đồ thị (`doc-1` 10,0%, `doc-2` 14,8%).

Số Q6 dự kiến (đã đo ở phân tích, dữ liệu phát triển): 5,0% và 8,2%. Độ mạch lạc **không** có cổng tự động ở vé này — nó
được chấm bằng người ở vé 10 (T6).

## Acceptance

- [ ] Hàm thuần `learning_sequence` và `segment_modules` ở tầng domain, test đỏ trước theo mục Testing của spec v2.
- [ ] `BuildRoadmap` dùng hai hàm đó; `algorithm_id = a10-book-anchored-sequence-v1`; payload `sequence`, `modules`,
      `chunk_module_map`.
- [ ] `score_roadmap_order` đọc `sequence` nếu có, không thì `stages`; báo Q6 và độ bám sách.
- [ ] `roadmap.html` hiện module có thứ tự.
- [ ] Đột biến: bỏ ràng buộc cạnh, đổi khoá vị trí, bỏ phạt mục — mỗi cái làm đỏ ít nhất một test.
- [ ] Sửa `spec-addendum.md` (sơ đồ §0, A10, A11, A12, A13, Pha B), `CONTEXT.md` (Module, Dãy học; Stage), spec A9–A10
      (V18 thay V7–V8 cho sản phẩm).
- [ ] Chạy trên bảy tài liệu **không gọi mô hình**, dán bảng: số khái niệm, số module, cỡ module, Q6 (hai chương vàng),
      độ bám sách.

## Kết quả — 2026-09-23

Chạy `scripts/phan-tich-v2/chay_a10_neo_sach.py` (không gọi mô hình; upstream là artifact teaching C8 v2). Mọi
assertion của cổng qua trên bảy tài liệu: mỗi khái niệm đủ điều kiện đúng một lần; nối module ra đúng dãy; 0 cạnh cứng
đi ngược; không module nào vượt 8.

| tài liệu | khái niệm | module | cỡ module | cấp chương/mục | Q6 | độ bám sách |
|---|---|---|---|---|---|---|
| `doc-1` v18 | 222 | 41 | 1×3, 2×2, 3×5, 4×2, 5×3, 6×12, 7×7, 8×7 | 1 / 2 | **5,0%** (CG 10,0%) | +0,912 |
| `doc-2` v13 | 432 | 70 | 3×4, 4×8, 5×10, 6×15, 7×16, 8×17 | — / 1 | **8,2%** (CG 14,8%) | +0,894 |
| `doc-3` v13 | 46 | 6 | 7×2, 8×4 | — / — | | |
| `baocao-canhan` v101 | 36 | 6 | 4×1, 5×2, 6×1, 8×2 | — / 1 | | |
| `naive-bayes` v31 | 31 | 4 | 7×1, 8×3 | — / — | | |
| `nhap-mon-ml` v31 | 75 | 13 | 3×2, 4×1, 5×2, 6×2, 7×5, 8×1 | 1 / 2 | | |
| `xstk-ch3-1` v31 | 98 | 18 | 4×5, 5×5, 6×4, 7×3, 8×1 | 1 / 2 | | |

Lần chạy đầu (trước phạt dưới sàn) cho 13 module một khái niệm trên `doc-1` và 13 trên `doc-2`; thêm phạt dưới sàn
(test đỏ trước) đưa về 3 và 0. Ba module lẻ còn lại của `doc-1` đều ở ranh giới cấu trúc: `Điểm đánh giá học phần`
(node hành chính C8 v2 bỏ lọt, một mình trong mục đề cương), `KerT` (chỉ dạy trong mục bài tập), `Định lý về số chiều`
(nút cuối của chuỗi dài nhất).

Mở đầu lộ trình `doc-1` nay đọc như giáo trình: module 2–3 "1.1 Tập hợp", module 4 "1.2 Quan hệ và ánh xạ".

Test: 14 test domain (đột biến bỏ ràng buộc cạnh, khoá vị trí theo mã node, bỏ phạt mục, đảo chiều phá hoà đều bị giết —
đột biến khoá vị trí ban đầu **sống sót** vì dữ liệu test trùng thứ tự chữ cái; đã sửa test), 3 test ứng dụng, 1 test bộ
chấm. Độ mạch lạc chấm bằng người ở vé 10 (T6).

## T6 / Q8 — kết quả nhận 2026-09-25 (`scripts/cham-module/cham_bang.py`)

| | A1 | A2 |
|---|---|---|
| module mới (neo sách), mạch lạc TB | **4,40** (bootstrap 95% 3,90–4,80), ≥ 4 điểm 17/20 | **4,20** (3,65–4,65), 17/20 |
| stage cũ (Coffman–Graham) | 1,70, ≥ 4 điểm 1/20 | 1,95, 1/20 |
| tên module đúng nội dung | 80% (n = 15) | 73% (n = 15) |

Hai người lệch ≤ 1 điểm ở 40/40 dòng. **Nguồn nhãn:** bản A2 ghi ở ô ghi chú "Bắt đầu 12:17; xong 12:23 (giờ VN, **AI thực
hiện**)"; bản A1 không ghi giờ, không có dấu hiệu AI. Q8 (≥ 4/5): ước lượng điểm đạt với cả hai bản; khoảng bootstrap chứa
vùng dưới 4 nên theo luật khoảng tin cậy là **chưa đủ bằng chứng**. Điều chắc chắn hơn: module mới hơn hẳn stage cũ (chênh
≈ 2,5 điểm, khoảng không chồng nhau). Chờ chủ dự án xác nhận nguồn nhãn A2 trước khi dùng làm cổng.
