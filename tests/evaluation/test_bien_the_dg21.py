"""DG-21: biến thể logistic và cross-encoder trong bộ đánh giá.

- A: luật chọn `C`, mô hình logistic cuối (manifest, nạp lại), isotonic ngoài mẫu.
- B: A1 với logistic (`NheLogistic`, lệnh `a1-logistic`).
- C: bộ chấm thay thế (`LogisticSecondaryScorer`, `DiemCoSanScorer`), xuất cặp cho cross-encoder, `pass-phu-thay`, kiểm tái tạo.

Fixture `kho-phat-lai` là bản CẮT 17 node của xstk-ch3-1 v68, nên đặc trưng toàn tài liệu (PageRank, độ khung, số chunk) khác lượt gốc: kiểm tái tạo với
điểm LightGBM đã lưu KHÔNG chạy được trên fixture (xem `test_fixture_cat_khong_tai_tao_duoc_diem_da_luu`), chỉ chạy được trên graph thật (cần
`DANHGIA_KHO_CHUNG`). Trên fixture ta kiểm bộ nối: bộ chấm LightGBM của sản phẩm qua bộ nối ra đúng kết quả chạy trực tiếp `BuildSecondaryMLEdges` trên bản chép kho.
"""
import hashlib
import json
import os
import shutil
import socket
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

from danhgia.__main__ import main
from danhgia.hoc_lai.chon import chon_c_nhieu_nhat
from danhgia.hop_dong import kiem
from tests.evaluation.test_phat_lai import DINH_DANH, DOC, KHO, PB

GOC = Path(__file__).resolve().parents[2]
MO_HINH = GOC / "evaluation" / "mo-hinh" / "dg21"
KET_QUA_DG20 = GOC / "report" / "danh-gia-pha-a" / "DG-20-ket-qua"
SECRET = "BI-MAT-GIA-DG21-XYZ"
for _duong in (GOC / "scripts" / "dg21", GOC / "scripts" / "dg20", GOC / "scripts" / "pass-phu-ml", GOC / "src"):
    if str(_duong) not in sys.path:
        sys.path.insert(0, str(_duong))


def _doc(duong):
    return json.loads(Path(duong).read_text(encoding="utf-8"))


@pytest.fixture
def chan_mang(monkeypatch):
    import doc2roadmap.infrastructure.llm.gemini as gm

    def cam(*a, **k):
        raise AssertionError("đã gọi mạng")

    monkeypatch.setattr(gm, "urlopen", cam)
    monkeypatch.setattr(socket, "socket", cam)
    monkeypatch.setattr(socket, "create_connection", cam)


def bam_cay(thu_muc):
    return {str(p.relative_to(thu_muc)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(thu_muc).rglob("*")) if p.is_file()}


# ================================================================================================ A. luật chọn C và mô hình logistic

def test_chon_c_nhieu_nhat_tinh_tay():
    # 0,1 được chọn 3 lần, 0,001 và 10 một lần: không phải C nhỏ nhất, cũng không phải C lớn nhất
    r = chon_c_nhieu_nhat([0.1, 0.1, 0.001, 10.0, 0.1])
    assert r["chon"] == 0.1 and r["dem"] == {0.001: 1, 0.1: 3, 10.0: 1} and r["hoa"] == [0.1]


def test_chon_c_hoa_lay_c_nho_hon():
    r = chon_c_nhieu_nhat([10.0, 1.0, 1.0, 10.0, 0.01])           # 1 và 10 cùng hai lần
    assert r["chon"] == 1.0 and r["hoa"] == [1.0, 10.0]
    assert chon_c_nhieu_nhat([10.0, 10.0, 1.0, 1.0, 0.1, 0.1])["chon"] == 0.1   # hoà ba bên: nhỏ nhất


def test_chon_c_khong_co_lan_chia_la_loi():
    with pytest.raises(ValueError):
        chon_c_nhieu_nhat([])


@pytest.mark.parametrize("m", ["m1", "m2", "m3"])
def test_manifest_logistic_c_dung_luat_tren_ket_qua_dg20(m):
    manifest = _doc(MO_HINH / f"{m}-logistic" / "manifest.json")
    ban_ghi = [json.loads(d) for d in (KET_QUA_DG20 / f"logistic-{m}-c-rong.jsonl").read_text(encoding="utf-8").splitlines()]
    dem = Counter(r["c"] for r in ban_ghi)                              # đếm độc lập với chon_c_nhieu_nhat
    cao = max(dem.values())
    assert manifest["cau_hinh"]["C"] == min(c for c, n in dem.items() if n == cao)
    assert len(ban_ghi) == 16 and manifest["sach_hoc"] == [f"d01-{i:02d}" for i in range(1, 17)]
    assert "ly_do_chon_c" in manifest and manifest["sha256_c_rong_dg20"] == hashlib.sha256((KET_QUA_DG20 / f"logistic-{m}-c-rong.jsonl").read_bytes()).hexdigest()


def test_m2_la_ca_hoa_c_001_va_10_lay_001():
    manifest = _doc(MO_HINH / "m2-logistic" / "manifest.json")
    assert manifest["dem_c"]["0.01"] == manifest["dem_c"]["10.0"] == 5 and manifest["cau_hinh"]["C"] == 0.01


@pytest.mark.parametrize("m", ["m1", "m2", "m3"])
def test_nap_lai_cho_ra_du_doan_y_het(m):
    import joblib
    thu_muc = MO_HINH / f"{m}-logistic"
    manifest = _doc(thu_muc / "manifest.json")
    assert hashlib.sha256((thu_muc / "model.joblib").read_bytes()).hexdigest() == manifest["sha256_model"]
    mo = joblib.load(thu_muc / "model.joblib")
    x = np.asarray([[np.nan if v is None else v for v in d] for d in manifest["mau_kiem"]["x"]], dtype=manifest["mau_kiem"]["dtype"])
    assert len(manifest["dac_trung"]) == x.shape[1]
    assert np.abs(mo.predict_proba(x)[:, 1] - np.asarray(manifest["mau_kiem"]["p"])).max() < 1e-12
    if m == "m3":
        assert np.isnan(x).any()      # mẫu kiểm có ô thiếu: xử lý thiếu (trung vị + cột chỉ báo) thật sự được dùng


def test_mo_hinh_a1_bam_khop_manifest_nguon():
    a1 = _doc(MO_HINH / "a1-logistic" / "manifest.json")
    for ten, m in (("heading.joblib", "m1"), ("join.joblib", "m2")):
        assert a1["models"][ten] == _doc(MO_HINH / f"{m}-logistic" / "manifest.json")["sha256_model"]
        assert hashlib.sha256((MO_HINH / "a1-logistic" / ten).read_bytes()).hexdigest() == a1["models"][ten]


def test_hieu_chinh_isotonic_hoc_tren_du_doan_ngoai_mau_khong_phai_trong_mau():
    """Nhãn là nhiễu thuần: mô hình khớp quá mức thì dự đoán trong mẫu tách rất rõ, ngoài mẫu thì không. Isotonic học ngoài mẫu vì thế phải phẳng quanh tỉ lệ dương."""
    import hoc_logistic
    import logistic
    from sklearn.isotonic import IsotonicRegression
    rng = np.random.RandomState(7)
    data = {f"s{i}": (rng.normal(size=(60, 40)), rng.randint(0, 2, 60)) for i in range(6)}
    cuon = sorted(data)
    c = 10.0
    iso = hoc_logistic.hieu_chinh_ngoai_mau(data, cuon, c)
    x = np.concatenate([data[b][0] for b in cuon])
    y = np.concatenate([data[b][1] for b in cuon])
    trong_mau = IsotonicRegression(out_of_bounds="clip").fit(logistic.mo_hinh(c).fit(x, y).predict_proba(x)[:, 1], y)   # phép phá: học trên dự đoán trong mẫu
    assert trong_mau.y_thresholds_.max() - trong_mau.y_thresholds_.min() > 0.8            # trong mẫu: tách gần hoàn hảo
    xac_suat = iso.y_thresholds_
    assert abs(xac_suat.mean() - y.mean()) < 0.1 and xac_suat.max() - xac_suat.min() < 0.7  # ngoài mẫu: quanh tỉ lệ dương, không tách
    assert iso.y_thresholds_.max() < trong_mau.y_thresholds_.max() or iso.y_thresholds_.min() > trong_mau.y_thresholds_.min()
    # độc lập với hàm: dự đoán ngoài mẫu tính lại bằng vòng lặp rõ ràng cho đúng cùng bộ hiệu chỉnh
    oof, nhan = [], []
    for de_ra in cuon:
        hoc = [b for b in cuon if b != de_ra]
        xh = np.concatenate([data[b][0] for b in hoc])
        yh = np.concatenate([data[b][1] for b in hoc])
        oof.append(logistic.mo_hinh(c).fit(xh, yh).predict_proba(data[de_ra][0])[:, 1])
        nhan.append(data[de_ra][1])
    mong_doi = IsotonicRegression(out_of_bounds="clip").fit(np.concatenate(oof), np.concatenate(nhan))
    assert np.array_equal(mong_doi.y_thresholds_, iso.y_thresholds_)


# ================================================================================================ C. bộ chấm thay thế

@pytest.fixture(scope="module")
def cap():
    from danhgia.phat_lai.pass_phu import cap_ung_vien
    return cap_ung_vien(KHO, DOC, PB)


class Ghi:
    """Bộ chấm ghi lại các dòng đặc trưng mà `BuildSecondaryMLEdges` thực sự gửi tới bộ chấm."""
    metadata = {"version": "ghi", "model_sha256": "0"}

    def __init__(self):
        self.dong = []

    def score(self, rows):
        self.dong.extend(rows)
        return [0.5] * len(rows)

    def calibrate(self, scores):
        return [0.5] * len(scores)


def test_cap_xuat_khop_tung_dong_ma_use_case_gui_cho_bo_cham(cap):
    from danhgia.phat_lai.bo_cham import dac_trung_sha
    from danhgia.phat_lai.pass_phu import chay_pass_phu
    ghi = Ghi()
    chay_pass_phu(KHO, DOC, PB, ghi)
    assert len(ghi.dong) == len(cap) > 0
    assert [dac_trung_sha(d) for d in ghi.dong] == [dac_trung_sha(h[3]) for h in cap]   # cùng số dòng, cùng thứ tự, cùng nội dung
    cap_hai_chieu = Counter(h[0] for h in cap)
    assert max(cap_hai_chieu.values()) == 2          # fixture có cặp chấm cả hai chiều
    chieu = {(h[0], h[1], h[2]) for h in cap}
    assert len(chieu) == len(cap)                     # mỗi chiều đúng một dòng
    for ma, x, y in list(chieu):
        if cap_hai_chieu[ma] == 2:
            assert (ma, y, x) in chieu


def test_dong_cap_ce_dung_khuon_ce_hoc(cap):
    van_ban = [h[4] for h in cap]
    for h, v in zip(cap, van_ban):
        assert {"id", "y_ten", "x_ten", "x_dinh_nghia", "cau", "cau_neo", "cau_co_x"} <= set(v)    # đủ trường mà ce_hoc.Encoder đọc
        assert v["id"] == f"{h[0]}|{h[1]}|{h[2]}"
        assert all(0 <= i < len(v["cau"]) for i in v["cau_co_x"]) and v["cau_co_x"]               # ứng viên có tên X trong cửa sổ Y
    assert any(" @ " in " " + c + " " for v in van_ban for c in v["cau"])                          # có đánh dấu X


def test_phan_van_ban_giong_make_row_cua_lan_hoc():
    import dung_du_lieu_e6 as e6
    from danhgia.xuat.cap_ce import phan_van_ban
    from doc2roadmap.infrastructure.secondary_tokenizer import VietnameseWordTokenizer
    cau = ["Tập hợp là khái niệm cơ bản của toán học .", "Mỗi phần tử thuộc tập hợp con của không gian véc tơ con .", "Không gian véc tơ con có phần tử 0 ."]
    ten_x, ten_y = ["phần tử", "pt"], ["không gian véc tơ", "tập hợp"]
    mong_doi, _ = e6.make_row(cau, 1, {1, 2}, ten_x, ten_y, "Phần tử  là thành viên của tập hợp")
    thuc = phan_van_ban(cau, 1, {1, 2}, ten_x, ten_y, "Phần tử  là thành viên của tập hợp", VietnameseWordTokenizer())
    for khoa in ("y_ten", "x_ten", "x_dinh_nghia", "cau", "cau_neo", "cau_co_x"):
        assert thuc[khoa] == mong_doi[khoa], khoa
    assert any("@" in c.split() for c in thuc["cau"]) and any("#" in c.split() for c in thuc["cau"])
