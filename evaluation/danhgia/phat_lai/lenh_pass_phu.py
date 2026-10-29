"""Lệnh con `pass-phu-thay` và `cap-ce` của `python -m danhgia` (vé DG-21). Không gọi mô hình, chi phí 0.

  python -m danhgia pass-phu-thay --kho K --doc D --phien-ban V --bo-cham lightgbm --kiem-tai-tao
      chấm lại pass phụ bằng bộ chấm LightGBM của sản phẩm rồi so với pass phụ và dãy học đã lưu (thoát 1 nếu lệch)
  python -m danhgia pass-phu-thay ... --bo-cham logistic --mo-hinh evaluation/mo-hinh/dg21/m3-logistic --hop-dong HD.json --ra OUT.json
      hệ `a8_logistic`: chấm lại bằng M3 logistic, thay cạnh pass phụ, phát lại A9 -> A10
  python -m danhgia pass-phu-thay ... --bo-cham diem-co-san --diem DIEM.jsonl --hop-dong HD.json --ra OUT.json
      hệ `a8_cross_encoder`: điểm do `scripts/dg21/ce_cham.py` chấm
  python -m danhgia cap-ce --kho K --doc D --phien-ban V --ra CAP.jsonl
      xuất mọi chiều ứng viên pass phụ kèm văn bản đầu vào cross-encoder, đúng thứ tự bộ chấm nhận

`--kho` chỉ đọc; không tệp nào của kho được ghi. Màn hình chỉ in khoá trong allowlist với giá trị số, bool, null (cổng `bao_cao.cong`),
nên chạy trên sách tập thử cũng không lộ tên khái niệm hay câu.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from danhgia.bao_cao import cong

HE = {"logistic": "a8_logistic", "diem-co-san": "a8_cross_encoder"}
CHO_PHEP_KIEM = ("tai_tao_dung", "canh_phu_dung", "nhat_ky_phu_dung", "day_hoc_dung", "canh_requires_dung", "so_canh_phu_moi", "so_canh_phu_cu",
                 "so_day_hoc_moi", "so_day_hoc_cu", "canh_phu_chi_o_moi", "canh_phu_chi_o_cu", "mo_hinh_khop_graph")
CHO_PHEP_THAY = ("so_khai_niem", "so_canh", "so_canh_cung", "so_day_hoc", "so_canh_phu_moi", "so_canh_phu_cu", "canh_phu_chi_o_moi", "canh_phu_chi_o_cu")
CHO_PHEP_CAP = ("so_cap_ung_vien", "so_dong", "so_chieu_phu_hop")


def them_lenh(parser):
    parser.add_argument("--kho", required=True)
    parser.add_argument("--doc", required=True)
    parser.add_argument("--phien-ban", type=int, required=True)
    parser.add_argument("--bo-cham", choices=("lightgbm", "logistic", "diem-co-san"), required=True)
    parser.add_argument("--mo-hinh", help="thư mục mô hình: logistic (model.joblib + manifest.json) hay LightGBM (model.txt + manifest.json; mặc định mô hình sản phẩm). "
                        "Kiểm tái tạo phải truyền đúng mô hình đã dựng graph")
    parser.add_argument("--diem", help="tệp điểm có sẵn của cross-encoder")
    parser.add_argument("--kiem-tai-tao", action="store_true", help="chỉ so với pass phụ và dãy học đã lưu, không xuất hợp đồng")
    parser.add_argument("--hop-dong", help="hợp đồng hệ chính của cùng graph (nguồn của dinh_danh)")
    parser.add_argument("--commit")
    parser.add_argument("--ngay-chay")
    parser.add_argument("--ra")
    parser.set_defaults(chay=chay)


def them_lenh_cap_ce(parser):
    parser.add_argument("--kho", required=True)
    parser.add_argument("--doc", required=True)
    parser.add_argument("--phien-ban", type=int, required=True)
    parser.add_argument("--ra", required=True)
    parser.set_defaults(chay=chay_cap_ce)


def bo_cham(args):
    if args.bo_cham == "lightgbm":
        from doc2roadmap.infrastructure.secondary_model import LightGBMSecondaryScorer
        return LightGBMSecondaryScorer(model_dir=args.mo_hinh)
    from .bo_cham import DiemCoSanScorer, LogisticSecondaryScorer
    if args.bo_cham == "logistic":
        if not args.mo_hinh:
            raise SystemExit("--bo-cham logistic cần --mo-hinh")
        return LogisticSecondaryScorer(args.mo_hinh)
    if not args.diem:
        raise SystemExit("--bo-cham diem-co-san cần --diem")
    return DiemCoSanScorer(args.diem)


def chay(args):
    from .pass_phu import phat_lai_voi_bo_cham, so_voi_da_luu
    from .xuat import hop_dong

    cham = bo_cham(args)
    ket_qua, artifact = phat_lai_voi_bo_cham(args.kho, args.doc, args.phien_ban, cham)
    so = so_voi_da_luu(ket_qua, artifact)
    if args.kiem_tai_tao:
        cong.in_allowlist({"tai_tao_dung": so["tai_tao_dung"], "canh_phu_dung": so["canh_phu_dung"], "nhat_ky_phu_dung": so["nhat_ky_phu_dung"],
                           "day_hoc_dung": so["day_hoc_dung"], "canh_requires_dung": so["canh_requires_dung"],
                           "so_canh_phu_moi": so["so_canh_phu"][0], "so_canh_phu_cu": so["so_canh_phu"][1],
                           "so_day_hoc_moi": so["so_day_hoc"][0], "so_day_hoc_cu": so["so_day_hoc"][1],
                           "canh_phu_chi_o_moi": so["canh_phu_chi_o_moi"], "canh_phu_chi_o_cu": so["canh_phu_chi_o_cu"],
                           "mo_hinh_khop_graph": so["mo_hinh_khop"]}, CHO_PHEP_KIEM)
        if so["mo_hinh_khop"] is False:
            print("CẢNH BÁO: mô hình chấm khác mô hình đã dựng graph (config.scorer của manifest edges); lệch nếu có là do mô hình, không phải bộ nối", file=sys.stderr)
        elif so["mo_hinh_khop"] is None:
            print("CẢNH BÁO: graph không ghi mô hình đã dựng; kiểm tái tạo chỉ đáng tin nếu --mo-hinh là mô hình đã dựng graph", file=sys.stderr)
        return 0 if so["tai_tao_dung"] else 1
    if args.bo_cham == "lightgbm":
        raise SystemExit("--bo-cham lightgbm chỉ dùng với --kiem-tai-tao (hệ chính đã có hợp đồng riêng)")
    if not (args.hop_dong and args.ra):
        raise SystemExit("xuất hợp đồng cần --hop-dong và --ra")
    chinh = json.loads(Path(args.hop_dong).read_text(encoding="utf-8"))
    ten_he = HE[args.bo_cham]
    dinh_danh = {**chinh["dinh_danh"], "bien_the": f"{cham.metadata['version']}:{(cham.metadata.get('model_sha256') or '')[:12]}"}
    if args.commit:
        dinh_danh["commit"] = args.commit
    if args.ngay_chay:
        dinh_danh["ngay_chay"] = args.ngay_chay
    tham_so = {"bien_the": ten_he, "bo_cham": cham.metadata}
    hd = hop_dong(ket_qua, args.kho, args.doc, args.phien_ban, dinh_danh=dinh_danh, he=ten_he, tham_so=tham_so)
    Path(args.ra).write_text(json.dumps(hd, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    canh_cung = sum(1 for c in hd["canh"] if not c["mem"] and not c["bo_qua"])
    cong.in_allowlist({"so_khai_niem": len(hd["khai_niem"]), "so_canh": len(hd["canh"]), "so_canh_cung": canh_cung,
                       "so_day_hoc": len(hd["lo_trinh"]["day_hoc"]), "so_canh_phu_moi": so["so_canh_phu"][0], "so_canh_phu_cu": so["so_canh_phu"][1],
                       "canh_phu_chi_o_moi": so["canh_phu_chi_o_moi"], "canh_phu_chi_o_cu": so["canh_phu_chi_o_cu"]}, CHO_PHEP_THAY)
    return 0


def chay_cap_ce(args):
    from .bo_cham import dac_trung_sha
    from .pass_phu import cap_ung_vien

    hang = cap_ung_vien(args.kho, args.doc, args.phien_ban)
    dong = [json.dumps({**van_ban, "dac_trung_sha": dac_trung_sha(dac_trung)}, ensure_ascii=False) for _, _, _, dac_trung, van_ban in hang]
    Path(args.ra).write_text("".join(d + "\n" for d in dong), encoding="utf-8", newline="\n")
    cong.in_allowlist({"so_cap_ung_vien": len({h[0] for h in hang}), "so_dong": len(dong), "so_chieu_phu_hop": len(hang)}, CHO_PHEP_CAP)
    return 0
