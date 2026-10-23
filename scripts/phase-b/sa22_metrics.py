"""SA-22 automatic measures (report 5.4), computed from tmp/sa22/ only. Zero network calls.

Writes tmp/sa22/metrics.json and tmp/sa22/metrics.md (tables for the report).
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sa22_common import OUT, STORE_PATH, load_graphs, use_case  # noqa: E402
from sa22_run import result_path  # noqa: E402
from doc2roadmap.infrastructure.artifacts.phase_b_store import JsonPhaseBStore  # noqa: E402

# Reason -> rule of report 3.4, in the order QuizUseCase applies them (normalize first, then local rules, then the verifier).
RULE_OF = {
    'normalize.malformed_candidate': 'Q1', 'normalize.concept_mismatch': 'Q1', 'normalize.option_count': 'Q1',
    'normalize.correct_source_label': 'Q2', 'normalize.correct_quote': 'Q2',
    'normalize.distractor_source_label': 'Q4', 'normalize.distractor_quote': 'Q4', 'normalize.from_source_mismatch': 'Q4',
    'normalize.distractor_same_chunk': 'Q4',
    'local.option_count_or_duplicate': 'Q1', 'local.option_substring_overlap': 'Q3', 'local.distractor_is_target_alias': 'Q3',
    'local.answer_too_long': 'Q5', 'local.negative_stem': 'Q5', 'local.absolute_option': 'Q5',
    'local.target_name_in_stem': 'Q5', 'local.answer_cue': 'Q5',
    'local.markup_or_source_label': 'Q7', 'local.visual_or_formula_reference': 'Q6', 'local.formula_option': 'Q6',
    'local.explanation_or_why_wrong_too_long': 'Q1', 'local.unsupported_math': 'K5 (ký hiệu toán)',
    'local.language_ratio': 'Q7', 'local.duplicate_variant': 'Q8', 'local.same_bloom_same_answer': 'Q8',
}
FUNNEL = ['Q1', 'Q2', 'Q4', 'Q3', 'Q5', 'Q6', 'K5 (ký hiệu toán)', 'Q7', 'Q8', 'Verifier']
VERIFIER_REASONS = ['verifier.wrong_choice', 'verifier.invalid_question', 'verifier.quote_not_found',
                    'verifier.distractor_inconclusive', 'verifier.distractor_supported',
                    'verifier.distractor_verdict_missing_or_not_wrong', 'verifier.missing_result', 'verifier.unknown_item']


def percentile(values, q):
    if not values:
        return None
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, max(0, round(q * (len(ordered) - 1))))]


def pct(a, b):
    return None if not b else round(100 * a / b, 1)


def main():
    plan = json.loads((OUT / 'plan.json').read_text(encoding='utf-8'))
    cloze = json.loads((OUT / 'cloze.json').read_text(encoding='utf-8'))
    graphs = load_graphs()
    store = JsonPhaseBStore(STORE_PATH)
    usage_rows = store.usage_rows()
    results, missing = {}, 0
    for doc_id, book in plan['books'].items():
        for node_id in book['concepts_in_chosen_modules']:
            path = result_path(doc_id, node_id, OUT / 'results')
            if path.exists():
                results[node_id] = json.loads(path.read_text(encoding='utf-8'))
            else:
                missing += 1
    # ---------- funnel Q1-Q8
    reasons = Counter()
    accepted_n = variant_cap = 0
    for row in results.values():
        accepted_n += len(row['accepted'])
        for c in row['captured']:
            if c['reason'] == 'local.variant_cap':
                variant_cap += 1
            else:
                reasons[c['reason']] += 1
    candidates = accepted_n + variant_cap + sum(reasons.values())
    verifier_reached = accepted_n + variant_cap + sum(n for r, n in reasons.items() if r.startswith('verifier.'))
    failed_by_rule = Counter()
    for reason, n in reasons.items():
        failed_by_rule['Verifier' if reason.startswith('verifier.') else RULE_OF.get(reason, 'other:' + reason)] += n
    funnel, reached = [], candidates
    for rule in [*FUNNEL, *[r for r in failed_by_rule if r not in FUNNEL]]:
        failed = failed_by_rule.get(rule, 0)
        funnel.append({'rule': rule, 'reached': reached, 'failed': failed, 'pass_pct': pct(reached - failed, reached)})
        reached -= failed
    # ---------- verifier
    verifier_reasons = {r: reasons.get(r, 0) for r in VERIFIER_REASONS}
    verifier_rejected = sum(verifier_reasons.values())
    # ---------- coverage
    coverage = {}
    for doc_id, book in plan['books'].items():
        nodes = book['concepts_in_chosen_modules']
        llm = {n for n in nodes if n in results and results[n]['accepted']}
        clz = {n for n in nodes if cloze.get(n, {}).get('items')}
        targets = set(book['targets'])
        coverage[doc_id] = {'concepts': len(nodes), 'llm': len(llm), 'cloze': len(clz), 'either': len(llm | clz),
                            'targets': len(targets), 'targets_llm': len(targets & llm), 'targets_cloze': len(targets & clz)}
    total_cov = {k: sum(c[k] for c in coverage.values()) for k in ('concepts', 'llm', 'cloze', 'either', 'targets',
                                                                  'targets_llm', 'targets_cloze')}
    # ---------- Bloom recorded by the system
    bloom_accepted = Counter(item.get('bloom') for r in results.values() for item in r['accepted'])
    bloom_rejected = Counter()
    seen = set()
    for r in results.values():
        for c in r['captured']:
            if c['stage'] == 'verifier' and c['item'] and c['item']['item_id'] not in seen:
                seen.add(c['item']['item_id'])
                bloom_rejected[c['item'].get('bloom')] += 1
    bloom_cloze = Counter(item.get('bloom') for v in cloze.values() for item in v['items'])
    # ---------- duplicates
    dup_q8 = reasons.get('local.duplicate_variant', 0) + reasons.get('local.same_bloom_same_answer', 0)
    first_items = defaultdict(list)
    for node_id, r in results.items():
        if r['accepted']:
            first_items[(r['doc_id'], r['module_id'])].append((node_id, r['accepted'][0]))
    cross_pairs = cross_dups = 0
    for (doc_id, _), rows in first_items.items():
        helper = use_case(graphs[doc_id], None, None, 'metrics', llm=False)
        for i in range(len(rows)):
            for j in range(i + 1, len(rows)):
                cross_pairs += 1
                cross_dups += helper._duplicate(rows[i][1], rows[j][1])
    # ---------- tokens, USD, time (usage rows of the main run; rows of the trial are counted apart)
    module_of = {}
    for doc_id, graph in graphs.items():
        for module_id, module in graph.modules.items():
            for node_id in module['node_ids']:
                module_of[node_id] = (doc_id, module_id)
    chosen_nodes = {n for b in plan['books'].values() for n in b['concepts_in_chosen_modules']}
    per_module = defaultdict(lambda: {'usd': 0.0, 'in': 0, 'out': 0, 'calls': 0})
    book_usd = Counter()
    gen_ms, ver_ms = [], []
    tot = {'usd': 0.0, 'in': 0, 'out': 0, 'thought': 0, 'calls': 0, 'failed_calls': 0, 'failed_usd': 0.0}
    trial_usd = other_usd = 0.0
    for row in usage_rows:
        cost = float(row.get('cost_usd', 0) or 0)
        node = row.get('sa22_node_id')
        if node not in chosen_nodes:
            if node in module_of:
                trial_usd += cost
            else:
                other_usd += cost
            continue
        key = module_of[node]
        slot = per_module[key]
        slot['usd'] += cost; slot['in'] += row.get('input_tokens', 0); slot['out'] += row.get('output_tokens', 0); slot['calls'] += 1
        book_usd[key[0]] += cost
        tot['usd'] += cost; tot['in'] += row.get('input_tokens', 0); tot['out'] += row.get('output_tokens', 0)
        tot['thought'] += row.get('thought_tokens', 0); tot['calls'] += 1
        if row.get('failed'):
            tot['failed_calls'] += 1; tot['failed_usd'] += cost
        elif row.get('purpose') == 'quiz_gen':
            gen_ms.append(row['elapsed_ms'])
        elif row.get('purpose') == 'quiz_verify':
            ver_ms.append(row['elapsed_ms'])
    module_usd = sorted(v['usd'] for v in per_module.values())
    bank_s = [r['elapsed_s'] for r in results.values()]
    ledger_total = sum(float(r.get('cost_usd', 0) or 0) for r in usage_rows)
    # ---------- cloze branch
    cloze_reasons = Counter(r for v in cloze.values() for r in v['rejections'])
    metrics = {
        'concepts_with_result': len(results), 'concepts_missing_result': missing,
        'result_errors': sum(r['status'] != 'ok' for r in results.values()),
        'candidates': candidates, 'accepted_first_two': accepted_n, 'variant_cap_dropped_after_pass': variant_cap,
        'funnel': funnel, 'rejection_reasons': dict(reasons.most_common()), 'verifier_reached': verifier_reached, 'verifier_rejected': verifier_rejected,
        'verifier_rejected_pct_of_reached': pct(verifier_rejected, verifier_reached),
        'verifier_reasons': verifier_reasons, 'coverage': coverage, 'coverage_total': total_cov,
        'bloom_accepted': dict(bloom_accepted), 'bloom_rejected': dict(bloom_rejected), 'bloom_cloze': dict(bloom_cloze),
        'duplicate_q8_rejected': dup_q8, 'duplicate_q8_pct_of_candidates': pct(dup_q8, candidates),
        'cross_item_pairs_same_module': cross_pairs, 'cross_item_duplicates': cross_dups,
        'tokens_usd_total': {k: (round(v, 6) if isinstance(v, float) else v) for k, v in tot.items()},
        'usd_by_book': {k: round(v, 6) for k, v in book_usd.items()},
        'usd_per_module': {'modules': len(per_module), 'min': round(module_usd[0], 6) if module_usd else None,
                           'p50': round(percentile(module_usd, .5), 6) if module_usd else None,
                           'max': round(module_usd[-1], 6) if module_usd else None,
                           'mean': round(sum(module_usd) / len(module_usd), 6) if module_usd else None},
        'usd_trial_modules': round(trial_usd, 6), 'usd_other_rows': round(other_usd, 6), 'ledger_total_usd': round(ledger_total, 6),
        'generation_ms': {'n': len(gen_ms), 'p50': percentile(gen_ms, .5), 'p95': percentile(gen_ms, .95)},
        'verifier_ms': {'n': len(ver_ms), 'p50': percentile(ver_ms, .5), 'p95': percentile(ver_ms, .95)},
        'concept_bank_seconds': {'n': len(bank_s), 'p50': percentile(bank_s, .5), 'p95': percentile(bank_s, .95)},
        'cloze': {'concepts': len(cloze), 'with_item': sum(bool(v['items']) for v in cloze.values()),
                  'rejection_reasons': dict(cloze_reasons.most_common())},
    }
    (OUT / 'metrics.json').write_text(json.dumps(metrics, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(json.dumps({k: metrics[k] for k in ('concepts_with_result', 'concepts_missing_result', 'result_errors', 'candidates',
                                              'verifier_rejected', 'verifier_rejected_pct_of_reached', 'coverage_total',
                                              'tokens_usd_total', 'ledger_total_usd', 'generation_ms', 'verifier_ms')},
                     ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
