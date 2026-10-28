"""Tính kết quả G5 từ phán của từng người: precision hiệu chỉnh (có CI Wilson), tỉ lệ bác câu đối chứng, điểm rubric, so sánh cặp."""
from collections import Counter

from danhgia.thong_ke.kiem_dinh import sign_test
from danhgia.thong_ke.wilson import wilson


def precision_hieu_chinh(khop, du, dung, n_mau):
    """Precision hiệu chỉnh của một hệ.

    - `khop`: số cạnh máy khớp vàng; `du`: số cạnh dư (ngoài vàng); `dung`, `n_mau`: số "can" trên mẫu phán `n_mau` cạnh dư (n_mau = min(du, 100)).
    - Ước lượng cạnh dư đúng = (dung / n_mau) × du; precision = (khop + ước lượng) / (khop + du).
    - Khoảng: Wilson trên tỉ lệ mẫu rồi suy ra theo cùng công thức (cận trên và dưới của tỉ lệ nhân với du). Mẫu phủ hết cạnh dư thì không có sai số chọn mẫu:
      khoảng thu về một điểm. Không có cạnh máy nào thì precision là None."""
    tong = khop + du
    if tong == 0:
        return {"precision": None, "thap": None, "cao": None, "ti_le_mau": None, "uoc_luong_du_dung": None, "n_mau": n_mau}
    if du == 0:
        return {"precision": khop / tong, "thap": khop / tong, "cao": khop / tong, "ti_le_mau": None, "uoc_luong_du_dung": 0.0, "n_mau": 0}
    if n_mau <= 0:
        raise ValueError("có cạnh dư mà không có mẫu phán nào")
    p = dung / n_mau
    uoc = p * du
    if n_mau >= du:
        diem = (khop + dung) / tong
        thap = cao = diem
    else:
        lo, hi = wilson(dung, n_mau)
        thap, cao = (khop + lo * du) / tong, (khop + hi * du) / tong
    return {"precision": (khop + uoc) / tong, "thap": thap, "cao": cao, "ti_le_mau": p, "uoc_luong_du_dung": uoc, "n_mau": n_mau}


def ket_qua_mot_nguoi(trang_thai, phan):
    kq = {"a": dict(Counter(phan["a"].values()))}
    dem = {he: Counter() for he in trang_thai["he"]}
    dc = {"doi_chung_vang": Counter(), "doi_chung_ngau": Counter()}
    for h in trang_thai["nguoi"][phan["nguoi"]]["b"]:
        v = phan["b"][h["ma"]]
        if h["loai"] == "may":
            for he, so in h["canh"].items():
                dem[he]["n"] += so
                dem[he][v] += so
        else:
            dc[h["loai"]]["n"] += 1
            dc[h["loai"]][v] += 1
    kq["precision"] = {}
    for he, tk in trang_thai["b_thong_ke"].items():
        kq["precision"][he] = precision_hieu_chinh(tk["khop"], tk["du"], dem[he]["can"], dem[he]["n"]) | {
            "khong_can": dem[he]["khong_can"], "nguoc_chieu": dem[he]["nguoc_chieu"], "khop": tk["khop"], "du": tk["du"]}
    vang, ngau = dc["doi_chung_vang"], dc["doi_chung_ngau"]
    kq["doi_chung"] = {"vang": {"n": vang["n"], "bac": vang["n"] - vang["can"], "ti_le_bac": (vang["n"] - vang["can"]) / vang["n"] if vang["n"] else None},
                       "ngau": {"n": ngau["n"], "nhan": ngau["can"], "ti_le_nhan": ngau["can"] / ngau["n"] if ngau["n"] else None}}
    diem = {he: [] for he in trang_thai["he"]}
    for h in trang_thai["m"]:
        for he in h["he"]:
            diem[he].append(phan["m"][h["ma"]])
    kq["rubric"] = {he: {"n": len(d), "trung_binh": sum(d) / len(d) if d else None} for he, d in diem.items()}
    so_sanh = {}
    for h in trang_thai["nguoi"][phan["nguoi"]]["p"]:
        v = phan["p"][h["ma"]]
        doi = h["cap"].split("~")[1]
        thang = {"trai": h["trai_la"], "phai": h["phai_la"]}.get(v)
        d = so_sanh.setdefault(h["cap"], {"chinh_thang": 0, "doi_thang": 0, "hoa": 0})
        d["hoa" if thang is None else "chinh_thang" if thang == trang_thai["chinh"] else "doi_thang"] += 1
    for d in so_sanh.values():
        d["sign_test_p"] = sign_test(d["chinh_thang"], d["doi_thang"])
    kq["so_sanh"] = so_sanh
    return kq


def ket_qua(trang_thai, phan_theo_nguoi):
    """Kết quả từng người và trung bình precision của các người."""
    theo_nguoi = {n: ket_qua_mot_nguoi(trang_thai, dict(p, nguoi=n)) for n, p in phan_theo_nguoi.items()}
    tb = {}
    for he in trang_thai["he"]:
        gia = [k["precision"][he]["precision"] for k in theo_nguoi.values() if k["precision"][he]["precision"] is not None]
        tb[he] = sum(gia) / len(gia) if gia else None
    return {"theo_nguoi": theo_nguoi, "precision_trung_binh": tb}
