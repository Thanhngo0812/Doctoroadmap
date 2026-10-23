"""SA-21 step 2: generate the lecture of every sample concept (plus the 2 trial concepts) for one configuration.

Configurations (all on the same sample, each in its own EMPTY JSON store under tmp/sa21/, never live.json):
  A2  design: LLM, lecture_temperature 0, stream mode. Run sequentially, so the per-concept seconds are the SA-13 measurement.
  A4  as A2 with lecture_temperature 1.0 (dataclasses.replace in sa21_common.b_settings).
  A1  ablation without the graph: the output of lectures._assemble is filtered here (prerequisites, bridge candidates, open edges,
      next_up and exercises dropped; only teaching sources kept). Product code is untouched.
  A0  citation-sentence baseline: lectures._fallback_sections (TextRank over the teaching sources), 0 USD, no network.
  A3  optional: A2 plus the images of the formulas of the teaching chunks (inlineData parts added to the request body).

Default is a dry run with zero network calls. `--allow-spend` runs for real under a hard cap: BudgetGate reserves a byte-based upper bound
before every HTTP attempt and refuses once the remaining cap or the attempt limit is reached. Results are saved concept by concept
(tmp/sa21/results/<config>/), so an interrupted run resumes without paying twice. Only gemini-3.1-flash-lite, via the configured Vertex transport.
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import doc2roadmap.application.phase_b.lectures as lectures  # noqa: E402
import doc2roadmap.infrastructure.llm.phase_b as phase_b_transport  # noqa: E402
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore  # noqa: E402,F401
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore, JsonPhaseBStore  # noqa: E402

from sa21_common import (CAP_USD, OPTIONAL_USD_LIMIT, OUT, STORE_NAMES, b_settings, chunk_formula_images, load_graphs,  # noqa: E402
                         make_runtime, read_json, result_path, write_json)
from sa29_acceptance import BudgetGate, install_budget_gate  # noqa: E402

RESULTS = OUT / 'results'
_real_assemble = lectures._assemble
_real_cache_key = lectures.lecture_cache_key
_ctx_hashes = {}
_ctx_lock = threading.Lock()
_current = threading.local()
_a3 = {'images': []}  # A3 runs one concept at a time; the request is built in another thread


class HardGate(BudgetGate):
    """BudgetGate plus a hard limit on HTTP attempts; remembers that it refused."""
    def __init__(self, cap, max_attempts):
        super().__init__(cap)
        self.max_attempts = max_attempts
        self.tripped = False

    def reserve_request(self, request):
        with self._lock:
            if self.attempts >= self.max_attempts:
                self.tripped = True
                raise PermissionError(f'SA-21 HTTP attempt limit reached ({self.max_attempts})')
        try:
            return super().reserve_request(request)
        except PermissionError:
            self.tripped = True
            raise


def spent_in(store_name):
    path = OUT / store_name
    return sum(float(r.get('cost_usd', 0) or 0) for r in JsonPhaseBStore(path).usage_rows()) if path.exists() else 0.0


_active = {'name': None, 'store': None}


def spent_all():
    """Sum over the stores; the one being written by this process is read through its live object, never from the file."""
    total = 0.0
    for name in STORE_NAMES.values():
        if name == _active['name'] and _active['store'] is not None:
            total += sum(float(r.get('cost_usd', 0) or 0) for r in _active['store'].usage_rows())
        else:
            total += spent_in(name)
    return total


def a1_assemble(graph, node_id, settings, source_registry=None):
    """Ablation without the graph: keep the teaching sources only."""
    context, skeleton, mapping = _real_assemble(graph, node_id, settings, source_registry)
    keep = {row['label'] for row in context['teaching']} | {row['label'] for row in context['extra_definitions']}
    keep.add(context['definition'].get('source'))
    context['sources'] = {label: source for label, source in context['sources'].items() if label in keep}
    context['prerequisites'] = []
    context['bridge_candidates'] = []
    context['open_edges'] = []
    context['exercise'] = []
    skeleton['prerequisites'] = []
    skeleton['next_up'] = []
    return context, skeleton, mapping


def recording_cache_key(**kwargs):
    key, ctx_hash = _real_cache_key(**kwargs)
    with _ctx_lock:
        _ctx_hashes[(kwargs['doc_id'], kwargs['node_id'])] = ctx_hash
    return key, ctx_hash


def collect_rows(store, doc_id, ctx_hash):
    rows = [r for r in store.usage_rows(doc_id) if r.get('context_hash') == ctx_hash]
    keep = ('purpose', 'cost_usd', 'input_tokens', 'output_tokens', 'thought_tokens', 'elapsed_ms', 'ttft_ms', 'generation_id',
            'generation_index', 'dropped_by_rule', 'validation_rules', 'passed', 'failure_reason', 'gate_ms', 'final_ms',
            'skeleton_ms', 'gate_to_final_ms')
    return [{k: r[k] for k in keep if k in r} for r in rows]


def run_a0(graph, node_id):
    settings = b_settings('A2')
    context, skeleton, _ = _real_assemble(graph, node_id, settings)
    sections = lectures._fallback_sections(context)
    use_case = lectures.LectureUseCase(None, InMemoryPhaseBStore(), settings=settings)
    return use_case._finish(skeleton, sections, 'ready', [], {}, 0, 'a0', 'a0', graph.doc_id)


def one(runtime, graph, config, node_id, trial, stream):
    doc_id = graph.doc_id
    events, started = [], time.perf_counter()

    def on_event(event):
        row = {'event': event.get('event'), 't_ms': round((time.perf_counter() - started) * 1000)}
        if event.get('section_kind'):
            row['section_kind'] = event['section_kind']
        events.append(row)

    error = None
    try:
        if config == 'A0':
            lecture = run_a0(graph, node_id)
        else:
            lecture = runtime.lecture(graph, node_id, on_event=on_event if stream else None)
    except PermissionError:
        raise
    except Exception as exc:  # recorded, the run goes on
        lecture, error = None, f'{type(exc).__name__}: {str(exc)[:300]}'
    wall_ms = round((time.perf_counter() - started) * 1000)
    ctx_hash = _ctx_hashes.get((doc_id, node_id))
    rows = collect_rows(runtime.store, doc_id, ctx_hash) if (runtime and ctx_hash) else []

    def first(name):
        return next((e['t_ms'] for e in events if e['event'] == name), None)

    row = {'config': config, 'doc_id': doc_id, 'node_id': node_id, 'trial': trial, 'error': error,
           'status': (lecture or {}).get('status', 'error'), 'wall_ms': wall_ms, 'events': events,
           't_skeleton_ms': first('skeleton'), 't_first_item_ms': first('item'),
           't_gate_ms': first('gate'), 't_final_ms': first('final') if first('final') is not None else
           (wall_ms if lecture and lecture.get('status') == 'ready' else None),
           'ctx_hash': ctx_hash, 'usage_rows': rows,
           'cost_usd': round(sum(float(r.get('cost_usd', 0) or 0) for r in rows if r.get('purpose') == 'lecture'), 8),
           'lecture': lecture}
    write_json(result_path(config, node_id), row)
    return row


# ---------------------------------------------------------------- A3: formula images as extra request parts

class ImageInjector(phase_b_transport.GeminiToolModel):
    """GeminiToolModel that appends the formula images of the current concept to the user message (A3)."""
    def _request(self, operation, body, **kwargs):
        images = _a3['images']
        if images:
            parts = body['contents'][0]['parts']
            parts.append({'text': 'Ảnh kèm theo là các công thức CT1, CT2, ... của đoạn dạy, theo thứ tự xuất hiện. '
                                  'Dùng ảnh để hiểu nghĩa; vẫn không chép lại công thức, chỉ dùng nhãn công thức.'})
            for image in images:
                parts.append({'inlineData': {'mimeType': 'image/png', 'data': image['png']}})
        return super()._request(operation, body, **kwargs)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', required=True, choices=['A0', 'A1', 'A2', 'A3', 'A4'])
    parser.add_argument('--allow-spend', action='store_true')
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--limit', type=int, help='at most this many concepts (smoke test)')
    args = parser.parse_args()
    config = args.config
    plan = read_json(OUT / 'plan.json')
    jobs = [(book_doc, node, False) for book_doc, book in plan['books'].items() for node in book['concepts']]
    jobs += [(info['doc_id'], node, True) for node, info in plan['trial'].items()]
    if config == 'A3':
        jobs = [j for j in jobs if (plan['trial'].get(j[1]) or plan['books'][j[0]]['concepts'][j[1]])['has_formula']]
    if not args.allow_spend and config != 'A0':
        print(json.dumps({'dry_run': True, 'network_calls': 0, 'config': config, 'concepts': len(jobs),
                          'estimate_usd_upper_all_configs': plan['estimate_usd_upper'], 'cap_usd': CAP_USD,
                          'within_cap': plan['estimate_usd_upper'] <= CAP_USD}))
        return
    graphs = load_graphs()
    if config == 'A1':
        lectures._assemble = a1_assemble
    lectures.lecture_cache_key = recording_cache_key
    runtime = None
    gate = None
    original = None
    todo = []
    for doc_id, node_id, trial in jobs:
        path = result_path(config, node_id)
        if not (path.exists() and read_json(path).get('status') in {'ready', 'no_source', 'failed'}):
            todo.append((doc_id, node_id, trial))
    if args.limit:
        todo = todo[:args.limit]
    stream = config in {'A2', 'A4', 'A1', 'A3'}
    if config != 'A0':
        store_file = OUT / STORE_NAMES[config]
        first_pass = not any((RESULTS / config).glob('*.json')) if (RESULTS / config).exists() else True
        if first_pass and store_file.exists() and JsonPhaseBStore(store_file).usage_rows():
            raise SystemExit('store is not empty at the start of a fresh pass; stop and ask')
        runtime = make_runtime(config)
        _active.update(name=STORE_NAMES[config], store=runtime.store)
        if config == 'A3':
            old = runtime.model('lecture')
            injector = ImageInjector.__new__(ImageInjector)
            injector.__dict__.update(old.__dict__)
            runtime._models['lecture'] = injector
        remaining = CAP_USD - spent_all() - 0.10
        if config == 'A3':
            remaining = min(remaining, OPTIONAL_USD_LIMIT - spent_all())
        if remaining <= 0.2:
            raise SystemExit('no budget left for this configuration; stop and ask')
        gate = HardGate(remaining, max_attempts=4 * len(todo) + 10)
        original = install_budget_gate(gate)
    done = failed = 0
    workers = 1 if config in {'A2', 'A3'} else args.workers

    def work(doc_id, node_id, trial):
        if config == 'A3':
            graph = graphs[doc_id]
            chunk_ids = [c for c in (graph.nodes[node_id].get('teaching_chunk_ids') or []) if c in graph.chunks]
            _a3['images'] = [image for chunk_id in chunk_ids for image in chunk_formula_images(graph, chunk_id)]
        return one(runtime, graphs[doc_id], config, node_id, trial, stream)

    status_path = OUT / f'run-status-{config}.json'
    try:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            futures = {}
            queue = iter(todo)

            def submit():
                job = next(queue, None)
                if job:
                    futures[pool.submit(work, *job)] = job

            for _ in range(workers):
                submit()
            while futures:
                finished = next(as_completed(list(futures)))
                futures.pop(finished)
                try:
                    row = finished.result()
                    done += 1
                    failed += row['status'] not in {'ready', 'no_source'}
                except PermissionError as exc:
                    print('STOP', exc, flush=True)
                tripped = bool(gate and gate.tripped)
                if not tripped and (config == 'A0' or spent_all() < CAP_USD - 0.15):
                    submit()
                write_json(status_path, {
                    'config': config, 'done_this_run': done, 'not_ready': failed, 'jobs_this_run': len(todo), 'stopped': tripped,
                    'reserved_upper_bound_usd': round(gate.reserved, 4) if gate else 0, 'http_attempts': gate.attempts if gate else 0,
                    'real_usd_all_stores': round(spent_all(), 6), 'at': time.strftime('%H:%M:%S')})
                if done % 10 == 0:
                    print(config, done, '/', len(todo), 'real_usd', round(spent_all(), 4), flush=True)
    finally:
        if original is not None:
            phase_b_transport.urlopen = original
    print(json.dumps({'config': config, 'done': done, 'not_ready': failed, 'stopped': bool(gate and gate.tripped),
                      'http_attempts': gate.attempts if gate else 0, 'reserved_upper_bound_usd': round(gate.reserved, 4) if gate else 0,
                      'real_usd_all_stores': round(spent_all(), 6)}))


if __name__ == '__main__':
    main()
