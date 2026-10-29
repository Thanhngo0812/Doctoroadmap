"""Vé DG-17: Hình 3 (điểm F1 theo cuốn, có CI) và Hình 4 (thác nước quy lỗi) do `bang-hinh` sinh."""
import copy
import json
import re
import xml.etree.ElementTree as ET

import numpy as np
import pytest

from danhgia.bao_cao import hinh, so_lieu as S
from tests.evaluation import bang_hinh_ho_tro as H
from tests.evaluation.test_bang_hinh import RefLcg, SEED, SO_VONG, chay, ref_ci_f1

SVG = "{http://www.w3.org/2000/svg}"
NS = {"s": "http://www.w3.org/2000/svg"}
# Bảng màu khâu viết thẳng từ palette.md của skill dataviz (bảy ô đầu của bảng phân loại, sáng / tối), độc lập với hằng số trong mã
MAU_DUNG = {"a1-a2": ("#2a78d6", "#3987e5"), "a3": ("#eb6834", "#d95926"), "a4": ("#1baf7a", "#199e70"), "a5": ("#eda100", "#c98500"),
            "a6-a7": ("#e87ba4", "#d55181"), "a8": ("#008300", "#008300"), "a9-a10": ("#6250d6", "#9085e9")}
KHAU_CUA_LY_DO = {1: "a1-a2", 2: "a3", 3: "a4", 4: "a5", 5: "a6-a7", 6: "a8", 7: "a9-a10"}


def doc_svg(ra, ten):
    text = (ra / ten).read_text(encoding="utf-8")
    return text, ET.fromstring(text)


def ref_ci_cuon(ds, so_vong=SO_VONG, seed=SEED):
    rng, mau = RefLcg(seed), []
    for _ in range(so_vong):
        c = [ds[rng.chi_so(len(ds))] for _ in ds]
        tp, fp, fn = (sum(d[i] for d in c) for i in range(3))
        mau.append(2 * tp / (2 * tp + fp + fn))
    return np.percentile(mau, [2.5, 97.5])


def x_ve_gia_tri(goc, x):
    v = goc.find(".//s:rect[@id='vung-ve']", NS)
    x0, w = float(v.get("x")), float(v.get("width"))
    lo, hi = float(v.get("data-truc-min")), float(v.get("data-truc-max"))
    return lo + (float(x) - x0) / w * (hi - lo)


def chu_cua(goc):
    return " | ".join("".join(t.itertext()) for t in goc.iter(f"{SVG}text"))


# ------------------------------------------------------------------------------------------------ chung


def test_hai_svg_hop_le_co_title_desc_va_hai_nen(tmp_path, capsys):
    ra, _ = chay(tmp_path, capsys)
    for ten, tieu_de in (("hinh-3.svg", "Hình 3. F1 cạnh tiên quyết theo từng cuốn"), ("hinh-4.svg", "Hình 4. Quan hệ tiên quyết bị mất qua từng khâu")):
        text, goc = doc_svg(ra, ten)
        assert goc.tag == f"{SVG}svg"
        assert goc.find("s:title", NS).text == tieu_de
        assert len(goc.find("s:desc", NS).text) > 40
        assert "@media (prefers-color-scheme: dark)" in text and "#1a1a19" in text and "#fcfcfb" in text
        assert "href" not in text and "<image" not in text and "<script" not in text            # không phụ thuộc thư viện hay tệp ngoài


# ------------------------------------------------------------------------------------------------ Hình 3


def test_hinh_3_cham_va_thanh_ci_ve_dung_gia_tri_so_lieu(tmp_path, capsys):
    ra, _ = chay(tmp_path, capsys)
    _, goc = doc_svg(ra, "hinh-3.svg")
    h3 = json.loads((ra / "so-lieu.json").read_text(encoding="utf-8"))["hinh_3"]
    for he in ("chinh", "b5"):
        cham = [float(c.get("cx")) for c in goc.iter(f"{SVG}circle") if c.get("data-he") == he and "diem" in c.get("class", "")]
        thanh = [(float(l.get("x1")), float(l.get("x2"))) for l in goc.iter(f"{SVG}line") if l.get("data-he") == he]
        mong = [m[he] for m in h3["sach"]] + [h3["trung_binh"][he]]
        assert len(cham) == len(thanh) == 4                                  # ba cuốn và hàng trung bình
        for cx, (a, b), m in zip(cham, thanh, mong):
            assert x_ve_gia_tri(goc, cx) == pytest.approx(m["gia_tri"], abs=0.002)
            assert x_ve_gia_tri(goc, a) == pytest.approx(m["thap"], abs=0.002)
            assert x_ve_gia_tri(goc, b) == pytest.approx(m["cao"], abs=0.002)


def test_hinh_3_khong_cat_ci_va_truc_tu_0_den_1(tmp_path, capsys):
    ra, _ = chay(tmp_path, capsys)
    _, goc = doc_svg(ra, "hinh-3.svg")
    v = goc.find(".//s:rect[@id='vung-ve']", NS)
    assert (float(v.get("data-truc-min")), float(v.get("data-truc-max"))) == (0.0, 1.0)
    x0, x1 = float(v.get("x")), float(v.get("x")) + float(v.get("width"))
    thanh = [l for l in goc.iter(f"{SVG}line") if l.get("data-he")]
    assert thanh
    for l in thanh:
        assert x0 - 1e-6 <= float(l.get("x1")) <= float(l.get("x2")) <= x1 + 1e-6
    # CI của cuốn C (F1 0,9) chạm trên 0,85: hình có chỗ cho nó, không bị chặn ở mép trục cắt
    assert any(x_ve_gia_tri(goc, l.get("x2")) > 0.85 for l in thanh)


def test_hinh_3_ci_cuon_va_ci_trung_binh_khop_bootstrap_doc_lap(tmp_path, capsys):
    ra, _ = chay(tmp_path, capsys)
    h3 = json.loads((ra / "so-lieu.json").read_text(encoding="utf-8"))["hinh_3"]
    a = h3["sach"][0]["chinh"]
    thap, cao = ref_ci_cuon(H.F1_CHINH["A"])
    assert a["gia_tri"] == pytest.approx(0.7) and (a["thap"], a["cao"]) == pytest.approx((thap, cao), abs=1e-12)
    tb = h3["trung_binh"]["chinh"]
    t2, c2 = ref_ci_f1(H.F1_CHINH)
    assert tb["gia_tri"] == pytest.approx(0.7) and (tb["thap"], tb["cao"]) == pytest.approx((t2, c2), abs=1e-12)


def test_hinh_3_nhan_viet_nhan_truc_va_nhan_hang(tmp_path, capsys):
    ra, _ = chay(tmp_path, capsys)
    _, goc = doc_svg(ra, "hinh-3.svg")
    chu = chu_cua(goc)
    for mong in ("Toán rời rạc", "Xác suất thống kê", "Máy học", "Trung bình", "F1 cạnh tiên quyết (trục từ 0 đến 1)", "Hệ chính", "B5 mô hình đọc thẳng",
                 "0,0", "0,2", "1,0"):
        assert mong in chu


def test_hinh_3_hang_thieu_so_hien_gach_ngang(tmp_path, capsys):
    rows = [r for r in H.dong_b5() if r["ma_sach"] != "B"]                  # B5 không có số ở cuốn B
    ra, _ = chay(tmp_path, capsys, "--dong", H.ghi_json(tmp_path / "d1.json", H.dong_he_chinh() + H.dong_b1()), H.ghi_json(tmp_path / "d2.json", rows),
                 ra="ra-thieu", co_b5=False)
    _, goc = doc_svg(ra, "hinh-3.svg")
    gach = [t for t in goc.iter(f"{SVG}text") if t.get("data-he") == "b5" and "".join(t.itertext()) == "—"]
    assert len(gach) == 1
    assert len([c for c in goc.iter(f"{SVG}circle") if c.get("data-he") == "b5" and "diem" in c.get("class", "")]) == 3


# ------------------------------------------------------------------------------------------------ Hình 4


def _thanh_giam(goc):
    return {int(e.get("data-ly-do")): e for e in goc.iter(f"{SVG}rect") if "cot" in e.get("class", "").split()}


def test_hinh_4_cot_dau_cong_cac_cot_giam_va_cot_cuoi_khop(tmp_path, capsys):
    ra, _ = chay(tmp_path, capsys)
    _, goc = doc_svg(ra, "hinh-4.svg")
    gia_tri = {}
    for t in goc.iter(f"{SVG}text"):
        if "gia-tri" in t.get("class", ""):
            khoa = ("ly_do", int(t.get("data-ly-do"))) if t.get("data-ly-do") else ("cot", t.get("data-cot"))
            gia_tri[khoa] = int("".join(t.itertext()))
    tong = gia_tri[("cot", "tong")]
    assert tong == H.TONG_QUY_LOI["tong"]
    giam = {k[1]: v for k, v in gia_tri.items() if k[0] == "ly_do"}
    assert giam == {i: v for i, v in H.TONG_QUY_LOI["ly_do"].items() if v is not None}
    assert gia_tri[("cot", "dung")] + sum(giam.values()) == tong
    # cùng điều đó đo trên hình học, không trên chữ: chiều cao thanh giảm cộng chiều cao thanh "đúng" bằng thanh đầu
    thanh = _thanh_giam(goc)
    y_day = float(goc.find(".//s:line[@class='truc']", NS).get("y1"))
    dinh = {e.get("data-cot"): float(re.search(r"Q[\d.]+ ([\d.]+) ", e.get("d")).group(1)) for e in goc.iter(f"{SVG}path") if e.get("data-cot")}
    cao_tong, cao_dung = y_day - dinh["tong"], y_day - dinh["dung"]
    assert cao_dung + sum(float(e.get("height")) for e in thanh.values()) == pytest.approx(cao_tong, abs=0.1)
    # tỉ lệ nhất quán: mỗi thanh giảm cao đúng giá trị × (cao_tong / tổng)
    for i, e in thanh.items():
        assert float(e.get("height")) == pytest.approx(giam[i] * cao_tong / tong, abs=0.05)


def test_hinh_4_ly_do_khong_ap_hien_nhan_va_khong_ve_cot(tmp_path, capsys):
    ra, _ = chay(tmp_path, capsys)
    _, goc = doc_svg(ra, "hinh-4.svg")
    for i in (1, 5):
        nhan = [t for t in goc.iter(f"{SVG}text") if t.get("data-ly-do") == str(i)]
        assert [("".join(t.itertext()), t.get("class")) for t in nhan] == [("không áp", "muted")]
    assert sorted(_thanh_giam(goc)) == [2, 3, 4, 6, 7]


def test_hinh_4_mau_tung_khau_dung_bang_mau_khau_sang_va_toi(tmp_path, capsys):
    ra, _ = chay(tmp_path, capsys)
    text, goc = doc_svg(ra, "hinh-4.svg")
    sang, toi = text.split("@media (prefers-color-scheme: dark)")
    for i, e in _thanh_giam(goc).items():
        khau = KHAU_CUA_LY_DO[i]
        assert f"khau-{khau}" in e.get("class").split()
        s, t = MAU_DUNG[khau]
        assert re.search(rf"\.khau-{khau}\{{fill:{s}\}}", sang)
        assert re.search(rf"\.khau-{khau}\{{fill:{t}\}}", toi)
    # chú giải đủ bảy khâu, mỗi khâu một ô màu đúng hex
    chu = chu_cua(goc)
    for khau in ("A1/A2", "A3", "A4", "A5", "A6/A7", "A8", "A9/A10"):
        assert khau in chu
    for k, (s, _) in MAU_DUNG.items():
        assert any(f"khau-{k}" in e.get("class", "").split() for e in goc.iter(f"{SVG}rect") if e.get("width") == "10")


def test_hinh_4_nhan_theo_bang_8_va_thanh_khong_day_qua_24px(tmp_path, capsys):
    ra, _ = chay(tmp_path, capsys)
    _, goc = doc_svg(ra, "hinh-4.svg")
    tu = " ".join(chu_cua(goc).replace("|", " ").split())
    # mỗi nhãn bị ngắt dòng ở 13 ký tự; đọc lại từng từ theo thứ tự trong hình
    for nhan in ("Không trích được khái niệm", "Gộp nhầm hoặc tách đôi", "Bị bỏ khỏi dãy học", "Suy luận không đề xuất", "Làm mềm hoặc xếp sai"):
        mau = r"\s+".join(re.escape(w) for w in nhan.split())
        assert re.search(mau, tu), nhan
    for e in _thanh_giam(goc).values():
        assert float(e.get("width")) <= 24


def test_thac_nuoc_tu_choi_du_lieu_khong_khep_kin():
    rows = [r for s in H.SACH for r in H.quy_loi(s)["theo_chuong"]]
    meta = {s: {"khong_ap": [1, 5]} for s in H.SACH}
    assert S.thac_nuoc(rows, "chinh", meta)["dung"] == 27
    hong = copy.deepcopy(rows)
    for r in hong:
        if r["thuoc"] == "quy_loi.dung.nghiem":
            r["gia_tri"] += 1                                          # tổng đúng + lý do vượt tổng cạnh vàng
    with pytest.raises(ValueError, match="không khép kín"):
        S.thac_nuoc(hong, "chinh", meta)
    with pytest.raises(ValueError, match="không áp"):
        S.thac_nuoc(rows, "chinh", {s: {"khong_ap": [1, 2, 5]} for s in H.SACH})        # lý do 2 khai không áp mà có 9 cạnh


def test_svg_hong_bi_kiem_xml_bat():
    with pytest.raises(ET.ParseError):
        hinh.kiem_xml("<svg><title>x</svg>")


def test_hinh_4_cac_cot_giam_noi_tiep_tu_dinh_xuong_dap_cot_dung():
    from danhgia.bao_cao import hinh as Hn

    h4 = {"he": "chinh", "so_cuon": 3, "tong": 60, "dung": 27, "khong_ap": [1, 5],
          "ly_do": {1: None, 2: 9, 3: 5, 4: 3, 5: None, 6: 10, 7: 6}}
    goc = ET.fromstring(Hn.hinh_4(h4))
    thanh = sorted(_thanh_giam(goc).items())
    y_day = float(goc.find(".//s:line[@class='truc']", NS).get("y1"))
    dinh = {e.get("data-cot"): float(re.search(r"Q[\d.]+ ([\d.]+) ", e.get("d")).group(1)) for e in goc.iter(f"{SVG}path") if e.get("data-cot")}
    # cột đầu bắt đầu ở đỉnh cột tổng; mỗi cột sau bắt đầu đúng ở đáy cột trước; đáy cột cuối bằng đỉnh cột "đúng"
    ky_vong_tren = dinh["tong"]
    for _, e in thanh:
        y, h = float(e.get("y")), float(e.get("height"))
        assert y == pytest.approx(ky_vong_tren, abs=0.1)
        ky_vong_tren = y + h
    assert ky_vong_tren == pytest.approx(dinh["dung"], abs=0.1)
    assert ky_vong_tren < y_day
