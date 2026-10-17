"""Độ phủ thân mục bởi tên các mục khác, cho mọi mục bị luật 'lặp ở đầu >= 3 mục' bắt (trừ T-01, smoke). Chỉ đọc."""
import json, re, sys, unicodedata
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path("artifacts/chunks")
SKIP = {"d01-t01", "d01-t02", "smoke", "smoke-e2e"}
NUM = re.compile(r"^\s*(?:[\dIVXLCDMivxlcdm]+(?:\.\d+)*|[^\W\d_])[.)]\s+")


def norm(text):
    text = unicodedata.normalize("NFC", text).casefold()
    return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", text)).strip()


def coverage(body, titles):
    b = norm(body)
    if not b:
        return None
    mask = [False] * len(b)
    for t in titles:
        if len(t) < 3:
            continue
        for m in re.finditer(r"(?<!\w)" + re.escape(t) + r"(?!\w)", b):
            for i in range(m.start(), m.end()):
                mask[i] = True
    letters = [i for i, ch in enumerate(b) if ch.isalnum()]
    return sum(mask[i] for i in letters) / len(letters) if letters else None


def latest(doc):
    return sorted(ROOT.joinpath(doc).iterdir(), key=lambda p: int(p.name[1:]))[-1]


def main():
    rows = []
    for doc in sorted(p.name for p in ROOT.iterdir() if p.name not in SKIP):
        d = latest(doc)
        secs = json.loads((d / "sections.json").read_text(encoding="utf-8"))
        chunks = json.loads((d / "chunks.json").read_text(encoding="utf-8"))
        chunks = chunks["chunks"] if isinstance(chunks, dict) else chunks
        text = defaultdict(list)
        for c in chunks:
            text[c["parent_section_id"]].append(c["text"])
        ordered = sorted(secs, key=lambda s: (s["order_index"], s["level"]))
        first = {}
        for s in ordered:
            first.setdefault(s["parent_section_id"], s["section_id"])
        rep = Counter(s["title"] for s in ordered if s["section_id"] == first.get(s["parent_section_id"]))
        for t in [t for t, n in rep.items() if n >= 3]:
            members = [s for s in ordered if s["title"] == t]
            own = norm(NUM.sub("", t))
            others = {norm(NUM.sub("", s["title"])) for s in ordered if s["title"] != t and s["level"] > 0} - {own, ""}
            covs = [coverage(" ".join(text[s["section_id"]]), others) for s in members]
            vals = [c for c in covs if c is not None]
            rows.append((doc, t, len(members), round(sorted(vals)[len(vals) // 2], 2) if vals else None,
                         round(max(vals), 2) if vals else None, sum(c is None for c in covs)))
    for r in sorted(rows, key=lambda r: -(r[3] or -1)):
        print(f"{r[0]:12} {r[1][:40]!r:44} mục={r[2]:2} phủ-trung-vị={r[3]} phủ-max={r[4]} thân-rỗng={r[5]}")


if __name__ == "__main__":
    main()
