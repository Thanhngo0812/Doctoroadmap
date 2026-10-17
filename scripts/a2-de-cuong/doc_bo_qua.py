import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from mo_phong_neo import run  # noqa: E402

for doc in sys.argv[1:]:
    canon, core, by_id = run(doc)
    nodes = {n["node_id"]: n for n in canon.payload["nodes"]}
    for k, v in core.candidates_of.items():
        if v or not core.outside_of.get(k):
            continue
        n = nodes[k]
        ev = next((s for s in n.get("evidence", []) if s.get("chunk_id") in by_id), {})
        c = by_id.get(ev.get("chunk_id"))
        path = " > ".join((getattr(c, "section_path", None) or [])[-2:]) if c else ""
        print(f"{doc} | {n['name'][:45]!r} | {core.outside_of[k]} | mục: {path[:60]!r} | căn cứ: {ev.get('quote', '')[:110]!r}")
