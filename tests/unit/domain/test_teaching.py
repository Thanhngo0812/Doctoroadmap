import pytest

from doc2roadmap.domain.teaching import bypass_excluded, teaching_status, validate_teaching_response, verdict_of

TEXT = "Định nghĩa. Ma trận là một bảng số gồm m hàng và n cột."


def reply(kind, role, **extra):
    return {"node_id": "n", "chunk_id": "c1", "kind": kind, "role": role, "reason": "vì đoạn nói vậy", **extra}


def check(value):
    validate_teaching_response(value, node_id="n", chunk_id="c1", chunk_text=TEXT)


def test_a_claim_about_the_passage_must_quote_it_verbatim():
    check(reply("concept", "teaches", quote="Ma trận là một bảng số"))
    check(reply("concept", "teaches", quote="  Ma trận là   một bảng số "))  # khoảng trắng không phải nội dung
    with pytest.raises(ValueError, match="không có trong đoạn"):
        check(reply("concept", "teaches", quote="Ma trận là một hàm số"))
    for kind, role in (("concept", "teaches"), ("concept", "prior_knowledge"), ("course_logistics", "mentions"),
                       ("example_detail", "mentions"), ("non_subject", "uncertain")):
        with pytest.raises(ValueError, match="cần quote"):
            check(reply(kind, role))


def test_answers_that_claim_nothing_about_the_passage_need_no_quote():
    check(reply("concept", "mentions"))
    check(reply("concept", "uncertain"))
    check(reply("uncertain", "teaches"))


def test_the_response_contract_rejects_foreign_ids_unknown_answers_confidence_and_empty_reasons():
    with pytest.raises(ValueError, match="node_id hoặc chunk_id"):
        check({**reply("concept", "mentions"), "chunk_id": "c9"})
    with pytest.raises(ValueError, match="kind"):
        check(reply("definition", "mentions"))
    with pytest.raises(ValueError, match="role"):
        check(reply("concept", "defines"))
    with pytest.raises(ValueError, match="confidence"):
        check(reply("concept", "mentions", confidence=0.9))
    with pytest.raises(ValueError, match="reason"):
        check({**reply("concept", "mentions"), "reason": "  "})


@pytest.mark.parametrize(("kind", "role", "verdict"), [
    # Ca v1 hỏng: một cột của bộ dữ liệu ví dụ "được nêu tên" vẫn không phải kiến thức môn học.
    ("example_detail", "mentions", "not_subject_matter"),
    ("course_logistics", "teaches", "not_subject_matter"),
    ("non_subject", "mentions", "not_subject_matter"),
    ("uncertain", "teaches", "uncertain"),
    ("concept", "teaches", "teaches"),
    ("concept", "mentions", "mentions_only"),
    ("concept", "prior_knowledge", "prior_knowledge"),
    ("concept", "uncertain", "uncertain"),
])
def test_what_the_item_is_decides_exclusion_before_what_the_passage_does_with_it(kind, role, verdict):
    assert verdict_of({"kind": kind, "role": role}) == verdict


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
