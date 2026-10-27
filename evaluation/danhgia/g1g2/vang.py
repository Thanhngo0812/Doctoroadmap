"""Vàng cuối G1/G2 từ phiếu sinh viên, gỡ lỗi cài bị bỏ sót, tỉ lệ bắt lỗi cài.

Một lỗi cài được tính là bắt được khi sinh viên đưa giá trị đúng của chính chỗ đó về như bản nháp trước khi cài:
- `doi_cap`, `gan_sai_vai_tro`: cấp (hay vai trò) sau duyệt bằng giá trị gốc, và hàng không bị xoá;
- `bo_tieu_de`: sheet Thêm có tiêu đề trùng ít nhất một mã dòng với tiêu đề bị bỏ.
Bỏ sót thì trả về giá trị nháp trước khi cài. Mọi sửa khác của sinh viên giữ nguyên (đó là phán đoán của họ); sửa ở tiêu đề không bị cài
được đếm riêng là `sua_ngoai_loi_cai`, không tính vào tỉ lệ bắt.
"""
import copy

from danhgia.g1g2 import kiem_cay
from danhgia.g1g2.kiem_cay import doi_so, tinh_cha
from danhgia.g1g2.loi_cai import LOAI


def _ti_le(bat, da_cai):
    return {"da_cai": da_cai, "bat": bat, "ti_le": bat / da_cai if da_cai else None}


def _dat(h, **truong):
    h.update(truong)
    h["vung"] = h["vai_tro"] if h["cap"] == 1 else None


def vang_cuoi(nhap_cai, so_loi, doc, dong, sach):
    """(vàng cuối, báo cáo bắt lỗi cài, lỗi của cây). Lỗi cây không rỗng nghĩa là sinh viên sửa ra cây hỏng: gửi phiếu lại."""
    vi_tri = {d["id"]: i for i, d in enumerate(dong)}
    sv = {h["khoa"]: h for h in doc["hang"]}
    khoa_loi = {x["khoa"] for x in so_loi}
    dong_goc_loi = [set(x["goc"]["dong"]) for x in so_loi if x["loai"] == "bo_tieu_de"]
    cur, sua_ngoai_loi_cai = [], 0
    for h in nhap_cai:
        k = h["dong"][0]
        d = sv.get(k, {"cap": h["cap"], "vai_tro": h["vai_tro"], "xoa": False})
        if k not in khoa_loi and (d["xoa"] or (d["cap"], d["vai_tro"]) != (h["cap"], h["vai_tro"])):
            sua_ngoai_loi_cai += 1
        if d["xoa"]:
            continue
        x = copy.deepcopy(h)
        _dat(x, cap=d["cap"], vai_tro=d["vai_tro"])
        cur.append(x)
    for i, t in enumerate(doc["them"]):
        if not any(set(t["dong"]) & g for g in dong_goc_loi):
            sua_ngoai_loi_cai += 1
        cur.append({"sach": sach, "id": f"n{i}", "dong": list(t["dong"]), "text": t["tieu_de"], "cap": t["cap"], "cha": None,
                    "vung": t["vai_tro"] if t["cap"] == 1 else None, "vai_tro": t["vai_tro"], "ghi_chu": ""})
    chi_tiet = []
    for x in so_loi:
        k, goc = x["khoa"], x["goc"]
        d = sv.get(k)
        if x["loai"] == "doi_cap":
            bat = bool(d) and not d["xoa"] and d["cap"] == goc["cap"]
        elif x["loai"] == "gan_sai_vai_tro":
            bat = bool(d) and not d["xoa"] and d["vai_tro"] == goc["vai_tro"]
        else:
            bat = any(set(t["dong"]) & set(goc["dong"]) for t in doc["them"])
        chi_tiet.append({"loai": x["loai"], "khoa": k, "bat": bat})
        if bat:
            continue
        if x["loai"] == "bo_tieu_de":
            moi = copy.deepcopy(goc)
            moi["id"] = f"g{k}"
            moi["cha"] = None
            cur.append(moi)
        else:
            dich = next((h for h in cur if h["dong"][0] == k), None)
            if dich is not None:  # hàng bị sinh viên xoá thì giữ phán đoán xoá của họ
                _dat(dich, **({"cap": goc["cap"]} if x["loai"] == "doi_cap" else {"vai_tro": goc["vai_tro"]}))
    cur.sort(key=lambda h: vi_tri[h["dong"][0]])
    muc = doi_so(tinh_cha(cur))
    loi = kiem_cay.kiem_cay(sach, muc, dong)
    bao_cao = _ti_le(sum(c["bat"] for c in chi_tiet), len(chi_tiet))
    bao_cao["theo_loai"] = {loai: _ti_le(sum(c["bat"] for c in chi_tiet if c["loai"] == loai),
                                         sum(c["loai"] == loai for c in chi_tiet))
                            for loai in LOAI if any(c["loai"] == loai for c in chi_tiet)}
    bao_cao.update(sua_ngoai_loi_cai=sua_ngoai_loi_cai, chi_tiet=chi_tiet, ma_sach=sach)
    return muc, bao_cao, loi


def tong_hop(bao_cao_theo_cuon):
    """Gộp báo cáo nhiều cuốn: tỉ lệ bắt theo cuốn, theo loại và chung."""
    theo_loai = {}
    for bc in bao_cao_theo_cuon.values():
        for loai, v in bc["theo_loai"].items():
            t = theo_loai.setdefault(loai, [0, 0])
            t[0] += v["bat"]
            t[1] += v["da_cai"]
    return {"theo_cuon": {ma: _ti_le(bc["bat"], bc["da_cai"]) for ma, bc in bao_cao_theo_cuon.items()},
            "theo_loai": {loai: _ti_le(*t) for loai, t in theo_loai.items()},
            "tong": _ti_le(sum(b["bat"] for b in bao_cao_theo_cuon.values()), sum(b["da_cai"] for b in bao_cao_theo_cuon.values()))}
