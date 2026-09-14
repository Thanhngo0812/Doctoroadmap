# 00 — Kế hoạch: 2a đề xuất quan hệ kiểu mở, `subtype_of` là một kiểu trong đó

> **Kết quả 2026-09-14: không nhận.** Precision gộp 0,809, dưới ngưỡng 0,95; bốn cổng còn lại qua. Chi tiết ở
> [ticket 07](07-cham-theo-luat-dang-ky-truoc.md) và feedback F18, vòng 25. Code v3 nằm trên nhánh
> `a4-quan-he-mo-2a`; `main` giữ code mặc định.

**Quyết định của chủ dự án (2026-09-12):**
- 2a không còn kênh riêng cho `subtype_of`. Giữa hai node tách riêng trong cụm, 2a được đề xuất **quan hệ kiểu mở**
  có bằng chứng; `subtype_of` là một kiểu trong nhóm đó.
- Đầu vào 2a giữ nguyên: không đưa thêm chunk.
- Mọi khâu LLM dùng `gemini-3.1-flash-lite`.

## Vì sao — số đo trên bốn tài liệu (cấu hình mặc định)

- **Mô hình bị ép chọn.** Trong 19 cạnh `subtype_of` sai, 10 cạnh có lý do tả một quan hệ khác loại: *"is used to
  estimate likelihood"*, *"a statistic of…"*, *"an application of…"*. Khuôn đầu ra chỉ có `subtype_of` để ghi.
- **Mô hình thấy quan hệ nhưng không có chỗ ghi.** 48/246 lý do của node đứng riêng tả quan hệ khác loại, ví dụ
  *"Sentiment Analysis is an application of Naïve Bayes Classification"*. Chúng chỉ nằm dưới dạng chữ trong nhật ký.
- **A3 không bù được.** 10/11 cặp *liên quan* bị gắn sai không có cạnh A3 nào. A3 đọc từng section, còn cụm 2a trải
  khắp tài liệu.
- **Cấm bằng prompt chỉ làm mô hình im lặng.** Prompt v2.1 bỏ được cả 11 cạnh sai ở cặp *liên quan*. Nhưng 8 cặp cha–con
  đúng cũng thành "tách, không cạnh", và 3 cặp bị gộp nhầm. Tính cả vài cặp bắt thêm, số cặp bắt đúng giảm từ 35 xuống 27.

Kênh mới không chữa được 9 cạnh sai còn lại. Đó là chuyện ranh giới "cùng" hay "hẹp hơn", hoặc chỗ mô hình lệch với
nhãn vàng.

## Phạm vi

**Đổi:**
- prompt merge/vá (v3);
- schema phân hoạch;
- validator quan hệ;
- phần lắp cạnh (thêm nguồn gốc cạnh);
- chỉ số;
- `a4-evaluate`;
- fixture hợp đồng;
- spec và ADR.

**Không đổi:**
- lớp tên, đồ thị đề cử, cụm, luật tên chuẩn, A5;
- luật gộp: chỉ *cùng* mới chung node;
- 2a vẫn không bao giờ sinh `requires`;
- F75 (chỉ ghi xung đột với A3) vẫn áp cho `subtype_of`.

## Hợp đồng mới

Đầu ra mỗi cụm và mỗi lượt vá:

```json
{
  "nodes": [{"groups": ["g_1", "g_2"], "reason": "..."}, {"groups": ["g_3"], "reason": "..."}],
  "relations": [{"source": "g_3", "target": "g_1", "edge_type": "subtype_of",
                 "chunk_ids": ["c_0042"], "reason": "..."}],
  "deferred": [{"group_id": "g_4", "reason": "..."}]
}
```

- `edge_type` đọc từ `source` sang `target`.
- Code kiểm từng quan hệ; quan hệ sai bị loại riêng, phân hoạch vẫn được áp.
- Cạnh vào artifact với `proposal: true` và `origins` (nguồn: `a3`, `2a` hoặc cả hai). 2b kiểm lại mọi quan hệ như
  kiểm đề xuất của A3.

**Prompt v3 — chốt 2026-09-12, dùng nguyên văn cho cả `a4-merge.txt` và `a4-repair.txt`:**

```text
Partition the supplied exact-name groups using only verbatim document evidence. Never use prior
knowledge to assert identity. Judgments: same entity => one node; parent-child, siblings, related or
different => separate nodes; uncertain => deferred.
Every group occurs exactly once in nodes or deferred. Refer to every group only by its group_id, never
by its name.
Between groups in separate nodes, add a relation only when a cited sentence states it. edge_type is open
and reads from source to target: subtype_of when the source is a kind, type, form, variant or special
case of the target; otherwise a short snake_case name such as component_of, uses, example_of, computed_by
or contrasts_with, or a new name when none fits. Cite source chunk IDs for every relation.
Never propose requires or a synonym of it. Do not choose canonical names, types, aliases or descriptions.
Return only JSON.
```

So với prompt hiện hành (v1):
- Hai câu đầu giữ nguyên chữ.
- Rubric danh tính giữ đủ các nhãn. Chữ "Relations:" đổi thành "Judgments:" để khỏi lẫn với danh sách quan hệ mới, và
  vế "subtype_of child to parent" bị bỏ.
- Thêm câu bắt dùng `group_id`. Đây là bài học từ v2 và v1.1: thiếu câu này thì flash-lite ghi tên nhóm thay id
  (48 và 20 lượt hỏng).
- Phần quan hệ là phần mới. Vì thế "Cite source chunk IDs for subtype relations" thành "…for every relation", và
  "Never propose requires" thêm "or a synonym of it".
- Không liệt kê loại trừ kiểu v2.1, vì liệt kê loại trừ làm mô hình im lặng thay vì chọn kiểu đúng.

## Chia việc

| Ticket | Việc | Ai | Chờ |
|---|---|---|---|
| Bước 0 | Commit mốc phase A4/A5, mở nhánh `a4-quan-he-mo-2a` | Chủ dự án | — |
| [01](01-spec-va-adr.md) | Spec D4/D5/D7, addendum, ADR 0007 | Claude | 0 |
| [02](02-schema-va-kiem-tung-quan-he.md) | Schema `relations` và validator từng quan hệ | Nhân viên | 01 |
| [03](03-lap-canh-nguon-goc-va-chi-so.md) | Lắp cạnh, `origins`, gộp với A3, chỉ số | Nhân viên | 02 |
| [04](04-prompt-v3-va-fixture-hop-dong.md) | Prompt v3, fixture hợp đồng `llm-v3` | Nhân viên | 01, 02, 03 |
| [05](05-a4-evaluate-do-quan-he.md) | `a4-evaluate` đo quan hệ | Nhân viên | 01, làm song song 02 |
| [06](06-chay-nhanh-thu.md) | Chạy nhánh thử vào kho riêng | Nhân viên | 03, 04, 05 |
| [07](07-cham-theo-luat-dang-ky-truoc.md) | Chấm theo luật dưới đây, lấy mẫu 30 quan hệ | Claude | 06 |
| [08](08-nhan-vao-kho-chinh.md) | Nhận vào kho chính, chỉ khi 07 qua | Nhân viên | 07 |

Sau 08, Claude review như các vòng trước và ghi vào feedback.

## Luật đánh giá — viết 2026-09-12, trước mọi lần chạy

So nhánh mới (flash-lite + v3 + quan hệ mở) với mặc định hiện hành: 31/0/16; F1 0,795; precision `subtype_of` 0,635;
0 cụm hỏng hẳn. Nhận khi **qua cả năm cổng**:

1. Precision gộp ≥ 0,95.
2. F1 gộp ≥ 0,775 (mặc định trừ 0,02).
3. Precision `subtype_of` ≥ 0,635 (không thấp hơn mặc định). Cách tính như báo cáo chạy thật: cạnh đúng / (đúng +
   sai), trên cặp có nhãn.
4. Cụm hỏng hẳn (sai sau lần thử lại) ≤ 1 trên bốn tài liệu.
5. Trong mẫu 30 quan hệ không phải `subtype_of` (seed 42; ít hơn 30 thì lấy hết), ≥ 60% đúng. "Đúng" nghĩa là câu
   trích nêu quan hệ đó, đúng chiều. Người gán là Claude.

Số phụ, ghi vào báo cáo nhưng không làm cổng:
- precision `subtype_of` tăng bao nhiêu; dự đoán 0,70–0,79 nếu phần chọn ép chuyển sang kiểu khác;
- recall `subtype_of` trên 47 cặp cha–con, và trên 44 cặp khi bỏ 3 cặp bộ phận mà bộ vàng gán cha–con: `Làm sạch dữ
  liệu` và `Biến đổi dữ liệu` ⊂ `Tiền xử lý dữ liệu`, `Thiết kế Cơ sở dữ liệu` ⊂ `Thiết kế hệ thống`;
- số quan hệ theo kiểu, và số dùng tên khác thay `subtype_of` (`is_a`, `kind_of`…);
- so với A3: trùng bộ ba, cùng cặp khác kiểu, cặp mới;
- quan hệ 2a nằm trên cặp có nhãn, chia theo nhãn vàng.

Trượt một cổng thì không nhận, và báo chủ dự án. Không chỉnh prompt rồi chấm lại trên bộ vàng này.

**Giới hạn biết trước:**
- Ý tưởng sinh ra từ việc đọc lỗi trên chính bộ vàng này, nên số sẽ lạc quan.
- Bộ vàng không có nhãn cho kiểu quan hệ; cổng 5 là mẫu do Claude gán, không phải người độc lập.
- 3 cặp bộ phận nói trên sẽ bị chấm là mất nếu mô hình gõ đúng thành `component_of`.

## Bước 0 và đường lui

- **Chủ dự án**: toàn bộ phase A3–A5 chưa commit. Commit mốc trước rồi làm trên nhánh riêng, thì lúc trượt chỉ việc bỏ
  nhánh. Nếu chưa muốn commit, nhân viên vẫn làm được, nhưng đường lui là gỡ tay.
- Ticket 06 chạy vào `artifacts/a4-ab/…`, nên `canonical/latest` không đổi cho tới ticket 08.
- Lần chạy kho chính ở ticket 08 là mẫu thứ hai, gọi mô hình độc lập với ticket 06. Trượt cổng 1, 3 hoặc 4 ở lần này
  thì revert.

## Chi phí

Chỉ flash-lite:
- ticket 04: 4 lời gọi;
- ticket 06: khoảng 63 merge và 38 vá, cộng A5 cho những node đổi thành viên;
- ticket 08: lặp lại mức của ticket 06;
- lượt chạy lại sau đó: 0 lời gọi.
