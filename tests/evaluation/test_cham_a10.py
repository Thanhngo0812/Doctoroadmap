"""Lõi chấm A10: Q6, Q7, Q7b, số chu trình, số thành phần liên thông. Số tính tay."""
import pytest

from danhgia.cham.bang import cham
from danhgia.cham import dong
from dung_tay import can, canh, g3, g4, hop_dong, khai_niem, ngoai

S = "S"


def the_gioi_2():
    """c1 có G1..G3 và G6 (không cạnh vàng). Vàng: 1>2, 2>3, 1>3, X>3 (X ngoài, không căn được).
    Dãy học: n1 n3 n2 n6. Máy cứng: 2>3, 6>3; máy mềm: 1>2."""
    vang3 = g3(S, [("G-S-001", "c1"), ("G-S-002", "c1"), ("G-S-003", "c1"), ("G-S-006", "c1")])
    x = ngoai("X", 9)
    vang4 = g4(S, [("G-S-001", "G-S-002"), ("G-S-002", "G-S-003"), ("G-S-001", "G-S-003"), (x, "G-S-003")])
    cc = can(S, [("G-S-001", "n1", "khop"), ("G-S-002", "n2", "khop"), ("G-S-003", "n3", "khop"),
                 ("G-S-006", "n6", "khop")])
    kn = [khai_niem(f"n{i}") for i in (1, 2, 3, 6)]
    hd = hop_dong(kn, [canh("n2", "n3"), canh("n6", "n3"), canh("n1", "n2", mem=True)], ["n1", "n3", "n2", "n6"])
    return hd, vang3, vang4, cc


def lay(rows, thuoc, chuong="c1"):
    ket_qua = [r for r in rows if r["thuoc"] == thuoc and r["chuong"] == chuong]
    assert len(ket_qua) == 1, (thuoc, chuong, sorted({r["thuoc"] for r in rows}))
    return ket_qua[0]


def test_q6_mau_so_la_moi_canh_vang_trong_pham_vi_dau_ngoai_day_hoc_tinh_la_loi():
    rows = cham(*the_gioi_2(), ma_sach=S)
    q6 = lay(rows, "a10.q6.nghiem")
    # 4 cạnh: 1>2 đúng (vị trí 0<2); 2>3 ngược (2>1); 1>3 đúng (0<1); X>3 đầu ngoài dãy học: lỗi
    assert (q6["tu"], q6["mau"]) == (2, 4)
    assert dong.gia_tri(q6) == pytest.approx(0.5)


def test_q6_khong_chi_chia_cho_canh_da_xep_duoc():
    rows = cham(*the_gioi_2(), ma_sach=S)
    q6 = lay(rows, "a10.q6.nghiem")
    chi_da_xep = 3  # sai: bỏ cạnh X>3 khỏi mẫu số
    assert q6["mau"] != chi_da_xep


def test_q7_canh_cung_va_ban_ca_canh_mem():
    rows = cham(*the_gioi_2(), ma_sach=S)
    # tổ tiên vàng: n2 {n1}; n3 {n1,n2,X}. Máy cứng: n2 {} nên 0; n3 {n2,n6} nên 1/3. tổng 1/3, 2 đích
    q7 = lay(rows, "a10.q7.nghiem")
    assert q7["kieu"] == "trung_binh"
    assert q7["tong"] == pytest.approx(1 / 3) and q7["n"] == 2
    # thêm cạnh mềm 1>2: n2 {n1} nên 1; n3 {n1,n2,n6} nên 2/3. tổng 5/3
    q7m = lay(rows, "a10.q7_ca_mem.nghiem")
    assert q7m["tong"] == pytest.approx(5 / 3) and q7m["n"] == 2


def test_q7b_chi_xet_to_tien_may_thuoc_chuong_vang():
    rows = cham(*the_gioi_2(), ma_sach=S)
    # n3 có tổ tiên máy cứng {n2,n6}, cả hai thuộc chương; cần: n2 (n6 không có trong vàng) nên 1/2. n2 không có tổ tiên máy
    q7b = lay(rows, "a10.q7b.nghiem")
    assert q7b["tong"] == pytest.approx(0.5) and q7b["n"] == 1


def test_q7_canh_may_co_dau_ngoai_day_hoc_bi_bo():
    hd, v3, v4, cc = the_gioi_2()
    hd["khai_niem"].append(khai_niem("n7", trong_day_hoc=False))
    hd["canh"].append(canh("n7", "n3"))  # n7 không trong dãy học
    rows = cham(hd, v3, v4, cc, ma_sach=S)
    assert lay(rows, "a10.q7.nghiem")["tong"] == pytest.approx(1 / 3)


def test_q6_nghiem_va_noi_khac_nhau():
    vang3 = g3(S, [("G-S-001", "c1"), ("G-S-002", "c1")])
    vang4 = g4(S, [("G-S-001", "G-S-002")])
    cc = can(S, [("G-S-001", "n1", "khop"), ("G-S-002", "n2", "may_hep_hon")])
    hd = hop_dong([khai_niem("n1"), khai_niem("n2")], [], ["n2", "n1"])  # n2 trước n1: ngược
    rows = cham(hd, vang3, vang4, cc, ma_sach=S)
    assert (lay(rows, "a10.q6.nghiem")["tu"], lay(rows, "a10.q6.nghiem")["mau"]) == (1, 1)  # G2 không căn: đầu ngoài
    assert (lay(rows, "a10.q6.noi")["tu"], lay(rows, "a10.q6.noi")["mau"]) == (1, 1)  # căn được nhưng ngược


def test_q6_khong_co_canh_vang_tra_none_khong_tra_khong():
    vang3 = g3(S, [("G-S-001", "c1")])
    vang4 = g4(S, [])
    cc = can(S, [("G-S-001", "n1", "khop")])
    hd = hop_dong([khai_niem("n1")], [], ["n1"])
    rows = cham(hd, vang3, vang4, cc, ma_sach=S)
    assert dong.gia_tri(lay(rows, "a10.q6.nghiem")) is None


def test_q6_khai_niem_vang_don_chung_mot_node_tu_noi_khong_vao_mau_so():
    vang3 = g3(S, [("G-S-001", "c1"), ("G-S-002", "c1"), ("G-S-003", "c1")])
    vang4 = g4(S, [("G-S-001", "G-S-002"), ("G-S-002", "G-S-003")])
    cc = can(S, [("G-S-001", "n1", "khop"), ("G-S-002", "n1", "khop"), ("G-S-003", "n3", "khop")])
    hd = hop_dong([khai_niem("n1"), khai_niem("n3")], [], ["n1", "n3"])
    rows = cham(hd, vang3, vang4, cc, ma_sach=S)
    q6 = lay(rows, "a10.q6.nghiem")
    assert (q6["tu"], q6["mau"]) == (0, 1)


def test_so_chu_trinh_va_so_thanh_phan_lien_thong():
    vang3 = g3(S, [("G-S-001", "c1")])
    cc = can(S, [("G-S-001", "a", "khop")])
    kn = [khai_niem(x) for x in "abcdef"]
    # a>b>c>a là một chu trình; d>e; f lẻ loi; cạnh mềm e>f không nối thành phần
    hd = hop_dong(kn, [canh("a", "b"), canh("b", "c"), canh("c", "a"), canh("d", "e"), canh("e", "f", mem=True)],
                  list("abcdef"))
    rows = cham(hd, vang3, g4(S, []), cc, ma_sach=S)
    assert lay(rows, "a10.so_chu_trinh", "toan_sach")["gia_tri"] == 1
    assert lay(rows, "a10.so_thanh_phan", "toan_sach")["gia_tri"] == 3  # {a,b,c}, {d,e}, {f}


def test_day_hoc_lap_bi_tu_choi():
    hd, v3, v4, cc = the_gioi_2()
    hd["lo_trinh"]["day_hoc"] = ["n1", "n1", "n3", "n2", "n6"]
    with pytest.raises(ValueError, match="lặp"):
        cham(hd, v3, v4, cc, ma_sach=S)


def test_he_khong_co_lo_trinh_bao_khong_ap_dung():
    hd, v3, v4, cc = the_gioi_2()
    hd["lo_trinh"] = None
    rows = cham(hd, v3, v4, cc, ma_sach=S)
    assert not [r for r in rows if r["thuoc"].startswith("a10.")]
    assert [r for r in rows if r["thuoc"].startswith("a8.")]


def test_q7_tong_cong_bu_sai_so_khop_tung_bit_voi_bo_cham_cu():
    # 10 đích, mỗi đích có 10 tổ tiên vàng và máy phủ đúng 1: mỗi tỉ lệ 0,1. Cộng thẳng cho 0,9999999999999999.
    a, t = [f"G-S-a{i}" for i in range(10)], [f"G-S-t{i}" for i in range(10)]
    vang3 = g3(S, [(m, "c1") for m in [*a, *t]])
    vang4 = g4(S, [(x, y) for y in t for x in a])
    cc = can(S, [(m, "n" + m[-2:], "khop") for m in [*a, *t]])
    nodes = ["n" + m[-2:] for m in [*a, *t]]
    hd = hop_dong([khai_niem(n) for n in nodes], [canh(nodes[0], nodes[10 + i]) for i in range(10)], nodes)
    q7 = lay(cham(hd, vang3, vang4, cc, ma_sach=S), "a10.q7.nghiem")
    assert q7["n"] == 10
    assert q7["tong"] == 1.0


def test_canh_bo_qua_tinh_vao_q7_nhung_khong_vao_f1():
    vang3 = g3(S, [("G-S-001", "c1"), ("G-S-002", "c1")])
    vang4 = g4(S, [("G-S-001", "G-S-002")])
    cc = can(S, [("G-S-001", "n1", "khop"), ("G-S-002", "n2", "khop")])
    hd = hop_dong([khai_niem("n1"), khai_niem("n2")], [canh("n1", "n2", bo_qua=True)], ["n1", "n2"])
    rows = cham(hd, vang3, g4_(vang4), cc, ma_sach=S)
    assert lay(rows, "a10.q7.nghiem")["tong"] == 1.0  # tổ tiên n1 của n2 được phủ nhờ cạnh bypass
    f1 = lay(rows, "a8.f1_truc_tiep.nghiem")
    assert (f1["tp"], f1["fp"], f1["fn"]) == (0, 0, 1)  # F1 chỉ xét cạnh yêu cầu, như bộ chấm cũ


def g4_(x):
    return x
