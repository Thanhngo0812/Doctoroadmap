"""Chấm bảng chấm mù đã điền.

Chạy từ gốc repo:
    .venv/Scripts/python.exe scripts/cham-mu/cham_bang.py doc-1 artifacts/a8-gold/cham-mu-doc-1-A1.xlsx [bản của A2 ...]
"""
import json
import sys
from pathlib import Path

import openpyxl

sys.path.insert(0, "src")
from doc2roadmap.domain.gold_scoring import blind_review_counts  # noqa: E402


def answers_of(path, labels):
    code_of = {label: code for code, label in labels.items()}
    rows = list(openpyxl.load_workbook(path, read_only=True)["Cặp"].iter_rows(values_only=True))[1:]
    answers = {}
    for row in rows:
        if row and row[0] is not None and row[5]:
            if row[5] not in code_of:
                raise ValueError(f"{path}: cặp {row[0]} có phán quyết {row[5]!r} không thuộc danh sách")
            answers[int(row[0])] = code_of[row[5]]
    return answers


def rate(part, whole):
    return f"{part}/{whole} ({part / whole:.0%})" if whole else "—"


def main(doc, paths):
    key = json.loads(Path(f"artifacts/a8-gold/cham-mu-{doc}-khoa.json").read_text(encoding="utf-8"))
    per_annotator = {}
    for path in paths:
        answers = answers_of(path, key["labels"])
        per_annotator[path] = answers
        counts = blind_review_counts(key["items"], answers)
        fp, tp, rnd = counts["fp"], counts["tp"], counts["random"]
        judged_fp = sum(fp[k] for k in ("agree_direct", "agree_indirect", "reversed", "none"))
        judged_tp = sum(tp[k] for k in ("agree_direct", "agree_indirect", "reversed", "none"))
        judged_rnd = rnd["ordered"] + rnd["none"]
        print(f"=== {doc} · {path}")
        print(f"  cạnh dư ({key['counts']['fp']}): đúng chiều trực tiếp {rate(fp['agree_direct'], judged_fp)}, "
              f"đúng chiều gián tiếp {rate(fp['agree_indirect'], judged_fp)}, NGƯỢC {rate(fp['reversed'], judged_fp)}, "
              f"không cần thứ tự {rate(fp['none'], judged_fp)} | không chắc {fp['unsure']}, bỏ trống {fp['unanswered']}")
        print(f"  cạnh đúng lấy mẫu ({key['counts']['tp_sampled']}): người gán xác nhận lại {rate(tp['agree_direct'] + tp['agree_indirect'], judged_tp)} "
              f"— độ tin của chính lần chấm này")
        print(f"  cặp ngẫu nhiên ({key['counts']['random']}): thấy có thứ tự {rate(rnd['ordered'], judged_rnd)} — gồm cả cặp đã nằm trong bao đóng vàng; "
              f"số vàng bỏ sót thật xem phan_tich_hai_nguoi.py")
        predicted = key["counts"]["predicted_in_scope"]
        tp_total = key["counts"]["tp_total"]
        if judged_fp:
            direct = tp_total + key["counts"]["fp"] * fp["agree_direct"] / judged_fp
            harmless = tp_total + key["counts"]["fp"] * (fp["agree_direct"] + fp["agree_indirect"]) / judged_fp
            print(f"  precision so vàng: {tp_total / predicted:.3f} | ước lượng theo chấm mù — cạnh trực tiếp đúng: "
                  f"{direct / predicted:.3f}; không làm sai thứ tự học: {harmless / predicted:.3f}")
    if len(per_annotator) == 2:
        first, second = per_annotator.values()
        both = sorted(set(first) & set(second))
        same = sum(first[item] == second[item] for item in both)
        print(f"  hai người trùng phán quyết: {rate(same, len(both))}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
