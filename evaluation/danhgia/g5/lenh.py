"""Lệnh con `phieu-g5` của `python -m danhgia` (vé DG-16).

  chuan-bi  hợp đồng các hệ + bảng căn gộp + G3 + G4 chính + G4 thô từng người -> `chuan-bi-g5.json` (của người giữ) và `phieu-<người>.xlsx`
  doc       phiếu đã phán -> `ket-qua-g5.json`: precision hiệu chỉnh kèm CI, tỉ lệ bác câu đối chứng, điểm rubric, so sánh cặp
"""
import json
from pathlib import Path

from danhgia.g5 import phieu, tinh


def _doc(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _ghi(p, v):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(v, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def _cap(muc):
    ten, _, duong = muc.partition("=")
    if not duong:
        raise SystemExit(f"cần dạng <tên>=<tệp>, nhận {muc!r}")
    return ten, duong


def _chuan_bi(a):
    from danhgia.hop_dong import kiem

    hop_dong = {}
    for muc in a.hop_dong:
        he, duong = _cap(muc)
        hd = _doc(duong)
        loi = kiem(hd)
        if loi or hd["dinh_danh"]["he"] != he:
            print(f"LỖI hợp đồng {he}: " + ("; ".join(loi[:3]) if loi else "tên hệ không khớp dinh_danh.he"))
            return 1
        hop_dong[he] = hd
    g3, g4 = _doc(a.g3), _doc(a.g4)
    g4_tho = {n: _doc(d) for n, d in map(_cap, a.g4_tho)}
    tt = phieu.chuan_bi(hop_dong, _doc(a.can), g3, g4, g4_tho, ma_sach=g3["ma_sach"], seed=a.seed)
    d = Path(a.ra)
    _ghi(d / "chuan-bi-g5.json", tt)
    for nguoi in tt["nguoi"]:
        phieu.sinh_phieu(tt, nguoi, d / f"phieu-{nguoi}.xlsx")
    n_b = {n: len(v["b"]) for n, v in tt["nguoi"].items()}
    print(f"(a) {len(tt['a'])}/{tt['tong_a']} khái niệm; (b) hàng mỗi người {n_b}; (c) {len(tt['m'])} module, "
          f"{len(next(iter(tt['nguoi'].values()))['p']) if tt['nguoi'] else 0} cặp so sánh; thống kê cạnh mỗi hệ {tt['b_thong_ke']}")
    return 0


def _doc_phieu(a):
    tt = _doc(Path(a.thu_muc) / "chuan-bi-g5.json")
    phan = {}
    for muc in a.phieu:
        nguoi, duong = _cap(muc)
        ket, loi = phieu.doc_phieu(duong, tt, nguoi)
        if loi:
            print("\n".join(f"LỖI {nguoi}: {x}" for x in loi) + f"\n{len(loi)} lỗi: gửi phiếu lại, không sửa hộ")
            return 1
        phan[nguoi] = ket
    kq = tinh.ket_qua(tt, phan)
    _ghi(Path(a.thu_muc) / "ket-qua-g5.json", kq)
    for nguoi, k in kq["theo_nguoi"].items():
        for he, p in k["precision"].items():
            print(f"{nguoi} {he}: precision hiệu chỉnh {p['precision']} [{p['thap']}, {p['cao']}], cận dưới {p['precision_can_duoi']} "
                  f"(mẫu {p['n_mau']}/{p['du']} cạnh dư, khớp {p['khop']}, thiếu trường {p['khong_du_truong']})")
        print(f"{nguoi} đối chứng: {k['doi_chung']}")
    return 0


def them_lenh(parser):
    sub = parser.add_subparsers(dest="viec", required=True)
    p = sub.add_parser("chuan-bi", help="sinh phiếu G5 cho từng người")
    p.add_argument("--hop-dong", nargs="+", required=True, help="<he>=<tệp>: hệ chính, B1, B5, ...")
    p.add_argument("--can", required=True, help="bảng căn gộp (`can-khai-niem doc-phan`)")
    p.add_argument("--g3", required=True)
    p.add_argument("--g4", required=True, help="G4 chính (có vang_chinh)")
    p.add_argument("--g4-tho", nargs="+", required=True, help="<người>=<G4 thô của người đó trước hội ý>")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--ra", required=True)
    p.set_defaults(chay=_chuan_bi)
    p = sub.add_parser("doc", help="đọc phiếu đã phán")
    p.add_argument("--thu-muc", required=True)
    p.add_argument("--phieu", nargs="+", required=True, help="<người>=<phiếu>")
    p.set_defaults(chay=_doc_phieu)
