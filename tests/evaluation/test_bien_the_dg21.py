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
from types import SimpleNamespace

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


# ================================================================================================ C. bộ chấm logistic và điểm có sẵn

M3 = MO_HINH / "m3-logistic"


def test_bo_cham_logistic_khop_predict_proba_va_isotonic_tinh_tay(cap):
    import joblib
    from danhgia.phat_lai.bo_cham import LogisticSecondaryScorer
    from doc2roadmap.domain.secondary_features import FEATURE_NAMES
    bo = LogisticSecondaryScorer(M3)
    dong = [h[3] for h in cap]
    diem = bo.score(dong)
    mo = joblib.load(M3 / "model.joblib")
    x = np.asarray([[np.nan if d[t] in ("", None) else float(d[t]) for t in FEATURE_NAMES] for d in dong], dtype=float)
    assert np.isnan(x).any()                                              # fixture có ô thiếu: đường xử lý NaN thật sự chạy
    assert np.abs(np.asarray(diem) - mo.predict_proba(x)[:, 1]).max() < 1e-12
    # isotonic nội suy tuyến tính từng đoạn, tính tay bằng vòng lặp rồi so với bộ chấm
    hc = _doc(M3 / "manifest.json")["hieu_chinh"]
    d, v = hc["diem"], hc["xac_suat"]
    for p, thuc in zip(diem, bo.calibrate(diem)):
        if p <= d[0]:
            mong_doi = v[0]
        elif p >= d[-1]:
            mong_doi = v[-1]
        else:
            i = max(j for j in range(len(d) - 1) if d[j] <= p)
            mong_doi = v[i] + (p - d[i]) / (d[i + 1] - d[i]) * (v[i + 1] - v[i])
        assert thuc == pytest.approx(mong_doi, abs=1e-12)
    assert len(set(np.round(bo.calibrate(diem), 9))) > 1                 # hiệu chỉnh không phẳng


def test_bo_cham_logistic_tu_choi_mo_hinh_bi_sua(tmp_path):
    from danhgia.phat_lai.bo_cham import LogisticSecondaryScorer
    shutil.copytree(M3, tmp_path / "m")
    with (tmp_path / "m" / "model.joblib").open("ab") as f:
        f.write(b"x")
    with pytest.raises(ValueError, match="băm"):
        LogisticSecondaryScorer(tmp_path / "m")


def _tep_diem(cap_, duong, sua=None):
    from danhgia.phat_lai.bo_cham import dac_trung_sha
    dau = {"schema": "diem-co-san-1", "mo_hinh": "ce-thu", "sha256_mo_hinh": "0" * 64, "sha256_hieu_chinh": "1" * 64}
    n = max(1, len(cap_) - 1)
    hang = [{"id": f"{h[0]}|{h[1]}|{h[2]}", "dac_trung_sha": dac_trung_sha(h[3]), "p": round(0.1 + 0.8 * i / n, 6),
             "xac_suat": round(0.2 + 0.6 * i / n, 6)} for i, h in enumerate(cap_)]
    if sua:
        hang = sua(hang)
    Path(duong).write_text("".join(json.dumps(d) + "\n" for d in [dau, *hang]), encoding="utf-8")
    return duong


def test_diem_co_san_thieu_diem_la_loi_khong_phai_0(cap, tmp_path):
    from danhgia.phat_lai.bo_cham import DiemCoSanScorer
    dong = [h[3] for h in cap]
    bo = DiemCoSanScorer(_tep_diem(cap, tmp_path / "d.jsonl"))
    diem = bo.score(dong)
    assert len(diem) == len(cap) and bo.calibrate(diem)[0] == 0.2 and bo.calibrate(diem)[-1] == 0.8
    with pytest.raises(ValueError, match="thiếu hay thừa"):
        DiemCoSanScorer(_tep_diem(cap, tmp_path / "t.jsonl", lambda h: h[:-1])).score(dong)
    with pytest.raises(ValueError, match="thiếu p"):
        DiemCoSanScorer(_tep_diem(cap, tmp_path / "n.jsonl", lambda h: [{**h[0], "p": None}, *h[1:]]))
    with pytest.raises(ValueError, match="không khớp"):
        DiemCoSanScorer(_tep_diem(cap, tmp_path / "h.jsonl", lambda h: list(reversed(h)))).score(dong)   # đổi thứ tự cặp


# ================================================================================================ lệnh cap-ce, pass-phu-thay

@pytest.fixture(scope="module")
def hd_chinh(tmp_path_factory):
    from danhgia.xuat import xuat
    duong = tmp_path_factory.mktemp("chinh21") / "chinh.json"
    duong.write_text(json.dumps(xuat(KHO, DOC, PB, dinh_danh=DINH_DANH), ensure_ascii=False), encoding="utf-8")
    return duong


def _cap_ce(tmp_path):
    ra = tmp_path / "cap.jsonl"
    assert main(["cap-ce", "--kho", str(KHO), "--doc", DOC, "--phien-ban", str(PB), "--ra", str(ra)]) == 0
    return [json.loads(d) for d in ra.read_text(encoding="utf-8").splitlines()]


def test_cap_ce_moi_chieu_dung_mot_dong_va_thu_tu_bo_cham(cap, tmp_path, chan_mang):
    dong = _cap_ce(tmp_path)
    assert [d["id"] for d in dong] == [f"{h[0]}|{h[1]}|{h[2]}" for h in cap]
    assert len({d["id"] for d in dong}) == len(dong)
    theo_cap = Counter(d["pair_id"] for d in dong)
    ids = {d["id"] for d in dong}
    for d in dong:
        if theo_cap[d["pair_id"]] == 2:                        # luật chấm hai chiều: chiều ngược lại có mặt
            assert f"{d['pair_id']}|{d['y']}|{d['x']}" in ids
    assert set(theo_cap.values()) == {1, 2}                    # fixture có cả cặp một chiều lẫn hai chiều


@pytest.mark.parametrize("bo,he", [("logistic", "a8_logistic"), ("diem-co-san", "a8_cross_encoder")])
def test_pass_phu_thay_ra_hop_dong_hop_le_va_khong_ghi_kho(bo, he, cap, hd_chinh, tmp_path, chan_mang):
    truoc = bam_cay(KHO)
    them = (["--mo-hinh", str(M3)] if bo == "logistic" else ["--diem", str(_tep_diem(cap, tmp_path / "d.jsonl"))])
    ra = tmp_path / "ra.json"
    assert main(["pass-phu-thay", "--kho", str(KHO), "--doc", DOC, "--phien-ban", str(PB), "--bo-cham", bo, *them, "--hop-dong", str(hd_chinh),
                 "--commit", "b" * 40, "--ngay-chay", "2026-10-30", "--ra", str(ra)]) == 0
    hd = _doc(ra)
    assert kiem(hd) == [] and hd["dinh_danh"]["he"] == he and hd["dinh_danh"]["commit"] == "b" * 40
    assert hd["chi_phi"]["tong"]["usd"] == 0 and hd["chi_phi"]["tong"]["token_vao"] == 0
    assert bam_cay(KHO) == truoc                                # kho lượt chính không bị ghi


def test_pass_phu_thay_diem_co_san_khong_the_dung_cho_dong_khac(cap, hd_chinh, tmp_path, chan_mang):
    """Điểm của cặp này không được gán cho dòng đặc trưng khác: dấu vân tay bắt được."""
    tep = _tep_diem(cap, tmp_path / "d.jsonl", lambda h: [{**h[0], "dac_trung_sha": "f" * 64}, *h[1:]])
    with pytest.raises(ValueError, match="không khớp"):
        main(["pass-phu-thay", "--kho", str(KHO), "--doc", DOC, "--phien-ban", str(PB), "--bo-cham", "diem-co-san", "--diem", str(tep),
              "--hop-dong", str(hd_chinh), "--ra", str(tmp_path / "ra.json")])


# ================================================================================================ kiểm tái tạo đúng mô hình

E1 = GOC / "tests" / "evaluation" / "fixtures" / "mo-hinh-e5-d01-a-v1"


def _chay_kiem(kho, mo_hinh, capsys):
    argv = ["pass-phu-thay", "--kho", str(kho), "--doc", DOC, "--phien-ban", str(PB), "--bo-cham", "lightgbm", "--kiem-tai-tao"]
    ma = main(argv + (["--mo-hinh", str(mo_hinh)] if mo_hinh else []))
    ra = capsys.readouterr()
    return ma, ra.out, ra.err


def _kho_dung_bang_e5_v1(tmp_path):
    """Bản chép fixture mà bước pass phụ do mô hình `e5-d01-a-v1` dựng: cạnh và nhật ký pass phụ của v2 ghi lại đúng kết quả mô hình đó, và manifest ghi
    `config.scorer` như graph thật. (Fixture gốc là bản cắt 17 node nên điểm đã lưu không còn tái tạo được bằng bất kỳ mô hình nào, kể cả v1.)"""
    from danhgia.phat_lai.pass_phu import chay_pass_phu
    from doc2roadmap.infrastructure.secondary_model import LightGBMSecondaryScorer
    bo = LightGBMSecondaryScorer(model_dir=E1)
    artifact, _ = chay_pass_phu(KHO, DOC, PB, bo)
    kho = tmp_path / "kho"
    shutil.copytree(KHO, kho)
    thu_muc = kho / "graph" / DOC / "v2"
    payload = _doc(thu_muc / "graph.json")
    for k in ("secondary_edges", "secondary_log"):
        payload[k] = artifact.payload[k]
    (thu_muc / "graph.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    manifest = _doc(thu_muc / "manifest.json")
    manifest["config"]["scorer"] = bo.metadata
    (thu_muc / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
    return kho


def _so_voi(kho, mo_hinh):
    from danhgia.phat_lai.pass_phu import phat_lai_voi_bo_cham, so_voi_da_luu
    from doc2roadmap.infrastructure.secondary_model import LightGBMSecondaryScorer
    ket_qua, artifact = phat_lai_voi_bo_cham(kho, DOC, PB, LightGBMSecondaryScorer(model_dir=mo_hinh))
    return so_voi_da_luu(ket_qua, artifact)


def test_e5_v1_dong_bang_trong_fixture_khop_manifest_sha():
    assert hashlib.sha256((E1 / "model.txt").read_bytes()).hexdigest() == _doc(E1 / "manifest.json")["sha256_model"]
    assert _doc(E1 / "manifest.json")["phien_ban"] == "e5-d01-a-v1"
    assert _doc(GOC / "vendor" / "a8-pass-phu-ml" / "manifest.json")["phien_ban"] != "e5-d01-a-v1"    # mô hình sản phẩm hiện tại là bản khác


def test_kiem_tai_tao_dung_mo_hinh_da_dung_lech_0(tmp_path, capsys, chan_mang):
    kho = _kho_dung_bang_e5_v1(tmp_path)
    so = _so_voi(kho, E1)
    assert so["canh_phu_dung"] and so["nhat_ky_phu_dung"] and so["mo_hinh_khop"] is True
    assert so["canh_phu_chi_o_moi"] == so["canh_phu_chi_o_cu"] == 0 and so["so_canh_phu"][0] == so["so_canh_phu"][1] > 0
    ma, out, err = _chay_kiem(kho, E1, capsys)                    # lệnh cũng thấy khớp và không cảnh báo
    assert "CẢNH BÁO" not in err and "mo_hinh_khop_graph" in out


def test_kiem_tai_tao_sai_mo_hinh_lech_va_canh_bao(tmp_path, capsys, chan_mang):
    """Bảng phá: không truyền đúng mô hình đã dựng graph (mô hình sản phẩm hiện tại) thì lệch, và lệnh nói rõ nguyên nhân."""
    kho = _kho_dung_bang_e5_v1(tmp_path)
    so = _so_voi(kho, None)
    assert so["mo_hinh_khop"] is False and not (so["canh_phu_dung"] and so["nhat_ky_phu_dung"])
    ma, out, err = _chay_kiem(kho, None, capsys)
    assert ma == 1 and "CẢNH BÁO: mô hình chấm khác mô hình đã dựng graph" in err


def test_kiem_tai_tao_graph_khong_ghi_mo_hinh_thi_canh_bao_phai_truyen_mo_hinh(capsys, chan_mang):
    ma, out, err = _chay_kiem(KHO, E1, capsys)     # fixture gốc: manifest edges không ghi `config.scorer`
    assert "graph không ghi mô hình đã dựng" in err


# ================================================================================================ script cross-encoder (phần không cần torch)

def test_ce_cham_nhap_duoc_khong_can_torch_va_ghi_diem_nap_duoc(cap, tmp_path):
    import ce_cham
    from danhgia.phat_lai.bo_cham import DiemCoSanScorer, dac_trung_sha
    dong_cap = [{"id": f"{h[0]}|{h[1]}|{h[2]}", "dac_trung_sha": dac_trung_sha(h[3])} for h in cap]
    p = [0.05 + 0.9 * i / (len(cap) - 1) for i in range(len(cap))]
    hc = {"diem": [0.0, 0.5, 1.0], "xac_suat": [0.0, 0.25, 1.0]}
    ce_cham.ghi_diem(tmp_path / "d.jsonl", dong_cap, p, hc, {"mo_hinh": "thu", "sha256_mo_hinh": "0" * 64, "sha256_hieu_chinh": "1" * 64})
    bo = DiemCoSanScorer(tmp_path / "d.jsonl")
    diem = bo.score([h[3] for h in cap])
    assert diem == pytest.approx(p)
    for v, x in zip(diem, bo.calibrate(diem)):                                 # isotonic tính tay trên hai đoạn của bộ hiệu chỉnh thử
        assert x == pytest.approx(v * 0.5 if v <= 0.5 else 0.25 + (v - 0.5) * 1.5)
    with pytest.raises(ValueError, match="điểm"):
        ce_cham.ghi_diem(tmp_path / "x.jsonl", dong_cap, p[:-1], hc, {})       # thiếu điểm là lỗi, không đệm 0


def test_ce_hieu_chinh_isotonic_tinh_tay_va_nep_phai_roi_nhau():
    import ce_hieu_chinh
    ngoai_mau = {k: [{"id": f"n{k}-{i}", "p": [0.1 * (1 + 2 * k + i), 0.0]} for i in range(2)] for k in range(4)}   # 8 điểm tăng dần 0,1 … 0,8 (hai điểm mỗi nếp)
    nhan = {}
    for k in range(4):
        for i in range(2):
            nhan[f"n{k}-{i}"] = "can_de_hieu" if (2 * k + i) in (1, 4, 6, 7) else "khong"     # y = 0,1,0,0,1,0,1,1 theo điểm
    kq = ce_hieu_chinh.hieu_chinh_tu_ngoai_mau(ngoai_mau, nhan)
    # PAV tính độc lập bằng vòng gộp các khối vi phạm đơn điệu
    khoi = [[v, 1] for v in (0, 1, 0, 0, 1, 0, 1, 1)]
    i = 0
    while i < len(khoi) - 1:
        if khoi[i][0] / khoi[i][1] > khoi[i + 1][0] / khoi[i + 1][1] + 1e-12:
            khoi[i] = [khoi[i][0] + khoi[i + 1][0], khoi[i][1] + khoi[i + 1][1]]
            del khoi[i + 1]
            i = max(0, i - 1)
        else:
            i += 1
    mong_doi = [s / n for s, n in khoi for _ in range(n)]
    gan = np.interp([0.1 * j for j in range(1, 9)], kq["diem"], kq["xac_suat"])
    assert gan.tolist() == pytest.approx(mong_doi)
    ngoai_mau[1][0] = {"id": "n0-0", "p": [0.5, 0.0]}                           # id trùng giữa hai nếp
    with pytest.raises(ValueError, match="hai nếp"):
        ce_hieu_chinh.hieu_chinh_tu_ngoai_mau(ngoai_mau, nhan)


# ================================================================================================ giữ mù tập thử cho ba lệnh mới

def _kho_co_bi_mat(tmp_path):
    """Bản chép fixture mà bí danh khái niệm (xuất vào hợp đồng) mang chuỗi bí mật giả."""
    kho = tmp_path / "kho"
    shutil.copytree(KHO, kho)

    def nhiem(x):
        if isinstance(x, dict):
            return {k: (v + [{"name": f"{SECRET} bí danh", "evidence": [], "candidate_id": "x"}] if k == "aliases" and isinstance(v, list) else nhiem(v))
                    for k, v in x.items()}
        return [nhiem(v) for v in x] if isinstance(x, list) else x
    for g in (kho / "graph" / DOC).glob("v*/graph.json"):      # bí danh không có trong văn bản nên không đổi đặc trưng; hợp đồng ra có xuất bí danh
        g.write_text(json.dumps(nhiem(_doc(g)), ensure_ascii=False), encoding="utf-8")
    return kho


def test_lenh_moi_khong_lo_bi_mat_len_man_hinh(tmp_path, monkeypatch, capsys, hd_chinh, cap, chan_mang):
    kho = _kho_co_bi_mat(tmp_path)

    def gom(argv):
        try:
            main(argv)
        except SystemExit as e:
            print(e.code)
        ra = capsys.readouterr()
        return ra.out + ra.err
    hd_thu = tmp_path / "hd-chinh.json"
    hd_thu.write_text(hd_chinh.read_text(encoding="utf-8"), encoding="utf-8")
    cung = ["--kho", str(kho), "--doc", DOC, "--phien-ban", str(PB)]
    cac_lenh = {
        "cap-ce": ["cap-ce", *cung, "--ra", str(tmp_path / "cap.jsonl")],
        "pass-phu-thay": ["pass-phu-thay", *cung, "--bo-cham", "logistic", "--mo-hinh", str(M3), "--hop-dong", str(hd_thu), "--ra", str(tmp_path / "ra.json")],
        "kiem": ["pass-phu-thay", *cung, "--bo-cham", "lightgbm", "--kiem-tai-tao"],
    }
    for ten, argv in cac_lenh.items():
        chu = gom(argv)
        assert SECRET not in chu and chu.strip(), ten                          # có in số, nhưng không lộ
    assert SECRET in (tmp_path / "ra.json").read_text(encoding="utf-8")        # chuỗi bí mật thật sự đã đi vào hợp đồng ra (tệp, theo thiết kế)
    # bản in ngây thơ làm lộ chuỗi: cổng thật sự chặn chứ không phải đầu vào vô hại
    import danhgia.phat_lai.lenh_pass_phu as lenh
    monkeypatch.setattr(lenh, "cong", SimpleNamespace(in_allowlist=lambda d, cho_phep: print((tmp_path / "ra.json").read_text(encoding="utf-8"))))
    assert SECRET in gom(cac_lenh["pass-phu-thay"])


def test_a1_logistic_khong_lo_bi_mat_len_man_hinh(tmp_path, monkeypatch, capsys):
    from tests.evaluation.ho_tro import tao_pdf
    trang = [f"1 {SECRET} Gioi thieu\nDay la doan van dau tien cua {SECRET} sach thu nghiem.", "1.1 Khai niem\nNoi dung muc mot co day du cau van."]
    pdf = tao_pdf(tmp_path / "s.pdf", trang)
    manifest = {"ma_sach": "thu-bi-mat", "tap": "thu", "so_trang": len(trang), "pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest()}
    (tmp_path / "m.json").write_text(json.dumps(manifest), encoding="utf-8")
    argv = ["a1-logistic", "--pdf", str(pdf), "--manifest", str(tmp_path / "m.json"), "--mo-hinh", str(MO_HINH / "a1-logistic"), "--commit", "c" * 40,
            "--ngay-chay", "2026-10-30", "--ra", str(tmp_path / "hd.json")]
    assert main(argv) == 0
    ra = capsys.readouterr()
    hd = _doc(tmp_path / "hd.json")
    assert kiem(hd) == [] and hd["dinh_danh"]["he"] == "a1_logistic" and hd["chi_phi"]["tong"]["usd"] == 0
    assert SECRET in json.dumps(hd, ensure_ascii=False)                        # tiêu đề bí mật có trong hợp đồng ra
    assert SECRET not in ra.out + ra.err and "tap_thu" in ra.out
    import danhgia.xuat.lenh_a1_logistic as lenh
    monkeypatch.setattr(lenh, "cong", SimpleNamespace(in_allowlist=lambda d, cho_phep: print(json.dumps(hd, ensure_ascii=False))))
    main(argv)
    assert SECRET in capsys.readouterr().out
