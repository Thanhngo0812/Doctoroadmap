"""Lệnh con `quy-loi` của `python -m danhgia`: quy lỗi theo khâu (DG-15), bảng số đếm theo cuốn cho Hình 4.

  --hop-dong HD --g3 G3 --g4 G4 --can CAN --manifest MANIFEST (lấy `tap`; `ma_sach` của manifest phải trùng vàng)
  (--g1 G1 --dong DONG: tính lý do 1 từ A1/A2 | --khong-ap-ly-do-1: chưa có G2, cờ "không áp")
  [--muc nghiem|noi] [--vang chinh|hop|giao] [--mem cung|ca_hai] [--g5b G5B.json: [[nguồn, đích, "dung"], ...]]
  [--ra BANG.json] [--ra-danh-sach DS.json (chỉ tập phát triển)]

Màn hình chỉ in tên thước cố định và số (allowlist), không bao giờ in tên khái niệm hay danh sách cạnh. Tập thử: `--ra-danh-sach` bị từ chối.
"""
import json
from pathlib import Path

from danhgia.cham import a1a2, dong, quy_loi

ALLOWLIST_META = ("so_canh_vang", "ly_do_5_khong_ap", "cua_so_thieu")


def _doc(p):
    t = Path(p).read_text(encoding="utf-8-sig")
    return [json.loads(x) for x in t.splitlines() if x.strip()] if str(p).endswith(".jsonl") else json.loads(t)


def _chay(a):
    hd, g3, g4, can = _doc(a.hop_dong), _doc(a.g3), _doc(a.g4), _doc(a.can)
    manifest = _doc(a.manifest)
    if manifest.get("ma_sach") != g3["ma_sach"]:
        raise SystemExit("ma_sach của manifest không trùng vàng G3")
    tap = manifest.get("tap")
    if tap not in quy_loi.TAP:
        raise SystemExit(f"manifest.tap phải là một trong {quy_loi.TAP}")
    if a.ra_danh_sach and tap != "phat_trien":
        raise SystemExit("tập thử: chỉ in số, không ghi danh sách cạnh theo lý do")
    muc_loi = None
    if a.g1:
        if not a.dong:
            raise SystemExit("--g1 cần --dong (bảng dòng)")
        bang_dong = _doc(a.dong)
        du_doan = a1a2.du_doan_tu_hop_dong(hd, bang_dong)
        muc_loi, khong_dinh_vi = quy_loi.muc_loi_tu_a1a2(g3["khai_niem"], _doc(a.g1), du_doan, bang_dong)
        print(f"quy_loi.khai_niem_o_muc_loi {len(muc_loi)}")
        print(f"quy_loi.cau_khong_dinh_vi {khong_dinh_vi}")
    elif not a.khong_ap_ly_do_1:
        raise SystemExit("cần --g1 và --dong để tính lý do 1, hoặc --khong-ap-ly-do-1 khi chưa có G2")
    g5b = {(n, d): p for n, d, p in _doc(a.g5b)} if a.g5b else None
    ket = quy_loi.quy_loi(hd, g3, g4, can, tap=tap, muc=a.muc, vang=a.vang, mem=a.mem, muc_loi=muc_loi, g5b=g5b,
                          co_danh_sach=bool(a.ra_danh_sach))
    cuon = dong.gop_cuon(ket["rows"])
    for r in cuon:
        print(f"{r['thuoc']:<36} {r['gia_tri']}")
    for k in ALLOWLIST_META:
        print(f"quy_loi.meta.{k} {ket['meta'][k]}")
    print(f"quy_loi.meta.khong_ap {' '.join(map(str, ket['meta']['khong_ap'])) or '-'}")
    if a.ra:
        Path(a.ra).write_text(json.dumps({"theo_chuong": ket["rows"], "theo_cuon": cuon, "meta": ket["meta"]}, ensure_ascii=False, indent=1) + "\n",
                              encoding="utf-8")
    if a.ra_danh_sach:
        Path(a.ra_danh_sach).write_text(json.dumps(ket["danh_sach"], ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


def them_lenh(parser):
    for ten in ("--hop-dong", "--g3", "--g4", "--can", "--manifest"):
        parser.add_argument(ten, required=True)
    parser.add_argument("--g1")
    parser.add_argument("--dong")
    parser.add_argument("--khong-ap-ly-do-1", action="store_true")
    parser.add_argument("--muc", choices=("nghiem", "noi"), default="nghiem")
    parser.add_argument("--vang", choices=("chinh", "hop", "giao"), default="chinh")
    parser.add_argument("--mem", choices=("cung", "ca_hai"), default="cung")
    parser.add_argument("--g5b")
    parser.add_argument("--ra")
    parser.add_argument("--ra-danh-sach")
    parser.set_defaults(chay=_chay)
