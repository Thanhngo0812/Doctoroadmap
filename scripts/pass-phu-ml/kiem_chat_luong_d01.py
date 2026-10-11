"""Chấm chất lượng một lượt nhãn D-01 (Claude chạy; cần khoa.jsonl, không giao script này cho agentic).

In theo nhóm người gán và theo khối phiếu: phân bố nhãn trong/ngoài cửa sổ, độ đa dạng lý do, chỉ báo "trích câu định nghĩa X";
độ đúng trên phiếu kiểm; độ tự nhất quán trên phiếu lặp; đồng thuận với một tệp nhãn khác (tuỳ chọn, ví dụ nhãn cũ trước khi gán lại).

Chạy:  python kiem_chat_luong_d01.py --phieu tmp/d01-phieu/phieu.jsonl --khoa tmp/d01-phieu/khoa.jsonl --nhan tmp/d01-gan-nhan/nhan-A-gop.jsonl
       [--so-voi tmp/d01-gan-nhan/nhan-A.jsonl] [--khoi 600]
"""
import argparse
import collections
import json
import sys


def read_jsonl(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return rows


def kappa(pairs):
    n = len(pairs)
    if not n:
        return float("nan"), float("nan")
    po = sum(a == b for a, b in pairs) / n
    left, right = collections.Counter(a for a, _ in pairs), collections.Counter(b for _, b in pairs)
    pe = sum(left[k] * right[k] for k in left) / n / n
    return po, (po - pe) / (1 - pe) if pe < 1 else float("nan")


def norm(text):
    return " ".join((text or "").split()).lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phieu", required=True)
    ap.add_argument("--khoa", required=True)
    ap.add_argument("--nhan", required=True)
    ap.add_argument("--so-voi")
    ap.add_argument("--khoi", type=int, default=600)
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    sheets, order = {}, {}
    for i, s in enumerate(read_jsonl(args.phieu), 1):
        sheets[s["phieu_id"]], order[s["phieu_id"]] = s, i
    key = {k["phieu_id"]: k for k in read_jsonl(args.khoa)}
    labels = {(r["phieu_id"], r["x_id"]): r for r in read_jsonl(args.nhan)}
    cand = {(pid, u["x_id"]): u for pid, s in sheets.items() for u in s["ung_vien"]}

    def cites_x_definition(r):
        if r["nhan"] != "can_de_hieu" or r["cau"] is None:
            return None
        s, u = sheets[r["phieu_id"]], cand[(r["phieu_id"], r["x_id"])]
        cited = norm(next((c["text"] for c in s["cau"] if c["i"] == r["cau"]), ""))
        xd = norm(u["x_dinh_nghia"])
        same = bool(xd) and (cited == xd or (len(cited) > 30 and (cited in xd or xd in cited)))
        return same and r["cau"] != s["cau_neo"]

    def profile(rows):
        inside = [r for r in rows if cand[(r["phieu_id"], r["x_id"])]["trong_cua_so"]]
        c = collections.Counter(r["nhan"] for r in inside)
        flags = [x for x in map(cites_x_definition, rows) if x is not None]
        reasons = collections.Counter(norm(r["ly_do"]) for r in rows)
        return {"cap": len(rows), "trong_cua_so": len(inside),
                **{k: f"{100 * c[k] / max(len(inside), 1):.0f}%" for k in ("can_de_hieu", "cong_cu", "khong", "khop_nham", "nguoc")},
                "chi_bao_dn_X": f"{100 * sum(flags) / max(len(flags), 1):.1f}%",
                "ly_do_khac_nhau": f"{100 * len(reasons) / max(len(rows), 1):.0f}%",
                "ly_do_lap_nhieu_nhat": reasons.most_common(1)[0][1] if reasons else 0}

    print("== theo người gán")
    groups = collections.defaultdict(list)
    for r in labels.values():
        groups[r["nguoi_gan"]].append(r)
    for name, rows in sorted(groups.items(), key=lambda kv: -len(kv[1])):
        print(f"  {name[:60]:60s}", json.dumps(profile(rows), ensure_ascii=False))
    print(f"== theo khối {args.khoi} phiếu (thứ tự trong tệp phiếu)")
    blocks = collections.defaultdict(list)
    for r in labels.values():
        blocks[(order[r["phieu_id"]] - 1) // args.khoi].append(r)
    for b in sorted(blocks):
        print(f"  {b * args.khoi + 1:5d}–{(b + 1) * args.khoi:5d}", json.dumps(profile(blocks[b]), ensure_ascii=False))

    print("== phiếu kiểm (vàng: co_quan_he = cạnh vàng; khong = hai đầu là đích vàng, ngoài bao đóng)")
    confusion = collections.Counter()
    for pid, k in key.items():
        if k["loai"] != "kiem":
            continue
        for x, gold in k["dap_an"].items():
            r = labels.get((pid, x))
            if r:
                confusion[(gold, r["nhan"], cand[(pid, x)]["trong_cua_so"])] += 1
    for k_, v in sorted(confusion.items(), key=str):
        print("  ", k_, v)
    tp = sum(v for (g, n, _), v in confusion.items() if g == "co_quan_he" and n == "can_de_hieu")
    fp = sum(v for (g, n, _), v in confusion.items() if g == "khong" and n == "can_de_hieu")
    fn = sum(v for (g, n, _), v in confusion.items() if g == "co_quan_he" and n != "can_de_hieu")
    tn = sum(confusion.values()) - tp - fp - fn
    print(f"  cạnh cứng: TP {tp} FP {fp} FN {fn} TN {tn} | P {tp / max(tp + fp, 1):.2f} R {tp / max(tp + fn, 1):.2f}"
          f" | khớp {(tp + tn) / max(sum(confusion.values()), 1):.2f} trên {sum(confusion.values())} cặp")

    print("== phiếu lặp (cùng phiếu, thứ tự ứng viên khác)")
    pairs = []
    for pid, k in key.items():
        if k["loai"] == "lap":
            for u in sheets[pid]["ung_vien"]:
                a, b = labels.get((k["lap_cua"], u["x_id"])), labels.get((pid, u["x_id"]))
                if a and b:
                    pairs.append((a["nhan"], b["nhan"]))
    po, kp = kappa(pairs)
    po_h, kp_h = kappa([(a == "can_de_hieu", b == "can_de_hieu") for a, b in pairs])
    print(f"  {len(pairs)} cặp: năm nhãn khớp {po:.2f} kappa {kp:.2f} | cạnh cứng khớp {po_h:.2f} kappa {kp_h:.2f}")

    if args.so_voi:
        other = {(r["phieu_id"], r["x_id"]): r for r in read_jsonl(args.so_voi)}
        common = [k_ for k_ in other if k_ in labels and other[k_].get("luot") == labels[k_].get("luot")]
        pairs = [(other[k_]["nhan"], labels[k_]["nhan"]) for k_ in common]
        po, kp = kappa(pairs)
        po_h, kp_h = kappa([(a == "can_de_hieu", b == "can_de_hieu") for a, b in pairs])
        po_c, kp_c = kappa([(a == "cong_cu", b == "cong_cu") for a, b in pairs])
        print(f"== so với {args.so_voi}: {len(pairs)} cặp chung | năm nhãn khớp {po:.2f} kappa {kp:.2f} | cạnh cứng kappa {kp_h:.2f}"
              f" | cong_cu kappa {kp_c:.2f}")


if __name__ == "__main__":
    main()
