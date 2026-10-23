"""SA-22 trial set source: a few whole modules that are NOT in the sample, run through the same branch A and the same cloze rules.

Run after sa22_run.py has finished (same store file, same hard cap of 2.0 USD for the whole ticket).
Writes tmp/sa22/results-trial/ and tmp/sa22/trial-cloze.json. `--allow-spend` is required to call the model.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sa22_common import OUT, SEEDS, load_graphs, make_runtime, use_case  # noqa: E402
from sa22_run import CAP_USD, HardGate, TaggingStore, one, real_spent, result_path  # noqa: E402
from sa29_acceptance import install_budget_gate  # noqa: E402
import doc2roadmap.infrastructure.llm.phase_b as phase_b_transport  # noqa: E402

RESULTS = OUT / 'results-trial'
PER_BOOK = {'doc-1': 2, 'xstk-ch3-1': 2, 'doc-4': 2, 'nhap-mon-ml': 1}


def choose(plan, graphs):
    chosen = {}
    for doc_id, count in PER_BOOK.items():
        graph = graphs[doc_id]
        outside = [m for m in sorted(graph.modules.values(), key=lambda m: m.get('index', 0))
                   if m['module_id'] not in plan['books'][doc_id]['modules_chosen'] and 3 <= len(m['node_ids']) <= 6]
        rng = random.Random(f"{SEEDS['trial']}:{doc_id}")
        for module in rng.sample(outside, count):
            chosen[module['module_id']] = (doc_id, [n for n in module['node_ids'] if graph.nodes[n].get('learnable', True)])
    return chosen


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--allow-spend', action='store_true')
    args = parser.parse_args()
    plan = json.loads((OUT / 'plan.json').read_text(encoding='utf-8'))
    graphs = load_graphs(set(PER_BOOK))
    modules = choose(plan, graphs)
    jobs = [(doc_id, module_id, node_id) for module_id, (doc_id, nodes) in modules.items() for node_id in nodes]
    outside_check = all(m not in plan['books'][d]['modules_chosen'] for m, (d, _) in modules.items())
    print(json.dumps({'trial_modules': len(modules), 'trial_concepts': len(jobs), 'outside_sample': outside_check}))
    cloze = {}
    for doc_id, module_id, node_id in jobs:
        graph = graphs[doc_id]
        concept = {**graph.nodes[node_id], 'node_id': node_id, 'module_order': graph.modules[module_id].get('index', 0)}
        uc = use_case(graph, None, None, f'trial-cloze:{node_id}', llm=False)
        items = uc._cloze_bank(concept, uc._context(module_id, concept))
        cloze[node_id] = {'doc_id': doc_id, 'module_id': module_id, 'items': items}
    (OUT / 'trial-cloze.json').write_text(json.dumps(cloze, ensure_ascii=False, indent=1, default=str) + '\n', encoding='utf-8')
    if not args.allow_spend:
        print('dry run: no network calls')
        return
    runtime = make_runtime()
    store = TaggingStore(runtime.store)
    pending = [j for j in jobs if not result_path(j[0], j[2], RESULTS).exists()
               or json.loads(result_path(j[0], j[2], RESULTS).read_text(encoding='utf-8')).get('status') != 'ok']
    gate = HardGate(CAP_USD - real_spent(runtime.store), max_attempts=len(pending) * 6 + 10)
    original = install_budget_gate(gate)
    try:
        with ThreadPoolExecutor(max_workers=4) as pool:
            rows = list(pool.map(lambda j: one(runtime, store, graphs[j[0]], *j, out_dir=RESULTS), pending))
    finally:
        phase_b_transport.urlopen = original
    print(json.dumps({'done': len(rows), 'errors': sum(r['status'] != 'ok' for r in rows),
                      'http_attempts': gate.attempts, 'real_usd_total': round(real_spent(runtime.store), 6),
                      'at': time.strftime('%H:%M:%S')}))


if __name__ == '__main__':
    main()
