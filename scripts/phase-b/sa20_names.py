"""SA-20: build the four name sets and run the paid experiments (L2 and the hidden-title test).

  base                 0 USD  read L1 / A10 from the pinned graphs, deterministic names, E/L/S/R counts
  dry                  0 USD  request counts and cost upper bounds for L2 and the hidden-title run
  run --allow-spend    paid   L2 (no neighbor modules) and L1 with the author title hidden on type-E modules

Outputs go to tmp/sa20/ of this worktree. The shared artifacts directory and artifacts/phase_b/live.json are never touched.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sa20_common import MODEL_ID, OUT, PINS, SHARED, Probe, classify_modules, load_pinned, store  # noqa: E402
from sa29_acceptance import BudgetGate, _request_body, install_budget_gate  # noqa: E402

from doc2roadmap.application.phase_b.common import stable_json  # noqa: E402
from doc2roadmap.application.phase_b.naming import SCHEMA, NameModulesB, _display  # noqa: E402
from doc2roadmap.config import Settings  # noqa: E402
from doc2roadmap.domain.canonical import digest  # noqa: E402
from doc2roadmap.domain.phase_b_limits import BSettings, context_hash  # noqa: E402
from doc2roadmap.domain.phase_b_pricing import estimate_cost  # noqa: E402
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore, JsonPhaseBStore  # noqa: E402
from doc2roadmap.infrastructure.llm.phase_b import GeminiToolModel, RecordingToolModel  # noqa: E402
import doc2roadmap.infrastructure.llm.phase_b as phase_b_transport  # noqa: E402

BASE = OUT / 'base.json'
L2_PATH = OUT / 'l2.json'
HIDDEN_PATH = OUT / 'hidden.json'
STORE_PATH = OUT / 'store-names.json'
RECORDINGS = OUT / 'recordings-names'
DRY_PATH = OUT / 'dry-run.json'
B = BSettings(model_id=MODEL_ID)
# Gate caps are in BudgetGate units: a deliberately loose byte-based upper bound, far above real spend.
CAP_L2 = 0.50
CAP_HIDDEN = 0.20


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=1) + '\n', encoding='utf-8')
    os.replace(temporary, path)


def sentences_of(node):
    out = []
    for item in node.get('description_sentences') or []:
        out.append(str(item.get('text', '')).strip())
    if not out:
        out.append(str(node.get('description', '')).split('[')[0].strip())
    return ' '.join(s for s in out if s)


def build_base():
    st = store()
    pinned = load_pinned(st)
    modules, docs = [], {}
    prompt_hash_expected = digest(NameModulesB(st, None, settings=B)._prompt())
    for doc_id, (named, upstream) in pinned.items():
        config = named.manifest['config']
        classes = classify_modules(st, doc_id, upstream)
        det_case = NameModulesB(st, None, phase_b_store=InMemoryPhaseBStore(), settings=B, deterministic=True)
        det, _ = det_case.execute(doc_id, upstream=upstream)
        chunks = st.load_role_chunks(doc_id, upstream.manifest['config']['chunks_version'])
        page_of = {c.chunk_id: c.page for c in chunks.result.chunks}
        nodes = {n['node_id']: n for n in upstream.payload['nodes']}
        docs[doc_id] = {
            'named_version': named.version, 'upstream_version': upstream.version,
            'upstream_chain': named.manifest['config'].get('upstream_chain'),
            'algorithm_id': config.get('algorithm_id'), 'model_id': config.get('model_id'),
            'deterministic': config.get('deterministic'),
            'prompt_hash_matches_current': config.get('prompt_hash') == prompt_hash_expected,
            'naming_settings_match_current': {k: v for k, v in config['settings'].items() if k.startswith(('naming_', 'title_'))}
            == {k: v for k, v in json.loads(json.dumps(asdict(B))).items() if k.startswith(('naming_', 'title_'))},
            'modules': len(named.payload['modules']),
            'types': dict(Counter(v['type'] for v in classes.values())),
        }
        for index, (a10, l1, dt) in enumerate(zip(upstream.payload['modules'], named.payload['modules'],
                                                  det.payload['modules'])):
            assert a10['module_id'] == l1['module_id'] == dt['module_id']
            detail = []
            for nid in a10['node_ids']:
                node = nodes[nid]
                defining = (node.get('defining_chunk_ids') or node.get('teaching_chunk_ids') or [None])[0]
                detail.append({'name': _display(node), 'definition': sentences_of(node),
                               'page': page_of.get(defining)})
            modules.append({
                'doc_id': doc_id, 'index': index, 'module_id': a10['module_id'],
                'type': classes[a10['module_id']]['type'],
                'section_title': classes[a10['module_id']]['section_title'],
                'node_ids': a10['node_ids'], 'concepts': detail,
                'names': {'L1': l1['title'], 'A10': a10['title'], 'DET': dt['title']},
                'l1': {'title_source': l1.get('title_source'), 'flags': l1.get('naming_flags', []),
                       'description': l1.get('description'), 'description_source': l1.get('description_source')},
                'det_source': dt.get('title_source'),
            })
    result = {'pins': PINS, 'docs': docs, 'modules': modules,
              'types': dict(Counter(m['type'] for m in modules)),
              'l1_title_source': dict(Counter(m['l1']['title_source'] for m in modules)),
              'l1_description_source': dict(Counter(m['l1']['description_source'] for m in modules))}
    write_json(BASE, result)
    return result


def load_base():
    return json.loads(BASE.read_text(encoding='utf-8'))


def planned_requests(base, *, experiment):
    """(doc_id, module_id, request bytes) for every request the experiment would send. 0 USD."""
    st = store()
    pinned = load_pinned(st)
    types = {(m['doc_id'], m['module_id']): m['type'] for m in base['modules']}
    rows = []
    for doc_id, (named, upstream) in pinned.items():
        hide = {mid for (d, mid), t in types.items() if d == doc_id and t == 'E'}
        use = Probe(st, object(), phase_b_store=InMemoryPhaseBStore(), settings=B,
                    drop_neighbors=experiment == 'l2', hide_author=hide if experiment == 'hidden' else ())
        _, prepared = use._prepare(doc_id, upstream)
        prompt = use._prompt()
        for module, _, data, _, _ in prepared:
            if experiment == 'hidden' and module['module_id'] not in hide:
                continue
            body = _request_body(prompt, stable_json(data), B)
            tokens = (len(prompt) + len(stable_json(data)) + len(stable_json(SCHEMA))) // 3
            rows.append({'doc_id': doc_id, 'module_id': module['module_id'], 'bytes': len(body),
                         'est_input_tokens': tokens})
    return rows


def dry():
    base = load_base()
    out = {'mode': 'dry_run_no_calls', 'model_id': MODEL_ID}
    for experiment in ('l2', 'hidden'):
        rows = planned_requests(base, experiment=experiment)
        gate_units = sum(estimate_cost(MODEL_ID, r['bytes'], B.naming_max_output_tokens) for r in rows)
        token_units = sum(estimate_cost(MODEL_ID, r['est_input_tokens'], B.naming_max_output_tokens) for r in rows)
        out[experiment] = {'calls': len(rows), 'bytes_total': sum(r['bytes'] for r in rows),
                           'usd_upper_bytes_as_tokens': round(gate_units, 6),
                           'usd_estimate_chars_div_3_max_output': round(token_units, 6)}
    write_json(DRY_PATH, out)
    return out


class Skipped(Exception):
    pass


class OnlyModules:
    """Lets only chosen modules reach the provider; the rest fail locally before any HTTP attempt."""
    def __init__(self, delegate, allowed):
        self.delegate, self.allowed = delegate, set(allowed)
        self.model_id = delegate.model_id

    def start_session(self, system_prompt):
        return _OnlySession(self.delegate.start_session(system_prompt), self.allowed)


class _OnlySession:
    last_usage: dict = {}
    last_ttft_ms = None

    def __init__(self, inner, allowed):
        self.inner, self.allowed = inner, allowed

    def ask_json(self, prompt, *, response_schema):
        if json.loads(prompt)['module_id'] not in self.allowed:
            raise Skipped('not part of this experiment')
        reply = self.inner.ask_json(prompt, response_schema=response_schema)
        self.last_usage = dict(getattr(self.inner, 'last_usage', {}))
        self.last_ttft_ms = getattr(self.inner, 'last_ttft_ms', None)
        return reply


def provider_model(settings, recording_name):
    model = GeminiToolModel(
        settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else None, MODEL_ID,
        transport=settings.llm_transport, vertex_project=settings.vertex_project,
        vertex_location=settings.vertex_location, temperature=B.naming_temperature,
        max_output_tokens=B.naming_max_output_tokens, timeout_seconds=settings.gemini_timeout_seconds)
    return RecordingToolModel(model, RECORDINGS / recording_name, prompt_hash=context_hash(['sa20', recording_name, MODEL_ID]))


def ledger_usd(phase_store):
    return round(sum(float(r.get('cost_usd', 0) or 0) for r in phase_store.usage_rows()), 8)


def run_experiment(name, path, cap, *, allow_spend):
    if not allow_spend:
        raise SystemExit('refusing to spend without --allow-spend')
    base = load_base()
    settings = Settings(_env_file=str(SHARED / '.env'))
    if settings.llm_transport != 'vertex':
        raise SystemExit(f'expected the Vertex transport used by SA-29, configured: {settings.llm_transport}')
    st = store()
    pinned = load_pinned(st)
    phase_store = JsonPhaseBStore(STORE_PATH)
    types = {(m['doc_id'], m['module_id']): m['type'] for m in base['modules']}
    gate = BudgetGate(cap)
    original = install_budget_gate(gate)
    result = {'status': 'running', 'experiment': name, 'cap_gate_units': cap, 'documents': {}}
    if path.exists():
        previous = json.loads(path.read_text(encoding='utf-8'))
        result['documents'] = previous.get('documents', {})
    write_json(path, result)
    try:
        for doc_id, (named, upstream) in pinned.items():
            if doc_id in result['documents'] and result['documents'][doc_id].get('complete'):
                continue
            hide = {mid for (d, mid), t in types.items() if d == doc_id and t == 'E'}
            model = provider_model(settings, f'{name}-{doc_id}.json')
            if name == 'hidden':
                model = OnlyModules(model, hide)
            use = Probe(st, model, phase_b_store=phase_store, settings=B, allow_spend=True, concurrency=4,
                        drop_neighbors=name == 'l2', hide_author=hide if name == 'hidden' else ())
            started = time.perf_counter()
            artifact, _ = use.execute(doc_id, upstream=upstream)
            modules = artifact.payload['modules']
            result['documents'][doc_id] = {
                'complete': True, 'elapsed_s': round(time.perf_counter() - started, 1),
                'modules': [{'module_id': m['module_id'], 'title': m['title'], 'title_source': m.get('title_source'),
                             'flags': m.get('naming_flags', []), 'description': m.get('description'),
                             'description_source': m.get('description_source'),
                             'hidden': use.hidden_log.get(m['module_id'])} for m in modules]}
            result['transport_attempts'] = gate.attempts
            result['gate_units_used'] = round(gate.reserved, 6)
            result['ledger_usd'] = ledger_usd(phase_store)
            write_json(path, result)
        result['status'] = 'complete'
    except BaseException as error:
        result['status'] = 'failed'
        result['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        phase_b_transport.urlopen = original
        result['transport_attempts'] = gate.attempts
        result['gate_units_used'] = round(gate.reserved, 6)
        result['ledger_usd'] = ledger_usd(phase_store)
        write_json(path, result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['base', 'dry', 'l2', 'hidden'])
    parser.add_argument('--allow-spend', action='store_true')
    args = parser.parse_args()
    if args.command == 'base':
        r = build_base()
        print(json.dumps({k: r[k] for k in ('types', 'l1_title_source', 'l1_description_source')}, ensure_ascii=False))
        print(json.dumps(r['docs'], ensure_ascii=False, indent=1))
    elif args.command == 'dry':
        print(json.dumps(dry(), indent=1))
    elif args.command == 'l2':
        r = run_experiment('l2', L2_PATH, CAP_L2, allow_spend=args.allow_spend)
        print(json.dumps({k: r[k] for k in ('status', 'transport_attempts', 'gate_units_used', 'ledger_usd')}))
    else:
        r = run_experiment('hidden', HIDDEN_PATH, CAP_HIDDEN, allow_spend=args.allow_spend)
        print(json.dumps({k: r[k] for k in ('status', 'transport_attempts', 'gate_units_used', 'ledger_usd')}))
