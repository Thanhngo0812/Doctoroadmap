"""DG-15: quy lỗi theo khâu (spec mục 10). Mỗi lý do 1-7 có một ca dựng tay rơi đúng vào lý do đó, không rơi vào lý do sau."""
import json

import pytest

from danhgia.cham import dong
from danhgia.cham.quy_loi import LY_DO, kiem_tong, quy_loi
from dung_tay import can, canh, g3, g4, hop_dong, khai_niem, ngoai

S = "S"
SECRET = "BI-MAT-GIA-KHAI-NIEM-XYZ"


def g(i):
    return f"G-S-{i:03d}"


def the_gioi():
    """15 cạnh vàng (đích ở chương c1, trừ chuỗi 21>22>23 có đích ở c2). Cạnh i>j nằm ở lý do ghi bên cạnh.

    Mỗi cạnh lỗi cố ý thỏa luôn điều kiện của các lý do SAU nó (không có cạnh máy, không là cặp ứng viên...), nên đặt sai thứ tự xét
    sẽ đổi lý do. Dãy học đặt đầu đích trước đầu nguồn ở mọi cạnh có cả hai đầu trong dãy, nên cạnh nào cũng hỏng Q6 trừ ba cạnh "đúng".
    """
    cac_chuong = {1: "c1", 2: "c1", 3: "c1", 4: "c1", 5: "c1", 6: "c1", 7: "c1", 8: "c1", 9: "c1", 10: "c1", 11: "c1", 12: "c1",
                  13: "c1", 14: "c1", 15: "c1", 16: "c1", 17: "c1", 18: "c1", 19: "c1", 20: "c1", 21: "c1", 22: "c2", 23: "c2",
                  24: "c1", 25: "c1", 26: "c1", 27: "c1"}
    vang3 = g3(S, [(g(i), c) for i, c in cac_chuong.items()])
    x = ngoai("X", 9)
    quan_he = [(g(1), g(2)),      # 1: G01 ở mục lỗi (G02 cũng không có node: sẽ là lý do 2 nếu xét sai thứ tự)
               (g(3), g(4)),      # 2: G03 không có node căn
               (x, g(20)),        # 2: nguồn ngoài sách, không căn được
               (g(5), g(6)),      # 3: G05 tách thành hai node trong dãy
               (g(7), g(8)),      # 3: hai khái niệm vàng dồn vào một node (gộp nhầm)
               (g(9), g(10)),     # 4: G09 có node nhưng node ra khỏi dãy học
               (g(11), g(12)),    # 5: không cạnh máy, không là cặp ứng viên
               (g(13), g(14)),    # 6: là cặp ứng viên
               (g(15), g(16)),    # 6: nguồn nằm trong cửa sổ định nghĩa của đích
               (g(17), g(18)),    # 7: có cạnh máy (mềm), dãy đặt ngược
               (g(19), g(20)),    # đúng
               (g(21), g(22)), (g(22), g(23)),   # đúng, đích ở c2
               (g(24), g(25)),    # 2: G24 không có node, còn G25 bị tách (lý do 3 sẽ đúng nếu xét sai thứ tự)
               (g(26), g(27))]    # 4: node G26 ngoài dãy, nhưng có cạnh máy n26>n27 (lý do 7 sẽ đúng nếu xét sai thứ tự)
    vang4 = g4(S, quan_he)
    hang = [(g(1), "n01", "khop"), (g(4), "n04", "khop"), (g(6), "n06", "khop"), (g(5), "n05a", "khop"), (g(5), "n05b", "khop"),
            (g(7), "n78", "khop"), (g(8), "n78", "khop"), (g(9), "n09", "khop"), (g(10), "n10", "khop")]
    hang += [(g(i), f"n{i}", "khop") for i in range(11, 24)]
    hang += [(g(25), "n25a", "khop"), (g(25), "n25b", "khop"), (g(26), "n26", "khop"), (g(27), "n27", "khop")]
    cc = can(S, hang)
    cac_nut = ["n01", "n04", "n06", "n09", "n10", "n11", "n12", "n13", "n14", "n15", "n16", "n17", "n18", "n19", "n20", "n21", "n22", "n23",
               "n05a", "n05b", "n78", "n25a", "n25b", "n26", "n27"]
    dau = ["n06", "n05a", "n05b", "n78", "n12", "n11", "n14", "n13", "n16", "n15", "n18", "n17", "n04", "n10", "n19", "n20", "n21", "n22", "n23", "n25a", "n25b", "n27"]
    kn = [khai_niem(n, trong_day_hoc=n in dau) for n in cac_nut]
    cac_canh = [canh("n17", "n18", mem=True),                       # lý do 7: có cạnh nhưng bị làm mềm
                canh("n19", "n20"), canh("n20", "n19"),             # đúng; ngược chiều
                canh("n21", "n23"), canh("n19", "n23"), canh("n21", "n20"),
                canh("n26", "n27")]   # bắc cầu; sai hẳn; đúng theo G5(b) nếu có phán
    hd = hop_dong(kn, cac_canh, dau)
    hd["cap_ung_vien"] = {"cap": [{"trai": "n13", "phai": "n14", "nguon_de_cu": ["cung_cum"], "quyet_dinh": "rejected",
                                   "nguong": None, "diem_ml": None}],
                          "cua_so_dinh_nghia": {"n16": ["n15"]}}
    return hd, vang3, vang4, cc


MUC_LOI = {g(1)}


def chay(**kw):
    hd, a, b, c = the_gioi()
    kw.setdefault("tap", "phat_trien")
    kw.setdefault("muc_loi", MUC_LOI)
    return quy_loi(hd, a, b, c, **kw)


def dem(rows, thuoc, chuong=None):
    return sum(r["gia_tri"] for r in rows if r["thuoc"] == thuoc and (chuong is None or r["chuong"] == chuong))


def danh_sach_theo_ly_do(ket_qua):
    ket = {}
    for muc in ket_qua["danh_sach"]:
        ket.setdefault(muc["ly_do"], []).append((muc["nguon"], muc["dich"]))
    return ket


def test_moi_ly_do_co_dung_ca_dung_tay_va_khong_roi_vao_ly_do_sau():
    ds = danh_sach_theo_ly_do(chay(co_danh_sach=True))
    assert ds[1] == [(g(1), g(2))]
    assert sorted(ds[2]) == sorted([(g(3), g(4)), ("ngoai:X|9", g(20)), (g(24), g(25))])
    assert sorted(ds[3]) == sorted([(g(5), g(6)), (g(7), g(8))])
    assert sorted(ds[4]) == sorted([(g(9), g(10)), (g(26), g(27))])
    assert ds[5] == [(g(11), g(12))]
    assert sorted(ds[6]) == sorted([(g(13), g(14)), (g(15), g(16))])
    assert ds[7] == [(g(17), g(18))]
    assert set(ds) == {1, 2, 3, 4, 5, 6, 7}


def test_tong_ly_do_cong_canh_dung_bang_tong_canh_vang_trong_pham_vi():
    rows = chay()["rows"]
    tong = dem(rows, "quy_loi.vang_pham_vi.nghiem")
    assert tong == 15
    assert dem(rows, "quy_loi.dung.nghiem") == 3
    assert [dem(rows, f"quy_loi.ly_do_{i}.nghiem") for i in LY_DO] == [1, 3, 2, 2, 1, 2, 1]
    assert dem(rows, "quy_loi.dung.nghiem") + sum(dem(rows, f"quy_loi.ly_do_{i}.nghiem") for i in LY_DO) == tong
    kiem_tong(rows)   # không ném lỗi


def test_theo_chuong_dich_cua_canh_quyet_dinh_chuong():
    rows = chay()["rows"]
    assert dem(rows, "quy_loi.vang_pham_vi.nghiem", "c2") == 2 and dem(rows, "quy_loi.dung.nghiem", "c2") == 2
    assert dem(rows, "quy_loi.vang_pham_vi.nghiem", "c1") == 13
    tong_cuon = {r["thuoc"]: dong.gia_tri(r) for r in dong.gop_cuon(rows)}
    assert tong_cuon["quy_loi.ly_do_2.nghiem"] == 3


def test_kiem_tong_bat_khi_mot_canh_bi_dem_hai_lan_hoac_bi_mat():
    rows = chay()["rows"]
    hai_lan = [dict(r, gia_tri=r["gia_tri"] + (1 if r["thuoc"] == "quy_loi.ly_do_5.nghiem" else 0)) for r in rows]
    with pytest.raises(ValueError, match="tổng"):
        kiem_tong(hai_lan)
    mat = [dict(r, gia_tri=r["gia_tri"] - (1 if r["thuoc"] == "quy_loi.ly_do_5.nghiem" and r["chuong"] == "c1" else 0)) for r in rows]
    with pytest.raises(ValueError, match="tổng"):
        kiem_tong(mat)


def test_ly_do_1_khong_ap_khi_chua_co_g2():
    ket = chay(muc_loi=None)
    assert 1 in ket["meta"]["khong_ap"]
    rows = ket["rows"]
    assert dem(rows, "quy_loi.ly_do_1.nghiem") == 0
    assert dem(rows, "quy_loi.ly_do_2.nghiem") == 4      # cạnh G01>G02 rơi sang lý do kế (G02 không có node)
    kiem_tong(rows)
    assert 1 not in chay()["meta"]["khong_ap"]


def test_he_khong_co_cap_ung_vien_gop_5_va_6_thanh_6_va_bao_co():
    hd, a, b, c = the_gioi()
    hd["cap_ung_vien"] = None
    ket = quy_loi(hd, a, b, c, tap="phat_trien", muc_loi=MUC_LOI)
    assert ket["meta"]["ly_do_5_khong_ap"] is True
    assert 5 in ket["meta"]["khong_ap"] and 1 not in ket["meta"]["khong_ap"]
    assert dem(ket["rows"], "quy_loi.ly_do_5.nghiem") == 0 and dem(ket["rows"], "quy_loi.ly_do_6.nghiem") == 3
    kiem_tong(ket["rows"])


def test_he_khong_co_lo_trinh_bi_tu_choi():
    hd, a, b, c = the_gioi()
    hd["lo_trinh"] = None
    with pytest.raises(ValueError, match="lộ trình"):
        quy_loi(hd, a, b, c, tap="phat_trien")


def test_canh_may_ngoai_vang_duoc_xep_loai():
    ket = chay(g5b={(g(21), g(20)): "dung"})["rows"]
    assert dem(ket, "quy_loi.may.trong_vang.nghiem") == 2      # n19>n20 và n26>n27
    assert dem(ket, "quy_loi.may.nguoc_chieu.nghiem") == 1     # n20>n19
    assert dem(ket, "quy_loi.may.bac_cau.nghiem") == 1         # n21>n23 (21>22>23 trong vàng)
    assert dem(ket, "quy_loi.may.sai_han.nghiem") == 1         # n19>n23
    assert dem(ket, "quy_loi.may.dung_g5b.nghiem") == 1        # n21>n20 được người phán cho là đúng
    khong_phan = chay()["rows"]
    assert dem(khong_phan, "quy_loi.may.dung_g5b.nghiem") == 0 and dem(khong_phan, "quy_loi.may.sai_han.nghiem") == 2


def test_g5b_khong_cuu_canh_ngoc_chieu_hay_bac_cau_da_xep_truoc_do():
    # G5(b) chỉ phán cạnh máy ngoài vàng; một cạnh vừa ngược chiều vừa được phán "đúng" tính là đúng theo G5(b) (thứ tự trong spec)
    ket = chay(g5b={(g(20), g(19)): "dung"})["rows"]
    assert dem(ket, "quy_loi.may.dung_g5b.nghiem") == 1 and dem(ket, "quy_loi.may.nguoc_chieu.nghiem") == 0


# ---------------------------------------------------------------- tập thử không in danh sách


def test_tap_thu_chan_danh_sach():
    with pytest.raises(ValueError, match="tập thử"):
        chay(tap="thu", co_danh_sach=True)
    ket = chay(tap="thu")
    assert ket["danh_sach"] is None and dem(ket["rows"], "quy_loi.vang_pham_vi.nghiem") == 15


def test_tap_la_bat_buoc_va_phai_hop_le():
    hd, a, b, c = the_gioi()
    with pytest.raises(TypeError):
        quy_loi(hd, a, b, c)
    with pytest.raises(ValueError, match="tap"):
        quy_loi(hd, a, b, c, tap="khac")


def _tep(tmp_path, ten, gia_tri):
    duong = tmp_path / ten
    duong.write_text(json.dumps(gia_tri, ensure_ascii=False), encoding="utf-8")
    return str(duong)


def _bo_tep(tmp_path, tap):
    hd, a, b, c = the_gioi()
    for k in a["khai_niem"]:
        k["ten"] = f"{SECRET}-{k['ma']}"        # tên khái niệm bí mật nằm trong G3
    hd["khai_niem"][0]["ten"] = SECRET
    manifest = {"schema": "danh-gia-sach-1", "ma_sach": S, "tap": tap, "chu_de": SECRET, "ghi_chu": {"long": {"sau": SECRET}}}
    return ["--hop-dong", _tep(tmp_path, "hd.json", hd), "--g3", _tep(tmp_path, "g3.json", a), "--g4", _tep(tmp_path, "g4.json", b),
            "--can", _tep(tmp_path, "can.json", c), "--manifest", _tep(tmp_path, "m.json", manifest), "--khong-ap-ly-do-1"]


def test_cli_tap_thu_chi_in_so_khong_in_ten_khai_niem(tmp_path, capsys):
    from danhgia.__main__ import main
    main(["quy-loi", *_bo_tep(tmp_path, "thu")])
    ra = capsys.readouterr().out
    assert "quy_loi.ly_do_2.nghiem" in ra and SECRET not in ra and "G-S-" not in ra
    with pytest.raises(SystemExit):
        main(["quy-loi", *_bo_tep(tmp_path, "thu"), "--ra-danh-sach", str(tmp_path / "ds.json")])
    assert not (tmp_path / "ds.json").exists()


def test_ban_in_ngay_tho_se_ro_ri_bi_mat_nen_test_tren_co_rang():
    # chứng minh chuỗi bí mật nằm ở trường lồng thật: in ngây thơ cả manifest hay cả G3 là lộ
    hd, a, b, c = the_gioi()
    a["khai_niem"][0]["ten"] = SECRET
    assert SECRET in json.dumps(a["khai_niem"][:1])
    assert SECRET in str({"ghi_chu": {"long": {"sau": SECRET}}})


def test_cli_tap_phat_trien_ghi_danh_sach_co_ten(tmp_path, capsys):
    from danhgia.__main__ import main
    ds = tmp_path / "ds.json"
    main(["quy-loi", *_bo_tep(tmp_path, "phat_trien"), "--ra-danh-sach", str(ds)])
    muc = json.loads(ds.read_text(encoding="utf-8"))
    assert len(muc) == 12 and any(SECRET in m["ten_nguon"] for m in muc)
    assert SECRET not in capsys.readouterr().out    # danh sách chỉ ghi tệp, không in ra màn hình


def test_cli_ma_sach_manifest_phai_khop_vang(tmp_path):
    from danhgia.__main__ import main
    tham_so = _bo_tep(tmp_path, "phat_trien")
    manifest = json.loads((tmp_path / "m.json").read_text(encoding="utf-8"))
    manifest["ma_sach"] = "KHAC"
    (tmp_path / "m.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(SystemExit):
        main(["quy-loi", *tham_so])


def test_cli_buoc_phai_chon_ro_ly_do_1(tmp_path):
    from danhgia.__main__ import main
    tham_so = [t for t in _bo_tep(tmp_path, "phat_trien") if t != "--khong-ap-ly-do-1"]
    with pytest.raises(SystemExit):
        main(["quy-loi", *tham_so])


def test_ly_do_5_doi_dung_khi_nguon_nam_trong_hay_ngoai_cua_so():
    hd, a, b, c = the_gioi()
    truoc = quy_loi(hd, a, b, c, tap="phat_trien", muc_loi=MUC_LOI, co_danh_sach=True)
    assert dem(truoc["rows"], "quy_loi.ly_do_5.nghiem") == 1 and dem(truoc["rows"], "quy_loi.ly_do_6.nghiem") == 2
    hd["cap_ung_vien"]["cua_so_dinh_nghia"]["n12"] = ["n11"]      # nguồn G11 vào cửa sổ định nghĩa của đích G12
    sau = quy_loi(hd, a, b, c, tap="phat_trien", muc_loi=MUC_LOI, co_danh_sach=True)
    assert dem(sau["rows"], "quy_loi.ly_do_5.nghiem") == 0 and dem(sau["rows"], "quy_loi.ly_do_6.nghiem") == 3
    lai = {(m["nguon"], m["dich"]) for m in sau["danh_sach"] if m["ly_do"] == 6}
    assert (g(11), g(12)) in lai
    hd["cap_ung_vien"]["cua_so_dinh_nghia"]["n12"] = ["n15"]      # nguồn khác trong cửa sổ: G11 vẫn ngoài cửa sổ
    ngoai = quy_loi(hd, a, b, c, tap="phat_trien")
    assert dem(ngoai["rows"], "quy_loi.ly_do_5.nghiem") == 1
    kiem_tong(sau["rows"])


def test_cua_so_thieu_duoc_bao_co_khi_hop_dong_co_ung_vien_ma_khong_co_cua_so():
    hd, a, b, c = the_gioi()
    hd["cap_ung_vien"]["cua_so_dinh_nghia"] = None
    ket = quy_loi(hd, a, b, c, tap="phat_trien", muc_loi=MUC_LOI)
    assert ket["meta"]["cua_so_thieu"] is True and 5 not in ket["meta"]["khong_ap"]
    assert dem(ket["rows"], "quy_loi.ly_do_6.nghiem") == 1    # chỉ còn cặp ứng viên G13>G14
    assert dem(ket["rows"], "quy_loi.ly_do_5.nghiem") == 2    # cạnh có nguồn trong cửa sổ (G15>G16) rơi về lý do 5 vì không biết cửa sổ
