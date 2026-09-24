"""Gộp hai bản chấm mù trên từng cạnh dư: đồng thuận mức thô, kappa, khoảng Wilson, và giờ làm người chấm ghi.

Mức thô theo chiều của máy: `dung_chieu` (trực tiếp hoặc gián tiếp), `nguoc`, `khong_can`, `khong_chac`.
Chạy từ gốc repo:
    .venv/Scripts/python.exe scripts/cham-mu/phan_tich_hai_nguoi.py doc-1 <bản A1> <bản A2>
"""
import json
import math
import sys
from collections import Counter
from pathlib import Path

import openpyxl

sys.path.insert(0, "scripts/cham-mu")
from cham_bang import answers_of  # noqa: E402


def coarse(item, answer):
    if answer is None or answer == "khong_chac":
        return "khong_chac"
    if answer == "khong_can_thu_tu":
        return "khong_can"
    first = item["x"] if answer.startswith("x_truoc_y") else item["y"]
    return "dung_chieu" if first == item["machine"][0] else "nguoc"


def wilson(k, n, z=1.96):
    if not n:
        return (float("nan"), float("nan"))
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - half, centre + half


def kappa(pairs):
    n = len(pairs)
    observed = sum(a == b for a, b in pairs) / n
    left, right = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    expected = sum(left[c] * right[c] for c in set(left) | set(right)) / (n * n)
    return (observed - expected) / (1 - expected) if expected < 1 else float("nan")


def note(path):
    row = next(openpyxl.load_workbook(path, read_only=True)["Cặp"].iter_rows(min_row=2, max_row=2, values_only=True))
    return row[-1]


def main(doc, first_path, second_path):
    key = json.loads(Path(f"artifacts/a8-gold/cham-mu-{doc}-khoa.json").read_text(encoding="utf-8"))
    first, second = (answers_of(p, key["labels"]) for p in (first_path, second_path))
    fp = [item for item in key["items"] if item["category"] == "fp"]
    pairs = [(coarse(i, first.get(i["item"])), coarse(i, second.get(i["item"]))) for i in fp]
    judged = [(a, b) for a, b in pairs if "khong_chac" not in (a, b)]
    print(f"=== {doc}: {len(fp)} cạnh dư, cả hai phán được {len(judged)}")
    print(f"  đồng thuận mức thô {sum(a == b for a, b in judged)}/{len(judged)}, kappa {kappa(judged):+.2f}")
    print(f"  bảng chéo (A1, A2): {dict(sorted(Counter(judged).items()))}")
    for label, test in (("cả hai: đúng chiều", lambda a, b: a == b == "dung_chieu"),
                        ("ít nhất một: ngược", lambda a, b: "nguoc" in (a, b)),
                        ("cả hai: ngược", lambda a, b: a == b == "nguoc"),
                        ("ít nhất một: không cần thứ tự", lambda a, b: "khong_can" in (a, b))):
        k = sum(test(a, b) for a, b in judged)
        low, high = wilson(k, len(judged))
        print(f"  {label}: {k}/{len(judged)} = {k / len(judged):.0%} (Wilson 95% {low:.0%}–{high:.0%})")
    graph = json.loads(Path(key["inputs"]["graph"]["path"]).read_text(encoding="utf-8"))
    concepts = {n["node_id"]: n["name"] for n in graph["nodes"]}
    for item, (a, b) in zip(fp, pairs):
        if "nguoc" in (a, b):
            source, target = item["machine"]
            print(f"    ngược: {concepts.get(source, source)} → {concepts.get(target, target)}  (A1 {a}, A2 {b})")
    # Cặp ngẫu nhiên người chấm thấy có thứ tự: nằm sẵn trong bao đóng vàng cùng chiều thì không phải vàng bỏ sót.
    gold = json.loads(Path(key["inputs"]["gold"]["path"]).read_text(encoding="utf-8"))
    children = {}
    for edge in gold["edges"]:
        children.setdefault(edge["prerequisite"], set()).add(edge["target"])

    def reaches(a, b):
        stack, seen = [a], {a}
        while stack:
            for c in children.get(stack.pop(), ()):
                if c == b:
                    return True
                if c not in seen:
                    seen.add(c)
                    stack.append(c)
        return False

    for tag, answers in (("A1", first), ("A2", second)):
        ordered = []
        for item in key["items"]:
            answer = answers.get(item["item"])
            if item["category"] != "random" or answer in (None, "khong_chac", "khong_can_thu_tu"):
                continue
            head, tail = (item["x"], item["y"]) if answer.startswith("x_truoc_y") else (item["y"], item["x"])
            ordered.append(reaches(head, tail))
        judged_random = sum(1 for i in key["items"] if i["category"] == "random"
                            and answers.get(i["item"]) not in (None, "khong_chac"))
        print(f"  cặp ngẫu nhiên {tag}: có thứ tự {len(ordered)}/{judged_random}, trong đó đã có trong bao đóng vàng "
              f"{sum(ordered)} → vàng bỏ sót thật {len(ordered) - sum(ordered)}/{judged_random}")
    print(f"  ghi chú dòng đầu — A1: {note(first_path)!r} | A2: {note(second_path)!r}")


if __name__ == "__main__":
    main(*sys.argv[1:4])
