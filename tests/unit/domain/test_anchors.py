from types import SimpleNamespace

import pytest

from doc2roadmap.domain.anchors import anchor_fields, candidate_sentences, validate_anchor_response


def chunk(chunk_id, order, text):
    return SimpleNamespace(chunk_id=chunk_id, order_index=order, text=text, section_path=["S"])


NODE = {"node_id": "cs", "name": "Cơ sở", "aliases": [{"name": "basis"}]}
CHUNKS = [
    chunk("de_cuong", 5, "Chương 3 học không gian véc tơ, cơ sở và số chiều."),
    chunk("c40", 40, "Nhắc lại hệ sinh. Một hệ véc tơ được gọi là một cơ sở của V nếu nó độc lập tuyến tính và sinh ra V. "
                     "Ví dụ trên cho thấy điều đó."),
    chunk("c41", 41, "Mỗi cơ sở của Rn có n véc tơ. Số chiều bằng số véc tơ của một cơ sở."),
    chunk("c90", 90, "Trong bài tập, hãy tìm một basis cho không gian nghiệm."),
    chunk("c99", 99, "Câu này không nói gì về khái niệm đó."),
]


def test_candidates_are_sentences_naming_the_concept_with_definition_signals_first():
    candidates = candidate_sentences(NODE, CHUNKS, limit=3)
    assert [c["chunk_id"] for c in candidates][0] == "c40"  # câu có "được gọi là" đứng đầu
    first = candidates[0]
    assert first["sentence"] == "Một hệ véc tơ được gọi là một cơ sở của V nếu nó độc lập tuyến tính và sinh ra V."
    assert CHUNKS[1].text[first["char_start"]:first["char_start"] + len(first["sentence"])] == first["sentence"]
    assert "Nhắc lại hệ sinh." in first["context"]  # một câu ngữ cảnh mỗi phía
    assert len(candidates) == 3 and all(c["chunk_id"] != "c99" for c in candidates)


def test_an_alias_counts_as_naming_the_concept():
    assert any(c["chunk_id"] == "c90" for c in candidate_sentences(NODE, CHUNKS, limit=10))


def test_math_letters_and_spacing_do_not_hide_the_name():
    # PDF toán cho chữ nghiêng toán học và khoảng trắng lạc: "𝑉1 × ⋯ × 𝑉 𝑚" vẫn là "V1 × ⋯ × Vm".
    node = {"node_id": "p", "name": "Addition on V1 × ⋯ × Vm", "aliases": []}
    text = "Addition on 𝑉1 × ⋯ × 𝑉 𝑚 is defined by the formula."
    assert [c["sentence"] for c in candidate_sentences(node, [chunk("c7", 7, text)])] == [text]


def test_the_a3_evidence_sentence_is_a_candidate_even_when_the_name_never_appears():
    # Tên mô tả do mô hình đặt ("Hàng hoặc cột tỷ lệ") không có nguyên văn; câu căn cứ A3 là nơi đã kiểm có trong sách.
    text = "Định thức bằng không nếu: Có hai hàng (hay hai cột) tỷ lệ; Có một hàng bằng không."
    node = {"node_id": "tl", "name": "Hàng hoặc cột tỷ lệ", "aliases": [],
            # offset căn cứ tính trên toàn văn bản, không trên chunk — không được dùng làm chỉ số vào chunk.text
            "evidence": [{"chunk_id": "c3", "char_start": 22478, "char_end": 22510, "quote": "Có hai hàng (hay hai cột) tỷ lệ;"}]}
    candidates = candidate_sentences(node, [chunk("c3", 3, text), chunk("c4", 4, "Câu khác.")])
    assert [c["chunk_id"] for c in candidates] == ["c3"]
    first = candidates[0]
    assert text[first["char_start"]:first["char_start"] + len(first["sentence"])] == first["sentence"]
    assert "Có hai hàng" in first["sentence"]


def reply(status, **extra):
    return {"node_id": "cs", "status": status, "reason": "vì đoạn nói vậy", **extra}


def check(value, candidates):
    validate_anchor_response(value, node_id="cs", candidates=candidates)


def test_an_anchored_status_must_point_to_a_candidate_and_quote_it_verbatim():
    candidates = candidate_sentences(NODE, CHUNKS, limit=4)
    anchor = candidates[0]["cand_id"]
    check(reply("defined_here", anchor=anchor, quote="được gọi là một cơ sở của V"), candidates)
    with pytest.raises(ValueError, match="ứng viên"):
        check(reply("defined_here", anchor="k99", quote="được gọi là một cơ sở của V"), candidates)
    with pytest.raises(ValueError, match="không có trong"):
        check(reply("defined_here", anchor=anchor, quote="cơ sở là tập rỗng"), candidates)
    with pytest.raises(ValueError, match="cần anchor"):
        check(reply("introduced_by_example", quote="được gọi là một cơ sở của V"), candidates)


def test_prior_knowledge_needs_an_explicit_signal_not_a_theorem_hypothesis():
    # v2 kích nhầm bởi "Suppose V is a complex inner product space": dùng khái niệm không có nghĩa là đòi biết trước.
    candidates = [{"cand_id": "k1", "chunk_id": "x", "order_index": 1, "char_start": 0,
                   "sentence": "Suppose V is a complex inner product space.",
                   "context": "Suppose V is a complex inner product space. Recall from a previous course the dot product."}]
    with pytest.raises(ValueError, match="tín hiệu tường minh"):
        check(reply("prior_knowledge", quote="Suppose V is a complex inner product space."), candidates)
    check(reply("prior_knowledge", quote="Recall from a previous course the dot product."), candidates)


def test_the_contract_rejects_unknown_status_confidence_and_empty_reason():
    candidates = candidate_sentences(NODE, CHUNKS, limit=2)
    with pytest.raises(ValueError, match="status"):
        check(reply("teaches"), candidates)
    with pytest.raises(ValueError, match="confidence"):
        check(reply("mentioned_only", confidence=0.8), candidates)
    with pytest.raises(ValueError, match="reason"):
        check({**reply("uncertain"), "reason": " "}, candidates)
    with pytest.raises(ValueError, match="quote"):
        check(reply("not_subject_matter"), candidates)


def test_an_anchor_keeps_the_node_and_moves_its_position_to_where_it_is_taught():
    candidates = candidate_sentences(NODE, CHUNKS, limit=4)
    anchor = candidates[0]
    fields = anchor_fields(reply("defined_here", anchor=anchor["cand_id"], quote="được gọi là một cơ sở của V"), candidates)
    assert fields["teaching_status"] == "taught"
    assert fields["teaching_chunk_ids"] == ["c40"] and fields["teaching_order_index"] == 40
    assert fields["anchor"] == {"chunk_id": "c40", "char_start": anchor["char_start"], "sentence": anchor["sentence"]}
    assert anchor_fields(reply("mentioned_only"), candidates)["teaching_status"] == "mentioned_only"
    assert anchor_fields(reply("uncertain"), candidates)["teaching_chunk_ids"] == []


def test_an_anchor_returned_with_a_non_teaching_status_is_not_used_as_the_teaching_place():
    candidates = candidate_sentences(NODE, CHUNKS, limit=4)
    fields = anchor_fields(reply("mentioned_only", anchor=candidates[0]["cand_id"]), candidates)
    assert fields["teaching_chunk_ids"] == [] and fields["anchor"] is None


def test_latex_markup_and_dash_variants_do_not_hide_the_name():
    # doc-2: nút `𝐅^{m,n}` không bao giờ thấy câu định nghĩa "… is denoted by 𝐅 𝑚 , 𝑛" vì `^{ }`; vị trí dạy rơi về chunk
    # dùng muộn và gây 3/6 vi phạm Q6 của chương vàng.
    node = {"node_id": "fmn", "name": "𝐅^{m,n}", "aliases": []}
    text = "The set of all 𝑚-by-𝑛 matrices with entries in 𝐅 is denoted by 𝐅 𝑚 , 𝑛 ."
    assert [c["sentence"] for c in candidate_sentences(node, [chunk("c356", 356, text)])] == [text]
    dashed = {"node_id": "crf", "name": "Column-row factorization", "aliases": []}
    text = "3.56 column–row factorization: every matrix is a product of two matrices."
    assert candidate_sentences(dashed, [chunk("c379", 379, text)])


def test_a_symbolic_name_is_searched_across_the_whole_document_but_a_plain_word_is_not():
    from doc2roadmap.domain.anchors import symbolic_name_chunks

    chunks = [chunk("c356", 356, "The set of all 𝑚-by-𝑛 matrices with entries in 𝐅 is denoted by 𝐅 𝑚 , 𝑛 ."),
              chunk("c431", 431, "Suppose 𝐴 ∈ 𝐅 𝑚 , 𝑛 and 𝐶 ∈ 𝐅 𝑛 , 𝑝 ."),
              chunk("c500", 500, "An additional remark about addition.")]
    fmn = {"node_id": "fmn", "name": "𝐅^{m,n}", "aliases": []}
    assert symbolic_name_chunks(fmn, chunks) == {"c356", "c431"}
    # tên chữ thường đã được mention map (A6) khớp theo ranh giới từ; so sau khi bỏ khoảng trắng sẽ khớp nhầm "additional"
    assert symbolic_name_chunks({"node_id": "add", "name": "Addition", "aliases": []}, chunks) == set()
