"""0 USD: kiểm lại 160 phản hồi tên module đã ghi (SA-28) với các tập từ vựng khác nhau."""
import json, collections
from doc2roadmap.composition import build_artifact_store
from doc2roadmap.application.phase_b.naming import NameModulesB, _words
PINS = {"doc-1": 52, "nhap-mon-ml": 37, "naive-bayes": 37, "doc-6": 24, "xstk-ch3-1": 63, "doc-4": 22}
rec = json.load(open("artifacts/phase_b/recordings/sa28-20261018/module_title.json", encoding="utf-8"))["sessions"]
replies = {}
for s in rec:
    c = s["calls"][0]
    data = json.loads(c["prompt"])
    replies[tuple(sorted(x["node_id"] for x in data["concepts"]))] = c["reply"]["payload"]
store = build_artifact_store()
prep, corpora = {}, {}
for doc, v in PINS.items():
    up = store.load_graph(doc, v)
    nm = NameModulesB(store)
    chunks, prepared = nm._prepare(doc, up)
    nm._nodes = {n["node_id"]: n for n in up.payload["nodes"]}
    corpus = collections.Counter(w for ch in chunks.result.chunks for w in _words(ch.text))
    nm._function_words = {w for w, c in corpus.most_common(max(1, len(corpus) // 100)) if c >= 3}
    text = {ch.chunk_id: ch.text for ch in chunks.result.chunks}
    prep[doc] = (nm, up, prepared, text)
    corpora[doc] = set(corpus)
common = {w for w in set().union(*corpora.values()) if sum(w in c for c in corpora.values()) >= 4}
print("âm tiết chung ≥4/6 cuốn:", len(common), "| có: này về để dùng giúp qua bày thích sở kiến module =",
      [w for w in ["này", "về", "để", "dùng", "giúp", "qua", "bày", "thích", "sở", "kiến", "module", "dạy"] if w in common])
tot = collections.Counter()
missing_after = collections.Counter()
for doc, (nm, up, prepared, text) in prep.items():
    titles = [m.get("title", "") for m in up.payload["modules"]]
    c = collections.Counter()
    for i, (module, fallback, data, vocab, fragments) in enumerate(prepared):
        reply = replies.get(tuple(sorted(module["node_ids"])))
        if reply is None:
            c["không có phản hồi"] += 1
            continue
        teach = set()
        for nid in module["node_ids"]:
            for cid in nm._nodes[nid].get("teaching_chunk_ids", []):
                teach.update(_words(text.get(cid, "")))
        a = nm._validate(reply, module, vocab, fragments, titles, i)
        b = nm._validate(reply, module, vocab | teach, fragments, titles, i)
        cc = nm._validate(reply, module, vocab | teach | common, fragments, titles, i)
        t_only = nm._validate({"title": reply.get("title"), "description": [{"text": "", "node_ids": module["node_ids"][:1]}]},
                              module, vocab, fragments, titles, i)
        c["A hiện tại đạt"] += a is None
        c["B +đoạn dạy đạt"] += b is None
        c["C +đoạn dạy+chung đạt"] += cc is None
        c["chỉ tên đạt (A)"] += t_only is None
        if cc == "vocabulary":
            for t in [reply.get("title", ""), *(s.get("text", "") for s in reply.get("description", []))]:
                missing_after.update(w for w in _words(t) if w not in vocab | teach | common)
        c["module"] += 1
    print(doc, dict(c))
    tot.update(c)
print("TỔNG", dict(tot))
print("âm tiết vẫn thiếu ở C (top 25):", missing_after.most_common(25))

print("---- quy tắc theo chính cuốn sách: âm tiết xuất hiện ở ≥ p% số đoạn")
for p in (0.02, 0.05, 0.10):
    tot2 = collections.Counter()
    for doc, (nm, up, prepared, text) in prep.items():
        df = collections.Counter(w for t in text.values() for w in set(_words(t)))
        frequent = {w for w, n in df.items() if n >= max(3, p * len(text))}
        titles = [m.get("title", "") for m in up.payload["modules"]]
        for i, (module, fallback, data, vocab, fragments) in enumerate(prepared):
            reply = replies.get(tuple(sorted(module["node_ids"])))
            if reply is None:
                continue
            teach = set()
            for nid in module["node_ids"]:
                for cid in nm._nodes[nid].get("teaching_chunk_ids", []):
                    teach.update(_words(text.get(cid, "")))
            tot2["đạt"] += nm._validate(reply, module, vocab | teach | frequent, fragments, titles, i) is None
            tot2["cỡ tập thêm"] += len(frequent)
            tot2["module"] += 1
    print(f"p={p:.0%}: đạt {tot2['đạt']}/{tot2['module']}, cỡ tập tần suất TB {tot2['cỡ tập thêm'] // tot2['module']}")
