# 06 — Chạy nhánh thử vào kho riêng

**What to build:** Chạy code mới trên bốn tài liệu bằng mô hình thật, ghi vào kho riêng. `canonical/latest` không đổi.

**Blocked by:** 03 — Lắp cạnh; 04 — Prompt v3 và fixture; 05 — `a4-evaluate`

**Status:** done

- [x] Chạy lệnh sau; mọi khâu dùng flash-lite:

      .\.venv\Scripts\python.exe scripts\run_a4_arm.py --out artifacts/a4-ab/gemini-3.1-flash-lite-relations-v3 `
          --doc-id baocao-canhan --doc-id naive-bayes --doc-id nhap-mon-ml --doc-id xstk-ch3-1

- [x] **Không** chạy `doc2roadmap a4` vào kho chính cho tới khi ticket 07 kết luận.
- [x] Dán vào ticket này dòng JSON của từng tài liệu và số lời gọi thật, không ước lượng.
- [x] Chạy lại cùng lệnh khi chặn mạng: cả bốn tài liệu phải `reused=true`, 0 lời gọi.
- [x] Toàn bộ test xanh, chặn mạng.

## Kết quả lời gọi thật — 2026-09-13

```jsonl
{"doc_id":"baocao-canhan","version":1,"reused":false,"tp":11,"fp":1,"fn":0,"subtype_recall":0.0,"subtype_incorrect":1,"subtype_precision":0.0,"relations_2a_on_gold":{"same":0,"parent_child":1,"related":3,"different":0},"calls":{"merge_calls":12,"repair_calls":6,"describe_calls":2,"check_calls":3,"merge_invalid":0,"repair_invalid":0},"relation_rejected":3,"relation_edges":6,"relation_types":{"component_of":1,"example_of":1,"subtype_of":1,"supports":1,"used_with":1,"uses":1},"relation_same_as_a3":1,"relation_other_type_than_a3":1,"relation_new_pair":4,"relation_self_removed":1,"subtype_conflicts_a3":0,"deferred_groups":0}
{"doc_id":"naive-bayes","version":1,"reused":false,"tp":10,"fp":0,"fn":0,"subtype_recall":0.5555555555555556,"subtype_incorrect":1,"subtype_precision":0.8,"relations_2a_on_gold":{"same":0,"parent_child":0,"related":3,"different":0},"calls":{"merge_calls":11,"repair_calls":4,"describe_calls":1,"check_calls":3,"merge_invalid":0,"repair_invalid":0},"relation_rejected":3,"relation_edges":10,"relation_types":{"contrasts_with":1,"example_of":1,"related_to":1,"subtype_of":6,"uses":1},"relation_same_as_a3":0,"relation_other_type_than_a3":3,"relation_new_pair":7,"relation_self_removed":1,"subtype_conflicts_a3":2,"deferred_groups":0}
{"doc_id":"nhap-mon-ml","version":1,"reused":false,"tp":7,"fp":3,"fn":3,"subtype_recall":0.45454545454545453,"subtype_incorrect":2,"subtype_precision":0.7142857142857143,"relations_2a_on_gold":{"same":1,"parent_child":3,"related":5,"different":0},"calls":{"merge_calls":19,"repair_calls":7,"describe_calls":3,"check_calls":6,"merge_invalid":0,"repair_invalid":0},"relation_rejected":4,"relation_edges":18,"relation_types":{"aims_to_achieve":1,"component_of":3,"contrasts_with":2,"equivalent_to":1,"example_of":1,"subtype_of":9,"uses":1},"relation_same_as_a3":3,"relation_other_type_than_a3":4,"relation_new_pair":11,"relation_self_removed":0,"subtype_conflicts_a3":0,"deferred_groups":0}
{"doc_id":"xstk-ch3-1","version":1,"reused":false,"tp":10,"fp":5,"fn":6,"subtype_recall":0.56,"subtype_incorrect":6,"subtype_precision":0.6842105263157895,"relations_2a_on_gold":{"same":1,"parent_child":0,"related":11,"different":0},"calls":{"merge_calls":21,"repair_calls":21,"describe_calls":8,"check_calls":7,"merge_invalid":0,"repair_invalid":0},"relation_rejected":4,"relation_edges":39,"relation_types":{"component_of":1,"computed_by":1,"computed_for":1,"contrasts_with":1,"estimates":1,"example_of":1,"informs":1,"produces":1,"rearranged_form_of":1,"related_to":1,"solves":1,"statistic_of":1,"subtype_of":23,"tests":1,"uses":3},"relation_same_as_a3":1,"relation_other_type_than_a3":7,"relation_new_pair":31,"relation_self_removed":0,"subtype_conflicts_a3":0,"deferred_groups":0}
```

Tổng lời gọi thật: **134** = 63 merge + 38 repair + 14 describe + 19 check; 0 lượt invalid. Hai số 0 của
`relation_self_removed` ban đầu là khoá thưa của `Counter`; code và phần in đã được chốt để biểu diễn rõ là 0.

## Phát lại chặn mạng

Cùng lệnh kết thúc trong 2,95 giây: cả bốn tài liệu `version=1`, `reused=true`; sáu bộ đếm call của từng tài liệu đều bằng 0.
Kho chính vẫn giữ nguyên `baocao-canhan v7`, `naive-bayes v6`, `nhap-mon-ml v6`, `xstk-ch3-1 v6`.
