"""Luật căn tự động (spec mục 7), chạy theo thứ tự và không dùng ký hiệu:

1. `luat_ten`: tên hoặc tên khác trùng sau chuẩn hoá, so theo ranh giới âm tiết (`ten.am_tiet`), không phải chuỗi con.
2. `luat_cau_neo`: câu neo của node giống câu định nghĩa vàng (độ giống ký tự sau chuẩn hoá >= `nguong_cau`) và cùng trang.
3. Ký hiệu (`μ`, `x`, `t α`, `P(A|B)`, một chữ cái đơn; `F` khác `f`) không bao giờ dùng để căn hay để đề cử ứng viên.

Cặp còn lại là **ứng viên gần** (rồi giữ tối đa `k_ung_vien` node gần nhất mỗi khái niệm vàng) khi tên này chứa tên kia liền kề theo âm tiết, hoặc Jaccard âm tiết >= `nguong_jaccard`, hoặc cùng trang
và câu giống nhau >= `nguong_gan`. Khái niệm vàng không có ứng viên gần là `khong_khop` mặc định (không có dòng trong bảng căn).
"""
import re
import unicodedata

from danhgia.cham.can import khoa_vang
from danhgia.ten import am_tiet, do_giong

NGUONG_CAU_MAC_DINH = 0.9   # Claude chốt giá trị vào giao thức ở DG-18
NGUONG_GAN_MAC_DINH = 0.5
NGUONG_JACCARD_MAC_DINH = 0.34
K_UNG_VIEN_MAC_DINH = 3     # số node gần nhất tối đa mỗi khái niệm vàng đưa vào phiếu; chưa hiệu chỉnh, Claude chốt ở DG-18
_CHU = re.compile(r"[^\W\d_]+")


def la_ky_hieu(ten):
    """Ký hiệu: không có từ nào dài từ hai chữ cái trở lên (chữ cái đơn, chữ Hy Lạp, `P(A|B)`, `t α`). `ML` là alias, không phải ký hiệu."""
    return not any(len(t) >= 2 for t in _CHU.findall(unicodedata.normalize("NFC", ten or "")))


def khoa_ten(ten, ten_khac=()):
    """Tập khoá âm tiết của các tên không phải ký hiệu."""
    return {k for k in (am_tiet(t) for t in [ten, *ten_khac] if not la_ky_hieu(t)) if k}


def _chua(a, b):
    n = len(b)
    return 0 < n <= len(a) and any(a[i : i + n] == b for i in range(len(a) - n + 1))


def trung_cau(trang_a, cau_a, trang_b, cau_b, nguong):
    if trang_a is None or trang_a != trang_b or not am_tiet(cau_a) or not am_tiet(cau_b):
        return False
    return do_giong(cau_a, cau_b) >= nguong


def gan_ten(ka, kb, nguong_jaccard):
    for x in ka:
        for y in kb:
            if _chua(x, y) or _chua(y, x) or len(set(x) & set(y)) / len(set(x) | set(y)) >= nguong_jaccard:
                return True
    return False


def doc_vang(g3, g4):
    """Khái niệm vàng: kho chốt G3 và nguồn "ngoài" của G4 (khử trùng theo (tên, trang))."""
    ds = [{"khoa": k["ma"], "ten": k["ten"], "ten_khac": list(k["ten_khac"]), "trang": k["dinh_nghia"]["trang"],
           "cau": k["dinh_nghia"]["cau"]} for k in g3["khai_niem"]]
    thay = set()
    for q in g4["quan_he"]:
        if isinstance(q["nguon"], dict):
            khoa = khoa_vang(q["nguon"])
            if khoa not in thay:
                thay.add(khoa)
                ds.append({"khoa": khoa, "ten": q["nguon"]["ngoai"]["ten"], "ten_khac": [],
                           "trang": q["nguon"]["ngoai"].get("trang"), "cau": None})
    return ds


def doc_nut(hop_dong_theo_he, *, bao_gom_bi_loai=False):
    """Node của mọi hệ, id `<he>:<ma>`. Bỏ node bị loại hoặc đã gộp vào node khác (không còn trong đồ thị) trừ khi `bao_gom_bi_loai`."""
    ds = []
    for he, hd in hop_dong_theo_he.items():
        for k in hd["khai_niem"]:
            if not bao_gom_bi_loai and (k["bi_loai"] or k["da_gop"]):
                continue
            neo = k["cau_neo"] or {}
            ds.append({"id": f"{he}:{k['ma']}", "ten": k["ten"], "ten_khac": list(k["ten_khac"] or []),
                       "trang": neo.get("trang"), "cau": neo.get("cau")})
    return ds


def _giong_ten(g, n):
    """Độ giống tên lớn nhất giữa các tên không phải ký hiệu của vàng và của node."""
    return max((do_giong(a, b) for a in [g["ten"], *g["ten_khac"]] if not la_ky_hieu(a)
                for b in [n["ten"], *n["ten_khac"]] if not la_ky_hieu(b)), default=0.0)


def _giong_cau(g, n):
    return do_giong(g["cau"], n["cau"]) if am_tiet(g["cau"]) and am_tiet(n["cau"]) else 0.0


def can_tu_dong(vang, nut, *, nguong_cau=NGUONG_CAU_MAC_DINH, nguong_gan=NGUONG_GAN_MAC_DINH,
                nguong_jaccard=NGUONG_JACCARD_MAC_DINH, k_ung_vien=K_UNG_VIEN_MAC_DINH):
    """`vang`: [{khoa, ten, ten_khac, trang, cau}]; `nut`: [{id, ten, ten_khac, trang, cau}].
    Trả `hang` (cặp căn bằng luật, quan hệ `khop`), `ung_vien` (cặp để phán tay) và `khong_ung_vien` (khoá vàng).

    Ứng viên của mỗi khái niệm vàng: tối đa `k_ung_vien` node gần nhất, xếp theo độ giống tên rồi độ giống câu. Khái niệm vàng đã căn bằng
    luật vẫn có ứng viên (để bắt `may_hep_hon` khi máy tách khái niệm) nhưng chỉ trong các node chưa căn bằng luật với khái niệm vàng nào."""
    khoa_nut = {n["id"]: khoa_ten(n["ten"], n["ten_khac"]) for n in nut}
    hang, gan, da_can = [], {}, set()
    for g in vang:
        kg = khoa_ten(g["ten"], g["ten_khac"])
        gan[g["khoa"]] = {"can": False, "ds": []}
        for n in nut:
            chung = kg & khoa_nut[n["id"]]
            if chung:
                luat, chi_tiet = "luat_ten", "tên trùng sau chuẩn hoá: " + " ".join(sorted(chung)[0])
            elif trung_cau(g["trang"], g["cau"], n["trang"], n["cau"], nguong_cau):
                luat = "luat_cau_neo"
                chi_tiet = f"câu neo giống câu định nghĩa vàng cùng trang {g['trang']} (độ giống {do_giong(g['cau'], n['cau']):.3f} >= {nguong_cau})"
            elif gan_ten(kg, khoa_nut[n["id"]], nguong_jaccard) or trung_cau(g["trang"], g["cau"], n["trang"], n["cau"], nguong_gan):
                gan[g["khoa"]]["ds"].append(n)
                continue
            else:
                continue
            hang.append({"vang": g["khoa"], "may": n["id"], "quan_he": "khop", "nguon_quyet_dinh": luat,
                         "ma_phan": None, "ghi_chu": "", "nhat_ky": chi_tiet})
            gan[g["khoa"]]["can"] = True
            da_can.add(n["id"])
    ung_vien, khong = [], []
    for g in vang:
        ds = gan[g["khoa"]]["ds"]
        if gan[g["khoa"]]["can"]:
            ds = [n for n in ds if n["id"] not in da_can]
        ds = sorted(ds, key=lambda n: (-_giong_ten(g, n), -_giong_cau(g, n), n["id"]))[:k_ung_vien]
        ung_vien += [{"vang": g["khoa"], "node": n["id"]} for n in ds]
        if not ds and not gan[g["khoa"]]["can"]:
            khong.append(g["khoa"])
    return {"hang": hang, "ung_vien": ung_vien, "khong_ung_vien": khong}
