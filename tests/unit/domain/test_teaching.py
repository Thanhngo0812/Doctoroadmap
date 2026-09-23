import pytest

from doc2roadmap.domain.teaching import bypass_excluded, teaching_status, validate_teaching_response

TEXT = "Định nghĩa. Ma trận là một bảng số gồm m hàng và n cột."


def reply(verdict, **extra):
    return {"node_id": "n", "chunk_id": "c1", "verdict": verdict, "reason": "vì đoạn nói vậy", **extra}


def check(value):
    validate_teaching_response(value, node_id="n", chunk_id="c1", chunk_text=TEXT)


def test_a_teaching_verdict_must_quote_the_passage_verbatim():
    check(reply("teaches", quote="Ma trận là một bảng số"))
    check(reply("teaches", quote="  Ma trận là   một bảng số "))  # khoảng trắng không phải nội dung
    with pytest.raises(ValueError, match="không có trong đoạn"):
        check(reply("teaches", quote="Ma trận là một hàm số"))
    for verdict in ("teaches", "prior_knowledge", "not_subject_matter"):
        with pytest.raises(ValueError, match="cần quote"):
            check(reply(verdict))


def test_verdicts_without_a_claim_about_the_passage_need_no_quote():
    check(reply("mentions_only"))
    check(reply("uncertain"))


def test_the_response_contract_rejects_foreign_ids_unknown_verdicts_confidence_and_empty_reasons():
    with pytest.raises(ValueError, match="node_id hoặc chunk_id"):
        check({**reply("uncertain"), "chunk_id": "c9"})
    with pytest.raises(ValueError, match="năm giá trị"):
        check(reply("defines"))
    with pytest.raises(ValueError, match="confidence"):
        check(reply("uncertain", confidence=0.9))
    with pytest.raises(ValueError, match="reason"):
        check({**reply("uncertain"), "reason": "  "})


def row(chunk_id, verdict, order):
    return {"chunk_id": chunk_id, "verdict": verdict, "order_index": order}


def test_one_teaching_passage_keeps_the_node_and_fixes_its_position_past_the_syllabus():
    # `Dạng toàn phương` bị đề cương đầu sách kéo vị trí về 10; đoạn dạy thật ở sau.
    status = teaching_status([row("de_cuong", "mentions_only", 10), row("c80", "teaches", 80), row("c95", "teaches", 95)])
    assert status == {"teaching_status": "taught", "teaching_chunk_ids": ["c80", "c95"],
                      "teaching_order_index": 80, "teaching_conflict": False}


def test_teaches_wins_over_an_exclusion_but_the_conflict_is_recorded():
    status = teaching_status([row("c1", "not_subject_matter", 1), row("c2", "teaches", 2)])
    assert status["teaching_status"] == "taught" and status["teaching_conflict"] is True


@pytest.mark.parametrize(("verdicts", "expected"), [
    (["uncertain", "not_subject_matter"], "uncertain"),
    (["uncertain", "prior_knowledge"], "uncertain"),  # một đoạn chưa rõ là chưa đủ căn cứ để loại
    (["prior_knowledge", "not_subject_matter"], "prior_knowledge"),
    (["not_subject_matter", "mentions_only"], "not_subject_matter"),
    (["mentions_only", "mentions_only"], "mentioned_only"),
    ([], "unchecked"),
])
def test_status_precedence_is_fixed(verdicts, expected):
    status = teaching_status([row(f"c{index}", verdict, index) for index, verdict in enumerate(verdicts)])
    assert status["teaching_status"] == expected
    assert status["teaching_chunk_ids"] == [] and status["teaching_order_index"] is None


def edge(source, target, **extra):
    return {"source": source, "target": target, "edge_type": "requires", **extra}


def test_bypassing_an_excluded_node_keeps_every_learn_before_constraint():
    # a → x → y → b với x, y bị loại: bỏ hai node mà không co thì mất ràng buộc a trước b.
    edges = [edge("a", "x"), edge("x", "y"), edge("y", "b"), edge("a", "c", reason="giữ nguyên")]
    kept, added = bypass_excluded(edges, {"x", "y"})
    assert {(value["source"], value["target"]) for value in kept} == {("a", "c"), ("a", "b")}
    assert added == [{"source": "a", "target": "b", "edge_type": "requires", "via_excluded": ["x", "y"]}]
    assert next(value for value in kept if value["target"] == "c")["reason"] == "giữ nguyên"


def test_bypassing_does_not_duplicate_a_constraint_that_already_exists():
    kept, added = bypass_excluded([edge("a", "x"), edge("x", "b"), edge("a", "b")], {"x"})
    assert added == [] and [(value["source"], value["target"]) for value in kept] == [("a", "b")]


def test_an_excluded_leaf_simply_disappears():
    kept, added = bypass_excluded([edge("a", "x"), edge("a", "b")], {"x"})
    assert added == [] and [(value["source"], value["target"]) for value in kept] == [("a", "b")]
