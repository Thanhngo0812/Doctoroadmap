"""SA-68: the message of `quiz-3` on the real xstk-ch3-1 v68 graph (read only, 0 USD). Skipped when the artifacts are absent.

The models are scripts; what is asserted is the message the generator and the solver received."""
import os
from pathlib import Path

import pytest

from doc2roadmap.application.phase_b.quiz import QuizUseCase
from doc2roadmap.composition_phase_b import PhaseBRuntime
from doc2roadmap.config import Settings
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore

from sa64_support import FakeClock, FakePages
from sa68_support import Generator, Reverse, Solver, raw_item

ARTIFACTS = Path(os.environ.get("SA64_REAL_ARTIFACTS", Path(__file__).resolve().parents[3] / "artifacts"))
pytestmark = pytest.mark.skipif(not (ARTIFACTS / "graph" / "xstk-ch3-1").exists(), reason="no real artifacts here")
CONCEPT = "Hệ số tương quan mẫu"


@pytest.fixture(scope="module")
def made():
    runtime = PhaseBRuntime(settings=Settings(artifact_dir=ARTIFACTS, _env_file=None), mode="offline",
                            store=InMemoryPhaseBStore())
    graph = runtime.graph("xstk-ch3-1", 68)
    node_id = next(key for key, node in graph.nodes.items() if (node.get("display_name") or node.get("name")) == CONCEPT)
    generator = Generator(lambda concept, lap: [raw_item(f"{concept} câu {k}", correct=k, bloom=b, labels=("S2",))
                                                for k, b in enumerate(("nho", "hieu", "van_dung"))])
    solver = Solver(generator)
    pages = FakePages({page: b"jpeg-%d" % page for page in range(1, 60)})
    use = QuizUseCase(graph, InMemoryPhaseBStore(), generator, verifier_model=solver, settings=BSettings(), rng=Reverse(),
                      page_images=pages, clock=FakeClock())
    quiz = use.make_quiz(graph.doc_id, None, "alice", node_ids=[node_id], allow_spend=True)
    return graph, quiz, generator, solver, use


def test_generator_message_has_the_definition_the_raw_formula_text_and_two_pages(made):
    _, quiz, generator, _, _ = made
    call = generator.calls[0]
    assert quiz["ready_count"] == 1 and len(generator.calls) == 1
    assert call.prompt.startswith(f"Khái niệm: {CONCEPT}\nCác khái niệm khác cùng module: ")
    assert "Định nghĩa . Hệ số thể hiện cường độ và chiều hướng của quan hệ tương quan giữa hai dấu hiệu X và Y" in call.prompt
    assert "0,8165" in call.prompt
    assert [page for page, _ in call.images] == [16, 17]
    assert "Ảnh các trang sách được đính kèm" in call.system


def test_solver_gets_the_same_material_and_pages_and_the_questions_after_it(made):
    _, _, generator, solver, _ = made
    call = solver.calls[0]
    assert call.prompt.startswith(generator.calls[0].prompt)
    assert [page for page, _ in call.images] == [16, 17]
    assert (call.thinking_level, call.temperature) == ("medium", 0.0)


def test_evidence_of_the_kept_question_is_the_definition_passage_of_the_book(made):
    graph, quiz, _, _, use = made
    result = use.submit(quiz["attempt_id"], "alice", {})
    (evidence,) = result["results"][0]["evidence"]
    assert (evidence["label"], evidence["page"]) == ("S2", 17)
    assert "Hệ số thể hiện cường độ và chiều hướng" in graph.chunks[evidence["chunk_id"]].text
