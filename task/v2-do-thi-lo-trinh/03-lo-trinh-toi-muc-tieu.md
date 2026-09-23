# 03 — Lộ trình tới mục tiêu

**Nguồn chân lý:** spec v2, W9–W10

**What to build:** cho một hoặc vài khái niệm đích, trả đúng các khái niệm cần học trước chúng theo thứ tự dãy học, chia
module; và đo Q7 trên bộ vàng.

**Blocked by:** 02

**Status:** ready sau 02

## Acceptance

- [ ] Hàm thuần `target_sequence(sequence, edges, targets)`: dãy con gồm đích và tổ tiên, giữ thứ tự dãy toàn cục. Test:
      mọi cạnh trong đồ thị con đi trước ra sau; không lẫn khái niệm không phải tổ tiên; đích không có tiên quyết thì chỉ
      còn chính nó.
- [ ] Hàm thuần `target_coverage(gold_edges, machine_edges, targets)` cho Q7, test trên đồ thị đồ chơi có đáp án tính tay.
- [ ] Lệnh `roadmap-target --graph <artifact> --concept <tên hoặc mã>` in JSON; `--output` ghi HTML.
- [ ] Báo Q7 hiện tại trên hai chương vàng (đã đo ở phân tích: 89%, 9/24 đích đủ trọn; 58%, 0/23).
