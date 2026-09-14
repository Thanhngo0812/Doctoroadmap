# 12 — Phiên bản luật trong config, chỉ số và runner

**What to build:** Đổi luật kiểm thì artifact cũ không được dùng lại. Mâu thuẫn được đếm, và ticket 14 đọc được số mà
không cần script riêng.

**Blocked by:** 10 — Luật nhất quán; 11 — Cache

**Status:** done — 2026-09-14

- [x] `CanonicalReasoning.config()` thêm `"partition_validation": "consistency-v1"`, cùng khuôn với
      `"description_validation"`. Config hash đổi, nên `find_canonical` không trả artifact v3 cũ.
- [x] **Chỉ số** (test khẳng định chỉ số khớp nhật ký):

  | Chỉ số | Nghĩa |
  |---|---|
  | `partition_contradictions` | số lượt thử bị `ContradictionError`, cộng cả lượt cụm và lượt vá |
  | `contradiction_retried_calls` | số lượt phán có ít nhất một lượt thử bị bắt |
  | `contradiction_deferred_calls` | số lượt phán hỏng hẳn mà lỗi cuối là mâu thuẫn |
  | `merge_cache_invalid`, `repair_cache_invalid` | từ ticket 11 |

  Mọi khoá có mặt kể cả khi bằng 0, rút kinh nghiệm từ `relation_self_removed` ở ticket 06.
- [x] `scripts/run_a4_arm.py` và `a4-evaluate` không phải đổi cách chấm. Runner in thêm các chỉ số trên.
- [x] Toàn bộ test xanh, chặn mạng.

## Bằng chứng hoàn tất

Config có `partition_validation = consistency-v1`. Năm khoá bắt buộc luôn có kể cả 0; seam đếm số
`ContradictionError` khớp từng attempt trong decision log. Runner đã in đủ năm khoá. Nhân tiện đóng F81, runner còn in
`relation_same_type_reversed_a3`; công thức đánh giá năm cổng không đổi.
