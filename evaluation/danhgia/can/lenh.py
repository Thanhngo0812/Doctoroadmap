"""Lệnh con `can-khai-niem` của `python -m danhgia` (vé DG-09).

  chuan-bi    G3 + G4 + hợp đồng các hệ -> luật tự động, phiếu mù `phieu-mu.xlsx`, `chuan-bi.json` (của người giữ: có id node)
  doc-phan    phiếu mù đã phán -> `can.json` (danh-gia-can-1, `may` = <he>:<ma>) và `nhat-ky.json`
  phieu-kiem  bốc 20% ca phán tay theo seed -> phiếu kiểm (không có phán gốc)
  doc-kiem    phiếu kiểm đã điền -> % đồng ý và κ
  tach        bảng căn gộp -> bảng căn riêng một hệ (id trần) cho lõi chấm
"""
import json
from pathlib import Path

from danhgia.can import kiem, luat, mu


def _doc(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _ghi(p, v):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(v, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def _chuan_bi(a):
    from danhgia.hop_dong import kiem as kiem_hop_dong

    hop_dong = {}
    for muc in a.hop_dong:
        he, _, duong = muc.partition("=")
        hd = _doc(duong)
        loi = kiem_hop_dong(hd)
        if loi or hd["dinh_danh"]["he"] != he or he in hop_dong:
            print(f"LỖI hợp đồng {he}: " + ("; ".join(loi[:3]) if loi else "tên hệ không khớp dinh_danh.he hoặc trùng"))
            return 1
        hop_dong[he] = hd
    g3, g4 = _doc(a.g3), _doc(a.g4)
    tt = mu.chuan_bi(luat.doc_vang(g3, g4), luat.doc_nut(hop_dong), ma_sach=g3["ma_sach"], seed=a.seed,
                     nguong_cau=a.nguong_cau, nguong_gan=a.nguong_gan, nguong_jaccard=a.nguong_jaccard, k_ung_vien=a.k_ung_vien, k_ung_vien_da_can=a.k_ung_vien_da_can)
    d = Path(a.ra)
    _ghi(d / "chuan-bi.json", tt)
    mu.sinh_phieu(tt, d / "phieu-mu.xlsx", nguoi="C")
    b = tt["bao_cao"]
    print(f"{b['so_vang']} khái niệm vàng, {b['so_nut']} node ({b['so_nut_khac_nhau']} khác nhau về chữ); "
          f"căn tự động {b['so_vang_can_tu_dong']}/{b['so_vang']} khái niệm vàng ({b['so_hang_tu_dong']} cặp); "
          f"phán tay {b['so_ca_phan_tay']} ca; không ứng viên (khong_khop mặc định) {b['so_vang_khong_ung_vien']}")
    return 0


def _doc_phan(a):
    d = Path(a.thu_muc)
    tt = _doc(d / "chuan-bi.json")
    phan, loi = mu.doc_phieu(a.phieu, tt)
    if loi:
        print("\n".join(f"LỖI {x}" for x in loi) + f"\n{len(loi)} lỗi: gửi phiếu lại, không sửa hộ")
        return 1
    can, nhat_ky = mu.bang_can(tt, phan)
    _ghi(d / "can.json", can)
    _ghi(d / "nhat-ky.json", nhat_ky)
    print(f"bảng căn {len(can['hang'])} dòng ({len(tt['tu_dong'])} từ luật, {len(can['hang']) - len(tt['tu_dong'])} phán tay)")
    return 0


def _phieu_kiem(a):
    d = Path(a.thu_muc)
    tt = _doc(d / "chuan-bi.json")
    chon = kiem.chon_kiem([p["ma_phan"] for p in tt["phieu"]], seed=a.seed, ti_le=a.ti_le)
    mu.sinh_phieu(tt, a.ra, nguoi="K", chon=chon)
    _ghi(d / "mau-kiem.json", {"seed": a.seed, "ti_le": a.ti_le, "ma_phan": chon})
    print(f"phiếu kiểm {len(chon)}/{len(tt['phieu'])} ca")
    return 0


def _doc_kiem(a):
    d = Path(a.thu_muc)
    tt = _doc(d / "chuan-bi.json")
    phan_kiem, loi = mu.doc_phieu(a.phieu, tt)
    if loi:
        print("\n".join(f"LỖI {x}" for x in loi))
        return 1
    goc = {h["ma_phan"]: h for h in _doc(d / "can.json")["hang"] if h["nguon_quyet_dinh"] == "phan_tay"}
    print(json.dumps(kiem.dong_thuan(goc, phan_kiem), ensure_ascii=False, indent=1))
    return 0


def _tach(a):
    _ghi(a.ra, mu.tach_theo_he(_doc(Path(a.thu_muc) / "can.json"), a.he))
    return 0


def them_lenh(parser):
    sub = parser.add_subparsers(dest="viec", required=True)

    p = sub.add_parser("chuan-bi", help="luật tự động và phiếu mù")
    p.add_argument("--g3", required=True)
    p.add_argument("--g4", required=True)
    p.add_argument("--hop-dong", nargs="+", required=True, help="<he>=<tệp hợp đồng>, mỗi hệ một mục")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--nguong-cau", type=float, default=luat.NGUONG_CAU_MAC_DINH)
    p.add_argument("--nguong-gan", type=float, default=luat.NGUONG_GAN_MAC_DINH)
    p.add_argument("--nguong-jaccard", type=float, default=luat.NGUONG_JACCARD_MAC_DINH)
    p.add_argument("--k-ung-vien", type=int, default=luat.K_UNG_VIEN_MAC_DINH,
                   help="khái niệm vàng chưa căn bằng luật: đưa vào phiếu tối đa k node gần nhất (mặc định 3)")
    p.add_argument("--k-ung-vien-da-can", type=int, default=luat.K_UNG_VIEN_DA_CAN_MAC_DINH,
                   help="khái niệm vàng đã căn bằng luật: tối đa k node chưa căn gần nhất (mặc định 1)")
    p.add_argument("--ra", required=True)
    p.set_defaults(chay=_chuan_bi)

    p = sub.add_parser("doc-phan", help="đọc phiếu mù đã phán")
    p.add_argument("--thu-muc", required=True)
    p.add_argument("--phieu", required=True)
    p.set_defaults(chay=_doc_phan)

    p = sub.add_parser("phieu-kiem", help="phiếu kiểm 20%")
    p.add_argument("--thu-muc", required=True)
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--ti-le", type=float, default=kiem.TI_LE_MAC_DINH)
    p.add_argument("--ra", required=True)
    p.set_defaults(chay=_phieu_kiem)

    p = sub.add_parser("doc-kiem", help="đọc phiếu kiểm, tính đồng ý")
    p.add_argument("--thu-muc", required=True)
    p.add_argument("--phieu", required=True)
    p.set_defaults(chay=_doc_kiem)

    p = sub.add_parser("tach", help="bảng căn riêng một hệ")
    p.add_argument("--thu-muc", required=True)
    p.add_argument("--he", required=True)
    p.add_argument("--ra", required=True)
    p.set_defaults(chay=_tach)
