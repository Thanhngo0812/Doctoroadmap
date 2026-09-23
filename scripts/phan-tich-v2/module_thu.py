"""Ba phép đo cho kế hoạch: CG đọc theo sách trong stage; chuỗi dài nhất; module liền mạch bám mục sách."""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "src")
from doc2roadmap.domain.gold_scoring import gold_order_violations  # noqa: E402
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore  # noqa: E402

exec(Path(__file__).with_name("baseline_sach.py").read_text(encoding="utf-8").split("for doc, chapter, version in CASES:")[0])
store = JsonArtifactStore(Path("artifacts"))


def section_of(nodes, doc):
    result = store.load_latest_chunks(doc).result
    chunk = {c.chunk_id: c for c in result.chunks}
    sections = {s.section_id: s for s in result.sections}

    def top(section_id, level):
        current = sections[section_id]
        while current.level > level and current.parent_section_id in sections:
            current = sections[current.parent_section_id]
        return current.section_id

    out = {}
    for n in nodes:
        ids = n.get("teaching_chunk_ids") or n.get("defining_chunk_ids", [])
        ids = sorted((chunk[c] for c in ids if c in chunk), key=lambda c: c.order_index)
        out[n["node_id"]] = top(ids[0].parent_section_id, 2) if ids else None
    return out


def modules(sequence, section, width=W):
    """Gom dãy thành module liền mạch ≤ W; ưu tiên cắt ở ranh giới mục khi module đã đủ nửa trần."""
    result, current = [], []
    for node in sequence:
        boundary = current and section.get(node) != section.get(current[-1])
        if current and (len(current) >= width or (boundary and len(current) >= width // 2)):
            result.append(current)
            current = []
        current.append(node)
    if current:
        result.append(current)
    return result


def coherence(groups, section):
    single = sum(1 for g in groups if len({section.get(n) for n in g}) == 1)
    return single, len(groups)


for doc, chapter, version in CASES:
    payload = json.loads(Path(f"artifacts/graph/{doc}/v{version}/graph.json").read_text(encoding="utf-8"))
    gold = {(e["prerequisite"], e["target"])
            for e in json.loads(Path(f"artifacts/a8-gold/{doc}-{chapter}-vang.json").read_text(encoding="utf-8"))["edges"]}
    placed = {n for s in payload["stages"] for n in s["node_ids"]}
    nodes = [n for n in payload["nodes"] if n["node_id"] in placed]
    by_id = {n["node_id"]: n for n in nodes}
    edges = [e for e in [*payload["requires_edges"], *payload.get("bypassed_edges", [])]
             if e["source"] in placed and e["target"] in placed]
    section = section_of(nodes, doc)

    # (a) CG nếu người học đọc mỗi stage theo thứ tự sách
    cg = [sorted(s["node_ids"], key=lambda n: (position(by_id[n]), n)) for s in payload["stages"]]
    cg_linear = [n for s in cg for n in s]
    a = gold_order_violations([[n] for n in cg_linear], gold)
    seq1, parents = linear_extension(nodes, edges)
    b = gold_order_violations([[n] for n in seq1], gold)
    print(f"=== {doc} v{version}")
    print(f"  (a) dãy tuyến tính — CG đọc theo sách trong stage: ngược {a['violated']} ({a['learning_order_error']:.1%}) | "
          f"B1: ngược {b['violated']} ({b['learning_order_error']:.1%})")

    # (b) chuỗi dài nhất
    pos_in = {n: i for i, n in enumerate(seq1)}
    longest, prev = {}, {}
    for n in seq1:
        best = max(((longest[p] + 1, p) for p in parents[n]), default=(1, None))
        longest[n], prev[n] = best
    end = max(longest, key=longest.get)
    chain = []
    while end:
        chain.append(by_id[end]["name"])
        end = prev[end]
    print(f"  (b) chuỗi dài nhất {len(chain)} node: " + " → ".join(reversed(chain)))

    # (c) module liền mạch bám mục sách, thứ tự bên trong theo dãy B1
    mods = modules(seq1, section)
    single, total = coherence(mods, section)
    cg_single, cg_total = coherence(payload_stages := [s["node_ids"] for s in payload["stages"]], section)
    sizes = Counter(len(m) for m in mods)
    print(f"  (c) module bám mục: {total} module, {single}/{total} nằm gọn trong một mục "
          f"| CG: {cg_single}/{cg_total} stage nằm gọn trong một mục | cỡ module {dict(sorted(sizes.items()))}")
