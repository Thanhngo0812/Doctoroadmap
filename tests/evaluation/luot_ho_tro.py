"""Hỗ trợ test điều phối lượt (DG-08): pipeline giả, chốt chặn kho chung, vàng dựng tay.

`GiaPipeline` thay `chay_cli_that`: mỗi lệnh pipeline (ingest, label-roles, a3, a4, roadmap) chép phần artifact tương ứng từ fixture
`kho-phat-lai` vào kho của lượt (chỉ vào `DOC2ROADMAP_ARTIFACT_DIR` mà lệnh nhận), và đếm lời gọi mô hình giả của các bước có chi.
Không có mạng: các test dùng thêm fixture `chan_mang` ở test_luot.py.
"""
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

import dung_tay as dt

KHO_MAU = Path(__file__).resolve().parent / "fixtures" / "kho-phat-lai"
DOC = "xstk-ch3-1"


class NganGiua(RuntimeError):
    """Mô phỏng lượt bị ngắt giữa một bước (mất kết nối, hết hạn mức)."""


def chep_neu_thieu(nguon: Path, dich: Path):
    for p in sorted(nguon.rglob("*")):
        if p.is_file():
            d = dich / p.relative_to(nguon)
            if not d.exists():
                d.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(p, d)


class GiaPipeline:
    def __init__(self):
        self.goi_mo_hinh = Counter()   # bước có chi -> số lần được gọi (kể cả lần ném lỗi)
        self.lenh = []                  # (argv, env) của mọi lệnh đã nhận
        self.hong_o = None              # tên bước sẽ ném NganGiua một lần
        self.so_dong_pha_b = 1
        self.canonical_luc_roadmap = []  # mỗi lần roadmap: các algorithm_id canonical có trong kho lúc đó

    def __call__(self, argv, env):
        kho = Path(env["DOC2ROADMAP_ARTIFACT_DIR"])
        self.lenh.append((list(argv), dict(env)))
        buoc = argv[0]
        if buoc != "ingest":
            self.goi_mo_hinh[buoc] += 1
        if self.hong_o == buoc:
            self.hong_o = None
            raise NganGiua(buoc)
        if buoc == "ingest":
            chep_neu_thieu(KHO_MAU / "chunks", kho / "chunks")
        elif buoc == "a3":
            (kho / "candidates" / DOC / "v1").mkdir(parents=True, exist_ok=True)
            (kho / "candidates" / DOC / "v1" / "manifest.json").write_text(json.dumps({"stage": "candidates", "stats": {}}), encoding="utf-8")
        elif buoc == "a4":
            chep_neu_thieu(KHO_MAU / "canonical", kho / "canonical")
        elif buoc == "roadmap":
            thu = kho / "canonical" / DOC
            self.canonical_luc_roadmap.append(sorted(json.loads((p / "manifest.json").read_text(encoding="utf-8")).get("config", {}).get("algorithm_id", "")
                                                     for p in thu.iterdir() if (p / "manifest.json").exists()) if thu.exists() else [])
            chep_neu_thieu(KHO_MAU / "graph", kho / "graph")
            chep_neu_thieu(KHO_MAU / "canonical", kho / "canonical")
            chep_neu_thieu(KHO_MAU / "chunks", kho / "chunks")
            (kho / "phase_b").mkdir(exist_ok=True)
            hang = [{"purpose": "module_title", "doc_id": DOC, "elapsed_ms": 1500, "input_tokens": 400, "output_tokens": 20,
                     "cost_usd": 0.0001} for _ in range(self.so_dong_pha_b)]
            (kho / "phase_b" / "live.json").write_text(json.dumps({"usage": hang}), encoding="utf-8")
        return 0, "{}"

    def lenh_dau(self, ten):
        return [(a, e) for a, e in self.lenh if a[0] == ten]


# ---------- chốt chặn kho chung: mọi lần ghi vào thư mục canh là lỗi ----------
_CANH = {"duong": None}
_GHI = set("wax+")


def _vao_trong(duong, goc):
    try:
        return Path(duong).resolve().is_relative_to(goc)
    except (TypeError, ValueError, OSError):
        return False


def _hook(su_kien, args):
    goc = _CANH["duong"]
    if goc is None:
        return
    nghi_ghi = False
    if su_kien == "open" and len(args) > 1 and isinstance(args[1], str):
        nghi_ghi = bool(_GHI & set(args[1])) and _vao_trong(args[0], goc)
    elif su_kien in ("os.mkdir", "os.remove", "os.rmdir", "os.rename", "shutil.copyfile", "shutil.copytree", "os.replace"):
        nghi_ghi = any(_vao_trong(a, goc) for a in args[:2] if isinstance(a, (str, bytes, Path)))
    if nghi_ghi:
        raise AssertionError(f"ghi vào kho chung: {su_kien} {args[:2]}")


sys.addaudithook(_hook)


def canh_kho_chung(duong):
    _CANH["duong"] = None if duong is None else Path(duong).resolve()


# ---------- vàng dựng tay trên node của hợp đồng ----------
def vang_tay(node, ma_sach="S"):
    """G1..G4 căn `khop` vào node[0..3]; cạnh vàng G1>G2, G2>G3, G3>G4. Chương duy nhất `c1`."""
    g3 = dt.g3(ma_sach, [(f"G{i}", "c1") for i in range(1, 5)])
    g4 = dt.g4(ma_sach, [("G1", "G2"), ("G2", "G3"), ("G3", "G4")])
    can = dt.can(ma_sach, [(f"G{i + 1}", node[i], "khop") for i in range(4)])
    return g3, g4, can
