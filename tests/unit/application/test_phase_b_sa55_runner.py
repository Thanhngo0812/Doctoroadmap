"""SA-55 runner: hard budget gate, and 0 USD replay of recorded assistant conversations."""
import importlib.util
import json
from pathlib import Path
from urllib.request import Request

import pytest

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / 'tests/fixtures/phase_b/sa55-replay-sample.json'


@pytest.fixture
def runner(monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / 'scripts/phase-b'))
    spec = importlib.util.spec_from_file_location('sa55_assistant_run_under_test', ROOT / 'scripts/phase-b/sa55_assistant_run.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def llm_request(size=2000, output=1024):
    body = json.dumps({'contents': 'x' * size, 'generationConfig': {'maxOutputTokens': output}}).encode()
    return Request('https://example.invalid/', data=body)


def test_gate_admits_inside_cap_and_counts_attempts(runner):
    gate = runner.Gate(0.50, llm_attempts=3, embedding_attempts=3)
    gate.llm(llm_request())
    assert gate.llm_attempts == 1 and gate.tripped is None


def test_gate_stops_at_http_attempt_cap_and_stays_stopped(runner):
    gate = runner.Gate(0.50, llm_attempts=2, embedding_attempts=3)
    gate.llm(llm_request())
    gate.llm(llm_request())
    with pytest.raises(PermissionError):
        gate.llm(llm_request())
    assert gate.llm_attempts == 2 and 'attempts' in gate.tripped
    with pytest.raises(PermissionError):      # once tripped nothing else goes out
        gate.embedding(Request('https://example.invalid/', data=b'{}'))
    assert gate.embed_attempts == 0


def test_gate_stops_when_actual_spend_plus_request_bound_reaches_cap(runner):
    gate = runner.Gate(0.50, llm_attempts=100, embedding_attempts=100)
    gate.assistant_usd = 0.499                # actual spend from returned tokens
    with pytest.raises(PermissionError):
        gate.llm(llm_request())
    assert gate.llm_attempts == 0 and 'usd' in gate.tripped


def test_gate_counts_embedding_estimate_against_the_same_cap(runner):
    gate = runner.Gate(0.50, llm_attempts=100, embedding_attempts=100)
    gate.embedding_usd = lambda: 0.4999
    with pytest.raises(PermissionError):
        gate.llm(llm_request())


def test_gate_refuses_a_request_it_cannot_inspect(runner):
    gate = runner.Gate(0.50, llm_attempts=5, embedding_attempts=5)
    with pytest.raises(RuntimeError):
        gate.llm(Request('https://example.invalid/', data=b'not json'))


# ------------------------------------------------------------------ replay of recorded conversations

def _needs_artifacts(plan):
    missing = [f"{doc}/v{pin['graph_version']}" for doc, pin in plan['pins'].items()
               if not (ROOT / 'artifacts/graph' / doc / f"v{pin['graph_version']}").exists()]
    if missing:
        pytest.skip(f'development artifacts not present: {missing}')


@pytest.fixture
def replay_case(runner, tmp_path, monkeypatch):
    sample = json.loads(FIXTURE.read_text(encoding='utf-8'))
    _needs_artifacts(sample['plan'])
    recordings = tmp_path / 'recordings'
    recordings.mkdir()
    for owner, files in sample['recordings'].items():
        (recordings / f'{owner}.json').write_text(json.dumps(files['model'], ensure_ascii=False), encoding='utf-8')
        (recordings / f'{owner}-tape.json').write_text(json.dumps(files['tape'], ensure_ascii=False), encoding='utf-8')
    monkeypatch.setattr(runner, 'WORK', tmp_path)
    monkeypatch.setattr(runner, 'REPLAY_RESULTS', tmp_path / 'replay.json')

    def run(expected=None):
        live = tmp_path / 'live.json'
        live.write_text(json.dumps({'turns': expected or sample['expected']}, ensure_ascii=False), encoding='utf-8')
        return runner.replay_run(sample['plan'], recordings=recordings, results_path=live)
    return run, sample, recordings


def test_replay_reproduces_the_live_turns_at_zero_usd(replay_case):
    run, sample, _ = replay_case
    result = run()
    assert result['turns_replayed'] == len(sample['expected']) == 3
    assert result['replay_usd'] == 0 and result['network_calls'] == 0
    assert result['mismatches'] == []
    # The sample must cover a refusal, a tool round trip and a focus turn, not only the happy path.
    assert {t['status'] for t in sample['expected']} >= {'insufficient_context', 'not_in_document', 'answered'}
    assert any(t['tools'] and t['rounds'] == 2 for t in sample['expected'])
    assert any(t['focus_node_id_sent'] for t in sample['expected'])


def test_replay_reports_a_turn_whose_live_result_differs(replay_case):
    run, sample, _ = replay_case
    changed = json.loads(json.dumps(sample['expected']))
    changed[1]['answer'] += ' (khác)'
    changed[2]['linked_node_ids'] = ['node_khac']
    fields = {(m['n'], m['field']) for m in run(changed)['mismatches']}
    assert (changed[1]['n'], 'answer') in fields and (changed[2]['n'], 'linked_node_ids') in fields


def test_replay_fails_loudly_when_the_recorded_model_output_changed(replay_case):
    run, sample, recordings = replay_case
    path = recordings / 'sa55-31.json'
    recorded = json.loads(path.read_text(encoding='utf-8'))
    events = recorded['sessions'][0]['calls'][0]['events']
    text = next(e for e in events if e['type'] == 'delta')
    text['text'] = 'Câu trả lời khác hẳn. [S1]'
    path.write_text(json.dumps(recorded, ensure_ascii=False), encoding='utf-8')
    fields = {m['field'] for m in run()['mismatches'] if m['n'] == 31}
    assert 'answer' in fields


def test_replay_restores_the_transport_and_makes_no_http_attempt(runner, replay_case, monkeypatch):
    from doc2roadmap.infrastructure.embedding import gemini
    from doc2roadmap.infrastructure.llm import phase_b
    before = phase_b.urlopen, gemini.urlopen
    run, _, _ = replay_case
    assert run()['network_calls'] == 0
    assert (phase_b.urlopen, gemini.urlopen) == before


def test_zero_cap_gate_installed_on_both_transports_refuses_every_request(runner):
    from doc2roadmap.infrastructure.embedding import gemini
    from doc2roadmap.infrastructure.llm import phase_b
    gate = runner.Gate(0.0, 0, 0)
    restore = runner.install_gate(gate)
    try:
        with pytest.raises(PermissionError):
            phase_b.urlopen(llm_request())
        with pytest.raises(PermissionError):
            gemini.urlopen(Request('https://example.invalid/', data=b'{}'))
    finally:
        restore()
    assert gate.tripped and gate.llm_attempts == gate.embed_attempts == 0
