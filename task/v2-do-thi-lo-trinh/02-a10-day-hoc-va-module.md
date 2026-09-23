# 02 — A10: dãy học neo sách và module

**Nguồn chân lý:** spec v2, W2–W8 · ADR 0010

**What to build:** A10 sinh một dãy học (sắp topo ưu tiên vị trí dạy) và chia nó thành module liền mạch có thứ tự; bộ
chấm và trang HTML đọc hợp đồng mới; spec tổng, `CONTEXT.md` và spec A9–A10 sửa cùng commit.

**Blocked by:** —

**Status:** ready

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
