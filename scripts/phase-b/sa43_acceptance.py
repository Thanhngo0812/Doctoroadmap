"""SA-43: one paid initial generation shared by the two repair temperatures.

Default: inspect the pinned plan, zero network calls. An explicit --allow-spend
and a hard HTTP-attempt budget are required to execute it. --replay never calls
the network. Recorded prompts and responses stay in an isolated development store.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import replace
from pathlib import Path
from time import perf_counter

from doc2roadmap.application.phase_b.lectures import LectureUseCase, _assemble
from doc2roadmap.composition_phase_b import PhaseBRuntime
from doc2roadmap.domain.phase_b_limits import BSettings, context_hash
from doc2roadmap.infrastructure.artifacts.phase_b_store import JsonPhaseBStore, InMemoryPhaseBStore
from doc2roadmap.infrastructure.llm.phase_b import RecordingToolModel, ReplayToolModel

from sa29_acceptance import BudgetGate, install_budget_gate


ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / 'report/pha-b2-sa43-plan-2026-10-18.json'
RECORDINGS = ROOT / 'artifacts/phase_b/recordings/sa43-20261018'
STORE = ROOT / 'artifacts/phase_b/sa43-20261018.json'
RESULT = ROOT / 'tmp/phaseb-sa43-live-20261018.json'


class SharedFirstModel:
    """Capture one first attempt, replay it exactly in the second comparison arm."""
    def __init__(self, delegate, shared, *, reuse=False):
        self.delegate, self.shared, self.reuse = delegate, shared, reuse
        self.model_id = delegate.model_id
        self.calls = 0
        self._replaying = bool(getattr(delegate, 'is_replay', False))

    @property
    def is_replay(self):
        return self._replaying

    def start_session(self, system_prompt):
        first = self.calls == 0
        self.calls += 1
        self._replaying = bool((first and self.reuse) or getattr(self.delegate, 'is_replay', False))
        if first and self.reuse:
            if self.shared.get('system_prompt') != system_prompt:
                raise ValueError('comparison arms must share the exact first system prompt')
            return SharedSession(None, self.shared, replay=True)
        session = self.delegate.start_session(system_prompt)
        if first:
            self.shared['system_prompt'] = system_prompt
            return SharedSession(session, self.shared)
        return session


class SharedSession:
    def __init__(self, delegate, shared, *, replay=False):
        self.delegate, self.shared, self.replay = delegate, shared, replay
        self.last_usage = {}
        self.last_ttft_ms = None
        self.last_finish_reason = None

    def stream_json(self, prompt, *, response_schema, temperature=None, transport_retries=None, timeout_seconds=None):
        request = {'prompt': prompt, 'schema': response_schema, 'temperature': temperature}
        if self.replay:
            if request != self.shared.get('request'):
                raise ValueError('comparison arms must share the exact first request')
            self.last_usage = self.shared.get('usage', {})
            self.last_ttft_ms = self.shared.get('ttft_ms')
            self.last_finish_reason = self.shared.get('finish_reason')
            yield from self.shared.get('chunks', [])
            if self.shared.get('error'):
                error = self.shared['error']
                if error['type'] == 'TimeoutError':
                    raise TimeoutError(error['message'])
                if error['type'] in {'OSError', 'ConnectionError'}:
                    raise OSError(error['message'])
                raise RuntimeError(error['message'])
            return
        self.shared.update(request=request, chunks=[])
        started = perf_counter()
        try:
            for chunk in self.delegate.stream_json(prompt, response_schema=response_schema, temperature=temperature,
                                                  transport_retries=transport_retries, timeout_seconds=timeout_seconds):
                self.shared['chunks'].append(chunk)
                yield chunk
        except Exception as error:
            self.shared['error'] = {'type': type(error).__name__, 'message': str(error)}
            raise
        finally:
            self.last_usage = dict(getattr(self.delegate, 'last_usage', {}))
            self.last_ttft_ms = getattr(self.delegate, 'last_ttft_ms', None)
            self.last_finish_reason = getattr(self.delegate, 'last_finish_reason', None)
            self.shared.update(usage=self.last_usage, ttft_ms=self.last_ttft_ms,
                               finish_reason=self.last_finish_reason,
                               elapsed_ms=round((perf_counter() - started) * 1000))


def _delegate(runtime, path, prompt_hash, *, replay):
    if replay:
        if not path.exists():
            # A successful shared first generation needs no second-arm session.
            class NoRemainingCalls:
                model_id = runtime.b_settings.model_id
                is_replay = True
                def start_session(self, *_):
                    raise AssertionError('recorded comparison has no paid repair session')
            return NoRemainingCalls()
        return ReplayToolModel(path, prompt_hash=prompt_hash)
    return RecordingToolModel(runtime.model('lecture'), path, prompt_hash=prompt_hash)


def execute(plan, *, replay=False, cap_usd=.50):
    if not replay and any(path.exists() for path in (STORE, RESULT, RECORDINGS)):
        raise FileExistsError('SA-43 outputs already exist; use --replay instead of spending twice')
    runtime = PhaseBRuntime(mode='gemini' if not replay else 'offline', allow_spend=not replay,
                            store_path=ROOT / 'tmp/sa43-runtime-unused-store.json')
    if not replay and runtime.settings.llm_transport != 'vertex':
        raise ValueError('reviewed SA-43 plan requires the configured Vertex transport')
    runtime.record_dir = None  # Only the explicitly named per-arm recorders below.
    store = InMemoryPhaseBStore() if replay else JsonPhaseBStore(STORE)
    gate = BudgetGate(cap_usd)
    original_transport = install_budget_gate(gate) if not replay else None
    rows = []
    try:
        for index, operation in enumerate(plan['rows']):
            graph = runtime.graph(operation['doc_id'], operation['graph_version'])
            context = _assemble(graph, operation['node_id'], runtime.b_settings)[0]
            if not context.get('bridge_candidates'):
                raise ValueError('pinned concept no longer has a quoted prerequisite')
            shared = {}
            arms = []
            for temperature in (0.0, 1.0):
                before = len(store.usage_rows())
                settings = replace(BSettings(), lecture_retry_temperature=temperature)
                path = RECORDINGS / f'{index:02d}-repair-{int(temperature)}.json'
                fixture_hash = context_hash(['SA-43', operation, temperature])
                model = SharedFirstModel(_delegate(runtime, path, fixture_hash, replay=replay), shared,
                                         reuse=temperature == 1.0)
                events = []
                result = LectureUseCase(model, store, settings=settings).make(
                    graph.doc_id, graph.graph_version, graph, operation['node_id'],
                    allow_spend=True, on_event=events.append)
                ledger = store.usage_rows()[before:]
                billed = [r for r in ledger if r.get('purpose') == 'lecture']
                validations = [r for r in ledger if r.get('purpose') == 'lecture_validation']
                arms.append({'repair_temperature': temperature, 'result': result,
                             'timing_kind': 'shared-first replay plus repair' if temperature else 'measured complete click',
                             'calls': len(billed), 'new_cost_usd': sum(r.get('cost_usd', 0) for r in billed),
                             'validation': validations,
                             'emitted_items': sum(e.get('event') == 'item' for e in events)})
                if not replay:
                    RESULT.parent.mkdir(parents=True, exist_ok=True)
                    RESULT.write_text(json.dumps({'plan': plan, 'completed': rows,
                        'current': {'operation': operation, 'arms': arms},
                        'reserved_usd': gate.reserved, 'http_attempts': gate.attempts},
                        ensure_ascii=False, indent=2), encoding='utf-8')
            rows.append({'operation': operation, 'shared_first': shared, 'arms': arms})
            print(json.dumps({'completed': len(rows), 'doc_id': graph.doc_id,
                              'statuses': [a['result']['status'] for a in arms],
                              'reserved_usd': gate.reserved}), flush=True)
    finally:
        if original_transport is not None:
            from doc2roadmap.infrastructure.llm import phase_b
            phase_b.urlopen = original_transport
    ledger = store.usage_rows()
    result = {'plan': plan, 'completed': rows, 'replayed': replay,
              'http_attempts': gate.attempts, 'reserved_usd': gate.reserved,
              'new_cost_usd': sum(r.get('cost_usd', 0) for r in ledger), 'usage_rows': ledger}
    output = ROOT / 'tmp/phaseb-sa43-replay-20261018.json' if replay else RESULT
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--allow-spend', action='store_true')
    mode.add_argument('--replay', action='store_true')
    parser.add_argument('--cap-usd', type=float, default=.50)
    args = parser.parse_args()
    if not 0 < args.cap_usd <= .50:
        raise ValueError('SA-43 hard cap must be in (0, 0.50] USD')
    plan = json.loads(PLAN.read_text(encoding='utf-8'))
    if not args.allow_spend and not args.replay:
        print(json.dumps({'dry_run': True, 'network_calls': 0, 'plan': str(PLAN),
                          'first_calls': 12, 'max_logical_calls': 36,
                          'estimate_usd': plan['max_logical_estimate_usd'], 'cap_usd': args.cap_usd}))
        return
    result = execute(plan, replay=args.replay, cap_usd=args.cap_usd)
    print(json.dumps({'completed': len(result['completed']), 'new_cost_usd': result['new_cost_usd'],
                      'http_attempts': result['http_attempts'], 'replayed': args.replay}))


if __name__ == '__main__':
    main()
