# 13 — Chạy nhánh thử lần 2

**What to build:** Chạy code đợt 2 trên bốn tài liệu bằng mô hình thật, ghi vào kho riêng. Đây là mẫu mới, độc lập với
lần v3 đầu; `canonical/latest` không đổi.

**Blocked by:** 12 — Config, chỉ số và runner

**Status:** done — 2026-09-14; chờ reviewer ở ticket 14

- [x] Chạy lệnh sau; mọi khâu dùng flash-lite:

      .\.venv\Scripts\python.exe scripts\run_a4_arm.py --out artifacts/a4-ab/gemini-3.1-flash-lite-relations-v3-consistency `
          --doc-id baocao-canhan --doc-id naive-bayes --doc-id nhap-mon-ml --doc-id xstk-ch3-1

- [x] **Không** chạy `doc2roadmap a4` vào kho chính, và không gộp nhánh vào `main`, cho tới khi ticket 14 kết luận.
- [x] Dán vào ticket này dòng JSON của từng tài liệu, số lời gọi thật, và các chỉ số mâu thuẫn. Không ước lượng.
- [x] Chạy lại cùng lệnh khi chặn mạng: cả bốn tài liệu phải `reused=true`, 0 lời gọi.
- [x] Toàn bộ test xanh, chặn mạng.

## Kết quả chạy thật

Kho riêng: `artifacts/a4-ab/gemini-3.1-flash-lite-relations-v3-consistency`. Judge và writer đều là
`gemini-3.1-flash-lite`. Tổng cộng **138 lời gọi thật**: 70 merge + 39 repair + 11 describe + 18 check; trong đó 8 là
lượt thử lại do mâu thuẫn. Kho canonical chính vẫn dừng ở báo cáo cá nhân v7 và ba tài liệu còn lại v6.

```json
{"doc_id": "baocao-canhan", "version": 1, "reused": false, "tp": 11, "fp": 0, "fn": 0, "subtype_recall": 0.5, "subtype_incorrect": 1, "subtype_precision": 0.5, "relations_2a_on_gold": {"same": 0, "parent_child": 1, "related": 4, "different": 0}, "calls": {"merge_calls": 13, "repair_calls": 7, "describe_calls": 1, "check_calls": 3, "merge_invalid": 0, "repair_invalid": 0}, "relation_rejected": 1, "relation_edges": 8, "relation_types": {"component_of": 1, "example_of": 1, "subtype_of": 2, "supports": 1, "used_with": 1, "uses": 2}, "relation_same_as_a3": 1, "relation_same_type_reversed_a3": 0, "relation_other_type_than_a3": 1, "relation_new_pair": 6, "relation_self_removed": 1, "partition_contradictions": 2, "contradiction_retried_calls": 2, "contradiction_deferred_calls": 0, "merge_cache_invalid": 0, "repair_cache_invalid": 0, "subtype_conflicts_a3": 0, "deferred_groups": 0}
{"doc_id": "naive-bayes", "version": 1, "reused": false, "tp": 10, "fp": 0, "fn": 0, "subtype_recall": 0.5555555555555556, "subtype_incorrect": 1, "subtype_precision": 0.8, "relations_2a_on_gold": {"same": 0, "parent_child": 0, "related": 3, "different": 0}, "calls": {"merge_calls": 11, "repair_calls": 4, "describe_calls": 1, "check_calls": 3, "merge_invalid": 0, "repair_invalid": 0}, "relation_rejected": 3, "relation_edges": 10, "relation_types": {"contrasts_with": 1, "example_of": 1, "related_to": 1, "subtype_of": 6, "uses": 1}, "relation_same_as_a3": 0, "relation_same_type_reversed_a3": 0, "relation_other_type_than_a3": 3, "relation_new_pair": 7, "relation_self_removed": 1, "partition_contradictions": 0, "contradiction_retried_calls": 0, "contradiction_deferred_calls": 0, "merge_cache_invalid": 0, "repair_cache_invalid": 0, "subtype_conflicts_a3": 2, "deferred_groups": 0}
{"doc_id": "nhap-mon-ml", "version": 1, "reused": false, "tp": 7, "fp": 1, "fn": 3, "subtype_recall": 0.5454545454545454, "subtype_incorrect": 3, "subtype_precision": 0.6666666666666666, "relations_2a_on_gold": {"same": 0, "parent_child": 2, "related": 6, "different": 0}, "calls": {"merge_calls": 22, "repair_calls": 7, "describe_calls": 4, "check_calls": 6, "merge_invalid": 0, "repair_invalid": 0}, "relation_rejected": 1, "relation_edges": 20, "relation_types": {"aims_to_achieve": 1, "component_of": 3, "contrasts_with": 2, "precedes": 2, "subtype_of": 11, "uses": 1}, "relation_same_as_a3": 3, "relation_same_type_reversed_a3": 0, "relation_other_type_than_a3": 4, "relation_new_pair": 13, "relation_self_removed": 0, "partition_contradictions": 3, "contradiction_retried_calls": 3, "contradiction_deferred_calls": 0, "merge_cache_invalid": 0, "repair_cache_invalid": 0, "subtype_conflicts_a3": 0, "deferred_groups": 0}
{"doc_id": "xstk-ch3-1", "version": 1, "reused": false, "tp": 7, "fp": 1, "fn": 9, "subtype_recall": 0.6, "subtype_incorrect": 8, "subtype_precision": 0.6363636363636364, "relations_2a_on_gold": {"same": 2, "parent_child": 0, "related": 10, "different": 0}, "calls": {"merge_calls": 24, "repair_calls": 21, "describe_calls": 5, "check_calls": 6, "merge_invalid": 0, "repair_invalid": 0}, "relation_rejected": 0, "relation_edges": 42, "relation_types": {"component_of": 1, "computed_by": 1, "computed_for": 1, "contrasts_with": 1, "estimates": 1, "example_of": 2, "informs": 1, "produces": 1, "rearranged_form_of": 1, "related_to": 1, "solves": 1, "statistic_of": 1, "subtype_of": 26, "tests": 1, "uses": 2}, "relation_same_as_a3": 1, "relation_same_type_reversed_a3": 0, "relation_other_type_than_a3": 7, "relation_new_pair": 34, "relation_self_removed": 0, "partition_contradictions": 3, "contradiction_retried_calls": 3, "contradiction_deferred_calls": 0, "merge_cache_invalid": 0, "repair_cache_invalid": 0, "subtype_conflicts_a3": 0, "deferred_groups": 0}
```

Tổng số thô để reviewer kiểm độc lập: 35 TP / 2 FP / 12 FN, precision gộp 0,9459 và F1 0,8333; `subtype_of`
25 đúng / 13 sai, precision 0,6579. Có 8 attempt bị luật R1/R2 bắt, thuộc 8 lượt phán, tất cả sửa được ở retry; 0
lượt phán bị hoãn vì mâu thuẫn, 0 merge/repair hỏng hẳn. Cổng precision gộp đăng ký trước là 0,95 nên số thô đang
thấp hơn ngưỡng; kết luận có thẩm quyền vẫn thuộc ticket 14.

Lượt phát lại cùng lệnh chạy trong sandbox chặn mạng: cả bốn dòng đều `reused=true`; mọi `merge_calls`,
`repair_calls`, `describe_calls`, `check_calls`, `merge_invalid`, `repair_invalid` đều bằng 0. Kiểm bàn giao cuối:
70 test domain+A4 xanh và toàn suite **294/294** xanh.
