"""So chunk của bộ đọc nhẹ với chunk của docling (vé v4-10 bước 2): cùng bộ cắt chunk, cùng tokenizer, cùng tham số luồng đã ghim. 0 USD.

Cây docling là bản parse mà chunk của luồng đang ghim. Cây nhẹ lấy từ `doc_nhe.py`. Hai cây đi qua đúng `chunk_document` với tham số đọc từ
manifest chunk đã ghim (kể cả `heading_scheme`). Không áp `strip_lines` cho bên nào, để so công bằng. Báo:
- số mục, số chunk, tổng token;
- độ giống dãy đường mục (tên mục theo thứ tự);
- căn chunk: với mỗi chunk docling, chunk nhẹ giống nhất (Jaccard theo từ, trong cửa sổ ±2 trang); tỉ lệ chunk docling có bạn giống từ 0,8 và
  từ 0,5; chiều ngược lại cũng báo.
Chạy từ gốc repo:  .venv/Scripts/python.exe scripts/thu-a1/so_chunk_doc_nhe.py [--tai-lieu=doc-4,doc-1,xstk]
"""
import difflib
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from doc_nhe import DOCS, parse  # noqa: E402
from doc2roadmap.domain.chunking import chunk_document  # noqa: E402
from doc2roadmap.domain.models import DocumentNode, DocumentTree  # noqa: E402
from doc2roadmap.domain.sentence_splitter import UnicodeSentenceSplitter  # noqa: E402
from doc2roadmap.infrastructure.text import SentencePieceTokenCounter  # noqa: E402

PINNED_CHUNKS = {"doc-1": 7, "doc-4": 6, "xstk": 5}
DOC_IDS = {"doc-1": "doc-1", "doc-4": "doc-4", "xstk": "xstk-ch3-1"}


def words(text):
    return set(re.findall(r"[^\W\d_]+|\d+", unicodedata.normalize("NFC", text).casefold()))


def light_tree(nodes):
    result = []
    for index, node in enumerate(nodes):
        kind = node["node_type"]
        text, raw = node["text"], None
        if kind == "formula":
            text, raw = "[formula]", node["text"]
        elif kind == "figure":
            text = node["text"] or "[figure]"
        elif kind == "caption":
            kind = "text"
        if not (text or "").strip():
            continue
        result.append(DocumentNode(node_type=kind, text=text, reading_order=len(result), level=node.get("level"), page=node["page"],
                                   raw_text=raw, tree_depth=1))
    return DocumentTree(nodes=result)


def chunks_of(tree, doc_id, counter, settings):
    return chunk_document(tree, doc_id, counter, UnicodeSentenceSplitter(), **settings).chunks


def compare(reference, candidate):
    def paths(chunks):
        out = []
        for chunk in chunks:
            key = " > ".join(" ".join(sorted(words(part))) for part in chunk.section_path)
            if not out or out[-1] != key:
                out.append(key)
        return out
    ref_words = [words(chunk.text) for chunk in reference]
    cand_words = [words(chunk.text) for chunk in candidate]
    def best(source, source_chunks, target, target_chunks):
        values = []
        for index, chunk in enumerate(source_chunks):
            page = chunk.page or 0
            scores = [len(source[index] & target[j]) / max(len(source[index] | target[j]), 1)
                      for j, other in enumerate(target_chunks) if abs((other.page or 0) - page) <= 2]
            values.append(max(scores, default=0.0))
        return values
    forward = best(ref_words, reference, cand_words, candidate)
    backward = best(cand_words, candidate, ref_words, reference)
    leaf_hits = 0
    for index, chunk in enumerate(reference):  # tiêu đề lá của chunk nhẹ giống nhất có cùng mục không (cho phép chứa nhau)
        page = chunk.page or 0
        options = [(len(ref_words[index] & cand_words[j]) / max(len(ref_words[index] | cand_words[j]), 1), j)
                   for j, other in enumerate(candidate) if abs((other.page or 0) - page) <= 2]
        if not options:
            continue
        _, j = max(options)
        a = " ".join(sorted(words(chunk.section_path[-1]))) if chunk.section_path else ""
        b = " ".join(sorted(words(candidate[j].section_path[-1]))) if candidate[j].section_path else ""
        a_words, b_words = words(chunk.section_path[-1]) if chunk.section_path else set(), words(candidate[j].section_path[-1]) if candidate[j].section_path else set()
        leaf_hits += bool(a_words and b_words and (a_words <= b_words or b_words <= a_words or
                                                   len(a_words & b_words) / len(a_words | b_words) >= 0.8))
    share = lambda values, limit: round(sum(value >= limit for value in values) / max(len(values), 1), 3)  # noqa: E731
    return {
        "chunk": [len(reference), len(candidate)],
        "duong_muc_giong": round(difflib.SequenceMatcher(None, paths(reference), paths(candidate), autojunk=False).ratio(), 3),
        "so_duong_muc": [len(paths(reference)), len(paths(candidate))],
        "docling_co_ban_tu_0_8": share(forward, 0.8), "docling_co_ban_tu_0_5": share(forward, 0.5),
        "nhe_co_ban_tu_0_8": share(backward, 0.8), "nhe_co_ban_tu_0_5": share(backward, 0.5),
        "jaccard_tb_docling": round(sum(forward) / max(len(forward), 1), 3),
        "cung_muc_la": round(leaf_hits / max(len(reference), 1), 3),
    }


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    counter = SentencePieceTokenCounter(ROOT / "vendor/gemma/tokenizer.model", "google-gemma-sentencepiece-v1")
    for key in options.get("tai-lieu", "doc-4,doc-1,xstk").split(","):
        pdf, tree_path = DOCS[key]
        manifest = json.loads((ROOT / "artifacts/chunks" / DOC_IDS[key] / f"v{PINNED_CHUNKS[key]}" / "manifest.json").read_text(encoding="utf-8"))
        chunk_config = manifest["config"]["chunk"]
        settings = {name: chunk_config[name] for name in ("max_tokens", "max_table_tokens", "hard_cap_tokens", "target_tokens",
                                                          "sentence_overlap") if name in chunk_config}
        settings["heading_scheme"] = chunk_config.get("heading_scheme")
        for name in ("result_min_count", "result_max_body_chars"):
            if name in chunk_config:
                settings[name] = chunk_config[name]
        reference_data = json.loads((ROOT / tree_path).read_text(encoding="utf-8"))
        reference_tree = DocumentTree(nodes=[DocumentNode.from_dict(node) for node in reference_data["nodes"]],
                                      structure_warnings=reference_data.get("structure_warnings", []),
                                      parse_stats=reference_data.get("parse_stats", {}))
        nodes, _ = parse(ROOT / pdf)
        reference = chunks_of(reference_tree, DOC_IDS[key], counter, settings)
        candidate = chunks_of(light_tree(nodes), DOC_IDS[key], counter, settings)
        print(json.dumps({key: {"tham_so": settings, **compare(reference, candidate)}}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
