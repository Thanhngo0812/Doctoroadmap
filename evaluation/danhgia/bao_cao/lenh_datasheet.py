"""Lệnh con `datasheet` của `python -m danhgia`: khung datasheet cho bộ vàng (Gebru và cộng sự 2021; mục D của danh mục ACL), vé DG-17.

  --manifest MANIFEST... --g3 MA=KHO_G3.json... --g4 MA=VANG_G4.json... [--dong-thuan-g3 MA=DEM.json]... [--dong-thuan-g4 MA=DEM_G4.json]... --ra datasheet.md

Phần chỉ số điền tự động; phần người gán ẩn danh S1..S16, giới hạn và khai việc dùng AI chừa chỗ `[ĐIỀN TAY]`. Màn hình chỉ in khoá allowlist với giá trị số.
"""
import json
from pathlib import Path

from danhgia.bao_cao import cong, datasheet

ALLOWLIST = ("tap_thu", "so_cuon", "so_trang", "so_chuong_boc", "so_khai_niem", "so_canh_vang_chinh", "so_tranh_chap")


def _cap(muc):
    ma, _, duong = muc.partition("=")
    if not duong:
        raise SystemExit("cần dạng <mã sách>=<tệp>")
    return ma, duong


def _doc(p):
    return json.loads(Path(p).read_text(encoding="utf-8-sig"))


def _chay(a):
    manifests = [_doc(m) for m in a.manifest]
    g3, g4 = dict(map(_cap, a.g3 or ())), dict(map(_cap, a.g4 or ()))
    ma_co = {m["ma_sach"] for m in manifests}
    for ma in (*g3, *g4, *(dict(map(_cap, a.dong_thuan_g3 or ()))), *(dict(map(_cap, a.dong_thuan_g4 or ())))):
        if ma not in ma_co:
            raise SystemExit("mã sách không có trong manifest")
    hash_vang = {ma: {"g3": datasheet.sha256_tep(g3[ma]) if ma in g3 else None, "g4": datasheet.sha256_tep(g4[ma]) if ma in g4 else None} for ma in ma_co}
    sl = datasheet.dung_so_lieu(manifests, {ma: _doc(p) for ma, p in g3.items()}, {ma: _doc(p) for ma, p in g4.items()},
                                {ma: _doc(p) for ma, p in map(_cap, a.dong_thuan_g3 or ())}, {ma: _doc(p) for ma, p in map(_cap, a.dong_thuan_g4 or ())}, hash_vang)
    Path(a.ra).parent.mkdir(parents=True, exist_ok=True)
    Path(a.ra).write_text(datasheet.dung_md(sl), encoding="utf-8")
    t = sl["tong"]
    cong.in_allowlist({"tap_thu": any(m.get("tap") == "thu" for m in manifests), "so_cuon": t["so_cuon"], "so_trang": t["so_trang"],
                       "so_chuong_boc": t["so_chuong_boc"], "so_khai_niem": t["so_khai_niem"], "so_canh_vang_chinh": t["so_canh_vang_chinh"],
                       "so_tranh_chap": t["so_khai_niem_tranh_chap"]}, ALLOWLIST)
    return 0


def them_lenh(parser):
    parser.add_argument("--manifest", nargs="+", required=True)
    parser.add_argument("--g3", nargs="*", metavar="MA=TEP")
    parser.add_argument("--g4", nargs="*", metavar="MA=TEP")
    parser.add_argument("--dong-thuan-g3", nargs="*", metavar="MA=TEP")
    parser.add_argument("--dong-thuan-g4", nargs="*", metavar="MA=TEP")
    parser.add_argument("--ra", required=True)
    parser.set_defaults(chay=_chay)
