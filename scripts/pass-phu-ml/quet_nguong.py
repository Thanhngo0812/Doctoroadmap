"""Quét ngưỡng của bộ kiểm cạnh cứng: mỗi mức giữ k% ứng viên cửa sổ có điểm cao nhất → lắp cạnh → A9 → A10 → chấm trên vàng. 0 USD.

Mục đích: vẽ đường độ chính xác–độ phủ của bản không LLM trên vàng người và đặt điểm LLM v3 lên cùng hình, để so cả đường chứ không so một ngưỡng.
**Không** dùng để chọn ngưỡng sản phẩm (chọn trên vàng là rò dữ liệu đo); ngưỡng chính thức do E2b chọn trên nhãn của tài liệu học.
Nạp artifact một lần cho mọi mức. Chạy từ gốc repo:
  .venv/Scripts/python.exe scripts/pass-phu-ml/quet_nguong.py <doc> <lượt điểm> [--muc=0.1,0.2,...]
"""
import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "scripts/pass-phu-ml")
from lap_canh import assemble  # noqa: E402
from phat_lai_e4 import GOLD_DOCS, replay, score_payload, summary  # noqa: E402
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore  # noqa: E402


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    doc, run = [arg for arg in sys.argv[1:] if not arg.startswith("--")][:2]
    levels = [float(value) for value in options.get("muc", "0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,1.0").split(",")]
    table = {}
    with open(f"tmp/pass-phu-ml/diem/{run}/{doc}.csv", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            table[row["pair_id"], row["x"], row["y"]] = float(row["score"])
    positive = sorted((value for value in table.values() if value > 0), reverse=True)
    root, version, _, _ = GOLD_DOCS[doc]
    secondary = JsonArtifactStore(Path(root)).load_graph(doc, version)
    rows = []
    for level in levels:
        threshold = positive[max(0, min(len(positive) - 1, int(round(level * len(positive))) - 1))] if level < 1 else 1e-12
        edges, stats, _ = assemble(doc, lambda p, x, y: table.get((p, x, y)), threshold, allow_soft=False, secondary=secondary,
                                   words="--tach-tu" in sys.argv)
        payload, _ = replay(doc, edges, secondary=secondary)
        result = summary(score_payload(doc, payload, "tmp/pass-phu-ml/quet", f"{run}-{level}"), payload, len(edges))
        rows.append({"muc": level, "nguong": threshold, **result})
        print(json.dumps({"doc": doc, "luot": run, "muc_giu": level, **{k: result[k] for k in (
            "canh_pass_phu", "canh_cung_A10", "Q7", "Q7b", "bao_dong_P", "bao_dong_R", "truc_tiep_P", "truc_tiep_R")}}, ensure_ascii=False),
              flush=True)
    out = Path("tmp/pass-phu-ml/quet") / f"{doc}-{run}.json"
    out.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
