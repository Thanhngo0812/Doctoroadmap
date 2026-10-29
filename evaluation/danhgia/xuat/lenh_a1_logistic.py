"""Lệnh con `a1-logistic`: chạy bộ đọc nhẹ với mô hình logistic trên một PDF và manifest sách, xuất hợp đồng hệ `a1_logistic` (chỉ khối `cau_truc`).

  python -m danhgia a1-logistic --pdf P.pdf --manifest M.json --mo-hinh evaluation/mo-hinh/dg21/a1-logistic --commit C --ngay-chay D --ra HD.json
  python -m danhgia cham-a1a2 --vang G1 --hop-dong HD.json --dong DONG.json --he a1_logistic --ma-sach MA

Không gọi mô hình ngôn ngữ. PDF phải khớp `pdf_sha256` của manifest, nếu không thì dừng. Màn hình chỉ in số qua cổng allowlist.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from danhgia.bao_cao import cong

CHO_PHEP = ("tap_thu", "so_trang", "so_tieu_de", "so_muc", "so_doan_van", "so_dong_can_duoc", "so_dong_khong_can")


def them_lenh(parser):
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--mo-hinh", required=True, help="thư mục có heading.joblib, join.joblib, manifest.json")
    parser.add_argument("--commit", required=True)
    parser.add_argument("--ngay-chay", required=True)
    parser.add_argument("--luot-nhieu", type=int, default=0)
    parser.add_argument("--ra", required=True)
    parser.set_defaults(chay=chay)


def chay(args):
    from .a1_logistic import doc_cau_truc

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    sha = hashlib.sha256(Path(args.pdf).read_bytes()).hexdigest()
    if sha != manifest.get("pdf_sha256"):
        raise SystemExit("PDF không khớp pdf_sha256 của manifest: dừng")
    dinh_danh = {"he": "a1_logistic", "bien_the": "a1-logistic-dg21", "luot_nhieu": args.luot_nhieu, "commit": args.commit,
                 "ngay_chay": args.ngay_chay, "transport": "none", "sha256_pdf": sha, "so_trang": manifest.get("so_trang")}
    hd = doc_cau_truc(args.pdf, args.mo_hinh, manifest["ma_sach"], dinh_danh=dinh_danh)
    Path(args.ra).write_text(json.dumps(hd, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    ct = hd["cau_truc"]
    cong.in_allowlist({"tap_thu": manifest.get("tap") == "thu", "so_trang": manifest.get("so_trang"), "so_tieu_de": len(ct["tieu_de"]),
                       "so_muc": len(ct["muc"]), "so_doan_van": len(ct["doan_van"]), "so_dong_can_duoc": len(ct["dong_thuoc_muc"]),
                       "so_dong_khong_can": len(ct["dong_khong_can"])}, CHO_PHEP)
    return 0
