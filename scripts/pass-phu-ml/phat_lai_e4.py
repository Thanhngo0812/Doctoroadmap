"""E4 (R-02 mục 7.7): thay tập cạnh pass phụ, phát lại A9 → tên khái niệm → A10, rồi chấm trên vàng người. 0 USD, không gọi mô hình.

- Pass chính, nút, chunk, mention map giữ nguyên artifact pass phụ v3; chỉ thay `secondary_edges`.
- Tên khái niệm dùng lại phản hồi đã ghi của khâu này (đầu vào là nút và câu neo, không phụ thuộc cạnh); thiếu bản ghi thì dừng.
- A10 chạy mã hiện tại với `module_cap` của artifact A10 v3 đã chấm (doc-1, doc-2: v7; xstk: v45; doc-4: v11).
- Chấm bằng `score` của `scripts/doc-lo-trinh/cham_tap_giu_lai.py` (Q6, Q7, Q7b, cạnh trực tiếp và bao đóng trên rút gọn bắc cầu).
- **Kiểm chứng bộ phát lại:** phương án `llm-v3` (cạnh pass phụ v3 nguyên vẹn) phải ra đúng `sequence` và `requires_edges` của A10 đã chấm.
Phương án:
  llm-v3        cạnh pass phụ v3;
  khong         không có pass phụ (chỉ cạnh pass chính);
  tep:<đường>   cạnh đọc từ tệp JSON (danh sách cạnh đúng dạng `validate_main_proposals`), do bộ lắp cạnh ML sinh ra.
Chạy từ gốc repo:
  .venv/Scripts/python.exe scripts/pass-phu-ml/phat_lai_e4.py <doc> <phương án> [--nhan=<tên lượt>] [--ra=tmp/pass-phu-ml/e4]
"""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, "src")
sys.path.insert(0, "scripts/doc-lo-trinh")
from cham_tap_giu_lai import score  # noqa: E402
from doc2roadmap.application.use_cases.build_roadmap import BuildRoadmap  # noqa: E402
from doc2roadmap.application.use_cases.name_concept_labels import NameConceptLabels  # noqa: E402
from doc2roadmap.application.use_cases.validate_graph import ValidateGraph  # noqa: E402
from doc2roadmap.domain.canonical import digest  # noqa: E402
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore  # noqa: E402

# tài liệu: (kho, phiên bản pass phụ v3, phiên bản A10 đã chấm, tệp vàng)
GOLD_DOCS = {
    "doc-1": ("artifacts/v3-r12-final-evaluation", 2, 7, "doc-1-10-12-vang.json"),
    "doc-2": ("artifacts/v3-r12-final-evaluation", 2, 7, "doc-2-98-115-vang.json"),
    "xstk-ch3-1": ("artifacts", 42, 45, "xstk-ch3-1-10-13-vang.json"),
    "doc-4": ("artifacts", 8, 11, "doc-4-chuong-8-vang.json"),
}


class RecordedModel:
    """Trả đúng phản hồi đã ghi theo băm đầu vào; đầu vào chưa ghi thì dừng (không bao giờ gọi mạng)."""

    def __init__(self, model_id, rows):
        self.model_id = model_id
        self.rows = {digest(row["input"]): row for row in rows}

    def start_session(self, system_prompt):
        return self

    def ask_json(self, prompt, *, response_schema):
        data = json.loads(prompt.split("\nCorrect this validation error:")[0])
        row = self.rows.get(digest(data))
        if row is None:
            raise AssertionError("đầu vào tên khái niệm chưa ghi: " + str(data.get("node_id")))
        return SimpleNamespace(payload=row.get("output", row.get("last_output", {})))


class MemoryStore(JsonArtifactStore):
    """Đọc artifact thật (kho chính khi kho đánh giá thiếu), ghi artifact mới vào bộ nhớ."""

    def __init__(self, root, start):
        super().__init__(Path(root))
        self.version, self.saved = start, {}
        self.fallback = JsonArtifactStore(Path("artifacts"))

    def find_graph(self, *args):
        return None

    def load_checkpoint(self, *args):
        return None

    def save_checkpoint(self, *args):
        pass

    def clear_checkpoint(self, *args):
        pass

    def save_graph(self, doc_id, source_hash, config_hash, config, payload, **kwargs):
        self.version += 1
        artifact = SimpleNamespace(payload=payload, version=self.version, path=None, manifest={
            "config": config, "config_hash": config_hash, "source_hash": source_hash,
            "upstream_version": kwargs.get("upstream_version"), **kwargs.get("manifest_fields", {})})
        self.saved[self.version] = artifact
        return artifact

    def load_graph(self, doc_id, version):
        # Kho đánh giá chỉ chứa chuỗi từ pass chính trở đi; số phiên bản thượng nguồn ghi trong payload (vd `node_vectors_version`)
        # trỏ về kho chính, như script phát lại v4-01. Artifact pass phụ, tên khái niệm, A10 gốc được đọc thẳng từ kho của chúng.
        if version in self.saved:
            return self.saved[version]
        if self.root == Path("artifacts") and (self.root / "graph" / doc_id / f"v{version}").exists():
            return super().load_graph(doc_id, version)
        return self.fallback.load_graph(doc_id, version)

    def load_chunks(self, doc_id, version):
        if (self.root / "chunks" / doc_id / f"v{version}").exists():
            return super().load_chunks(doc_id, version)
        return self.fallback.load_chunks(doc_id, version)

    def load_role_chunks(self, doc_id, version):
        if not (self.root / "chunks" / doc_id).exists():
            return self.fallback.load_role_chunks(doc_id, version)
        return super().load_role_chunks(doc_id, version)

    def load_canonical(self, doc_id, version):
        if (self.root / "canonical" / doc_id / f"v{version}").exists():
            return super().load_canonical(doc_id, version)
        return self.fallback.load_canonical(doc_id, version)


def replay(doc, secondary_edges, *, secondary=None):
    """Chạy A9 → tên khái niệm → A10 trên artifact pass phụ v3 với `secondary_edges` thay thế; trả payload A10 và artifact A10 gốc."""
    root, version, a10_version, _ = GOLD_DOCS[doc]
    original = JsonArtifactStore(Path(root))
    secondary = secondary or original.load_graph(doc, version)
    a10 = original.load_graph(doc, a10_version)
    labels = original.load_graph(doc, a10.manifest["upstream_version"])
    store = MemoryStore(root, 10_000)
    edges = sorted(secondary_edges, key=lambda e: (e["source"], e["target"], e.get("session_id", ""), e.get("operation_index", 0)))
    upstream = SimpleNamespace(payload={**secondary.payload, "secondary_edges": edges}, version=secondary.version,
                               manifest=secondary.manifest, path=None)
    validated, _ = ValidateGraph(store).execute(doc, upstream=upstream)
    model = RecordedModel(labels.manifest["config"]["model_id"], labels.payload.get("concept_display_name_decision_log", []))
    labeled, _ = NameConceptLabels(store, model, concurrency=1).execute(doc, upstream=validated)
    roadmap, _ = BuildRoadmap(store, stage_cap=a10.manifest["config"]["module_cap"]).execute(doc, upstream=labeled)
    return roadmap.payload, a10


def score_payload(doc, payload, out_root, label):
    """Ghi payload A10 vào kho tạm và chấm bằng đúng hàm chấm tập giữ lại."""
    folder = Path(out_root) / label / "graph" / doc / "v1"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "graph.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return score(doc, GOLD_DOCS[doc][3], Path(out_root) / label, 1)


def summary(result, payload, edge_count):
    def value(row):
        return None if row is None else round(row["value"], 3) if isinstance(row, dict) else round(row, 3)

    def interval(row):
        return [None if bound is None else round(bound, 3) for bound in row.get("wilson95", [None, None])]
    return {"canh_pass_phu": edge_count,
            "canh_cung_A10": sum(1 for e in payload["requires_edges"] if not e.get("soft")),
            "Q6": value(result["Q6_learning_order_error"]), "Q6_ro": result["Q6_buckets"],
            "Q7": value(result["Q7_mean_coverage"]), "Q7b": value(result["Q7b_mean_precision"]),
            "truc_tiep_P": value(result["edges_direct_reduced"]["precision"]), "truc_tiep_R": value(result["edges_direct_reduced"]["recall"]),
            "bao_dong_P": value(result["edges_closure_reduced"]["precision"]), "bao_dong_R": value(result["edges_closure_reduced"]["recall"]),
            "Q6_kt95": interval(result["Q6_learning_order_error"]),
            "bao_dong_P_kt95": interval(result["edges_closure_reduced"]["precision"]),
            "bao_dong_R_kt95": interval(result["edges_closure_reduced"]["recall"]),
            "bao_dong_dem": {"dung": result["edges_closure_reduced"]["precision"]["k"],
                             "du_doan": result["edges_closure_reduced"]["precision"]["n"],
                             "vang": result["edges_closure_reduced"]["recall"]["n"]}}


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    options = dict(arg[2:].split("=", 1) for arg in sys.argv[1:] if arg.startswith("--") and "=" in arg)
    doc, plan = [arg for arg in sys.argv[1:] if not arg.startswith("--")][:2]
    out = options.get("ra", "tmp/pass-phu-ml/e4")
    root, version, _, _ = GOLD_DOCS[doc]
    secondary = JsonArtifactStore(Path(root)).load_graph(doc, version)
    if plan == "llm-v3":
        edges = secondary.payload["secondary_edges"]
    elif plan == "khong":
        edges = []
    elif plan.startswith("tep:"):
        edges = json.loads(Path(plan[4:]).read_text(encoding="utf-8"))
    else:
        raise SystemExit("phương án phải là llm-v3, khong hoặc tep:<đường>")
    payload, a10 = replay(doc, edges, secondary=secondary)
    if plan == "llm-v3":
        for key in ("sequence", "requires_edges"):
            if payload[key] != a10.payload[key]:
                raise SystemExit(f"KIỂM CHỨNG HỎNG: {key} khác A10 v{a10.version} đã chấm — bộ phát lại không tái tạo được v3")
        print(f"kiểm chứng: sequence và requires_edges trùng A10 v{a10.version}")
    label = options.get("nhan", plan.replace(":", "-").replace("/", "_").replace("\\", "_"))
    result = summary(score_payload(doc, payload, out, label), payload, len(edges))
    print(json.dumps({"doc": doc, "phuong_an": label, **result}, ensure_ascii=False))


if __name__ == "__main__":
    main()
