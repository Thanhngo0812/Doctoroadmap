import json
import random
from types import SimpleNamespace
from types import MethodType

from doc2roadmap.application.phase_b.documents import DocumentUseCase
from doc2roadmap.application.phase_b.quiz import QuizUseCase
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.domain.source_labels import SourceRegistry
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore


def test_document_scope_remap_reads_configured_jaccard_threshold():
    graph = RoadmapGraph(module_count=6, nodes_per_module=1)
    scope = {'kind': 'module', 'node_ids': ['n0_0', 'n1_0'],
             'module_id_at_creation': 'old', 'graph_version_at_creation': 0}
    low = DocumentUseCase(None, InMemoryPhaseBStore(), settings=BSettings(scope_remap_min_jaccard=.5))
    high = DocumentUseCase(None, InMemoryPhaseBStore(), settings=BSettings(scope_remap_min_jaccard=.6))
    narrow = low.create('dev', 1, graph, 'Tóm tắt', scope, owner='alice', dry_run=True)
    broad = high.create('dev', 1, graph, 'Tóm tắt', scope, owner='alice', dry_run=True)
    assert narrow['scope']['module_ids'] == ['m0']
    assert broad['failure']['reason_code'] == 'scope_too_large'
from doc2roadmap.infrastructure.llm.phase_b_demo import DemoModel


class RoadmapGraph:
    doc_id = "dev"
    graph_version = 1

    def __init__(self, module_count=4, nodes_per_module=3):
        self.nodes = {}
        self.learnable_nodes = self.nodes
        self.modules = {}
        self.chunks = {}
        for module_index in range(module_count):
            module_id = f"m{module_index}"
            node_ids = []
            for node_index in range(nodes_per_module):
                node_id = f"n{module_index}_{node_index}"
                chunk_id = f"c{module_index}_{node_index}"
                name = f"Khái niệm {module_index} {node_index}"
                text = f"{name} được định nghĩa bằng thuộc tính {module_index + node_index + 1}."
                self.nodes[node_id] = {
                    "node_id": node_id, "name": name, "learnable": True,
                    "module_id": module_id, "module_order": node_index,
                    "teaching_chunk_ids": [chunk_id],
                    "anchor": {"chunk_id": chunk_id, "sentence": text},
                }
                self.chunks[chunk_id] = SimpleNamespace(
                    chunk_id=chunk_id, text=text, page=module_index + 1,
                    char_start=0, char_end=len(text), section_path=[f"M{module_index}"],
                    order_index=module_index * nodes_per_module + node_index, role="noi_dung",
                )
                node_ids.append(node_id)
            self.modules[module_id] = {
                "module_id": module_id, "index": module_index,
                "title": f"Module {module_index}", "node_ids": node_ids,
            }
        self.payload = {"sequence": list(self.nodes), "doc_id": self.doc_id}

    def new_source_registry(self):
        return SourceRegistry(self.chunks.values())

    def lookup_concept(self, _query):
        return {"matches": []}

    def why_here(self, _node_id, **_kwargs):
        return {"prerequisites": []}

    def get_media(self, _node_id):
        return []

    def traverse(self, *_args, **_kwargs):
        return {"edges": []}


def test_roadmap_quiz_prefers_learned_nodes_and_spreads_selection_by_module():
    graph = RoadmapGraph(module_count=4)

    class Progress:
        marked = []

        def get_progress(self, owner, doc_id):
            assert (owner, doc_id) == ("alice", "dev")
            return {"nodes": {
                "n0_0": {"state": "learned", "source": "learner"},
                "n0_1": {"state": "learned", "source": "learner"},
                "n2_0": {"state": "learned", "source": "quiz"},
                "n3_1": {"state": "learned", "source": "learner"},
            }}

        def mark_quiz_correct(self, owner, doc_id, node_ids):
            self.marked.append((owner, doc_id, node_ids))

    progress = Progress()
    use_case = QuizUseCase(graph, InMemoryPhaseBStore(), progress_use_case=progress,
                           settings=BSettings(quiz_roadmap_max_items=10), rng=random.Random(3))
    def bank(self, _doc_id, _module_id, concept, _allow_spend, _level, *, owner=None):
        return [{"item_id": f"q-{concept['node_id']}", "concept_id": concept["node_id"],
                 "stem": f"Chọn đúng cho {concept['node_id']}.", "options": [
                     {"option_id": "a", "text": "Đúng", "is_correct": True},
                     {"option_id": "b", "text": "Sai một", "is_correct": False},
                     {"option_id": "c", "text": "Sai hai", "is_correct": False},
                 ], "evidence": [], "explanation": "ẩn", "checks": {} }], {}
    use_case._bank = MethodType(bank, use_case)
    result = use_case.make_quiz("dev", owner="alice", scope={"kind": "roadmap"}, seed="same-seed")

    selected = result["node_ids"]
    assert {"n0_0", "n0_1", "n2_0", "n3_1"} <= set(selected)
    assert result["home_scope"] == {"kind": "roadmap"}
    assert result["origin"] == "button"
    assert result["session_id"] is None
    assert result["created_at"]
    assert result["contract_version"] == "quiz-3"
    assert len(result["items"]) <= 10
    assert all("answer" not in item and "explanation" not in item for item in result["items"])
    assert len({graph.nodes[node_id]["module_id"] for node_id in selected}) == 4
    second = use_case.make_quiz("dev", owner="alice", scope={"kind": "roadmap"}, seed="same-seed")
    assert set(second["node_ids"]) == set(selected)
    attempt = use_case.store.get_record("quiz_attempt", result["attempt_id"])
    item = result["items"][0]
    private = attempt["_private"][item["item_id"]]
    correct = next(option for option in private["options"] if option["is_correct"])
    use_case.submit(result["attempt_id"], "alice", {item["item_id"]: correct["option_id"]})
    assert progress.marked == [("alice", "dev", [item["concept_id"]])]


def test_document_scope_over_five_modules_fails_before_calling_model():
    graph = RoadmapGraph(module_count=6, nodes_per_module=1)

    class NoModel:
        def ask_json(self, *_args, **_kwargs):
            raise AssertionError("scope validation must precede model calls")

    result = DocumentUseCase(NoModel(), InMemoryPhaseBStore(),
                             settings=BSettings(document_max_modules=5)).create(
        "dev", 1, graph, "Tổng hợp", {"module_ids": list(graph.modules)},
        owner="alice", allow_spend=True,
    )

    assert result["status"] == "failed"
    assert result["failure"]["reason_code"] == "scope_too_large"
    assert result["usage"] == {}
    assert result["origin"] == "button"
    assert result["session_id"] is None
    assert result["home_scope"] == {"kind": "roadmap"}


def test_five_module_document_is_allowed_and_stores_button_metadata():
    graph = RoadmapGraph(module_count=5, nodes_per_module=1)

    from sa64_support import FakeModel
    Model = FakeModel  # SA-67: document-3 streams Markdown

    result = DocumentUseCase(Model(), InMemoryPhaseBStore(), settings=BSettings(document_max_modules=5)).create(
        "dev", 1, graph, "Tổng hợp", {"module_ids": list(graph.modules)}, owner="alice", allow_spend=True,
        home_scope={"kind": "roadmap"}, origin="button",
    )

    assert result["status"] == "ready"
    assert result["contract_version"] == "document-3"
    assert result["home_scope"] == {"kind": "roadmap"}
    assert result["origin"] == "button"
    assert result["session_id"] is None
    assert set(result["node_ids"]) == set(graph.nodes)
    assert result["created_at"]


def test_spend_guard_checks_each_quiz_call_and_keeps_cloze_when_denied():
    # Cloze needs two distinct local distractors when the verifier/generator is
    # denied; one-concept fixtures cannot produce a ready question.
    graph = RoadmapGraph(module_count=1, nodes_per_module=3)

    class Guard:
        checks = []

        def check(self, purpose, estimated_usd, owner=None):
            self.checks.append((purpose, estimated_usd, owner))
            return False

    class NoModel:
        def ask_json(self, *_args, **_kwargs):
            raise AssertionError("a denied system-budget call must not reach the model")

    guard = Guard()
    result = QuizUseCase(graph, InMemoryPhaseBStore(), NoModel(), spend_guard=guard).make_quiz(
        "dev", "m0", "alice", n=1, allow_spend=True,
    )

    assert result["ready_count"] == 1
    assert guard.checks and guard.checks[0][0] == "quiz_gen"
    assert all(row[2] is None for row in guard.checks)
    assert result["usage"]["usd"] == 0


def test_document_spend_guard_denial_is_a_zero_call_daily_limit():
    graph = RoadmapGraph(module_count=1, nodes_per_module=1)

    class Guard:
        checks = []

        def check(self, purpose, estimated_usd, owner=None):
            self.checks.append((purpose, estimated_usd, owner))
            return False

    class NoModel:
        def ask_json(self, *_args, **_kwargs):
            raise AssertionError("a denied learner-budget call must not reach the model")

    guard = Guard()
    result = DocumentUseCase(NoModel(), InMemoryPhaseBStore(), spend_guard=guard).create(
        "dev", 1, graph, "Tổng hợp", "m0", owner="alice", allow_spend=True,
    )

    assert result["status"] == "failed"
    assert result["failure"]["reason_code"] == "daily_limit"
    assert guard.checks == [("document", guard.checks[0][1], "alice")]
    assert result["usage"] == {}


def test_demo_model_uses_new_module_scope_shape_and_roadmap_tool_scope():
    tools = [
        {"name": "make_quiz"},
        {"name": "make_document"},
    ]
    session = DemoModel().start_session("", tools)
    module = session.stream([{"text": json.dumps({"scope": {
        "kind": "module", "module": {"module_id": "m0", "node_ids": ["n0_0"]}},
        "question": "tạo quiz", "concepts": []}, ensure_ascii=False)},
        {"role": "user", "text": "tạo quiz"}])
    assert next(module).args["scope"] == "m0"

    roadmap = session.stream([{"text": json.dumps({"scope": {
        "kind": "roadmap", "modules": []}, "question": "tạo đề cương", "concepts": []},
        ensure_ascii=False)}, {"role": "user", "text": "tạo đề cương"}])
    assert next(roadmap).args["scope"] == "roadmap"


def test_roadmap_string_scope_resolves_for_quiz_and_documents():
    graph = RoadmapGraph(module_count=2, nodes_per_module=1)
    quiz = QuizUseCase(graph, InMemoryPhaseBStore())
    assert quiz._resolve_scope("roadmap") == (None, None)

    from doc2roadmap.application.phase_b.documents import _scope_nodes
    nodes, modules = _scope_nodes(graph, "roadmap")
    assert set(nodes) == set(graph.nodes)
    assert modules == list(graph.modules)
