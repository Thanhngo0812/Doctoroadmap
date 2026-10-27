"""Lệnh con `phieu-g3` của `python -m danhgia`.

  sinh          manifest -> phiếu G3 trống (Excel) cho một người
  kiem          phiếu đã điền -> JSON thô `danh-gia-g3-1` (hoặc danh sách lỗi, mã thoát 1)
  can           hai JSON thô -> bản căn (JSON)
  bat-dong      bản căn -> hai phiếu bất đồng (mỗi người một tệp)
  kiem-bat-dong phiếu bất đồng đã điền -> lỗi (nếu có)
  chot          bản căn + hai phiếu bất đồng đã điền -> kho chốt (JSON)
  dem           bản căn (và kho chốt, nếu có) -> số đếm đồng thuận
"""

import json
from pathlib import Path

from danhgia.phieu import bat_dong, g3
from danhgia.phieu.can import can_hai_ban
from danhgia.phieu.kiem import NGUONG_CAU_MAC_DINH, kiem_phieu
from danhgia.phieu.trang import doc_trang
from danhgia.vang.g3 import chot, dem_dong_thuan, dem_kho


def _doc(p: str) -> dict:
    return json.loads(Path(p).read_text(encoding="utf-8"))


def _ghi(p: str, d: dict) -> None:
    Path(p).write_text(json.dumps(d, ensure_ascii=False, indent=2, sort_keys=False) + "\n", encoding="utf-8")


def _sinh(a) -> int:
    chuong = a.chuong.split(",") if a.chuong else None
    g3.sinh_phieu(_doc(a.manifest), a.nguoi, a.ra, so_dong=a.so_dong, chuong=chuong)
    print(f"đã ghi {a.ra}")
    return 0


def _kiem(a) -> int:
    kq = kiem_phieu(a.phieu, _doc(a.manifest), doc_trang(a.pdf), nguong=a.nguong)
    for c in kq.canh_bao:
        print("CẢNH BÁO", c)
    for e in kq.loi:
        print("LỖI", e)
    if not kq.ok:
        print(f"{len(kq.loi)} lỗi: gửi phiếu lại cho người gán, không sửa hộ")
        return 1
    if a.ra:
        _ghi(a.ra, kq.du_lieu)
    print(f"phiếu hợp lệ: {len(kq.du_lieu['khai_niem'])} khái niệm, {len(kq.canh_bao)} cảnh báo")
    return 0


def _can(a) -> int:
    can = can_hai_ban(_doc(a.a), _doc(a.b))
    _ghi(a.ra, can)
    d = dem_dong_thuan(can)["tong"]
    print(f"khớp {d['a']}, chỉ {can['nguoi'][0]} {d['b']}, chỉ {can['nguoi'][1]} {d['c']}, cặp gần {len(can['cap_gan'])}")
    return 0


def _bat_dong(a) -> int:
    can = _doc(a.can)
    Path(a.ra_dir).mkdir(parents=True, exist_ok=True)
    for nguoi in can["nguoi"]:
        bat_dong.sinh_phieu_bat_dong(can, nguoi, Path(a.ra_dir) / f"bat-dong-{nguoi}.xlsx")
    print(f"{len(bat_dong.tao_muc(can))} mục bất đồng, đã ghi 2 phiếu vào {a.ra_dir}")
    return 0


def _kiem_bat_dong(a) -> int:
    loi = bat_dong.kiem_phieu_bat_dong(_doc(a.can), bat_dong.doc_phieu_bat_dong(a.phieu))
    for e in loi:
        print("LỖI", e)
    return 1 if loi else 0


def _chot(a) -> int:
    can = _doc(a.can)
    quyet_dinh = {}
    for p in (a.a, a.b):
        doc = bat_dong.doc_phieu_bat_dong(p)
        loi = bat_dong.kiem_phieu_bat_dong(can, doc)
        for e in loi:
            print("LỖI", p, e)
        if loi:
            return 1
        quyet_dinh[doc["nguoi"]] = doc["quyet_dinh"]
    kho = chot(can, quyet_dinh)
    _ghi(a.ra, kho)
    print(json.dumps(dem_kho(kho)["tong"], ensure_ascii=False))
    return 0


def _dem(a) -> int:
    ket_qua = {"dong_thuan_truoc_hoi_y": dem_dong_thuan(_doc(a.can))}
    if a.kho:
        ket_qua["kho_chot"] = dem_kho(_doc(a.kho))
    print(json.dumps(ket_qua, ensure_ascii=False, indent=2))
    return 0


def them_lenh(parser) -> None:
    sub = parser.add_subparsers(dest="viec", required=True)

    p = sub.add_parser("sinh", help="sinh phiếu G3 trống")
    p.add_argument("--manifest", required=True)
    p.add_argument("--nguoi", required=True, help="mã ẩn danh của người gán, ví dụ T1-a")
    p.add_argument("--ra", required=True)
    p.add_argument("--so-dong", type=int, default=g3.SO_DONG_MAC_DINH)
    p.add_argument("--chuong", help="danh sách chương cách nhau dấu phẩy; mặc định các chương bốc trong manifest")
    p.set_defaults(chay=_sinh)

    p = sub.add_parser("kiem", help="kiểm phiếu đã điền, đọc ra JSON thô")
    p.add_argument("--manifest", required=True)
    p.add_argument("--pdf", required=True)
    p.add_argument("--phieu", required=True)
    p.add_argument("--ra", help="JSON thô (chỉ ghi khi phiếu hợp lệ)")
    p.add_argument("--nguong", type=float, default=NGUONG_CAU_MAC_DINH, help="ngưỡng khớp mờ câu định nghĩa (chỉ cảnh báo)")
    p.set_defaults(chay=_kiem)

    p = sub.add_parser("can", help="căn hai JSON thô")
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

    p = sub.add_parser("chot", help="chốt kho từ hai phiếu bất đồng đã điền")
    p.add_argument("--can", required=True)
    p.add_argument("--a", required=True)
    p.add_argument("--b", required=True)
    p.add_argument("--ra", required=True)
    p.set_defaults(chay=_chot)

    p = sub.add_parser("dem", help="số đếm đồng thuận")
    p.add_argument("--can", required=True)
    p.add_argument("--kho")
    p.set_defaults(chay=_dem)

