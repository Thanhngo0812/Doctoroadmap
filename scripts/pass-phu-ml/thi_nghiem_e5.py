"""E5 (vòng 2): bộ kiểm cạnh cứng học trên nhãn agentic D-01, chấm điểm bốn tài liệu tiếng Việt cũ để lắp cạnh và đo E4 trên vàng.

- **Học:** dòng của `tmp/pass-phu-ml/bang-d01/*.csv` (E0') với `loai = thuc` và `trong_cua_so = 1`. Nhãn dương là `can_de_hieu` của lượt A
  (`--nhan=a`, mặc định) hoặc nhãn A cũ (`--nhan=a-cu`, chỉ phiếu đã có). `--chi-cap`: chỉ dòng là cặp ứng viên của luồng (`src_*` khác 0),
  gần hơn với tập mà pass phụ thật sự chấm. `--bo-nhom=<chuỗi>`: bỏ phiếu mà người gán chứa chuỗi này (cần `--nhan-goc`).
  `--ti-le-phieu=0.25`: chỉ học trên phần đầu tệp phiếu (phiếu đã xáo, nên là mẫu ngẫu nhiên), cho đường học theo cỡ dữ liệu.
- **Đặc trưng:** đúng bộ của vòng 1 (`thi_nghiem_e2b.py --tach-tu --khong-main`), giao với cột của bảng D-01.
- **Chấm:** dòng ứng viên của `tmp/pass-phu-ml/bang/<doc>.csv` (hợp đồng cho phép, tên X trong cửa sổ theo ranh giới từ); dòng khác điểm 0.
- **Ngưỡng**, chốt trên D-01 trước khi nhìn vàng, cùng ba chính sách như E2b: F1 lớn nhất trên dự đoán ngoài mẫu (chia theo sách); giữ tỉ lệ
  dương của D-01; hiệu chỉnh isotonic trên dự đoán ngoài mẫu rồi giữ số ứng viên bằng tổng xác suất trên tài liệu đo.
- **In thêm:** AP ngoài mẫu theo từng sách D-01 (so với nhãn agentic), và AP trên bốn tài liệu cũ so với ý định cứng của LLM v3 (chỉ để tham
  khảo: cả hai đều là nhãn bạc).
Đầu ra `tmp/pass-phu-ml/diem/<lượt>/<doc>.csv` và `nguong.json`, đúng định dạng `lap_canh.py` đọc. Chạy bằng tmp/venv-ml:
  tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/thi_nghiem_e5.py [--nhan=a|a-cu] [--chi-cap] [--ti-le-phieu=1.0] [--luot=<tên>]
"""
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import average_precision_score

sys.argv += ["--tach-tu", "--khong-main"]  # bộ đặc trưng của vòng 1 dùng cho D-01
sys.path.insert(0, str(Path(__file__).resolve().parent))
import thi_nghiem_e2b as e2b  # noqa: E402

warnings.filterwarnings("ignore", category=UserWarning)
ROLES = ("noi_dung", "bai_tap", "loi_giai", "de_cuong", "mo_dau", "hanh_chinh", "cuoi_sach")
OLD_DOCS = ("doc-1", "nhap-mon-ml", "xstk-ch3-1", "doc-4")


def add_roles(frame):
    frame["vai_tro_neo_y"] = frame["vai_tro_neo_y"].fillna("")
    for role in ROLES:
        frame[f"neo_y_{role}"] = (frame.vai_tro_neo_y == role).astype(int)
    return frame


def load_d01(label, only_pairs, ticket_share, drop_group, original_labels):
    frame = pd.concat([pd.read_csv(p) for p in sorted(Path("tmp/pass-phu-ml/bang-d01").glob("*.csv"))], ignore_index=True)
    frame = add_roles(frame)
    frame = frame[(frame.loai == "thuc") & (frame.trong_cua_so == 1)]
    source_cols = [c for c in frame.columns if c.startswith("src_") and c != "src_so_chunk_contact"]
    frame = frame.assign(la_cap=(frame[source_cols].sum(axis=1) > 0).astype(int))
    column = {"a": "nhan_a", "a-cu": "nhan_a_cu"}[label]
    frame = frame[frame[column].notna() & (frame[column] != "")]
    frame["nhan"] = (frame[column] == "can_de_hieu").astype(int)
    if only_pairs:
        frame = frame[frame.la_cap == 1]
    if ticket_share < 1.0:
        order = [json.loads(line)["phieu_id"] for line in open("tmp/d01-phieu/phieu.jsonl", encoding="utf-8")]
        keep = set(order[:int(round(ticket_share * len(order)))])
        frame = frame[frame.phieu_id.isin(keep)]
    if drop_group:
        who = {}
        with open(original_labels, encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                who[row["phieu_id"]] = row["nguoi_gan"]
        frame = frame[~frame.phieu_id.map(lambda pid: drop_group in who.get(pid, ""))]
    return frame


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    label = options.get("nhan", "a")
    only_pairs = "--chi-cap" in sys.argv
    share = float(options.get("ti-le-phieu", "1.0"))
    drop_group = options.get("bo-nhom")
    run = options.get("luot", f"e5-d01-{label}" + ("-chi-cap" if only_pairs else "") + (f"-{share:g}" if share < 1 else "")
                      + (f"-bo-{drop_group}" if drop_group else ""))
    out = Path("tmp/pass-phu-ml/diem") / run
    out.mkdir(parents=True, exist_ok=True)

    old, old_features = e2b.load(OLD_DOCS, "y-dinh-cung")
    train = load_d01(label, only_pairs, share, drop_group, options.get("nhan-goc", "tmp/d01-gan-nhan/nhan-A-gop.jsonl"))
    features = [c for c in old_features if c in train.columns]
    train[features] = train[features].apply(pd.to_numeric, errors="coerce")
    missing = sorted(set(old_features) - set(features))
    print(f"lượt {run}: {len(train)} dòng học, {train.phieu_id.nunique()} phiếu, {train.doc.nunique()} sách, dương {train.nhan.mean():.3f}; "
          f"là cặp của luồng {train.la_cap.mean():.3f}; {len(features)} đặc trưng (thiếu so với vòng 1: {missing})")

    # Dự đoán ngoài mẫu, chia theo sách (leave-one-book-out).
    oof = np.zeros(len(train))
    per_book = {}
    for book in sorted(train.doc.unique()):
        mask = (train.doc == book).to_numpy()
        _, oof[mask] = e2b.fit_predict("lightgbm", train[~mask], train[mask], features)
        if train.nhan[mask].any():
            per_book[book] = round(float(average_precision_score(train.nhan[mask], oof[mask])), 3)
    threshold, train_f1 = e2b.best_f1_threshold(train.nhan.to_numpy(), oof)
    calibrator = IsotonicRegression(out_of_bounds="clip").fit(oof, train.nhan.to_numpy())
    rate = float(train.nhan.mean())
    model, _ = e2b.fit_predict("lightgbm", train, train.head(1), features)
    print(f"  AP ngoài mẫu theo sách (so với nhãn agentic): trung vị {np.median(list(per_book.values())):.3f}, "
          f"khoảng {min(per_book.values()):.3f}–{max(per_book.values()):.3f}; ngưỡng F1 {threshold:.3f} (F1 {train_f1:.3f})")

    report = {"luot": run, "nhan": label, "chi_cap": only_pairs, "ti_le_phieu": share, "bo_nhom": drop_group,
              "dong_hoc": int(len(train)), "phieu_hoc": int(train.phieu_id.nunique()), "ti_le_duong_hoc": round(rate, 4),
              "dac_trung": features, "ap_ngoai_mau_theo_sach": per_book, "tai_lieu": {}}
    for doc in OLD_DOCS:
        data = old[old.doc == doc]
        scores = model.predict_proba(data[features].fillna(-1.0).to_numpy())[:, 1]
        rows = data[["pair_id", "x", "y"]].assign(score=np.where(data.ung_vien == 1, scores, 0.0))
        rows.to_csv(out / f"{doc}.csv", index=False)
        asked = data[(data.ung_vien == 1) & data.status.isin(e2b.ASKED)]
        asked_scores = np.sort(rows.loc[asked.index, "score"].to_numpy())[::-1]
        candidate_scores = np.sort(rows.loc[data[data.ung_vien == 1].index, "score"].to_numpy())[::-1]
        rate_threshold = float(asked_scores[max(0, int(round(rate * len(asked_scores))) - 1)]) if len(asked_scores) else 1.0
        expected = int(round(float(calibrator.predict(asked_scores).sum())))
        calibrated_threshold = float(asked_scores[max(0, expected - 1)]) if len(asked_scores) and expected else 1.0
        test_scores = rows.loc[asked.index, "score"].to_numpy()
        report["tai_lieu"][doc] = {
            "nguong": threshold, "nguong_ti_le": rate_threshold, "nguong_hieu_chinh": calibrated_threshold, "so_duong_uoc_luong": expected,
            "ung_vien": int((data.ung_vien == 1).sum()), "ung_vien_da_hoi": int(len(asked)),
            "giu_f1": int((candidate_scores >= threshold).sum()), "giu_hieu_chinh": int((candidate_scores >= calibrated_threshold).sum()),
            "AP_so_y_dinh_llm": round(float(average_precision_score(asked.nhan, test_scores)), 3) if asked.nhan.any() else None}
        row = report["tai_lieu"][doc]
        print(f"  {doc:12s} ứng viên {row['ung_vien']} | giữ: F1 {row['giu_f1']}, hiệu chỉnh {row['giu_hieu_chinh']} | "
              f"AP so với ý định cứng LLM v3 {row['AP_so_y_dinh_llm']}")
    gain = sorted(zip(features, model.booster_.feature_importance("gain")), key=lambda pair: -pair[1])
    total = sum(value for _, value in gain) or 1.0
    report["gain"] = [(name, round(value / total, 4)) for name, value in gain]
    print("  gain: " + ", ".join(f"{name} {value / total:.3f}" for name, value in gain[:12]))
    (out / "nguong.json").write_text(json.dumps(report, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
