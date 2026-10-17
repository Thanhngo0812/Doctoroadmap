"""Trần số cạnh vàng xstk trở lại phạm vi nếu mọi khái niệm vàng có thêm ứng viên đều được dạy. Chỉ đọc."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from mo_phong_neo import GOLD, load, run  # noqa: E402
from so_dich import flagged_sections  # noqa: E402
from doc2roadmap.application.use_cases.a8_score import load_gold, merge_gold  # noqa: E402

doc = "xstk-ch3-1"
store, canon, stored = load(doc)
flag = flagged_sections(doc, stored.version)
_, before, _ = run(doc)
_, after, by_id = run(doc, relabel=lambda c: c.parent_section_id in flag)
red = canon.payload.get("redirects", {})
cur = lambda i: cur(red[i]) if i in red else i  # noqa: E731
nodes = {n["node_id"]: n for n in canon.payload["nodes"]}
gold = load_gold(Path("artifacts/a8-gold") / GOLD[doc])
edges = {(cur(a), cur(b)) for a, b in merge_gold([gold], mode="union")}
targets = {cur(t) for t in gold["targets"]}
taught = {k for k, n in nodes.items() if n.get("teaching_status") in {"taught", "uncertain"}}
relabeled = {cid for cid, c in by_id.items() if c.parent_section_id in flag}
gain = {k for k, v in after.candidates_of.items() if any(c["chunk_id"] in relabeled for c in v)} - taught
inside = lambda s: sum(1 for a, b in edges if a in s and b in s)  # noqa: E731
print(f"đích vàng: {len(targets)}, đang trong dãy học {len(targets & taught)}; có thêm ứng viên từ 'Cách giải' {len(targets & gain)}")
print(f"cạnh vàng: {len(edges)}, hai đầu trong dãy học hiện nay {inside(taught)}, trần sau sửa {inside(taught | gain)}")
