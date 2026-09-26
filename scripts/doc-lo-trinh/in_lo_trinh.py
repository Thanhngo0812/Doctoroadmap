"""In lộ trình của một artifact `stages` ra văn bản đọc được, kèm vài chẩn đoán độ dễ đọc. Không gọi mô hình.

Chạy từ gốc repo:  .venv/Scripts/python.exe scripts/doc-lo-trinh/in_lo_trinh.py <doc> [phiên bản stages] [--tat]
`--tat`: chỉ in chẩn đoán, không in từng module.
"""
import json
import statistics
import sys
from collections import Counter
from pathlib import Path


def latest_stages(doc):
    versions = sorted((int(p.name[1:]) for p in Path(f"artifacts/graph/{doc}").glob("v*")), reverse=True)
    for version in versions:
        manifest = json.loads(Path(f"artifacts/graph/{doc}/v{version}/manifest.json").read_text(encoding="utf-8"))
        if manifest.get("stage") == "stages":
            return version
    raise SystemExit(f"{doc}: chưa có artifact stages")


def main(doc, version=None, short=False):
    version = version or latest_stages(doc)
    payload = json.loads(Path(f"artifacts/graph/{doc}/v{version}/graph.json").read_text(encoding="utf-8"))
    nodes = {n["node_id"]: n for n in payload["nodes"]}
    names = {n["node_id"]: n["name"] for n in [*payload["nodes"], *payload.get("excluded_nodes", []),
                                               *payload.get("merged_nodes", [])]}
    modules = payload["modules"]
    sizes = [len(m["node_ids"]) for m in modules]
    statuses = Counter(nodes[n].get("teaching_status") for m in modules for n in m["node_ids"])
    prereq_counts = [len(nodes[n].get("prerequisites", [])) for m in modules for n in m["node_ids"]]
    position = {n: i for i, n in enumerate(payload["sequence"])}
    gaps = [position[n] - position[p] for m in modules for n in m["node_ids"]
            for p in nodes[n].get("prerequisites", []) if p in position]
    print(f"# {doc} — stages v{version}: {len(payload['sequence'])} khái niệm, {len(modules)} module")
    print(f"  cỡ module: trung vị {statistics.median(sizes)}, nhỏ nhất {min(sizes)}, lớn nhất {max(sizes)}; "
          f"module 1–2 khái niệm: {sum(1 for s in sizes if s <= 2)}")
    print(f"  trạng thái dạy: {dict(statuses)}")
    print(f"  tiên quyết trực tiếp / khái niệm: trung vị {statistics.median(prereq_counts)}, lớn nhất {max(prereq_counts)}; "
          f"khái niệm không tiên quyết: {sum(1 for c in prereq_counts if c == 0)}")
    if gaps:
        print(f"  khoảng cách tiên quyết trong dãy (số khái niệm): trung vị {statistics.median(gaps)}, lớn nhất {max(gaps)}")
    excluded = payload.get("excluded_nodes", [])
    if excluded:
        print(f"  ngoài lộ trình: {[(n['name'], n.get('teaching_status')) for n in excluded]}")
    merged = payload.get("merged_nodes", [])
    if merged:
        print(f"  đã gộp: {[(n['name'], names.get(n.get('merged_into'))) for n in merged]}")
    if short:
        return
    for module in modules:
        print(f"\n## {module['index'] + 1}. {module['title']}")
        for node_id in module["node_ids"]:
            node = nodes[node_id]
            mark = "" if node.get("teaching_status") == "taught" else f" [{node.get('teaching_status')}]"
            needs = ", ".join(names.get(p, p) for p in node.get("prerequisites", []))
            print(f"  - {node['name']}{mark}" + (f"  ← {needs}" if needs else ""))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--tat"]
    main(args[0], int(args[1]) if len(args) > 1 else None, short="--tat" in sys.argv)
