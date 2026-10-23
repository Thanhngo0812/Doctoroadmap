"""SA-22 step 2: branch A (LLM with the blind verifier), one bank per concept of every chosen module.

Default is a dry run with zero network calls (the estimate lives in plan.json). `--allow-spend` runs for real under a hard
cap: BudgetGate reserves a byte-based upper bound before every HTTP attempt and refuses once the remaining cap or the attempt
limit is reached. Results are saved concept by concept (tmp/sa22/results/), so an interrupted run resumes without paying twice.
Only gemini-3.1-flash-lite, via the configured Vertex transport.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sa22_common import OUT, OWNER, STORE_PATH, load_graphs, make_runtime, use_case  # noqa: E402
from sa29_acceptance import BudgetGate, install_budget_gate  # noqa: E402
import doc2roadmap.infrastructure.llm.phase_b as phase_b_transport  # noqa: E402

RESULTS = OUT / 'results'
STATUS = OUT / 'run-status.json'
CAP_USD = 2.0
_current = threading.local()


class HardGate(BudgetGate):
    """BudgetGate plus a hard limit on HTTP attempts."""
    def __init__(self, cap, max_attempts):
        super().__init__(cap)
        self.max_attempts = max_attempts

    def reserve_request(self, request):
        with self._lock:
            if self.attempts >= self.max_attempts:
                raise PermissionError(f'SA-22 HTTP attempt limit reached ({self.max_attempts})')
        return super().reserve_request(request)


class TaggingStore:
    """Delegates to the real store; every usage row gets the concept being worked on by the calling thread."""
    def __init__(self, inner):
        self._inner = inner

    def __getattr__(self, name):
        return getattr(self._inner, name)

    def append_usage(self, row):
        self._inner.append_usage({**row, 'sa22_node_id': getattr(_current, 'node_id', None)})


def result_path(doc_id, node_id, out_dir=None):
    return (out_dir or RESULTS) / (hashlib.sha1(f'{doc_id}|{node_id}'.encode()).hexdigest()[:20] + '.json')


def real_spent(store):
    return sum(float(r.get('cost_usd', 0) or 0) for r in store.usage_rows())


def one(runtime, store, graph, doc_id, module_id, node_id, out_dir=None):
    _current.node_id = node_id
    concept = {**graph.nodes[node_id], 'node_id': node_id,
               'module_order': graph.modules.get(module_id, {}).get('index', 0)}
    uc = use_case(graph, runtime, store, f'{doc_id}:{node_id}')
    context = uc._context(module_id, concept)
    generated, error, bank = {}, None, []
    started = time.perf_counter()
    try:
        bank = uc._generate_bank(concept, context, generated, doc_id, owner=OWNER)
    except Exception as exc:  # recorded, the run goes on
        link = exc
        while link is not None:  # the transport turns the gate's PermissionError into RuntimeError("...failed")
            if isinstance(link, PermissionError):
                raise PermissionError(str(link)) from exc
            link = link.__cause__ or link.__context__
        error = f'{type(exc).__name__}: {str(exc)[:300]}'
    row = {'doc_id': doc_id, 'module_id': module_id, 'node_id': node_id,
           'status': 'error' if error else 'ok', 'error': error,
           'elapsed_s': round(time.perf_counter() - started, 3),
           'accepted': bank, 'captured': uc.captured,
           'usage': generated.get('usage', {})}
    out_dir = out_dir or RESULTS
    out_dir.mkdir(parents=True, exist_ok=True)
    result_path(doc_id, node_id, out_dir).write_text(json.dumps(row, ensure_ascii=False, indent=1, default=str) + '\n',
                                            encoding='utf-8')
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--allow-spend', action='store_true')
    parser.add_argument('--workers', type=int, default=6)
    parser.add_argument('--only', help='comma separated doc ids (smoke test)')
    parser.add_argument('--limit', type=int, help='at most this many concepts (smoke test)')
    args = parser.parse_args()
    plan = json.loads((OUT / 'plan.json').read_text(encoding='utf-8'))
    if not args.allow_spend:
        print(json.dumps({'dry_run': True, 'network_calls': 0, 'totals': plan['totals'],
                          'estimate_usd_upper': plan['estimate_usd_upper'], 'cap_usd': CAP_USD,
                          'within_cap': plan['estimate_usd_upper'] <= CAP_USD}))
        return
    if plan['estimate_usd_upper'] > CAP_USD:
        raise SystemExit('dry-run estimate is above the cap; stop and ask')
    docs = set(args.only.split(',')) if args.only else None
    graphs = load_graphs(docs)
    runtime = make_runtime()
    store = TaggingStore(runtime.store)
    jobs = []
    for doc_id, book in plan['books'].items():
        if docs and doc_id not in docs:
            continue
        for node_id in book['concepts_in_chosen_modules']:
            module_id = graphs[doc_id].nodes[node_id].get('module_id')
            path = result_path(doc_id, node_id)
            if not path.exists() or json.loads(path.read_text(encoding='utf-8')).get('status') != 'ok':
                jobs.append((doc_id, module_id, node_id))
    if args.limit:
        jobs = jobs[:args.limit]
    already = real_spent(runtime.store)
    gate = HardGate(CAP_USD - already, max_attempts=int(plan['totals']['calls'] * 1.5) + 20)
    original = install_budget_gate(gate)
    done = failed = 0
    stop = False
    try:
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            futures = {}
            queue = iter(jobs)

            def submit():
                job = next(queue, None)
                if job:
                    futures[pool.submit(one, runtime, store, graphs[job[0]], *job)] = job

            for _ in range(args.workers):
                submit()
            while futures:
                finished = next(as_completed(list(futures)))
                futures.pop(finished)
                try:
                    row = finished.result()
                    done += 1
                    failed += row['status'] != 'ok'
                except PermissionError as exc:
                    stop = True
                    print('STOP', exc, flush=True)
                if not stop and real_spent(runtime.store) < CAP_USD - 0.05:
                    submit()
                STATUS.write_text(json.dumps({
                    'done_this_run': done, 'errors': failed, 'jobs_this_run': len(jobs), 'stopped': stop,
                    'reserved_upper_bound_usd': round(gate.reserved, 4), 'http_attempts': gate.attempts,
                    'real_usd_so_far': round(real_spent(runtime.store), 6), 'at': time.strftime('%H:%M:%S')},
                    indent=1), encoding='utf-8')
                if done % 10 == 0:
                    print(done, '/', len(jobs), 'real_usd', round(real_spent(runtime.store), 4), flush=True)
    finally:
        phase_b_transport.urlopen = original
    print(json.dumps({'done': done, 'errors': failed, 'stopped': stop, 'http_attempts': gate.attempts,
                      'real_usd_total': round(real_spent(runtime.store), 6), 'store': STORE_PATH.name}))


if __name__ == '__main__':
    main()
