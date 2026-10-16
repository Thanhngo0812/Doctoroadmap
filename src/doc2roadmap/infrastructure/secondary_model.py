"""Frozen E5 inference only: no pickle, training data, network, or LLM."""
import hashlib
import json
from pathlib import Path

import numpy as np

from doc2roadmap.domain.secondary_features import FEATURE_NAMES


class LightGBMSecondaryScorer:
    def __init__(self, model_dir=None):
        import lightgbm as lgb

        bundled = Path(__file__).with_name("secondary_models")
        directory = (Path(model_dir) if model_dir is not None else bundled if bundled.is_dir()
                     else Path(__file__).resolve().parents[3] / "vendor/a8-pass-phu-ml")
        try:
            manifest_bytes = (directory / "manifest.json").read_bytes()
            model_bytes = (directory / "model.txt").read_bytes()
        except OSError as error:
            raise ValueError(f"thiếu tệp mô hình pass phụ ML: {directory}") from error
        manifest = json.loads(manifest_bytes)
        model_hash = hashlib.sha256(model_bytes).hexdigest()
        if model_hash != manifest.get("sha256_model"):
            raise ValueError("băm mô hình pass phụ ML không khớp manifest")
        if manifest.get("dac_trung") != list(FEATURE_NAMES):
            raise ValueError("danh sách hoặc thứ tự đặc trưng pass phụ ML không khớp")
        model_text = model_bytes.decode("utf-8")
        header = next((line.removeprefix("feature_names=").split() for line in model_text.splitlines()
                       if line.startswith("feature_names=")), [])
        if header != list(FEATURE_NAMES):
            raise ValueError("thứ tự đặc trưng trong tệp LightGBM không khớp")
        self.model = lgb.Booster(model_str=model_text)
        if self.model.feature_name() != list(FEATURE_NAMES):
            raise ValueError("thứ tự đặc trưng trong tệp LightGBM không khớp")
        self.missing = float(manifest["gia_tri_thieu"])
        if self.missing != -1.0:
            raise ValueError("giá trị thiếu của mô hình pass phụ ML phải là -1")
        self.points = np.asarray(manifest["hieu_chinh"]["diem"], dtype=float)
        self.probabilities = np.asarray(manifest["hieu_chinh"]["xac_suat"], dtype=float)
        if (self.points.ndim != 1 or len(self.points) < 2 or self.probabilities.shape != self.points.shape
                or not np.isfinite(self.points).all() or not np.isfinite(self.probabilities).all()
                or not np.all(np.diff(self.points) > 0) or not np.all(np.diff(self.probabilities) >= 0)
                or np.any(self.probabilities < 0) or np.any(self.probabilities > 1)):
            raise ValueError("bộ hiệu chỉnh pass phụ ML không hợp lệ")
        self.metadata = {"version": manifest["phien_ban"], "model_sha256": model_hash,
                         "calibration_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
                         "feature_names": list(FEATURE_NAMES), "missing_value": self.missing}

    def score(self, rows):
        if not rows:
            return []
        if any(set(row) != set(FEATURE_NAMES) for row in rows):
            raise ValueError("dòng chấm không khớp 82 đặc trưng pass phụ ML")
        values = np.asarray([[self.missing if row[name] in ("", None) else float(row[name])
                              for name in FEATURE_NAMES] for row in rows], dtype=float)
        values[np.isnan(values)] = self.missing
        return self.model.predict(values, num_threads=4).tolist()

    def calibrate(self, scores):
        return np.interp(scores, self.points, self.probabilities).tolist()
