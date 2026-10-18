"""Zero-network B2 source scan and recorded-response audit, development books only."""
import json
from collections import Counter
from pathlib import Path
from statistics import median

from doc2roadmap.application.phase_b.lectures import LectureUseCase, _assemble
from doc2roadmap.composition_phase_b import PhaseBRuntime, DEVELOPMENT_DOCS
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore


def percentile(values, fraction):
    return sorted(values)[min(len(values) - 1, int(len(values) * fraction))] if values else None


def main():
    root = Path.cwd()
    runtime = PhaseBRuntime(mode='offline', store_path=root / 'tmp/b2-audit-unused-store.json')
    scan = []
    for doc_id in DEVELOPMENT_DOCS:
        graph = runtime.graph(doc_id)
        counts = Counter()
        for node_id in graph.learnable_nodes:
            context, skeleton, _ = _assemble(graph, node_id, runtime.b_settings)
            counts['concepts'] += 1
            counts['prerequisites'] += len(skeleton['prerequisites'])
            counts['q_eligible'] += len(context['bridge_candidates'])
            counts['next_up'] += len(skeleton['next_up'])
        scan.append({'doc_id': doc_id, 'graph_version': graph.graph_version, **counts})
        print(json.dumps(scan[-1]), flush=True)
    old = json.loads((root / 'tmp/phaseb-live-group2-v2.json').read_text(encoding='utf-8'))
    fixture = json.loads((root / 'tmp/phaseb-live-group2-v2-merged-recordings/lecture.json').read_text(encoding='utf-8'))
    old_results = []
    for operation in (row for row in old['operations'] if row['kind'] == 'lecture'):
        node_id = operation['node_id']
        sessions = []
        for session in fixture['sessions']:
            calls = session['calls']
            if not calls or calls[0]['kind'] != 'json_stream':
                continue
            prompt = calls[0]['prompt']
            if node_id in prompt:
                sessions.extend(c for c in calls if c['kind'] == 'json_stream')
        class HistoricalResponses:
            is_replay = True
            model_id = fixture['model_id']
            def __init__(self):
                self.index = 0
            def start_session(self, *_):
                if self.index >= len(sessions):
                    raise ValueError('historical recording has no additional response')
                call = sessions[self.index]
                self.index += 1
                class Session:
                    last_usage = call.get('usage', {})
                    last_ttft_ms = call.get('ttft_ms')
                    last_finish_reason = call.get('finish_reason')
                    def stream_json(self, prompt, *, response_schema):
                        for part in call['chunks']:
                            # Historical B1 responses cannot invent the new bridges.
                            yield part.replace('"prereq_notes"', '"bridges"')
                return Session()
        graph = runtime.graph(operation['doc_id'], operation['graph_version'])
        result = LectureUseCase(HistoricalResponses(), InMemoryPhaseBStore()).make(
            graph.doc_id, graph.graph_version, graph, node_id, allow_spend=True)
        old_results.append({'doc_id': graph.doc_id, 'graph_version': graph.graph_version,
                            'node_id': node_id, 'before_status': operation['result']['status'],
                            'after_status': result['status'], 'result': result})
    live = json.loads((root / 'tmp/phaseb-sa43-live-20261018.json').read_text(encoding='utf-8'))
    replay = json.loads((root / 'tmp/phaseb-sa43-replay-20261018.json').read_text(encoding='utf-8'))
    metrics = []
    for temperature in (0, 1):
        arms = [row['arms'][temperature] for row in live['completed']]
        timings = [a['result'].get('diagnostics', {}) for a in arms]
        # The second arm replays the first response without its wall-clock delay.
        # Only complete initial-arm click timings are usable for latency claims.
        latency = {}
        if temperature == 0:
            for key in ['skeleton_ms', 'gate_ms', 'final_ms', 'gate_to_final_ms']:
                values = [t[key] for t in timings if key in t]
                latency[key] = {'count': len(values), 'p50': median(values) if values else None,
                                'p90': percentile(values, .9)}
        validations = [d for a in arms for d in a['validation']]
        dropped = Counter()
        for d in validations:
            dropped.update(d.get('dropped_by_rule', {}))
        metrics.append({'repair_temperature': temperature,
                        'live_statuses': dict(Counter(a['result']['status'] for a in arms)),
                        'corrected_replay_statuses': dict(Counter(r['arms'][temperature]['result']['status'] for r in replay['completed'])),
                        'additional_paid_usd': sum(a['new_cost_usd'] for a in arms),
                        'dropped': dict(dropped), 'live_latency': latency,
                        'replay_prompt_mismatches': sum('matching this request' in str(d.get('failure_reason'))
                             for r in replay['completed'] for d in r['arms'][temperature]['validation'])})
    payload = {'source_scan': scan, 'historical': old_results,
               'historical_replay_note': 'B1 raw responses revalidated against B2 context; not exact prompt replay, no bridge-quality or replay-latency claim.',
               'sa43': metrics, 'live_cost_usd': live['new_cost_usd'], 'http_attempts': live['http_attempts'],
               'new_cost_usd': 0, 'network_calls': 0}
    (root / 'tmp/phaseb-b2-lecture-audit.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'historical_statuses': dict(Counter(r['after_status'] for r in old_results)),
                      'sa43': metrics, 'network_calls': 0}), flush=True)


if __name__ == '__main__':
    main()
