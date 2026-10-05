"""D-01 bước 2: xuất phiếu gán nhãn cho agentic, đúng định dạng `task/v4/D-01-dac-ta-du-lieu-pass-phu.md`. 0 USD.

Đọc artifact danh tính (stage `identity`, sau A9'') mới nhất của mỗi cuốn, cùng bản chunk mà chuỗi đó dùng.
- **Phiếu:** mỗi khái niệm Y mà hợp đồng cho phép làm đích (trạng thái dạy `taught` hoặc `uncertain`, học được, có cửa sổ định nghĩa).
- **Ứng viên:**
  - mọi X học được, X ≠ Y, có tên (tên hoặc bí danh) trong cửa sổ của Y, khớp theo ranh giới từ tiếng Việt (`trong_cua_so: true`,
    `cau_co_ten` là các câu có tên);
  - tối đa 5 X **không** có tên trong cửa sổ, lấy từ cặp ứng viên của luồng (`trong_cua_so: false`). Ưu tiên theo nguồn: X được nhắc trong
    chunk định nghĩa của Y, đề xuất quan hệ của A3, cùng mục, tiếp xúc; hoà thì X dạy sớm hơn trước.
- **Kiểm chất lượng:**
  - phiếu kiểm (mặc định 5% số phiếu thật) dựng giống hệt từ doc-1, xstk, doc-4. Chỉ giữ ứng viên có đáp án vàng người: cạnh vàng thì có quan hệ,
    cặp hai đầu là đích vàng mà ngoài bao đóng vàng thì `khong`;
  - phiếu lặp (mặc định 5%): phiếu thật xuất lại, thứ tự ứng viên đảo.
  Mọi phiếu có `phieu_id` mờ và được xáo. **Đáp án và loại phiếu chỉ ghi ở `khoa.jsonl`**, không giao cho agentic.
Ghi `tmp/d01-phieu/phieu.jsonl` (giao agentic) và `tmp/d01-phieu/khoa.jsonl` (Claude giữ). Chạy bằng `tmp/venv-ml` (cần underthesea):
  tmp/venv-ml/Scripts/python.exe scripts/pass-phu-ml/xuat_phieu.py [--tai-lieu=d01-01,...] [--ti-le-kiem=0.05] [--ti-le-lap=0.05] [--ra=tmp/d01-phieu]
"""
import hashlib
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from dung_bang_cap import found, found_words, regexes, window_sentences, word_regexes  # noqa: E402
from doc2roadmap.domain.mentions import _names  # noqa: E402
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore  # noqa: E402

ALLOWED = {"taught", "uncertain"}
SOURCE_RANK = {"citation_hard": 0, "proposed_relation": 1, "same_section": 2, "citation_soft": 3, "contact": 4}
# Tài liệu phát triển có vàng người, dùng làm phiếu kiểm: (kho, phiên bản artifact danh tính, tệp vàng)
CHECK_DOCS = {"doc-1": ("artifacts", None, "doc-1-10-12-vang.json"), "xstk-ch3-1": ("artifacts", 40, "xstk-ch3-1-10-13-vang.json"),
              "doc-4": ("artifacts", None, "doc-4-chuong-8-vang.json")}


def latest_identity(store_root, doc, version=None):
    store = JsonArtifactStore(Path(store_root))
    if version is not None:
        return store.load_graph(doc, version)
    folder = Path(store_root) / "graph" / doc
    for path in sorted((p for p in folder.iterdir() if p.name.startswith("v")), key=lambda p: -int(p.name[1:])):
        manifest = json.loads((path / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("stage") == "identity":
            return store.load_graph(doc, int(path.name[1:]))
    raise FileNotFoundError(f"{doc}: chưa có artifact danh tính")


def chunks_for(doc, artifact):
    """Bản chunk mà chuỗi danh tính dùng: lần ngược identity → … → cụm → canonical → candidates → chunks."""
    store = JsonArtifactStore(ROOT / "artifacts")
    current = artifact
    while current.manifest.get("stage") != "clusters":
        current = store.load_graph(doc, current.manifest["upstream_version"])
    canonical = store.load_canonical(doc, current.manifest["config"]["canonical_version"])
    candidates = json.loads((ROOT / "artifacts/candidates" / doc / f"v{canonical.manifest['upstream_version']}" / "manifest.json")
                            .read_text(encoding="utf-8"))
    return store.load_chunks(doc, candidates["upstream_version"]).result.chunks


def sheets(doc, field, artifact, chunks, before=4, after=2):
    payload = artifact.payload
    nodes = payload["nodes"]
    node_by_id = {node["node_id"]: node for node in nodes}
    chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks}
    raw_patterns = {node_id: regexes(node) for node_id, node in node_by_id.items()}
    word_patterns = {node_id: word_regexes(node) for node_id, node in node_by_id.items()}
    order = {chunk.chunk_id: chunk.order_index for chunk in chunks}
    def taught_order(node_id):
        values = [order[c] for c in node_by_id[node_id].get("defining_chunk_ids", []) if c in order]
        return min(values) if values else 10 ** 9
    partners = {}
    for pair in payload.get("suspected_pairs", []):
        for x, y in ((pair["left"], pair["right"]), (pair["right"], pair["left"])):
            rank = min((SOURCE_RANK.get(source, 9) for source in pair.get("sources", [])), default=9)
            if "citation_hard" in pair.get("sources", []):
                citation = next((row for row in payload.get("citations", []) if (row["source"], row["target"]) == (x, y)), None)
                rank = 0 if citation else 3
            partners.setdefault(y, []).append((rank, taught_order(x), x))
    result = []
    for y, node in node_by_id.items():
        if node.get("teaching_status") not in ALLOWED or not node.get("learnable"):
            continue
        sentences, anchor_index = window_sentences(node, chunks, before, after)
        if not sentences:
            continue
        named, named_ids = [], set()
        for x, other in node_by_id.items():
            if x == y or not other.get("learnable"):
                continue
            hits = [i for i, sentence in enumerate(sentences) if found(raw_patterns[x], sentence) and found_words(word_patterns[x], sentence)]
            if hits:
                named.append((x, hits))
                named_ids.add(x)
        extra = [x for _, _, x in sorted(partners.get(y, [])) if x not in named_ids and node_by_id.get(x, {}).get("learnable")]
        extra = list(dict.fromkeys(extra))[:5]
        def candidate(x, hits, inside):
            other = node_by_id[x]
            return {"x_id": x, "x_ten": other["name"], "x_bi_danh": [name for name in _names(other)[1:] if name],
                    "x_dinh_nghia": (other.get("anchor") or {}).get("sentence"), "cau_co_ten": hits, "trong_cua_so": inside}
        anchor_chunk = chunk_by_id.get((node.get("anchor") or {}).get("chunk_id"))
        result.append({"phieu": "D-01", "doc_id": doc, "linh_vuc": field, "y_id": y, "y_ten": node["name"],
                       "y_bi_danh": [name for name in _names(node)[1:] if name], "muc": list(anchor_chunk.section_path) if anchor_chunk else [],
                       "cau": [{"i": i, "text": " ".join(sentence.split())} for i, sentence in enumerate(sentences)], "cau_neo": anchor_index,
                       "ung_vien": [candidate(x, hits, True) for x, hits in named] + [candidate(x, [], False) for x in extra]})
    return [sheet for sheet in result if sheet["ung_vien"]]


def check_answers(doc, artifact, gold_file):
    """Đáp án vàng cho phiếu kiểm: (X, Y) cạnh vàng → "co_quan_he"; hai đầu là đích vàng, ngoài bao đóng vàng → "khong"."""
    import networkx as nx
    gold = json.loads((ROOT / "artifacts/a8-gold" / gold_file).read_text(encoding="utf-8"))
    identity = artifact.payload.get("identity_map", {})
    edges = {(identity.get(e["prerequisite"], e["prerequisite"]), identity.get(e["target"], e["target"])) for e in gold["edges"]}
    targets = {identity.get(t, t) for t in gold["targets"]}
    graph = nx.DiGraph(list(edges))
    closure = {(a, b) for a in graph for b in nx.descendants(graph, a)}
    return edges, targets, closure


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    manifest = json.loads((ROOT / "document-data/manifest.json").read_text(encoding="utf-8"))
    fields = {book["id"]: book["field"] for book in manifest["books"] if book["split"] == "train"}
    docs = options["tai-lieu"].split(",") if "tai-lieu" in options else list(fields)
    rng = random.Random(20261005)
    real, missing = [], []
    for doc in docs:
        assert doc in fields, f"{doc} không phải sách học của D-01"
        try:
            artifact = latest_identity(ROOT / "artifacts", doc)
        except FileNotFoundError:
            missing.append(doc)
            continue
        real.extend(sheets(doc, fields[doc], artifact, chunks_for(doc, artifact)))
    checks = []
    for doc, (root, version, gold_file) in CHECK_DOCS.items():
        artifact = latest_identity(ROOT / root, doc, version)
        edges, targets, closure = check_answers(doc, artifact, gold_file)
        for sheet in sheets(doc, "kiem", artifact, chunks_for(doc, artifact)):
            if sheet["y_id"] not in targets:
                continue
            known = [c for c in sheet["ung_vien"] if (c["x_id"], sheet["y_id"]) in edges
                     or (c["x_id"] in targets and (c["x_id"], sheet["y_id"]) not in closure)]
            if known:
                answers = {c["x_id"]: ("co_quan_he" if (c["x_id"], sheet["y_id"]) in edges else "khong") for c in known}
                checks.append(({**sheet, "ung_vien": known}, answers))
    count_check = round(float(options.get("ti-le-kiem", 0.05)) * len(real))
    count_repeat = round(float(options.get("ti-le-lap", 0.05)) * len(real))
    chosen_checks = rng.sample(checks, min(count_check, len(checks)))
    repeats = rng.sample(real, min(count_repeat, len(real)))
    rows, keys = [], []
    def opaque(*parts):
        return "p_" + hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:16]
    for sheet in real:
        pid = opaque("thuc", sheet["doc_id"], sheet["y_id"])
        rows.append({"phieu_id": pid, **{k: v for k, v in sheet.items() if k != "linh_vuc"}, "linh_vuc": sheet["linh_vuc"]})
        keys.append({"phieu_id": pid, "loai": "thuc", "doc_id": sheet["doc_id"], "y_id": sheet["y_id"]})
    for sheet, answers in chosen_checks:
        pid = opaque("kiem", sheet["doc_id"], sheet["y_id"])
        rows.append({"phieu_id": pid, **{**sheet, "doc_id": "kiem-" + hashlib.sha256(sheet["doc_id"].encode()).hexdigest()[:6]}})
        keys.append({"phieu_id": pid, "loai": "kiem", "doc_id": sheet["doc_id"], "y_id": sheet["y_id"], "dap_an": answers})
    for sheet in repeats:
        pid = opaque("lap", sheet["doc_id"], sheet["y_id"])
        shuffled = list(sheet["ung_vien"])
        rng.shuffle(shuffled)
        rows.append({"phieu_id": pid, **{**sheet, "ung_vien": shuffled}})
        keys.append({"phieu_id": pid, "loai": "lap", "doc_id": sheet["doc_id"], "y_id": sheet["y_id"],
                     "lap_cua": opaque("thuc", sheet["doc_id"], sheet["y_id"])})
    rng.shuffle(rows)
    out = ROOT / options.get("ra", "tmp/d01-phieu")
    out.mkdir(parents=True, exist_ok=True)
    (out / "phieu.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    (out / "khoa.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in keys), encoding="utf-8")
    pairs = sum(len(row["ung_vien"]) for row in rows)
    print(json.dumps({"phieu_thuc": len(real), "phieu_kiem": len(chosen_checks), "phieu_kiem_co_san": len(checks), "phieu_lap": len(repeats),
                      "cap_can_gan": pairs, "thieu_artifact_danh_tinh": missing, "ra": str(out)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
