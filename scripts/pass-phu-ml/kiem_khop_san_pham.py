"""Compare only pre-secondary features on development books; print counts, never book text."""
import argparse
import csv
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from doc2roadmap.domain.secondary_features import FEATURE_NAMES  # noqa: E402


def read(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return {(row["pair_id"], row["x"], row["y"]): row for row in csv.DictReader(handle)}


def number(row, feature):
    if feature.startswith("neo_y_") and feature not in row:
        return float(row.get("vai_tro_neo_y", "") == feature.removeprefix("neo_y_"))
    value = row[feature]
    return -1.0 if value == "" else float(value)


def compare(reference, product):
    if set(reference) != set(product):
        return {"same_rows": False, "same_candidates": False, "max_error": None, "passed": False}
    expected = {key for key, row in reference.items()
                if float(row["hop_dong_cho_phep"]) == 1 and float(row["x_trong_ywin_tu"]) > 0}
    actual = {key for key, row in product.items() if int(row["ung_vien"]) == 1}
    errors = {name: max((abs(number(reference[key], name) - number(product[key], name))
                         for key in expected), default=0.0) for name in FEATURE_NAMES}
    maximum = max(errors.values(), default=0.0)
    return {"rows": len(reference), "candidates": len(actual), "same_rows": True,
            "same_candidates": expected == actual, "feature_count": len(FEATURE_NAMES),
            "max_error": maximum, "different_columns": [key for key, value in errors.items() if value > 1e-9],
            "passed": expected == actual and math.isfinite(maximum) and maximum <= 1e-9}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--reference", type=Path, default=Path("tmp/pass-phu-ml/bang"))
    parser.add_argument("--product", type=Path, default=Path("tmp/v4-18b-features"))
    args = parser.parse_args()
    failed = False
    for doc in ("doc-1", "nhap-mon-ml", "xstk-ch3-1", "doc-4"):
        result = compare(read(args.reference / f"{doc}.csv"), read(args.product / f"{doc}.csv"))
        print(json.dumps({"doc_id": doc, **result}, ensure_ascii=False), flush=True)
        failed |= not result["passed"]
    return int(failed)


if __name__ == "__main__":
    sys.exit(main())
