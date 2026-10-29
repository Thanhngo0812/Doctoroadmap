"""Bộ chấm pass phụ thay thế (vé DG-21), cài giao diện `SecondaryScorer` của sản phẩm. Thuộc seam xuất: nhập `doc2roadmap`, không gọi mạng.

- `LogisticSecondaryScorer`: nạp M3 logistic (`model.joblib` + `manifest.json` có SHA-256) và hiệu chỉnh isotonic của manifest. Ô thiếu là NaN
  (bộ điền trung vị của pipeline lo), không phải -1 như LightGBM.
- `DiemCoSanScorer`: đọc điểm của từng cặp từ tệp (cross-encoder chấm ở nơi có `torch`). Điểm gắn với cặp bằng thứ tự VÀ dấu vân tay đặc trưng
  (`dac_trung_sha`), nên tệp của đồ thị khác hay của lần xuất khác bị từ chối. Thiếu điểm là lỗi, không bao giờ coi là 0.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from doc2roadmap.domain.secondary_features import FEATURE_NAMES

SCHEMA_DIEM = "diem-co-san-1"


def dac_trung_sha(dong):
    """Dấu vân tay của một dòng đặc trưng (theo thứ tự `FEATURE_NAMES`); xuất cặp và nạp điểm cùng dùng hàm này."""
    return hashlib.sha256(json.dumps([dong[ten] for ten in FEATURE_NAMES], ensure_ascii=False).encode("utf-8")).hexdigest()


def _kiem_hieu_chinh(diem, xac_suat):
    diem, xac_suat = np.asarray(diem, dtype=float), np.asarray(xac_suat, dtype=float)
    if (diem.ndim != 1 or len(diem) < 2 or xac_suat.shape != diem.shape or not np.isfinite(diem).all() or not np.isfinite(xac_suat).all()
            or not np.all(np.diff(diem) > 0) or not np.all(np.diff(xac_suat) >= 0) or np.any(xac_suat < 0) or np.any(xac_suat > 1)):
        raise ValueError("bộ hiệu chỉnh pass phụ không hợp lệ")
    return diem, xac_suat


class LogisticSecondaryScorer:
    def __init__(self, thu_muc):
        import joblib

        thu_muc = Path(thu_muc)
        try:
            bytes_manifest = (thu_muc / "manifest.json").read_bytes()
            bytes_mo_hinh = (thu_muc / "model.joblib").read_bytes()
        except OSError as loi:
            raise ValueError(f"thiếu tệp mô hình logistic pass phụ: {thu_muc}") from loi
        manifest = json.loads(bytes_manifest)
        sha = hashlib.sha256(bytes_mo_hinh).hexdigest()
        if sha != manifest.get("sha256_model"):
            raise ValueError("băm mô hình logistic pass phụ không khớp manifest")
        if manifest.get("dac_trung") != list(FEATURE_NAMES):
            raise ValueError("danh sách hoặc thứ tự đặc trưng của mô hình logistic không khớp pass phụ")
        self.diem, self.xac_suat = _kiem_hieu_chinh(manifest["hieu_chinh"]["diem"], manifest["hieu_chinh"]["xac_suat"])
        import io
        self.mo_hinh = joblib.load(io.BytesIO(bytes_mo_hinh))   # chỉ sau khi băm khớp
        self.metadata = {"version": manifest["phien_ban"], "model_sha256": sha,
                         "calibration_sha256": hashlib.sha256(bytes_manifest).hexdigest(),
                         "feature_names": list(FEATURE_NAMES), "missing_value": "nan"}

    def score(self, rows):
        if not rows:
            return []
        if any(set(row) != set(FEATURE_NAMES) for row in rows):
            raise ValueError("dòng chấm không khớp 82 đặc trưng pass phụ ML")
        gia_tri = np.asarray([[np.nan if row[ten] in ("", None) else float(row[ten]) for ten in FEATURE_NAMES] for row in rows], dtype=float)
        return self.mo_hinh.predict_proba(gia_tri)[:, 1].tolist()

    def calibrate(self, scores):
        return np.interp(scores, self.diem, self.xac_suat).tolist()


class DiemCoSanScorer:
    """Tệp jsonl: dòng đầu `{"schema": "diem-co-san-1", "mo_hinh": ..., "sha256_mo_hinh": ..., "sha256_hieu_chinh": ...}`; mỗi dòng sau
    `{"id", "dac_trung_sha", "p", "xac_suat"}` theo đúng thứ tự `cap-ce` đã xuất."""

    def __init__(self, tep):
        tep = Path(tep)
        try:
            bytes_tep = tep.read_bytes()
        except OSError as loi:
            raise ValueError(f"không đọc được tệp điểm có sẵn: {tep}") from loi
        dong = [json.loads(d) for d in bytes_tep.decode("utf-8").splitlines() if d.strip()]
        if not dong or dong[0].get("schema") != SCHEMA_DIEM:
            raise ValueError(f"tệp điểm phải bắt đầu bằng dòng đầu schema {SCHEMA_DIEM}")
        dau, self.hang = dong[0], dong[1:]
        for so, h in enumerate(self.hang):
            for khoa in ("id", "dac_trung_sha", "p", "xac_suat"):
                if h.get(khoa) is None:
                    raise ValueError(f"dòng điểm {so}: thiếu {khoa}")
            if not (0 <= h["p"] <= 1 and 0 <= h["xac_suat"] <= 1):
                raise ValueError(f"dòng điểm {so}: điểm ngoài [0, 1]")
        self.xac_suat_theo_diem = {}
        for h in self.hang:
            if self.xac_suat_theo_diem.setdefault(h["p"], h["xac_suat"]) != h["xac_suat"]:
                raise ValueError("cùng một điểm mà hai xác suất hiệu chỉnh khác nhau: bộ hiệu chỉnh không đơn trị")
        self.metadata = {"version": f"diem-co-san:{dau.get('mo_hinh')}", "model_sha256": dau.get("sha256_mo_hinh"),
                         "calibration_sha256": dau.get("sha256_hieu_chinh"), "scores_sha256": hashlib.sha256(bytes_tep).hexdigest(),
                         "feature_names": list(FEATURE_NAMES), "missing_value": None}

    def score(self, rows):
        if len(rows) != len(self.hang):
            raise ValueError(f"tệp điểm có {len(self.hang)} cặp nhưng pass phụ cần chấm {len(rows)} dòng: thiếu hay thừa điểm")
        for so, (dong, h) in enumerate(zip(rows, self.hang)):
            if dac_trung_sha(dong) != h["dac_trung_sha"]:
                raise ValueError(f"dòng {so}: đặc trưng không khớp cặp {h['id']} của tệp điểm (tệp của đồ thị hay lần xuất khác)")
        return [h["p"] for h in self.hang]

    def calibrate(self, scores):
        try:
            return [self.xac_suat_theo_diem[s] for s in scores]
        except KeyError as loi:
            raise ValueError("có điểm không thuộc tệp điểm có sẵn") from loi
