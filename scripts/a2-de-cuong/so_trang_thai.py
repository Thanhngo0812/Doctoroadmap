import json, sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, "scripts/a2-de-cuong"); sys.path.insert(0, "src")
from mo_phong_neo import GOLD  # noqa: E402
from doc2roadmap.application.use_cases.a8_score import load_gold, merge_gold  # noqa: E402

doc, a, b = sys.argv[1], sys.argv[2], sys.argv[3]
load = lambda v: json.load(open(f"artifacts/canonical/{doc}/{v}/canonical.json", encoding="utf-8"))  # noqa: E731
A, B = load(a), load(b)
na, nb = {n["node_id"]: n for n in A["nodes"]}, {n["node_id"]: n for n in B["nodes"]}
red = B.get("redirects", {})
cur = lambda i: cur(red[i]) if i in red else i  # noqa: E731
st = lambda n: n.get("teaching_status") if n else None  # noqa: E731
changed = [(k, st(na.get(k)), st(nb[k])) for k in nb if na.get(k) and st(na[k]) != st(nb[k])]
print(f"{doc} {a}->{b}: khái niệm đổi trạng thái {len(changed)}:", Counter((x, y) for _, x, y in changed))
anc = {r["input"]["node_id"]: r for r in B.get("anchor_decision_log", []) if r.get("stage") == "anchor" and r.get("valid", True)}
if doc in GOLD:
    gold = load_gold(Path("artifacts/a8-gold") / GOLD[doc])
    ids = {cur(i) for i in set(gold["targets"]) | {x for e in merge_gold([gold], mode="union") for x in e}}
    targets = {cur(t) for t in gold["targets"]}
    inseq = lambda N, S: sum(1 for i in S if st(N.get(i)) in {"taught", "uncertain"})  # noqa: E731
    edges = {(cur(x), cur(y)) for x, y in merge_gold([gold], mode="union")}
    both = lambda N: sum(1 for x, y in edges if st(N.get(x)) in {"taught", "uncertain"} and st(N.get(y)) in {"taught", "uncertain"})  # noqa: E731
    print(f"  đích trong dãy học: {inseq(na, targets)} -> {inseq(nb, targets)} / {len(targets)}; cạnh vàng hai đầu trong dãy: {both(na)} -> {both(nb)} / {len(edges)}")
    for i in sorted(ids, key=lambda i: nb.get(i, {}).get("name", "")):
        if i in nb and st(na.get(i)) != st(nb[i]) or (i in nb and st(nb[i]) not in {"taught"}):
            n = nb[i]; out = (anc.get(i) or {}).get("output") or {}
            sent = next((c["sentence"] for c in (anc.get(i) or {}).get("input", {}).get("candidates", []) if c["cand_id"] == out.get("anchor")), "")
            print(f"  - {n['name']!r}: {st(na.get(i))} -> {st(n)} | {out.get('status')} | neo: {sent[:110]!r} | lý do: {str(out.get('reason',''))[:140]!r}")
