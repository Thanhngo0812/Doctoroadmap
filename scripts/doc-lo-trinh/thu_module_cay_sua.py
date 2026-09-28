"""Thử nghiệm (kiểm thử vé 09b): chia module trên cây mục đã sửa thay cho cây vỡ, cho tài liệu có `role_transfer`.

Câu hỏi: tên module doc-2 còn "Chapter 3 — …" vì 09b chỉ chuyển cây đã sửa cho **tên**, còn **ranh giới module** vẫn tính trên
cây vỡ của version chunks cũ. Nếu `segment_modules` nhận đường dẫn mục từ cây đã sửa (phép chuyển theo văn bản của vé 14b), module
có nằm gọn trong một mục hơn không, và tên nền có cụ thể hơn không? Dãy học, ID, cạnh giữ nguyên; chỉ đổi cách chia module.
Không gọi mô hình. Chạy từ gốc repo:
  .venv/Scripts/python.exe scripts/doc-lo-trinh/thu_module_cay_sua.py [doc] [--goc=artifacts/v3-05b-a9v10-evaluation] [--phien-ban=5]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")
from doc2roadmap.config import Settings  # noqa: E402
from doc2roadmap.domain.module_titles import clean_titles, common_content_title, transfer_chunk_sections  # noqa: E402
from doc2roadmap.domain.sequence import _at, choose_levels, segment_modules  # noqa: E402
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore  # noqa: E402


def chains(sections):
    def chain(section_id):
        path, current = [], sections.get(section_id)
        while current is not None and current.level >= 1:
            path.append(current.section_id)
            current = sections.get(current.parent_section_id)
        return path[::-1]
    return chain


def segment(sequence, ancestry, width):
    """Đúng phép chia của `build_sequence_roadmap`, chỉ thay đường dẫn mục."""
    chapter_level, unit_level = choose_levels({node: ancestry.get(node, []) for node in sequence}, width)
    unit_of = {node: _at(ancestry.get(node), unit_level) for node in sequence}
    chapter_of = {node: _at(ancestry.get(node), chapter_level) for node in sequence}
    return segment_modules(sequence, width=width, unit_of=unit_of, chapter_of=chapter_of)


def base_section(section_ids, sections, cleaned):
    """Như `common_content_title` nhưng trả section: tổ tiên chung sâu nhất là mục nội dung có tiêu đề hợp lệ."""
    paths = [path_of(sections, section_id) for section_id in section_ids]
    answer = None
    for ids in zip(*paths):
        if len(set(ids)) != 1:
            break
        if sections[ids[0]].role == "noi_dung" and ids[0] in cleaned:
            answer = ids[0]
    return answer


def numbering_only(title):
    """Tiêu đề không còn từ ≥ 2 chữ cái sau khi bỏ các token có chữ số ("6B", "3.2") — nhận bằng Unicode, không danh sách từ."""
    words = [token for token in title.split() if not any(char.isdigit() for char in token)]
    return not any(sum(char.isalpha() for char in token) >= 2 for token in words)


def titles_on_fixed_tree(groups, fixed_section_of, sections, cleaned):
    rows = []
    for members in groups:
        section_ids = [fixed_section_of.get(node) for node in members]
        base = base_section(section_ids, sections, cleaned) if all(section_ids) else None
        assert (cleaned.get(base, "") if base else "") == (
            common_content_title(section_ids, sections, cleaned) if all(section_ids) else "")
        units = {tuple(path_of(sections, s)[:2]) for s in section_ids if s}
        rows.append((cleaned.get(base, "") if base else "", sections[base].level if base else None, len(units)))
    return rows


def path_of(sections, section_id):
    path, current = [], sections.get(section_id)
    while current is not None and current.level >= 1:
        path.append(current.section_id)
        current = sections.get(current.parent_section_id)
    return path[::-1]


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    doc = args[0] if args else "doc-2"
    root = Path(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--goc=")),
                     "artifacts/v3-05b-a9v10-evaluation"))
    version = int(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--phien-ban=")), "5"))
    settings = Settings()
    graph = json.loads((root / "graph" / doc / f"v{version}" / "graph.json").read_text(encoding="utf-8"))
    manifest = json.loads((root / "graph" / doc / f"v{version}" / "manifest.json").read_text(encoding="utf-8"))
    store = JsonArtifactStore(settings.artifact_dir)
    chunks = store.load_role_chunks(doc, manifest["config"]["chunks_version"])
    reference_version = (chunks.manifest.get("role_transfer") or {}).get("reference_version")
    if not reference_version:
        raise SystemExit(f"{doc}: không có role_transfer — cây mục của graph đã là cây hiện hành")
    reference = store.load_chunks(doc, reference_version)
    old_sections = {s.section_id: s for s in chunks.result.sections}
    new_sections = {s.section_id: s for s in reference.result.sections}
    by_id = {c.chunk_id: c for c in chunks.result.chunks}
    transferred = transfer_chunk_sections(chunks.result.chunks, reference.result.chunks)
    nodes = {n["node_id"]: n for n in graph["nodes"]}
    sequence = graph["sequence"]

    def teaching_chunk(node):
        ids = node.get("teaching_chunk_ids") or node.get("defining_chunk_ids", [])
        found = sorted((by_id[i] for i in ids if i in by_id and by_id[i].role == "noi_dung"), key=lambda c: c.order_index)
        return found[0] if found else None

    old_chain, new_chain = chains(old_sections), chains(new_sections)
    old_ancestry, new_ancestry, fixed_section_of = {}, {}, {}
    for node_id in sequence:
        chunk = teaching_chunk(nodes[node_id])
        if chunk is None:
            continue
        old_ancestry[node_id] = old_chain(chunk.parent_section_id)
        target = transferred.get(chunk.chunk_id)
        if target:
            new_ancestry[node_id] = new_chain(target)
            fixed_section_of[node_id] = target
    cleaned = clean_titles(list(new_sections.values()))
    width = settings.roadmap_stage_cap
    print(f"# {doc}: {len(sequence)} khái niệm, width {width}; đường dẫn cây sửa cho {len(new_ancestry)}/{len(sequence)}")
    current = [module["node_ids"] for module in graph["modules"]]
    replay = segment(sequence, old_ancestry, width)
    print(f"phép chia lại trên cây vỡ trùng module hiện tại: {replay == current}")
    for label, groups in [("hiện tại (cây vỡ)", current), ("thử (cây sửa)", segment(sequence, new_ancestry, width))]:
        rows = titles_on_fixed_tree(groups, fixed_section_of, new_sections, cleaned)
        single = sum(1 for _, _, units in rows if units == 1)
        empty = sum(1 for base, _, _ in rows if not base)
        chapter = sum(1 for base, level, _ in rows if base and level == 1)
        number = sum(1 for base, _, _ in rows if base and numbering_only(base))
        print(f"\n## {label}: {len(groups)} module; nằm gọn trong một mục cấp 2: {single}/{len(groups)}; "
              f"tên nền rỗng {empty}, cấp chương {chapter}, chỉ-số {number}")
        print("   tên nền:", [base for base, _, _ in rows])


if __name__ == "__main__":
    main()
