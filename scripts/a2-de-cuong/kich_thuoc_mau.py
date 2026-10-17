import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from mo_phong_neo import run, load  # noqa: E402
from so_dich import flagged_sections  # noqa: E402

doc = "xstk-ch3-1"
store, canon, stored = load(doc)
flag = flagged_sections(doc, stored.version)
_, after, by_id = run(doc, relabel=lambda c: c.parent_section_id in flag)
nodes = {n["node_id"]: n for n in canon.payload["nodes"]}
for name in ["Bài toán tìm kích thước mẫu", "Xác định kích thước mẫu", "Xác định kích thước mẫu trong ước lượng trung bình", "Độ chính xác"]:
    k = next(i for i, n in nodes.items() if n["name"] == name)
    n = nodes[k]
    print("==", name, "| alias:", [a["name"] if isinstance(a, dict) else a for a in n.get("aliases", [])],
          "| nguồn:", len(n.get("source_chunk_ids", [])), "| căn cứ:", [s.get("quote", "")[:80] for s in n.get("evidence", [])][:2])
    for c in after.candidates_of[k]:
        ch = by_id[c["chunk_id"]]
        print("   ", c["cand_id"], " > ".join((ch.section_path or [])[-2:])[:50], "|", c["sentence"][:120].replace("\n", " "))
print("\n== văn bản mục 2.4")
for ch in sorted(by_id.values(), key=lambda c: c.order_index):
    if any("2.4" in p for p in (ch.section_path or [])):
        print(f"[{ch.role}] {' > '.join((ch.section_path or [])[-2:])[:50]} :: {ch.text[:400]!r}\n")
