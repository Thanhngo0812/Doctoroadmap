"""T-01b: chi của các artifact mới sau một bước (chỉ in số). Dùng: chi_buoc.py <graph|canonical|chunks> <doc> <version_truoc>.
Đồ thị: cộng token LLM trong stats (bỏ token embedding), giá flash-lite 0,25/1,50 USD mỗi triệu token. Canonical: cost_summary.usd."""
import json, sys
from pathlib import Path

kind, doc, before = sys.argv[1], sys.argv[2], int(sys.argv[3])
usd = 0.0
for d in Path("artifacts", kind, doc).iterdir():
    if int(d.name[1:]) <= before:
        continue
    m = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
    if kind == "canonical":
        usd += float((m.get("cost_summary") or {}).get("usd") or 0)
    elif kind == "chunks":
        r = m.get("role_metrics") or {}
        usd += int(r.get("region_roles_input_tokens") or 0) * 0.25e-6 + int(r.get("region_roles_output_tokens") or 0) * 1.5e-6
    else:
        s = m.get("stats") or {}
        llm_in = int(s.get("input_tokens") or 0) - int(s.get("embedding_input_tokens") or 0)
        usd += llm_in * 0.25e-6 + int(s.get("output_tokens") or 0) * 1.5e-6
print(f"{usd:.4f}")
