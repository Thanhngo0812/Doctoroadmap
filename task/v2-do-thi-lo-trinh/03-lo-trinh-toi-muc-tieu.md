# 03 — Lộ trình tới mục tiêu

**Nguồn chân lý:** spec v2, W9–W10

**What to build:** cho một hoặc vài khái niệm đích, trả đúng các khái niệm cần học trước chúng theo thứ tự dãy học, chia
module; và đo Q7 trên bộ vàng.

**Blocked by:** 02

**Status:** done — 2026-09-23

## Acceptance

- [ ] Hàm thuần `target_sequence(sequence, edges, targets)`: dãy con gồm đích và tổ tiên, giữ thứ tự dãy toàn cục. Test:
      mọi cạnh trong đồ thị con đi trước ra sau; không lẫn khái niệm không phải tổ tiên; đích không có tiên quyết thì chỉ
      còn chính nó.
- [ ] Hàm thuần `target_coverage(gold_edges, machine_edges, targets)` cho Q7, test trên đồ thị đồ chơi có đáp án tính tay.
- [ ] Lệnh `roadmap-target --graph <artifact> --concept <tên hoặc mã>` in JSON; `--output` ghi HTML.
- [ ] Báo Q7 hiện tại trên hai chương vàng (đã đo ở phân tích: 89%, 9/24 đích đủ trọn; 58%, 0/23).

## Kết quả — 2026-09-23

- `target_modules` (domain): lọc module toàn cục theo tổ tiên, không chia lại — W9 sửa theo; `target_coverage` (Q7) trong
  `gold_scoring`; `score_roadmap_order` báo `target_coverage`; lệnh `roadmap-target`. 4 test mới, đều đỏ trước; toàn
  suite 551/551.
- **Q7 hiện tại** (không đổi so với phân tích vì cùng bộ cạnh): `doc-1` v18 phủ trung bình **89%**, **9/24** đích đủ trọn,
  tổ tiên máy trung vị 48; `doc-2` v13 **58%**, **0/23**, trung vị 21. Cả hai dưới ngưỡng Q7 (≥ 95%; ≥ 80% đích): recall
  của đồ thị vẫn là nút thắt, như kế hoạch dự báo.
- **Lộ trình tới `Cơ sở` (`doc-1`)**: 56/222 khái niệm, đi đúng khung giáo trình — tập hợp → quan hệ, ánh xạ → nhóm, vành,
  trường → ma trận → định thức → nghịch đảo → hệ phương trình → không gian véc tơ → tổ hợp tuyến tính → độc lập tuyến tính
  → hệ sinh → cơ sở. Nhưng nó kéo theo cả chương ma trận và định thức qua cạnh `Hệ phương trình tuyến tính → Không gian
  véc tơ`, cạnh mà giải phẫu cạnh dư (kế hoạch cũ mục 13) xếp là *động cơ*, không phải tiên quyết. Đây là cái giá cụ thể
  của cạnh mềm với người học — thứ Q6 không thấy mà lộ trình tới mục tiêu phơi ra. Chấm mù (vé 10, T1) sẽ cho biết
  cạnh loại này nhiều tới đâu.
