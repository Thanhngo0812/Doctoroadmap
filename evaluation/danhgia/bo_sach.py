"""Manifest sách `danh-gia-sach-1`, bốc 3 chương theo seed, kiểm PDF gốc (spec mục 4; vé DG-01).

Luật bốc chỉ đọc danh sách chương của manifest (lấy từ mục lục in), không đọc nội dung sách và không nhìn đầu ra máy:
- chương hợp lệ là chương `noi_dung` dài từ `n_trang_toi_thieu` trang trở lên;
- các chương hợp lệ, theo thứ tự sách, chia thành ba phần liền nhau gần bằng nhau (đầu, giữa, cuối);
- mỗi phần bốc một chương bằng LCG tất định theo seed.

Lệnh kiểm PDF chỉ in trường số trong allowlist: tên sách và đường dẫn tập thử không bao giờ được in.

Chạy: `python -m danhgia.bo_sach boc <manifest.json> --seed S --n-trang N` hoặc `python -m danhgia.bo_sach kiem-pdf <mã> <tệp.pdf>`.
"""
import argparse
import json
import sys
from pathlib import Path

from danhgia.thong_ke.lcg import Lcg

SCHEMA = "danh-gia-sach-1"
TAP = {"phat_trien", "thu"}
LOAI = {"noi_dung", "mo_dau", "bai_tap", "phu_luc"}
NGUONG_KY_TU = 80          # một trang có lớp chữ khi có từ 80 ký tự không trắng trở lên
NGUONG_BAN_QUET = 0.8      # dưới 80% trang có lớp chữ thì nghi là bản quét, phải kiểm thêm bằng bộ định tuyến vé 15
ALLOWLIST_PDF = ("so_trang", "so_trang_co_chu", "ti_le_co_chu", "nghi_ban_quet")


def _so_trang(chuong):
    return chuong["trang_cuoi"] - chuong["trang_dau"] + 1


def kiem_manifest(m):
    """Danh sách lỗi; rỗng là hợp lệ."""
    loi = []
    if m.get("schema") != SCHEMA:
        loi.append(f"schema phải là {SCHEMA}")
    for truong in ("ma_sach", "chu_de", "pdf_sha256", "quyen"):
        if not isinstance(m.get(truong), str) or not m.get(truong):
            loi.append(f"thiếu {truong}")
    if m.get("tap") not in TAP:
        loi.append(f"tap phải thuộc {sorted(TAP)}")
    so_trang = m.get("so_trang")
    if not isinstance(so_trang, int) or so_trang < 1:
        loi.append("so_trang phải là số nguyên dương")
        so_trang = None
    chuong = m.get("chuong") or []
    if not chuong:
        loi.append("thiếu danh sách chuong")
    ma_da_thay, truoc = set(), None
    for c in chuong:
        ma = c.get("ma")
        if ma in ma_da_thay:
            loi.append(f"trùng mã chương {ma}")
        ma_da_thay.add(ma)
        if c.get("loai") not in LOAI:
            loi.append(f"{ma}: loai phải thuộc {sorted(LOAI)}")
        dau, cuoi = c.get("trang_dau"), c.get("trang_cuoi")
        if not isinstance(dau, int) or not isinstance(cuoi, int) or dau < 1 or cuoi < dau or (so_trang and cuoi > so_trang):
            loi.append(f"{ma}: trang_dau/trang_cuoi không hợp lệ")
            continue
        if truoc is not None and dau <= truoc["trang_cuoi"] and dau != truoc["trang_cuoi"]:
            # Hai chương được phép chung đúng một trang (chương sau bắt đầu giữa trang cuối của chương trước); chồng hơn thế là lỗi.
            loi.append(f"{ma}: chồng trang với {truoc['ma']}")
        truoc = c
    boc = m.get("boc")
    if boc is not None:
        for ma in boc.get("chuong", []):
            if ma not in ma_da_thay:
                loi.append(f"boc: chương {ma} không có trong danh sách")
    return loi


def boc_chuong(m, *, seed, n_trang_toi_thieu):
    loi = kiem_manifest(m)
    if loi:
        raise ValueError(f"manifest không hợp lệ: {loi}")
    hop_le = [c["ma"] for c in m["chuong"] if c["loai"] == "noi_dung" and _so_trang(c) >= n_trang_toi_thieu]
    if len(hop_le) < 3:
        raise ValueError(f"{m['ma_sach']}: chỉ có {len(hop_le)} chương hợp lệ, cần ít nhất 3")
    n = len(hop_le)
    co = [n // 3 + (1 if i < n % 3 else 0) for i in range(3)]
    sinh, dau, chon = Lcg(seed), 0, []
    for kich in co:
        chon.append(hop_le[dau + sinh.chi_so(kich)])
        dau += kich
    return {"seed": seed, "n_trang_toi_thieu": n_trang_toi_thieu, "chuong": chon}


def kiem_pdf_goc(duong):
    import pypdfium2

    doc = pypdfium2.PdfDocument(str(duong))
    try:
        co_chu = 0
        for i in range(len(doc)):
            trang = doc[i]
            tp = trang.get_textpage()
            chu = tp.get_text_range()
            if sum(1 for k in chu if not k.isspace()) >= NGUONG_KY_TU:
                co_chu += 1
            tp.close()
            trang.close()
        so_trang = len(doc)
    finally:
        doc.close()
    ti_le = co_chu / so_trang if so_trang else 0.0
    return {"so_trang": so_trang, "so_trang_co_chu": co_chu, "ti_le_co_chu": round(ti_le, 4),
            "nghi_ban_quet": ti_le < NGUONG_BAN_QUET}


def tom_tat_kiem_pdf(ma, ket):
    """Một dòng in được ra màn hình: mã ẩn danh cộng trường trong allowlist, không gì khác."""
    if not isinstance(ma, str) or not ma.replace("-", "").isalnum() or len(ma) > 12:
        raise ValueError("mã in ra phải là mã ẩn danh ngắn, không phải tên sách")
    phan = [f"{k}={ket[k]}" for k in ALLOWLIST_PDF if isinstance(ket.get(k), (int, float, bool))]
    return f"{ma} " + " ".join(phan)


def main(argv=None):
    p = argparse.ArgumentParser(prog="python -m danhgia.bo_sach")
    lenh = p.add_subparsers(dest="lenh", required=True)
    boc = lenh.add_parser("boc", help="bốc 3 chương theo seed, ghi vào manifest")
    boc.add_argument("manifest", type=Path)
    boc.add_argument("--seed", type=int, required=True)
    boc.add_argument("--n-trang", type=int, required=True)
    kiem = lenh.add_parser("kiem", help="kiểm manifest")
    kiem.add_argument("manifest", type=Path)
    pdf = lenh.add_parser("kiem-pdf", help="kiểm PDF gốc; chỉ in số")
    pdf.add_argument("ma")
    pdf.add_argument("pdf", type=Path)
    a = p.parse_args(argv)
    if a.lenh == "kiem-pdf":
        print(tom_tat_kiem_pdf(a.ma, kiem_pdf_goc(a.pdf)))
        return 0
    m = json.loads(a.manifest.read_text(encoding="utf-8"))
    if a.lenh == "kiem":
        loi = kiem_manifest(m)
        print("hợp lệ" if not loi else "\n".join(loi))
        return 0 if not loi else 1
    m["boc"] = boc_chuong(m, seed=a.seed, n_trang_toi_thieu=a.n_trang)
    a.manifest.write_text(json.dumps(m, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(" ".join(m["boc"]["chuong"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
