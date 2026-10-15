"""E8 (vòng 2): làm cứng có chọn lọc cạnh mà R17 làm mềm vì "ngược thứ tự sách". 0 USD, không gọi mô hình, không sửa `src/`.

Phát lại A9 → A10 (`phat_lai_e4.replay`), thay `soften_backward_edges` bằng monkeypatch rồi chấm trên vàng.

Phương án và tiêu chí chốt 2026-10-15, trước khi chấm, từ thống kê mô tả không nhìn vàng (doc-4 E5: 304 cạnh bị làm mềm; 177 cùng chương,
75 có confidence 0,9, 66 từ pass chính, 6 cùng section; doc-1 và xstk chỉ 19 và 6 cạnh). Cạnh ngược giữ cứng khi:
- `bat`: không bao giờ (R17 hiện tại); `tat`: luôn;
- `cung-chuong`: X và Y dạy trong cùng chương (section cấp 1 của chuỗi tổ tiên);
- `pass-chinh`: cạnh đến từ pass chính (đã đọc rộng hơn cửa sổ);
- `tin-chac`: confidence ≥ 0,9;
- `cung-chuong-tin-chac`: cả hai điều kiện trên.
Tiêu chí "đáng làm vé" (so với `bat`, cùng tài liệu và hệ): Q7 tăng ≥ 0,05, Q7b giảm ≤ 0,05, bao đóng P giảm ≤ 0,03; doc-1 và xstk không xấu đi
quá các ngưỡng đó. Vì gần như chỉ doc-4 bị tác động, phương án đạt chỉ là ứng viên; kết luận cuối đo trên vàng T-01.

Ghi một dòng JSON mỗi (hệ, tài liệu, phương án) vào stdout. Chạy từ gốc repo:
  .venv/Scripts/python.exe scripts/pass-phu-ml/thi_nghiem_e8.py [--he=llm-v3,e5-a-hieu-chinh] > tmp/pass-phu-ml/ket-qua/e8.jsonl
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


def same_chapter(edge, ancestry):
    source, target = ancestry.get(edge["source"]), ancestry.get(edge["target"])
    return bool(source) and bool(target) and source[0] == target[0]


def from_main(edge):
    return not str(edge.get("session_id", "")).startswith("secondary")


def confident(edge):
    return (edge.get("confidence") or 0) >= 0.9


RULES = {
    "bat": lambda edge, ancestry: False,
    "tat": lambda edge, ancestry: True,
    "cung-chuong": same_chapter,
    "pass-chinh": lambda edge, ancestry: from_main(edge),
    "tin-chac": lambda edge, ancestry: confident(edge),
    "cung-chuong-tin-chac": lambda edge, ancestry: same_chapter(edge, ancestry) and confident(edge),
}


def selective(rule):
    def soften(edges, position):
        # `ancestry` là biến cục bộ của BuildRoadmap.execute ngay trước lời gọi R17; đọc qua frame vì R17 không nhận nó.
        ancestry = sys._getframe(1).f_locals["ancestry"]
        hard, soft = WITH_R17(edges, position)
        back = [edge for edge in soft if edge.get("soft_reason") == "ngược thứ tự sách" and rule(edge, ancestry)]
        keep = {id(edge) for edge in back}
        restored = [{key: value for key, value in edge.items() if key not in ("soft", "soft_reason")} for edge in back]
        return hard + restored, [edge for edge in soft if id(edge) not in keep]
    return soften


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    for system in options.get("he", "llm-v3,e5-a-hieu-chinh").split(","):
        for doc in DOCS:
            root, version, _, _ = e4.GOLD_DOCS[doc]
            secondary = JsonArtifactStore(Path(root)).load_graph(doc, version)
            edges = (secondary.payload["secondary_edges"] if system == "llm-v3"
                     else json.loads(Path(f"tmp/pass-phu-ml/e4/{system}/{doc}-canh.json").read_text(encoding="utf-8")))
            for name, rule in RULES.items():
                build_roadmap.soften_backward_edges = selective(rule)
                payload, _ = e4.replay(doc, edges, secondary=secondary)
                result = e4.summary(e4.score_payload(doc, payload, "tmp/pass-phu-ml/e4", f"e8-{name}-{system}"), payload, len(edges))
                print(json.dumps({"he": system, "doc": doc, "phuong_an": name, **result}, ensure_ascii=False), flush=True)
    build_roadmap.soften_backward_edges = WITH_R17


if __name__ == "__main__":
    main()
