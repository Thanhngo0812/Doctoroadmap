"""E1–E2 (R-02 mục 7.7, đổi mục tiêu sang **thay** pass phụ): luật đơn và mô hình học từ phán quyết LLM v3, đo theo từng tài liệu để riêng.

Đầu vào: bảng E0 (`dung_bang_cap.py`). Đơn vị: dòng có hướng X→Y của cặp v3 **đã hỏi** (created, rejected, deferred). Cặp bị tỉa không có nhãn.
- E1: mỗi luật đơn là một bộ phân loại "tạo cạnh X→Y"; báo P/R/F1 so với cạnh v3 theo từng tài liệu.
- E2: hồi quy logistic và LightGBM, chia leave-one-document-out (cặp của tài liệu đo không bao giờ nằm trong tập học). Ở mức cặp: lấy chiều
  có điểm cao hơn, tạo cạnh khi điểm ≥ ngưỡng; ngưỡng chọn trên dự đoán ngoài mẫu của **các tài liệu học** (F1 lớn nhất), không nhìn tài
  liệu đo. Báo kèm ngưỡng tốt nhất trên chính tài liệu đo (trần, chỉ để tham khảo), AP (PR-AUC) mức dòng.
- So với vàng người (nếu có): trên các cặp được hỏi mà cạnh vàng rơi vào, đếm cạnh vàng v3 tạo được và mô hình tạo được.
Môi trường: `tmp/venv-ml` (scikit-learn, lightgbm), không cần mã dự án. Chạy từ gốc repo:
  tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/thi_nghiem_e1_e2.py [--tai-lieu=doc-1,nhap-mon-ml,...] [--hoan=am|bo] [--ra=tmp/pass-phu-ml/ket-qua]
`--hoan=am`: cặp hoãn là âm khi học (mặc định, vì v3 không tạo cạnh); `--hoan=bo`: bỏ cặp hoãn khỏi tập học, vẫn tính là âm khi đo.
"""
import json
import sys
import warnings
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore", category=UserWarning)
NOT_FEATURES = {"hop_dong_cho_phep", "doc", "ngon_ngu", "pair_id", "thu_tu_cap", "x", "y", "ten_x", "ten_y", "status", "reason", "y_label", "kind",
                "evidence_kind", "llm_quote_co_ten_x", "dec_trai", "dec_phai", "loai_trai", "loai_phai", "vang_xy", "vang_yx", "vang_pham_vi"}
ASKED = ("created", "rejected", "deferred")
RULES = {  # luật đơn: tạo X→Y khi biểu thức đúng
    "ten_X_trong_cua_so_Y": lambda d: d.x_trong_ywin > 0,
    "ten_X_trong_cau_neo_Y": lambda d: d.x_trong_neo_y > 0,
    "trich_dan_cung_X_toi_Y": lambda d: d.cit_hard_xy > 0,
    "trich_dan_X_toi_Y_va_X_truoc": lambda d: (d.cit_hard_xy + d.cit_soft_xy > 0) & (d.x_truoc_y > 0),
    "refd_duong": lambda d: d.refd > 0,
    "X_truoc_Y_cung_muc": lambda d: (d.x_truoc_y > 0) & (d.cung_muc > 0),
    "ten_X_nam_trong_ten_Y": lambda d: d.ten_x_trong_ten_y > 0,
    "cua_so_hoac_ten_long": lambda d: (d.x_trong_ywin > 0) | (d.ten_x_trong_ten_y > 0),
}


def load(docs):
    frames = []
    for doc in docs:
        frame = pd.read_csv(f"tmp/pass-phu-ml/bang/{doc}.csv", keep_default_na=True)
        frames.append(frame[frame.status.isin(ASKED)])
    data = pd.concat(frames, ignore_index=True)
    data["vai_tro_neo_y"] = data["vai_tro_neo_y"].fillna("")
    for role in sorted(data.vai_tro_neo_y.unique()):
        data[f"neo_y_{role or 'khong'}"] = (data.vai_tro_neo_y == role).astype(int)
    features = [c for c in data.columns if c not in NOT_FEATURES and c != "vai_tro_neo_y"]
    data[features] = data[features].apply(pd.to_numeric, errors="coerce")
    return data, features


def prf(tp, predicted, actual):
    p = tp / predicted if predicted else 0.0
    r = tp / actual if actual else 0.0
    return {"P": round(p, 3), "R": round(r, 3), "F1": round(2 * p * r / (p + r), 3) if p + r else 0.0, "du_doan": int(predicted),
            "that": int(actual), "dung": int(tp)}


def pair_decisions(frame, scores, threshold):
    """Mỗi cặp: chiều có điểm cao hơn; tạo cạnh khi điểm ≥ ngưỡng. Trả tập (pair_id, x, y) được tạo."""
    work = frame[["pair_id", "x", "y"]].assign(score=scores)
    best = work.sort_values(["pair_id", "score"], ascending=[True, False]).drop_duplicates("pair_id")
    best = best[best.score >= threshold]
    return set(zip(best.pair_id, best.x, best.y))


def pair_scores(frame, decided):
    truth = set(zip(*[frame.loc[frame.y_label == 1, c] for c in ("pair_id", "x", "y")]))
    return prf(len(decided & truth), len(decided), len(truth))


def best_threshold(frame, scores):
    grid = np.unique(np.quantile(scores, np.linspace(0.5, 0.999, 200)))
    rows = [(pair_scores(frame, pair_decisions(frame, scores, t))["F1"], t) for t in grid]
    return max(rows)[1]


def models(seed=20261005):
    return {
        "logistic": lambda: make_pipeline(StandardScaler(), LogisticRegression(max_iter=4000, class_weight="balanced", C=0.5)),
        "lightgbm": lambda: lgb.LGBMClassifier(n_estimators=400, learning_rate=0.03, num_leaves=31, min_child_samples=20,
                                               subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_lambda=1.0,
                                               is_unbalance=True, random_state=seed, verbose=-1),
    }


def fit_predict(make, train, test, features):
    model = make()
    x_train = train[features].fillna(-1.0).to_numpy()
    model.fit(x_train, train.y_label.to_numpy())
    return model, model.predict_proba(test[features].fillna(-1.0).to_numpy())[:, 1]


def gold_rows(frame, decided):
    """Trên cặp đã hỏi có cạnh vàng (theo một chiều): v3 tạo đúng chiều bao nhiêu, mô hình tạo đúng chiều bao nhiêu."""
    gold = frame[frame.vang_xy == 1]
    if gold.empty:
        return None
    v3 = int(gold.y_label.sum())
    model = sum((row.pair_id, row.x, row.y) in decided for row in gold.itertuples())
    return {"canh_vang_trong_cap_hoi": int(len(gold)), "v3_tao_dung": v3, "mo_hinh_tao_dung": int(model)}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    docs = options.get("tai-lieu", "doc-1,nhap-mon-ml,xstk-ch3-1,doc-2,doc-3").split(",")
    deferred = options.get("hoan", "am")
    out = Path(options.get("ra", "tmp/pass-phu-ml/ket-qua"))
    out.mkdir(parents=True, exist_ok=True)
    data, features = load(docs)
    report = {"tai_lieu": docs, "hoan": deferred, "so_dac_trung": len(features), "dac_trung": features, "E1": {}, "E2": {}}

    print("E1 — luật đơn (mức dòng có hướng, so với cạnh v3)")
    for name, rule in RULES.items():
        report["E1"][name] = {}
        line = []
        for doc in docs:
            frame = data[data.doc == doc]
            hit = rule(frame)
            score = prf(int((hit & (frame.y_label == 1)).sum()), int(hit.sum()), int(frame.y_label.sum()))
            report["E1"][name][doc] = score
            line.append(f"{doc}: P {score['P']:.2f} R {score['R']:.2f}")
        print(f"  {name:30s} " + " | ".join(line))

    print("\nE2 — leave-one-document-out, mức cặp (chiều phải khớp), so với cạnh v3")
    for model_name, make in models().items():
        report["E2"][model_name] = {}
        for doc in docs:
            test = data[data.doc == doc]
            train = data[data.doc != doc]
            if deferred == "bo":
                train = train[train.status != "deferred"]
            # Ngưỡng: dự đoán ngoài mẫu trên tài liệu học (mỗi tài liệu học được chấm bởi mô hình học trên các tài liệu học còn lại).
            oof_scores = np.zeros(len(train))
            for inner in train.doc.unique():
                inner_train, inner_test = train[train.doc != inner], train[train.doc == inner]
                if inner_train.y_label.nunique() < 2:
                    continue
                _, oof_scores[(train.doc == inner).to_numpy()] = fit_predict(make, inner_train, inner_test, features)
            threshold = best_threshold(train, oof_scores)
            model, scores = fit_predict(make, train, test, features)
            decided = pair_decisions(test, scores, threshold)
            oracle = best_threshold(test, scores)
            row = {"AP_dong": round(float(average_precision_score(test.y_label, scores)), 3),
                   "nguong": round(float(threshold), 4), "cap": pair_scores(test, decided),
                   "nguong_tran": round(float(oracle), 4), "cap_tran": pair_scores(test, pair_decisions(test, scores, oracle)),
                   "vang": gold_rows(test, decided)}
            report["E2"][model_name][doc] = row
            print(f"  {model_name:9s} {doc:12s} AP {row['AP_dong']:.3f} | ngưỡng ngoài mẫu: P {row['cap']['P']:.3f} R {row['cap']['R']:.3f} "
                  f"F1 {row['cap']['F1']:.3f} ({row['cap']['du_doan']} cạnh / {row['cap']['that']} v3) | trần F1 {row['cap_tran']['F1']:.3f}"
                  + (f" | vàng: v3 {row['vang']['v3_tao_dung']}/{row['vang']['canh_vang_trong_cap_hoi']}, "
                     f"mô hình {row['vang']['mo_hinh_tao_dung']}" if row["vang"] else ""))
        if model_name == "lightgbm":
            model, _ = fit_predict(make, data, data.head(1), features)
            gain = sorted(zip(features, model.booster_.feature_importance("gain")), key=lambda p: -p[1])
            total = sum(value for _, value in gain) or 1.0
            report["E2"]["lightgbm_gain_toan_bo"] = [(name, round(value / total, 4)) for name, value in gain]
            print("  độ quan trọng (gain, học trên mọi tài liệu): " + ", ".join(f"{n} {v / total:.3f}" for n, v in gain[:15]))
    path = out / f"e1-e2-{'-'.join(docs)}-hoan-{deferred}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"\nghi {path}")


if __name__ == "__main__":
    main()
