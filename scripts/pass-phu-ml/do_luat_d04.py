"""D-04d: đo độ chính xác và độ phủ `can_hoc_truoc` của các luật giữ cứng cạnh ngược (E8) trên nhãn D-04.

Mỗi cặp (X, Y) tính một lần: bỏ phiếu lặp (khoá có `lap_cua`). Nhãn nhị phân "cần học trước":
- `da-so` (chính): A và B cùng ý thì lấy; lệch thì lượt C quyết. Nhãn giữ chỗ của B không tính, khi đó A và C phải cùng ý, không thì `khong_ro`
  và bỏ khỏi phép đo.
- độ nhạy: `A`, `B` từng lượt; `A-giao-B` (cả hai cùng nói cần học trước); `A-hop-B` (một trong hai nói cần học trước).
Luật giữ cứng (đúng định nghĩa E8, thêm khoảng cách): `tat` (giữ cứng mọi cạnh), `cung-chuong`, `pass-chinh`, `tin-chac` (confidence ≥ 0,9),
`cung-chuong-tin-chac`, `so-muc-giua<=k`. Độ chính xác = tỉ lệ cần học trước trong các cạnh luật giữ cứng, kèm khoảng Wilson 95%; độ phủ = tỉ lệ
cạnh cần học trước được luật giữ cứng. Tiêu chí (chốt ở đặc tả D-04 trước khi có nhãn): chính xác ≥ 0,70, cận dưới Wilson ≥ 0,60, phủ ≥ 0,30.
Mô hình học (đặc tả: chỉ khi không luật đơn nào đạt): LightGBM trên đặc trưng cấu trúc, xác suất ngoài mẫu bỏ một sách; báo AP và độ chính xác
tốt nhất ở độ phủ ≥ 0,30. Phụ phẩm: phân bố bảy nhãn của từng lượt theo hệ đề xuất.

Chạy:  python do_luat_d04.py <khoa.jsonl> <phieu.jsonl> <nhan-A> <nhan-B> <nhan-C> <ra.json>
"""
import json
import sys
from collections import Counter
from math import sqrt

PLACEHOLDER_REASONS = {"đoạn Y không cho thấy quan hệ"}
KS = (0, 1, 2, 3, 5, 10)


def wilson(hits, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = hits / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return (centre - half, centre + half)


def rules():
    found = {
        "tat": lambda k: True,
        "cung-chuong": lambda k: k["cung_chuong"],
        "pass-chinh": lambda k: "chinh" in k["pass"],
        "tin-chac": lambda k: (k["confidence"] or 0) >= 0.9,
        "cung-chuong-tin-chac": lambda k: k["cung_chuong"] and (k["confidence"] or 0) >= 0.9,
    }
    for k in KS:
        found[f"so-muc-giua<={k}"] = lambda key, k=k: key["so_muc_giua"] <= k
    return found


def majority(row_a, row_b, row_c):
    """Nhị phân cần học trước theo đa số; None khi không quyết được."""
    votes = [row["nhan"] == "can_hoc_truoc" for row in (row_a, row_b, row_c)
             if row is not None and row["ly_do"] not in PLACEHOLDER_REASONS]
    if len(votes) >= 2 and votes[0] == votes[1]:
        return votes[0]
    if len(votes) == 3:
        return votes[2]
    return None


def label_sets(ids, run_a, run_b, run_c):
    prereq = {name: {pid: row["nhan"] == "can_hoc_truoc" for pid, row in run.items()} for name, run in (("A", run_a), ("B", run_b))}
    for pid, row in run_b.items():
        if row["ly_do"] in PLACEHOLDER_REASONS:
            prereq["B"][pid] = None
    return {
        "da-so": {pid: majority(run_a[pid], run_b[pid], run_c.get(pid)) for pid in ids},
        "A": {pid: prereq["A"][pid] for pid in ids},
        "B": {pid: prereq["B"][pid] for pid in ids},
        "A-giao-B": {pid: prereq["A"][pid] and bool(prereq["B"][pid]) for pid in ids},
        "A-hop-B": {pid: prereq["A"][pid] or bool(prereq["B"][pid]) for pid in ids},
    }


def measure(keys, labels, rule):
    pool = [k for k in keys if labels[k["phieu_id"]] is not None]
    kept = [k for k in pool if rule(k)]
    hits = sum(labels[k["phieu_id"]] for k in kept)
    total = sum(labels[k["phieu_id"]] for k in pool)
    low, high = wilson(hits, len(kept))
    return {"n": len(pool), "giu_cung": len(kept), "dung": hits, "can_hoc_truoc": total,
            "chinh_xac": hits / len(kept) if kept else None, "wilson": [low, high], "do_phu": hits / total if total else None}


def passes(row):
    return (row["chinh_xac"] or 0) >= 0.70 and row["wilson"][0] >= 0.60 and (row["do_phu"] or 0) >= 0.30


def _features(key, card):
    nhan = key["nhan_d01"]
    return [key["so_muc_giua"], key["cung_chuong"], key["nguon"], "chinh" in key["pass"], key["confidence"] or 0.0,
            -1.0 if key["p_e5"] is None else key["p_e5"], nhan == "can_de_hieu", nhan == "khong", nhan is None,
            not card["y"]["cau_co_ten_x"], "llm-v3" in key["he"], any(s.startswith("e5") for s in key["he"])]


def learned(keys, cards, labels, seed=0):
    import lightgbm
    import numpy as np
    from sklearn.metrics import average_precision_score

    pool = [k for k in keys if labels[k["phieu_id"]] is not None]
    x = np.array([_features(k, cards[k["phieu_id"]]) for k in pool], dtype=float)
    y = np.array([labels[k["phieu_id"]] for k in pool], dtype=int)
    docs = np.array([k["doc_id"] for k in pool])
    score = np.zeros(len(pool))
    for doc in sorted(set(docs)):
        test = docs == doc
        model = lightgbm.LGBMClassifier(n_estimators=200, learning_rate=0.05, num_leaves=7, min_child_samples=10,
                                        random_state=seed, verbose=-1)
        model.fit(x[~test], y[~test])
        score[test] = model.predict_proba(x[test])[:, 1]
    order = np.argsort(-score)
    best = None
    hits = 0
    for rank, index in enumerate(order, 1):
        hits += y[index]
        if hits / y.sum() >= 0.30:
            precision = hits / rank
            if best is None or precision > best["chinh_xac"]:
                best = {"giu_cung": rank, "dung": int(hits), "chinh_xac": precision, "wilson": list(wilson(int(hits), rank)),
                        "do_phu": hits / y.sum()}
    return {"n": len(pool), "can_hoc_truoc": int(y.sum()), "ap": float(average_precision_score(y, score)),
            "ti_le_nen": float(y.mean()), "tot_nhat_o_phu_0_30": best}


def _read(path):
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) != 7:
        print(__doc__)
        return 2
    keys_path, cards_path, a_path, b_path, c_path, out_path = sys.argv[1:]
    keys = [k for k in _read(keys_path) if not k["lap_cua"]]
    domain = {card["phieu_id"]: card["linh_vuc"] for card in _read(cards_path)}
    run_a, run_b, run_c = ({row["phieu_id"]: row for row in _read(path)} for path in (a_path, b_path, c_path))
    labels = label_sets([k["phieu_id"] for k in keys], run_a, run_b, run_c)
    groups = {
        "tat-ca": keys,
        "nguon-1": [k for k in keys if k["nguon"] == 1],
        "nguon-2": [k for k in keys if k["nguon"] == 2],
        "nguon-2-e5-de-xuat": [k for k in keys if k["nguon"] == 2 and k["e5_de_xuat"]],
    }
    for system in sorted({s for k in keys for s in k["he"]}):
        groups[f"he-{system}"] = [k for k in keys if system in k["he"]]
    for name in sorted(set(domain.values())):
        groups[f"linh-vuc-{name}"] = [k for k in keys if domain[k["phieu_id"]] == name]
    result = {"so_cap": len(keys), "khong_ro": sum(v is None for v in labels["da-so"].values()), "do": {}}
    for label_name, label in labels.items():
        for group_name, group in groups.items():
            if label_name != "da-so" and not group_name.startswith(("tat-ca", "nguon")):
                continue
            for rule_name, rule in rules().items():
                row = measure(group, label, rule)
                row["dat"] = passes(row)
                result["do"].setdefault(label_name, {}).setdefault(group_name, {})[rule_name] = row
    cards = {card["phieu_id"]: card for card in _read(cards_path)}
    result["mo_hinh"] = {name: learned(keys, cards, labels[name]) for name in ("da-so", "A-hop-B")}
    by_label = Counter()
    for k in keys:
        system = "+".join(sorted(k["he"]))
        for run_name, run in (("A", run_a), ("B", run_b)):
            by_label[(run_name, system, run[k["phieu_id"]]["nhan"])] += 1
    result["phan_bo_nhan"] = {f"{r}|{system}|{lab}": c for (r, system, lab), c in sorted(by_label.items())}
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=1)
    print(f"{result['so_cap']} cặp, khong_ro {result['khong_ro']}")
    for label_name in labels:
        print(f"\n== nhãn {label_name}, nhóm tat-ca")
        for rule_name, row in result["do"][label_name]["tat-ca"].items():
            pr = "—" if row["chinh_xac"] is None else f"{row['chinh_xac']:.3f}"
            ph = "—" if row["do_phu"] is None else f"{row['do_phu']:.3f}"
            print(f"  {rule_name:22} giữ {row['giu_cung']:4} đúng {row['dung']:3} chính xác {pr} [{row['wilson'][0]:.3f}, {row['wilson'][1]:.3f}]"
                  f" phủ {ph} {'ĐẠT' if row['dat'] else ''}")
    for name, row in result["mo_hinh"].items():
        print(f"\n== mô hình học, nhãn {name}: {json.dumps(row, ensure_ascii=False)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
