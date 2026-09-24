"""Vé v2-06 lượt 1: pass cạnh ngầm trên identity (doc-1 v26, doc-2 v20), rồi A10; đo theo đúng cổng đã khoá trong vé.

Có gọi mô hình (< 1 USD). Chạy từ gốc repo:  .venv/Scripts/python.exe scripts/phan-tich-v2/chay_canh_ngam.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")
from doc2roadmap.application.use_cases.a8_score import score_roadmap_order  # noqa: E402
from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap  # noqa: E402
from doc2roadmap.application.use_cases.find_implicit import FindImplicitPrerequisites  # noqa: E402
from doc2roadmap.composition import build_learning_graph  # noqa: E402
from doc2roadmap.domain.global_validation import strongly_connected_components  # noqa: E402

RUNS = {"doc-1": (26, 27, "artifacts/a8-gold/doc-1-10-12-vang.json"),
        "doc-2": (20, 21, "artifacts/a8-gold/doc-2-98-115-vang.json")}


def graph(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def children_of(payload):
    children = {}
    for edge in [*payload["requires_edges"], *payload.get("bypassed_edges", [])]:
        children.setdefault(edge["source"], set()).add(edge["target"])
    return children


def reaches(children, a, b):
    stack, seen = [a], {a}
    while stack:
        for c in children.get(stack.pop(), ()):
            if c == b:
                return True
            if c not in seen:
                seen.add(c)
                stack.append(c)
    return False


def ancestors(children, node):
    parents = {}
    for a, bs in children.items():
        for b in bs:
            parents.setdefault(b, set()).add(a)
    stack, seen = [node], set()
    while stack:
        for p in parents.get(stack.pop(), ()):
            if p not in seen:
                seen.add(p)
                stack.append(p)
    return seen


def gold_pairs(payload, gold):
    identity = payload.get("identity_map", {})
    pairs = {(identity.get(e["prerequisite"], e["prerequisite"]), identity.get(e["target"], e["target"])) for e in gold["edges"]}
    targets = {identity.get(t, t) for t in gold["targets"]}
    return {p for p in pairs if p[0] != p[1]}, targets


pipeline, _ = build_learning_graph(allow_spend=True)
store = pipeline.teaching.store
finder = FindImplicitPrerequisites(store, pipeline.teaching.model, concurrency=4)
roadmap = BuildRoadmap(store, stage_cap=8)
total = 0.0
for doc, (identity_version, baseline_version, gold_path) in RUNS.items():
    implicit, _ = finder.execute(doc, upstream=store.load_graph(doc, identity_version))
    stages, _ = roadmap.execute(doc, upstream=implicit)
    usd = implicit.payload["cost_summary"].get("implicit_usd", 0.0)
    total += usd
    before = graph(f"artifacts/graph/{doc}/v{baseline_version}/graph.json")
    after = stages.payload
    gold = graph(gold_path)
    pairs, targets = gold_pairs(after, gold)
    kb, ka = children_of(before), children_of(after)
    had = {p for p in pairs if reaches(kb, *p)}
    has = {p for p in pairs if reaches(ka, *p)}
    # bất biến
    edges = after["requires_edges"]
    cycles = [c for c in strongly_connected_components({n for e in edges for n in (e["source"], e["target"])}, edges) if len(c) > 1]
    chunk_text = {c.chunk_id: c.text for c in store.load_chunks(doc, implicit.manifest["config"]["chunks_version"]).result.chunks}
    implicit_edges = [e for e in edges if e.get("origin") == "implicit_pass"]
    bad_quote = [e for e in implicit_edges if " ".join(e["quote"].split()) not in " ".join(chunk_text[e["chunk_ids"][0]].split())]
    stats = implicit.payload["stats"]
    lost = had - has
    in_scope = [e for e in implicit_edges if e["target"] in targets]
    gold_hit = [e for e in in_scope if (e["source"], e["target"]) in pairs]
    len_before = sum(len(ancestors(kb, t)) for t in targets) / len(targets)
    len_after = sum(len(ancestors(ka, t)) for t in targets) / len(targets)
    report = score_roadmap_order(stages.path / "graph.json", [Path(gold_path)])
    g = report["gold_order"]
    print(f"{doc} implicit v{implicit.version} → stages v{stages.version} | {usd:.3f} USD | đích hỏi {stats['implicit_target_count']}"
          f", đề xuất {stats['implicit_proposed']}, thêm {stats['implicit_added']}, gỡ do chu trình {stats['implicit_removed_by_cycles']}"
          f", đích hỏng {stats['implicit_invalid_targets']}")
    print(f"   bất biến: chu trình {len(cycles)}, câu trích sai {len(bad_quote)}")
    print(f"   Q5 {len(had)}/{len(pairs)} = {len(had)/len(pairs):.0%} → {len(has)}/{len(pairs)} = {len(has)/len(pairs):.0%}"
          f" | cạnh vàng mất đường {len(lost)} | +{len(has) - len(had) + len(lost)} cạnh vàng, {(len(has)-len(had))/usd if usd else 0:.1f}/USD")
    print(f"   cạnh ngầm tới đích vàng {len(in_scope)}, trùng cạnh vàng trực tiếp {len(gold_hit)}"
          f" | tổ tiên trung bình của đích vàng {len_before:.1f} → {len_after:.1f}")
    print(f"   Q6 {g['learning_order_error']:.1%} | Q7 {report['target_coverage']['mean_coverage']:.0%}"
          f" ({report['target_coverage']['complete']}/{report['target_coverage']['targets']} đích đủ)")
print(f"Tổng chi vòng này: {total:.3f} USD")
