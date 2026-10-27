"""Lệnh con `cham-a1a2` của `python -m danhgia`: A1 (M1, M2, M3, complete entry) và A2 (vai trò vùng, lỗi có hại).

  --vang VANG.json     tiêu đề G1/G2 (JSON mảng, hoặc `cay-muc/<sách>.jsonl`)
  --du-doan DD.json    dự đoán của hệ: {headings: [...], lines?, evaluation_excluded?}; hoặc --hop-dong HD.json (định vị tiêu đề bằng chữ và trang)
  --dong DONG.json     bảng dòng (JSON mảng, hoặc `dong/<sách>.jsonl`)
  --he HE --ma-sach MA [--chuong MANIFEST.json] [--trang-mau TM.jsonl] [--g3 G3.json] [--ra BANG.json]
"""
import json
from pathlib import Path

from danhgia.cham import a1a2, dong


def _doc(p):
    t = Path(p).read_text(encoding="utf-8-sig")
    return [json.loads(x) for x in t.splitlines() if x.strip()] if str(p).endswith(".jsonl") else json.loads(t)


def _chay(a):
    bang_dong = _doc(a.dong)
    if a.hop_dong:
        du_doan = a1a2.du_doan_tu_hop_dong(_doc(a.hop_dong), bang_dong)
        if du_doan["khong_dinh_vi"]:
            print(f"cảnh báo: {len(du_doan['khong_dinh_vi'])} tiêu đề của hệ không định vị được trên bảng dòng (tính là thừa ở M1)")
    else:
        du_doan = _doc(a.du_doan)
    chuong = _doc(a.chuong)["chuong"] if a.chuong else None
    g3 = _doc(a.g3)["khai_niem"] if a.g3 else None
    rows = a1a2.cham(_doc(a.vang), du_doan, bang_dong, he=a.he, ma_sach=a.ma_sach, chuong=chuong,
                     trang_mau=_doc(a.trang_mau) if a.trang_mau else None, g3_khai_niem=g3)
    cuon = dong.gop_cuon(rows)
    for r in cuon:
        if r["thuoc"].startswith("a2.nham."):
            continue
        gia = dong.gia_tri(r)
        print(f"{r['thuoc']:<36} {'—' if gia is None else format(gia, '.4f')}")
    macro = a1a2.macro_f1_vai_tro(cuon)
    print(f"{'a2.macro_f1_vai_tro':<36} {'—' if macro['gia_tri'] is None else format(macro['gia_tri'], '.4f')} ({macro['so_vai_tro_co_so']}/{macro['so_vai_tro']} vai trò có mẫu)")
    if a.ra:
        Path(a.ra).write_text(json.dumps({"theo_chuong": rows, "theo_cuon": cuon}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


def them_lenh(parser):
    parser.add_argument("--vang", required=True)
    nguon = parser.add_mutually_exclusive_group(required=True)
    nguon.add_argument("--du-doan")
    nguon.add_argument("--hop-dong")
    parser.add_argument("--dong", required=True)
    parser.add_argument("--he", required=True)
    parser.add_argument("--ma-sach", required=True)
    parser.add_argument("--chuong", help="manifest sách (có `chuong`)")
    parser.add_argument("--trang-mau")
    parser.add_argument("--g3")
    parser.add_argument("--ra")
    parser.set_defaults(chay=_chay)
