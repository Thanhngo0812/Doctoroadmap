"""Căn hai bản thô G4: hai quan hệ là một khi cùng đích và cùng nguồn (spec mục 6).

Nguồn là mã khái niệm kho chốt, hoặc nguồn "ngoài". Hai nguồn ngoài là một khi tên chuẩn hoá (theo âm tiết) giống nhau và trang
định nghĩa lệch tối đa 1 trang; trang trống chỉ khớp với trang trống. Kho chốt phải khớp `kho_chot_sha256` của cả hai bản.
"""

from danhgia.phieu.can import khoa_chuong
from danhgia.phieu.g4 import SCHEMA, kho_sha256
from danhgia.ten import am_tiet

SCHEMA_CAN = "danh-gia-g4-can-1"
SAI_LECH_TRANG_NGOAI = 1


def co_duong(do_thi: dict, tu, den) -> bool:
    """Có đường (một cạnh trở lên) theo chiều nguồn -> đích từ `tu` tới `den`; có tập đã thăm nên chịu được chu trình."""
    da_tham, hang = {tu}, [tu]
    while hang:
        nut = hang.pop()
        for ke in do_thi.get(nut, ()):
            if ke == den:
                return True
            if ke not in da_tham:
                da_tham.add(ke)
                hang.append(ke)
    return False


def do_thi_cua(canh: dict, chi_loai: str | None = None) -> dict:
    do_thi: dict = {}
    for e in canh.values():
        if chi_loai is None or e["loai"] == chi_loai:
            do_thi.setdefault(e["nguon_khoa"], set()).add(e["dich_khoa"])
    return do_thi


def _cum_nguon_ngoai(ban_a: dict, ban_b: dict) -> dict:
    """`{(tên âm tiết, trang): khoá}`; khoá ổn định, không phụ thuộc thứ tự đầu vào."""
    theo_ten: dict[tuple, set] = {}
    for ban in (ban_a, ban_b):
        for q in ban["quan_he"]:
            if isinstance(q["nguon"], dict):
                ng = q["nguon"]["ngoai"]
                theo_ten.setdefault(am_tiet(ng["ten"]), set()).add(ng["trang"])
    khoa = {}
    for ten, cac_trang in theo_ten.items():
        co_so = sorted(t for t in cac_trang if t is not None)
        cum, goc = [], None
        for t in co_so:
            if goc is None or t - goc > SAI_LECH_TRANG_NGOAI:
                goc = t
                cum.append(goc)
            khoa[(ten, t)] = f"ngoai:{' '.join(ten)}#{len(cum)}"
        if None in cac_trang:
            khoa[(ten, None)] = f"ngoai:{' '.join(ten)}#0"
    return khoa


def can_g4(ban_1: dict, ban_2: dict, kho: dict) -> dict:
    for ban in (ban_1, ban_2):
        if ban["schema"] != SCHEMA:
            raise ValueError(f"không phải {SCHEMA}")
    if ban_1["ma_sach"] != ban_2["ma_sach"]:
        raise ValueError(f"hai bản khác ma_sach: {ban_1['ma_sach']} và {ban_2['ma_sach']}")
    if ban_1["nguoi_gan"] == ban_2["nguoi_gan"]:
        raise ValueError(f"hai bản cùng nguoi_gan: {ban_1['nguoi_gan']}")
    sha = kho_sha256(kho)
    if ban_1["kho_chot_sha256"] != sha or ban_2["kho_chot_sha256"] != sha:
        raise ValueError("kho_chot_sha256 của phiếu không khớp kho chốt đang dùng")
    ban_a, ban_b = sorted((ban_1, ban_2), key=lambda b: b["nguoi_gan"])
    theo_ma = {k["ma"]: k for k in kho["khai_niem"]}
    cum = _cum_nguon_ngoai(ban_a, ban_b)
    thu_tu = {ch: i for i, ch in enumerate(sorted(kho["chuong"], key=khoa_chuong))}

    def chuan(ban: dict) -> dict:
        ket, khoa_da_co = {}, set()
        for q in ban["quan_he"]:
            if q["dich"] not in theo_ma or (isinstance(q["nguon"], str) and q["nguon"] not in theo_ma):
                raise ValueError(f"{ban['nguoi_gan']}: {q['ma']}: khái niệm không có trong kho chốt")
            if isinstance(q["nguon"], dict):
                ng = q["nguon"]["ngoai"]
                nguon_khoa = cum[(am_tiet(ng["ten"]), ng["trang"])]
            else:
                nguon_khoa = q["nguon"]
            khoa = (q["dich"], nguon_khoa)
            if khoa in khoa_da_co or q["ma"] in ket:
                raise ValueError(f"{ban['nguoi_gan']}: {q['ma']}: quan hệ hoặc mã dòng bị trùng")
            khoa_da_co.add(khoa)
            ket[q["ma"]] = {**q, "chuong": theo_ma[q["dich"]]["chuong"], "dich_khoa": q["dich"], "nguon_khoa": nguon_khoa}
        return ket

    canh_a, canh_b = chuan(ban_a), chuan(ban_b)

    def sap_xep(e: dict):
        return (thu_tu[e["chuong"]], e["dich_khoa"], e["nguon_khoa"], e["ma"])

    theo_khoa_b = {(e["dich_khoa"], e["nguon_khoa"]): ma for ma, e in canh_b.items()}
    khop, chi_a = [], []
    for ma, e in sorted(canh_a.items(), key=lambda kv: sap_xep(kv[1])):
        mb = theo_khoa_b.get((e["dich_khoa"], e["nguon_khoa"]))
        if mb is None:
            chi_a.append(ma)
        else:
            khop.append({"chuong": e["chuong"], "a": ma, "b": mb})
    da_khop_b = {k["b"] for k in khop}
    chi_b = [ma for ma, e in sorted(canh_b.items(), key=lambda kv: sap_xep(kv[1])) if ma not in da_khop_b]
    # Cạnh chỉ một người ghi mà đồ thị toàn `van_ban` của người kia có đường nguồn -> ... -> đích: đồng ý qua bắc cầu,
    # không vào phiếu bất đồng (hướng dẫn chỉ ghi quan hệ trực tiếp).
    van_ban_a, van_ban_b = do_thi_cua(canh_a, "van_ban"), do_thi_cua(canh_b, "van_ban")
    bao_ham = {
        "a": [ma for ma in chi_a if co_duong(van_ban_b, canh_a[ma]["nguon_khoa"], canh_a[ma]["dich_khoa"])],
        "b": [ma for ma in chi_b if co_duong(van_ban_a, canh_b[ma]["nguon_khoa"], canh_b[ma]["dich_khoa"])],
    }
    return {
        "schema": SCHEMA_CAN, "ma_sach": ban_a["ma_sach"], "kho_chot_sha256": sha,
        "nguoi": [ban_a["nguoi_gan"], ban_b["nguoi_gan"]], "chuong": sorted(kho["chuong"], key=khoa_chuong),
        "kho": {k["ma"]: {"ten": k["ten"], "chuong": k["chuong"], "trang_thai": k["trang_thai"]} for k in kho["khai_niem"]},
        "canh": {"a": canh_a, "b": canh_b}, "khop": khop, "chi_a": chi_a, "chi_b": chi_b, "bao_ham": bao_ham,
    }
