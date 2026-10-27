"""Lệnh con `thuoc-khai-niem` của `python -m danhgia`: A3, A4, A5, truy nguyên cho một hệ trên một cuốn.

  --hop-dong HD --g3 G3 --g4 G4 --can CAN (bảng căn một hệ: dùng `can-khai-niem tach`) --anh-xa ANH_XA.json
  (--pdf PDF | --van-ban VB.json) [--ra BANG.json] [--ca-truot CA.json]

In bảng thước theo cuốn (mức nghiêm và nới). `--ca-truot` ghi mọi câu neo hay câu bằng chứng khớp dưới ngưỡng nghiêm để người đọc xem.
"""
import json
from pathlib import Path

from danhgia.cham import dong, khai_niem


def _doc(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _van_ban(a):
    if a.van_ban:
        return {int(k): v for k, v in _doc(a.van_ban).items()}
    from danhgia.phieu.trang import doc_trang
    import pypdfium2

    so_trang = len(pypdfium2.PdfDocument(Path(a.pdf).read_bytes()))
    lay = doc_trang(a.pdf)
    return {t: lay(t) for t in range(1, so_trang + 1)}


def _chay(a):
    hd, g3, g4, can = _doc(a.hop_dong), _doc(a.g3), _doc(a.g4), _doc(a.can)
    anh_xa = khai_niem.doc_anh_xa(a.anh_xa)
    van_ban = _van_ban(a)
    nguong = anh_xa.get("nguong_truy_nguyen")
    rows = khai_niem.cham_khai_niem(hd, g3, g4, can, van_ban, anh_xa, nguong_truy_nguyen=nguong)
    cuon = dong.gop_cuon([r for r in rows if not r["thuoc"].startswith("a5.nham.")])
    for r in cuon:
        gia = dong.gia_tri(r)
        print(f"{r['thuoc']:<46} {'—' if gia is None else format(gia, '.4f')}")
    if a.ra:
        Path(a.ra).write_text(json.dumps({"theo_chuong": rows, "theo_cuon": dong.gop_cuon(rows)}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    ca = khai_niem.ca_truot(hd, van_ban, nguong=(nguong or khai_niem.NGUONG_TRUY_NGUYEN)["nghiem"])
    print(f"ca bằng chứng khớp dưới ngưỡng nghiêm: {len(ca)}")
    if a.ca_truot:
        Path(a.ca_truot).write_text(json.dumps(ca, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


def them_lenh(parser):
    for ten in ("--hop-dong", "--g3", "--g4", "--can", "--anh-xa"):
        parser.add_argument(ten, required=True)
    nguon = parser.add_mutually_exclusive_group(required=True)
    nguon.add_argument("--pdf")
    nguon.add_argument("--van-ban", help="JSON {trang: chữ}")
    parser.add_argument("--ra")
    parser.add_argument("--ca-truot")
    parser.set_defaults(chay=_chay)
