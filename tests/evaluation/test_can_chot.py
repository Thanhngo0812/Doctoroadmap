import random

import openpyxl
import pytest

from danhgia.phieu import bat_dong
from danhgia.phieu.can import can_hai_ban
from danhgia.vang.g3 import chot, dem_dong_thuan, dem_kho
from tests.evaluation.ho_tro import khai_niem as kn, nfd, tho


def cap(a_muc, b_muc):
    return can_hai_ban(tho("T1-a", *a_muc), tho("T1-b", *b_muc))


# --- căn hai bản ---

def test_khop_ten_sau_chuan_hoa_ke_ca_ten_co_y_va_nfd():
    a = [kn("c10-001", "c10", "Quy luật", trang=1, cau="Theo quy luật này."), kn("c10-002", "c10", "Tỷ lệ", trang=1)]
    b = [kn("c10-005", "c10", nfd("QUY  LUẬT"), trang=2), kn("c10-006", "c10", "tỷ lệ.", trang=3)]
    can = cap(a, b)
    assert {(k["a"], k["b"], k["luat"]) for k in can["khop"]} == {("c10-001", "c10-005", "ten"), ("c10-002", "c10-006", "ten")}
    assert can["chi_a"] == [] and can["chi_b"] == [] and can["cap_gan"] == []


def test_khop_qua_ten_khac():
    can = cap([kn("c10-001", "c10", "Luật số lớn", ten_khac=["quy luật số lớn"])], [kn("c10-001", "c10", "Quy luật số lớn")])
    assert [(k["a"], k["b"], k["luat"]) for k in can["khop"]] == [("c10-001", "c10-001", "ten")]


CAU_BC = "Biến cố độc lập là hai biến cố mà việc xảy ra của biến cố này không ảnh hưởng đến xác suất của biến cố kia."


def test_khop_theo_cau_dinh_nghia_cung_trang_khi_ten_khac_nhau():
    can = cap([kn("c10-001", "c10", "Biến cố độc lập", trang=3, cau=CAU_BC)],
              [kn("c10-009", "c10", "Độc lập", trang=3, cau=CAU_BC.replace("hai biến cố", "2 biến cố"))])
    assert [k["luat"] for k in can["khop"]] == ["cau"]


def test_cung_cau_nhung_khac_trang_khong_khop_theo_cau():
    can = cap([kn("c10-001", "c10", "Biến cố độc lập", trang=3, cau=CAU_BC)], [kn("c10-009", "c10", "Phụ thuộc", trang=2, cau=CAU_BC)])
    assert can["khop"] == []


def test_khong_khop_xuyen_chuong():
    can = cap([kn("c10-001", "c10", "Kỳ vọng")], [kn("c11-001", "c11", "Kỳ vọng")])
    assert can["khop"] == [] and can["chi_a"] == ["c10-001"] and can["chi_b"] == ["c11-001"]


def test_cap_con_lai_gan_nhau_thanh_cau_hoi_cung_khai_niem():
    can = cap([kn("c10-001", "c10", "Xác suất", trang=2)], [kn("c10-001", "c10", "Xác suất có điều kiện", trang=2)])
    assert can["khop"] == [] and [(c["a"], c["b"]) for c in can["cap_gan"]] == [("c10-001", "c10-001")]
    assert can["chi_a"] == ["c10-001"] and can["chi_b"] == ["c10-001"]  # vẫn là mục riêng cho tới khi hội ý


def test_chuoi_con_khong_theo_am_tiet_khong_thanh_cap_gan():
    can = cap([kn("c10-001", "c10", "hi")], [kn("c10-001", "c10", "chi tiết")])
    assert can["cap_gan"] == []


def test_ket_qua_khong_phu_thuoc_thu_tu_dau_vao_va_thu_tu_muc():
    a = [kn("c10-001", "c10", "Quy luật"), kn("c10-002", "c10", "Kỳ vọng"), kn("c10-003", "c10", "Phương sai")]
    b = [kn("c10-001", "c10", "kỳ vọng"), kn("c10-002", "c10", "Phương sai"), kn("c10-003", "c10", "Mốt")]
    x = can_hai_ban(tho("T1-a", *a), tho("T1-b", *b))
    y = can_hai_ban(tho("T1-b", *b[::-1]), tho("T1-a", *a[::-1]))
    assert x == y and x["nguoi"] == ["T1-a", "T1-b"]


def test_hai_ban_cung_ma_nguoi_la_loi():
    with pytest.raises(ValueError, match="nguoi_gan"):
        can_hai_ban(tho("T1-a"), tho("T1-a"))


def test_hai_ban_khac_sach_la_loi():
    with pytest.raises(ValueError, match="ma_sach"):
        can_hai_ban(tho("T1-a"), tho("T1-b", ma_sach="khac"))


# --- số đếm đồng thuận ---

def test_dem_dong_thuan_theo_chuong_dung_tren_vi_du_dung_tay():
    a = [kn("c10-001", "c10", "Quy luật"), kn("c10-002", "c10", "Kỳ vọng"), kn("c10-003", "c10", "Phương sai"),
         kn("c11-001", "c11", "Mốt")]
    b = [kn("c10-001", "c10", "kỳ vọng"), kn("c10-002", "c10", "Phương sai"), kn("c10-003", "c10", "Hàm mật độ"),
         kn("c10-004", "c10", "Hiệp phương sai"), kn("c11-001", "c11", "Trung vị")]
    d = dem_dong_thuan(cap(a, b))
    assert d["theo_chuong"]["c10"] == {"a": 2, "b": 1, "c": 2, "f1": pytest.approx(4 / 7)}
    assert d["theo_chuong"]["c11"] == {"a": 0, "b": 1, "c": 1, "f1": 0.0}
    assert d["tong"] == {"a": 2, "b": 2, "c": 3, "f1": pytest.approx(4 / 9)}


def test_dem_khong_ai_liet_ke_thi_f1_la_none_khong_chia_cho_khong():
    assert dem_dong_thuan(cap([], []))["tong"] == {"a": 0, "b": 0, "c": 0, "f1": None}


# --- phiếu bất đồng và luật chốt ---

def bo_hai_nguoi():
    a = [kn("c10-001", "c10", "Kỳ vọng", trang=3, cau="Kỳ vọng là trung bình."),
         kn("c10-002", "c10", "Xác suất", trang=2),
         kn("c10-003", "c10", "Mốt", trang=5, trang_thai="chi_nhac")]
    b = [kn("c10-001", "c10", "kỳ vọng", trang=3, trang_thai="day_qua_vi_du"),
         kn("c10-002", "c10", "Xác suất có điều kiện", trang=2),
         kn("c10-003", "c10", "Trung vị", trang=4, trang_thai="chi_nhac")]
    return cap(a, b)


def quyet(**kw):
    return {k: {"lua_chon": v, "ly_do": "lý do"} for k, v in kw.items()}


def test_tao_muc_chi_gom_muc_hai_nguoi_khac_nhau_va_id_on_dinh():
    muc = bat_dong.tao_muc(bo_hai_nguoi())
    assert [(m["id"], m["loai"]) for m in muc] == [
        ("BD-c10-001", "cap_gan"), ("BD-c10-002", "rieng"), ("BD-c10-003", "rieng"),
        ("BD-c10-004", "rieng"), ("BD-c10-005", "rieng"),
    ]
    assert "Kỳ vọng" not in {m["ten"] for m in muc if m["loai"] == "rieng"}  # khớp tự động không phải bất đồng


def test_chot_ca_hai_giu_vao_kho_ca_hai_bo_loai_con_lai_tranh_chap():
    can = cap([kn("c10-001", "c10", "Mốt", trang=5), kn("c10-002", "c10", "Trung vị", trang=4), kn("c10-003", "c10", "Mode", trang=1)], [])
    ids = {m["muc"]: m["id"] for m in bat_dong.tao_muc(can)}
    qa = quyet(**{ids["c10-001"]: "giu", ids["c10-002"]: "giu", ids["c10-003"]: "bo"})
    qb = quyet(**{ids["c10-001"]: "giu", ids["c10-002"]: "bo", ids["c10-003"]: "bo"})
    kho = chot(can, {"T1-a": qa, "T1-b": qb})
    assert [k["ten"] for k in kho["khai_niem"]] == ["Mốt"]
    assert [t["muc"]["ten"] for t in kho["tranh_chap"]] == ["Trung vị"]
    assert [m["ten"] for m in kho["loai"]] == ["Mode"]
    assert kho["nguoi_gan"] == "hoi-y"


@pytest.mark.parametrize("qa,qb", [("giu", "bo"), ("bo", "giu")])
def test_mot_nguoi_giu_mot_nguoi_bo_la_tranh_chap_khong_vao_kho(qa, qb):
    can = cap([kn("c10-001", "c10", "Mốt")], [])
    i = bat_dong.tao_muc(can)[0]["id"]
    kho = chot(can, {"T1-a": quyet(**{i: qa}), "T1-b": quyet(**{i: qb})})
    assert kho["khai_niem"] == [] and len(kho["tranh_chap"]) == 1 and kho["loai"] == []


def test_khop_tu_dong_vao_kho_khong_can_hoi_y_va_ghi_trang_thai_hai_ben():
    can = bo_hai_nguoi()
    qd = {m["id"]: ("bo" if m["loai"] == "rieng" else "khac") for m in bat_dong.tao_muc(can)}
    kho = chot(can, {"T1-a": quyet(**qd), "T1-b": quyet(**qd)})
    ky_vong = [k for k in kho["khai_niem"] if k["ten"] == "Kỳ vọng"]
    assert len(ky_vong) == 1 and ky_vong[0]["trang_thai"] == "day_o_day"
    assert ky_vong[0]["trang_thai_khac"] == {"T1-a": "day_o_day", "T1-b": "day_qua_vi_du"}


def test_cap_gan_ca_hai_cung_thi_gop_thanh_mot_khai_niem():
    can = bo_hai_nguoi()
    muc = bat_dong.tao_muc(can)
    gan = [m for m in muc if m["loai"] == "cap_gan"][0]["id"]
    qd = {m["id"]: "bo" for m in muc if m["loai"] == "rieng"}
    kho = chot(can, {"T1-a": quyet(**qd, **{gan: "cung"}), "T1-b": quyet(**qd, **{gan: "cung"})})
    ten = [k["ten"] for k in kho["khai_niem"]]
    assert ten.count("Xác suất") == 1 and "Xác suất có điều kiện" not in ten
    assert "Xác suất có điều kiện" in [k for k in kho["khai_niem"] if k["ten"] == "Xác suất"][0]["ten_khac"]


def test_cap_gan_mot_nguoi_noi_khac_thi_hai_muc_van_rieng_va_xet_giu_bo():
    can = bo_hai_nguoi()
    muc = bat_dong.tao_muc(can)
    gan = [m for m in muc if m["loai"] == "cap_gan"][0]["id"]
    giu = {m["id"]: "giu" for m in muc if m["loai"] == "rieng"}
    kho = chot(can, {"T1-a": quyet(**giu, **{gan: "cung"}), "T1-b": quyet(**giu, **{gan: "khac"})})
    ten = [k["ten"] for k in kho["khai_niem"]]
    assert "Xác suất" in ten and "Xác suất có điều kiện" in ten


def test_ma_kho_theo_chuong_trang_ten_chuan_hoa_on_dinh_giua_hai_lan_va_thu_tu_muc():
    a = [kn("c11-001", "c11", "Zeta", trang=4), kn("c10-001", "c10", "Beta", trang=3), kn("c10-002", "c10", "Alpha", trang=3),
         kn("c10-003", "c10", "Gamma", trang=1), kn("c10-004", "c10", "Omega", trang=None, cau="")]

    def giu(c):
        return {m["id"]: "giu" for m in bat_dong.tao_muc(c)}

    can1 = can_hai_ban(tho("T1-a", *a), tho("T1-b"))
    can2 = can_hai_ban(tho("T1-b"), tho("T1-a", *random.Random(1).sample(a, len(a))))
    kho1 = chot(can1, {"T1-a": quyet(**giu(can1)), "T1-b": quyet(**giu(can1))})
    kho2 = chot(can2, {"T1-b": quyet(**giu(can2)), "T1-a": quyet(**giu(can2))})
    ma = [(k["ma"], k["ten"]) for k in kho1["khai_niem"]]
    assert ma == [("G-dev-test-001", "Gamma"), ("G-dev-test-002", "Alpha"), ("G-dev-test-003", "Beta"),
                  ("G-dev-test-004", "Omega"), ("G-dev-test-005", "Zeta")]
    assert [(k["ma"], k["ten"]) for k in kho2["khai_niem"]] == ma


def test_chot_thieu_quyet_dinh_hoac_ly_do_trong_la_loi():
    can = cap([kn("c10-001", "c10", "Mốt")], [])
    i = bat_dong.tao_muc(can)[0]["id"]
    with pytest.raises(ValueError, match=i):
        chot(can, {"T1-a": quyet(**{i: "giu"}), "T1-b": {}})
    with pytest.raises(ValueError, match="ly_do"):
        chot(can, {"T1-a": quyet(**{i: "giu"}), "T1-b": {i: {"lua_chon": "giu", "ly_do": " "}}})


def test_dem_kho_vao_kho_loai_tranh_chap_theo_chuong():
    can = cap([kn("c10-001", "c10", "Mốt"), kn("c10-002", "c10", "Mode"), kn("c10-003", "c10", "Trung vị")], [])
    ids = {m["muc"]: m["id"] for m in bat_dong.tao_muc(can)}
    kho = chot(can, {"T1-a": quyet(**{ids["c10-001"]: "giu", ids["c10-002"]: "bo", ids["c10-003"]: "giu"}),
                     "T1-b": quyet(**{ids["c10-001"]: "giu", ids["c10-002"]: "bo", ids["c10-003"]: "bo"})})
    assert dem_kho(kho)["theo_chuong"]["c10"] == {"vao_kho": 1, "loai": 1, "tranh_chap": 1}


# --- phiếu bất đồng Excel: round-trip và validator ---

def test_phieu_bat_dong_excel_round_trip(tmp_path):
    can = bo_hai_nguoi()
    p = tmp_path / "bd.xlsx"
    bat_dong.sinh_phieu_bat_dong(can, "T1-a", p)
    wb = openpyxl.load_workbook(p)
    assert wb.sheetnames[0] == "Hướng dẫn" and wb["DS"].sheet_state == "hidden"
    ws = wb["bat-dong"]
    assert ws.column_dimensions["A"].hidden is True
    assert all(r.type == "list" for r in ws.data_validations.dataValidation) and ws.data_validations.dataValidation
    muc = bat_dong.tao_muc(can)
    bat_dong.dien_thu(p, {m["id"]: ("cung" if m["loai"] == "cap_gan" else "giu", f"lý do {m['id']}") for m in muc})
    doc = bat_dong.doc_phieu_bat_dong(p)
    assert doc["nguoi"] == "T1-a" and doc["ma_sach"] == "dev-test"
    assert doc["quyet_dinh"]["BD-c10-001"] == {"lua_chon": "cung", "ly_do": "lý do BD-c10-001"}
    assert bat_dong.kiem_phieu_bat_dong(can, doc) == []


def test_phieu_bat_dong_khong_chua_muc_khop_tu_dong_va_khong_ten_nguoi_kia(tmp_path):
    can = bo_hai_nguoi()
    p = tmp_path / "bd.xlsx"
    bat_dong.sinh_phieu_bat_dong(can, "T1-a", p)
    gia_tri = " ".join(str(c.value) for ws in openpyxl.load_workbook(p).worksheets for row in ws.iter_rows() for c in row if c.value)
    assert "T1-b" not in gia_tri and "Kỳ vọng là trung bình" not in gia_tri
    assert "Trung vị" in gia_tri and "Mốt" in gia_tri  # câu trích của mỗi bên hiện ở mục bất đồng


def test_kiem_phieu_bat_dong_bat_tung_loi():
    can = cap([kn("c10-001", "c10", "Mốt")], [])
    i = bat_dong.tao_muc(can)[0]["id"]
    ok = {"nguoi": "T1-a", "ma_sach": "dev-test", "quyet_dinh": {i: {"lua_chon": "giu", "ly_do": "x"}}}
    assert bat_dong.kiem_phieu_bat_dong(can, ok) == []
    assert [l.ma_loi for l in bat_dong.kiem_phieu_bat_dong(can, {**ok, "quyet_dinh": {}})] == ["thieu_quyet_dinh"]
    sai = {**ok, "quyet_dinh": {i: {"lua_chon": "ok", "ly_do": "x"}}}
    assert [l.ma_loi for l in bat_dong.kiem_phieu_bat_dong(can, sai)] == ["gia_tri_ngoai_danh_sach"]
    khong_ly_do = {**ok, "quyet_dinh": {i: {"lua_chon": "giu", "ly_do": ""}}}
    assert [l.ma_loi for l in bat_dong.kiem_phieu_bat_dong(can, khong_ly_do)] == ["thieu_ly_do"]
    assert [l.ma_loi for l in bat_dong.kiem_phieu_bat_dong(can, {**ok, "nguoi": "T9-z"})] == ["sai_nguoi"]
