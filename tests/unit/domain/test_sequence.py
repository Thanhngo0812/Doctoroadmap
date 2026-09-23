import random

import pytest

from doc2roadmap.domain.sequence import choose_levels, learning_sequence, segment_modules


def edge(source, target):
    return {"source": source, "target": target, "edge_type": "requires"}


# --- W2: dãy học -------------------------------------------------------------------------------------------------


def test_without_edges_the_sequence_is_the_teaching_order():
    # Thứ tự dạy cố ý ngược thứ tự chữ cái, để test phân biệt được "theo sách" với "theo mã node".
    position = {"c": (1, 0), "b": (1, 50), "a": (3, 0)}
    assert learning_sequence(["a", "b", "c"], [], position) == ["c", "b", "a"]


def test_a_prerequisite_the_book_teaches_late_is_pulled_forward_by_the_ready_rule():
    # Sách dạy z trước m, a; nhưng a là tiên quyết của z. Luật: luôn lấy khái niệm sẵn sàng đứng sớm nhất trong sách.
    position = {"z": (1, 0), "m": (2, 0), "a": (3, 0)}
    assert learning_sequence(["a", "m", "z"], [edge("a", "z")], position) == ["m", "a", "z"]


def test_input_order_does_not_change_the_sequence():
    position = {name: (index // 2, index) for index, name in enumerate("abcdefgh")}
    edges = [edge("f", "b"), edge("c", "h"), edge("a", "d")]
    expected = learning_sequence(list("abcdefgh"), edges, position)
    for seed in range(5):
        ids = list("abcdefgh")
        random.Random(seed).shuffle(ids)
        assert learning_sequence(ids, list(reversed(edges)), position) == expected


def test_every_edge_of_a_random_dag_goes_forward():
    rng = random.Random(7)
    ids = [f"n{index}" for index in range(60)]
    rank = {node: rng.random() for node in ids}  # thứ tự ẩn làm cho đồ thị là DAG
    edges = [edge(a, b) for a in ids for b in ids if rank[a] < rank[b] and rng.random() < 0.05]
    position = {node: (rng.randrange(20), rng.randrange(100)) for node in ids}
    sequence = learning_sequence(ids, edges, position)
    index = {node: i for i, node in enumerate(sequence)}
    assert sorted(sequence) == sorted(ids)
    assert all(index[e["source"]] < index[e["target"]] for e in edges)


def test_a_cycle_is_refused():
    with pytest.raises(ValueError, match="chu trình"):
        learning_sequence(["a", "b"], [edge("a", "b"), edge("b", "a")], {"a": (1, 0), "b": (2, 0)})


# --- W3: chia module -----------------------------------------------------------------------------------------------


def names(count, prefix="x"):
    return [f"{prefix}{index}" for index in range(count)]


def test_modules_partition_the_sequence_in_order_and_respect_the_width():
    sequence = names(23)
    modules = segment_modules(sequence, width=8)
    assert [node for module in modules for node in module] == sequence
    assert all(1 <= len(module) <= 8 for module in modules)


def test_two_short_sections_become_two_modules_not_one_mixed_module():
    sequence = names(4, "a") + names(4, "b")
    unit_of = {**{n: "sec-a" for n in names(4, "a")}, **{n: "sec-b" for n in names(4, "b")}}
    assert [len(m) for m in segment_modules(sequence, width=8, unit_of=unit_of)] == [4, 4]


def test_a_long_section_is_split_into_balanced_modules():
    sequence = names(12)
    unit_of = {n: "sec" for n in sequence}
    assert [len(m) for m in segment_modules(sequence, width=8, unit_of=unit_of)] == [6, 6]


def test_a_flat_document_is_cut_by_size_alone_into_balanced_modules():
    assert [len(m) for m in segment_modules(names(20), width=8)] == [7, 7, 6]


def test_a_module_does_not_straddle_two_chapters_when_it_can_avoid_it():
    sequence = names(3, "a") + names(3, "b")
    chapter_of = {**{n: "ch1" for n in names(3, "a")}, **{n: "ch2" for n in names(3, "b")}}
    assert [len(m) for m in segment_modules(sequence, width=8, chapter_of=chapter_of)] == [3, 3]


# --- W4: cấp mục theo tài liệu ---------------------------------------------------------------------------------------


def test_levels_are_chosen_from_how_many_concepts_each_section_holds():
    # Hai chương, mỗi chương hai mục bốn khái niệm: cấp 1 là "chương", cấp 2 là "mục".
    ancestry = {f"n{i}": [f"ch{i // 8}", f"sec{i // 4}"] for i in range(16)}
    assert choose_levels(ancestry, width=8) == (1, 2)


def test_a_flat_deck_with_one_concept_per_slide_turns_section_penalties_off():
    ancestry = {f"n{i}": [f"slide{i}"] for i in range(30)}
    assert choose_levels(ancestry, width=8) == (None, None)


def test_when_only_one_level_qualifies_it_is_the_unit_and_there_is_no_chapter_level():
    # Axler: cấp 2 mịn gần một khái niệm mỗi mục, chỉ cấp 1 đủ lớn.
    ancestry = {f"n{i}": [f"ch{i // 10}", f"box{i}"] for i in range(40)}
    assert choose_levels(ancestry, width=8) == (None, 1)


def test_a_lone_concept_from_another_section_is_folded_into_a_neighbour_instead_of_standing_alone():
    # Đồ thị kéo một tiên quyết từ mục khác lên giữa hai mục: để nó thành module một khái niệm là vụn (đo được 13 module
    # như vậy trên doc-1). Gộp vào module bên cạnh và để tên module ghi rõ hai mục thì hơn.
    sequence = names(4, "a") + ["b0"] + names(3, "c")
    unit_of = {**{n: "sec-a" for n in names(4, "a")}, "b0": "sec-b", **{n: "sec-c" for n in names(3, "c")}}
    modules = segment_modules(sequence, width=8, unit_of=unit_of)
    assert all(len(module) >= 3 for module in modules)
    assert ["b0"] not in modules


# --- W9: lộ trình tới mục tiêu ---------------------------------------------------------------------------------------


def test_a_target_path_keeps_exactly_the_target_and_its_ancestors_in_roadmap_order():
    from doc2roadmap.domain.sequence import target_modules

    edges = [edge("a", "c"), edge("b", "c"), edge("c", "e"), edge("d", "f")]
    modules = [{"module_id": "module_001", "node_ids": ["a", "d", "b"]},
               {"module_id": "module_002", "node_ids": ["c", "f", "e"]}]
    assert target_modules(modules, edges, ["e"]) == [
        {"module_id": "module_001", "node_ids": ["a", "b"]},
        {"module_id": "module_002", "node_ids": ["c", "e"]},
    ]
    # Đích không có tiên quyết chỉ còn chính nó; module không còn khái niệm nào thì bỏ.
    assert target_modules(modules, edges, ["d"]) == [{"module_id": "module_001", "node_ids": ["d"]}]
    # Nhiều đích: hợp tổ tiên.
    assert [m["node_ids"] for m in target_modules(modules, edges, ["c", "f"])] == [["a", "d", "b"], ["c", "f"]]
