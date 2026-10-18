import json
from copy import deepcopy
from types import SimpleNamespace as NS

from doc2roadmap.application.phase_b.naming import NameModulesB
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore
from test_phase_b_naming import Model, Store, upstream


def one_module_graph(*, display_name="Ma trận", description="Ma trận biểu diễn hệ số của hệ tuyến tính.",
                     alias=None, title="Tên cũ", section_id="s0"):
    graph = upstream()
    node = graph.payload["nodes"][0]
    node.update(
        name=display_name,
        display_name=display_name,
        description=description,
        aliases=[alias] if alias else [],
        teaching_chunk_ids=["c0"],
    )
    module = graph.payload["modules"][0]
    module.update(module_id="module_1", title=title, node_ids=[node["node_id"]],
                  title_section_ids=[section_id], module_dependencies=[])
    graph.payload["nodes"] = [node]
    graph.payload["modules"] = [module]
    graph.payload["sequence"] = [node["node_id"]]
    return graph


class CaptureModel:
    model_id = "gemini-3.1-flash-lite"

    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.system_prompts = []
        self.requests = []

    def start_session(self, prompt):
        self.system_prompts.append(prompt)
        return self

    def ask_json(self, prompt, *, response_schema):
        self.requests.append(json.loads(prompt))
        return NS(payload=next(self.outputs), usage={}, raw_text="")


def response(title, text, node_id):
    return {"title": title, "description": [{"text": text, "node_ids": [node_id]}]}


def test_dependency_fallback_uses_human_module_title_and_display_number():
    graph = upstream()
    graph.payload["modules"][1]["module_dependencies"] = ["m0"]
    result, _ = NameModulesB(Store(), deterministic=True).execute("book", upstream=graph)
    description = result.payload["modules"][1]["description"]
    prerequisite = next(item["text"] for item in description if item["text"].startswith("Cần trước:"))
    assert prerequisite == "Cần trước: Ma trận (module 1)."
    assert "module_" not in prerequisite and "node_" not in prerequisite


def test_generic_title_falls_back_with_generic_title_reason():
    graph = one_module_graph(
        display_name="Trị riêng",
        description="Các định nghĩa giúp xác định trị riêng.",
    )
    model = CaptureModel([response("Các định nghĩa", "Các định nghĩa giúp xác định trị riêng.", "n0a")])
    result, _ = NameModulesB(Store(), model, phase_b_store=InMemoryPhaseBStore(), allow_spend=True).execute(
        "book", upstream=graph)
    module = result.payload["modules"][0]
    assert module["title_source"] == "fallback"
    assert module["naming_flags"] == ["generic_title"]
    assert "định nghĩa" not in module["title"].casefold()


def test_same_section_duplicate_after_four_modules_gets_continuation_suffix():
    graph = upstream()
    original = graph.payload["modules"][0]
    node = graph.payload["nodes"][0]
    modules = []
    nodes = []
    for index in range(5):
        item = deepcopy(original)
        item.update(module_id=f"m{index}", index=index, title=f"Tên cũ {index}",
                        node_ids=[f"dup{index}"], title_section_ids=["s0"], module_dependencies=[], section_code="1")
        modules.append(item)
        concept = deepcopy(node)
        concept.update(node_id=f"dup{index}", module_id=f"m{index}", name="Ma trận",
                       display_name="Ma trận", description="Ma trận biểu diễn hệ tuyến tính.",
                       teaching_chunk_ids=["c0"])
        nodes.append(concept)
    graph.payload["modules"] = modules
    graph.payload["nodes"] = nodes
    graph.payload["sequence"] = [item["node_id"] for item in nodes]
    outputs = [response("Ma trận", "Ma trận biểu diễn hệ tuyến tính.", item["node_id"]) for item in nodes]
    result, _ = NameModulesB(Store(), CaptureModel(outputs), phase_b_store=InMemoryPhaseBStore(),
                             allow_spend=True).execute("book", upstream=graph)
    assert result.payload["modules"][4]["title"] == "Ma trận (tiếp)"
    assert result.payload["modules"][4]["title_source"] == "llm"


def test_cross_section_duplicate_uses_fallback_and_duplicate_flag():
    graph = upstream()
    original = graph.payload["modules"][:2]
    nodes = graph.payload["nodes"][:2]
    for index, (module, node, name, section_id) in enumerate(zip(
        original, nodes, ["Ma trận", "Hạng ma trận"], ["s0", "s1"], strict=True
    )):
        node.update(node_id=f"dup{index}", module_id=f"m{index}", name=name, display_name=name,
                    description=f"{name} biểu diễn hệ tuyến tính.", aliases=[{"name": "Ma trận"}] if index else [],
                    teaching_chunk_ids=[f"c{index}"])
        module.update(module_id=f"m{index}", title=f"Tên cũ {index}", node_ids=[f"dup{index}"],
                      title_section_ids=[section_id], module_dependencies=[], section_code=str(index + 1))
    graph.payload["modules"] = original
    graph.payload["nodes"] = nodes
    graph.payload["sequence"] = [item["node_id"] for item in nodes]
    outputs = [response("Ma trận", "Ma trận biểu diễn hệ tuyến tính.", item["node_id"]) for item in nodes]
    use_case = NameModulesB(Store(), CaptureModel(outputs), phase_b_store=InMemoryPhaseBStore(), allow_spend=True)
    _, prepared = use_case._prepare("book", upstream=graph)
    expected = prepared[1][1]["title"]
    result, _ = use_case.execute("book", upstream=graph)
    second = result.payload["modules"][1]
    assert second["title"] == expected
    assert second["title_source"] == "fallback"
    assert "duplicate" in second["naming_flags"]


def test_lowercase_initial_is_capitalized_without_changing_rest():
    graph = one_module_graph()
    model = CaptureModel([response("ma trận", "Ma trận biểu diễn hệ số của hệ tuyến tính.", "n0a")])
    result, _ = NameModulesB(Store(), model, phase_b_store=InMemoryPhaseBStore(), allow_spend=True).execute(
        "book", upstream=graph)
    assert result.payload["modules"][0]["title"] == "Ma trận"


def test_prompt_and_format_example_use_a5_sentence_not_a_name_list():
    sentence = "Ma trận biểu diễn hệ số trong một hệ tuyến tính."
    graph = one_module_graph(description=sentence)
    model = CaptureModel([response("Ma trận", sentence, "n0a")])
    NameModulesB(Store(), model, phase_b_store=InMemoryPhaseBStore(), allow_spend=True).execute("book", upstream=graph)
    prompt = model.system_prompts[0].casefold()
    example = model.requests[0]["format_example"]["description"][0]["text"]
    assert "chỉ liệt kê" not in prompt
    assert "dạy" in prompt and "làm gì" in prompt
    assert example == sentence
    assert any(word in example.casefold() for word in ("biểu diễn", "xác định", "cho phép"))
