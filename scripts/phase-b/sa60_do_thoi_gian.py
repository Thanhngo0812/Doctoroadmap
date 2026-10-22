"""SA-60: đo thời gian thật từng khâu của trợ lý (12 lượt SA-55 trên doc-1 và nhap-mon-ml). Có tiền, trần cứng 0,08 USD.

Chỉ bọc trong bộ chạy (không sửa src/): adapter embedding, urlopen của embedding và của mô hình, `_persist` của kho,
`PhaseBRuntime.search`/`lookup`, `IndexConcepts.execute`.

  python scripts/phase-b/sa60_do_thoi_gian.py --dry-run                 # không mạng: lượt, lời gọi tối đa, USD
  python scripts/phase-b/sa60_do_thoi_gian.py --run vertex              # kho JSON, Vertex
  python scripts/phase-b/sa60_do_thoi_gian.py --run devapi              # kho JSON, Gemini Developer API
  python scripts/phase-b/sa60_do_thoi_gian.py --run memory              # kho trong bộ nhớ, Vertex
  python scripts/phase-b/sa60_do_thoi_gian.py --tables                  # bảng Markdown từ kết quả đã lưu

Kết quả và kho nằm trong tmp/sa60 của worktree. Sổ chi cộng dồn giữa các lần chạy (tmp/sa60/ledger.json).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import sys
import threading
import time
from collections import Counter
from copy import deepcopy
from functools import partial
from pathlib import Path
from statistics import median
from urllib.error import HTTPError

import doc2roadmap
from doc2roadmap.application.phase_b import concept_index
from doc2roadmap.application.phase_b.assistant import AssistantUseCase
from doc2roadmap.application.phase_b.budget import DailySpendGuard
from doc2roadmap.application.phase_b.lectures import LectureUseCase
from doc2roadmap.application.phase_b.progress import ProgressUseCase
from doc2roadmap.application.phase_b.sessions import SessionUseCase
from doc2roadmap.composition_phase_b import PhaseBRuntime
from doc2roadmap.config import Settings
from doc2roadmap.domain.phase_b_limits import BSettings
from doc2roadmap.domain.phase_b_pricing import estimate_cost
from doc2roadmap.infrastructure.artifacts import phase_b_store
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore, JsonPhaseBStore
from doc2roadmap.infrastructure.embedding import gemini as embedding_transport
from doc2roadmap.infrastructure.llm import phase_b as llm_transport

ROOT = Path(__file__).resolve().parents[2]
PLAN = Path(__file__).with_name('sa55_plan.json')
WORK = ROOT / 'tmp' / 'sa60'
LEDGER = WORK / 'ledger.json'
PRISTINE_DOC1 = ROOT / 'tmp' / 'doc1-store-src.json'      # bản chép của artifacts/phase_b/doc-1-rebuild-20261020.json
# 7 lượt phiên module + 5 lượt phiên lộ trình (dòng 14, 18, 23, 25, 27) của sa55_plan.json
ROWS = (11, 13, 15, 16, 14, 18, 19, 20, 21, 23, 25, 27)
RUNS = {'vertex': ('vertex', 'json'), 'devapi': ('developer_api', 'json'), 'memory': ('vertex', 'memory')}
MODEL_ID = 'gemini-3.1-flash-lite'
EMBEDDING_MODEL = 'gemini-embedding-001'
CAP_USD = 0.08
HTTP_CAPS = {'llm': 40, 'embedding': 500}            # mỗi lần chạy; chặn cứng
TURN_MARGIN_USD = 0.0035
APPROVAL = '"tôi duyệt tiền hết" (chủ dự án, 2026-10-22)'
SUPPRESSED = 'sa60_suppressed'
SITES = {('SearchDocumentB', 'execute'): 'tim_kiem', ('IndexConcepts', 'lookup'): 'tra_khai_niem',
         ('IndexConcepts', 'execute'): 'dung_chi_muc'}
# Chi USD thật của SA-55 cho đúng 12 câu này (report/pha-b-sa55-2026-10-22.md), dùng làm dự toán.
SA55_USD = {11: .00135, 13: .00212, 15: .00218, 16: .00130, 14: .00188, 18: .00065,
            19: .00098, 20: .00116, 21: .00095, 23: .00092, 25: .00043, 27: .00099}

TURN = {'t0': 0.0, 'embed': [], 'http_embed': [], 'http_llm': [], 'persist': [], 'search': [], 'lookup': [],
        'index_build': []}
LOCK = threading.Lock()


def now_ms():
    return (time.perf_counter() - TURN['t0']) * 1000


def reset_turn():
    TURN['t0'] = time.perf_counter()
    for key in ('embed', 'http_embed', 'http_llm', 'persist', 'search', 'lookup', 'index_build'):
        TURN[key] = []


# ---------------------------------------------------------------------------- budget gate

class BudgetGate:
    """Chặn cứng số lời gọi HTTP và USD: chi thật cộng dồn + cận trên các yêu cầu đang bay phải dưới trần."""

    def __init__(self, cap_usd, llm_cap, embed_cap, spent_before):
        self.cap, self.llm_cap, self.embed_cap = cap_usd, llm_cap, embed_cap
        self.llm = self.embed = 0
        self.spent_before = spent_before
        self.assistant_usd = 0.0
        self.embedding_usd = lambda: 0.0
        self.reserved = 0.0
        self.tripped = None
        self.strip_schema = False        # Developer API: bỏ additionalProperties khỏi schema công cụ (xem báo cáo)
        self._lock = threading.Lock()

    @property
    def actual_usd(self):
        return self.spent_before + self.assistant_usd + self.embedding_usd()

    def new_turn(self):
        with self._lock:
            self.reserved = 0.0

    def admit(self, kind, upper):
        with self._lock:
            used, limit = (self.llm, self.llm_cap) if kind == 'llm' else (self.embed, self.embed_cap)
            if used + 1 > limit:
                self.tripped = f'{kind} http cap {limit}'
            elif self.actual_usd + self.reserved + upper > self.cap:
                self.tripped = f'usd cap {self.cap:.2f}'
            if self.tripped:
                raise PermissionError(f'SA-60 hard cap: {self.tripped}')
            if kind == 'llm':
                self.llm += 1
            else:
                self.embed += 1
            self.reserved += upper


def upper_llm(request):
    try:
        output = int(json.loads(request.data)['generationConfig']['maxOutputTokens'])
    except (ValueError, KeyError, TypeError) as error:
        raise RuntimeError('cannot inspect request budget; refusing network call') from error
    return estimate_cost(MODEL_ID, len(request.data) // 2, output)


def strip_additional_properties(data):
    """Developer API từ chối `additionalProperties` trong tools[].function_declarations[].parameters (HTTP 400);
    Vertex nhận. Bộ chạy bỏ khoá này để đo được đường Developer API; mã sản phẩm không đổi."""
    def clean(value):
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items() if k != 'additionalProperties'}
        if isinstance(value, list):
            return [clean(v) for v in value]
        return value
    body = json.loads(data)
    if 'tools' in body:
        body['tools'] = clean(body['tools'])
    return json.dumps(body, ensure_ascii=False, separators=(',', ':')).encode('utf-8')


def upper_embedding(request):
    if not isinstance(request.data, (bytes, bytearray)):
        raise RuntimeError('cannot inspect embedding request; refusing network call')
    return estimate_cost(EMBEDDING_MODEL, len(request.data) // 2, 0)


# ---------------------------------------------------------------------------- instruments

def status_of(error):
    return error.code if isinstance(error, HTTPError) else type(error).__name__


def install(gate):
    llm_original, embedding_original = llm_transport.urlopen, embedding_transport.urlopen
    embed_original = embedding_transport.GeminiEmbedding.embed
    originals = {name: getattr(cls, name) for cls, name in _PATCHED}

    def llm_open(request, timeout=None):
        gate.admit('llm', upper_llm(request))
        if gate.strip_schema:
            request.data = strip_additional_properties(request.data)
        started = now_ms()
        record = {'start_ms': started, 'rid': id(request)}
        try:
            response = llm_original(request, timeout=timeout)
            record['status'] = getattr(response, 'status', 200)
            return response
        except Exception as error:
            record['status'] = status_of(error)
            if isinstance(error, HTTPError):         # thân lỗi của máy chủ (không chứa khoá)
                record['body'] = error.read().decode('utf-8', 'replace')[:500]
            raise
        finally:
            record['headers_ms'] = now_ms() - started
            with LOCK:
                TURN['http_llm'].append(record)

    def embedding_open(request, timeout=None):
        gate.admit('embedding', upper_embedding(request))
        started = now_ms()
        record = {'start_ms': started, 'rid': id(request)}
        try:
            response = embedding_original(request, timeout=timeout)
            record['status'] = getattr(response, 'status', 200)
            return response
        except Exception as error:
            record['status'] = status_of(error)
            raise
        finally:
            record['dur_ms'] = now_ms() - started
            with LOCK:
                TURN['http_embed'].append(record)

    llm_transport.urlopen, embedding_transport.urlopen = llm_open, embedding_open

    def embed(self, requests):
        requests = list(requests)
        site, frame = 'khac', sys._getframe(1)
        while frame is not None:
            label = SITES.get((type(frame.f_locals.get('self')).__name__, frame.f_code.co_name))
            if label:
                site = label
                break
            frame = frame.f_back
        started = now_ms()
        try:
            return embed_original(self, requests)
        finally:
            with LOCK:
                TURN['embed'].append({'site': site, 'texts': len(requests), 'start_ms': started,
                                      'dur_ms': now_ms() - started, 'transport': self.transport,
                                      'tasks': sorted({r.task_type for r in requests})})
    embedding_transport.GeminiEmbedding.embed = embed

    patched_persist = []
    for cls in (phase_b_store._PhaseBStore, JsonPhaseBStore):
        if '_persist' in cls.__dict__:
            original = cls.__dict__['_persist']

            def persist(self, _original=original):
                started = now_ms()
                try:
                    return _original(self)
                finally:
                    with LOCK:
                        TURN['persist'].append({'start_ms': started, 'dur_ms': now_ms() - started})
            setattr(cls, '_persist', persist)
            patched_persist.append((cls, original))

    def timed(bucket, original):
        def wrapper(*args, **kwargs):
            started = now_ms()
            try:
                return original(*args, **kwargs)
            finally:
                with LOCK:
                    TURN[bucket].append({'start_ms': started, 'dur_ms': now_ms() - started})
        return wrapper
    PhaseBRuntime.search = timed('search', originals['search'])
    PhaseBRuntime.lookup = timed('lookup', originals['lookup'])
    concept_index.IndexConcepts.execute = timed('index_build', originals['execute'])

    def restore():
        llm_transport.urlopen, embedding_transport.urlopen = llm_original, embedding_original
        embedding_transport.GeminiEmbedding.embed = embed_original
        for cls, original in patched_persist:
            setattr(cls, '_persist', original)
        PhaseBRuntime.search, PhaseBRuntime.lookup = originals['search'], originals['lookup']
        concept_index.IndexConcepts.execute = originals['execute']
    return restore


_PATCHED = ((PhaseBRuntime, 'search'), (PhaseBRuntime, 'lookup'), (concept_index.IndexConcepts, 'execute'))


# ---------------------------------------------------------------------------- books and assistant

class StubLectureModel:
    model_id = MODEL_ID

    def __getattr__(self, name):
        raise RuntimeError('SA-60 must not generate lectures')


def scope_of(graph, name):
    if name == 'roadmap':
        return {'kind': 'roadmap'}
    module = graph.modules[name]
    return {'kind': 'module', 'node_ids': list(module.get('node_ids', [])), 'module_id_at_creation': name,
            'graph_version_at_creation': graph.graph_version}


def make_settings(transport):
    env = ROOT / '.env'
    if not env.is_file():
        env = ROOT.parents[1] / '.env'
    return Settings(_env_file=env, artifact_dir=ROOT / 'artifacts', llm_transport=transport)


def has_dev_key(settings):
    return bool(settings.gemini_api_key and settings.gemini_api_key.get_secret_value().strip())


def open_book(doc_id, pin, settings, backend, directory):
    path = directory / f'{doc_id}.json'
    if path.exists():
        raise FileExistsError(f'{path} already exists')
    directory.mkdir(parents=True, exist_ok=True)
    seeded = pin['store'].startswith('copy:')
    if seeded and backend == 'json':
        shutil.copyfile(PRISTINE_DOC1, path)
    runtime = PhaseBRuntime(settings=settings, allow_spend=True, mode='gemini', store_path=path)
    runtime.record_dir = None
    if backend == 'memory':
        store = InMemoryPhaseBStore()
        if seeded:                       # same starting content as the JSON run, no file behind it
            seed = JsonPhaseBStore(PRISTINE_DOC1)
            store._cache, store._records, store._usage = (deepcopy(seed._cache), deepcopy(seed._records),
                                                          deepcopy(seed._usage))
        runtime.store = store
        runtime.spend_guard = DailySpendGuard(store, settings=runtime.b_settings, clock=runtime.clock)
    graph = runtime.graph(doc_id, pin['graph_version'])
    return runtime, graph, path


def build_assistant(runtime, graph, counters):
    progress = ProgressUseCase(runtime.store, graph, clock=runtime.clock)
    guard = runtime.spend_guard
    lecture = LectureUseCase(StubLectureModel(), runtime.store, settings=runtime.b_settings, clock=runtime.clock,
                             progress=progress, spend_guard=guard)

    def get_lecture(concept, **kwargs):
        if not kwargs.get('cache_only'):
            counters['get_lecture'] += 1
        return lecture.make(graph.doc_id, graph.graph_version, graph, concept, owner=kwargs.get('owner'),
                            cache_only=True)

    def make_quiz(scope, n=None, level=None, **kwargs):
        counters['make_quiz'] += 1
        return {'status': 'failed', 'reason': SUPPRESSED}

    def make_document(request, scope, **kwargs):
        counters['make_document'] += 1
        return {'status': 'failed', 'reason': SUPPRESSED}

    return AssistantUseCase(graph, runtime.store, runtime.model('assistant'), settings=runtime.b_settings,
                            search=partial(runtime.search, graph), concept_lookup=partial(runtime.lookup, graph),
                            lecture=get_lecture, quiz=make_quiz, document=make_document, clock=runtime.clock,
                            progress=progress, spend_guard=guard)


# ---------------------------------------------------------------------------- one turn

def analyse(wall_ms, first_model_ms):
    """Collapse the raw event lists of the turn into stage numbers."""
    https = TURN['http_embed']
    calls = []
    for call in TURN['embed']:
        end = call['start_ms'] + call['dur_ms']
        inside = [h for h in https if call['start_ms'] - 1 <= h['start_ms'] <= end + 1]
        expected = call['texts'] if call['transport'] == 'vertex' else math.ceil(call['texts'] / 100)
        statuses = Counter(str(h.get('status')) for h in inside)
        calls.append({'site': call['site'], 'texts': call['texts'], 'dur_ms': round(call['dur_ms']),
                      'start_ms': round(call['start_ms']), 'http_attempts': len(inside),
                      'retries': max(0, len(inside) - expected), 'statuses': dict(statuses),
                      'http_ms_max': round(max((h['dur_ms'] for h in inside), default=0)),
                      'http_ms_median': round(median([h['dur_ms'] for h in inside]) if inside else 0)})
    persist = TURN['persist']
    before = first_model_ms if first_model_ms is not None else wall_ms
    return {
        'embedding_calls': len(calls), 'embedding_texts': sum(c['texts'] for c in calls),
        'embedding_http_attempts': sum(c['http_attempts'] for c in calls),
        'embedding_retries': sum(c['retries'] for c in calls),
        'embedding_non_200': sum(n for c in calls for s, n in c['statuses'].items() if s != '200'),
        'embedding_ms': round(sum(c['dur_ms'] for c in calls)),
        'embedding_ms_before_model': round(sum(c['dur_ms'] for c in calls if c['start_ms'] < before)),
        'embedding_calls_detail': calls,
        'store_writes': len(persist), 'store_write_ms': round(sum(p['dur_ms'] for p in persist), 1),
        'store_writes_before_model': sum(1 for p in persist if p['start_ms'] < before),
        'store_write_ms_before_model': round(sum(p['dur_ms'] for p in persist if p['start_ms'] < before), 1),
        'search_ms': round(sum(s['dur_ms'] for s in TURN['search'])), 'search_calls': len(TURN['search']),
        'lookup_ms': round(sum(s['dur_ms'] for s in TURN['lookup'])), 'lookup_calls': len(TURN['lookup']),
        'index_build_ms': round(sum(s['dur_ms'] for s in TURN['index_build'])),
        'llm_http': [{'start_ms': round(h['start_ms']), 'headers_ms': round(h['headers_ms']),
                      'status': h.get('status'), **({'body': h['body']} if 'body' in h else {})}
                     for h in TURN['http_llm']],
    }


def run_turn(row, runtime, graph, session_id, owner, question, gate, run_label):
    counters = Counter()
    assistant = build_assistant(runtime, graph, counters)
    gate.new_turn()
    reset_turn()
    first_delta = []

    def on_event(event):
        if event.get('event') == 'delta' and not first_delta:
            first_delta.append(now_ms())

    result = error = None
    started = time.perf_counter()
    try:
        result = assistant.ask(graph.doc_id, graph.graph_version, session_id, question, owner=owner,
                               client_turn_id=f'{owner}-t1', allow_spend=True, on_event=on_event)
    except Exception as exception:
        error = f'{type(exception).__name__}: {exception}'
    wall_ms = (time.perf_counter() - started) * 1000
    first_model_ms = min((h['start_ms'] for h in TURN['http_llm']), default=None)
    usage = (result or {}).get('usage', {})
    rows = [r for r in runtime.store.usage_rows(graph.doc_id, learner_id=owner) if r.get('purpose') == 'assistant']
    round1 = [r for r in rows if r.get('tool_round') == 1]
    turn = {'run': run_label, 'n': row['n'], 'doc_id': row['doc_id'], 'scope': row['scope'],
            'session': 'lo_trinh' if row['scope'] == 'roadmap' else 'module', 'kind': row['kind'],
            'question': question, 'status': (result or {}).get('status', 'loi'), 'error': error,
            'wall_ms': round(wall_ms), 'to_first_model_ms': None if first_model_ms is None else round(first_model_ms),
            'model_ttft_ms': round1[0].get('ttft_ms') if round1 else None, 'product_ttft_ms': usage.get('ttft_ms'),
            'first_delta_ms': round(first_delta[0]) if first_delta else None,
            'rounds': usage.get('model_calls', 0), 'usd': usage.get('usd', 0.0),
            'tools': [log['name'] for log in (result or {}).get('tool_calls', [])],
            'content_tool_calls': dict(counters), **analyse(wall_ms, first_model_ms)}
    gate.assistant_usd += turn['usd']
    return turn


# ---------------------------------------------------------------------------- dry run

def load_plan():
    plan = json.loads(PLAN.read_text(encoding='utf-8'))
    by_n = {row['n']: row for row in plan['rows']}
    return plan, [by_n[n] for n in ROWS]


def read_ledger():
    return json.loads(LEDGER.read_text(encoding='utf-8')) if LEDGER.exists() else {'runs': {}, 'spent_usd': 0.0}


def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=1), encoding='utf-8')
    os.replace(temporary, path)


def dry_run():
    plan, rows = load_plan()
    settings = make_settings('vertex')
    bs = BSettings()
    docs, problems, upper_worst = {}, [], 0.0
    for row in rows:
        doc_id = row['doc_id']
        if doc_id not in docs:
            runtime = PhaseBRuntime(settings=settings, mode='offline', store_path=WORK / 'dryrun-unused.json')
            docs[doc_id] = (runtime.graph(doc_id, plan['pins'][doc_id]['graph_version']), InMemoryPhaseBStore())
        graph, store = docs[doc_id]
        owner = f"sa60-dry-{row['n']:02d}"
        try:
            session = SessionUseCase(store, graph, settings=bs).create_session(
                owner, doc_id, scope_of(graph, row['scope']))
            estimate = AssistantUseCase(graph, store, None, settings=bs).ask(
                doc_id, graph.graph_version, session['session_id'], row['questions'][0], owner=owner, dry_run=True)
            upper_worst += estimate['usd_estimate'] * plan['max_rounds_per_turn']
        except Exception as error:
            problems.append(f"row {row['n']}: {type(error).__name__}: {error}")
    runs = 3
    llm_run = sum(SA55_USD[n] for n in ROWS)
    embedding_run = estimate_cost(EMBEDDING_MODEL, (len(ROWS) * 3 + 298) * 150, 0)   # tra cứu + chỉ mục khái niệm
    result = {
        'dry_run': True, 'network_calls': 0, 'turns_per_run': len(rows), 'runs': runs, 'turns': len(rows) * runs,
        'rows': list(ROWS), 'http_cap_per_run': HTTP_CAPS,
        'max_http_total': {k: v * runs for k, v in HTTP_CAPS.items()},
        'usd_estimate_from_sa55_same_questions': round((llm_run + embedding_run) * runs, 4),
        'usd_llm_per_run_sa55': round(llm_run, 5), 'usd_embedding_per_run_upper': round(embedding_run, 5),
        'usd_worst_case_5_full_rounds_per_run': round(upper_worst, 4),
        'usd_worst_case_total': round(upper_worst * runs, 4), 'cap_usd': CAP_USD,
        'within_cap_estimate': (llm_run + embedding_run) * runs <= CAP_USD, 'problems': problems,
        'dev_api_key_present': has_dev_key(make_settings('developer_api'))}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    save_json(WORK / 'dryrun.json', result)
    return result


# ---------------------------------------------------------------------------- paid run

def paid_run(label, only=None):
    transport, backend = RUNS[label]
    plan, rows = load_plan()
    if only:
        rows = [r for r in rows if r['n'] in only]
    settings = make_settings(transport)
    if transport == 'developer_api' and not has_dev_key(settings):
        print('Không có khoá Developer API trong .env: bỏ lần chạy devapi.')
        return None
    out_path = WORK / (f'run-{label}-diag.json' if only else f'run-{label}.json')
    if out_path.exists():
        raise FileExistsError(f'{out_path} đã có; không chi hai lần cho cùng một lần chạy')
    if Path(doc2roadmap.__file__).resolve().parents[1] != ROOT / 'src':
        raise RuntimeError('doc2roadmap không nạp từ worktree này; đặt PYTHONPATH')
    ledger = read_ledger()
    gate = BudgetGate(CAP_USD, HTTP_CAPS['llm'], HTTP_CAPS['embedding'], ledger['spent_usd'])
    directory = WORK / f'store-{label}'
    if directory.exists():
        shutil.rmtree(directory)
    books = {}
    for doc_id in dict.fromkeys(r['doc_id'] for r in rows):
        books[doc_id] = open_book(doc_id, plan['pins'][doc_id], settings, backend, directory)
    gate.embedding_usd = lambda: sum(r.get('cost_usd', 0) for rt, _, _ in books.values()
                                     for r in rt.store.usage_rows() if r.get('purpose') == 'embedding')
    gate.strip_schema = transport == 'developer_api'
    restore = install(gate)
    result = {'ticket': 'SA-60', 'run': label, 'transport': transport, 'store': backend, 'approval': APPROVAL,
              'status': 'running', 'started_at': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'turns': [], 'skipped': []}
    try:
        for row in rows:
            runtime, graph, _ = books[row['doc_id']]
            if gate.tripped or gate.actual_usd + TURN_MARGIN_USD > CAP_USD:
                result['skipped'].append({'n': row['n'], 'reason': gate.tripped or 'ledger+margin>cap'})
                continue
            owner = f"sa60-{label}-{row['n']:02d}"
            session = SessionUseCase(runtime.store, graph, settings=runtime.b_settings, clock=runtime.clock) \
                .create_session(owner, row['doc_id'], scope_of(graph, row['scope']))
            turn = run_turn(row, runtime, graph, session['session_id'], owner, row['questions'][0], gate, label)
            result['turns'].append(turn)
            result['spent_this_run_usd'] = round(gate.assistant_usd + gate.embedding_usd(), 6)
            save_json(out_path, result)
            print(json.dumps({'n': row['n'], 'status': turn['status'], 'wall_s': round(turn['wall_ms'] / 1000, 1),
                              'to_model_s': None if turn['to_first_model_ms'] is None
                              else round(turn['to_first_model_ms'] / 1000, 1),
                              'emb': turn['embedding_calls'], 'retries': turn['embedding_retries'],
                              'writes': turn['store_writes'], 'usd_run': result['spent_this_run_usd'],
                              'usd_total': round(gate.actual_usd, 5)}, ensure_ascii=False), flush=True)
    finally:
        restore()
        result['status'] = 'complete' if not gate.tripped and not result['skipped'] else 'stopped'
        result['tripped'] = gate.tripped
        result['llm_http_attempts'], result['embedding_http_attempts'] = gate.llm, gate.embed
        result['assistant_usd'] = round(gate.assistant_usd, 6)
        result['embedding_usd_estimated'] = round(gate.embedding_usd(), 6)
        result['total_usd'] = round(result['assistant_usd'] + result['embedding_usd_estimated'], 6)
        result['store_bytes'] = {d: (p.stat().st_size if p.exists() else 0) for d, (_, _, p) in books.items()}
        result['finished_at'] = time.strftime('%Y-%m-%dT%H:%M:%S%z')
        save_json(out_path, result)
        ledger['runs'][label + ('-diag' if only else '')] = result['total_usd']
        ledger['spent_usd'] = round(sum(ledger['runs'].values()), 6)
        save_json(LEDGER, ledger)
    print(json.dumps({k: result[k] for k in ('status', 'total_usd', 'llm_http_attempts', 'embedding_http_attempts')}))
    print('chi cộng dồn', ledger['spent_usd'])
    return result


# ---------------------------------------------------------------------------- tables

def pct(values, q):
    values = sorted(v for v in values if v is not None)
    return values[min(len(values) - 1, int(q * len(values)))] if values else None


def fmt(value):
    return '-' if value is None else f'{value:.0f}'


STAGE_COLUMNS = (
    ('embedding_ms', 'embedding, tổng ms/lượt'), ('embedding_ms_before_model', 'embedding trước mô hình, ms'),
    ('store_write_ms', 'ghi kho, tổng ms/lượt'), ('search_ms', 'tìm kiếm (gồm embedding), ms'),
    ('lookup_ms', 'tra khái niệm (gồm dựng chỉ mục), ms'), ('index_build_ms', 'dựng chỉ mục khái niệm, ms'),
    ('to_first_model_ms', 'tới lời gọi mô hình đầu, ms'), ('model_ttft_ms', 'TTFT mô hình, ms'),
    ('wall_ms', 'tổng, ms'))


def tables():
    runs = {}
    for label in RUNS:
        path = WORK / f'run-{label}.json'
        if path.exists():
            runs[label] = json.loads(path.read_text(encoding='utf-8'))
    lines = []
    for scope_name, test in (('tất cả', lambda t: True), ('module', lambda t: t['session'] == 'module'),
                             ('lộ trình', lambda t: t['session'] == 'lo_trinh')):
        lines.append(f'\n### p50 / p90 theo khâu, phiên: {scope_name}\n')
        lines.append('| khâu | ' + ' | '.join(runs) + ' |')
        lines.append('|---|' + '---|' * len(runs))
        for key, name in STAGE_COLUMNS:
            cells = []
            for run in runs.values():
                values = [t[key] for t in run['turns'] if test(t) and t[key] is not None]
                cells.append(f'{fmt(median(values) if values else None)} / {fmt(pct(values, .9))} (n={len(values)})')
            lines.append(f'| {name} | ' + ' | '.join(cells) + ' |')
    lines.append('\n### Số lượng mỗi lượt\n')
    for label, run in runs.items():
        lines.append(f'\n**{label}** (chi {run["total_usd"]} USD, trạng thái {run["status"]})\n')
        lines.append('| # | cuốn | phiên | lượt gọi embedding | văn bản | HTTP | thử lại | ngoài 200 | ghi kho | ghi kho ms | '
                     'ghi trước mô hình | embedding ms | tới mô hình ms | TTFT mô hình ms | tổng ms | vòng |')
        lines.append('|' + '---|' * 16)
        for t in run['turns']:
            lines.append(f"| {t['n']} | {t['doc_id']} | {t['scope']} | {t['embedding_calls']} | {t['embedding_texts']} | "
                         f"{t['embedding_http_attempts']} | {t['embedding_retries']} | {t['embedding_non_200']} | "
                         f"{t['store_writes']} | {t['store_write_ms']:.0f} | {t['store_writes_before_model']} | "
                         f"{t['embedding_ms']} | {t['to_first_model_ms']} | {t['model_ttft_ms']} | {t['wall_ms']} | "
                         f"{t['rounds']} |")
    text = '\n'.join(lines)
    (WORK / 'tables.md').write_text(text, encoding='utf-8')
    print(text)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--run', choices=sorted(RUNS))
    parser.add_argument('--tables', action='store_true')
    parser.add_argument('--only', type=int, nargs='+', help='chạy thử vài dòng; ghi run-<nhãn>-diag.json')
    args = parser.parse_args()
    if args.dry_run:
        dry_run()
    elif args.run:
        paid_run(args.run, args.only)
    elif args.tables:
        tables()
    else:
        parser.error('cần --dry-run, --run hoặc --tables')
