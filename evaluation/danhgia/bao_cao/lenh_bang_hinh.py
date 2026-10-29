"""Lệnh con `bang-hinh` của `python -m danhgia`: dòng số đếm của mọi hệ và mọi cuốn -> Bảng 9–12, Hình 3–4 và `so-lieu.json` (vé DG-17).

  --dong DONG... (JSON/JSONL dòng `{he, ma_sach, chuong, thuoc, kieu}`, hay tệp `cham --ra` có `theo_chuong`)
  --manifest MANIFEST... (mỗi cuốn một tệp: `ma_sach`, `chu_de`, `tap`)
  [--hop-dong MA_SACH=HOP_DONG]... (khối `chi_phi`: phút và USD)   [--dong-thuan MA_SACH=DEM_G4.json]... (trần người)
  [--quy-loi QUY_LOI.json]... (`quy-loi --ra`, có `meta`: Hình 4)   [--nhieu DONG.json]... (mỗi tệp một lượt nhiễu của hệ chính)
  [--g5 ket-qua-g5.json] [--he-b5 b5a|b5b] [--he-hinh-4 chinh] [--so-vong 10000] [--seed 20261114] --ra DIR

Màn hình chỉ in khoá trong allowlist với giá trị số, bool hay null (`bao_cao.cong`), kể cả khi mọi manifest là tập phát triển.
"""
import json
from pathlib import Path

from danhgia.bao_cao import bang, cong, so_lieu as S
from danhgia.bao_cao import thuoc as T

ALLOWLIST = ("tap_thu", "so_cuon", "so_dong", "so_o", "so_bang", "so_hinh", "p_holm_q6_chinh_so_b1", "p_holm_f1_chinh_so_b5",
             "p_holm_bang_chung_chinh_so_b5")


def doc_json(duong):
    t = Path(duong).read_text(encoding="utf-8-sig")
    return [json.loads(x) for x in t.splitlines() if x.strip()] if str(duong).endswith(".jsonl") else json.loads(t)


def doc_dong(duong):
    """(dòng, meta hoặc None). Tệp là mảng dòng, hay dict có `theo_chuong` (và có thể có `meta`)."""
    d = doc_json(duong)
    if isinstance(d, dict):
        return d["theo_chuong"], d.get("meta")
    return d, None


def _cap(muc):
    ten, _, duong = muc.partition("=")
    if not duong:
        raise SystemExit("cần dạng <mã sách>=<tệp>")
    return ten, duong


def dung_so_lieu(a):
    rows = []
    for duong in a.dong:
        rows += doc_dong(duong)[0]
    meta_theo_sach = {}
    for duong in a.quy_loi or ():
        r, meta = doc_dong(duong)
        rows += r
        if meta is not None and r:
            for ma_sach in {x["ma_sach"] for x in r}:
                meta_theo_sach[ma_sach] = meta
    hop_dong = [(ma, doc_json(d)) for ma, d in map(_cap, a.hop_dong or ())]
    rows += S.dong_chi_phi(hop_dong)
    rows += S.dong_tran_nguoi({ma: doc_json(d) for ma, d in map(_cap, a.dong_thuan or ())})
    he_b5, doi = S.chuan_he_b5(rows, a.he_b5)
    rows = S.doi_ten_he(rows, doi)
    tinh = S.Tinh(rows, so_vong=a.so_vong, seed=a.seed)
    nhieu = []
    for duong in a.nhieu or ():
        r = [{**x, "he": "chinh"} for x in doc_dong(duong)[0]]
        nhieu.append(S.Tinh(r, so_vong=a.so_vong, seed=a.seed))
    g5 = S.g5_tong(doc_json(a.g5), doi) if a.g5 else None
    return rows, tinh, nhieu, g5, meta_theo_sach, doi


def _chay(a):
    manifests = [doc_json(m) for m in a.manifest]
    tap_thu = any(m.get("tap") == "thu" for m in manifests)
    rows, tinh, nhieu, g5, meta_theo_sach, doi = dung_so_lieu(a)
    boi = bang.Boi(tinh, nhieu=nhieu, g5=g5, doi_he=doi)
    ra = Path(a.ra)
    ra.mkdir(parents=True, exist_ok=True)
    cac_bang = bang.tao_bang(boi)
    for ten, text in cac_bang.items():
        (ra / ten).write_text(text, encoding="utf-8")
    o, hieu = tinh.tat_ca()
    so_lieu = {"so_cuon": boi.n, "sach": tinh.sach, "so_vong": a.so_vong, "seed": a.seed, "o": o, "hieu": hieu, "kiem_dinh": boi.kd, "dai_nhieu": boi.dai,
               "g5": g5}
    (ra / "so-lieu.json").write_text(json.dumps(so_lieu, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    cong.in_allowlist({"tap_thu": tap_thu, "so_cuon": boi.n, "so_dong": len(rows), "so_o": len(o), "so_bang": len(cac_bang), "so_hinh": 0,
                       **{f"p_holm_{k}": v["p_holm"] for k, v in boi.kd.items()}}, ALLOWLIST)
    return 0


def them_lenh(parser):
    parser.add_argument("--dong", nargs="+", required=True)
    parser.add_argument("--manifest", nargs="+", required=True)
    parser.add_argument("--hop-dong", action="append", metavar="MA_SACH=TEP")
    parser.add_argument("--dong-thuan", action="append", metavar="MA_SACH=TEP")
    parser.add_argument("--quy-loi", nargs="+")
    parser.add_argument("--nhieu", nargs="+")
    parser.add_argument("--g5")
    parser.add_argument("--he-b5", choices=T.HE_B5_CO_THE)
    parser.add_argument("--he-hinh-4", default="chinh")
    parser.add_argument("--so-vong", type=int, default=S.SO_VONG)
    parser.add_argument("--seed", type=int, default=S.SEED)
    parser.add_argument("--ra", required=True)
    parser.set_defaults(chay=_chay)
