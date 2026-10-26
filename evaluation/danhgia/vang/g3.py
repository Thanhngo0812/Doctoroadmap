"""Vàng G3: luật chốt ba nhánh, kho chốt có mã `G-<ma_sach>-<nnn>` ổn định, số đếm đồng thuận."""

from danhgia.phieu import bat_dong
from danhgia.phieu.can import NGUONG_CAU, _cung_trang_giong_cau
from danhgia.phieu.g3 import SCHEMA
from danhgia.ten import chuan_hoa

_CUOI = 10**9


def dem_dong_thuan(can: dict) -> dict:
    """Trước hội ý: a = cả hai liệt kê (khớp tự động), b = chỉ người thứ nhất, c = chỉ người thứ hai."""
    ent = can["khai_niem"]

    def f1(a: int, b: int, c: int):
        return 2 * a / (2 * a + b + c) if (a + b + c) else None

    theo = {}
    for ch in can["chuong"]:
        a = sum(1 for k in can["khop"] if k["chuong"] == ch)
        b = sum(1 for m in can["chi_a"] if ent["a"][m]["chuong"] == ch)
        c = sum(1 for m in can["chi_b"] if ent["b"][m]["chuong"] == ch)
        theo[ch] = {"a": a, "b": b, "c": c, "f1": f1(a, b, c)}
    a, b, c = (sum(v[k] for v in theo.values()) for k in "abc")
    return {"theo_chuong": theo, "tong": {"a": a, "b": b, "c": c, "f1": f1(a, b, c)}}


def dem_kho(kho: dict) -> dict:
    theo = {ch: {"vao_kho": 0, "loai": 0, "tranh_chap": 0, "trang_thai_tranh_chap": 0} for ch in kho["chuong"]}
    for k in kho["khai_niem"]:
        theo[k["chuong"]]["vao_kho"] += 1
        theo[k["chuong"]]["trang_thai_tranh_chap"] += k["trang_thai"] is None
    for k in kho["loai"]:
        theo[k["chuong"]]["loai"] += 1
    for k in kho["tranh_chap"]:
        theo[k["chuong"]]["tranh_chap"] += 1
    return {"theo_chuong": theo, "tong": {x: sum(v[x] for v in theo.values()) for x in ("vao_kho", "loai", "tranh_chap", "trang_thai_tranh_chap")}}


def _gop(ea: dict, eb: dict, nguoi: list[str], chon_trang_thai: dict | None) -> dict:
    """Gộp hai khái niệm khớp. `ea` là của người có mã nhỏ hơn. `chon_trang_thai` là lựa chọn hội ý của từng người, nếu có mục."""
    da_co = {chuan_hoa(ea["ten"])}
    ten_khac = []
    for t in [*ea["ten_khac"], eb["ten"], *eb["ten_khac"]]:
        if chuan_hoa(t) not in da_co:
            da_co.add(chuan_hoa(t))
            ten_khac.append(t)
    gop = {**ea, "ten_khac": ten_khac, "khong_chac": ea["khong_chac"] or eb["khong_chac"],
           "ghi_chu": " | ".join(x for x in (ea["ghi_chu"], eb["ghi_chu"]) if x)}
    if not ea["dinh_nghia"]["cau"] and eb["dinh_nghia"]["cau"]:
        gop["dinh_nghia"] = dict(eb["dinh_nghia"])
    else:
        gop["dinh_nghia"] = dict(ea["dinh_nghia"])
        if eb["dinh_nghia"]["cau"] and not _cung_trang_giong_cau(ea, eb, NGUONG_CAU):
            gop["dinh_nghia_khac"] = [dict(eb["dinh_nghia"])]
    if ea["trang_thai"] == eb["trang_thai"]:
        gop["trang_thai"] = ea["trang_thai"]
    elif len(set(chon_trang_thai.values())) == 1:
        gop["trang_thai"] = next(iter(chon_trang_thai.values()))
    else:
        gop["trang_thai"] = None
        gop["trang_thai_tranh_chap"] = dict(chon_trang_thai)
    return gop


def chot(can: dict, quyet_dinh: dict[str, dict]) -> dict:
    """Luật chốt: cả hai giữ -> kho; cả hai bỏ -> loại; còn lại -> tranh chấp."""
    nguoi = can["nguoi"]
    muc = bat_dong.tao_muc(can)
    for code in nguoi:
        qd = quyet_dinh.get(code, {})
        for m in muc:
            q = qd.get(m["id"])
            if not q or q.get("lua_chon") not in bat_dong.LUA_CHON[m["loai"]]:
                raise ValueError(f"{code}: {m['id']}: thiếu hoặc sai lựa chọn")
            if not str(q.get("ly_do", "")).strip():
                raise ValueError(f"{code}: {m['id']}: ly_do trống")
    ent = can["khai_niem"]
    gop = [(k["a"], k["b"]) for k in can["khop"]]
    dung_a, dung_b = {a for a, _ in gop}, {b for _, b in gop}
    for m in muc:
        if m["loai"] == "cap_gan" and all(quyet_dinh[c][m["id"]]["lua_chon"] == "cung" for c in nguoi):
            if m["a"] not in dung_a and m["b"] not in dung_b:
                gop.append((m["a"], m["b"]))
                dung_a.add(m["a"])
                dung_b.add(m["b"])
    vao = []
    muc_tt = {(m["a"], m["b"]): m["id"] for m in muc if m["loai"] == "trang_thai"}
    for ma_a, ma_b in gop:
        id_tt = muc_tt.get((ma_a, ma_b))
        chon = {c: quyet_dinh[c][id_tt]["lua_chon"] for c in nguoi} if id_tt else None
        e = _gop(ent["a"][ma_a], ent["b"][ma_b], nguoi, chon)
        e["nguon"] = [f"{nguoi[0]}:{ma_a}", f"{nguoi[1]}:{ma_b}"]
        vao.append(e)
    loai, tranh_chap = [], []
    for m in muc:
        if m["loai"] != "rieng" or m["muc"] in (dung_a if m["ben"] == "a" else dung_b):
            continue  # mục đã gộp: giữ/bỏ của nó không còn ý nghĩa
        e = dict(ent[m["ben"]][m["muc"]])
        e["nguon"] = [f"{nguoi[0] if m['ben'] == 'a' else nguoi[1]}:{m['muc']}"]
        lua = {c: quyet_dinh[c][m["id"]]["lua_chon"] for c in nguoi}
        if all(v == "giu" for v in lua.values()):
            vao.append(e)
        elif all(v == "bo" for v in lua.values()):
            loai.append(e)
        else:
            tranh_chap.append({"chuong": e["chuong"], "muc": e, "quyet_dinh": {c: dict(quyet_dinh[c][m["id"]]) for c in nguoi}})
    thu_tu = {ch: i for i, ch in enumerate(can["chuong"])}
    vao.sort(key=lambda e: (thu_tu[e["chuong"]], e["dinh_nghia"]["trang"] if e["dinh_nghia"]["trang"] is not None else _CUOI,
                            chuan_hoa(e["ten"]), e["nguon"]))
    khai_niem = [{**e, "ma": f"G-{can['ma_sach']}-{i:03d}", "ma_dong_goc": e["ma"]} for i, e in enumerate(vao, start=1)]
    return {"schema": SCHEMA, "ma_sach": can["ma_sach"], "nguoi_gan": "hoi-y",
            "phien_ban_huong_dan": can["phien_ban_huong_dan"], "chuong": can["chuong"],
            "khai_niem": khai_niem, "tranh_chap": tranh_chap, "loai": loai}
