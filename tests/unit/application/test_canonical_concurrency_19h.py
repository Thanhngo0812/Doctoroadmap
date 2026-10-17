import json
from copy import deepcopy
from io import BytesIO
from threading import Condition, Lock
from time import sleep
from types import SimpleNamespace

import pytest

from doc2roadmap.application.use_cases.canonical_anchors import GENERATION, anchor_nodes, prepare_anchors
from doc2roadmap.domain.canonical import digest
from doc2roadmap.infrastructure.llm.gemini import GeminiEntityExtractor
from doc2roadmap.infrastructure.llm.rate_limit import AdaptiveModelLimiter
from tests.unit.application.test_canonical_gop import DOC, gop


def document(size=32):
    nodes = [{'node_id': f'n{index:02}', 'name': 'Không gian', 'learnable': True,
              'source_chunk_ids': ['body'], 'defining_chunk_ids': []} for index in reversed(range(size))]
    chunks = [SimpleNamespace(chunk_id='body', text='Không gian là một tập hợp có cấu trúc.',
                              order_index=0, role='noi_dung', section_path=[])]
    return nodes, chunks


class DelayedModel:
    model_id = 'delayed-anchor-fixture'

    def __init__(self, concurrency, status):
        self.concurrency, self.status = concurrency, status
        self.condition, self.active, self.peaks = Condition(), {}, {}

    def start_session(self, prompt):
        return self

    def ask_json(self, prompt, *, response_schema):
        data = json.loads(prompt)
        stage = 'anchor' if 'candidates' in data else 'prior'
        with self.condition:
            self.active[stage] = self.active.get(stage, 0) + 1
            self.peaks[stage] = max(self.peaks.get(stage, 0), self.active[stage])
            self.condition.notify_all()
            self.condition.wait_for(lambda: self.peaks[stage] >= self.concurrency, timeout=1)
        sleep((int(data['node_id'][1:]) % 4 + 1) * .005)
        with self.condition:
            self.active[stage] -= 1
        if stage == 'prior':
            value = {'node_id': data['node_id'], 'explicit_prior': True, 'reason': 'fixture'}
        else:
            candidate = data['candidates'][0]
            value = {'node_id': data['node_id'], 'status': self.status, 'anchor': candidate['cand_id'],
                     'quote': candidate['sentence'], 'reason': 'fixture'}
        return SimpleNamespace(payload=value, usage={'promptTokenCount': 3, 'candidatesTokenCount': 2})


@pytest.mark.parametrize('status', ['defined_here', 'prior_knowledge'])
def test_canonical_anchor_concurrency_reaches_configured_limit_and_is_deterministic(status):
    nodes, chunks = document()
    serial = DelayedModel(1, status)
    expected = anchor_nodes(nodes, chunks, serial, concurrency=1)
    parallel = DelayedModel(16, status)
    actual = anchor_nodes(nodes, chunks, parallel, concurrency=16)
    assert parallel.peaks['anchor'] == 16
    if status == 'prior_knowledge':
        assert parallel.peaks['prior'] == 16
    assert digest(actual) == digest(expected)
    assert [row['input']['node_id'] for row in actual[1]['anchor_decision_log']] == sorted(
        node['node_id'] for node in nodes)


def test_canonical_anchor_requests_still_pass_existing_model_limiter(monkeypatch):
    active = peak = calls = 0
    lock = Lock()
    limiter = AdaptiveModelLimiter(3, 1_000_000)
    def fake_open(request, timeout):
        nonlocal active, peak, calls
        data = json.loads(json.loads(request.data)['contents'][0]['parts'][0]['text'])
        with lock:
            active += 1
            peak = max(peak, active)
            calls += 1
        sleep(.03)
        candidate = data['candidates'][0]
        value = {'node_id': data['node_id'], 'status': 'defined_here', 'anchor': candidate['cand_id'],
                 'quote': candidate['sentence'], 'reason': 'fixture'}
        with lock:
            active -= 1
        return BytesIO(json.dumps({'candidates': [{'content': {'parts': [{'text': json.dumps(value)}]}}],
                                  'usageMetadata': {'totalTokenCount': 10}}).encode())
    monkeypatch.setattr('doc2roadmap.infrastructure.llm.gemini.urlopen', fake_open)
    model = GeminiEntityExtractor('fake-key', limiter=limiter)
    nodes, chunks = document(24)
    checked, log, _ = anchor_nodes(nodes, chunks, model, concurrency=16)
    assert calls == len(log['anchor_decision_log']) == 24
    assert all(node['teaching_status'] == 'taught' for node in checked)
    assert peak == limiter.max_observed == 3


def test_teaching_keeps_eight_node_checkpoints_and_deterministic_order():
    nodes, chunks = document(24)
    core = prepare_anchors(nodes, chunks)
    snapshots = []
    answers, log, _ = core.judge(DelayedModel(1, 'defined_here'), generation=GENERATION, concurrency=1,
                               save_checkpoint=lambda state: snapshots.append(deepcopy(state)))
    assert [len(state['answers']) for state in snapshots] == [8, 16, 24]
    assert list(answers) == [row['input']['node_id'] for row in log] == sorted(node['node_id'] for node in nodes)


def test_canonical_concurrency_reuses_the_same_cache(tmp_path):
    _, model, stage = gop(tmp_path)
    stage.reasoning.concurrency = 1
    first, reused = stage.execute(DOC)
    assert not reused
    counts = len(model.calls), len(model.anchor_calls)
    stage.reasoning.concurrency = 16
    cached, reused = stage.execute(DOC)
    assert reused and first.version == cached.version
    assert first.manifest['config_hash'] == cached.manifest['config_hash']
    assert counts == (len(model.calls), len(model.anchor_calls))
