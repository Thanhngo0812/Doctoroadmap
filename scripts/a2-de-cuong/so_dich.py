"""So khái niệm đích vàng: vai trò hiện tại và vai trò sau sửa luật lặp A2 (nhóm không phải danh sách tên mục -> giả định noi_dung)."""
import json, sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from mo_phong_neo import GOLD, load, run  # noqa: E402
from do_phu_tieu_de import NUM, coverage, norm  # noqa: E402
from doc2roadmap.application.use_cases.a8_score import load_gold, merge_gold  # noqa: E402


def flagged_sections(doc, chunks_version):
    d = Path("artifacts/chunks") / doc / f"v{chunks_version}"
    secs = json.loads((d / "sections.json").read_text(encoding="utf-8"))
    raw = json.loads((d / "chunks.json").read_text(encoding="utf-8"))
    raw = raw["chunks"] if isinstance(raw, dict) else raw
    text = defaultdict(list)
    for c in raw:
        text[c["parent_section_id"]].append(c["text"])
    ordered = sorted(secs, key=lambda s: (s["order_index"], s["level"]))
    first = {}
    for s in ordered:
        first.setdefault(s["parent_section_id"], s["section_id"])
    rep = Counter(s["title"] for s in ordered if s["section_id"] == first.get(s["parent_section_id"]))
    out = set()
    for t in [t for t, n in rep.items() if n >= 3]:
        others = {norm(NUM.sub("", s["title"])) for s in ordered if s["title"] != t and s["level"] > 0} - {norm(NUM.sub("", t)), ""}
        members = [s for s in ordered if s["title"] == t]
        covs = sorted(c for c in (coverage(" ".join(text[s["section_id"]]), others) for s in members) if c is not None)
        # Luật đề xuất của vé 05a: cả nhóm cùng tiêu đề là đề cương khi trung vị độ phủ >= 0,5; còn lại để lớp nhãn LLM quyết.
        if not covs or covs[len(covs) // 2] < .5:
            out.update(s["section_id"] for s in members)
    return out


def main():
    doc = sys.argv[1]
    store, canon, stored = load(doc)
    flag = flagged_sections(doc, stored.version)
    _, before, _ = run(doc)
    _, after, by_id = run(doc, relabel=lambda c: c.parent_section_id in flag)
    relabeled = {cid for cid, c in by_id.items() if c.parent_section_id in flag}
    nodes = {n["node_id"]: n for n in canon.payload["nodes"]}
    redirects = canon.payload.get("redirects", {})


    def cur(i):
        while i in redirects:
            i = redirects[i]
        return i


    changed = [k for k in after.candidates_of if [c["sentence"] for c in after.candidates_of[k]] != [c["sentence"] for c in before.candidates_of.get(k, [])]]
    gained = [k for k in changed if not before.candidates_of.get(k)]
    print(f"{doc}: mục đổi vai trò={len(flag)}, chunk đổi={len(relabeled)}; khái niệm đổi ứng viên={len(changed)} "
          f"(từ không có ứng viên sang có={len(gained)})")
    if doc in GOLD:
        gold = load_gold(Path("artifacts/a8-gold") / GOLD[doc])
        ids = {cur(i) for i in set(gold["targets"]) | {x for e in merge_gold([gold], mode="union") for x in e}}
        status = Counter(nodes[i].get("teaching_status") for i in ids if i in nodes)
        print("  khái niệm vàng (đích + đầu cạnh):", len(ids), dict(status))
        for i in sorted(ids, key=lambda i: nodes.get(i, {}).get("name", "")):
            n = nodes.get(i)
            if n is None or n.get("teaching_status") == "taught":
                continue
            b, a = before.candidates_of.get(i, []), after.candidates_of.get(i, [])
            new = [c for c in a if c["chunk_id"] in relabeled]
            print(f"  - {n['name']!r}: {n.get('teaching_status')} {n.get('mentioned_in', '')} | ứng viên {len(b)} -> {len(a)}, "
                  f"mới từ mục sửa {len(new)}")
            for c in new[:2]:
                print(f"      + {c['sentence'][:150]!r}")


if __name__ == "__main__":
    main()
