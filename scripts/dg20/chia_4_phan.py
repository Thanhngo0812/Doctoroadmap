"""Ghi `scripts/dg20/chia-4-phan.json`: 16 cuốn D-01 chia 4 phần × 4 cuốn, tất định theo seed 20261027. LightGBM, logistic và cross-encoder dùng đúng tệp này."""
import json
from pathlib import Path

import chung
from danhgia.hoc_lai.chia import chia_k_phan

CUON = [f"d01-{i:02d}" for i in range(1, 17)]


def main():
    phan = chia_k_phan(CUON, 4, seed=chung.SEED)
    duong = Path(__file__).with_name("chia-4-phan.json")
    duong.write_text(json.dumps({"seed": chung.SEED, "phan": phan}, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(phan)


if __name__ == "__main__":
    main()
