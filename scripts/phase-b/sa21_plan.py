"""SA-21 step 1, zero network calls: choose the sample (and 2 trial concepts outside it) and compute the dry-run estimate.

Sample: per book K concepts (doc-1 15, xstk 10, doc-4 15, nhap-mon-ml 5, naive-bayes 3, doc-6 2). Inside a book the concepts are
split in four cells (formula in the anchor sentence yes/no x visible prerequisite yes/no) and drawn round-robin over the cells
in a seeded order, so the rare cells are represented on purpose. Concepts without a teaching source (no_source) are excluded.
Writes tmp/sa21/plan.json. Prints counts and the estimate only.
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from doc2roadmap.application.phase_b.lectures import LectureUseCase  # noqa: E402
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore  # noqa: E402

from sa21_common import CAP_USD, OUT, PINS, SEEDS, STRATA, b_settings, classify, load_graphs, write_json  # noqa: E402

CELLS = [(True, True), (True, False), (False, True), (False, False)]


def pick(rows, k, seed):
    cells = {cell: sorted(n for n, c in rows.items() if (c['has_formula'], c['has_prereq']) == cell) for cell in CELLS}
    rng = random.Random(seed)
    order = list(CELLS)
    rng.shuffle(order)
    for cell in order:
        rng.shuffle(cells[cell])
    chosen = []
    while len(chosen) < k and any(cells.values()):
        for cell in order:
            if cells[cell] and len(chosen) < k:
                chosen.append(cells[cell].pop())
    return sorted(chosen)


def dry_estimate(graph, node_id):
    """LectureUseCase.make(dry_run=True) on the full design: upper bound of one attempt (the plan doubles it for the repair try)."""
    use_case = LectureUseCase(None, InMemoryPhaseBStore(), settings=b_settings('A2'))
    result = use_case.make(graph.doc_id, graph.graph_version, graph, node_id, dry_run=True)
    return result['estimate_usd']


def main():
    graphs = load_graphs()
    plan = {'seeds': SEEDS, 'strata': STRATA, 'pins': PINS, 'books': {}, 'trial': {}}
    rows_all = {}
    for doc_id, graph in graphs.items():
        rows = {}
        for node_id in sorted(graph.learnable_nodes):
            info = classify(graph, node_id)
            if info is not None:
                rows[node_id] = info
        rows_all[doc_id] = rows
        chosen = pick(rows, STRATA[doc_id], f"{SEEDS['sample']}:{doc_id}")
        plan['books'][doc_id] = {
            'graph_version': graph.graph_version, 'k': STRATA[doc_id], 'learnable': len(graph.learnable_nodes),
            'with_teaching': len(rows), 'no_source_excluded': len(graph.learnable_nodes) - len(rows),
            'cell_sizes': {f'formula={c[0]},prereq={c[1]}': sum(1 for r in rows.values() if (r['has_formula'], r['has_prereq']) == c)
                           for c in CELLS},
            'concepts': {n: rows[n] for n in chosen}}
    # Two trial concepts outside the sample: one with a formula (doc-1), one philosophy concept with prerequisites (doc-4).
    rng = random.Random(SEEDS['trial'])
    for doc_id, want in (('doc-1', lambda r: r['has_formula'] and r['has_prereq']),
                         ('doc-4', lambda r: r['has_prereq'] and not r['has_formula'])):
        pool = sorted(n for n, r in rows_all[doc_id].items() if want(r) and n not in plan['books'][doc_id]['concepts'])
        node_id = rng.choice(pool)
        plan['trial'][node_id] = {'doc_id': doc_id, **rows_all[doc_id][node_id]}
    one_pass = 0.0
    for doc_id, book in plan['books'].items():
        usd = sum(dry_estimate(graphs[doc_id], node_id) for node_id in book['concepts'])
        book['estimate_usd_one_pass'] = round(usd, 5)
        one_pass += usd
    for node_id, info in plan['trial'].items():
        info['estimate_usd_one_pass'] = round(dry_estimate(graphs[info['doc_id']], node_id), 5)
        one_pass += info['estimate_usd_one_pass']
    sample = sum(len(b['concepts']) for b in plan['books'].values())
    formula = sum(1 for b in plan['books'].values() for r in b['concepts'].values() if r['has_formula'])
    plan['totals'] = {'concepts': sample, 'trial_concepts': len(plan['trial']), 'with_formula': formula,
                      'with_prereq': sum(1 for b in plan['books'].values() for r in b['concepts'].values() if r['has_prereq']),
                      'llm_configs': 3}
    # A1, A2, A4 each one design call per concept; each call may be repeated once (repair try): x2. Output counted at the 2048 cap.
    plan['estimate_usd_upper'] = round(one_pass * 3 * 2, 4)
    plan['estimate_usd_a3_optional_upper'] = round(one_pass * 2 * formula / max(1, sample + 2), 4)
    plan['cap_usd'] = CAP_USD
    plan['network_calls'] = 0
    write_json(OUT / 'plan.json', plan)
    print(json.dumps({'totals': plan['totals'], 'estimate_usd_upper': plan['estimate_usd_upper'],
                      'estimate_usd_a3_optional_upper': plan['estimate_usd_a3_optional_upper'], 'cap_usd': CAP_USD,
                      'within_cap': plan['estimate_usd_upper'] <= CAP_USD, 'network_calls': 0}))
    for doc_id, book in plan['books'].items():
        print(doc_id, 'v', book['graph_version'], 'learnable', book['learnable'], 'with_teaching', book['with_teaching'],
              'cells', book['cell_sizes'], 'chosen', len(book['concepts']),
              dict(Counter((r['has_formula'], r['has_prereq']) for r in book['concepts'].values())))


if __name__ == '__main__':
    main()
