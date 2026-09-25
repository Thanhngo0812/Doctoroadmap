import math

import pytest

from doc2roadmap.domain.gold_scoring import (
    agreement,
    bootstrap_interval,
    classify_positions,
    coverage_rows,
    generator_rows,
    index_stream,
    gold_order_violations,
    metric_by_target,
    presentation_agreement,
    normalized_mutual_information,
    pairs_within,
    position_counts,
    recall_by_target,
    score_edges,
    share_by_target,
    subset_rows,
    transitive_closure,
    undirected,
)


def hard(*node_ids):
    return {node_id: {"channels": ["exact"]} for node_id in node_ids}


# Tài liệu dựng tay: hai chương, hai cụm, sáu khái niệm.
#   c1 (mục s1, chương ch1): a, b     c2 (mục s2, chương ch1): c
#   c3 (mục s3, chương ch2): d        c4 (mục s4, chương ch2): e, và nhắc cả a
#   c5 (mục s5, chương ch2): f
CONTEXT = {
    "provenance": {"a": ["c1"], "b": ["c1"], "c": ["c2"], "d": ["c3"], "e": ["c4"], "f": ["c5"]},
    "section_of_chunk": {"c1": "s1", "c2": "s2", "c3": "s3", "c4": "s4", "c5": "s5"},
    "chapter_of_chunk": {"c1": "ch1", "c2": "ch1", "c3": "ch2", "c4": "ch2", "c5": "ch2"},
    "cluster_of_node": {"a": "g1", "b": "g1", "c": "g1", "d": "g2", "e": "g2", "f": "g3"},
    "mention_map": {
        "c1": hard("a", "b"),
        "c2": hard("c"),
        "c3": hard("d"),
        "c4": {**hard("e"), "a": {"channels": ["exact"]}},
        "c5": {**hard("f"), "d": {"channels": ["dense"]}},
    },
}


def test_six_position_classes_match_hand_computed_document():
    edges = {
        ("a", "b"),  # cùng chunk c1
        ("b", "c"),  # khác chunk, cùng chương ch1 (khác mục)
        ("d", "e"),  # khác chương? không: d ở ch2, e ở ch2 → cùng chương
        ("c", "d"),  # ch1 với ch2, khác cụm, không chunk nào nhắc cả hai → ngầm
        ("a", "e"),  # khác chương, khác cụm, nhưng c4 nhắc cả a lẫn e bằng kênh cứng
        ("d", "f"),  # khác chương? cùng ch2 → cùng chương
    }
    rows = classify_positions(edges, **CONTEXT)
    by_pair = {(row["prerequisite"], row["target"]): row["position"] for row in rows}

    assert by_pair == {
        ("a", "b"): "same_chunk",
        ("b", "c"): "same_chapter",
        ("d", "e"): "same_chapter",
        ("c", "d"): "implicit",
        ("a", "e"): "bridge_hard",
        ("d", "f"): "same_chapter",
    }
    counts = position_counts(rows)
    assert counts["same_chunk"] == 1 and counts["same_chapter"] == 3
    assert counts["bridge_hard"] == 1 and counts["implicit"] == 1
    assert sum(counts.values()) == len(edges)


def test_same_section_and_cluster_and_soft_bridge_are_separated():
    context = {
        **CONTEXT,
        "provenance": {**CONTEXT["provenance"], "b": ["c2"]},  # a ở mục s1, b sang mục s2 nhưng cùng chương
    }
    assert classify_positions({("a", "b")}, **context)[0]["position"] == "same_chapter"

    # cùng mục: hai chunk khác nhau nhưng cùng section
    context = {**CONTEXT, "section_of_chunk": {**CONTEXT["section_of_chunk"], "c2": "s1"},
               "provenance": {**CONTEXT["provenance"], "b": ["c2"]}}
    assert classify_positions({("a", "b")}, **context)[0]["position"] == "same_section"

    # cùng cụm: hai chương khác nhau nhưng cùng cluster_id
    context = {**CONTEXT, "cluster_of_node": {**CONTEXT["cluster_of_node"], "d": "g1"}}
    assert classify_positions({("c", "d")}, **context)[0]["position"] == "same_cluster"

    # bắc cầu mềm: chunk c5 nhắc d chỉ bằng kênh dense
    assert classify_positions({("d", "f")}, **{**CONTEXT,
                                               "chapter_of_chunk": {**CONTEXT["chapter_of_chunk"], "c5": "ch3"},
                                               "cluster_of_node": {**CONTEXT["cluster_of_node"], "f": "g9"}})[0][
        "position"] == "bridge_soft"


def test_closure_scoring_counts_paths_that_direct_scoring_misses():
    gold = {("a", "b"), ("b", "c")}
    predicted = {("a", "b"), ("b", "c"), ("a", "c")}

    direct = score_edges(predicted, gold, targets=["b", "c"])
    assert direct["true_positive"] == 2 and direct["false_positive"] == 1
    assert direct["precision"] == pytest.approx(2 / 3) and direct["recall"] == 1.0
    # F1 là trung bình điều hoà: 0,8 chứ không phải trung bình cộng 0,833.
    assert direct["f1"] == pytest.approx(0.8)

    closed = score_edges(predicted, gold, targets=["b", "c"], closure=True)
    assert closed["precision"] == 1.0 and closed["recall"] == 1.0 and closed["f1"] == 1.0
    assert transitive_closure(gold) == {("a", "b"), ("b", "c"), ("a", "c")}


def test_scoring_ignores_predictions_outside_the_annotated_targets():
    gold = {("a", "b")}
    predicted = {("a", "b"), ("a", "z")}

    assert score_edges(predicted, gold, targets=["b"])["false_positive"] == 0
    assert score_edges(predicted, gold)["false_positive"] == 1


def test_generator_rows_report_recall_and_the_part_only_one_generator_has():
    gold_pairs = undirected({("a", "b"), ("c", "d"), ("a", "e")})
    sources = {
        frozenset(("a", "b")): {"same_section", "citation_hard"},
        frozenset(("c", "d")): {"citation_hard"},
        frozenset(("a", "e")): {"contact"},
        frozenset(("b", "f")): {"same_section"},
    }
    rows = {row["generator"]: row for row in generator_rows(gold_pairs, sources)}

    assert rows["citation_hard"]["pairs"] == 2
    assert rows["citation_hard"]["recall"] == pytest.approx(2 / 3)
    assert rows["citation_hard"]["unique_gold_covered"] == 1  # chỉ cặp (c, d)
    assert rows["same_section"]["unique_gold_covered"] == 0  # (a, b) đã được citation_hard phủ
    assert rows["contact"]["unique_recall"] == pytest.approx(1 / 3)

    subsets = {tuple(row["generators"]): row for row in subset_rows(gold_pairs, sources)}
    assert subsets[("citation_hard", "contact")]["recall" ] == 1.0
    assert subsets[("citation_hard", "contact")]["pairs"] == 3
    assert subsets[("same_section",)]["pairs"] == 2 and subsets[("same_section",)]["gold_covered"] == 1


def test_routing_coverage_uses_pairs_inside_each_axis():
    groups = [{"a", "b", "c"}, {"d", "e"}]
    assert pairs_within(groups) == {
        frozenset(("a", "b")), frozenset(("a", "c")), frozenset(("b", "c")), frozenset(("d", "e")),
    }
    gold_pairs = undirected({("a", "b"), ("d", "e"), ("a", "e")})
    rows = {row["configuration"]: row for row in coverage_rows(gold_pairs, {"axis": pairs_within(groups)})}
    assert rows["axis"]["gold_covered"] == 2 and rows["axis"]["recall"] == pytest.approx(2 / 3)


def test_nmi_is_one_for_identical_partitions_and_zero_for_independent_ones():
    left = {"a": "x", "b": "x", "c": "y", "d": "y"}
    same = {"a": "1", "b": "1", "c": "2", "d": "2"}
    crossed = {"a": "1", "b": "2", "c": "1", "d": "2"}

    assert normalized_mutual_information(left, same) == pytest.approx(1.0)
    assert normalized_mutual_information(left, crossed) == pytest.approx(0.0, abs=1e-12)
    assert normalized_mutual_information(left, {"z": "1"}) is None


def test_kappa_matches_a_hand_computed_table():
    # Không gian ứng viên: hai đích c, d × bốn khái niệm, bỏ cặp tự nối → 6 cặp.
    # Người 1 ghi (a→c) và (b→d); người 2 ghi (a→c) và (a→d): cùng 1, lệch 2, cùng không 3.
    # po = 4/6; mỗi người khẳng định 2/6 → pe = (1/3)² + (2/3)² = 5/9; κ = (2/3 − 5/9) / (4/9) = 0,25.
    result = agreement({("a", "c"), ("b", "d")}, {("a", "c"), ("a", "d")},
                       targets=["c", "d"], concepts=["a", "b", "c", "d"])

    assert result["candidate_pairs"] == 6
    assert (result["both"], result["only_first"], result["only_second"], result["neither"]) == (1, 1, 1, 3)
    assert result["observed"] == pytest.approx(4 / 6)
    assert result["expected"] == pytest.approx(5 / 9)
    assert result["kappa"] == pytest.approx(0.25)


def test_agreement_counts_implicit_agreement_through_a_path():
    first = {("a", "c")}                 # người 1: a cần trước c
    second = {("a", "b"), ("b", "c")}    # người 2: đi đường vòng qua b
    targets, concepts = ["b", "c"], ["a", "b", "c"]

    direct = agreement(first, second, targets=targets, concepts=concepts)
    assert direct["both"] == 0 and direct["only_first"] == 1 and direct["only_second"] == 2

    implicit = agreement(first, second, targets=targets, concepts=concepts, transitive=True)
    assert implicit["both"] == 1  # (a, c) nay được cả hai khẳng định
    assert implicit["kappa"] > direct["kappa"]


def test_bootstrap_resamples_target_concepts_not_edges():
    # Hai khái niệm đích: t1 có 3 cạnh cùng loại, t2 có 1 cạnh loại khác.
    rows = [
        {"prerequisite": "p1", "target": "t1", "position": "same_chunk"},
        {"prerequisite": "p2", "target": "t1", "position": "same_chunk"},
        {"prerequisite": "p3", "target": "t1", "position": "same_chunk"},
        {"prerequisite": "p4", "target": "t2", "position": "implicit"},
    ]
    statistic = share_by_target(rows, "same_chunk", ["t1", "t2"])
    assert statistic(("t1", "t2")) == pytest.approx(0.75)
    # Lấy mẫu theo khái niệm đích: chỉ có ba kết quả có thể, 0, 0,75 và 1.
    assert {statistic(("t1", "t1")), statistic(("t2", "t2")), statistic(("t1", "t2"))} == {1.0, 0.0, 0.75}

    interval = bootstrap_interval(["t1", "t2"], statistic, samples=200, seed=7)
    assert interval["point"] == pytest.approx(0.75)
    assert interval["low"] == 0.0 and interval["high"] == 1.0
    assert interval["unit_count"] == 2

    # Cùng seed thì ra cùng khoảng; đơn vị lấy mẫu là khái niệm đích nên khoảng rất rộng với hai đích.
    assert bootstrap_interval(["t1", "t2"], statistic, samples=200, seed=7) == interval


def test_bootstrap_is_deterministic_and_matches_hand_case_for_recall():
    gold = {("p1", "t1"), ("p2", "t1"), ("p3", "t2")}
    covered = {frozenset(("p1", "t1"))}
    statistic = recall_by_target(gold, covered)

    assert statistic(("t1",)) == pytest.approx(0.5)
    assert statistic(("t2",)) == 0.0
    assert statistic(("t1", "t2")) == pytest.approx(1 / 3)

    f1 = metric_by_target({("p1", "t1")}, gold, metric="f1")
    assert f1(("t1",)) == pytest.approx(2 * 1.0 * 0.5 / 1.5)
    assert f1(("t2",)) is None  # không dự đoán gì cho t2 nên F1 không xác định
    precision = metric_by_target({("p1", "t1"), ("p9", "t1")}, gold, metric="precision")
    assert precision(("t1", "t1")) == pytest.approx(0.5)


def test_sampling_stream_is_pinned_so_intervals_reproduce_on_any_machine():
    # Dòng lấy mẫu là một phần của con số báo cáo, nên ghim lại như một hash vàng.
    assert index_stream(20260918, 8, 5) == [3, 4, 4, 3, 2, 0, 3, 0]
    assert index_stream(20260918, 4, 5) == index_stream(20260918, 8, 5)[:4]
    assert index_stream(7, 8, 5) != index_stream(20260918, 8, 5)
    assert set(index_stream(1, 400, 3)) == {0, 1, 2}


def test_closure_metric_by_target_uses_closed_edges():
    gold = {("a", "b"), ("b", "c")}
    predicted = {("a", "b"), ("b", "c")}
    closed = metric_by_target(predicted, gold, metric="recall", closure=True)
    # Bao đóng thêm (a, c) vào cả hai phía, nên recall theo đích c vẫn 1,0 và đích c có hai cạnh.
    assert closed(("c",)) == pytest.approx(1.0)
    assert math.isclose(closed(("b", "c")), 1.0)


def test_presentation_agreement_is_one_when_the_roadmap_follows_the_book():
    stages = [["a"], ["b"], ["c"]]
    book = {"a": 10, "b": 20, "c": 30}
    result = presentation_agreement(stages, book)
    assert result["tau"] == pytest.approx(1.0)
    assert (result["concordant"], result["discordant"]) == (3, 0)


def test_presentation_agreement_is_minus_one_when_the_roadmap_reverses_the_book():
    result = presentation_agreement([["c"], ["b"], ["a"]], {"a": 10, "b": 20, "c": 30})
    assert result["tau"] == pytest.approx(-1.0)
    assert (result["concordant"], result["discordant"]) == (0, 3)


def test_presentation_agreement_drops_ties_from_the_ratio_but_still_reports_them():
    # Hai khái niệm cùng stage không được lộ trình xếp thứ tự; hai khái niệm cùng vị trí sách thì
    # sách không xếp thứ tự. Cả hai loại phải ra khỏi mẫu số, nhưng phải đếm được.
    stages = [["a", "b"], ["c"]]
    book = {"a": 10, "b": 10, "c": 30}
    result = presentation_agreement(stages, book)
    assert result["comparable_pairs"] == 2  # chỉ (a,c) và (b,c)
    assert result["same_stage_pairs"] == 1
    assert result["same_position_pairs"] == 1
    assert result["tau"] == pytest.approx(1.0)


def test_presentation_agreement_has_no_tau_when_nothing_is_comparable():
    result = presentation_agreement([["a", "b"]], {"a": 10, "b": 20})
    assert result["comparable_pairs"] == 0
    assert result["tau"] is None


def test_gold_violations_are_empty_when_the_roadmap_respects_every_gold_edge():
    stages = [["p"], ["t"]]
    result = gold_order_violations(stages, {("p", "t")})
    assert result["violated"] == 0 and result["respected"] == 1
    assert result["rate"] == pytest.approx(0.0)
    assert result["rows"] == []


def test_gold_violations_name_the_exact_reversed_pair():
    stages = [["t"], ["p"]]
    result = gold_order_violations(stages, {("p", "t")}, names={"p": "Phân phối chuẩn", "t": "Độ tin cậy"})
    assert result["violated"] == 1 and result["rate"] == pytest.approx(1.0)
    assert result["rows"] == [{
        "prerequisite": "p", "target": "t",
        "prerequisite_name": "Phân phối chuẩn", "target_name": "Độ tin cậy",
        "prerequisite_stage": 1, "target_stage": 0, "bucket": "violated",
    }]


def test_gold_edge_inside_one_stage_is_its_own_bucket_not_a_silent_pass():
    # Cùng stage nghĩa là lộ trình không xếp thứ tự cho cặp ấy — không phải tôn trọng, cũng không phải vi phạm.
    result = gold_order_violations([["p", "t"]], {("p", "t")})
    assert (result["respected"], result["violated"], result["same_stage"]) == (0, 0, 1)
    assert result["rate"] is None  # không có cặp nào xếp được thứ tự thì tỉ lệ không xác định


def test_gold_edge_outside_the_staged_concepts_is_reported_not_dropped():
    result = gold_order_violations([["p"], ["t"]], {("p", "t"), ("p", "ngoai"), ("x", "t")})
    assert result["out_of_scope"] == 2
    assert result["respected"] == 1
    assert result["rate"] == pytest.approx(0.0)  # tỉ lệ chỉ tính trên cặp nằm trong phạm vi


def test_learning_order_error_counts_every_gold_edge_not_learned_strictly_before():
    # Stage là tập học song song: cùng stage chưa bảo đảm học tiên quyết trước, và đầu cạnh vắng mặt khỏi lộ
    # trình cũng là lỗi. Mẫu số là **toàn bộ** bộ vàng, để bỏ node khỏi output không làm điểm đẹp lên.
    stages = [["p"], ["t", "u"]]
    gold = {("p", "t"), ("t", "u"), ("u", "p"), ("p", "vang_mat")}
    result = gold_order_violations(stages, gold)
    assert (result["respected"], result["violated"], result["same_stage"], result["out_of_scope"]) == (1, 1, 1, 1)
    assert result["learning_order_error"] == pytest.approx(3 / 4)
    assert result["rate"] == pytest.approx(1 / 2)  # chỉ số lịch sử, giữ để so với số đã báo trước đây
    assert sorted((row["bucket"], row["prerequisite"], row["target"]) for row in result["rows"]) == [
        ("out_of_scope", "p", "vang_mat"), ("same_stage", "t", "u"), ("violated", "u", "p"),
    ]


def test_learning_order_error_is_undefined_for_an_empty_gold_not_a_pass():
    assert gold_order_violations([["p"], ["t"]], set())["learning_order_error"] is None


def test_blind_review_reads_each_answer_against_the_machine_direction_whatever_order_the_pair_was_shown():
    from doc2roadmap.domain.gold_scoring import blind_review_counts

    items = [
        # Cặp hiện theo đúng chiều máy (X = tiên quyết của máy).
        {"item": 1, "category": "fp", "x": "a", "y": "b", "machine": ["a", "b"]},
        # Cặp hiện đảo chiều: "Y trước X" mới là đồng ý với máy.
        {"item": 2, "category": "fp", "x": "d", "y": "c", "machine": ["c", "d"]},
        {"item": 3, "category": "fp", "x": "e", "y": "f", "machine": ["e", "f"]},
        {"item": 4, "category": "tp", "x": "h", "y": "g", "machine": ["g", "h"]},
        # Cặp ngẫu nhiên không có cạnh máy: chỉ hỏi có thứ tự học hay không.
        {"item": 5, "category": "random", "x": "p", "y": "q", "machine": None},
        {"item": 6, "category": "random", "x": "r", "y": "s", "machine": None},
        {"item": 7, "category": "fp", "x": "u", "y": "v", "machine": ["u", "v"]},
    ]
    answers = {1: "x_truoc_y_truc_tiep", 2: "y_truoc_x_gian_tiep", 3: "y_truoc_x_truc_tiep",
               4: "y_truoc_x_truc_tiep", 5: "y_truoc_x_truc_tiep", 6: "khong_can_thu_tu", 7: "khong_chac"}
    counts = blind_review_counts(items, answers)
    assert counts["fp"] == {"agree_direct": 1, "agree_indirect": 1, "reversed": 1, "none": 0, "unsure": 1,
                            "unanswered": 0}
    assert counts["tp"]["agree_direct"] == 1
    assert counts["random"] == {"ordered": 1, "none": 1, "unsure": 0, "unanswered": 0}


def test_blind_review_refuses_an_answer_outside_the_six_choices():
    from doc2roadmap.domain.gold_scoring import blind_review_counts

    with pytest.raises(ValueError, match="ngoài sáu lựa chọn"):
        blind_review_counts([{"item": 1, "category": "fp", "x": "a", "y": "b", "machine": ["a", "b"]}], {1: "co"})


def test_target_coverage_counts_how_much_of_what_a_target_needs_the_machine_graph_brings_along():
    from doc2roadmap.domain.gold_scoring import target_coverage

    # Vàng: a → b → t và c → t. Máy có a → b → t nhưng thiếu c → t.
    gold = {("a", "b"), ("b", "t"), ("c", "t")}
    machine = {("a", "b"), ("b", "t"), ("x", "t")}
    result = target_coverage(gold, machine, ["t", "b", "a"])
    # t cần {a, b, c}, máy mang theo {a, b} → 2/3; b cần {a}, máy có → 1/1; a không cần gì nên không tính.
    assert result["targets"] == 2
    assert result["complete"] == 1
    assert result["mean_coverage"] == pytest.approx((2 / 3 + 1) / 2)
    assert result["median_machine_ancestors"] == pytest.approx((3 + 1) / 2)  # t: {a, b, x}; b: {a}


def test_target_precision_q7b_counts_how_much_of_what_the_machine_makes_a_target_require_is_really_needed():
    from doc2roadmap.domain.gold_scoring import target_precision

    # Chương vàng gồm t, b, a, x. Vàng: a → b → t và c → t (c ngoài chương). Máy: a → b → t, x → t, z → t (z ngoài chương).
    gold = {("a", "b"), ("b", "t"), ("c", "t")}
    machine = {("a", "b"), ("b", "t"), ("x", "t"), ("z", "t")}
    result = target_precision(gold, machine, ["t", "b", "a", "x"])
    # t: tổ tiên máy trong chương {a, b, x}, cần {a, b} → 2/3 (z ngoài chương không tính); b: {a}, cần → 1/1;
    # a và x không có tổ tiên máy trong chương nên không tính.
    assert result["targets"] == 2
    assert result["mean_precision"] == pytest.approx((2 / 3 + 1) / 2)
    assert (result["in_chapter_ancestors"], result["needed"]) == (4, 3)
    # Đích mà vàng nói không cần gì nhưng máy bắt học trước một khái niệm trong chương: độ chính xác 0, vẫn tính.
    assert target_precision(set(), {("a", "x")}, ["a", "x"])["mean_precision"] == 0
