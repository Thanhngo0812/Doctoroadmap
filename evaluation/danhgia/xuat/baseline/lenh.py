"""Lệnh con `baseline` của `python -m danhgia`: xuất B1-B4 ra hợp đồng `danh-gia-xuat-1`.

  python -m danhgia baseline --loai b1|b2|b3|b4 --kho K --doc D --phien-ban V --hop-dong HD.json --ra OUT.json

`HD.json` là hợp đồng của hệ chính (lệnh `xuat`) cho cùng graph `V`. `--kho` chỉ đọc. B1 và B2 chạy hàm dãy học A10 qua bộ phát lại;
B3 chỉ cần hợp đồng; B4 đọc ứng viên A3 từ canonical mà graph `V` dùng.
"""
from __future__ import annotations

import json
from pathlib import Path

from .b3 import hop_dong_b3
from .b4 import hop_dong_b4

LOAI = ("b1", "b2", "b3", "b4")


def them_lenh(parser):
    parser.add_argument("--loai", choices=LOAI, required=True)
    parser.add_argument("--kho", required=True)
    parser.add_argument("--doc", required=True)
    parser.add_argument("--phien-ban", type=int, required=True)
    parser.add_argument("--hop-dong", required=True, help="hợp đồng của hệ chính cho cùng graph")
    parser.add_argument("--ra", required=True)
    parser.set_defaults(chay=chay)


def _doc(duong):
    return json.loads(Path(duong).read_text(encoding="utf-8"))


def _cau_hinh(kho, doc, phien_ban):
    return _doc(Path(kho) / "graph" / doc / f"v{phien_ban}" / "manifest.json")["config"]


def _chunks(kho, doc, phien_ban):
    return _doc(Path(kho) / "chunks" / doc / f"v{_cau_hinh(kho, doc, phien_ban)['chunks_version']}" / "chunks.json")


def _chay_phat_lai(args, hop_dong, canh_thay, he, tham_so):
    from danhgia.phat_lai import hop_dong as xuat_phat_lai, phat_lai

    kq = phat_lai(args.kho, args.doc, args.phien_ban, canh_thay=canh_thay)
    return xuat_phat_lai(kq, args.kho, args.doc, args.phien_ban, dinh_danh=hop_dong["dinh_danh"], he=he,
                         tham_so=tham_so, nguon_goc_canh="baseline")


def xuat_baseline(args):
    hop_dong = _doc(args.hop_dong)
    if args.loai == "b3":
        return hop_dong_b3(hop_dong)
    if args.loai == "b4":
        canonical = _doc(Path(args.kho) / "canonical" / args.doc
                         / f"v{_cau_hinh(args.kho, args.doc, args.phien_ban)['canonical_version']}" / "canonical.json")
        trang = {c["chunk_id"]: c["page"] for c in _chunks(args.kho, args.doc, args.phien_ban)}
        return hop_dong_b4(hop_dong, canonical["source_candidates"], trang)
    from .b2 import canh_b2

    if args.loai == "b1":
        return _chay_phat_lai(args, hop_dong, [], "b1", {"canh": "khong"})
    canh = canh_b2(hop_dong, _chunks(args.kho, args.doc, args.phien_ban))
    return _chay_phat_lai(args, hop_dong, canh, "b2", {"canh": "ten_trong_cua_so_chunk_cau_neo"})


def chay(args):
    ket_qua = xuat_baseline(args)
    Path(args.ra).write_text(json.dumps(ket_qua, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"đã ghi {args.ra}: he={ket_qua['dinh_danh']['he']}, {len(ket_qua['khai_niem'])} khái niệm, "
          f"{len(ket_qua['canh'])} cạnh, dãy học {len(ket_qua['lo_trinh']['day_hoc'])}")
    return 0
