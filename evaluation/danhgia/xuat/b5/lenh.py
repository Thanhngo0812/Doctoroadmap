"""Lệnh con `b5` của `python -m danhgia`.

  python -m danhgia b5 --manifest M --pdf P --che-do a|b (--bien-the K | --seed S) --ra DIR [--dry-run] [--allow-spend]

Không có `--dry-run` thì bắt buộc `--allow-spend`; thiếu cờ này thì không dựng khách mô hình, không mở kết nối nào.
Ra: `b5{a|b}-k{K}.json` (hợp đồng), `b5{a|b}-k{K}-luot.json` (phản hồi thô, usage, cờ, báo cáo), hoặc `dry-run.json`.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

from danhgia.bo_sach import kiem_manifest
from danhgia.ten import chuan_hoa

from . import chuyen as chuyen_mod
from . import goi, loi_nhac, van_ban


def them_lenh(parser):
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--pdf", required=True)
    parser.add_argument("--che-do", choices=("a", "b"), required=True, help="a: một lời gọi cả cuốn; b: mỗi chương một lời gọi")
    nhom = parser.add_mutually_exclusive_group()
    nhom.add_argument("--bien-the", type=int, choices=range(1, loi_nhac.SO_BIEN_THE + 1), help="biến thể định dạng 1..5")
    nhom.add_argument("--seed", type=int, help="chọn biến thể theo seed")
    parser.add_argument("--ra", required=True)
    parser.add_argument("--dry-run", action="store_true", help="không gọi mạng; ghi dry-run.json")
    parser.add_argument("--allow-spend", action="store_true", help="bắt buộc khi không dry-run (lượt có tiền)")
    parser.add_argument("--commit", default=None)
    parser.add_argument("--ngay-chay", default=None)
    parser.set_defaults(chay=chay)


def tao_khach():
    """Dựng khách mô hình thật từ cấu hình dự án. Chỉ được gọi sau khi đã có `--allow-spend`. Trả (khách, transport)."""
    return goi.khach_that()


def _ghi(duong, gia_tri):
    Path(duong).write_text(json.dumps(gia_tri, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def _commit_hien_tai():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "khong-ro"


def _du_toan(manifest, doc_trang, k):
    he_thong, luoc_do = loi_nhac.he_thong(k), loi_nhac.luoc_do()
    cuon = van_ban.cuon(manifest, doc_trang)
    a = goi.du_toan([goi.uoc_token_vao(he_thong, loi_nhac.nguoi_dung(cuon), luoc_do)])
    a["so_ky_tu_van_ban"] = len(cuon)
    chuong = van_ban.chuong(manifest, doc_trang)
    b = goi.du_toan([goi.uoc_token_vao(he_thong, loi_nhac.nguoi_dung(c["text"]), luoc_do) for c in chuong])
    b["so_ky_tu_van_ban"] = sum(len(c["text"]) for c in chuong)
    return {"bien_the": k, "mo_hinh": goi.MO_HINH, "b5a": a, "b5b": b,
            "ghi_chu": "token_vao_uoc = (ký tự lời nhắc + văn bản + lược đồ) // 3, cách của dự án; B5b chưa tính danh sách "
                       "khái niệm các chương trước. Đầu ra tính ở trần nên usd_toi_da là cận trên, không phải số kỳ vọng."}


def _hash_cau_hinh(che_do, k):
    tep = loi_nhac.DUONG_MAC_DINH.read_bytes()
    goc = {"loi_nhac_sha256": hashlib.sha256(tep).hexdigest(), "che_do": che_do, "bien_the": k, "mo_hinh": goi.MO_HINH,
           "temperature": 0, "tran_token_ra": goi.TRAN_TOKEN_RA}
    return hashlib.sha256(json.dumps(goc, sort_keys=True).encode()).hexdigest()[:16]


def _ban_ghi_luot(nhan, dau, cuoi, l):
    return {"nhan": nhan, "dau": dau, "cuoi": cuoi, "phan_hoi_tho": l.text, "ly_do_dung": l.ly_do_dung, "giay": l.giay,
            "usage": l.usage, "ok": l.ok, "loi": l.loi, "cat_vi_tran": l.cat_vi_tran, "usd": l.usd}


def chay(args):
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    loi = kiem_manifest(manifest)
    if loi:
        print("manifest không hợp lệ: " + "; ".join(loi), file=sys.stderr)
        return 2
    sha = hashlib.sha256(Path(args.pdf).read_bytes()).hexdigest()
    if sha != manifest["pdf_sha256"]:
        print("sha256 của PDF khác manifest; từ chối chạy", file=sys.stderr)
        return 2
    if args.bien_the:
        k = args.bien_the
    else:
        k = loi_nhac.chon_bien_the(args.seed) if args.seed is not None else 1
    doc_trang = van_ban.doc_trang_pdf(args.pdf)
    ra = Path(args.ra)
    if args.dry_run:
        bao = _du_toan(manifest, doc_trang, k)
        ra.mkdir(parents=True, exist_ok=True)
        _ghi(ra / "dry-run.json", bao)
        print(json.dumps(bao, ensure_ascii=False, indent=1))
        return 0
    if not args.allow_spend:
        print("lượt thật có tiền: cần --allow-spend (hoặc --dry-run); không gọi mô hình", file=sys.stderr)
        return 2
    khach, transport = tao_khach()
    che_do, tien_to = args.che_do, f"b5{args.che_do}-k{k}"
    he_thong, luoc_do = loi_nhac.he_thong(k), loi_nhac.luoc_do()
    if che_do == "a":
        phan = [{"ma": "cuon", "dau": 1, "cuoi": manifest["so_trang"], "text": van_ban.cuon(manifest, doc_trang)}]
    else:
        phan = van_ban.chuong(manifest, doc_trang)
    ra.mkdir(parents=True, exist_ok=True)
    luots, ban_ghi, truoc, da_thay = [], [], [], set()
    for p in phan:
        l = goi.chay_luot(khach, he_thong, loi_nhac.nguoi_dung(p["text"], truoc), luoc_do)
        luots.append(chuyen_mod.LuotCuaChuong(p["ma"], p["dau"], p["cuoi"], l))
        ban_ghi.append(_ban_ghi_luot(p["ma"], p["dau"], p["cuoi"], l))
        _ghi(ra / f"{tien_to}-luot.json", {"che_do": che_do, "bien_the": k, "luot": ban_ghi, "bao_cao": None})  # lưu dần
        if l.ok:
            for kn in l.du_lieu["khai_niem"]:
                khoa = chuan_hoa(kn["ten"])
                if khoa and khoa not in da_thay:
                    da_thay.add(khoa)
                    truoc.append(kn["ten"])
    try:
        hop_dong, bao_cao = chuyen_mod.chuyen(
            luots, manifest=manifest, doc_trang=doc_trang, che_do=che_do, k=k, commit=args.commit or _commit_hien_tai(),
            ngay_chay=args.ngay_chay or date.today().isoformat(), transport=transport, mo_hinh=goi.MO_HINH,
            hash_cau_hinh=_hash_cau_hinh(che_do, k))
    except chuyen_mod.KhongCoLuotNaoThanhCong as ngoai_le:
        bao_cao = {"so_luot": len(luots), "so_luot_ok": 0, "cat_vi_tran": any(l.luot.cat_vi_tran for l in luots),
                   "luot_that_bai": [{"nhan": l.nhan, "cat_vi_tran": l.luot.cat_vi_tran, "loi": l.luot.loi} for l in luots],
                   "ly_do": str(ngoai_le)}
        _ghi(ra / f"{tien_to}-luot.json", {"che_do": che_do, "bien_the": k, "luot": ban_ghi, "bao_cao": bao_cao})
        print("không có lượt nào thành công; không ghi hợp đồng", file=sys.stderr)
        return 1
    _ghi(ra / f"{tien_to}.json", hop_dong)
    _ghi(ra / f"{tien_to}-luot.json", {"che_do": che_do, "bien_the": k, "luot": ban_ghi, "bao_cao": bao_cao})
    so_kn, so_canh = len(hop_dong["khai_niem"]), len(hop_dong["canh"])
    print(f"đã ghi {tien_to}.json: {so_kn} khái niệm, {so_canh} cạnh, {bao_cao['so_luot_ok']}/{bao_cao['so_luot']} lượt ok")
    return 0 if bao_cao["so_luot_ok"] == bao_cao["so_luot"] else 1
