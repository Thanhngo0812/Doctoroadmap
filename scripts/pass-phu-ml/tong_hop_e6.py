"""E6 (vòng 2): tổng hợp các lượt cross-encoder sau khi chạy đủ seed. 0 USD, không gọi mô hình.

Đọc:
- `tmp/pass-phu-ml/diem/e6-<lượt>[-ghep-lightgbm]/nguong.json` của `thi_nghiem_e6.py`: epoch chọn, AP ngoài mẫu trên D-01;
- `tmp/pass-phu-ml/ket-qua/e6-tat-ca.jsonl`: E4 của `lap_canh.py`, nhãn `e6-<lượt>[-ghep-lightgbm]-hieu-chinh`;
- mốc, cùng bộ khớp đã sửa: E5 sáu seed (`e9-sua-y.jsonl` và `sua-y.jsonl`), LLM v3 (`r17-script.jsonl`, bản bật R17);
- `tmp/pass-phu-ml/ket-qua/e6-cpu-*.jsonl`: phút/cuốn trên CPU của `e6_toc_do_cpu.py`.
In bảng markdown (trung bình ± độ lệch chuẩn [min–max] qua các seed) và ghi vào `tmp/pass-phu-ml/ket-qua/e6-tong-hop.md`. Chạy bằng tmp/venv-ml:
  tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/tong_hop_e6.py
"""
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

DOCS = ("doc-1", "xstk-ch3-1", "doc-4")
METRICS = ("canh_pass_phu", "Q7", "Q7b", "bao_dong_P", "bao_dong_R")
MODELS = ("phobert", "e5")
RESULTS = Path("tmp/pass-phu-ml/ket-qua")


def read_jsonl(path):
    path = Path(path)
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()] if path.exists() else []


def cell(values):
    if len(values) == 1:
        return f"{values[0]:.3f}" if isinstance(values[0], float) else str(values[0])
    mean, std = float(np.mean(values)), float(np.std(values))
    if all(isinstance(v, int) for v in values):
        return f"{mean:.0f} ± {std:.0f}"
    return f"{mean:.3f} ± {std:.3f} [{min(values):.2f}–{max(values):.2f}]"


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    out = ["## AP ngoài mẫu trên D-01 (nhãn agentic `can_de_hieu`)", "",
           "| lượt | epoch chọn | E6 | LightGBM cùng nếp | ghép |", "|---|---:|---:|---:|---:|"]
    for model in MODELS:
        for seed in (1, 2, 3):
            alone = Path(f"tmp/pass-phu-ml/diem/e6-{model}-s{seed}/nguong.json")
            if not alone.exists():
                continue
            row = json.loads(alone.read_text(encoding="utf-8"))
            joined = Path(f"tmp/pass-phu-ml/diem/e6-{model}-s{seed}-ghep-lightgbm/nguong.json")
            ghep = json.loads(joined.read_text(encoding="utf-8"))["ap_ngoai_mau_gop"].get("ghep", "") if joined.exists() else ""
            out.append(f"| {model}-s{seed} | {row['epoch']} | {row['ap_ngoai_mau_gop']['e6']} | {row['ap_ngoai_mau_gop']['lightgbm']} | {ghep} |")

    groups = defaultdict(list)
    for row in read_jsonl(RESULTS / "e6-tat-ca.jsonl"):
        name = row["phuong_an"]
        model = next(m for m in MODELS if f"-{m}-" in name)
        groups[(row["doc"], f"E6 {model}" + (" ghép LightGBM" if "ghep" in name else ""))].append(row)
    for row in read_jsonl(RESULTS / "e9-sua-y.jsonl") + read_jsonl(RESULTS / "sua-y.jsonl"):
        if row["phuong_an"].startswith("e5-a"):
            groups[(row["doc"], "E5 (LightGBM)")].append(row)
    for row in read_jsonl(RESULTS / "r17-script.jsonl"):
        if row["he"] == "llm-v3" and row["r17"] == "bat":
            groups[(row["doc"], "LLM v3")].append(row)
    systems = ["LLM v3", "E5 (LightGBM)"] + [f"E6 {m}{v}" for m in MODELS for v in ("", " ghép LightGBM")]
    out += ["", "## E4 trên vàng người (ngưỡng hiệu chỉnh, `--chi-cung --tach-tu`)", "",
            "| tài liệu | hệ | số seed | cạnh pass phụ | Q7 | Q7b | bao đóng P | bao đóng R |", "|---|---|---:|---|---|---|---|---|"]
    for doc in DOCS:
        for system in systems:
            rows = groups.get((doc, system), [])
            if rows:
                out.append(f"| {doc} | {system} | {len(rows)} | " + " | ".join(cell([r[m] for r in rows]) for m in METRICS) + " |")

    out += ["", "## Phút/cuốn trên CPU laptop (doc-4)", ""]
    for path in sorted(RESULTS.glob("e6-cpu-*.jsonl")):
        out += [f"- `{path.name}`: {json.dumps(row, ensure_ascii=False)}" for row in read_jsonl(path)]
    text = "\n".join(out) + "\n"
    (RESULTS / "e6-tong-hop.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
