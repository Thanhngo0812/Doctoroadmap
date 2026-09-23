import hashlib
import json
from types import SimpleNamespace

import pytest

from doc2roadmap.application.use_cases.a8_gold import scope_from_store
from doc2roadmap.application.use_cases.a8_score import load_gold, merge_gold, score_from_store, score_roadmap_order


def section(section_id, title, level, parent, order):
    return {"section_id": section_id, "title": title, "level": level, "parent_section_id": parent,
            "order_index": order}


SECTIONS = [
    section("root", "<document>", 0, None, -1),
    section("ch1", "Chương 1. Xác suất", 1, "root", 1),
    section("s11", "1.1 Biến cố", 2, "ch1", 2),
    section("ch2", "Chương 2. Thống kê", 1, "root", 3),
    section("s21", "2.1 Mẫu", 2, "ch2", 4),
    section("s22", "2.2 Ước lượng", 2, "ch2", 5),
]

CHUNKS = [
    {"chunk_id": "c1", "parent_section_id": "s11", "section_path": ["Chương 1. Xác suất", "1.1 Biến cố"],
     "page": 3, "order_index": 1},
    {"chunk_id": "c2", "parent_section_id": "s21", "section_path": ["Chương 2. Thống kê", "2.1 Mẫu"],
     "page": 10, "order_index": 2},
    {"chunk_id": "c3", "parent_section_id": "s22", "section_path": ["Chương 2. Thống kê", "2.2 Ước lượng"],
     "page": 12, "order_index": 3},
]


def node(node_id, name, defining, *, learnable=True, cluster="g1"):
    return {"node_id": node_id, "name": name, "defining_chunk_ids": list(defining), "learnable": learnable,
            "node_type": "concept", "aliases": [], "first_order_index": 0, "cluster_id": cluster}


NODES = [
    node("n_bienco", "Biến cố", ["c1"], cluster="g1"),
    node("n_mau", "Mẫu", ["c2"], cluster="g2"),
    node("n_uocluong", "Ước lượng điểm", ["c3"], cluster="g2"),
    node("n_khoang", "Khoảng tin cậy", ["c3"], cluster="g2"),
    node("n_hinh", "Hình 2.1", ["c3"], learnable=False, cluster="g2"),
]


class FakeStore:
    def load_latest_canonical(self, doc_id):
        return SimpleNamespace(payload={"stage": "complete", "nodes": NODES, "edges": []}, version=7,
                               manifest={"upstream_version": 5})

    def load_canonical(self, doc_id, version):
        assert version == 7
        return self.load_latest_canonical(doc_id)

    def load_candidates(self, doc_id, version):
        return SimpleNamespace(manifest={"upstream_version": 2})

    def load_chunks(self, doc_id, version):
        return SimpleNamespace(result=SimpleNamespace(
            sections=[SimpleNamespace(**value) for value in SECTIONS],
            chunks=[SimpleNamespace(**value) for value in CHUNKS],
        ))


def hard(*node_ids):
    return {node_id: {"channels": ["exact"], "level": "mention"} for node_id in node_ids}


def graph_payload(**extra):
    return {
        "stage": "mentions",
        "doc_id": "xstk",
        "nodes": NODES,
        "mention_map": {
            "c1": hard("n_bienco"),
            "c2": hard("n_mau", "n_bienco"),
            "c3": hard("n_uocluong", "n_khoang", "n_mau"),
        },
        "suspected_pairs": [
            {"pair_id": "p1", "left": "n_mau", "right": "n_uocluong", "sources": ["same_section", "citation_hard"]},
            {"pair_id": "p2", "left": "n_uocluong", "right": "n_khoang", "sources": ["same_section"]},
            {"pair_id": "p3", "left": "n_bienco", "right": "n_mau", "sources": ["contact"]},
        ],
        **extra,
    }


def write_graph(tmp_path, payload, name="graph.json"):
    path = tmp_path / name
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def write_gold(tmp_path, edges, *, annotator="A1", concept_hash=None, name=None):
    scope = scope_from_store(FakeStore(), "xstk", chapter=2)
    value = {
        "schema": scope["schema"],
        "doc_id": "xstk",
        "canonical_version": 7,
        "chapter_level": 1,
        "chapter": scope["chapter"],
        "concept_hash": concept_hash or scope["concept_hash"],
        "annotator": annotator,
        "targets": [c["node_id"] for c in scope["concepts"] if c["in_scope"]],
        "edges": [{"target": target, "prerequisite": prerequisite, "evidence_kind": "noi_ro",
                   "strength": "manh", "location": "", "note": "", "row": index + 2}
                  for index, (prerequisite, target) in enumerate(sorted(edges))],
        "flags": [],
        "timing": {"annotation_minutes": 30, "revision_minutes": 5},
        "errors": [],
        "warnings": [],
    }
    path = tmp_path / (name or f"gold-{annotator}.json")
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return path


def test_report_covers_e1_positions_nmi_and_e2_generators(tmp_path):
    gold = write_gold(tmp_path, {("n_mau", "n_uocluong"), ("n_uocluong", "n_khoang"), ("n_bienco", "n_mau")})
    report = score_from_store(FakeStore(), "xstk", write_graph(tmp_path, graph_payload()), [gold], samples=50)

    assert report["gold"]["edges"] == 3 and report["gold"]["targets"] == 3
    positions = {row["position"]: row["count"] for row in report["e1"]["positions"]}
    # n_uocluong và n_khoang cùng chunk c3; n_mau với n_uocluong cùng chương 2; n_bienco ở chương 1 nhưng
    # chunk c2 nhắc cả n_bienco lẫn n_mau bằng kênh cứng.
    assert positions == {"same_chunk": 1, "same_section": 0, "same_chapter": 1, "same_cluster": 0,
                         "bridge_hard": 1, "bridge_soft": 0, "implicit": 0}
    assert sum(row["count"] for row in report["e1"]["positions"]) == 3
    assert report["e1"]["nmi_cluster_chapter"] == pytest.approx(1.0)

    generators = {row["generator"]: row for row in report["e2"]["generators"]}
    assert generators["same_section"]["recall"] == pytest.approx(2 / 3)
    assert generators["contact"]["unique_gold_covered"] == 1
    assert generators["citation_hard"]["unique_gold_covered"] == 0
    assert {row["configuration"] for row in report["e2"]["routing"]} == {
        "chapter_axis", "cluster_axis", "both_axes", "generators_union",
        "chapter_axis_plus_generators", "both_axes_plus_generators",
    }
    routing = {row["configuration"]: row for row in report["e2"]["routing"]}
    assert routing["both_axes_plus_generators"]["recall"] == 1.0
    # Đếm tay: trục chương cho 4 cặp (mục 2.1 ghép Mẫu với Biến cố; mục 2.2 ghép ba khái niệm),
    # trục cụm cho 6 cặp (cụm g2 kéo theo Biến cố qua mention), bộ sinh cho 3 cặp.
    assert routing["chapter_axis"]["pairs"] == 4
    assert routing["cluster_axis"]["pairs"] == 6
    assert routing["both_axes"]["pairs"] == 6
    assert routing["generators_union"]["pairs"] == 3
    # Cả ba cặp vàng đều nằm trong một phiên của trục chương, nên trục chương phủ hết.
    assert routing["chapter_axis"]["gold_covered"] == 3 and routing["chapter_axis"]["recall"] == 1.0
    for row in report["e1"]["positions"] + report["e2"]["generators"]:
        assert row["interval"]["unit_count"] == 3


def test_scoring_refuses_a_gold_file_made_for_another_concept_list(tmp_path):
    gold = write_gold(tmp_path, {("n_mau", "n_uocluong")}, concept_hash="deadbeef" * 8)
    with pytest.raises(ValueError, match="sinh lại file gán|phiên bản"):
        score_from_store(FakeStore(), "xstk", write_graph(tmp_path, graph_payload()), [gold], samples=10)


def test_gold_file_with_errors_is_never_scored(tmp_path):
    path = tmp_path / "gold.json"
    path.write_text(json.dumps({"doc_id": "xstk", "errors": ["dòng 5: khái niệm lạ"]}), encoding="utf-8")
    with pytest.raises(ValueError, match="còn lỗi chưa sửa"):
        load_gold(path)


def test_two_annotators_are_merged_and_agreement_counts_paths(tmp_path):
    first = write_gold(tmp_path, {("n_mau", "n_uocluong"), ("n_uocluong", "n_khoang")}, annotator="A1")
    second = write_gold(tmp_path, {("n_mau", "n_uocluong"), ("n_mau", "n_khoang")}, annotator="A2")
    golds = [load_gold(first), load_gold(second)]

    assert len(merge_gold(golds, mode="union")) == 3
    assert len(merge_gold(golds, mode="intersection")) == 1

    graph = write_graph(tmp_path, graph_payload())
    union = score_from_store(FakeStore(), "xstk", graph, [first, second], mode="union", samples=20)
    intersection = score_from_store(FakeStore(), "xstk", graph, [first, second], mode="intersection", samples=20)
    assert union["gold"]["edges"] == 3 and intersection["gold"]["edges"] == 1
    assert union["gold"]["annotators"] == ["A1", "A2"]

    direct = union["gold"]["agreement"]["direct"]
    implicit = union["gold"]["agreement"]["transitive"]
    # A1 ghi n_mau → n_uocluong → n_khoang, A2 ghi thẳng n_mau → n_khoang: đồng thuận ngầm qua bắc cầu.
    assert direct["both"] == 1 and implicit["both"] == 2
    assert implicit["kappa"] > direct["kappa"]


def test_prediction_section_scores_direct_and_closure_when_artifact_has_edges(tmp_path):
    gold = write_gold(tmp_path, {("n_mau", "n_uocluong"), ("n_uocluong", "n_khoang")})
    edges = [
        {"source": "n_mau", "target": "n_uocluong", "edge_type": "requires"},
        {"source": "n_mau", "target": "n_khoang", "edge_type": "requires"},
        {"source": "n_hinh", "target": "n_khoang", "edge_type": "requires"},
        {"source": "n_bienco", "target": "n_uocluong", "edge_type": "estimator_of"},
    ]
    payload = graph_payload(stage="validated", requires_edges=edges)
    report = score_from_store(FakeStore(), "xstk", write_graph(tmp_path, payload), [gold], samples=50)

    prediction = report["prediction"]
    # Cạnh từ node không học được và cạnh kiểu mở đều bị loại, chỉ còn hai cạnh `requires`.
    assert prediction["edges"] == 2
    assert prediction["direct"]["true_positive"] == 1
    assert prediction["direct"]["precision"] == pytest.approx(0.5)
    assert prediction["direct"]["recall"] == pytest.approx(0.5)
    # Bao đóng của vàng có thêm n_mau → n_khoang, nên dự đoán thành đúng cả hai cạnh.
    assert prediction["closure"]["precision"] == 1.0
    assert prediction["closure"]["recall"] == pytest.approx(2 / 3)
    assert prediction["direct"]["intervals"]["f1"]["unit_count"] == 3


def test_gold_edges_pointing_outside_the_annotated_chapter_are_dropped(tmp_path):
    # n_bienco được dạy ở chương 1, không nằm trong phạm vi đích của chương 2.
    gold = write_gold(tmp_path, {("n_mau", "n_uocluong"), ("n_mau", "n_bienco")})
    report = score_from_store(FakeStore(), "xstk", write_graph(tmp_path, graph_payload()), [gold], samples=10)

    assert report["gold"]["edges"] == 1
    assert sum(row["count"] for row in report["e1"]["positions"]) == 1


def test_bootstrap_can_be_switched_off_and_report_stays_deterministic(tmp_path):
    gold = write_gold(tmp_path, {("n_mau", "n_uocluong")})
    graph = write_graph(tmp_path, graph_payload())
    without = score_from_store(FakeStore(), "xstk", graph, [gold], samples=0)
    assert without["e1"]["positions"][0]["interval"]["samples"] == 0
    assert score_from_store(FakeStore(), "xstk", graph, [gold], samples=30) == score_from_store(
        FakeStore(), "xstk", graph, [gold], samples=30)


def test_gold_made_from_patched_provenance_is_scoreable(tmp_path):
    # D13 bắt cột "Nơi dạy" lấy từ stage provenance, nên mọi bảng gán thật đều sinh có --graph. Bộ chấm phải
    # dựng scope từ **cùng** payload ấy, nếu không nó tự từ chối mọi bộ vàng thật (F124).
    patched = graph_payload(nodes=[
        {**value, "defining_chunk_ids": ["c3", "c2"]} if value["node_id"] == "n_khoang" else value
        for value in NODES
    ])
    scope = scope_from_store(FakeStore(), "xstk", chapter=2, graph_payload=patched)
    assert scope["concept_hash"] != scope_from_store(FakeStore(), "xstk", chapter=2)["concept_hash"]

    gold = write_gold(tmp_path, {("n_mau", "n_uocluong")}, concept_hash=scope["concept_hash"])
    report = score_from_store(FakeStore(), "xstk", write_graph(tmp_path, patched), [gold], samples=0)
    assert report["gold"]["edges"] == 1


def staged_payload(stages, *, doc_id="xstk", nodes=NODES):
    return {"stage": "stages", "doc_id": doc_id, "nodes": [value for value in nodes if value["learnable"]],
            "stages": [{"stage_id": f"s{index}", "node_ids": list(members)} for index, members in enumerate(stages)]}


def test_roadmap_order_refuses_a_gold_made_for_another_document(tmp_path):
    gold = write_gold(tmp_path, {("n_mau", "n_uocluong")})
    graph = write_graph(tmp_path, staged_payload([["n_mau"], ["n_uocluong"]], doc_id="doc-khac"))
    with pytest.raises(ValueError, match="doc_id"):
        score_roadmap_order(graph, [gold])


def test_roadmap_order_refuses_golds_of_two_canonical_versions(tmp_path):
    first = write_gold(tmp_path, {("n_mau", "n_uocluong")}, annotator="A1")
    second = write_gold(tmp_path, {("n_mau", "n_uocluong")}, annotator="A2")
    value = json.loads(second.read_text(encoding="utf-8"))
    second.write_text(json.dumps({**value, "canonical_version": 8}, ensure_ascii=False), encoding="utf-8")
    graph = write_graph(tmp_path, staged_payload([["n_mau"], ["n_uocluong"]]))
    with pytest.raises(ValueError, match="canonical"):
        score_roadmap_order(graph, [first, second])


def test_roadmap_order_refuses_a_gold_whose_concepts_the_graph_does_not_have(tmp_path):
    # Khác danh tính thì không có điểm nào để trả: điểm "đạt" trên khái niệm không tồn tại là điểm giả.
    gold = write_gold(tmp_path, {("n_mau", "n_uocluong")})
    nodes = [value for value in NODES if value["node_id"] != "n_mau"]
    graph = write_graph(tmp_path, staged_payload([["n_uocluong"]], nodes=nodes))
    with pytest.raises(ValueError, match="không có trong đồ thị"):
        score_roadmap_order(graph, [gold])


def test_roadmap_order_counts_a_concept_left_out_of_the_stages_and_pins_its_inputs(tmp_path):
    # Node có trong đồ thị mà không lên lộ trình là lỗi của lộ trình, không được làm mẫu số nhỏ đi.
    gold = write_gold(tmp_path, {("n_mau", "n_uocluong"), ("n_uocluong", "n_khoang")})
    graph = write_graph(tmp_path, staged_payload([["n_mau"], ["n_uocluong"]]))
    report = score_roadmap_order(graph, [gold])
    assert report["gold_order"]["out_of_scope"] == 1
    assert report["gold_order"]["learning_order_error"] == pytest.approx(1 / 2)
    assert report["inputs"]["graph"]["sha256"] == hashlib.sha256(graph.read_bytes()).hexdigest()
    assert [row["sha256"] for row in report["inputs"]["golds"]] == [hashlib.sha256(gold.read_bytes()).hexdigest()]
