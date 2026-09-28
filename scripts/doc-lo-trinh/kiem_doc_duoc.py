"""Bảng kiểm đọc được (spec v3 R11, vé v3-02) trên một artifact `stages`. Không gọi mô hình.

Chạy từ gốc repo:  .venv/Scripts/python.exe scripts/doc-lo-trinh/kiem_doc_duoc.py <doc> [phiên bản stages] [--goc=<kho>]
In từng vi phạm và dòng tổng; mã thoát 0 dù có vi phạm (đây là công cụ đọc, không phải cổng).
`--goc` trỏ tới một kho thử (vd. artifacts/v3-05b-a9v10-evaluation); mặc định là kho chính `artifacts`.
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

# Mẫu tiêu đề của vùng không phải bài giảng (spec v3 R1). Khi artifact chunks có `role` (vé 03) thì dùng vai trò thay mẫu.
NON_TEACHING = re.compile(r"bài tập|câu hỏi ôn tập|đề số|đề cương|nội dung môn học|mục lục|lời nói đầu|mở ?đầu|"
                          r"exercises?\b|problems?\b|preface|foreword|contents|improvements|top ten", re.IGNORECASE)
NUMBERED_LABEL = re.compile(r"^(tính chất|định lý|định lí|hệ quả|mệnh đề|bổ đề|ví dụ|proposition|theorem|lemma|corollary|"
                            r"property|example)\s*\d+[\w.]*$", re.IGNORECASE)
GENERIC = {"definition", "theorem", "định nghĩa", "định lý", "định lí", "ví dụ", "example", "proof", "chứng minh"}
MAX_SHOWN_PREREQUISITES = 3
ROOT = Path("artifacts")


def latest_stages(doc):
    for version in sorted((int(p.name[1:]) for p in (ROOT / "graph" / doc).glob("v*")), reverse=True):
        manifest = json.loads((ROOT / "graph" / doc / f"v{version}" / "manifest.json").read_text(encoding="utf-8"))
        if manifest.get("stage") == "stages":
            return version
    raise SystemExit(f"{doc}: chưa có artifact stages")


def main(doc, version=None):
    version = version or latest_stages(doc)
    payload = json.loads((ROOT / "graph" / doc / f"v{version}" / "graph.json").read_text(encoding="utf-8"))
    nodes = {n["node_id"]: n for n in payload["nodes"]}
    modules = payload["modules"]
    problems = Counter()
    rows = []

    def flag(kind, text):
        problems[kind] += 1
        rows.append(f"  [{kind}] {text}")

    titles = [m["title"] for m in modules]
    if titles and NON_TEACHING.search(titles[0]):
        flag("module-1-ngoai-bai-giang", titles[0])
    for title, count in Counter(titles).items():
        if count > 1:
            flag("ten-module-trung", f"{title!r} ×{count}")
    for title in titles:
        if NON_TEACHING.search(title):
            flag("ten-tu-vung-khong-day", title)
        if len(title.split()) > 12:
            flag("ten-la-cau-dai", title)
    for node_id in payload["sequence"]:
        node = nodes[node_id]
        if node.get("teaching_status") in ("mentioned_only", "unchecked"):
            flag("chi-nhac-trong-day-hoc", f"{node['name']} [{node.get('teaching_status')}]")
        shown = node.get("display_prerequisites", node.get("prerequisites", []))
        if len(shown) > MAX_SHOWN_PREREQUISITES:
            flag("can-qua-dai", f"{node['name']}: {len(shown)} tiên quyết hiển thị")
        name = node.get("display_name", node["name"]).strip()
        if NUMBERED_LABEL.match(name) or name.casefold() in GENERIC:
            flag("ten-khai-niem-vo-nghia", name)
    # Một section bị tách thành hai module cách nhau quá một module khác chương: xét section cụ thể nhất của module.
    seen = {}
    for module in modules:
        for section in module.get("section_ids", [])[:1]:
            if section in seen and module["index"] - seen[section] > 2:
                flag("muc-bi-xe", f"{module['title']!r}: module {seen[section] + 1} và {module['index'] + 1}")
            seen.setdefault(section, module["index"])
    print(f"# {doc} stages v{version}: {len(payload['sequence'])} khái niệm, {len(modules)} module")
    for kind in ("module-1-ngoai-bai-giang", "ten-module-trung", "ten-tu-vung-khong-day", "ten-la-cau-dai",
                 "chi-nhac-trong-day-hoc", "can-qua-dai", "ten-khai-niem-vo-nghia", "muc-bi-xe"):
        print(f"  {kind:<26} {problems.get(kind, 0)}")
    if "--chi-tiet" in sys.argv:
        print("\n".join(rows))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    ROOT = Path(next((a.split("=", 1)[1] for a in sys.argv[1:] if a.startswith("--goc=")), "artifacts"))
    main(args[0], int(args[1]) if len(args) > 1 else None)
