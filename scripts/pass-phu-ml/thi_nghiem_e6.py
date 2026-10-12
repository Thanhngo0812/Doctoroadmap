"""E6 (vòng 2): đọc dự đoán của cross-encoder (máy GPU, `e6_cross_encoder.py`), chốt ngưỡng như E5 và xuất điểm cho `lap_canh.py`. 0 USD.

- **Chọn epoch** bằng AP gộp ngoài mẫu trên D-01 (so với nhãn `can_de_hieu` của lượt A), không nhìn vàng. `--epoch=<n>` để ép.
- **So công bằng với LightGBM:** học lại LightGBM của E5 (cùng đặc trưng, cùng nhãn) trên **đúng bốn nhóm sách** của lượt E6, rồi so AP
  ngoài mẫu theo sách. Số E5 cũ (bỏ một sách) có lợi hơn vì học trên 15 sách thay vì 12.
- **Điểm trên tài liệu đo:** trung bình xác suất `can_de_hieu` của bốn mô hình nếp. Dòng ngoài ứng viên điểm 0, như E5.
- **Ngưỡng**, chốt trên D-01 trước khi nhìn vàng, ba chính sách như E5:
  - F1 lớn nhất trên dự đoán ngoài mẫu;
  - giữ tỉ lệ dương của D-01;
  - hiệu chỉnh isotonic: mỗi nếp một bộ hiệu chỉnh học trên dự đoán ngoài mẫu của chính nếp đó; xác suất đã hiệu chỉnh trên tài liệu đo là
    trung bình bốn nếp, số cạnh giữ bằng tổng xác suất trên ứng viên đã hỏi.
- `--ghep=lightgbm`: điểm ghép = trung bình xác suất đã hiệu chỉnh của cross-encoder và LightGBM (cùng bốn nhóm sách).
Ra `tmp/pass-phu-ml/diem/<lượt>/<doc>.csv` và `nguong.json`, như E5. Chạy bằng tmp/venv-ml:
  tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/thi_nghiem_e6.py --ket-qua=tmp/pass-phu-ml/e6/ket-qua/<lượt GPU> [--epoch=<n>]
      [--ghep=lightgbm] [--luot=<tên>]
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import average_precision_score

sys.argv += ["--tach-tu", "--khong-main"]  # bộ đặc trưng LightGBM của E5
sys.path.insert(0, str(Path(__file__).resolve().parent))
import thi_nghiem_e2b as e2b  # noqa: E402
import thi_nghiem_e5 as e5  # noqa: E402

warnings.filterwarnings("ignore", category=UserWarning)
DATA = Path("tmp/pass-phu-ml/e6/du-lieu")
DEV_DOCS = ("doc-1", "xstk-ch3-1", "doc-4")
HARD = 0  # chỉ số của `can_de_hieu` trong 5 nhãn


def read_jsonl(path):
    with open(path, encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def read_probs(path):
    return {row["id"]: row["p"][HARD] for row in read_jsonl(path)}


def best_epoch(results, folds, train, forced):
    """AP gộp ngoài mẫu theo từng epoch có đủ mọi nếp; chọn epoch AP cao nhất (hoặc epoch bị ép)."""
    scores = {}
    for epoch in range(1, 20):
        paths = [results / f"ngoai-mau-nep{k}-e{epoch}.jsonl" for k in folds]
        if not all(path.exists() for path in paths):
            break
        probs = {}
        for path in paths:
            probs.update(read_probs(path))
        if set(probs) != set(train.id):
            raise SystemExit(f"epoch {epoch}: dự đoán ngoài mẫu không phủ đúng các dòng học")
        scores[epoch] = (float(average_precision_score(train.nhan, train.id.map(probs))), probs)
    if not scores:
        raise SystemExit("chưa có epoch nào đủ mọi nếp")
    epoch = forced or max(scores, key=lambda e: scores[e][0])
    return epoch, scores


def calibrated(train, oof, fold_of, dev_scores):
    """Hiệu chỉnh isotonic theo nếp: bộ của nếp k học trên dự đoán ngoài mẫu của nếp k, áp lên điểm của mô hình nếp k trên tài liệu đo."""
    result = []
    for fold, scores in dev_scores.items():
        mask = (fold_of == fold).to_numpy()
        calibrator = IsotonicRegression(out_of_bounds="clip").fit(oof[mask], train.nhan.to_numpy()[mask])
        result.append(calibrator.predict(scores))
    return np.mean(result, axis=0)


def lightgbm_same_folds(train, fold_of, folds):
    """LightGBM của E5 học lại trên đúng bốn nhóm sách của E6: dự đoán ngoài mẫu trên D-01 và điểm của từng mô hình nếp trên tài liệu đo."""
    frame = e5.load_d01("a", False, 1.0, None, None)
    frame = frame.assign(id=frame.phieu_id + "|" + frame.x).set_index("id").loc[train.id].reset_index()
    old, old_features = e2b.load(e5.OLD_DOCS, "y-dinh-cung")
    features = [c for c in old_features if c in frame.columns]
    frame[features] = frame[features].apply(pd.to_numeric, errors="coerce")
    oof, dev = np.zeros(len(frame)), {doc: {} for doc in DEV_DOCS}
    for fold in folds:
        mask = (fold_of == fold).to_numpy()
        model, oof[mask] = e2b.fit_predict("lightgbm", frame[~mask], frame[mask], features)
        for doc in DEV_DOCS:
            data = old[old.doc == doc]
            dev[doc][fold] = pd.Series(model.predict_proba(data[features].fillna(-1.0).to_numpy())[:, 1],
                                       index=data.pair_id + "|" + data.x + "|" + data.y)
    return oof, dev


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    results = Path(options["ket-qua"])
    log = json.loads((results / "nhat-ky.json").read_text(encoding="utf-8"))
    assignment = log["chia"]
    folds = sorted(set(assignment.values()))
    combine = options.get("ghep")
    run = options.get("luot", "e6-" + results.name + (f"-ghep-{combine}" if combine else ""))
    out = Path("tmp/pass-phu-ml/diem") / run
    out.mkdir(parents=True, exist_ok=True)

    train = pd.DataFrame([{"id": r["id"], "nhom": r["nhom"], "nhan": int(r["nhan"] == "can_de_hieu")} for r in read_jsonl(DATA / "d01.jsonl")])
    fold_of = train.nhom.map(assignment)
    epoch, by_epoch = best_epoch(results, folds, train, int(options["epoch"]) if "epoch" in options else None)
    oof = train.id.map(by_epoch[epoch][1]).to_numpy()
    dev_rows = {doc: read_jsonl(DATA / f"{doc}.jsonl") for doc in DEV_DOCS}
    dev = {doc: {fold: np.array([p[r["id"]] for r in dev_rows[doc]])
                 for fold in folds for p in [read_probs(results / f"{doc}-nep{fold}-e{epoch}.jsonl")]} for doc in DEV_DOCS}

    lgb_oof, lgb_dev = lightgbm_same_folds(train, fold_of, folds)
    per_book = {}
    for book in sorted(train.nhom.unique()):
        mask = (train.nhom == book).to_numpy()
        if train.nhan[mask].any():
            per_book[book] = {"e6": round(float(average_precision_score(train.nhan[mask], oof[mask])), 3),
                              "lightgbm": round(float(average_precision_score(train.nhan[mask], lgb_oof[mask])), 3)}
    pooled = {"e6": round(float(average_precision_score(train.nhan, oof)), 4),
              "lightgbm": round(float(average_precision_score(train.nhan, lgb_oof)), 4)}

    if combine == "lightgbm":
        # Ghép bằng trung bình xác suất đã hiệu chỉnh theo nếp: hai mô hình cùng thang, rồi coi trung bình là điểm mới.
        def per_fold_calibrated(values):
            result = np.zeros(len(values))
            for fold in folds:
                mask = (fold_of == fold).to_numpy()
                result[mask] = IsotonicRegression(out_of_bounds="clip").fit(values[mask], train.nhan.to_numpy()[mask]).predict(values[mask])
            return result
        new_oof = (per_fold_calibrated(oof) + per_fold_calibrated(lgb_oof)) / 2
        for doc in DEV_DOCS:
            keys = [f"{r['pair_id']}|{r['x']}|{r['y']}" for r in dev_rows[doc]]
            for fold in folds:
                mask = (fold_of == fold).to_numpy()
                ce = IsotonicRegression(out_of_bounds="clip").fit(oof[mask], train.nhan.to_numpy()[mask]).predict(dev[doc][fold])
                lg = IsotonicRegression(out_of_bounds="clip").fit(lgb_oof[mask], train.nhan.to_numpy()[mask]).predict(
                    lgb_dev[doc][fold].loc[keys].to_numpy())
                dev[doc][fold] = (ce + lg) / 2
        oof = new_oof
        pooled["ghep"] = round(float(average_precision_score(train.nhan, oof)), 4)

    threshold, train_f1 = e2b.best_f1_threshold(train.nhan.to_numpy(), oof)
    rate = float(train.nhan.mean())
    report = {"luot": run, "ket_qua_gpu": str(results), "mo_hinh": log["tham_so"]["mo_hinh"], "seed": log["tham_so"]["seed"], "ghep": combine,
              "epoch": epoch, "ap_gop_theo_epoch": {e: round(v[0], 4) for e, v in by_epoch.items()}, "ap_ngoai_mau_gop": pooled,
              "ap_ngoai_mau_theo_sach": per_book, "nguong_f1": threshold, "f1_ngoai_mau": round(train_f1, 4), "ti_le_duong_hoc": round(rate, 4),
              "tai_lieu": {}}
    print(f"lượt {run}: epoch {epoch} (AP gộp theo epoch {report['ap_gop_theo_epoch']}); AP ngoài mẫu gộp {pooled}")
    for doc in DEV_DOCS:
        table = pd.read_csv(f"tmp/pass-phu-ml/bang/{doc}.csv")
        keys = [f"{r['pair_id']}|{r['x']}|{r['y']}" for r in dev_rows[doc]]
        mean_score = pd.Series(np.mean([dev[doc][fold] for fold in folds], axis=0), index=keys)
        table_keys = table.pair_id + "|" + table.x + "|" + table.y
        rows = table[["pair_id", "x", "y"]].assign(score=table_keys.map(mean_score).fillna(0.0).to_numpy())
        rows.to_csv(out / f"{doc}.csv", index=False)
        candidate = table_keys.isin(mean_score.index).to_numpy()
        asked_mask = candidate & table.status.isin(e2b.ASKED).to_numpy()
        asked_scores = np.sort(rows.score.to_numpy()[asked_mask])[::-1]
        rate_threshold = float(asked_scores[max(0, int(round(rate * len(asked_scores))) - 1)]) if len(asked_scores) else 1.0
        if combine:
            calibrated_dev = pd.Series(np.mean([dev[doc][fold] for fold in folds], axis=0), index=keys)  # đã ở thang xác suất
        else:
            calibrated_dev = pd.Series(calibrated(train, oof, fold_of, dev[doc]), index=keys)
        expected = int(round(float(calibrated_dev.loc[table_keys[asked_mask]].sum())))
        calibrated_threshold = float(asked_scores[max(0, expected - 1)]) if len(asked_scores) and expected else 1.0
        candidate_scores = rows.score.to_numpy()[candidate]
        report["tai_lieu"][doc] = {"nguong": threshold, "nguong_ti_le": rate_threshold, "nguong_hieu_chinh": calibrated_threshold,
                                   "so_duong_uoc_luong": expected, "ung_vien": int(candidate.sum()), "ung_vien_da_hoi": int(asked_mask.sum()),
                                   "giu_f1": int((candidate_scores >= threshold).sum()),
                                   "giu_hieu_chinh": int((candidate_scores >= calibrated_threshold).sum())}
        row = report["tai_lieu"][doc]
        print(f"  {doc:12s} ứng viên {row['ung_vien']} (đã hỏi {row['ung_vien_da_hoi']}) | giữ: F1 {row['giu_f1']}, hiệu chỉnh {row['giu_hieu_chinh']}")
    print("  AP ngoài mẫu theo sách (E6 | LightGBM cùng nếp): "
          + ", ".join(f"{book} {v['e6']}|{v['lightgbm']}" for book, v in per_book.items()))
    (out / "nguong.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
