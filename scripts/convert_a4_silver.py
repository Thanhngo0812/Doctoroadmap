"""Map existing Appendix A annotations; never infer missing or ambiguous labels."""
import json
import re
from pathlib import Path

from doc2roadmap.composition import build_artifact_store
from doc2roadmap.application.use_cases.a4_gold import gold_items
from doc2roadmap.domain.canonical import digest, name_key


def main():
    store = build_artifact_store()
    docs = ["nhap-mon-ml", "xstk-ch3-1", "baocao-canhan", "naive-bayes"]
    sheet = gold_items(store, docs)
    source = Path("report/nghien-cuu-a4-a5-hop-nhat-thuc-the.md").read_text(encoding="utf-8")
    appendix = source.split("## Phụ lục A", 1)[1].split("## Nguồn", 1)[0]
    examples = []
    for line in appendix.splitlines():
        match = re.match(r"\| ([\w-]+) \| `([^`]+)` / `([^`]+)`", line)
        if match:
            examples.append((match[1], match[2], match[3], "same"))
    negative = appendix.split("**Khác hẳn", 1)[1].split("**Cha–con", 1)[0]
    for block in negative.split("\n- "):
        label = "related" if block.startswith("*Anh em*") else "different"
        examples.extend((None, a, b, label) for a, b in re.findall(r"`([^`]+)`\s*/\s*`([^`]+)`", block))
    ambiguous = appendix.split("**Cha–con", 1)[1].split("**Alias sai", 1)[0]
    examples.extend((None, a, b, "uncertain") for a, b in re.findall(r"`([^`]+)`\s*/\s*`([^`]+)`", ambiguous))
    items, skipped = {}, []
    groups = {doc: {} for doc in docs}
    for item in sheet["items"]:
        for group in item["groups"]:
            groups[item["doc_id"]][group["name_key"]] = group
    for doc, a, b, label in examples:
        matches = [(d, groups[d][name_key(a)], groups[d][name_key(b)]) for d in ([doc] if doc else docs)
                   if name_key(a) in groups[d] and name_key(b) in groups[d]]
        if len(matches) != 1:
            skipped.append({"names": [a, b], "reason": "no unique exact-name match; no inference"})
            continue
        d, left, right = matches[0]
        pair = sorted([left, right], key=lambda g: g["group_id"])
        id = digest([d, "pair", [(g["name_key"], [m["candidate_id"] for m in g["members"]]) for g in pair]])
        items[id] = {"item_id": id, "doc_id": d, "kind": "pair", "groups": pair, "label": label}
    payload = {"schema_version": 1, "documents": sheet["documents"], "items": list(items.values()),
               "annotator": "Appendix A — existing secondary annotations (report)",
               "annotated_at": "2026-09-11", "timestamp_precision": "day; time unspecified in source",
               "blind_before_first_a4_run": True,
               "provenance": "Existing report annotations predate A4 LLM runs; not newly annotated by the implementation agent.",
               "skipped": skipped, "mapped_count": len(items), "skipped_count": len(skipped)}
    target = Path("tests/fixtures/a4/silver-appendix-a.json")
    store._write(target, payload)
    print(json.dumps({"path": str(target), "mapped": len(items), "skipped": len(skipped)}))


if __name__ == "__main__":
    main()
