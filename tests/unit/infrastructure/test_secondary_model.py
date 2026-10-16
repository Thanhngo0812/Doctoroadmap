import hashlib
import json

import lightgbm as lgb
import numpy as np
import pytest

from doc2roadmap.domain.secondary_features import FEATURE_NAMES
from doc2roadmap.infrastructure.secondary_model import LightGBMSecondaryScorer


def model_files(tmp_path):
    values = np.zeros((12, len(FEATURE_NAMES)))
    values[:, 0] = np.arange(12) - 6
    labels = values[:, 0] >= 0
    data = lgb.Dataset(values, label=labels, feature_name=list(FEATURE_NAMES))
    model = lgb.train({"objective": "binary", "verbosity": -1, "min_data_in_leaf": 1,
                       "min_data_in_bin": 1, "num_leaves": 2, "num_threads": 1, "seed": 1}, data, num_boost_round=2)
    model.save_model(str(tmp_path / "model.txt"))
    manifest = {"phien_ban": "test", "dac_trung": list(FEATURE_NAMES), "gia_tri_thieu": -1.0,
                "sha256_model": hashlib.sha256((tmp_path / "model.txt").read_bytes()).hexdigest(),
                "hieu_chinh": {"diem": [.2, .8], "xac_suat": [.1, .9]}}
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    return manifest


def test_scores_blank_as_minus_one_and_interpolates_clipping_both_ends(tmp_path):
    model_files(tmp_path)
    scorer = LightGBMSecondaryScorer(tmp_path)
    blank = dict.fromkeys(FEATURE_NAMES, "")
    minus_one = dict.fromkeys(FEATURE_NAMES, -1.0)
    assert scorer.score([blank]) == scorer.score([minus_one])
    assert scorer.score([minus_one]) != scorer.score([dict.fromkeys(FEATURE_NAMES, 0.0)])
    assert scorer.calibrate([0, .2, .5, .8, 1]) == pytest.approx([.1, .1, .5, .9, .9])
    with pytest.raises(ValueError, match="82 đặc trưng"):
        scorer.score([{}])


@pytest.mark.parametrize("failure", ["missing", "hash", "features", "model_features", "calibration"])
def test_broken_model_files_stop_with_clear_error(tmp_path, failure):
    manifest = model_files(tmp_path)
    if failure == "missing":
        (tmp_path / "model.txt").unlink()
    elif failure == "hash":
        manifest["sha256_model"] = "bad"
    elif failure == "features":
        manifest["dac_trung"].reverse()
    elif failure == "model_features":
        text = (tmp_path / "model.txt").read_text(encoding="utf-8").replace("src_same_section", "wrong_name")
        (tmp_path / "model.txt").write_text(text, encoding="utf-8", newline="\n")
        manifest["sha256_model"] = hashlib.sha256((tmp_path / "model.txt").read_bytes()).hexdigest()
    else:
        manifest["hieu_chinh"]["diem"].reverse()
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="thiếu|băm|đặc trưng|hiệu chỉnh"):
        LightGBMSecondaryScorer(tmp_path)
