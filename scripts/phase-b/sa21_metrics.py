"""SA-21 automatic measures (report 6.3), computed from tmp/sa21/results/<config>/. Zero network calls.

Prints a JSON summary and writes tmp/sa21/metrics.json. The 2 trial concepts are left out of every measure.
Percentiles are nearest-rank (p50 = ceil(0.5 n)-th smallest, p90 = ceil(0.9 n)-th smallest).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sa21_common import CONFIGS, OUT, read_json, write_json  # noqa: E402

ITEM_KINDS = ('cau_noi', 'giai_thich', 'vi_du', 'phan_biet')


def pct(values, p):
    values = sorted(v for v in values if v is not None)
    if not values:
        return None
    return values[max(0, math.ceil(p * len(values)) - 1)]


def load(config):
    folder = OUT / 'results' / config
    rows = [read_json(p) for p in sorted(folder.glob('*.json'))] if folder.exists() else []
    return [r for r in rows if not r.get('trial')]


def effective_wait_ms(row):
    """Wall time of the call. A concept served from a cache of this store after an interrupted pass (or a negative-cache hit on a rerun)
    has a wall time of a few milliseconds; its real wait is the sum of the model calls recorded for it."""
    recorded = sum(u.get('elapsed_ms', 0) or 0 for u in row['usage_rows'] if u.get('purpose') == 'lecture')
    return recorded if row['status'] != 'ready' and recorded > row['wall_ms'] + 500 else row['wall_ms']


def kept_items(lecture):
    return [item for s in (lecture or {}).get('sections', []) if s['kind'] in ITEM_KINDS for item in s['items']]


def summarize(config, rows):
    ready = [r for r in rows if r['status'] == 'ready']
    out = {'concepts': len(rows), 'ready': len(ready), 'failed': sum(r['status'] == 'failed' for r in rows),
           'other_status': sum(r['status'] not in {'ready', 'failed'} for r in rows)}
    items = [i for r in ready for i in kept_items(r['lecture'])]
    out['items_kept'] = len(items)
    out['items_per_lecture_mean'] = round(len(items) / max(1, len(ready)), 2)
    out['chars_per_lecture_mean'] = round(sum(len(i['text']) for i in items) / max(1, len(ready)), 1)
    out['bridges_total'] = sum(len(next((s['items'] for s in r['lecture']['sections'] if s['kind'] == 'cau_noi'), [])) for r in ready)
    out['outside_example_lectures'] = sum(any(i.get('outside_document') for i in kept_items(r['lecture'])) for r in ready)
    out['outside_example_lecture_rate'] = round(out['outside_example_lectures'] / max(1, len(ready)), 4)
    out['can_soat_items'] = sum(i.get('check') == 'can_soat' for i in items)
    if config == 'A0':
        out['cost_usd'] = 0.0
        return out
    dropped, generations, k6_lectures, regenerated, truncated = {}, 0, 0, 0, 0
    final_dropped = {}
    candidates = len(items)
    k10, prereq_with_q = 0, 0
    for r in rows:
        validations = [u for u in r['usage_rows'] if u.get('purpose') == 'lecture_validation']
        if not validations:
            continue
        generations += len(validations)
        regenerated += len(validations) >= 2
        k6_lectures += any('K6' in (u.get('validation_rules') or []) for u in validations)
        last = max(validations, key=lambda u: u.get('generation_index', 0))
        for rule, count in (last.get('dropped_by_rule') or {}).items():
            final_dropped[rule] = final_dropped.get(rule, 0) + count
        for u in validations:
            for rule, count in (u.get('dropped_by_rule') or {}).items():
                dropped[rule] = dropped.get(rule, 0) + count
        truncated += 'cat_ngan' in ((r['lecture'] or {}).get('warnings') or [])
    k10 = final_dropped.get('K10', 0)
    item_drops = {rule: n for rule, n in final_dropped.items() if rule != 'K10'}
    candidates = len(items) + sum(item_drops.values())
    out.update({
        'validation_generations': generations,
        'dropped_by_rule_final_generation': dict(sorted(final_dropped.items())),
        'dropped_by_rule_all_generations': dict(sorted(dropped.items())),
        'candidate_items_final_generation': candidates,
        'item_drop_rate_by_rule': {rule: round(n / max(1, candidates), 4) for rule, n in sorted(item_drops.items())},
        'item_drop_rate_total': round(sum(item_drops.values()) / max(1, candidates), 4),
        'k10_bridges_missing': k10,
        'regenerated_lectures': regenerated, 'regenerated_rate': round(regenerated / max(1, len(rows)), 4),
        'failed_rate': round(out['failed'] / max(1, len(rows)), 4),
        'k6_lectures': k6_lectures, 'k6_lecture_rate': round(k6_lectures / max(1, len(rows)), 4),
        'k6_item_rate': round(item_drops.get('K6', 0) / max(1, candidates), 4),
        'truncated_lectures': truncated, 'truncated_rate': round(truncated / max(1, len(rows)), 4),
        'failure_reasons': {},
    })
    for r in rows:
        if r['status'] == 'failed':
            reason = (r['lecture'] or {}).get('failure', {}).get('reason_code', 'unknown')
            out['failure_reasons'][reason] = out['failure_reasons'].get(reason, 0) + 1
    costs = [r['cost_usd'] for r in rows]
    waits = [effective_wait_ms(r) / 1000 for r in rows]
    out['rows_with_wait_from_usage_rows'] = sum(effective_wait_ms(r) != r['wall_ms'] for r in rows)
    out.update({'cost_usd': round(sum(costs), 6), 'cost_usd_per_lecture_mean': round(sum(costs) / max(1, len(rows)), 6),
                'cost_usd_p50': pct(costs, .5), 'cost_usd_p90': pct(costs, .9),
                'wait_s_p50': round(pct(waits, .5), 2), 'wait_s_p90': round(pct(waits, .9), 2),
                'wait_s_mean': round(sum(waits) / max(1, len(waits)), 2),
                'input_tokens_mean': round(sum(u.get('input_tokens', 0) for r in rows for u in r['usage_rows']
                                               if u.get('purpose') == 'lecture') / max(1, len(rows))),
                'output_tokens_mean': round(sum(u.get('output_tokens', 0) for r in rows for u in r['usage_rows']
                                                if u.get('purpose') == 'lecture') / max(1, len(rows)))})
    return out


def sa13(rows):
    ok = [r for r in rows if r['status'] == 'ready']
    def seconds(field):
        values = [r[field] / 1000 for r in ok if r.get(field) is not None]
        return {'n': len(values), 'p50': round(pct(values, .5), 3) if values else None,
                'p90': round(pct(values, .9), 3) if values else None,
                'min': round(min(values), 3) if values else None, 'max': round(max(values), 3) if values else None}
    gap = [(r['t_final_ms'] - r['t_first_item_ms']) / 1000 for r in ok if r.get('t_final_ms') is not None and r.get('t_first_item_ms') is not None]
    return {'skeleton_s': seconds('t_skeleton_ms'), 'first_item_s': seconds('t_first_item_ms'), 'final_s': seconds('t_final_ms'),
            'first_item_to_final_s': {'n': len(gap), 'p50': round(pct(gap, .5), 3) if gap else None,
                                      'p90': round(pct(gap, .9), 3) if gap else None},
            'lectures_without_item_event': sum(r.get('t_first_item_ms') is None for r in ok),
            'transport': 'Vertex (gemini-3.1-flash-lite), stream, sequential, empty store'}


def main():
    result = {'configs': {}}
    for config in CONFIGS:
        rows = load(config)
        if rows:
            result['configs'][config] = summarize(config, rows)
    a2 = load('A2')
    if a2:
        result['sa13_A2'] = sa13(a2)
    write_json(OUT / 'metrics.json', result)
    print(json.dumps(result, ensure_ascii=False, indent=1, sort_keys=True))


if __name__ == '__main__':
    main()
