from types import SimpleNamespace

import pytest

from doc2roadmap.domain.anchors import (anchor_fields, candidate_sentences, label_families,
                                        validate_anchor_response, validate_display_name)


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


def test_candidates_without_evidence_follow_document_order_not_language_signals():
    candidates = candidate_sentences(NODE, CHUNKS, limit=3)
    assert [c["chunk_id"] for c in candidates] == ["de_cuong", "c40", "c41"]
    first = candidates[1]
    assert first["sentence"] == "Một hệ véc tơ được gọi là một cơ sở của V nếu nó độc lập tuyến tính và sinh ra V."
    assert CHUNKS[1].text[first["char_start"]:first["char_start"] + len(first["sentence"])] == first["sentence"]
    assert "Nhắc lại hệ sinh." in first["context"]  # một câu ngữ cảnh mỗi phía
    assert len(candidates) == 3 and all(c["chunk_id"] != "c99" for c in candidates)


@pytest.mark.parametrize("name,title,first", [
    ("espace vectoriel", "3.31 définition : espace vectoriel", "Soit V un ensemble muni de deux opérations."),
    ("向量空间", "定义：向量空间", "设 V 是一个集合。"),
])
def test_heading_named_block_precedes_preview_and_teaches_from_first_body_sentence(name, title, first):
    chunks = [chunk("preview", 1, f"{name} sera étudié plus tard."),
              chunk("real", 9, f"{title}\n{first} Autre détail.")]
    candidates = candidate_sentences({"name": name}, chunks)
    assert candidates[0]["chunk_id"] == "real"
    assert candidates[0]["sentence"] == first
    assert chunks[1].text[candidates[0]["char_start"]:].startswith(first)
    assert title in candidates[0]["context"]


def test_section_title_is_a_candidate_when_body_never_repeats_name():
    chunks = [chunk("preview", 1, "Column-row factorization will be introduced later."),
              chunk("real", 9, "Suppose A is an m-by-n matrix. Then A = CR.")]
    chunks[1].section_path = ["3.56 column-row factorization"]
    candidates = candidate_sentences({"name": "Column-row factorization"}, chunks)
    assert candidates[0]["chunk_id"] == "real"
    assert candidates[0]["sentence"] == "Suppose A is an m-by-n matrix."
    assert "3.56 column-row factorization" in candidates[0]["context"]


def test_other_definition_signals_do_not_outrank_true_heading():
    chunks = [chunk("other", 2, "A square matrix is called invertible."),
              chunk("real", 20, "An m-by-n matrix A is a rectangular array of scalars.")]
    chunks[1].section_path = ["3.29 definition: matrix"]
    candidates = candidate_sentences({"name": "Matrix"}, chunks)
    assert candidates[0]["chunk_id"] == "real"


def test_a3_citation_stays_ahead_of_named_heading():
    chunks = [chunk("evidence", 30, "Câu căn cứ mô tả tính chất cốt lõi."),
              chunk("heading", 10, "Định nghĩa: Khái niệm X\nĐây là câu đầu tiên.")]
    node = {"name": "Khái niệm X", "evidence": [{"chunk_id": "evidence", "quote": "Câu căn cứ mô tả tính chất cốt lõi."}]}
    candidates = candidate_sentences(node, chunks)
    assert [c["chunk_id"] for c in candidates[:2]] == ["evidence", "heading"]


def test_named_teaching_block_survives_six_a3_mentions_in_top_six():
    previews = [chunk(f"e{i}", i, f"The matrix of a linear map is discussed in chapter {i}.")
                for i in range(6)]
    real = chunk("real", 50, "Now we come to the key definition.\n"
                 "3.31 definition: matrix of a linear map\n"
                 "Suppose T is a linear map. Its matrix contains the coordinates of T applied to basis vectors.")
    node = {"name": "Matrix of a linear map", "evidence": [
        {"chunk_id": value.chunk_id, "quote": value.text} for value in previews]}
    candidates = candidate_sentences(node, [*previews, real], limit=6)
    assert any(value["chunk_id"] == "real" and value["sentence"].startswith("Suppose T")
               for value in candidates)


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
    anchor = next(c["cand_id"] for c in candidates if c["chunk_id"] == "c40")
    check(reply("defined_here", anchor=anchor, quote="được gọi là một cơ sở của V"), candidates)
    with pytest.raises(ValueError, match="ứng viên"):
        check(reply("defined_here", anchor="k99", quote="được gọi là một cơ sở của V"), candidates)
    with pytest.raises(ValueError, match="không có trong"):
        check(reply("defined_here", anchor=anchor, quote="cơ sở là tập rỗng"), candidates)
    with pytest.raises(ValueError, match="cần anchor"):
        check(reply("introduced_by_example", quote="được gọi là một cơ sở của V"), candidates)


def test_prior_knowledge_quote_is_checked_before_independent_semantic_verification():
    # Vé 05: kiểm nghĩa đã chuyển sang lượt độc lập; luật thuần chỉ kiểm câu có trong ứng viên.
    candidates = [{"cand_id": "k1", "chunk_id": "x", "order_index": 1, "char_start": 0,
                   "sentence": "Suppose V is a complex inner product space.",
                   "context": "Suppose V is a complex inner product space. Recall from a previous course the dot product."}]
    check(reply("prior_knowledge", quote="Suppose V is a complex inner product space."), candidates)
    with pytest.raises(ValueError, match="không có trong"):
        check(reply("prior_knowledge", quote="Made-up quote."), candidates)
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
    anchor = next(c for c in candidates if c["chunk_id"] == "c40")
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


def test_label_families_use_two_distinct_numbers_in_names_or_headings_across_scripts():
    names = ["Tính chất 1", "Tính chất 3", "Theorem 4", "Theorem 7", "Teorema 2", "Teorema 8",
             "定理2", "定理5", "Lemma 1"]
    nodes = [{"name": name} for name in names]
    headings = [SimpleNamespace(section_path=["Định lý 4"]), SimpleNamespace(section_path=["Định lý 7"])]
    assert label_families(nodes, headings) == {"tính chất", "theorem", "teorema", "定理", "định lý"}
    assert "lemma" not in label_families(nodes, headings)


def test_display_name_must_be_short_and_grounded_in_anchor_sentence():
    sentence = "Tính chất 1. Nếu ma trận A khả nghịch thì định thức của A khác không."
    validate_display_name({"node_id": "n", "display_name": "Định thức khác không"},
                          node_id="n", label="Tính chất 1", sentence=sentence)
    with pytest.raises(ValueError, match="không nằm"):
        validate_display_name({"node_id": "n", "display_name": "Định thức luôn dương"},
                              node_id="n", label="Tính chất 1", sentence=sentence)
    with pytest.raises(ValueError, match="nhãn đánh số"):
        validate_display_name({"node_id": "n", "display_name": "Tính chất 1"},
                              node_id="n", label="Tính chất 1", sentence=sentence)
    with pytest.raises(ValueError, match="nhãn đánh số"):
        validate_display_name({"node_id": "n", "display_name": "Tính chất"},
                              node_id="n", label="Tính chất 1", sentence=sentence)
    validate_display_name({"node_id": "z", "display_name": "逆行列"}, node_id="z", label="定理2",
                          sentence="定理2。逆行列が存在する。")
