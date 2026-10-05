"""E2b: bộ kiểm cạnh cứng cho pass phụ không LLM — học từ phán quyết LLM v3, đo theo từng tài liệu để riêng, xuất điểm cho bộ lắp cạnh (E4).

Vì sao chỉ xét "ứng viên cửa sổ": phép chấm trên vàng (Q7, cạnh trực tiếp, bao đóng) chỉ tính cạnh cứng, và hợp đồng vé 12 đòi cạnh cứng có câu
trích nguyên văn trong cửa sổ định nghĩa của đích. Bộ lắp cạnh không LLM chỉ dựng được câu trích như vậy khi tên X có trong cửa sổ của Y. Vì thế
ứng viên = dòng có hướng X→Y mà hợp đồng cho phép (đích được dạy hoặc chưa rõ, hai đầu học được) và tên X có trong cửa sổ định nghĩa của Y.

Nhãn (chọn bằng `--nhan`):
- `v3`: v3 tạo cạnh X→Y (`y_label`);
- `y-dinh`: ý định của LLM — ít nhất một thứ tự trả `create` đúng chiều X→Y (kể cả phản hồi bị loại vì trượt kiểm định dạng) và không thứ tự
  nào trả chiều ngược. Nhãn này tách phán đoán ngữ nghĩa của LLM khỏi lỗi định dạng và luật hợp đồng.
- `y-dinh-cung`: như `y-dinh` nhưng mọi `create` X→Y đều là `can_de_hieu` (cạnh cứng). Phép chấm trên vàng chỉ tính cạnh cứng.
Chia: leave-one-document-out trên tài liệu tiếng Việt; tài liệu tiếng Anh chỉ thêm vào tập học khi có `--them-anh`. Ngưỡng chọn trên dự đoán
ngoài mẫu của chính các tài liệu học (F1 mức dòng lớn nhất), không nhìn tài liệu đo. Chính sách thứ hai (`nguong_ti_le`): giữ tỉ lệ ứng
viên bằng tỉ lệ dương gộp của nhãn trên tài liệu học. Chính sách thứ ba (`nguong_hieu_chinh`): hiệu chỉnh isotonic trên dự đoán ngoài mẫu
của tài liệu học, giữ số ứng viên bằng tổng xác suất đã hiệu chỉnh trên tài liệu đo. Cả ba chốt trước khi chấm vàng.
Đầu ra: `tmp/pass-phu-ml/diem/<lượt>/<doc>.csv` (pair_id, x, y, score; dòng ngoài ứng viên điểm 0) và `nguong.json`.
Chạy: tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/thi_nghiem_e2b.py [--nhan=v3|y-dinh|y-dinh-cung] [--mo-hinh=lightgbm|logistic] [--them-anh] [--ngu-nghia] [--tach-tu] [--khong-main] [--luot=<tên>]
"""
import json
import sys
import warnings
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore", category=UserWarning)
VIETNAMESE = ("doc-1", "nhap-mon-ml", "xstk-ch3-1", "doc-4")
ENGLISH = ("doc-2", "doc-3")
NOT_FEATURES = {"hop_dong_cho_phep", "doc", "ngon_ngu", "pair_id", "thu_tu_cap", "x", "y", "ten_x", "ten_y", "status", "reason", "y_label",
                "kind", "evidence_kind", "llm_quote_co_ten_x", "dec_trai", "dec_phai", "loai_trai", "loai_phai", "vang_xy", "vang_yx", "vang_pham_vi", "nhan",
                "ung_vien", "vai_tro_neo_y"}
ASKED = ("created", "rejected", "deferred")


def intent(row):
    decisions = [str(value).rstrip("!") for value in (row.dec_trai, row.dec_phai) if isinstance(value, str) and value]
    return int("create_xy" in decisions and "create_yx" not in decisions)


def hard_intent(row):
    """Ý định cạnh cứng: có thứ tự trả `create` X→Y, mọi `create` X→Y đều là `can_de_hieu`, không thứ tự nào trả chiều ngược.
    (Khi hai thứ tự khác loại, luật gộp v3 chọn `cong_cu`, nên trường hợp đó không tính là cứng.)"""
    rows = [(str(value).rstrip("!"), kind) for value, kind in ((row.dec_trai, row.loai_trai), (row.dec_phai, row.loai_phai))
            if isinstance(value, str) and value]
    kinds = [kind for value, kind in rows if value == "create_xy"]
    return int(bool(kinds) and all(kind == "can_de_hieu" for kind in kinds) and all(value != "create_yx" for value, _ in rows))


def load(docs, label, semantic=False):
    frames = []
    for doc in docs:
        frame = pd.read_csv(f"tmp/pass-phu-ml/bang/{doc}.csv")
        if semantic:  # đặc trưng embedding tại máy (`dac_trung_ngu_nghia.py`)
            extra = pd.read_csv(f"tmp/pass-phu-ml/bang/{doc}-ngu-nghia.csv")
            frame = frame.merge(extra, on=["pair_id", "x", "y"], how="left", validate="one_to_one")
        frames.append(frame)
    data = pd.concat(frames, ignore_index=True)
    data["vai_tro_neo_y"] = data["vai_tro_neo_y"].fillna("")
    for role in ("noi_dung", "bai_tap", "loi_giai", "de_cuong", "mo_dau", "hanh_chinh", "cuoi_sach"):
        data[f"neo_y_{role}"] = (data.vai_tro_neo_y == role).astype(int)
    window = "x_trong_ywin_tu" if WORDS else "x_trong_ywin"  # `--tach-tu`: ứng viên theo ranh giới từ tiếng Việt
    data["ung_vien"] = ((data.hop_dong_cho_phep == 1) & (data[window] > 0)).astype(int)
    data["nhan"] = (data.y_label if label == "v3" else data.apply(hard_intent, axis=1) if label == "y-dinh-cung"
                    else data.apply(intent, axis=1))
    features = [c for c in data.columns if c not in NOT_FEATURES]
    if NO_MAIN:  # `--khong-main`: bỏ đặc trưng lấy từ cạnh A8 pass chính (dữ liệu D-01 không chạy pass chính)
        features = [c for c in features if not c.startswith("main_")]
    data[features] = data[features].apply(pd.to_numeric, errors="coerce")
    return data, features


WORDS = "--tach-tu" in sys.argv
NO_MAIN = "--khong-main" in sys.argv


def make_model(name, seed=20261005):
    if name == "logistic":
        return make_pipeline(StandardScaler(), LogisticRegression(max_iter=4000, class_weight="balanced", C=0.5))
    return lgb.LGBMClassifier(n_estimators=300, learning_rate=0.03, num_leaves=15, min_child_samples=20, subsample=0.8, subsample_freq=1,
                              colsample_bytree=0.8, reg_lambda=1.0, is_unbalance=True, random_state=seed, verbose=-1, n_jobs=4)


def fit_predict(name, train, test, features):
    model = make_model(name)
    model.fit(train[features].fillna(-1.0).to_numpy(), train.nhan.to_numpy())
    return model, model.predict_proba(test[features].fillna(-1.0).to_numpy())[:, 1]


def best_f1_threshold(labels, scores):
    order = np.argsort(-scores)
    labels, scores = np.asarray(labels)[order], np.asarray(scores)[order]
    tp = np.cumsum(labels)
    precision = tp / np.arange(1, len(labels) + 1)
    recall = tp / max(labels.sum(), 1)
    f1 = np.where(precision + recall > 0, 2 * precision * recall / np.maximum(precision + recall, 1e-12), 0)
    index = int(np.argmax(f1))
    return float(scores[index]), float(f1[index])


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    label, model_name = options.get("nhan", "y-dinh"), options.get("mo-hinh", "lightgbm")
    extra = ENGLISH if "--them-anh" in sys.argv else ()
    semantic = "--ngu-nghia" in sys.argv
    run = options.get("luot", f"{model_name}-{label}" + ("-anh" if extra else "") + ("-ngu-nghia" if semantic else "")
                      + ("-tach-tu" if WORDS else "") + ("-khong-main" if NO_MAIN else ""))
    out = Path("tmp/pass-phu-ml/diem") / run
    out.mkdir(parents=True, exist_ok=True)
    data, features = load(VIETNAMESE + extra, label, semantic)
    candidates = data[(data.ung_vien == 1) & data.status.isin(ASKED)]
    report = {"luot": run, "nhan": label, "mo_hinh": model_name, "tai_lieu_hoc_them": list(extra), "dac_trung": features, "tai_lieu": {}}
    print(f"lượt {run}: {len(features)} đặc trưng; ứng viên đã hỏi theo tài liệu:",
          candidates.groupby("doc").agg(n=("nhan", "size"), duong=("nhan", "sum")).to_dict("index"))
    for doc in VIETNAMESE:
        train = candidates[candidates.doc != doc]
        oof = np.zeros(len(train))
        for inner in train.doc.unique():
            mask = (train.doc == inner).to_numpy()
            _, oof[mask] = fit_predict(model_name, train[~mask], train[mask], features)
        threshold, train_f1 = best_f1_threshold(train.nhan.to_numpy(), oof)
        _, scores = fit_predict(model_name, train, data[data.doc == doc], features)
        rows = data[data.doc == doc][["pair_id", "x", "y"]].assign(score=np.where(data[data.doc == doc].ung_vien == 1, scores, 0.0))
        # Chính sách thứ hai, chốt trước khi nhìn vàng: giữ tỉ lệ ứng viên (đã hỏi) bằng tỉ lệ dương gộp của nhãn trên tài liệu học.
        rate = float(train.nhan.mean())
        asked_scores = np.sort(rows.loc[candidates[candidates.doc == doc].index, "score"].to_numpy())[::-1]
        rate_threshold = float(asked_scores[max(0, int(round(rate * len(asked_scores))) - 1)]) if len(asked_scores) else 1.0
        # Chính sách thứ ba: hiệu chỉnh isotonic trên dự đoán ngoài mẫu của tài liệu học; số cạnh giữ = tổng xác suất đã hiệu chỉnh trên
        # ứng viên của tài liệu đo (ước lượng số dương của chính cuốn đó, không dùng nhãn của nó).
        calibrator = IsotonicRegression(out_of_bounds="clip").fit(oof, train.nhan.to_numpy())
        expected = int(round(float(calibrator.predict(asked_scores).sum())))
        calibrated_threshold = float(asked_scores[max(0, expected - 1)]) if len(asked_scores) and expected else 1.0
        rows.to_csv(out / f"{doc}.csv", index=False)
        test = candidates[candidates.doc == doc]
        test_scores = rows.loc[test.index, "score"].to_numpy()
        hit = test_scores >= threshold
        tp = int((hit & (test.nhan == 1)).sum())
        report["tai_lieu"][doc] = {"nguong": threshold, "f1_hoc_ngoai_mau": round(train_f1, 3),
                                   "ti_le_duong_hoc": round(rate, 4), "nguong_ti_le": rate_threshold,
                                   "so_duong_uoc_luong": expected, "nguong_hieu_chinh": calibrated_threshold,
                                   "AP": round(float(average_precision_score(test.nhan, test_scores)), 3) if test.nhan.any() else None,
                                   "ung_vien": int(len(test)), "duong": int(test.nhan.sum()), "giu": int(hit.sum()), "giu_dung": tp,
                                   "P": round(tp / max(hit.sum(), 1), 3), "R": round(tp / max(test.nhan.sum(), 1), 3)}
        row = report["tai_lieu"][doc]
        print(f"  {doc:12s} ngưỡng {threshold:.3f} | AP {row['AP']} | giữ {row['giu']}/{row['ung_vien']} ứng viên, "
              f"P {row['P']} R {row['R']} so với nhãn {label}")
    model, _ = fit_predict(model_name, candidates, candidates.head(1), features)
    if model_name == "lightgbm":
        gain = sorted(zip(features, model.booster_.feature_importance("gain")), key=lambda pair: -pair[1])
        total = sum(value for _, value in gain) or 1.0
        report["gain"] = [(name, round(value / total, 4)) for name, value in gain]
        print("  gain: " + ", ".join(f"{name} {value / total:.3f}" for name, value in gain[:14]))
    (out / "nguong.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
