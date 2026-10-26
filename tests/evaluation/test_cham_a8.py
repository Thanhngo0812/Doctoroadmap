"""Lõi chấm A8: số tính tay trên thế giới nhỏ. Cạnh viết là (tiên quyết -> đích)."""
from danhgia.cham.bang import cham
from danhgia.cham import dong
from dung_tay import can, canh, g3, g4, hop_dong, khai_niem, ngoai

S = "S"


def the_gioi_1():
    """Sách S, hai chương. Vàng: 1>2, 2>3, 1>3 (c1); 3>4, 4>5 (c2). Mỗi khái niệm vàng Gi khớp node ni.
    Máy (cứng): 1>2, 2>3, 4>5, 3>5, 9>3 (n9 không có trong vàng)."""
    ma = [f"G-S-00{i}" for i in range(1, 6)]
    vang3 = g3(S, [(ma[0], "c1"), (ma[1], "c1"), (ma[2], "c1"), (ma[3], "c2"), (ma[4], "c2")])
    vang4 = g4(S, [(ma[0], ma[1]), (ma[1], ma[2]), (ma[0], ma[2]), (ma[2], ma[3]), (ma[3], ma[4])])
    cc = can(S, [(m, f"n{i}", "khop") for i, m in enumerate(ma, 1)])
    kn = [khai_niem(f"n{i}") for i in (1, 2, 3, 4, 5, 9)]
    hd = hop_dong(kn, [canh("n1", "n2"), canh("n2", "n3"), canh("n4", "n5"), canh("n3", "n5"), canh("n9", "n3")],
                  ["n1", "n2", "n3", "n4", "n5", "n9"])
    return hd, vang3, vang4, cc


def lay(rows, thuoc, chuong):
    ket_qua = [r for r in rows if r["thuoc"] == thuoc and r["chuong"] == chuong]
    assert len(ket_qua) == 1, (thuoc, chuong, sorted({r["thuoc"] for r in rows}))
    return ket_qua[0]


def bo(row):
    return row["tp"], row["fp"], row["fn"]


def test_f1_truc_tiep_theo_chuong_spec():
    rows = cham(*the_gioi_1(), ma_sach=S)
    # c1: vàng đích thuộc T = {1>2,2>3,1>3}; máy {1>2,2>3,9>3}: tp 2, fp 1 (9>3), fn 1 (1>3)
    assert bo(lay(rows, "a8.f1_truc_tiep.nghiem", "c1")) == (2, 1, 1)
    # c2: vàng {3>4,4>5}; máy {4>5,3>5}: tp 1, fp 1, fn 1
    assert bo(lay(rows, "a8.f1_truc_tiep.nghiem", "c2")) == (1, 1, 1)


def test_bao_dong_tinh_truoc_khi_loc_pham_vi_dich():
    rows = cham(*the_gioi_1(), ma_sach=S)
    # c1: vàng đóng có 3 cạnh đích thuộc T; máy đóng thêm 1>3: tp 3, fp 1 (9>3), fn 0
    assert bo(lay(rows, "a8.f1_bao_dong.nghiem", "c1")) == (3, 1, 0)
    # c2: vàng đóng có 7 cạnh đích thuộc {4,5}; máy đóng {1>5,2>5,3>5,4>5,9>5}: tp 4, fp 1 (9>5), fn 3
    assert bo(lay(rows, "a8.f1_bao_dong.nghiem", "c2")) == (4, 1, 3)


def test_ho_so_giu_lai_v3_loc_hai_dau_truoc_roi_dong_bao():
    rows = cham(*the_gioi_1(), ma_sach=S, ho_so="giu_lai_v3")
    # c1: T={1,2,3}; máy rút gọn lọc hai đầu = {1>2,2>3}; vàng {1>2,2>3,1>3}: tp 2, fp 0, fn 1
    assert bo(lay(rows, "a8.f1_truc_tiep.nghiem", "c1")) == (2, 0, 1)
    # đóng sau khi lọc: máy {1>2,2>3,1>3} khớp vàng
    assert bo(lay(rows, "a8.f1_bao_dong.nghiem", "c1")) == (3, 0, 0)


def test_ho_so_giu_lai_v3_rut_gon_bac_cau_cua_may():
    hd, v3, v4, cc = the_gioi_1()
    hd["canh"].append(canh("n1", "n3"))  # 1>3 là cạnh bắc cầu của 1>2>3, bị rút gọn
    rows = cham(hd, v3, v4, cc, ma_sach=S, ho_so="giu_lai_v3")
    assert bo(lay(rows, "a8.f1_truc_tiep.nghiem", "c1")) == (2, 0, 1)
    rows = cham(hd, v3, v4, cc, ma_sach=S)  # hồ sơ spec không rút gọn nên 1>3 là trúng
    assert bo(lay(rows, "a8.f1_truc_tiep.nghiem", "c1")) == (3, 1, 0)


def test_canh_mem_khong_dem_vao_canh_cung():
    hd, v3, v4, cc = the_gioi_1()
    hd["canh"].append(canh("n1", "n3", mem=True))
    rows = cham(hd, v3, v4, cc, ma_sach=S)
    assert bo(lay(rows, "a8.f1_truc_tiep.nghiem", "c1")) == (2, 1, 1)  # cạnh mềm 1>3 không làm fn giảm
    rows = cham(hd, v3, v4, cc, ma_sach=S, mem="ca_hai")
    assert bo(lay(rows, "a8.f1_truc_tiep.nghiem", "c1")) == (3, 1, 0)


def test_nghiem_va_noi_khac_nhau():
    # vàng 1>2; G2 chỉ khớp "máy rộng hơn" với n2; máy có 1>2
    vang3 = g3(S, [("G-S-001", "c1"), ("G-S-002", "c1")])
    vang4 = g4(S, [("G-S-001", "G-S-002")])
    cc = can(S, [("G-S-001", "n1", "khop"), ("G-S-002", "n2", "may_rong_hon")])
    hd = hop_dong([khai_niem("n1"), khai_niem("n2")], [canh("n1", "n2")], ["n1", "n2"])
    rows = cham(hd, vang3, vang4, cc, ma_sach=S)
    # nghiêm: G2 không căn được; đích máy n2 nằm ngoài phạm vi nên không là fp; vàng là fn
    assert bo(lay(rows, "a8.f1_truc_tiep.nghiem", "c1")) == (0, 0, 1)
    assert bo(lay(rows, "a8.f1_truc_tiep.noi", "c1")) == (1, 0, 0)


def test_dau_canh_khong_can_duoc_van_la_fn_va_khong_bao_gio_thanh_tp():
    vang3 = g3(S, [("G-S-001", "c1"), ("G-S-002", "c1")])
    vang4 = g4(S, [("G-S-001", "G-S-002")])
    cc = can(S, [("G-S-002", "n2", "khop"), ("G-S-001", "n7", "khong_khop")])
    hd = hop_dong([khai_niem("n2"), khai_niem("n7")], [canh("n7", "n2")], ["n7", "n2"])
    rows = cham(hd, vang3, vang4, cc, ma_sach=S)
    # nguồn vàng không căn được: máy n7>n2 vẫn là fp, vàng là fn
    assert bo(lay(rows, "a8.f1_truc_tiep.nghiem", "c1")) == (0, 1, 1)


def test_khai_niem_vang_bi_tach_thanh_hai_node():
    vang3 = g3(S, [("G-S-001", "c1"), ("G-S-002", "c1")])
    vang4 = g4(S, [("G-S-001", "G-S-002")])
    cc = can(S, [("G-S-001", "n1", "khop"), ("G-S-002", "n2", "khop"), ("G-S-002", "n2b", "khop")])
    hd = hop_dong([khai_niem("n1"), khai_niem("n2"), khai_niem("n2b")], [canh("n1", "n2")], ["n1", "n2", "n2b"])
    rows = cham(hd, vang3, vang4, cc, ma_sach=S)
    # vàng thành hai cặp node (n1>n2, n1>n2b); máy chỉ có n1>n2
    assert bo(lay(rows, "a8.f1_truc_tiep.nghiem", "c1")) == (1, 0, 1)


def test_hai_khai_niem_vang_don_chung_mot_node_tu_noi_roi_phep_cham_va_duoc_bao_cao():
    vang3 = g3(S, [("G-S-001", "c1"), ("G-S-002", "c1"), ("G-S-003", "c1")])
    vang4 = g4(S, [("G-S-001", "G-S-002"), ("G-S-002", "G-S-003")])
    cc = can(S, [("G-S-001", "n1", "khop"), ("G-S-002", "n1", "khop"), ("G-S-003", "n3", "khop")])
    hd = hop_dong([khai_niem("n1"), khai_niem("n3")], [canh("n1", "n3")], ["n1", "n3"])
    rows = cham(hd, vang3, vang4, cc, ma_sach=S)
    assert bo(lay(rows, "a8.f1_truc_tiep.nghiem", "c1")) == (1, 0, 0)  # chỉ còn n1>n3
    assert lay(rows, "can.tu_noi.nghiem", "c1")["gia_tri"] == 1


def test_khong_quen_anh_xa_danh_tinh_khi_node_da_gop():
    # ban_do_danh_tinh: n2old -> n2; vàng căn tới id cũ n2old, máy dùng đại diện n2
    vang3 = g3(S, [("G-S-001", "c1"), ("G-S-002", "c1")])
    vang4 = g4(S, [("G-S-001", "G-S-002")])
    cc = can(S, [("G-S-001", "n1", "khop"), ("G-S-002", "n2old", "khop")])
    hd = hop_dong([khai_niem("n1"), khai_niem("n2"), khai_niem("n2old", da_gop=True, trong_day_hoc=False)],
                  [canh("n1", "n2")], ["n1", "n2"], ban_do_danh_tinh={"n2old": "n2"})
    rows = cham(hd, vang3, vang4, cc, ma_sach=S)
    assert bo(lay(rows, "a8.f1_truc_tiep.nghiem", "c1")) == (1, 0, 0)


def test_chi_cham_quan_he_van_ban_khong_dem_kien_thuc_vao_vang_chinh():
    vang3 = g3(S, [("G-S-001", "c1"), ("G-S-002", "c1"), ("G-S-003", "c1")])
    vang4 = g4(S, [("G-S-001", "G-S-002"), ("G-S-001", "G-S-003", "kien_thuc")])
    cc = can(S, [("G-S-001", "n1", "khop"), ("G-S-002", "n2", "khop"), ("G-S-003", "n3", "khop")])
    hd = hop_dong([khai_niem(f"n{i}") for i in (1, 2, 3)], [canh("n1", "n2")], ["n1", "n2", "n3"])
    rows = cham(hd, vang3, vang4, cc, ma_sach=S)
    assert bo(lay(rows, "a8.f1_truc_tiep.nghiem", "c1")) == (1, 0, 0)


def test_tranh_chap_khong_vao_vang_chinh():
    vang3 = g3(S, [("G-S-001", "c1"), ("G-S-002", "c1"), ("G-S-003", "c1")])
    vang4 = g4(S, [("G-S-001", "G-S-002"), ("G-S-001", "G-S-003")], tranh_chap=[("G-S-001", "G-S-003")])
    cc = can(S, [("G-S-001", "n1", "khop"), ("G-S-002", "n2", "khop"), ("G-S-003", "n3", "khop")])
    hd = hop_dong([khai_niem(f"n{i}") for i in (1, 2, 3)], [canh("n1", "n2")], ["n1", "n2", "n3"])
    rows = cham(hd, vang3, vang4, cc, ma_sach=S)
    assert bo(lay(rows, "a8.f1_truc_tiep.nghiem", "c1")) == (1, 0, 0)  # 1>3 đang tranh chấp nên không phải fn


def test_nguon_ngoai_chuong_duoc_can_theo_bang_can():
    x = ngoai("Khái niệm ngoài", 3)
    vang3 = g3(S, [("G-S-001", "c1")])
    vang4 = g4(S, [(x, "G-S-001")])
    cc = can(S, [("G-S-001", "n1", "khop"), (x, "n8", "khop")])
    hd = hop_dong([khai_niem("n1"), khai_niem("n8")], [canh("n8", "n1")], ["n8", "n1"])
    rows = cham(hd, vang3, vang4, cc, ma_sach=S)
    assert bo(lay(rows, "a8.f1_truc_tiep.nghiem", "c1")) == (1, 0, 0)


def test_mau_so_khong_la_none_khong_la_khong():
    vang3 = g3(S, [("G-S-001", "c1"), ("G-S-002", "c2")])
    vang4 = g4(S, [("G-S-001", "G-S-002")])  # c1 không có cạnh vàng đích ở c1
    cc = can(S, [("G-S-001", "n1", "khop"), ("G-S-002", "n2", "khop")])
    hd = hop_dong([khai_niem("n1"), khai_niem("n2")], [canh("n1", "n2")], ["n1", "n2"])
    rows = cham(hd, vang3, vang4, cc, ma_sach=S)
    q6_c1 = lay(rows, "a10.q6.nghiem", "c1")
    assert (q6_c1["tu"], q6_c1["mau"]) == (0, 0)
    assert dong.gia_tri(q6_c1) is None
    f1_c1 = lay(rows, "a8.f1_truc_tiep.nghiem", "c1")
    assert bo(f1_c1) == (0, 0, 0)
    assert dong.gia_tri(f1_c1) is None
