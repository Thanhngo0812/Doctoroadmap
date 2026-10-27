"""Đường dẫn và nạp dữ liệu dùng chung của vé DG-20. Dữ liệu học nằm ở thư mục chung (chỉ đọc), đầu ra nằm ở `tmp/dg20/` của worktree.

Chỉ D-01 (16 cuốn học) được nạp. Không có đường nào tới tập khoá, tập thử hay tập phát triển.
"""
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

WORKTREE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(WORKTREE / "evaluation"))
SEED = 20261027
THREADS = 4
LEAVES = (7, 15, 31, 63, 127, 255)
MAX_ROUNDS = 5000
PATIENCE = 100


def goc():
    """Thư mục chung chứa dữ liệu học (`tmp/pass-phu-ml`, `tmp/doc-nhe-v414`...)."""
    if os.environ.get("DG20_GOC"):
        return Path(os.environ["DG20_GOC"])
    return WORKTREE.parents[1] if WORKTREE.parent.name == "tmp" else WORKTREE


def ra():
    out = WORKTREE / "tmp" / "dg20"
    out.mkdir(parents=True, exist_ok=True)
    return out


def m3_data():
    """Bảng học của M3, đúng như `thi_nghiem_e5.load_d01('a', ...)`: dòng thực trong cửa sổ có nhãn lượt A."""
    frame = pd.concat([pd.read_csv(p) for p in sorted((goc() / "tmp/pass-phu-ml/bang-d01").glob("*.csv"))], ignore_index=True)
    frame["vai_tro_neo_y"] = frame["vai_tro_neo_y"].fillna("")
    for role in ("noi_dung", "bai_tap", "loi_giai", "de_cuong", "mo_dau", "hanh_chinh", "cuoi_sach"):
        frame[f"neo_y_{role}"] = (frame.vai_tro_neo_y == role).astype(int)
    frame = frame[(frame.loai == "thuc") & (frame.trong_cua_so == 1)]
    frame = frame[frame["nhan_a"].notna() & (frame["nhan_a"] != "")].copy()
    frame["nhan"] = (frame["nhan_a"] == "can_de_hieu").astype(int)
    return frame


def _a1_modules():
    """Mã A1 nhẹ của thư mục chung (đã có dấu vân tay khớp với tập dữ liệu); chỉ đọc."""
    sys.path.append(str(goc() / ".venv/Lib/site-packages"))
    sys.path.insert(0, str(goc() / "src"))
    sys.path.insert(0, str(goc() / "scripts/thu-a1"))
    sys.path.insert(0, str(goc() / "scripts/doc-nhe"))
    import hoc_tieu_de as base
    import noi_tieu_de_r5 as pairs
    return base, pairs


def _a1_books(base):
    source = goc() / "tmp/doc-nhe-v414"
    pinned = base.manifest(source)
    return source, [b for b in pinned["books"] if b["split"] == "train"]


def m1_data():
    """M1 (nhận tiêu đề): {cuốn: (X, y)} chỉ 16 cuốn học, bỏ dòng nhãn -1, đúng như `hoc_tieu_de.training_arrays`."""
    base, _ = _a1_modules()
    source, books = _a1_books(base)
    result = {}
    for book in books:
        d = base.read(source / "datasets" / (book["id"] + ".json"))
        assert d["fingerprint"] == base.code_fingerprint(), "mã A1 đổi so với lúc dựng dữ liệu"
        x, y = base.feature_matrix(d["rows"], d["body"]), np.asarray(d["y"])
        result[book["id"]] = (x[y >= 0], y[y >= 0])
    return result, list(base.FEATURE_NAMES)


def m2_data():
    """M2 (nối dòng tiêu đề): như `hoc_noi_r5.run`, nhãn cặp từ `tmp/a1-v414-r3/labels`."""
    base, pairs = _a1_modules()
    source, books = _a1_books(base)
    result = {}
    for book in books:
        key = book["id"]
        d = base.read(source / "datasets" / (key + ".json"))
        labels = base.read(goc() / "tmp/a1-v414-r3/labels" / (key + ".json"))
        assert labels["dataset_sha256"] == base.digest(source / "datasets" / (key + ".json"))
        x, y = pairs.matrix(d["rows"]), pairs.pair_labels(d["rows"], labels["rows"])
        result[key] = (x[y >= 0], y[y >= 0])
    return result, list(pairs.FEATURES)
