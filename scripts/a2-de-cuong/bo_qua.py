"""Đếm khái niệm bị mã xếp 'chỉ nhắc' mà không hỏi mô hình (chỉ có căn cứ ngoài vùng nội dung), theo vùng. Chỉ đọc."""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mo_phong_neo import run  # noqa: E402

for doc in ["doc-1", "nhap-mon-ml", "naive-bayes", "doc-6", "xstk-ch3-1", "doc-4"]:
    canon, core, by_id = run(doc)
    skipped = [k for k, v in core.candidates_of.items() if not v and core.outside_of.get(k)]
    unchecked = [k for k, v in core.candidates_of.items() if not v and not core.outside_of.get(k)]
    regions = Counter(r for k in skipped for r in core.outside_of[k])
    nodes = {n["node_id"]: n for n in canon.payload["nodes"]}
    ev_out = sum(1 for k in skipped if any(by_id.get(s.get("chunk_id")) is not None
                 and getattr(by_id[s["chunk_id"]], "role", "noi_dung") != "noi_dung" for s in nodes[k].get("evidence", [])))
    asked = sum(1 for v in core.candidates_of.values() if v)
    print(f"{doc:12} học được={len(core.candidates_of):4} hỏi mô hình={asked:4} mã xếp chỉ-nhắc={len(skipped):3} "
          f"(căn cứ A3 nằm ngoài nội dung: {ev_out}) unchecked={len(unchecked):3} vùng={dict(regions)}")
