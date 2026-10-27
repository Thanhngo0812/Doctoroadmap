"""Lệnh con `phieu-g4` của `python -m danhgia` (kho chốt G3 -> phiếu G4 -> vàng G4).

  sinh          kho chốt + manifest -> phiếu G4 trống (Excel) cho một người
  kiem          phiếu đã điền -> JSON thô `danh-gia-g4-1` (hoặc danh sách lỗi, mã thoát 1)
  can           kho chốt + hai JSON thô -> bản căn (JSON)
  bat-dong      bản căn -> hai phiếu bất đồng (mỗi người một tệp)
  kiem-bat-dong phiếu bất đồng đã điền -> lỗi (nếu có)
  chot          bản căn + hai phiếu bất đồng đã điền -> vàng chính, hợp, giao (JSON)
  dem           bản căn (và vàng, nếu có) -> số đếm đồng thuận, có và không có tín dụng bắc cầu
"""

import json
from pathlib import Path

from danhgia.phieu import bat_dong, bat_dong_g4, g4
from danhgia.phieu.can_g4 import can_g4
from danhgia.phieu.kiem import NGUONG_CAU_MAC_DINH
from danhgia.phieu.kiem_g4 import kiem_phieu_g4
from danhgia.phieu.trang import doc_trang
from danhgia.vang.g4 import chot_g4, dem_g4


def _doc(p: str) -> dict:
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _ghi(p: str, d: dict) -> None:
    Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _sinh(a) -> int:
    g4.sinh_phieu_g4(_doc(a.manifest), _doc(a.kho), a.nguoi, a.ra, so_dong=a.so_dong)
    print(f"đã ghi {a.ra}")
    return 0


def _kiem(a) -> int:
    kq = kiem_phieu_g4(a.phieu, _doc(a.manifest), _doc(a.kho), doc_trang(a.pdf), nguong=a.nguong)
    for c in kq.canh_bao:
        print("CẢNH BÁO", c)
    for e in kq.loi:
        print("LỖI", e)
    if not kq.ok:
        print(f"{len(kq.loi)} lỗi: gửi phiếu lại cho người gán, không sửa hộ")
        return 1
    if a.ra:
        _ghi(a.ra, kq.du_lieu)
    print(f"phiếu hợp lệ: {len(kq.du_lieu['quan_he'])} quan hệ, {len(kq.canh_bao)} cảnh báo")
    return 0


def _can(a) -> int:
    can = can_g4(_doc(a.a), _doc(a.b), _doc(a.kho))
    _ghi(a.ra, can)
    d = dem_g4(can)
    for ten in ("khong_bac_cau", "bac_cau"):
        t = d[ten]["tong"]["tong"]
        print(f"{ten}: cả hai {t['a']}, chỉ {can['nguoi'][0]} {t['b']}, chỉ {can['nguoi'][1]} {t['c']}, F1 {t['f1']}")
    print(f"{len(bat_dong_g4.tao_muc_g4(can))} mục bất đồng")
    return 0


def _bat_dong(a) -> int:
    can = _doc(a.can)
    Path(a.ra_dir).mkdir(parents=True, exist_ok=True)
    for nguoi in can["nguoi"]:
        bat_dong_g4.sinh_phieu_bat_dong_g4(can, nguoi, Path(a.ra_dir) / f"bat-dong-g4-{nguoi}.xlsx")
    print(f"{len(bat_dong_g4.tao_muc_g4(can))} mục bất đồng, đã ghi 2 phiếu vào {a.ra_dir}")
    return 0


def _kiem_bat_dong(a) -> int:
    loi = bat_dong_g4.kiem_phieu_bat_dong_g4(_doc(a.can), bat_dong.doc_phieu_bat_dong(a.phieu))
    for e in loi:
        print("LỖI", e)
    return 1 if loi else 0


def _chot(a) -> int:
    can = _doc(a.can)
    quyet_dinh = {}
    for p in (a.a, a.b):
        doc = bat_dong.doc_phieu_bat_dong(p)
        loi = bat_dong_g4.kiem_phieu_bat_dong_g4(can, doc)
        for e in loi:
            print("LỖI", p, e)
        if loi:
            return 1
        quyet_dinh[doc["nguoi"]] = doc["quyet_dinh"]
    vang = chot_g4(can, quyet_dinh)
    _ghi(a.ra, vang)
    print(json.dumps({k: len(vang[k]) for k in ("vang_chinh", "vang_hop", "vang_giao", "kien_thuc", "tranh_chap", "loai")}))
    return 0


def _dem(a) -> int:
    print(json.dumps(dem_g4(_doc(a.can)), ensure_ascii=False, indent=2))
    return 0


def them_lenh(parser) -> None:
    sub = parser.add_subparsers(dest="viec", required=True)

    p = sub.add_parser("sinh", help="sinh phiếu G4 trống")
    p.add_argument("--manifest", required=True)
    p.add_argument("--kho", required=True, help="kho chốt G3 (JSON)")
    p.add_argument("--nguoi", required=True)
    p.add_argument("--ra", required=True)
    p.add_argument("--so-dong", type=int, default=g4.SO_DONG_MAC_DINH)
    p.set_defaults(chay=_sinh)

    p = sub.add_parser("kiem", help="kiểm phiếu đã điền, đọc ra JSON thô")
    p.add_argument("--manifest", required=True)
    p.add_argument("--kho", required=True)
    p.add_argument("--pdf", required=True)
    p.add_argument("--phieu", required=True)
    p.add_argument("--ra")
    p.add_argument("--nguong", type=float, default=NGUONG_CAU_MAC_DINH)
    p.set_defaults(chay=_kiem)

    p = sub.add_parser("can", help="căn hai JSON thô")
    p.add_argument("--kho", required=True)
    p.add_argument("--a", required=True)
    p.add_argument("--b", required=True)
    p.add_argument("--ra", required=True)
    p.set_defaults(chay=_can)

    p = sub.add_parser("bat-dong", help="sinh phiếu bất đồng cho hai người")
    p.add_argument("--can", required=True)
    p.add_argument("--ra-dir", required=True)
    p.set_defaults(chay=_bat_dong)

    p = sub.add_parser("kiem-bat-dong", help="kiểm một phiếu bất đồng đã điền")
    p.add_argument("--can", required=True)
    p.add_argument("--phieu", required=True)
    p.set_defaults(chay=_kiem_bat_dong)

    p = sub.add_parser("chot", help="chốt vàng từ hai phiếu bất đồng đã điền")
    p.add_argument("--can", required=True)
    p.add_argument("--a", required=True)
    p.add_argument("--b", required=True)
    p.add_argument("--ra", required=True)
    p.set_defaults(chay=_chot)

    p = sub.add_parser("dem", help="số đếm đồng thuận")
    p.add_argument("--can", required=True)
    p.set_defaults(chay=_dem)
