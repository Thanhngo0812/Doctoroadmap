"""W10 through real HTTP/PostgreSQL/core; model/media/mail are always fake."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import json
import random

import pytest
from sqlalchemy import text

from test_learning_progress_w07 import w07
from wayfinder.fakes.quiz import ScriptedQuizModel
from wayfinder.fakes.lecture import ScriptedLectureModel


pytestmark = pytest.mark.postgres


@pytest.fixture
def content(w07):
    w = w07
    from wayfinder.composition import compose_sharing_service
    w.app.state.services.sharing = compose_sharing_service(w.courses.settings, w.engine, graph_loader=lambda *args: w.graph, clock=w.clock)
    generator = ScriptedQuizModel()
    verifier = ScriptedQuizModel(generator)
    document = ScriptedLectureModel([['# Tài liệu ôn tập\n\n', 'Công thức $1+1=2$. [S1] [S999]']])
    for runtime in [w.gateway.runtime, w.other_gateway.runtime]:
        runtime.model_for = lambda purpose: {'quiz_gen': generator, 'quiz_verify': verifier, 'document': document}.get(purpose)
    w.generator, w.verifier, w.document = generator, verifier, document
    w.base = f'/api/v1/courses/{w.course.id}'
    return w


def create_quiz(w, **body):
    response = w.a.client.post(w.base + '/quizzes', headers=w.a.headers,
        json={'scope': {'kind': 'module', 'module_id': 'm1'}, 'n': 1, **body})
    assert response.status_code == 201, response.text
    return response.json()


def assert_no_answers(value):
    if isinstance(value, dict):
        for key, child in value.items():
            assert not any(word in key.lower() for word in ('correct', 'answer', 'explanation', 'why_wrong', 'validation', '_private', 'public_id', 'usage'))
            assert_no_answers(child)
    elif isinstance(value, list):
        for child in value:
            assert_no_answers(child)


def test_w10_quiz_public_snapshot_has_no_answers_and_submission_preserves_shuffled_mapping(content):
    w = content
    original = w.gateway.runtime.quiz
    class Reverse(random.Random):
        def shuffle(self, rows):
            rows.reverse()
    def quiz(graph):
        case = original(graph); case.rng = Reverse(1); return case
    w.gateway.runtime.quiz = quiz
    made = create_quiz(w, owner=w.b.actor.user_id, doc_id='forged', graph_version=99)
    assert made['contract_version'] == 'quiz-3' and made['status'] == 'ready'
    assert_no_answers(made)
    item = made['items'][0]
    assert item['generator'] == 'llm' and len(item['options']) == 4
    assert item['bloom'] in {'nho', 'hieu', 'van_dung'} and '$' in item['stem']
    with w.independent_engine.connect() as c:
        stored = c.scalar(text("SELECT value FROM phase_b_record WHERE kind='quiz_attempt' AND record_id=:id"), {'id': made['attempt_id']})
    assert stored['owner'] == w.a.actor.user_id and stored['doc_id'] == 'doc-1'
    correct = next(option for option in stored['_private'][item['item_id']]['options'] if option['is_correct'])
    assert item['options'][0]['option_id'] != correct['option_id']
    path = w.base + '/quizzes/' + made['attempt_id']
    assert w.b.client.get(path).status_code == 404
    assert w.b.client.post(path + '/submit', headers=w.b.headers, json={'answers': {}}).status_code == 404
    selected = {item['item_id']: correct['option_id']}
    first = w.a.client.post(path + '/submit', headers=w.a.headers, json={'answers': selected})
    assert first.status_code == 200, first.text
    assert first.json()['correct_count'] == 1
    assert first.json()['results'][0]['explanation'] and first.json()['results'][0]['evidence']
    replay = w.a.client.post(path + '/submit', headers=w.a.headers, json={'answers': selected})
    assert replay.json() == first.json()
    conflict = w.a.client.post(path + '/submit', headers=w.a.headers, json={'answers': {}})
    assert conflict.status_code == 409
    assert_no_answers(w.a.client.get(path).json())
    assert w.a.client.get(path + '/result').json() == first.json()
    assert len(w.generator.calls) == len(w.verifier.calls) == 1


def test_w10_wrong_answer_returns_only_selected_why_wrong_and_library_score(content):
    w = content; made = create_quiz(w); item = made['items'][0]
    stored = w.phase_b.get_record('quiz_attempt', made['attempt_id'])
    wrong = next(o for o in stored['_private'][item['item_id']]['options'] if not o['is_correct'])
    response = w.a.client.post(w.base + '/quizzes/' + made['attempt_id'] + '/submit', headers=w.a.headers,
        json={'answers': {item['item_id']: wrong['option_id']}})
    assert response.status_code == 200
    assert response.json()['results'][0]['why_wrong'] == wrong['why_wrong']
    assert 'PRIVATE_SOLVER_REASON' not in response.text
    library = w.a.client.get(w.base + '/library?scope=module:m1').json()
    assert library['items'][0]['score'] == {'correct': 0, 'total': 1}


def test_w10_document_six_modules_rejected_before_model_and_eleventh_request_is_rate_limited(content):
    w = content
    for index in range(2, 7):
        mid = f'm{index}'; nid = f'n{index}'
        w.graph.nodes[nid] = {**w.graph.nodes['a'], 'node_id': nid, 'module_id': mid}
        w.graph.learnable_nodes[nid] = w.graph.nodes[nid]
        w.graph.modules[mid] = {'module_id': mid, 'index': index, 'title': mid, 'node_ids': [nid]}
    rejected = w.a.client.post(w.base + '/documents', headers=w.a.headers,
        json={'request': 'Tóm tắt', 'module_ids': ['m1', 'm2', 'm3', 'm4', 'm5', 'm6']})
    assert rejected.status_code == 422 and rejected.json()['error']['code'] == 'scope_too_large'
    assert not w.document.calls
    for _ in range(10):
        response = w.a.client.post(w.base + '/documents', headers=w.a.headers,
            json={'request': 'Tóm tắt', 'module_ids': ['m1']})
        assert response.status_code == 201, response.text
    other = w.courses.create_course(w.a.actor, doc_id='doc-1', title='Other', graph_version=8, module_count=6)
    last = w.a.client.post(f'/api/v1/courses/{other.id}/documents', headers=w.a.headers,
        json={'request': 'Tóm tắt', 'module_ids': ['m1']})
    assert last.status_code == 429 and last.json()['error']['code'] == 'rate_limited'
    assert len(w.document.calls) == 10


def test_w10_library_groups_are_independent_of_button_or_assistant_origin(content):
    w = content
    w.graph.modules['m2'] = {'module_id': 'm2', 'index': 2, 'title': 'Module B', 'node_ids': ['b']}
    w.graph.modules['m1']['node_ids'] = ['a']; w.graph.nodes['b']['module_id'] = 'm2'
    # Home A, content B: both creation sources belong to here in A and elsewhere in B.
    for origin in ['button', 'assistant']:
        raw = w.gateway.runtime.document(w.graph).create('doc-1', 8, w.graph, 'Ôn B', ['b'],
            owner=w.a.actor.user_id, origin=origin, allow_spend=True,
            home_scope={'kind': 'module', 'module_id_at_creation': 'm1', 'graph_version_at_creation': 8, 'node_ids': ['a']})
        assert raw['status'] == 'ready'
    here = w.a.client.get(w.base + '/library?scope=module:m1').json()['items']
    elsewhere = w.a.client.get(w.base + '/library?scope=module:m2').json()['items']
    assert {row['origin'] for row in here} == {row['origin'] for row in elsewhere} == {'button', 'assistant'}
    assert {row['group'] for row in here} == {'here'}
    assert {row['group'] for row in elsewhere} == {'elsewhere'}
    did = here[0]['id']
    viewed = w.a.client.get(w.base + '/documents/' + did)
    assert viewed.status_code == 200 and viewed.json()['contract_version'] == 'document-3'
    assert 'usage' not in viewed.text and 'validation' not in viewed.text and 'owner' not in viewed.json()
    assert w.b.client.get(w.base + '/documents/' + did).status_code == 404
    exported = w.a.client.get(w.base + '/documents/' + did + '/markdown')
    assert exported.status_code == 200 and '[^S1]' in exported.text and 'tr.' in exported.text


def test_w10_document_stream_is_public_and_rate_limit_fails_before_sse_headers(content):
    w = content; w.courses.settings.documents_per_hour = 1
    path = w.base + '/documents'
    headers = {**w.a.headers, 'Accept': 'text/event-stream'}
    streamed = w.a.client.post(path, headers=headers, json={'module_ids': ['m1'], 'request': 'Ôn tập'})
    assert streamed.status_code == 200 and 'text/event-stream' in streamed.headers['content-type']
    events = [json.loads(line[6:]) for line in streamed.text.splitlines() if line.startswith('data: ')]
    assert any(row.get('text') for row in events)
    assert events[-1]['document']['status'] == 'ready'
    assert all(key not in streamed.text for key in ['"owner"', '"usage"', '"validation"', 'public_id'])
    limited = w.a.client.post(path, headers=headers, json={'module_ids': ['m1']})
    assert limited.status_code == 429 and limited.json()['error']['retry_after'] > 0
    assert len(w.document.calls) == 1


def test_w10_submission_rolls_back_both_attempt_and_progress_when_core_write_fails(content, monkeypatch):
    from doc2roadmap.application.phase_b.progress import ProgressUseCase
    w = content; made = create_quiz(w); item = made['items'][0]
    stored = w.phase_b.get_record('quiz_attempt', made['attempt_id'])
    correct = next(o for o in stored['_private'][item['item_id']]['options'] if o['is_correct'])
    def broken(*args, **kwargs):
        raise RuntimeError('W10 rollback probe')
    monkeypatch.setattr(ProgressUseCase, 'mark_quiz_correct', broken)
    response = w.a.client.post(w.base + '/quizzes/' + made['attempt_id'] + '/submit', headers=w.a.headers,
        json={'answers': {item['item_id']: correct['option_id']}})
    assert response.status_code == 500
    with w.independent_engine.connect() as c:
        row = c.scalar(text("SELECT value FROM phase_b_record WHERE kind='quiz_attempt' AND record_id=:aid"), {'aid': made['attempt_id']})
        assert 'submission' not in row
        assert c.scalar(text("SELECT count(*) FROM phase_b_record WHERE kind='progress'")) == 0


def test_w10_independent_runtimes_serialize_competing_submissions(content):
    from threading import Barrier
    from wayfinder.api.errors import WebError
    w = content; made = create_quiz(w); item = made['items'][0]
    stored = w.phase_b.get_record('quiz_attempt', made['attempt_id'])
    options = stored['_private'][item['item_id']]['options']
    choices = [next(o['option_id'] for o in options if o['is_correct']), next(o['option_id'] for o in options if not o['is_correct'])]
    barrier = Barrier(2)
    def submit(pair):
        gateway, choice = pair
        barrier.wait()
        try:
            return gateway.submit_quiz(w.a.actor, w.course.id, made['attempt_id'], {item['item_id']: choice})
        except WebError as error:
            return error.code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(submit, zip([w.gateway, w.other_gateway], choices)))
    assert sum(isinstance(row, dict) for row in results) == 1 and 'conflict' in results
    winner = next(row for row in results if isinstance(row, dict))
    saved = w.other_gateway.get_quiz_result(w.a.actor, w.course.id, made['attempt_id'])
    assert saved == winner


def test_w10_quiz_sse_keeps_answers_private_and_revocation_denies_the_next_request(content):
    w = content
    streamed = w.b.client.post(w.base + '/quizzes', headers={**w.b.headers, 'Accept': 'text/event-stream'},
        json={'scope': {'kind': 'module', 'module_id': 'm1'}, 'n': 1})
    assert streamed.status_code == 200
    events = [json.loads(line[6:]) for line in streamed.text.splitlines() if line.startswith('data: ')]
    assert any('item' in row for row in events)
    assert_no_answers(events)
    aid = events[-1]['quiz']['attempt_id']
    assert w.b.client.get(w.base + '/quizzes/' + aid).status_code == 200
    removed = w.a.client.delete(w.base + '/members/' + w.b.actor.user_id, headers=w.a.headers)
    assert removed.status_code == 200
    assert w.b.client.get(w.base + '/quizzes/' + aid).status_code == 404
    assert w.b.client.post(w.base + '/quizzes/' + aid + '/submit', headers=w.b.headers, json={'answers': {}}).status_code == 404
