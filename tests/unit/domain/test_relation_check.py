import pytest

from doc2roadmap.domain.relation_check import apply_relation_verdicts, edge_id, validate_relation_response

PASSAGES = [
    "Định nghĩa. Cho K là một trường. Tập V cùng phép cộng và phép nhân với vô hướng thuộc K là không gian véc tơ.",
    "Ví dụ 4. Tập C[a, b] các hàm thực liên tục là một không gian véc tơ.",
]


def reply(verdict, **extra):
    return {"edge_id": "a->b", "verdict": verdict, "reason": "vì đoạn nói vậy", **extra}


def check(value):
    validate_relation_response(value, edge_id="a->b", passages=PASSAGES)


def test_a_verdict_that_claims_a_link_must_quote_one_of_the_supplied_passages():
    check(reply("requires", quote="phép nhân với vô hướng thuộc K"))
    check(reply("supports", quote="Tập C[a, b] các hàm thực liên tục là một không gian véc tơ."))
    with pytest.raises(ValueError, match="không có trong hồ sơ"):
        check(reply("requires", quote="không gian véc tơ cần ma trận"))
    for verdict in ("requires", "supports", "reversed"):
        with pytest.raises(ValueError, match="cần quote"):
            check(reply(verdict))


def test_verdicts_that_claim_no_link_need_no_quote():
    check(reply("unrelated"))
    check(reply("unresolved"))


def test_the_response_contract_rejects_foreign_edges_unknown_verdicts_confidence_and_empty_reasons():
    with pytest.raises(ValueError, match="edge_id"):
        check({**reply("unrelated"), "edge_id": "b->a"})
    with pytest.raises(ValueError, match="năm giá trị"):
        check(reply("maybe"))
    with pytest.raises(ValueError, match="confidence"):
        check(reply("unrelated", confidence=0.9))
    with pytest.raises(ValueError, match="reason"):
        check({**reply("unrelated"), "reason": " "})


def edge(source, target):
    return {"source": source, "target": target, "edge_type": "requires", "chunk_ids": ["c1"]}


def test_only_a_definitional_dependency_stays_a_hard_constraint():
    edges = [edge("a", "b"), edge("c", "b"), edge("d", "b"), edge("e", "b"), edge("f", "b"), edge("g", "b")]
    verdicts = {
        edge_id(edges[0]): {"verdict": "requires", "reason": "định nghĩa b dùng a"},
        # Ví dụ hoặc định lý nối hai khái niệm giúp học nhưng không phải tiên quyết cứng.
        edge_id(edges[1]): {"verdict": "supports", "reason": "c là một ví dụ của b"},
        edge_id(edges[2]): {"verdict": "reversed", "reason": "định nghĩa d dùng b"},
        edge_id(edges[3]): {"verdict": "unrelated", "reason": "không liên quan"},
        # Chưa đủ căn cứ, hoặc phản hồi hỏng: giữ cạnh để không đánh mất recall vì một câu trả lời không dùng được.
        edge_id(edges[4]): {"verdict": "unresolved", "reason": "đoạn không đủ"},
    }
    result = apply_relation_verdicts(edges, verdicts)
    assert [(value["source"], value["target"]) for value in result["requires"]] == [("a", "b"), ("f", "b"), ("g", "b")]
    assert [(value["source"], value["target"], value["relation_check"]) for value in result["recommended"]] == [
        ("c", "b", "supports")]
    assert [(value["source"], value["target"], value["relation_check"]) for value in result["rejected"]] == [
        ("d", "b", "reversed"), ("e", "b", "unrelated")]
    kept = {(value["source"], value["relation_check"]) for value in result["requires"]}
    assert kept == {("a", "requires"), ("f", "unresolved"), ("g", "unchecked")}
