"""Vàng G4: luật chốt, ba vàng, số đếm đồng thuận (kể cả tín dụng bắc cầu kiểu PREAP).

Ba vàng (mỗi quan hệ là một cạnh nguồn -> đích):
- `vang_chinh`: cạnh đã thống nhất sau hội ý (cả hai cùng ghi, hoặc cả hai giữ) và có loại `van_ban`. Chỉ số chính chấm trên vàng này;
- `vang_hop`: mọi cạnh còn sống sau hội ý, gồm cạnh `kien_thuc`, cạnh loại tranh chấp (`loai: null`) và cạnh tranh chấp giữ/bỏ;
- `vang_giao`: cạnh cả hai cùng ghi từ đầu (không cần hội ý) và có loại `van_ban`.
`kien_thuc` liệt kê riêng các cạnh đã thống nhất loại `kien_thuc`, để báo riêng mức sách bỏ ngầm tiên quyết.
"""

from danhgia.phieu import bat_dong_g4
from danhgia.phieu.can_g4 import co_duong as _co_duong
from danhgia.phieu.can_g4 import do_thi_cua as _do_thi
from danhgia.phieu.g4 import SCHEMA, LOAI


def _f1(a: int, b: int, c: int):
    return 2 * a / (2 * a + b + c) if (a + b + c) else None


def _dem(a: int, b: int, c: int) -> dict:
    return {"a": a, "b": b, "c": c, "f1": _f1(a, b, c)}


def _dem_theo_chuong(can: dict, bac_cau: bool) -> dict:
    ca, cb = can["canh"]["a"], can["canh"]["b"]
    khoa_a = {(e["dich_khoa"], e["nguon_khoa"]): e for e in ca.values()}
    khoa_b = {(e["dich_khoa"], e["nguon_khoa"]): e for e in cb.values()}
    do_thi_a, do_thi_b = _do_thi(ca), _do_thi(cb)

    def duoc_tin_dung(khoa, do_thi_kia, kia) -> bool:
        # chỉ cạnh người kia hoàn toàn không ghi mới xét; đường phải theo chiều nguồn -> đích
        return bac_cau and khoa not in kia and _co_duong(do_thi_kia, khoa[1], khoa[0])

    ket = {}
    for ch in can["chuong"]:
        ket[ch] = {}
        for ten, loai in (("tong", None), *((l, l) for l in LOAI)):
            sa = {k for k, e in khoa_a.items() if e["chuong"] == ch and (loai is None or e["loai"] == loai)}
            sb = {k for k, e in khoa_b.items() if e["chuong"] == ch and (loai is None or e["loai"] == loai)}
            a, b, c = len(sa & sb), len(sa - sb), len(sb - sa)
            if bac_cau:
                tin_a = sum(1 for k in sa - sb if duoc_tin_dung(k, do_thi_b, khoa_b))
                tin_b = sum(1 for k in sb - sa if duoc_tin_dung(k, do_thi_a, khoa_a))
                a, b, c = a + tin_a + tin_b, b - tin_a, c - tin_b
            ket[ch][ten] = _dem(a, b, c)
    tong = {ten: _dem(*(sum(ket[ch][ten][k] for ch in ket) for k in "abc")) for ten in ("tong", *LOAI)}
    return {"theo_chuong": ket, "tong": tong}


def dem_g4(can: dict) -> dict:
    """(a, b, c) theo chương: cả hai ghi, chỉ người một, chỉ người hai; F1 = 2a/(2a+b+c), `None` khi không ai ghi gì.

    `tong` bỏ qua loại; `van_ban` và `kien_thuc` đếm theo loại mỗi người ghi (cạnh cả hai ghi nhưng khác loại là chỉ-một-người ở cả hai
    loại). Bản `bac_cau` coi cạnh một người ghi mà người kia có đường nguồn -> ... -> đích (không có cạnh trực tiếp) là đồng thuận.
    """
    bao_ham = {ch: sum(1 for ben, ds in (("a", can["bao_ham"]["a"]), ("b", can["bao_ham"]["b"])) for ma in ds
                       if can["canh"][ben][ma]["chuong"] == ch) for ch in can["chuong"]}
    return {"khong_bac_cau": _dem_theo_chuong(can, False), "bac_cau": _dem_theo_chuong(can, True),
            "bao_ham_bac_cau": {"theo_chuong": bao_ham, "tong": sum(bao_ham.values())}}


def _kiem_quyet_dinh(muc: list[dict], nguoi: list[str], quyet_dinh: dict) -> None:
    for code in nguoi:
        qd = quyet_dinh.get(code, {})
        for m in muc:
            q = qd.get(m["id"])
            if not q or q.get("lua_chon") not in bat_dong_g4.LUA_CHON[m["loai"]]:
                raise ValueError(f"{code}: {m['id']}: thiếu hoặc sai lựa chọn")
            if not str(q.get("ly_do", "")).strip():
                raise ValueError(f"{code}: {m['id']}: ly_do trống")


def _ban_ghi(e: dict, nguoi: list[str]) -> dict:
    return {"dich": e["dich"], "nguon": e["nguon"], "loai": e["loai"], "chuong": e["chuong"], "bang_chung": dict(e["bang_chung"]),
            "khong_chac": e["khong_chac"], "ghi_chu": e["ghi_chu"], "nguoi_gan": list(nguoi), "ma_dong_goc": [e["ma"]]}


def _khoa_vang(thu_tu: dict):
    return lambda r: (thu_tu[r["chuong"]], r["dich"], str(r["nguon"]), r["ma_dong_goc"])


def chot_g4(can: dict, quyet_dinh: dict[str, dict]) -> dict:
    nguoi = can["nguoi"]
    muc = bat_dong_g4.tao_muc_g4(can)
    _kiem_quyet_dinh(muc, nguoi, quyet_dinh)
    ca, cb = can["canh"]["a"], can["canh"]["b"]
    muc_loai = {(m["a"], m["b"]): m["id"] for m in muc if m["loai"] == "loai"}
    dong_y, giao_goc, tranh_chap, loai_bo = [], set(), [], []
    for k in can["khop"]:
        ea, eb = ca[k["a"]], cb[k["b"]]
        r = _ban_ghi(ea, nguoi)
        r["ma_dong_goc"] = [ea["ma"], eb["ma"]]
        r["khong_chac"] = ea["khong_chac"] or eb["khong_chac"]
        r["ghi_chu"] = " | ".join(x for x in (ea["ghi_chu"], eb["ghi_chu"]) if x)
        if eb["bang_chung"]["cau"] or eb["bang_chung"]["trang"] is not None:
            r["bang_chung_khac"] = [dict(eb["bang_chung"])]
        if ea["loai"] != eb["loai"]:
            chon = {c: quyet_dinh[c][muc_loai[(k["a"], k["b"])]]["lua_chon"] for c in nguoi}
            if len(set(chon.values())) == 1:
                r["loai"] = next(iter(chon.values()))
            else:
                r["loai"], r["loai_tranh_chap"] = None, chon
        dong_y.append(r)
        giao_goc.add(id(r))
    for m in muc:
        if m["loai"] != "rieng":
            continue
        e = (ca if m["ben"] == "a" else cb)[m["muc"]]
        r = _ban_ghi(e, [nguoi[0] if m["ben"] == "a" else nguoi[1]])
        lua = {c: quyet_dinh[c][m["id"]]["lua_chon"] for c in nguoi}
        if all(v == "giu" for v in lua.values()):
            dong_y.append(r)
        elif all(v == "bo" for v in lua.values()):
            loai_bo.append(r)
        else:
            tranh_chap.append({**r, "quyet_dinh": {c: dict(quyet_dinh[c][m["id"]]) for c in nguoi}})
    thu_tu = {ch: i for i, ch in enumerate(can["chuong"])}
    khoa = _khoa_vang(thu_tu)
    van_ban = [r for r in dong_y if r["loai"] == "van_ban"]
    vang_chinh = sorted(van_ban, key=khoa)
    vang_giao = sorted((r for r in van_ban if id(r) in giao_goc), key=khoa)
    kien_thuc = sorted((r for r in dong_y if r["loai"] == "kien_thuc"), key=khoa)
    bao_ham = [{**_ban_ghi((ca if ben == "a" else cb)[ma], [nguoi[0] if ben == "a" else nguoi[1]]), "nhan": "bao_ham_bac_cau"}
               for ben in ("a", "b") for ma in can["bao_ham"][ben]]
    vang_hop = sorted([*dong_y, *bao_ham, *({k: v for k, v in t.items() if k != "quyet_dinh"} for t in tranh_chap)], key=khoa)
    return {"schema": SCHEMA, "ma_sach": can["ma_sach"], "nguoi_gan": "hoi-y", "kho_chot_sha256": can["kho_chot_sha256"],
            "quan_he": vang_chinh, "vang_chinh": vang_chinh, "vang_hop": vang_hop, "vang_giao": vang_giao,
            "kien_thuc": kien_thuc, "tranh_chap": sorted(tranh_chap, key=khoa), "loai": sorted(loai_bo, key=khoa), "bao_ham_bac_cau": len(bao_ham)}
