"""Lệnh con `g1g2` của `python -m danhgia` (vé DG-12).

  goi          manifest + PDF -> gói nháp cho Codex (bảng dòng, hướng dẫn, validator)
  kiem-nhap    kiểm cay-muc do Codex trả
  cai-loi      (người giữ) cài 3–5 lỗi vào bản nháp; sổ lỗi ghi ra tệp riêng, ngoài thư mục gói
  phieu        bản nháp sau cài -> phiếu Excel; thêm --mau-seed thì là phiếu người duyệt thứ hai (mẫu ~30%)
  vang         phiếu người thứ nhất -> vàng cuối (đã gỡ lỗi bỏ sót) + tỉ lệ bắt lỗi cài
  dong-thuan   hai phiếu đã điền -> κ và % đồng ý (vai trò G2, cấp) trên mẫu của người hai
  tong-hop     nhiều báo cáo bắt lỗi -> tỉ lệ theo cuốn và theo loại
"""
import json
import shutil
from pathlib import Path

from danhgia.g1g2 import goi, kiem_cay, loi_cai, nguoi_hai, phieu, vang


def _doc(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _ghi(p, v):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(v, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def _nap(a):
    m = _doc(a.manifest)
    dong = kiem_cay.doc_jsonl(Path(a.thu_muc) / "dong" / f"{m['ma_sach']}.jsonl")
    return m, dong, kiem_cay.doc_jsonl(a.nhap_cai)


def _goi(a):
    ra = goi.sinh_goi(_doc(a.manifest), a.pdf, a.ra)
    print(f"đã ghi gói nháp vào {ra}: {json.loads((ra / 'thong-tin.json').read_text(encoding='utf-8'))['so_dong']} dòng")
    return 0


def _kiem_nhap(a):
    ds = kiem_cay.kiem_thu_muc(a.sach, a.thu_muc)
    print("\n".join(ds) if ds else "ĐẠT")
    return 1 if ds else 0


def _cai_loi(a):
    thu_muc = Path(a.thu_muc).resolve()
    if thu_muc in Path(a.ra_so_loi).resolve().parents:
        raise SystemExit("sổ lỗi cài không được nằm trong thư mục gói giao cho người làm nháp")
    dong = kiem_cay.doc_jsonl(thu_muc / "dong" / f"{a.sach}.jsonl")
    nhap = kiem_cay.doc_jsonl(thu_muc / "cay-muc" / f"{a.sach}.jsonl")
    nhap_cai, so = loi_cai.cai_loi(nhap, dong, seed=a.seed, so_loi=a.so_loi)
    goi.ghi_jsonl(a.ra_nhap_cai, nhap_cai)
    _ghi(a.ra_so_loi, {"schema": "danh-gia-so-loi-cai-1", "ma_sach": a.sach, "seed": a.seed, "loi": so})
    print(f"đã cài {len(so)} lỗi ({', '.join(x['loai'] for x in so)}); sổ ở {a.ra_so_loi}")
    return 0


def _phieu(a):
    m, dong, nhap_cai = _nap(a)
    khoa = None
    if a.mau_seed is not None:
        khoa = nguoi_hai.chon_mau([h["dong"][0] for h in nhap_cai], seed=a.mau_seed, ti_le=a.ti_le)
    phieu.sinh_phieu(nhap_cai, dong, m, a.nguoi, a.ra, khoa=khoa)
    print(f"đã ghi {a.ra}: {len(nhap_cai) if khoa is None else len(khoa)} hàng")
    return 0


def _vang(a):
    m, dong, nhap_cai = _nap(a)
    doc, loi = phieu.doc_phieu(a.phieu, nhap_cai, dong, m)
    if loi:
        print("\n".join(f"LỖI {x}" for x in loi) + f"\n{len(loi)} lỗi: gửi phiếu lại cho người duyệt, không sửa hộ")
        return 1
    muc, bao_cao, loi = vang.vang_cuoi(nhap_cai, _doc(a.so_loi)["loi"], doc, dong, m["ma_sach"])
    if loi:
        print("\n".join(f"LỖI CÂY {x}" for x in loi) + "\nphiếu sửa ra cây không hợp lệ: gửi phiếu lại cho người duyệt")
        return 1
    ra = Path(a.ra)
    for ten in ("dong", "chon-trang-mau"):
        shutil.copytree(Path(a.thu_muc) / ten, ra / ten, dirs_exist_ok=True)
    goi.ghi_jsonl(ra / "cay-muc" / f"{m['ma_sach']}.jsonl", muc)
    _ghi(a.ra_bao_cao, bao_cao)
    print(f"vàng cuối {len(muc)} mục; bắt được {bao_cao['bat']}/{bao_cao['da_cai']} lỗi cài; sửa nhầm {bao_cao['sua_nham']}")
    return 0


def _dong_thuan(a):
    m, dong, nhap_cai = _nap(a)
    docs = []
    for p in (a.phieu1, a.phieu2):
        doc, loi = phieu.doc_phieu(p, nhap_cai, dong, m)
        if loi:
            print("\n".join(f"LỖI {p}: {x}" for x in loi))
            return 1
        docs.append(doc)
    print(json.dumps(nguoi_hai.dong_thuan(*docs), ensure_ascii=False, indent=1))
    return 0


def _tong_hop(a):
    bc = {}
    for p in a.bao_cao:
        v = _doc(p)
        bc[v["ma_sach"]] = v
    print(json.dumps(vang.tong_hop(bc), ensure_ascii=False, indent=1))
    return 0


def them_lenh(parser):
    sub = parser.add_subparsers(dest="viec", required=True)

    p = sub.add_parser("goi", help="gói nháp cho Codex")
    p.add_argument("--manifest", required=True)
    p.add_argument("--pdf", required=True)
    p.add_argument("--ra", required=True)
    p.set_defaults(chay=_goi)

    p = sub.add_parser("kiem-nhap", help="kiểm cay-muc đã trả")
    p.add_argument("--sach", required=True)
    p.add_argument("--thu-muc", required=True)
    p.set_defaults(chay=_kiem_nhap)

    p = sub.add_parser("cai-loi", help="(người giữ) cài lỗi vào bản nháp")
    p.add_argument("--sach", required=True)
    p.add_argument("--thu-muc", required=True, help="thư mục gói, có dong/ và cay-muc/")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--so-loi", type=int, default=None, help="3–5; mặc định bốc theo seed")
    p.add_argument("--ra-nhap-cai", required=True)
    p.add_argument("--ra-so-loi", required=True, help="sổ lỗi cài, để ngoài repo và ngoài thư mục gói")
    p.set_defaults(chay=_cai_loi)

    def chung(p):
        p.add_argument("--manifest", required=True)
        p.add_argument("--thu-muc", required=True, help="thư mục gói, có dong/")
        p.add_argument("--nhap-cai", required=True)

    p = sub.add_parser("phieu", help="phiếu duyệt Excel")
    chung(p)
    p.add_argument("--nguoi", required=True, help="mã ẩn danh của người duyệt")
    p.add_argument("--ra", required=True)
    p.add_argument("--mau-seed", type=int, default=None, help="có thì sinh phiếu mẫu cho người thứ hai")
    p.add_argument("--ti-le", type=float, default=0.30)
    p.set_defaults(chay=_phieu)

    p = sub.add_parser("vang", help="phiếu người thứ nhất -> vàng cuối và tỉ lệ bắt lỗi cài")
    chung(p)
    p.add_argument("--so-loi", required=True)
    p.add_argument("--phieu", required=True)
    p.add_argument("--ra", required=True, help="thư mục vàng cuối (cùng định dạng D-02, qua kiem_nhan_d02.py --chi-cay)")
    p.add_argument("--ra-bao-cao", required=True)
    p.set_defaults(chay=_vang)

    p = sub.add_parser("dong-thuan", help="κ giữa hai người duyệt")
    chung(p)
    p.add_argument("--phieu1", required=True)
    p.add_argument("--phieu2", required=True)
    p.set_defaults(chay=_dong_thuan)

    p = sub.add_parser("tong-hop", help="gộp báo cáo bắt lỗi nhiều cuốn")
    p.add_argument("bao_cao", nargs="+")
    p.set_defaults(chay=_tong_hop)
