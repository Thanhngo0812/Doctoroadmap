"""`python -m danhgia <lệnh>`: bảng lệnh con. PYTHONPATH gồm `evaluation` và `src`.

Lệnh của vé DG-04 (`xuat`, `kiem`, `chuyen-vang`, `cham`, `doi-chieu`) khai báo trong `_tham_so`. Các vé khác thêm một dòng vào `_LENH`.
"""
from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path

# tên lệnh con -> mô-đun có `them_lenh(parser)`; parser đặt `args.chay` là hàm nhận args và trả mã thoát
_LENH = {
    "phieu-g3": "danhgia.phieu.lenh_g3",
    "phieu-g4": "danhgia.phieu.lenh_g4",
}


def _ghi(duong, gia_tri):
    Path(duong).write_text(json.dumps(gia_tri, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def _doc(duong):
    return json.loads(Path(duong).read_text(encoding="utf-8"))


def lenh_xuat(args):
    from danhgia.xuat import xuat
    dinh_danh = {"he": args.he, "bien_the": args.bien_the, "luot_nhieu": args.luot_nhieu, "commit": args.commit,
                 "ngay_chay": args.ngay_chay, "transport": args.transport, "sha256_pdf": args.sha256_pdf,
                 "so_trang": args.so_trang}
    hd = xuat(args.kho, args.doc, args.phien_ban, dinh_danh=dinh_danh, kho_pha_b=args.kho_pha_b)
    _ghi(args.ra, hd)
    print(f"đã ghi {args.ra}: {len(hd['khai_niem'])} khái niệm, {len(hd['canh'])} cạnh")


def lenh_kiem(args):
    from danhgia.hop_dong import kiem
    loi = kiem(_doc(args.hop_dong))
    for dong in loi:
        print(dong)
    print("hợp lệ" if not loi else f"{len(loi)} lỗi")
    return 1 if loi else 0


def lenh_chuyen_vang(args):
    from danhgia.vang.cu import chuyen
    from danhgia.xuat.chuyen_huong import doc_chuyen_huong
    hd = _doc(args.hop_dong)
    _, chuyen_huong = doc_chuyen_huong(args.kho, args.doc, args.phien_ban)
    ket_qua = chuyen(_doc(args.vang_cu), ma_sach=args.ma_sach or args.doc,
                     ten={k["ma"]: k["ten"] for k in hd["khai_niem"]},
                     node_ids={k["ma"] for k in hd["khai_niem"]}, redirects=chuyen_huong, danh_tinh=hd["ban_do_danh_tinh"],
                     cho_phep_chua_can=args.cho_phep_chua_can)
    ra = Path(args.ra)
    ra.mkdir(parents=True, exist_ok=True)
    for ten in ("g3", "g4", "can"):
        _ghi(ra / f"{ten}.json", ket_qua[ten])
    print(json.dumps(ket_qua["bao_cao"], ensure_ascii=False))


def lenh_cham(args):
    from danhgia.cham import dong
    from danhgia.cham.bang import cham
    rows = cham(_doc(args.hop_dong), _doc(args.g3), _doc(args.g4), _doc(args.can), ho_so=args.ho_so, mem=args.mem)
    cuon = dong.gop_cuon(rows)
    if args.ra:
        _ghi(args.ra, {"theo_chuong": rows, "theo_cuon": cuon})
    for row in cuon:
        gia = dong.gia_tri(row)
        print(f"{row['thuoc']:<28} {'—' if gia is None else format(gia, '.4f')}")


def lenh_doi_chieu(args):
    from danhgia.doi_chieu import doi_chieu, in_bang
    ket_qua = doi_chieu(args.kho, args.doc, args.phien_ban, args.vang)
    print(in_bang(ket_qua, f"{args.doc} v{args.phien_ban}"))
    print(json.dumps(ket_qua["ghi_chu"], ensure_ascii=False))
    return 1 if ket_qua["lech"] else 0


def _tham_so():
    goc = argparse.ArgumentParser(prog="python -m danhgia")
    lenh = goc.add_subparsers(dest="lenh", required=True)

    xuat = lenh.add_parser("xuat", help="kho artifact -> hợp đồng danh-gia-xuat-1")
    xuat.add_argument("--kho", required=True)
    xuat.add_argument("--doc", required=True)
    xuat.add_argument("--phien-ban", type=int, required=True)
    xuat.add_argument("--he", required=True)
    xuat.add_argument("--bien-the", required=True)
    xuat.add_argument("--luot-nhieu", type=int, required=True)
    xuat.add_argument("--commit", required=True)
    xuat.add_argument("--ngay-chay", required=True)
    xuat.add_argument("--transport", required=True)
    xuat.add_argument("--sha256-pdf", default=None)
    xuat.add_argument("--so-trang", type=int, default=None)
    xuat.add_argument("--kho-pha-b", default=None, help="tệp JSON kho Pha B riêng của lượt chạy")
    xuat.add_argument("--ra", required=True)
    xuat.set_defaults(chay=lenh_xuat)

    kiem = lenh.add_parser("kiem", help="kiểm hợp đồng")
    kiem.add_argument("hop_dong")
    kiem.set_defaults(chay=lenh_kiem)

    chuyen = lenh.add_parser("chuyen-vang", help="vàng A8 cũ -> G3, G4, bảng căn")
    chuyen.add_argument("--kho", required=True)
    chuyen.add_argument("--doc", required=True)
    chuyen.add_argument("--phien-ban", type=int, required=True)
    chuyen.add_argument("--hop-dong", required=True)
    chuyen.add_argument("--vang-cu", required=True)
    chuyen.add_argument("--ma-sach", default=None)
    chuyen.add_argument("--cho-phep-chua-can", action="store_true",
                        help="chuyển phần quy được thay vì từ chối khi có id vàng không quy được")
    chuyen.add_argument("--ra", required=True, help="thư mục ghi g3.json, g4.json, can.json")
    chuyen.set_defaults(chay=lenh_chuyen_vang)

    cham = lenh.add_parser("cham", help="hợp đồng + G3 + G4 + bảng căn -> bảng số đếm")
    cham.add_argument("--hop-dong", required=True)
    cham.add_argument("--g3", required=True)
    cham.add_argument("--g4", required=True)
    cham.add_argument("--can", required=True)
    cham.add_argument("--ho-so", choices=("spec", "giu_lai_v3"), default="spec",
                      help="spec = số báo cáo (mặc định); giu_lai_v3 = hồ sơ lịch sử, chỉ để so với số v3 và T-01 đã báo")
    cham.add_argument("--mem", choices=("cung", "ca_hai"), default="cung")
    cham.add_argument("--ra", default=None)
    cham.set_defaults(chay=lenh_cham)

    doi = lenh.add_parser("doi-chieu", help="bộ chấm mới so với bộ chấm cũ trên cùng graph và vàng")
    doi.add_argument("--kho", required=True)
    doi.add_argument("--doc", required=True)
    doi.add_argument("--phien-ban", type=int, required=True)
    doi.add_argument("--vang", required=True, help="tệp vàng A8 cũ")
    doi.set_defaults(chay=lenh_doi_chieu)

    for ten, mo_dun in _LENH.items():
        importlib.import_module(mo_dun).them_lenh(lenh.add_parser(ten))
    return goc


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    args = _tham_so().parse_args(argv)
    return args.chay(args) or 0


if __name__ == "__main__":
    sys.exit(main())
