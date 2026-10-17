"""Vé 19j: gộp kết quả các lượt `thu_pass_chinh.py` — E4, độ trùng cạnh giữa các lượt, nhiễu mô hình khi đầu vào y hệt. 0 USD.

Lượt `noi-s0` là lượt cuối 17i trong kho riêng (pass chính ở phiên bản mentions + 1, dãy học ở phiên bản mentions + 5), cùng upstream và
cùng khoá cấu hình với các lượt chạy lại, nên được tính là một mẫu của biến thể nối tiếp.
- Độ trùng cạnh: Jaccard của tập (tiền quyết, đích) giữa hai lượt, ở cạnh pass chính và ở cạnh cứng của dãy học.
- Nhiễu mô hình: các phiên có `input_hash` trùng giữa hai lượt (đầu vào y hệt, temperature 0), tỷ lệ ra cùng tập cạnh.
Chạy từ gốc repo:  .venv/Scripts/python.exe scripts/gop-khau/phan_tich_19j.py
"""
import json
import statistics
import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cham_gop import score  # noqa: E402
from thu_pass_chinh import MENTIONS  # noqa: E402

OUT = ROOT / "tmp/v4-19j"
METRICS = ("Q6", "Q7", "Q7b", "truc_tiep_P", "truc_tiep_R", "bao_dong_P", "bao_dong_R")


def runs(doc):
    base = ROOT / "tmp/v4-17i/artifacts"
    manifest = json.loads((base / "graph" / doc / f"v{MENTIONS[doc] + 1}" / "manifest.json").read_text(encoding="utf-8"))
    found = {"noi-s0": {"store": base, "e4": score(doc, base, MENTIONS[doc] + 5),
                        "seconds": round(manifest["stats"]["runtime_seconds"], 1)}}
    for path in sorted((OUT / "ket-qua").glob(f"{doc}-*.json")):
        row = json.loads(path.read_text(encoding="utf-8"))
        main = next(stage for stage in row["stages"] if stage["stage"] == "main_edges")
        found[f"{row['variant']}-{row['tag']}"] = {"store": ROOT / row["store"], "e4": row["e4"], "seconds": main["seconds"],
                                                   "usd": row["usd"]}
    return found


def load(store, doc, version):
    return json.loads((store / "graph" / doc / f"v{version}" / "graph.json").read_text(encoding="utf-8"))


def pairs(edges):
    return {(edge["source"], edge["target"]) for edge in edges if edge.get("edge_type", "requires") == "requires"}


def jaccard(a, b):
    return round(len(a & b) / len(a | b), 3) if a | b else None


def session_outputs(graph):
    result = {}
    for row in graph["decision_log"]:
        if row.get("stage") == "main" and row.get("valid") and isinstance(row.get("output"), dict):
            result[row["input_hash"]] = {(edge["prerequisite"], edge["target"]) for edge in row["output"].get("edges", [])}
    return result


def main():
    report = {}
    for doc in MENTIONS:
        found = runs(doc)
        if len(found) < 2:
            continue
        graphs = {name: (load(row["store"], doc, MENTIONS[doc] + 1), load(row["store"], doc, MENTIONS[doc] + 5))
                  for name, row in found.items()}
        overlap = []
        for left, right in combinations(sorted(found), 2):
            same_input = set(session_outputs(graphs[left][0])) & set(session_outputs(graphs[right][0]))
            outputs = session_outputs(graphs[left][0]), session_outputs(graphs[right][0])
            overlap.append({
                "cap": [left, right],
                "jaccard_pass_chinh": jaccard(pairs(graphs[left][0]["main_edges"]), pairs(graphs[right][0]["main_edges"])),
                "jaccard_canh_cung_day_hoc": jaccard(
                    pairs(edge for edge in graphs[left][1]["requires_edges"] if not edge.get("soft")),
                    pairs(edge for edge in graphs[right][1]["requires_edges"] if not edge.get("soft"))),
                "phien_cung_dau_vao": len(same_input),
                "phien_cung_dau_ra": sum(outputs[0][key] == outputs[1][key] for key in same_input),
                "jaccard_tb_phien_cung_dau_vao": round(statistics.mean(
                    jaccard(outputs[0][key], outputs[1][key]) or 1.0 for key in same_input), 3) if same_input else None,
            })
        summary = {}
        for variant in ("noi", "song"):
            names = [name for name in found if name.startswith(variant + "-")]
            summary[variant] = {"luot": names, **{metric: {
                "gia_tri": [found[name]["e4"][metric] for name in names],
                "min": min(found[name]["e4"][metric] for name in names),
                "max": max(found[name]["e4"][metric] for name in names),
                "tb": round(statistics.mean(found[name]["e4"][metric] for name in names), 3)}
                for metric in METRICS if names},
                "giay_pass_chinh": [found[name]["seconds"] for name in names],
                "usd": [found[name].get("usd") for name in names]}
        report[doc] = {"e4": summary, "do_trung": overlap}
    path = OUT / "ket-qua" / "tong-hop.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
