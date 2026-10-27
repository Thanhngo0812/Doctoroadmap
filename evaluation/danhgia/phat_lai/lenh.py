"""Lệnh con `phat-lai` của `python -m danhgia`.

  python -m danhgia phat-lai --kho K --doc D --phien-ban V --bien-the khong-doi
      kiểm tái tạo: phát lại với cạnh không đổi, so `sequence` và `requires_edges` với graph V đã lưu (thoát 1 nếu lệch)
  python -m danhgia phat-lai --kho K --doc D --phien-ban V --bien-the tat-r17|bo-pass-chinh|bo-pass-phu --hop-dong HD.json --ra OUT.json
  python -m danhgia phat-lai ... --bien-the oracle-a10 --hop-dong HD.json --g3 G3 --g4 G4 --can CAN --ra OUT.json

`--kho` chỉ đọc; không gọi mạng (tên khái niệm lấy từ phản hồi đã ghi). `HD.json` là hợp đồng hệ chính của cùng graph, nguồn của `dinh_danh`.
"""
from __future__ import annotations

import json
from pathlib import Path

from .chay import kiem_tai_tao, phat_lai
from .oracle import canh_oracle
from .xuat import hop_dong

BIEN_THE = ("khong-doi", "tat-r17", "bo-pass-chinh", "bo-pass-phu", "oracle-a10")
HE = {"tat-r17": "tat_r17", "bo-pass-chinh": "bo_pass_chinh", "bo-pass-phu": "bo_pass_phu", "oracle-a10": "oracle_a10"}


def them_lenh(parser):
    parser.add_argument("--kho", required=True)
    parser.add_argument("--doc", required=True)
    parser.add_argument("--phien-ban", type=int, required=True)
    parser.add_argument("--bien-the", choices=BIEN_THE, required=True)
    parser.add_argument("--hop-dong")
    parser.add_argument("--g3")
    parser.add_argument("--g4")
    parser.add_argument("--can")
    parser.add_argument("--ra")
    parser.set_defaults(chay=chay)


def _doc(duong):
    return json.loads(Path(duong).read_text(encoding="utf-8"))


def chay(args):
    if args.bien_the == "khong-doi":
        ket_qua = kiem_tai_tao(args.kho, args.doc, args.phien_ban)
        print(json.dumps(ket_qua, ensure_ascii=False))
        return 0 if ket_qua["tai_tao_dung"] else 1
    if not (args.hop_dong and args.ra):
        raise SystemExit("biến thể này cần --hop-dong và --ra")
    chinh = _doc(args.hop_dong)
    tham_so = {"bien_the": args.bien_the}
    nguon_goc = None
    if args.bien_the == "oracle-a10":
        if not (args.g3 and args.g4 and args.can):
            raise SystemExit("oracle-a10 cần --g3, --g4 và --can")
        ids_node = {k["ma"] for k in chinh["khai_niem"]}
        canh, thong_ke = canh_oracle(chinh, _doc(args.g3), _doc(args.g4), _doc(args.can), ids_node)
        kq = phat_lai(args.kho, args.doc, args.phien_ban, canh_thay=canh)
        nguon_goc, tham_so = "baseline", {**tham_so, **thong_ke}
        print(json.dumps({"oracle": thong_ke}, ensure_ascii=False))
    else:
        kq = phat_lai(args.kho, args.doc, args.phien_ban, tat_luat_r17=args.bien_the == "tat-r17",
                      bo_pass_chinh=args.bien_the == "bo-pass-chinh", bo_pass_phu=args.bien_the == "bo-pass-phu")
    ket_qua = hop_dong(kq, args.kho, args.doc, args.phien_ban, dinh_danh=chinh["dinh_danh"], he=HE[args.bien_the],
                       tham_so=tham_so, nguon_goc_canh=nguon_goc)
    Path(args.ra).write_text(json.dumps(ket_qua, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    cung = sum(1 for c in ket_qua["canh"] if not c["mem"] and not c["bo_qua"])
    print(f"đã ghi {args.ra}: he={HE[args.bien_the]}, {len(ket_qua['khai_niem'])} khái niệm, {len(ket_qua['canh'])} cạnh "
          f"({cung} cứng), dãy học {len(ket_qua['lo_trinh']['day_hoc'])}")
    return 0
