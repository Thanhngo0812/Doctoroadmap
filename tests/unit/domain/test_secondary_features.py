from types import SimpleNamespace

from doc2roadmap.domain.secondary_features import (
    FEATURE_NAMES, SecondaryFeatureContext, feature_rows, found_words, word_regexes,
)


def document():
    chunks = [SimpleNamespace(chunk_id="c1", text="Chất là vật chất.", order_index=0,
                              parent_section_id="s1", section_path=["Chương", "1"], role="noi_dung"),
              SimpleNamespace(chunk_id="c2", text="Y là quy luật của Chất.", order_index=1,
                              parent_section_id="s2", section_path=["Chương", "2"], role="bai_tap")]
    nodes = [{"node_id": x, "name": name, "cluster_id": "g", "learnable": True,
              "teaching_status": "taught", "defining_chunk_ids": [chunk.chunk_id],
              "anchor": {"chunk_id": chunk.chunk_id, "sentence": chunk.text}}
             for x, name, chunk in zip(("x", "y"), ("Chất", "Y"), chunks)]
    return {"nodes": nodes, "mention_map": {"c1": {"x": {"channels": ["exact"]}},
                                           "c2": {"x": {}, "y": {}}},
            "suspected_pairs": [{"pair_id": "xy", "left": "x", "right": "y", "sources": ["same_section"]}],
            "routing": {"route": "chapter"}}, chunks


def fake_words(text):
    return [word.replace("_", " ") for word in
            text.replace("vật chất", "vật_chất").replace("quy luật", "quy_luật").split()]


def test_word_boundaries_and_y_syllable_normalization():
    assert not found_words(word_regexes({"name": "Chất"}), "vật chất", fake_words)
    assert found_words(word_regexes({"name": "Quy luật"}), "Y là quy luật tự nhiên.", fake_words)


def test_features_order_structure_contract_and_missing_cells():
    payload, chunks = document()
    rows = list(feature_rows(payload, chunks, fake_words))
    xy = rows[0]
    assert len(FEATURE_NAMES) == 82 and not any(key.startswith("main_") for key in FEATURE_NAMES)
    assert tuple(key for key in xy if key in FEATURE_NAMES) == FEATURE_NAMES
    assert xy["ung_vien"] == 1
    assert (xy["ord_x"], xy["ord_y"], xy["ord_hieu"]) == (0, .5, .5)
    assert (xy["x_truoc_y"], xy["cung_muc"], xy["cung_chuong"], xy["muc_chung"]) == (1, 0, 1, 1)
    assert xy["neo_y_bai_tap"] == 1 and xy["neo_y_noi_dung"] == 0
    chunks[1].parent_section_id = "s1"
    chunks[1].section_path = ["Khác", "2"]
    changed = list(feature_rows(payload, chunks, fake_words))[0]
    assert (changed["cung_muc"], changed["cung_chuong"], changed["muc_chung"]) == (1, 0, 0)
    reverse = list(feature_rows(payload, chunks, fake_words))[1]
    assert reverse["ord_hieu"] == -.5 and reverse["x_truoc_y"] == 0
    payload["nodes"][1]["teaching_status"] = "mentioned_only"
    assert list(feature_rows(payload, chunks, fake_words))[0]["ung_vien"] == 0
    payload["nodes"][0]["defining_chunk_ids"] = []
    assert list(feature_rows(payload, chunks, fake_words))[0]["ord_x"] == ""


def test_feature_inputs_ignore_main_edges_and_require_both_matches():
    payload, chunks = document()
    before = list(feature_rows(payload, chunks, fake_words))
    payload["main_edges"] = [{"source": "x", "target": "y", "soft": False}]
    assert list(feature_rows(payload, chunks, fake_words)) == before
    payload["nodes"][0]["learnable"] = False
    assert list(feature_rows(payload, chunks, fake_words))[0]["ung_vien"] == 0
    ctx = SecondaryFeatureContext(payload, chunks, tokenize=fake_words)
    assert ctx.rank == {"x": 0.0, "y": 0.0}


def test_candidate_needs_exact_and_word_match_not_a_compound_fragment():
    payload, chunks = document()
    chunks[1].text = "Y là vật chất."
    payload["nodes"][1]["anchor"]["sentence"] = chunks[1].text
    row = list(feature_rows(payload, chunks, fake_words))[0]
    assert row["x_trong_ywin"] == 1
    assert row["x_trong_ywin_tu"] == 0 and row["ung_vien"] == 0
    chunks[1].text = "Y không nói về X."
    payload["nodes"][1]["anchor"]["sentence"] = chunks[1].text
    # A tokenizer cannot invent a name that was absent from the exact channel.
    row = list(feature_rows(payload, chunks, lambda text: ["Chất"]))[0]
    assert row["x_trong_ywin"] == 0 and row["ung_vien"] == 0
