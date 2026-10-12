"""E8 (vòng 2), khảo sát: phát lại A9 → A10 khi tắt R17 (`soften_backward_edges`: tiên quyết được dạy sau đích thì làm mềm) và chấm trên vàng.
0 USD, không gọi mô hình. Tắt bằng monkeypatch trong script nghiên cứu, không sửa `src/`. Bản bật R17 của `llm-v3` phải ra đúng số E4 đã báo.

Hệ: `llm-v3` (cạnh pass phụ v3) và các lượt đã lắp cạnh bằng `lap_canh.py` (đọc `tmp/pass-phu-ml/e4/<lượt>/<doc>-canh.json`).
Ghi một dòng JSON mỗi (hệ, tài liệu, chế độ). Chạy từ gốc repo:
  .venv/Scripts/python.exe scripts/pass-phu-ml/phat_lai_tat_r17.py [--he=llm-v3,e5-a-hieu-chinh]
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")
sys.path.insert(0, "scripts/pass-phu-ml")
sys.path.insert(0, "scripts/doc-lo-trinh")
import doc2roadmap.application.use_cases.build_roadmap as build_roadmap  # noqa: E402
import phat_lai_e4 as e4  # noqa: E402
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore  # noqa: E402

DOCS = ("doc-1", "xstk-ch3-1", "doc-4")
WITH_R17 = build_roadmap.soften_backward_edges


def without_r17(edges, position):
    """Giữ nguyên cạnh đã mềm từ trước (`cong_cu`), không làm mềm thêm cạnh nào vì ngược thứ tự sách."""
    return [edge for edge in edges if not edge.get("soft")], [edge for edge in edges if edge.get("soft")]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    for system in options.get("he", "llm-v3,e5-a-hieu-chinh").split(","):
        for doc in DOCS:
            root, version, _, _ = e4.GOLD_DOCS[doc]
            secondary = JsonArtifactStore(Path(root)).load_graph(doc, version)
            edges = (secondary.payload["secondary_edges"] if system == "llm-v3"
                     else json.loads(Path(f"tmp/pass-phu-ml/e4/{system}/{doc}-canh.json").read_text(encoding="utf-8")))
            for mode, soften in (("bat", WITH_R17), ("tat", without_r17)):
                build_roadmap.soften_backward_edges = soften
                payload, _ = e4.replay(doc, edges, secondary=secondary)
                result = e4.summary(e4.score_payload(doc, payload, "tmp/pass-phu-ml/e4", f"r17-{mode}-{system}"), payload, len(edges))
                print(json.dumps({"he": system, "doc": doc, "r17": mode, **result}, ensure_ascii=False), flush=True)
    build_roadmap.soften_backward_edges = WITH_R17


if __name__ == "__main__":
    main()
