"""Gom đúng các tệp cần chép lên máy GPU cho phần C vào `tmp/dg20/chep-len-may/dg20/` và ghi SHA-256 (`SHA256.txt`).

Chỉ có: mã (`ce_hoc.py`, `ce_do_cpu.py`, `e6_cross_encoder.py`), `chia-4-phan.json`, `du-lieu/d01.jsonl` (phiếu D-01, 16 cuốn học). KHÔNG có tài liệu phát triển
(doc-1, xstk, doc-4), tập thử hay tập khoá. Kiểm lại trong tệp dữ liệu: mọi dòng `nguon == d01` và `nhom` thuộc 16 cuốn D-01.
  tmp/venv-ml/Scripts/python.exe scripts/dg20/ce_chuan_bi_chep.py
"""
import hashlib
import json
import shutil
from pathlib import Path

import chung


def main():
    dich = chung.ra() / "chep-len-may" / "dg20"
    (dich / "du-lieu").mkdir(parents=True, exist_ok=True)
    nguon_du_lieu = chung.goc() / "tmp/pass-phu-ml/e6/du-lieu/d01.jsonl"
    cuon = {f"d01-{i:02d}" for i in range(1, 17)}
    for dong in nguon_du_lieu.read_text(encoding="utf-8").splitlines():
        r = json.loads(dong)
        assert r["nguon"] == "d01" and r["nhom"] in cuon, "dòng không thuộc D-01"
    cac_tep = {
        dich / "ce_hoc.py": chung.WORKTREE / "scripts/dg20/ce_hoc.py",
        dich / "ce_do_cpu.py": chung.WORKTREE / "scripts/dg20/ce_do_cpu.py",
        dich / "chia-4-phan.json": chung.WORKTREE / "scripts/dg20/chia-4-phan.json",
        dich / "e6_cross_encoder.py": chung.WORKTREE / "scripts/pass-phu-ml/e6_cross_encoder.py",
        dich / "du-lieu" / "d01.jsonl": nguon_du_lieu,
    }
    dong = []
    for dich_tep, nguon in cac_tep.items():
        shutil.copyfile(nguon, dich_tep)
        dong.append(f"{hashlib.sha256(dich_tep.read_bytes()).hexdigest()}  {dich_tep.relative_to(dich)}")
    (dich / "SHA256.txt").write_text("\n".join(dong) + "\n", encoding="utf-8")
    print("\n".join(dong))


if __name__ == "__main__":
    main()
