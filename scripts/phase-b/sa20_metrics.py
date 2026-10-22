"""SA-20 automatic measures for the four name sets (L1, L2, A10, DET).

  intrusion-dry                 0 USD  count the name-to-module matching requests and bound their cost
  intrusion --allow-spend       paid   one judge call per unique (name, module): which of the module and its neighbors fits
  metrics                       0 USD  every measure, from base.json, l2.json, hidden.json, intrusion.json

Local embeddings: multilingual-e5-base from the local Hugging Face cache (offline).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import time
import unicodedata
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from statistics import mean, median

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sa20_common import MODEL_ID, OUT, SHARED, Probe, load_pinned, store  # noqa: E402
from sa20_names import B, BASE, HIDDEN_PATH, L2_PATH, STORE_PATH, load_base, write_json  # noqa: E402
from sa29_acceptance import BudgetGate, install_budget_gate  # noqa: E402

from doc2roadmap.application.phase_b.common import call_json, stable_json  # noqa: E402
from doc2roadmap.application.phase_b.naming import clean_title, _words  # noqa: E402
from doc2roadmap.config import Settings  # noqa: E402
from doc2roadmap.domain.phase_b_limits import context_hash  # noqa: E402
from doc2roadmap.domain.phase_b_pricing import estimate_cost  # noqa: E402
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore, JsonPhaseBStore  # noqa: E402
from doc2roadmap.infrastructure.llm.phase_b import GeminiToolModel, RecordingToolModel  # noqa: E402
import doc2roadmap.infrastructure.llm.phase_b as phase_b_transport  # noqa: E402

VERSIONS = ('L1', 'L2', 'A10', 'DET')
INTRUSION_PATH = OUT / 'intrusion.json'
METRICS_PATH = OUT / 'metrics.json'
INTRUSION_STORE = OUT / 'store-intrusion.json'
INTRUSION_RECORDING = OUT / 'recordings-intrusion'
INTRUSION_CAP = 0.35
INTRUSION_MAX_OUTPUT = 256
INTRUSION_SEED = 20261022
SYSTEM_PROMPT = ('Bạn đọc một giáo trình. Cho một tên module và danh sách khái niệm của vài module ứng viên (đánh số). '
                 'Chọn đúng một module mà tên đó mô tả đúng nhất. Chỉ trả JSON {"chon": số thứ tự của module}.')
SCHEMA = {'type': 'object', 'properties': {'chon': {'type': 'integer'}}, 'required': ['chon']}


def names_by_version(base, *, l2_placeholder=False):
    """{version: {(doc_id, index): name}}. l2_placeholder is for the dry run only: L1 stands in for L2."""
    l2_title = {}
    if L2_PATH.exists() and not l2_placeholder:
        l2 = json.loads(L2_PATH.read_text(encoding='utf-8'))
        for doc_id, doc in l2['documents'].items():
            for index, module in enumerate(doc['modules']):
                l2_title[(doc_id, index)] = module
    elif not l2_placeholder:
        raise SystemExit('l2.json is missing: run sa20_names.py l2 first')
    else:
        l2_title = {(m['doc_id'], m['index']): {'title': m['names']['L1'], 'title_source': m['l1']['title_source']}
                    for m in base['modules']}
    out = {v: {} for v in VERSIONS}
    for m in base['modules']:
        key = (m['doc_id'], m['index'])
        out['L1'][key] = m['names']['L1']
        out['A10'][key] = m['names']['A10']
        out['DET'][key] = m['names']['DET']
        out['L2'][key] = l2_title[key]['title']
    return out, l2_title


def norm(value):
    return ' '.join(unicodedata.normalize('NFC', str(value)).casefold().split())


def intrusion_items(base, names):
    """Unique (name, module) questions; the module's own position is hidden by a fixed shuffle."""
    by_doc = defaultdict(list)
    for m in base['modules']:
        by_doc[m['doc_id']].append(m)
    items = {}
    for m in base['modules']:
        doc, i = m['doc_id'], m['index']
        candidates = [j for j in (i - 1, i, i + 1) if 0 <= j < len(by_doc[doc])]
        candidates.sort(key=lambda j: hashlib.sha256(f'{INTRUSION_SEED}:{doc}:{i}:{j}'.encode()).hexdigest())
        options = [{'so': n + 1, 'khai_niem': [c['name'] for c in by_doc[doc][j]['concepts']]}
                   for n, j in enumerate(candidates)]
        answer = candidates.index(i) + 1
        for version in VERSIONS:
            name = names[version][(doc, i)]
            key = f'{doc}|{i}|{norm(name)}'
            items.setdefault(key, {'doc_id': doc, 'index': i, 'name': name, 'options': options, 'answer': answer,
                                   'versions': []})['versions'].append(version)
    return items


def request_prompt(item):
    return stable_json({'ten_module': item['name'], 'ung_vien': item['options']})


def intrusion_dry():
    base = load_base()
    names, _ = names_by_version(base, l2_placeholder=True)
    items = intrusion_items(base, names)
    chars = [len(SYSTEM_PROMPT) + len(request_prompt(i)) + len(stable_json(SCHEMA)) for i in items.values()]
    byte_units = sum(estimate_cost(MODEL_ID, len(SYSTEM_PROMPT.encode()) + len(request_prompt(i).encode()) + 400,
                                   INTRUSION_MAX_OUTPUT) for i in items.values())
    token_units = sum(estimate_cost(MODEL_ID, c // 3, INTRUSION_MAX_OUTPUT) for c in chars)
    result = {'mode': 'dry_run_no_calls', 'unique_questions': len(items),
              'questions_by_version_sum': sum(len(i['versions']) for i in items.values()),
              'usd_upper_bytes_as_tokens': round(byte_units, 6),
              'usd_estimate_chars_div_3_max_output': round(token_units, 6)}
    write_json(OUT / 'dry-run-intrusion.json', result)
    return result


def intrusion_run(allow_spend):
    if not allow_spend:
        raise SystemExit('refusing to spend without --allow-spend')
    base = load_base()
    names, _ = names_by_version(base)
    items = intrusion_items(base, names)
    settings = Settings(_env_file=str(SHARED / '.env'))
    if settings.llm_transport != 'vertex':
        raise SystemExit('expected the Vertex transport')
    phase_store = JsonPhaseBStore(INTRUSION_STORE)
    model = GeminiToolModel(
        settings.gemini_api_key.get_secret_value() if settings.gemini_api_key else None, MODEL_ID,
        transport=settings.llm_transport, vertex_project=settings.vertex_project,
        vertex_location=settings.vertex_location, temperature=0.0, max_output_tokens=INTRUSION_MAX_OUTPUT,
        timeout_seconds=settings.gemini_timeout_seconds)
    model = RecordingToolModel(model, INTRUSION_RECORDING / 'intrusion.json',
                               prompt_hash=context_hash(['sa20-intrusion', MODEL_ID, SYSTEM_PROMPT]))
    result = json.loads(INTRUSION_PATH.read_text(encoding='utf-8')) if INTRUSION_PATH.exists() else {'answers': {}}
    result.update(status='running', cap_gate_units=INTRUSION_CAP)
    gate = BudgetGate(INTRUSION_CAP)
    original = install_budget_gate(gate)

    def ask(key):
        item = items[key]
        prompt = request_prompt(item)
        reply = call_json(model, prompt, response_schema=SCHEMA, system_prompt=SYSTEM_PROMPT, store=phase_store,
                          purpose='sa20_intrusion', doc_id=item['doc_id'], context_hash=context_hash([key, prompt]),
                          allow_spend=True, settings=B)
        return key, reply.payload.get('chon')

    pending = [k for k in items if k not in result['answers']]
    try:
        with ThreadPoolExecutor(max_workers=4) as pool:
            for count, (key, choice) in enumerate(pool.map(ask, pending), 1):
                result['answers'][key] = choice
                if count % 50 == 0:
                    write_json(INTRUSION_PATH, result)
        result['status'] = 'complete'
    except BaseException as error:
        result['status'] = 'failed'
        result['error'] = f'{type(error).__name__}: {error}'
        raise
    finally:
        phase_b_transport.urlopen = original
        result['transport_attempts_this_run'] = gate.attempts
        result['gate_units_used'] = round(gate.reserved, 6)
        result['ledger_usd'] = round(sum(float(r.get('cost_usd', 0) or 0) for r in phase_store.usage_rows()), 8)
        write_json(INTRUSION_PATH, result)
    return result


# ---------------------------------------------------------------- local measures

_embedder = None


def embed(texts):
    global _embedder
    os.environ.setdefault('HF_HUB_OFFLINE', '1')
    import torch
    from transformers import AutoModel, AutoTokenizer
    if _embedder is None:
        tok = AutoTokenizer.from_pretrained('intfloat/multilingual-e5-base')
        mod = AutoModel.from_pretrained('intfloat/multilingual-e5-base').eval()
        _embedder = (tok, mod)
    tok, mod = _embedder
    vectors = []
    for start in range(0, len(texts), 32):
        batch = ['query: ' + t for t in texts[start:start + 32]]
        enc = tok(batch, padding=True, truncation=True, max_length=64, return_tensors='pt')
        with torch.no_grad():
            out = mod(**enc).last_hidden_state
        mask = enc['attention_mask'].unsqueeze(-1)
        pooled = (out * mask).sum(1) / mask.sum(1)
        vectors.extend(torch.nn.functional.normalize(pooled, dim=1).tolist())
    return vectors


def cosine(a, b):
    return sum(x * y for x, y in zip(a, b))


def chrf(hypothesis, reference, n=6, beta=2.0):
    """chrF over character n-grams 1..n (spaces dropped), averaged over n like sacreBLEU's default."""
    h, r = norm(hypothesis).replace(' ', ''), norm(reference).replace(' ', '')
    precisions, recalls = [], []
    for k in range(1, n + 1):
        hc = Counter(h[i:i + k] for i in range(len(h) - k + 1))
        rc = Counter(r[i:i + k] for i in range(len(r) - k + 1))
        if not hc or not rc:
            continue
        overlap = sum((hc & rc).values())
        precisions.append(overlap / sum(hc.values()))
        recalls.append(overlap / sum(rc.values()))
    if not precisions:
        return 0.0
    p, rec = mean(precisions), mean(recalls)
    return 0.0 if p + rec == 0 else (1 + beta ** 2) * p * rec / (beta ** 2 * p + rec)


def lexicons(base):
    """Per module: allowed words for a name (content vocabulary plus common words) and words borrowed from +-1 neighbors."""
    st = store()
    pinned = load_pinned(st)
    out = {}
    for doc_id, (named, upstream) in pinned.items():
        use = Probe(st, object(), phase_b_store=InMemoryPhaseBStore(), settings=B)
        chunks, prepared = use._prepare(doc_id, upstream)
        _, borrowed = use._description_lexicons(chunks, prepared, upstream)
        from collections import Counter as C
        corpus = C(w for c in chunks.result.chunks for w in _words(c.text))
        function_words = {w for w, n in corpus.most_common(max(1, len(corpus) // 100)) if n >= 3}
        for index, (row, borrow) in enumerate(zip(prepared, borrowed)):
            out[(doc_id, index)] = {'allowed': set(row[2]['content_vocabulary']) | function_words, 'borrowed': borrow,
                                'author_ok': row[2]['exact_author_section']}
    return out


def summarize(values):
    return {'mean': round(mean(values), 4) if values else None, 'median': round(median(values), 4) if values else None,
            'n': len(values)}


def per_book(rows, fn):
    """Median over books of fn(rows of that book): the 'per book then median' reading of the report."""
    books = defaultdict(list)
    for r in rows:
        books[r['doc_id']].append(r)
    return {b: fn(v) for b, v in books.items()}


def compute_metrics():
    base = load_base()
    names, l2 = names_by_version(base)
    modules = {(m['doc_id'], m['index']): m for m in base['modules']}
    lex = lexicons(base)
    intrusion = json.loads(INTRUSION_PATH.read_text(encoding='utf-8')) if INTRUSION_PATH.exists() else None
    items = intrusion_items(base, names)
    keys = list(modules)
    unique = sorted({norm(clean_title(n)[0]) for v in VERSIONS for n in names[v].values()} | {norm(n) for v in VERSIONS for n in names[v].values()})
    vectors = dict(zip(unique, embed(unique)))
    result = {'versions': {}, 'counts': base['types']}
    for version in VERSIONS:
        rows = []
        for key in keys:
            doc_id, index = key
            name = names[version][key]
            cleaned = clean_title(name)[0]
            words = _words(cleaned)
            allowed, borrowed = lex[key]['allowed'], lex[key]['borrowed']
            neighbor_keys = [(doc_id, index + d) for d in (-2, -1, 1, 2) if (doc_id, index + d) in modules]
            sims = [cosine(vectors[norm(name)], vectors[norm(names[version][k])]) for k in neighbor_keys]
            adjacent = [(doc_id, index + d) for d in (-1, 1) if (doc_id, index + d) in modules]
            source = {'L1': modules[key]['l1']['title_source'], 'L2': l2[key]['title_source'],
                      'DET': 'fallback', 'A10': None}[version]
            row = {'doc_id': doc_id, 'max_sim': max(sims) if sims else None,
                   'same_pm1': any(norm(name) == norm(names[version][k]) for k in adjacent),
                   'same_pm2': any(norm(name) == norm(names[version][k]) for k in neighbor_keys),
                   'grounded': all(w in allowed for w in words),
                   'borrowed': any(w in borrowed for w in words),
                   'fallback': None if source is None else source != 'llm',
                   'chars': len(name), 'dot': '·' in name, 'code': clean_title(name)[1] != '' or cleaned != name}
            ikey = f'{doc_id}|{index}|{norm(name)}'
            if intrusion and intrusion['answers'].get(ikey) is not None:
                row['intrusion'] = intrusion['answers'][ikey] == items[ikey]['answer']
                row['chance'] = 1 / len(items[ikey]['options'])
            rows.append(row)
        def rate(field, subset=rows):
            vals = [r[field] for r in subset if r.get(field) is not None]
            return round(sum(vals) / len(vals), 4) if vals else None
        sims = [r['max_sim'] for r in rows if r['max_sim'] is not None]
        result['versions'][version] = {
            'n': len(rows),
            'adjacent_similarity': {**summarize(sims),
                                   'ge_0.90': round(sum(s >= .90 for s in sims) / len(sims), 4),
                                   'per_book_mean': per_book([r for r in rows if r['max_sim'] is not None],
                                                             lambda v: round(mean(x['max_sim'] for x in v), 4))},
            'identical_pairs_pm1_modules': sum(r['same_pm1'] for r in rows),
            'identical_pm2_modules': sum(r['same_pm2'] for r in rows),
            'grounded_rate': rate('grounded'), 'borrowed_rate': rate('borrowed'), 'fallback_rate': rate('fallback'),
            'median_chars': median(r['chars'] for r in rows), 'dot_share': rate('dot'), 'code_or_form_share': rate('code'),
            'intrusion_accuracy': rate('intrusion'),
            'intrusion_chance': round(mean(r['chance'] for r in rows if 'chance' in r), 4) if intrusion else None,
            'intrusion_n': sum('intrusion' in r for r in rows),
            'per_type': {t: {'n': sum(modules[(r_doc, r_i)]['type'] == t for (r_doc, r_i) in keys),
                             'intrusion': rate('intrusion', [r for r, k in zip(rows, keys) if modules[k]['type'] == t])}
                         for t in 'ELSR'}}
        result['versions'][version]['per_book_grounded'] = per_book(rows, lambda v: round(sum(x['grounded'] for x in v) / len(v), 4))
        result['versions'][version]['per_book_borrowed'] = per_book(rows, lambda v: round(sum(x['borrowed'] for x in v) / len(v), 4))
    # hidden author title, type E only
    if HIDDEN_PATH.exists():
        hidden = json.loads(HIDDEN_PATH.read_text(encoding='utf-8'))
        e_rows, lines = [], []
        for doc_id, doc in hidden['documents'].items():
            for index, m in enumerate(doc['modules']):
                base_m = modules[(doc_id, index)]
                if base_m['type'] != 'E':
                    continue
                reference = base_m['section_title']
                generated = m['title'] if m['title_source'] == 'llm' else None
                e_rows.append((doc_id, index, reference, generated, base_m['names']['L1'], m))
        texts = sorted({norm(r[2]) for r in e_rows} | {norm(r[3]) for r in e_rows if r[3]} | {norm(r[4]) for r in e_rows})
        vec = dict(zip(texts, embed(texts)))
        def score(hyp, ref):
            return {'exact': norm(clean_title(hyp)[0]) == norm(ref), 'chrf': chrf(hyp, ref),
                    'cos': cosine(vec[norm(hyp)], vec[norm(ref)])}
        generated_rows = [(r, score(r[3], r[2])) for r in e_rows if r[3]]
        unhidden_rows = [(r, score(r[4], r[2])) for r in e_rows]
        def agg(rows_):
            return {'n': len(rows_), 'exact_rate': round(sum(s['exact'] for _, s in rows_) / max(1, len(rows_)), 4),
                    'chrf_mean': round(mean(s['chrf'] for _, s in rows_), 4) if rows_ else None,
                    'cosine_mean': round(mean(s['cos'] for _, s in rows_), 4) if rows_ else None,
                    'cosine_median': round(median(s['cos'] for _, s in rows_), 4) if rows_ else None}
        # Title-quality filter for the reference: naming.py's own author_ok (E, not a generic label seen under two or more
        # parents, not purely numeric) plus conditions 4 and 5 of report section 6.4 (title differs from the A10 names
        # of modules within +-2 once the numbering is stripped; not a lead-in ending in ':' and not code-only).
        def passes(doc_id, index, reference):
            if not lex[(doc_id, index)]['author_ok']:
                return 'naming.py author_ok'
            near = [norm(clean_title(names['A10'][(doc_id, index + d)])[0]) for d in (-2, -1, 1, 2) if (doc_id, index + d) in modules]
            if norm(reference) in near:
                return '6.4 dieu 4'
            if reference.rstrip().endswith(':') or not _words(reference):
                return '6.4 dieu 5'
            return None
        verdict = {(r[0], r[1]): passes(r[0], r[1], r[2]) for r in e_rows}
        kept_g = [(r, s_) for r, s_ in generated_rows if verdict[(r[0], r[1])] is None]
        kept_u = [(r, s_) for r, s_ in unhidden_rows if verdict[(r[0], r[1])] is None]
        result['hidden_title_filtered'] = {
            'filter': 'naming.py author_ok + report 6.4 conditions 4 and 5',
            'type_E_modules': len(e_rows), 'passing_filter': sum(v is None for v in verdict.values()),
            'rejected_by': dict(Counter(v for v in verdict.values() if v)),
            'passing_and_generated_by_llm': len(kept_g),
            'hidden_run': agg(kept_g), 'l1_unhidden_same_modules': agg([(r, s_) for r, s_ in kept_u if r[3]]),
            'l1_unhidden_all_passing': agg(kept_u)}
        result['hidden_title'] = {
            'type_E_modules': len(e_rows), 'generated_by_llm': len(generated_rows),
            'fallback_or_error': len(e_rows) - len(generated_rows),
            'hidden_run': agg(generated_rows),
            'l1_unhidden_same_modules': agg([(r, s) for r, s in unhidden_rows if r[3]]),
            'l1_unhidden_all_E': agg(unhidden_rows),
            'per_book_hidden_cosine': per_book([{'doc_id': r[0], 'cos': s['cos']} for r, s in generated_rows],
                                               lambda v: round(mean(x['cos'] for x in v), 4)),
            'examples': [{'reference': r[2], 'hidden_run': r[3], 'l1': r[4], 'cos': round(s['cos'], 3)}
                         for r, s in sorted(generated_rows, key=lambda t: t[1]['cos'])[:6]]}
    write_json(METRICS_PATH, result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=['intrusion-dry', 'intrusion', 'metrics'])
    parser.add_argument('--allow-spend', action='store_true')
    args = parser.parse_args()
    if args.command == 'intrusion-dry':
        print(json.dumps(intrusion_dry(), indent=1))
    elif args.command == 'intrusion':
        r = intrusion_run(args.allow_spend)
        print(json.dumps({k: r.get(k) for k in ('status', 'transport_attempts_this_run', 'gate_units_used', 'ledger_usd')}))
    else:
        print(json.dumps(compute_metrics(), ensure_ascii=False, indent=1))
