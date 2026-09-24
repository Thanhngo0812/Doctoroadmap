"""Chấm T11 (cổng 2 của vé 06): Q4 trên cạnh ngầm — ngược ≤ 5% và "không làm sai thứ tự học" ≥ 0,90, từng người.

Chạy từ gốc repo:
    .venv/Scripts/python.exe scripts/cham-mu/cham_bang_v2.py doc-2 <bản A1> [bản A2]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "scripts/cham-mu")
from cham_bang import answers_of  # noqa: E402
from phan_tich_hai_nguoi import wilson  # noqa: E402

from doc2roadmap.domain.gold_scoring import blind_review_counts  # noqa: E402


def main(doc, paths, key_dir="artifacts/a8-gold"):
    key = json.loads(Path(f"{key_dir}/cham-mu-v2-{doc}-khoa.json").read_text(encoding="utf-8"))
    implicit = [item for item in key["items"] if item.get("implicit")]
    extra = [item for item in key["items"] if item["category"] == "tp" and not item.get("implicit")]
    randoms = [item for item in key["items"] if item["category"] == "random"]
    for path in paths:
        answers = answers_of(path, key["labels"])
        # Cạnh ngầm chấm chung một rổ bất kể có trong vàng hay không: cổng hỏi về mọi cạnh mới.
        counts = blind_review_counts([{**item, "category": "fp"} for item in implicit], answers)["fp"]
        judged = sum(counts[k] for k in ("agree_direct", "agree_indirect", "reversed", "none"))
        harmless = counts["agree_direct"] + counts["agree_indirect"]
        calibration = blind_review_counts(extra, answers)["tp"]
        confirmed = calibration["agree_direct"] + calibration["agree_indirect"]
        calibration_judged = confirmed + calibration["reversed"] + calibration["none"]
        ordered = blind_review_counts(randoms, answers)["random"]
        print(f"=== {doc} · {path}: {len(implicit)} cạnh ngầm, phán được {judged}, không chắc {counts['unsure']},"
              f" bỏ trống {counts['unanswered']}")
        if judged:
            for label, k, rule in (("không làm sai thứ tự học", harmless, "≥ 0,90"),
                                   ("ngược chiều", counts["reversed"], "≤ 5%"),
                                   ("không cần thứ tự", counts["none"], "báo kèm"),
                                   ("trực tiếp", counts["agree_direct"], "báo kèm")):
                low, high = wilson(k, judged)
                print(f"  {label}: {k}/{judged} = {k / judged:.0%} (Wilson 95% {low:.0%}–{high:.0%}) — ngưỡng {rule}")
        print(f"  cạnh vàng khác được xác nhận lại: {confirmed}/{calibration_judged} | cặp ngẫu nhiên thấy có thứ tự:"
              f" {ordered['ordered']}/{ordered['ordered'] + ordered['none']}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
