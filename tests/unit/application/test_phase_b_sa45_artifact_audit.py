"""SA-45 acceptance assertions; pending defects are named in repair tickets."""
from types import MethodType

import pytest

from doc2roadmap.application.phase_b.quiz import QuizUseCase
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore
from tests.unit.application.test_phase_b_b2_artifacts import RoadmapGraph
from tests.unit.application.test_phase_b_quiz import Graph


def _quiz_with_banks():
    graph = RoadmapGraph(module_count=6, nodes_per_module=3)
    quiz = QuizUseCase(graph, InMemoryPhaseBStore(), settings=BSettings())

    def bank(self, _doc_id, _module_id, concept, _allow_spend, _level, *, owner=None):
        node_id = concept['node_id']
        return [{'item_id': f'q-{node_id}', 'concept_id': node_id,
                 'stem': f'Câu riêng cho {node_id}', 'options': [
                     {'option_id': 'a', 'text': f'Đúng {node_id}', 'is_correct': True},
                     {'option_id': 'b', 'text': f'Sai B {node_id}', 'is_correct': False},
                     {'option_id': 'c', 'text': f'Sai C {node_id}', 'is_correct': False}],
                 'evidence': [], 'explanation': 'ẩn', 'checks': {}}], {}

    quiz._bank = MethodType(bank, quiz)
    return quiz


@pytest.mark.xfail(strict=True, reason='SA-46: string roadmap bypasses sampling and cap')
def test_assistant_roadmap_string_obeys_ten_question_cap():
    quiz = _quiz_with_banks()
    result = quiz.make_quiz('dev', owner='alice', scope='roadmap',
                            origin='assistant', seed='audit-45')
    assert result['ready_count'] <= 10


@pytest.mark.xfail(strict=True, reason='SA-46: string roadmap bypasses seeded sampling')
def test_assistant_roadmap_string_matches_canonical_scope_sample():
    quiz = _quiz_with_banks()
    canonical = quiz.make_quiz('dev', owner='alice', scope={'kind': 'roadmap'}, seed='audit-45')
    tool_form = quiz.make_quiz('dev', owner='alice', scope='roadmap', seed='audit-45')
    assert set(tool_form['node_ids']) == set(canonical['node_ids'])


@pytest.mark.xfail(strict=True, reason='SA-46: explicit n overrides configured roadmap cap')
def test_roadmap_with_configured_cap_also_limits_explicit_n():
    quiz = _quiz_with_banks()
    quiz.settings = BSettings(quiz_roadmap_max_items=3)
    result = quiz.make_quiz('dev', owner='alice', scope={'kind': 'roadmap'},
                            seed='audit-45', n=10)
    assert result['ready_count'] <= 3


@pytest.mark.xfail(strict=True, reason='SA-50: cloze admits missing formula references despite Q6')
def test_cloze_rejects_sentence_that_requires_a_missing_formula():
    graph = Graph()
    quote = 'Tam giác được xác định bởi biểu thức [formula] sau đây.'
    graph.chunks['ca'].text = quote
    graph.nodes['a']['anchor']['sentence'] = quote
    quiz = QuizUseCase(graph, InMemoryPhaseBStore())
    result = quiz.make_quiz('d', 'm', 'alice', node_ids=['a'])
    assert not any('[formula]' in item['stem'] for item in result['items'])


@pytest.mark.xfail(strict=True, reason='SA-50: cloze turns an incomplete definition lead-in into a question')
def test_cloze_rejects_definition_lead_in_without_its_missing_conditions():
    graph = Graph()
    quote = 'Tam giác là một hình phẳng được xác định bởi ba điều kiện sau đây:'
    graph.chunks['ca'].text = quote
    graph.nodes['a']['anchor']['sentence'] = quote
    quiz = QuizUseCase(graph, InMemoryPhaseBStore())
    result = quiz.make_quiz('d', 'm', 'alice', node_ids=['a'])
    assert not result['items']


@pytest.mark.xfail(strict=True, reason='SA-50: cloze options bypass Q3 substring exclusion')
def test_cloze_options_do_not_contain_each_other():
    graph = Graph()
    graph.nodes['b']['name'] = 'Tam giác đều'
    result = QuizUseCase(graph, InMemoryPhaseBStore()).make_quiz('d', 'm', 'alice', node_ids=['a'])
    for item in result['items']:
        texts = [option['text'].casefold() for option in item['options']]
        assert all(left not in right and right not in left
                   for index, left in enumerate(texts) for right in texts[index + 1:])
