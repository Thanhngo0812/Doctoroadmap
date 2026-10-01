"""Bảng kiểm đọc được (spec v3 R11; vé v3-02, viết lại theo vé 02b) trên một artifact `stages`. Không gọi mô hình.

Chạy từ gốc repo:  .venv/Scripts/python.exe scripts/doc-lo-trinh/kiem_doc_duoc.py <doc> [phiên bản stages] [--goc=<kho>] [--chi-tiet]
Tự kiểm các luật nhận mã/độ dài trên ví dụ đa ngôn ngữ:  ... kiem_doc_duoc.py --tu-kiem
In từng vi phạm và dòng tổng; mã thoát 0 dù có vi phạm (đây là công cụ đọc, không phải cổng).
`--goc` trỏ tới một kho thử (vd. artifacts/v3-05b-a9v10-evaluation); mặc định là kho chính `artifacts`. Chunk luôn đọc từ kho chính.

Không có danh sách từ của ngôn ngữ nào (spec v3, Nguyên tắc đa ngôn ngữ). Vùng không dạy lấy từ vai trò section của R1. Nhãn đánh số lấy từ
họ nhãn trong chính tài liệu như R9 (`label_families`). Mã chương/mục lấy từ họ đánh số của `document_structure`.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, "src")
from doc2roadmap.domain.anchors import label_families, numbered_label  # noqa: E402
from doc2roadmap.domain.document_structure import chapter_members, section_code  # noqa: E402
from doc2roadmap.domain.module_titles import clean_titles  # noqa: E402
from doc2roadmap.domain.unicode_text import unspaced_character  # noqa: E402
from doc2roadmap.infrastructure.artifacts import JsonArtifactStore  # noqa: E402

MAX_SHOWN_PREREQUISITES = 3
MAX_WORDS, MAX_UNSPACED_CHARS = 12, 36  # cùng ngưỡng với `clean_titles`
SUFFIX = " — "  # dấu nối tên nền và phần phụ của `NameModules`
KINDS = ("module-1-ngoai-bai-giang", "ten-module-trung", "ten-tu-vung-khong-day", "ten-la-cau-dai", "ten-nen-la-goc",
         "ten-nen-chi-co-ma", "ten-theo-khai-niem-dau", "chi-nhac-trong-day-hoc", "can-qua-dai", "ten-khai-niem-vo-nghia",
         "muc-bi-xe")
ROOT = Path("artifacts")


def latest_stages(doc):
    for version in sorted((int(p.name[1:]) for p in (ROOT / "graph" / doc).glob("v*")), reverse=True):
        manifest = json.loads((ROOT / "graph" / doc / f"v{version}" / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("stage") == "stages":
            return version
    raise SystemExit(f"{doc}: chưa có artifact stages")


def _norm(text):
    return " ".join(str(text).casefold().split())


def too_long(title):
    if any(unspaced_character(char) for char in title):
        return len(title.replace(" ", "")) > MAX_UNSPACED_CHARS
    return len(title.split()) > MAX_WORDS


def numbering_only_titles(sections):
    """Tiêu đề chỉ gồm mã, nhận bằng cấu trúc chứ không bằng từ khoá.

    - Mã mục ("6B") phủ trọn tiêu đề.
    - Thành viên họ chương (`chapter_members`) có **khung** (thay số bằng #) lặp ở ít nhất hai chương: "Chapter #", "Chương #", "第#章".
      Chương có tên riêng ("Kapitel 2 Lineare Abbildungen") có khung riêng nên không bị tính.
    """
    ordered = [section for section in sections if getattr(section, "level", 0) > 0]
    members = chapter_members([(index, section.title, section.level, getattr(section, "order_index", index))
                               for index, section in enumerate(ordered)])
    skeleton = {index: _norm(re.sub(r"\d+(?:\.\d+)*", "#", str(ordered[index].title))) for index in members}
    repeated = {shape for shape, count in Counter(skeleton.values()).items() if count >= 2}
    found = set()
    for index, section in enumerate(ordered):
        title = str(section.title).strip()
        code = section_code(title)
        if (code is not None and code.span() == (0, len(title))) or skeleton.get(index) in repeated:
            found.add(_norm(title))
    return found


def self_check():
    """`--tu-kiem`: ví dụ tổng hợp ở chữ Latin ngoài vi/en và chữ viết không cách từ; sai thì dừng."""
    from types import SimpleNamespace

    def tree(titles):
        return [SimpleNamespace(title=title, level=1, order_index=5 * index) for index, title in enumerate(titles)]

    assert numbering_only_titles(tree(["Kapitel 1", "Kapitel 2 Lineare Abbildungen", "Kapitel 3"])) == {"kapitel 1", "kapitel 3"}
    assert numbering_only_titles(tree(["第1章", "第2章", "第3章 線形写像"])) == {"第1章", "第2章"}
    assert numbering_only_titles(tree(["6B", "6C Orthogonal Complements"])) == {"6b"}
    assert too_long(" ".join(["mot"] * 13)) and not too_long(" ".join(["mot"] * 12))
    assert too_long("線" * 37) and not too_long("線" * 36)
    print("tự kiểm: đạt")


def main(doc, version=None):
    version = version or latest_stages(doc)
    folder = ROOT / "graph" / doc / f"v{version}"
    payload = json.loads((folder / "graph.json").read_text(encoding="utf-8"))
    config = json.loads((folder / "manifest.json").read_text(encoding="utf-8")).get("config", {})
    store = JsonArtifactStore(Path("artifacts"))
    chunks = store.load_role_chunks(doc, config["chunks_version"])
    title_version = config.get("title_sections_version") or config["chunks_version"]
    title_chunks = chunks if title_version == config["chunks_version"] else store.load_chunks(doc, title_version)
    trees = [chunks.result.sections, title_chunks.result.sections]
    chunk_by_id = {chunk.chunk_id: chunk for chunk in chunks.result.chunks}
    section_role = {section.section_id: (section.role, getattr(section, "has_direct_content", True))
                    for tree in trees for section in tree}

    nodes = {n["node_id"]: n for n in payload["nodes"]}
    everyone = [*payload["nodes"], *payload.get("mentioned_nodes", []), *payload.get("merged_nodes", []),
                *payload.get("excluded_nodes", [])]
    families = label_families(everyone, chunks.result.chunks)
    root_titles = {_norm(title) for tree in trees
                   for title in clean_titles([s for s in tree if getattr(s, "level", 1) == 0]).values()}
    code_titles = numbering_only_titles(title_chunks.result.sections) | numbering_only_titles(chunks.result.sections)
    non_teaching_titles = {_norm(title) for tree in trees for section_id, title in clean_titles(list(tree)).items()
                           if section_role[section_id][0] != "noi_dung" and section_role[section_id][1]}
    modules = payload["modules"]
    problems, rows = Counter(), []

    def flag(kind, text):
        problems[kind] += 1
        rows.append(f"  [{kind}] {text}")

    def teaching_regions(module):
        """Vai trò nơi dạy từng khái niệm: section dùng đặt tên (09c) nếu có, nếu không thì chunk dạy."""
        if module.get("title_section_ids"):
            return [section_role.get(section_id, ("noi_dung", True)) for section_id in module["title_section_ids"] if section_id]
        regions = []
        for node_id in module["node_ids"]:
            for chunk_id in nodes[node_id].get("teaching_chunk_ids") or nodes[node_id].get("defining_chunk_ids", [])[:1]:
                if chunk_id in chunk_by_id:
                    regions.append((chunk_by_id[chunk_id].role, True))
        return regions

    if modules and any(role != "noi_dung" and direct for role, direct in teaching_regions(modules[0])):
        flag("module-1-ngoai-bai-giang", modules[0]["title"])
    titles = [module["title"] for module in modules]
    for title, count in Counter(_norm(title) for title in titles).items():
        if count > 1:
            flag("ten-module-trung", f"{title!r} ×{count}")
    for module in modules:
        title = module["title"]
        base = _norm(title.split(SUFFIX, 1)[0])
        if base in non_teaching_titles:
            flag("ten-tu-vung-khong-day", title)
        if too_long(title):
            flag("ten-la-cau-dai", title)
        if base in root_titles:
            flag("ten-nen-la-goc", title)
        if base in code_titles:
            flag("ten-nen-chi-co-ma", title)
        if module.get("title_source") == "concept":
            flag("ten-theo-khai-niem-dau", title)
    for node_id in payload["sequence"]:
        node = nodes[node_id]
        if node.get("teaching_status") in ("mentioned_only", "unchecked"):
            flag("chi-nhac-trong-day-hoc", f"{node['name']} [{node.get('teaching_status')}]")
        shown = node.get("display_prerequisites", node.get("prerequisites", []))
        if len(shown) > MAX_SHOWN_PREREQUISITES:
            flag("can-qua-dai", f"{node['name']}: {len(shown)} tiên quyết hiển thị")
        name = node.get("display_name") or node["name"]
        label = numbered_label(name)
        if (label and label[0] in families) or _norm(name) in families:
            flag("ten-khai-niem-vo-nghia", name)
    # Một section bị tách thành hai module cách nhau quá một module khác: xét section cụ thể nhất của module.
    seen = {}
    for module in modules:
        for section in module.get("section_ids", [])[:1]:
            if section in seen and module["index"] - seen[section] > 2:
                flag("muc-bi-xe", f"{module['title']!r}: module {seen[section] + 1} và {module['index'] + 1}")
            seen.setdefault(section, module["index"])
    print(f"# {doc} stages v{version}: {len(payload['sequence'])} khái niệm, {len(modules)} module; "
          f"họ nhãn {sorted(families)}")
    for kind in KINDS:
        print(f"  {kind:<26} {problems.get(kind, 0)}")
    if "--chi-tiet" in sys.argv:
        print("\n".join(rows))


if __name__ == "__main__":
    if "--tu-kiem" in sys.argv:
        self_check()
        sys.exit(0)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ROOT = Path(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--goc=")), "artifacts"))
    main(args[0], int(args[1]) if len(args) > 1 else None)
