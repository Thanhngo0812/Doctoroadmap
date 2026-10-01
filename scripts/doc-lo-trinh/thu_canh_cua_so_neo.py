"""Thử nghiệm 0 USD cho vé 12: cạnh A8 có căn cứ trong **cửa sổ định nghĩa** của đích thì đúng hơn không?

Cửa sổ định nghĩa = câu neo của đích và hai câu kế tiếp trong cùng chunk (như căn cứ mở rộng của vé 11b). Cạnh "có tên trong cửa sổ" khi tên,
alias hoặc tên thành viên đã gộp của tiên quyết xuất hiện trọn từ trong cửa sổ (so sau NFKC, casefold, tách từ Unicode). Chỉ xét cạnh cứng có
hai đầu thuộc các đích của bộ vàng, chấm với bao đóng vàng (cách đọc Q7b). Đây là đường cơ sở luật thuần mà vé 12 phải vượt: mô hình được
phép nhận diễn đạt khác của tiên quyết ("the columns of A"), luật tên nguyên văn thì không. Không gọi mô hình. Chạy từ gốc repo:
  .venv/Scripts/python.exe scripts/doc-lo-trinh/thu_canh_cua_so_neo.py doc-1 doc-1-10-12-vang.json [--goc=<kho>] [--phien-ban=6] [--truoc=0]
`--truoc=K` (kiểm thử vé 12, 2026-10-01) mở cửa sổ thêm K câu **trước** câu neo trong cùng chunk: định nghĩa toán thường đặt giả thiết
("Giả sử K là một trường.", "Suppose A is an m-by-n matrix.") trước câu "được gọi là". K = 0 là cửa sổ gốc của vé 12.
"""
import json
import re
import sys
import unicodedata
from collections import Counter
from pathlib import Path

sys.path.insert(0, "src")
from doc2roadmap.application.use_cases.a8_score import load_gold, merge_gold  # noqa: E402
from doc2roadmap.domain.gold_scoring import transitive_closure  # noqa: E402
from doc2roadmap.domain.sentence_splitter import UnicodeSentenceSplitter  # noqa: E402
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore  # noqa: E402

NODE_LISTS = ("nodes", "merged_nodes", "mentioned_nodes", "excluded_nodes")


def words(text):
    return " ".join(re.findall(r"[^\W_]+", unicodedata.normalize("NFKC", text).casefold()))


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    doc, gold_name = args[0], args[1]
    root = Path(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--goc=")),
                     "artifacts/v3-05b-a9v10-evaluation"))
    version = next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--phien-ban=")), "6")
    before = int(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--truoc=")), "0"))
    folder = root / "graph" / doc / f"v{version}"
    graph = json.loads((folder / "graph.json").read_text(encoding="utf-8"))
    manifest = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    chunks = {chunk.chunk_id: chunk for chunk in
              JsonArtifactStore(Path("artifacts")).load_role_chunks(doc, manifest["config"]["chunks_version"]).result.chunks}
    nodes = {node["node_id"]: node for node in graph["nodes"]}
    info = {node["node_id"]: node for key in NODE_LISTS for node in graph.get(key, [])}
    identity = graph.get("identity_map", {})
    split = UnicodeSentenceSplitter().split

    def names(node_id):
        node = info[node_id]
        found = [node["name"], *[(a.get("name") if isinstance(a, dict) else a) for a in node.get("aliases", [])],
                 *[info[member]["name"] for member, head in identity.items() if head == node_id and member in info]]
        return [words(name) for name in found if name and len(words(name)) >= 2]

    def window(node_id):
        anchor = nodes[node_id].get("anchor") or {}
        chunk = chunks.get(anchor.get("chunk_id"))
        if chunk is None:
            return ""
        spans = split(chunk.text)
        start = anchor.get("char_start", 0)
        index = next((i for i, span in enumerate(spans) if span.start <= start < span.end), 0)
        return words(chunk.text[spans[max(0, index - before)].start:spans[min(index + 2, len(spans) - 1)].end])

    def grounded(source, target):
        text = f" {window(target)} "
        return any(f" {name} " in text for name in names(source))

    gold = load_gold(Path("artifacts/a8-gold") / gold_name)
    edges = {(identity.get(a, a), identity.get(b, b)) for a, b in merge_gold([gold], mode="union")}
    edges = {(a, b) for a, b in edges if a != b}
    closure = set(transitive_closure(edges))
    targets = {identity.get(target, target) for target in gold["targets"]}
    sequence = set(graph["sequence"])
    counts = Counter()
    for edge in graph["requires_edges"]:
        source, target = edge["source"], edge["target"]
        if edge.get("soft") or not {source, target} <= targets & sequence:
            continue
        verdict = "direct" if (source, target) in edges else ("closure" if (source, target) in closure else "outside")
        counts[(grounded(source, target), verdict)] += 1
    print(f"# {doc} v{version}: cạnh máy cứng, hai đầu thuộc đích vàng và nằm trong dãy học")
    for key, label in ((True, "tiên quyết có tên trong cửa sổ định nghĩa"), (False, "không có tên trong cửa sổ")):
        total = sum(value for (flag, _), value in counts.items() if flag == key)
        if total:
            direct, via, outside = counts[(key, "direct")], counts[(key, "closure")], counts[(key, "outside")]
            print(f"  {label:<42} n={total:>3} | vàng trực tiếp {direct:>3} | bắc cầu {via:>3} | ngoài vàng {outside:>3} | "
                  f"đúng theo bao đóng {(direct + via) / total:.2f}")
    inside = [(a, b) for a, b in edges if a in sequence and b in sequence]
    named = sum(1 for a, b in inside if grounded(a, b))
    print(f"  cạnh vàng trong dãy học có tên tiên quyết trong cửa sổ định nghĩa của đích: {named}/{len(inside)}")


if __name__ == "__main__":
    main()
