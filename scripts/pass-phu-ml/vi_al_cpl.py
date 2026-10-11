"""Đo VI-AL-CPL: chiếu khái niệm AL-CPL sang Wikipedia tiếng Việt (như ITA-PREREQ làm cho tiếng Ý), rồi đếm cặp (A, B) có tên B trong đoạn
mở đầu trang tiếng Việt của A. Chỉ gửi tên khái niệm công khai tới GitHub, Wikidata và Wikipedia; không đụng văn bản giáo trình.

Có đệm trong thư mục ra: chạy lại thì dùng tiếp phần đã lấy. API hành động của Wikipedia trả 429 cho máy này (2026-10-10), nên dùng Wikidata
SPARQL cho liên kết liên ngôn ngữ và REST `page/summary` của vi.wikipedia cho đoạn mở đầu, gọi chậm.

Khớp tên theo ranh giới âm tiết (hai đầu không dính chữ cái), bỏ phần ngoặc đơn cuối tiêu đề: xấp xỉ, chưa tách từ như vòng 1.

Chạy:  .venv/Scripts/python.exe -I scripts/pass-phu-ml/vi_al_cpl.py [--ra tmp/pass-phu-ml/vi-al-cpl]
"""
import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import networkx as nx

DOMAINS = ["data_mining", "geometry", "physics", "precalculus"]
RAW = "https://raw.githubusercontent.com/harrylclc/AL-CPL-dataset/master/data/"
UA = {"User-Agent": "doc2roadmap-research/0.1 (academic coverage check)"}


def fetch(url, data=None, accept=None, as_json=True):
    headers = dict(UA, **({"Accept": accept} if accept else {}))
    for attempt in range(8):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, data=data, headers=headers), timeout=60) as r:
                return json.load(r) if as_json else r.read().decode("utf-8")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            time.sleep(min(int(e.headers.get("Retry-After") or 0) or 10 * (attempt + 1), 120))
            error = e
        except OSError as e:
            time.sleep(5 * (attempt + 1))
            error = e
    raise error


def read_pairs(path):
    return [tuple(line.strip().split(",", 1)) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def en_url(title):
    return "<https://en.wikipedia.org/wiki/" + urllib.parse.quote(title, safe="(),'!*-._~:") + ">"


def name_pattern(title):
    name = re.sub(r"\s*\(.*?\)\s*$", "", title).strip().lower()
    return re.compile(r"(?<![^\W\d_])" + re.escape(name) + r"(?![^\W\d_])") if len(name) > 1 else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ra", default="tmp/pass-phu-ml/vi-al-cpl")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    out = Path(args.ra)
    out.mkdir(parents=True, exist_ok=True)
    for domain in DOMAINS:
        for ext in ("pairs", "preqs"):
            path = out / f"{domain}.{ext}"
            if not path.exists():
                path.write_text(fetch(RAW + path.name, as_json=False), encoding="utf-8")
    pairs = {d: read_pairs(out / f"{d}.pairs") for d in DOMAINS}
    positives = {d: set(read_pairs(out / f"{d}.preqs")) for d in DOMAINS}
    concepts = sorted({c for d in DOMAINS for p in pairs[d] for c in p})

    cache_path = out / "dem.json"
    cache = json.loads(cache_path.read_text(encoding="utf-8")) if cache_path.exists() else {"vi": None, "lead": {}}
    if cache["vi"] is None:
        vi = {}
        for i in range(0, len(concepts), 200):
            query = ("SELECT ?en ?vi WHERE { VALUES ?en { " + " ".join(en_url(t) for t in concepts[i:i + 200]) + " } "
                     "?en schema:about ?item . ?vi schema:about ?item ; schema:isPartOf <https://vi.wikipedia.org/> . }")
            result = fetch("https://query.wikidata.org/sparql", data=urllib.parse.urlencode({"query": query}).encode(),
                           accept="application/sparql-results+json")
            for row in result["results"]["bindings"]:
                en = urllib.parse.unquote(row["en"]["value"].rsplit("/wiki/", 1)[1])
                vi[en] = urllib.parse.unquote(row["vi"]["value"].rsplit("/wiki/", 1)[1]).replace("_", " ")
            time.sleep(2)
        cache["vi"] = vi
        cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
    vi, lead = cache["vi"], cache["lead"]
    todo = [t for t in sorted({vi[c] for c in concepts if vi.get(c)}) if t not in lead]
    for n, title in enumerate(todo, 1):
        summary = fetch("https://vi.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(title.replace(" ", "_"), safe=""))
        lead[title] = (summary or {}).get("extract") or ""
        if n % 20 == 0 or n == len(todo):
            cache_path.write_text(json.dumps(cache, ensure_ascii=False), encoding="utf-8")
            print("đã lấy đoạn mở đầu", n, "/", len(todo), flush=True)
        time.sleep(1.5)

    print("khái niệm khác nhau:", len(concepts), "| có trang tiếng Việt:", sum(1 for c in concepts if vi.get(c)),
          "| có đoạn mở đầu:", sum(1 for c in concepts if lead.get(vi.get(c) or "")))
    total = {}
    for d in DOMAINS:
        graph = nx.DiGraph((b, a) for a, b in positives[d])   # b là tiên quyết của a
        direct = {(a, b) for b, a in nx.transitive_reduction(graph).edges()}
        with_lead = [p for p in pairs[d] if vi.get(p[0]) and vi.get(p[1]) and lead.get(vi[p[0]])]
        window = [(a, b) for a, b in with_lead
                  if (pattern := name_pattern(vi[b])) and pattern.search(lead[vi[a]].lower())]
        row = {"cap": len(pairs[d]), "duong": len(positives[d]), "duong_truc_tiep": len(direct), "cap_A_co_mo_dau": len(with_lead),
               "cua_so": len(window), "cua_so_duong_truc_tiep": sum(p in direct for p in window),
               "cua_so_chi_bac_cau": sum(p in positives[d] and p not in direct for p in window),
               "cua_so_am": sum(p not in positives[d] for p in window)}
        print(d, row)
        for key, value in row.items():
            total[key] = total.get(key, 0) + value
    print("TỔNG", total)
    lengths = sorted(len(text) for text in lead.values() if text)
    if lengths:
        print("đoạn mở đầu: độ dài trung vị", lengths[len(lengths) // 2], "ký tự")


if __name__ == "__main__":
    main()
