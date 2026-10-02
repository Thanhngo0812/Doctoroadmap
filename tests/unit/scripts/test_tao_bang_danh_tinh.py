import importlib.util
import json
from pathlib import Path

import openpyxl


def test_gold_free_identity_sheet_reads_only_identity_artifact(tmp_path):
    path = Path("scripts/duyet-danh-tinh/tao_bang.py")
    spec = importlib.util.spec_from_file_location("tao_bang_danh_tinh", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    graph = tmp_path / "input" / "graph" / "doc" / "v2" / "graph.json"
    graph.parent.mkdir(parents=True)
    graph.write_text(json.dumps({"stage": "identity", "nodes": [
        {"node_id": "a", "name": "A"}, {"node_id": "b", "name": "B"},
        {"node_id": "c", "name": "C"}], "merged_nodes": [], "identity_log": [
        {"pair_id": "ab", "left": "a", "right": "b", "verdict": "same", "reason": "alias"},
        {"pair_id": "ac", "left": "a", "right": "c", "verdict": "sense_split", "reason": "two senses"},
        {"pair_id": "bc", "left": "b", "right": "c", "verdict": "different", "reason": "other"},
    ]}), encoding="utf-8")
    out = tmp_path / "out"
    module.main(["doc", "2", "--no-gold", "--artifact-dir", str(tmp_path / "input"),
                 "--output-dir", str(out)])
    workbook = openpyxl.load_workbook(out / "duyet-danh-tinh-doc.xlsx")
    assert [row[7] for row in list(workbook["Cặp"].values)[1:]] == ["Gộp", "Giữ tách — hai nghĩa"]
    assert len(json.loads((out / "duyet-danh-tinh-doc-khoa.json").read_text(encoding="utf-8"))["items"]) == 2
