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

## Phân tích Q7 — độ phủ và độ chính xác (2026-09-25, 0 USD)

Độ chính xác trong chương: với mỗi đích vàng, trong các tổ tiên máy **là khái niệm của chương vàng** (đã gán đầy đủ), tỉ lệ
cũng là tổ tiên theo vàng. Đây là cận dưới của độ chính xác thật (T1: khoảng nửa cạnh dư được người chấm coi là cần).

| | Q7 phủ | chính xác trong chương | tổ tiên TB / đích |
|---|---|---|---|
| doc-1 đồ thị hiện tại (lượt 4, stages v35) | 90% | 59% | 46,6 |
| doc-1 + pass cạnh ngầm | 98% | 51% | 68,2 |
| doc-1 + nối 1 khái niệm dạy ngay trước | 98% | 39% | 106,7 |
| doc-2 đồ thị hiện tại (lượt 4, stages v29) | 58% | 93% | 20,9 |
| doc-2 + pass cạnh ngầm | 68% | 69% | 32,5 |
| doc-2 + nối 1 khái niệm dạy ngay trước | 80% | 33% | 135,6 |
| vàng | 100% | 100% | 8,4 / 5,7 |

- **Q7 chỉ đo phủ nên làm đẹp được** bằng cách nối theo thứ tự sách: phủ tăng, độ chính xác sụp, lộ trình tới đích dài gấp 6.
- doc-1 đã thừa (59%); doc-2 thiếu (58%). Độ thừa doc-1 phân tán: bỏ riêng cạnh "cầu nối" tệ nhất chỉ bớt 6/54 tổ tiên thừa.
- Loại căn cứ không tách được cạnh cần/thừa: gần như mọi cạnh là `trong_dinh_nghia` (đối chiếu T1).

**Quyết định chủ dự án 2026-09-25: thêm Q7b, ngưỡng ≥ 70%**, áp từ nay (kể cả tập giữ lại, vé 07). Đề xuất gốc: thêm **Q7b — độ chính xác tổ tiên trong chương**, báo cạnh Q7, để can thiệp
tăng phủ bằng cách nối thừa không được tính là tiến bộ. Ngưỡng cần chủ dự án chốt trước khi dùng làm cổng; tôi không tự đặt ngưỡng
sau khi đã thấy số trên dữ liệu phát triển.

Mã: `gold_scoring.target_precision`, báo trong `score_roadmap_order` dưới khoá `target_precision` cạnh `target_coverage`
(cùng tập cạnh `requires` + `bypassed`, cùng bản đồ danh tính). Đột biến bỏ lọc "chỉ tổ tiên trong chương" → 2 test đỏ.

### Q7b chấm bằng bộ chấm (2026-09-25)

| | Q6 | Q7 phủ | đích đủ | **Q7b** (cần / tổ tiên trong chương) |
|---|---|---|---|---|
| doc-1 C8 v2 (chuỗi mặc định, stages v18) | 5,0% | 89% | 9/24 | 60% (119/175) |
| doc-1 neo + danh tính (lượt 4, stages v35) | 2,6% | 90% | 9/23 | **59%** (108/162) |
| doc-1 + pass cạnh ngầm (stages v29) | 2,6% | 98% | 20/23 | 51% (130/218) |
| doc-2 C8 v2 (chuỗi mặc định, stages v13) | 8,2% | 58% | 0/23 | 93% (26/28) |
| doc-2 neo + danh tính (lượt 4, stages v29) | 4,9% | 58% | 0/23 | **93%** (26/28) |
| doc-2 + pass cạnh ngầm (stages v23, dựng trước khi sửa `𝐅^{m,n}`) | 9,8% | 68% | 0/23 | 69% (42/69) |

Q7b ≥ 70%: doc-2 đạt, **doc-1 trượt (59%)** ở mọi cấu hình — đồ thị doc-1 nối thừa từ A8, không do bước neo hay danh tính.
Q7 (≥ 95%, ≥ 80% đích đủ) trượt cả hai chương. Hai chương lệch hai phía: doc-1 thừa, doc-2 thiếu.
