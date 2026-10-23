"""SA-55: 36 assistant questions on four pinned books, with recorded replay.

Default (no flag) and --dry-run: zero network calls; print turns, max HTTP calls, max USD.
--allow-spend: run the paid plan (hard cap 0.50 USD, gemini-3.1-flash-lite only).
--replay: replay every recorded conversation at 0 USD and compare with the live results.
--report: write the Markdown report from the saved live results (and the replay, if any).
Recordings, stores and results stay in tmp/sa55 of this worktree.
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
from pathlib import Path
from statistics import median
from urllib.request import Request

import doc2roadmap
from doc2roadmap.application.phase_b.assistant import REFUSAL, AssistantUseCase
from doc2roadmap.application.phase_b.budget import DailySpendGuard
from doc2roadmap.application.phase_b.lectures import LectureUseCase
from doc2roadmap.application.phase_b.progress import ProgressUseCase
from doc2roadmap.application.phase_b.sessions import SessionUseCase
from doc2roadmap.composition_phase_b import PhaseBRuntime
from doc2roadmap.config import Settings
from doc2roadmap.domain.phase_b_limits import BSettings, context_hash
from doc2roadmap.domain.phase_b_pricing import estimate_cost
from doc2roadmap.infrastructure.artifacts.phase_b_store import InMemoryPhaseBStore, JsonPhaseBStore
from doc2roadmap.infrastructure.llm.phase_b import RecordingToolModel, ReplayToolModel

ROOT = Path(__file__).resolve().parents[2]
PLAN = Path(__file__).with_name('sa55_plan.json')
WORK = ROOT / 'tmp/sa55'
RESULTS = WORK / 'results.json'
REPLAY_RESULTS = WORK / 'replay.json'
DRYRUN = WORK / 'dryrun.json'
RECORDINGS = WORK / 'recordings'
REPORT = ROOT / 'report/pha-b-sa55-2026-10-22.md'
ERROR_TYPES = {'ValueError': ValueError, 'KeyError': KeyError, 'PermissionError': PermissionError,
               'TypeError': TypeError, 'RuntimeError': RuntimeError}
SUPPRESSED = 'sa55_suppressed'
SCOPE_ALIASES = {'ưu tiên module': 'uu_tien_module'}
MODEL_ERRORS = {'invalid_tool_call', 'tool_error', 'result_limit'}
EMBEDDING_MODEL = 'gemini-embedding-001'


# ---------------------------------------------------------------------------- plan and settings

def load_plan():
    return json.loads(PLAN.read_text(encoding='utf-8'))


def make_settings():
    """Worktree artifacts; key, transport and project come from the shared .env (never printed)."""
    env = ROOT / '.env'
    if not env.is_file():
        env = ROOT.parents[1] / '.env'
    return Settings(_env_file=env, artifact_dir=ROOT / 'artifacts')


def check_code_path():
    # The editable install points at the shared checkout; PYTHONPATH must put this worktree first.
    loaded = Path(doc2roadmap.__file__).resolve()
    if ROOT not in loaded.parents:
        raise RuntimeError(f'doc2roadmap loaded from {loaded}, not from this worktree; set PYTHONPATH')


def conversation_id(row):
    return f"sa55-{row['n']:02d}"


# ---------------------------------------------------------------------------- budget gate

class Gate:
    """Hard stop on HTTP attempts and on USD: actual so far + in-flight upper bound must stay under the cap."""

    def __init__(self, cap_usd, llm_attempts, embedding_attempts):
        self.cap, self.llm_cap, self.embed_cap = cap_usd, llm_attempts, embedding_attempts
        self.llm_attempts = self.embed_attempts = 0
        self.assistant_usd = 0.0       # from returned tokens, added by the runner after every turn
        self.embedding_usd = lambda: 0.0   # estimated embedding spend recorded in the stores
        self.turn_reserved = 0.0       # upper bounds of requests sent in the current turn
        self.embed_reserved = 0.0
        self.tripped = None
        self._lock = threading.Lock()

    @property
    def actual_usd(self):
        return self.assistant_usd + self.embedding_usd()

    def new_turn(self):
        with self._lock:
            self.turn_reserved = 0.0

    def _admit(self, kind, upper):
        with self._lock:
            attempts = self.llm_attempts if kind == 'llm' else self.embed_attempts
            limit = self.llm_cap if kind == 'llm' else self.embed_cap
            if attempts + 1 > limit:
                self.tripped = f'{kind} http attempts cap {limit}'
            elif self.actual_usd + self.turn_reserved + self.embed_reserved + upper > self.cap:
                self.tripped = f'usd cap {self.cap:.2f}'
            if self.tripped:
                raise PermissionError(f'SA-55 hard cap: {self.tripped}')
            if kind == 'llm':
                self.llm_attempts += 1
                self.turn_reserved += upper
            else:
                self.embed_attempts += 1
                self.embed_reserved += upper

    def llm(self, request):
        try:
            output = int(json.loads(request.data)['generationConfig']['maxOutputTokens'])
        except (ValueError, KeyError, TypeError) as error:
            raise RuntimeError('cannot inspect request budget; refusing network call') from error
        # Vietnamese JSON: at most one token per two bytes, a deliberate over-estimate.
        self._admit('llm', estimate_cost(MODEL_ID, len(request.data) // 2, output))

    def embedding(self, request):
        if not isinstance(request.data, (bytes, bytearray)):
            raise RuntimeError('cannot inspect embedding request; refusing network call')
        self._admit('embedding', estimate_cost(EMBEDDING_MODEL, len(request.data) // 2, 0))


MODEL_ID = 'gemini-3.1-flash-lite'


def install_gate(gate):
    from doc2roadmap.infrastructure.embedding import gemini as embedding_transport
    from doc2roadmap.infrastructure.llm import phase_b as llm_transport
    originals = (llm_transport.urlopen, embedding_transport.urlopen)
    llm_original, embedding_original = originals

    def llm_open(request, timeout=None):
        gate.llm(request)
        return llm_original(request, timeout=timeout)

    def embedding_open(request, timeout=None):
        gate.embedding(request)
        return embedding_original(request, timeout=timeout)

    llm_transport.urlopen, embedding_transport.urlopen = llm_open, embedding_open

    def restore():
        llm_transport.urlopen, embedding_transport.urlopen = originals
    return restore


# ---------------------------------------------------------------------------- recording helpers

class Tape:
    """Search and concept-lookup outputs of one conversation, so replay needs no embedding calls."""

    def __init__(self, path, *, replay):
        self.path, self.replay, self.items, self.pos = Path(path), replay, [], 0
        if replay:
            self.items = json.loads(self.path.read_text(encoding='utf-8'))['items']

    def call(self, kind, key, function):
        if self.replay:
            if self.pos >= len(self.items):
                raise RuntimeError('tape exhausted')
            item = self.items[self.pos]
            self.pos += 1
            if item['kind'] != kind or item['key'] != key:
                raise ValueError(f'tape mismatch at {self.pos}: {kind}')
            if 'error' in item:
                raise ERROR_TYPES.get(item['error']['type'], RuntimeError)(item['error']['message'])
            return deepcopy(item['result'])
        try:
            result = function()
        except Exception as error:
            self.items.append({'kind': kind, 'key': key, 'error': {'type': type(error).__name__, 'message': str(error)}})
            self.save()
            raise
        self.items.append({'kind': kind, 'key': key, 'result': deepcopy(result)})
        self.save()
        return result

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix('.tmp')
        temporary.write_text(json.dumps({'items': self.items}, ensure_ascii=False, indent=1), encoding='utf-8')
        os.replace(temporary, self.path)


class CaptureModel:
    """Keeps the first context message of every assistant session (focus block, definition label)."""

    def __init__(self, delegate):
        self.delegate, self.model_id = delegate, delegate.model_id
        self.contexts = []

    @property
    def is_replay(self):
        return bool(getattr(self.delegate, 'is_replay', False))

    def start_session(self, system_prompt, tools=()):
        return CaptureSession(self, self.delegate.start_session(system_prompt, tools))


class CaptureSession:
    def __init__(self, owner, delegate):
        self.owner, self.delegate, self.first = owner, delegate, True

    @property
    def last_usage(self):
        return getattr(self.delegate, 'last_usage', {})

    def stream(self, messages, *, mode='AUTO'):
        if self.first:
            self.first = False
            self.owner.contexts.append(json.loads(messages[0]['text']))
        # RecordingToolSession keeps a reference to `messages`, which the assistant extends after the call;
        # recording a copy keeps each recorded request identical to what was really sent.
        return self.delegate.stream(deepcopy(messages), mode=mode)


class StubLectureModel:
    """Never reached: the assistant reads lectures with cache_only=True."""
    model_id = MODEL_ID

    def __getattr__(self, name):
        raise RuntimeError('SA-55 must not generate lectures')


# ---------------------------------------------------------------------------- one conversation

class Book:
    def __init__(self, doc_id, graph_version, store_path, *, replay, settings):
        self.runtime = PhaseBRuntime(settings=settings, allow_spend=not replay, mode='offline' if replay else 'gemini',
                                     store_path=store_path)
        self.runtime.record_dir = None
        self.graph = self.runtime.graph(doc_id, graph_version)
        self.store = self.runtime.store
        self.doc_id, self.graph_version = doc_id, graph_version


def prepare_store(doc_id, spec, directory):
    path = directory / f'{doc_id}.json'
    if path.exists():
        raise FileExistsError(f'{path} already exists')
    directory.mkdir(parents=True, exist_ok=True)
    if spec.startswith('copy:'):
        shutil.copyfile(ROOT / spec[5:], path)
    return path


def scope_of(book, name):
    if name == 'roadmap':
        return {'kind': 'roadmap'}
    module = book.graph.modules[name]
    node_ids = list(module.get('node_ids', []))
    return {'kind': 'module', 'node_ids': node_ids, 'module_id_at_creation': name,
            'graph_version_at_creation': book.graph_version}


def focus_id_of(book, name):
    matches = book.graph.lookup_concept(name)['matches']
    exact = [m for m in matches if m['name'] == name]
    if len(exact) != 1:
        raise ValueError(f'focus {name!r} does not resolve to one concept in {book.doc_id}')
    return exact[0]['node_id']


def build_assistant(book, model, tape, counters):
    graph, store, runtime = book.graph, book.store, book.runtime
    settings = runtime.b_settings
    clock = runtime.clock
    progress = ProgressUseCase(store, graph, clock=clock)
    guard = DailySpendGuard(store, settings=settings, clock=clock)
    lecture = LectureUseCase(StubLectureModel(), store, settings=settings, clock=clock, progress=progress,
                             spend_guard=guard)

    def get_lecture(concept, **kwargs):
        if not kwargs.get('cache_only'):
            counters['get_lecture'] += 1       # a model-chosen call; the focus read passes cache_only
        return lecture.make(graph.doc_id, book.graph_version, graph, concept, owner=kwargs.get('owner'),
                            cache_only=True)

    def make_quiz(scope, n=None, level=None, **kwargs):
        counters['make_quiz'] += 1
        return {'status': 'failed', 'reason': SUPPRESSED}

    def make_document(request, scope, **kwargs):
        counters['make_document'] += 1
        return {'status': 'failed', 'reason': SUPPRESSED}

    def search(query, *, scope='ưu tiên module', k=4, current_module_id=None):
        # Harness workaround, not a product change: AssistantUseCase asks for scope 'ưu tiên module', but
        # SearchDocumentB only accepts 'uu_tien_module' (see the report, section "Câu hỏi").
        mapped = SCOPE_ALIASES.get(scope, scope)
        return tape.call('search', [query, scope, k, current_module_id],
                         lambda: runtime.search(graph, query, scope=mapped, k=k, current_module_id=current_module_id))

    def lookup(query):
        return tape.call('lookup', [query], lambda: runtime.lookup(graph, query))

    return AssistantUseCase(graph, store, model, settings=settings, search=search, concept_lookup=lookup,
                            lecture=get_lecture, quiz=make_quiz, document=make_document, clock=clock,
                            progress=progress, spend_guard=guard)


def summarise_turn(row, index, question, result, error, wall_s, first_delta_ms, counters_delta, capture, focus_id):
    usage = (result or {}).get('usage', {})
    logs = (result or {}).get('tool_calls', [])
    tool_errors = []
    for log in logs:
        summary = log.get('result_summary')
        if isinstance(summary, dict) and isinstance(summary.get('error'), dict):
            code = summary['error'].get('code')
            tool_errors.append({'name': log['name'], 'code': code, 'suppressed': code == SUPPRESSED})
    focus_block = (capture or {}).get('focus') or {}
    answer = (result or {}).get('answer', '')
    label = focus_block.get('definition_source')
    return {
        'n': row['n'], 'turn': index + 1, 'owner': conversation_id(row), 'doc_id': row['doc_id'],
        'scope': row['scope'], 'kind': row['kind'], 'question': question,
        'status': (result or {}).get('status', 'loi'), 'error': error,
        'answer': answer, 'citations': len((result or {}).get('citations', [])),
        'usd': usage.get('usd', 0.0), 'ttft_ms': usage.get('ttft_ms'), 'wall_s': round(wall_s, 3),
        'first_delta_ms': first_delta_ms, 'rounds': usage.get('model_calls', 0),
        'input_tokens': usage.get('input_tokens', 0), 'output_tokens': usage.get('output_tokens', 0),
        'thought_tokens': usage.get('thought_tokens', 0),
        'tools': [log['name'] for log in logs], 'tool_args': [log['args'] for log in logs],
        'tool_errors': tool_errors, 'invalid_tool_calls': usage.get('invalid_tool_calls', 0),
        'content_tool_calls': dict(counters_delta),
        'reminders': len(((result or {}).get('graph_cards') or {}).get('reminders', [])),
        'outside_blocks': (result or {}).get('outside_document_blocks', 0),
        'refusal_text': answer == REFUSAL, 'warnings': (result or {}).get('warnings', []),
        'linked_node_ids': (result or {}).get('linked_node_ids', []),
        'focus_node_id_sent': focus_id, 'focus_node_id_echoed': (result or {}).get('focus_node_id'),
        'focus_definition_label': label,
        'focus_has_lecture_ideas': 'lecture_ideas' in focus_block,
        'answer_cites_definition_label': bool(label) and f'[{label}]' in answer,
        'module_cards': [c['node_id'] for c in ((result or {}).get('graph_cards') or {}).get('module_cards', [])],
    }


def run_conversation(row, book, plan, *, replay, gate=None, recordings=RECORDINGS):
    settings = book.runtime.b_settings
    owner = conversation_id(row)
    tape = Tape(recordings / f'{owner}-tape.json', replay=replay)
    path = recordings / f'{owner}.json'
    prompt_hash = context_hash(['sa55', owner, plan['model_id']])
    if replay:
        delegate = ReplayToolModel(path, prompt_hash=prompt_hash)
    else:
        delegate = RecordingToolModel(book.runtime.model('assistant'), path, prompt_hash=prompt_hash)
        if delegate.model_id != plan['model_id']:
            raise RuntimeError(f'unexpected model {delegate.model_id}')
    model = CaptureModel(delegate)
    counters = Counter()
    assistant = build_assistant(book, model, tape, counters)
    sessions = SessionUseCase(book.store, book.graph, settings=settings, clock=book.runtime.clock)
    session = sessions.create_session(owner, book.doc_id, scope_of(book, row['scope']))
    focus_id = focus_id_of(book, row['focus_name']) if row.get('focus_name') else None
    turns = []
    for index, question in enumerate(row['questions']):
        before = Counter(counters)
        seen = len(model.contexts)
        events = []
        started = time.perf_counter()
        first_delta = []
        if gate:
            gate.new_turn()

        def on_event(event):
            if event.get('event') == 'delta' and not first_delta:
                first_delta.append(round((time.perf_counter() - started) * 1000))

        result = error = None
        try:
            result = assistant.ask(book.doc_id, book.graph_version, session['session_id'], question, owner=owner,
                                   client_turn_id=f'{owner}-t{index + 1}', allow_spend=not replay,
                                   on_event=on_event, focus_node_id=focus_id)
        except Exception as exception:   # one failed turn must not stop the others
            error = f'{type(exception).__name__}: {exception}'
        wall = time.perf_counter() - started
        capture = model.contexts[seen] if len(model.contexts) > seen else None
        turn = summarise_turn(row, index, question, result, error, wall, first_delta[0] if first_delta else None,
                              counters - before, capture, focus_id)
        turns.append(turn)
        if gate:
            gate.assistant_usd += turn['usd']
            if gate.tripped:
                break
    return turns


# ---------------------------------------------------------------------------- dry run

def dry_run(plan):
    settings = make_settings()
    bs = BSettings()
    rounds = plan['max_rounds_per_turn']
    graphs, rows, problems = {}, [], []
    for doc_id, pin in plan['pins'].items():
        runtime = PhaseBRuntime(settings=settings, mode='offline', store_path=WORK / 'dryrun-unused.json')
        graphs[doc_id] = runtime.graph(doc_id, pin['graph_version'])
    total_turns = total_calls = 0
    brut = 0.0
    capped = 0.0
    embedding_queries = 0
    for row in plan['rows']:
        graph = graphs[row['doc_id']]
        book = type('B', (), {'graph': graph, 'graph_version': plan['pins'][row['doc_id']]['graph_version'],
                              'doc_id': row['doc_id']})
        store = InMemoryPhaseBStore()
        sessions = SessionUseCase(store, graph, settings=bs)
        try:
            scope = scope_of(book, row['scope'])
            if scope['kind'] == 'module' and not scope['node_ids']:
                problems.append(f"row {row['n']}: module {row['scope']} has no node_ids")
            session = sessions.create_session(conversation_id(row), row['doc_id'], scope)
            focus_id = focus_id_of(book, row['focus_name']) if row.get('focus_name') else None
            assistant = AssistantUseCase(graph, store, None, settings=bs)
            for index, question in enumerate(row['questions']):
                estimate = assistant.ask(row['doc_id'], book.graph_version, session['session_id'], question,
                                         owner=conversation_id(row), dry_run=True, focus_node_id=focus_id)
                per_round = estimate['usd_estimate'] + (estimate_cost(bs.model_id, bs.assistant_history_tokens, 0)
                                                        if index else 0)
                total_turns += 1
                total_calls += rounds
                brut += per_round * rounds
                capped += min(per_round * rounds, bs.assistant_max_usd + per_round)
                embedding_queries += 1 + rounds
                rows.append({'n': row['n'], 'turn': index + 1, 'usd_per_round': round(per_round, 6),
                             'focus_node_id': estimate.get('focus_node_id'), 'warnings': estimate.get('warnings')})
        except Exception as error:
            problems.append(f"row {row['n']}: {type(error).__name__}: {error}")
    concept_texts = sum(1 for graph in graphs.values() for node in graph.learnable_nodes.values())
    embedding_usd = estimate_cost(EMBEDDING_MODEL, embedding_queries * 120 + concept_texts * 150, 0)
    result = {
        'dry_run': True, 'network_calls': 0, 'turns': total_turns, 'conversations': len(plan['rows']),
        'max_llm_calls_no_retry': total_calls, 'llm_http_attempt_cap': plan['llm_http_attempt_cap'],
        'embedding_http_attempt_cap': plan['embedding_http_attempt_cap'],
        'usd_max_llm_unbounded_5_rounds': round(brut, 4),
        'usd_max_llm_with_product_turn_cap': round(capped, 4),
        'usd_max_embedding': round(embedding_usd, 5),
        'usd_max_total': round(brut + embedding_usd, 4),
        'cap_usd': plan['cap_usd'], 'per_turn_product_cap_usd': bs.assistant_max_usd,
        'within_cap': brut + embedding_usd <= plan['cap_usd'], 'problems': problems, 'rows': rows}
    WORK.mkdir(parents=True, exist_ok=True)
    DRYRUN.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, ensure_ascii=False, indent=2))
    return result


# ---------------------------------------------------------------------------- paid run and replay

def save_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')
    os.replace(temporary, path)


def paid_run(plan, *, resume):
    settings = make_settings()
    if settings.llm_transport != 'vertex':
        raise RuntimeError('SA-55 uses the configured Vertex transport')
    if RESULTS.exists() and not resume:
        raise FileExistsError('results already exist; use --resume or --replay, never spend twice')
    results = json.loads(RESULTS.read_text(encoding='utf-8')) if RESULTS.exists() else {
        'ticket': 'SA-55', 'model_id': plan['model_id'], 'cap_usd': plan['cap_usd'], 'status': 'running',
        'started_at': time.strftime('%Y-%m-%dT%H:%M:%S%z'), 'turns': [], 'skipped': []}
    done = Counter(t['n'] for t in results['turns'])
    gate = Gate(plan['cap_usd'], plan['llm_http_attempt_cap'], plan['embedding_http_attempt_cap'])
    gate.assistant_usd = sum(t['usd'] for t in results['turns'])
    store_dir = WORK / 'stores'
    books = {}
    for doc_id, pin in plan['pins'].items():
        path = store_dir / f'{doc_id}.json'
        if not path.exists():
            prepare_store(doc_id, pin['store'], store_dir)
        books[doc_id] = Book(doc_id, pin['graph_version'], path, replay=False, settings=settings)
    gate.embedding_usd = lambda: sum(r.get('cost_usd', 0) for book in books.values() for r in book.store.usage_rows()
                                     if r.get('purpose') == 'embedding')
    restore = install_gate(gate)
    per_turn_margin = BSettings().assistant_max_usd + 0.005
    try:
        for row in plan['rows']:
            if done[row['n']] == len(row['questions']):
                continue
            if done[row['n']]:
                raise RuntimeError(f"conversation {row['n']} is partly done; refusing to guess")
            if gate.tripped or gate.actual_usd + per_turn_margin > plan['cap_usd']:
                results['skipped'].append({'n': row['n'], 'reason': 'bo_qua_vi_tran', 'tripped': gate.tripped})
                save_json(RESULTS, results)
                continue
            turns = run_conversation(row, books[row['doc_id']], plan, replay=False, gate=gate)
            results['turns'].extend(turns)
            results['spent_usd_tokens'] = round(sum(t['usd'] for t in results['turns']), 6)
            results['llm_http_attempts'], results['embedding_http_attempts'] = gate.llm_attempts, gate.embed_attempts
            save_json(RESULTS, results)
            print(json.dumps({'n': row['n'], 'status': [t['status'] for t in turns],
                              'usd': round(sum(t['usd'] for t in turns), 5),
                              'total_usd': results['spent_usd_tokens']}, ensure_ascii=False), flush=True)
    finally:
        restore()
        results['status'] = 'complete' if not gate.tripped else 'stopped_by_cap'
        results['tripped'] = gate.tripped
        results['llm_http_attempts'], results['embedding_http_attempts'] = gate.llm_attempts, gate.embed_attempts
        results['embedding_usd_estimated'] = round(sum(
            r.get('cost_usd', 0) for book in books.values() for r in book.store.usage_rows()
            if r.get('purpose') == 'embedding'), 6)
        results['usage_rows'] = {doc: [r for r in book.store.usage_rows() if r.get('purpose') == 'embedding']
                                 for doc, book in books.items()}
        results['assistant_usd_from_tokens'] = round(sum(t['usd'] for t in results['turns']), 6)
        results['total_usd'] = round(results['assistant_usd_from_tokens'] + results['embedding_usd_estimated'], 6)
        results['finished_at'] = time.strftime('%Y-%m-%dT%H:%M:%S%z')
        save_json(RESULTS, results)
    print(json.dumps({k: results[k] for k in ('status', 'total_usd', 'assistant_usd_from_tokens',
                                               'embedding_usd_estimated', 'llm_http_attempts',
                                               'embedding_http_attempts')}, ensure_ascii=False))
    return results


COMPARE = ('status', 'answer', 'citations', 'rounds', 'input_tokens', 'output_tokens', 'thought_tokens', 'tools',
           'tool_args', 'tool_errors', 'linked_node_ids', 'reminders', 'outside_blocks', 'focus_node_id_echoed',
           'focus_definition_label', 'focus_has_lecture_ideas', 'answer_cites_definition_label', 'error',
           'content_tool_calls', 'module_cards', 'warnings')


def replay_run(plan, recordings=RECORDINGS, results_path=RESULTS):
    settings = make_settings()
    live = json.loads(results_path.read_text(encoding='utf-8'))
    expected = {(t['n'], t['turn']): t for t in live['turns']}
    directory = WORK / 'replay-stores'
    if directory.exists():
        shutil.rmtree(directory)
    books = {}
    for doc_id, pin in plan['pins'].items():
        books[doc_id] = Book(doc_id, pin['graph_version'], prepare_store(doc_id, pin['store'], directory),
                             replay=True, settings=settings)
    replayed, mismatches = [], []
    tripwire = Gate(0.0, 0, 0)       # any HTTP attempt during replay is refused and noted
    restore = install_gate(tripwire)
    for row in plan['rows']:
        if not any(t['n'] == row['n'] for t in live['turns']):
            continue
        turns = run_conversation(row, books[row['doc_id']], plan, replay=True, recordings=recordings)
        for turn in turns:
            want = expected[(turn['n'], turn['turn'])]
            for field in COMPARE:
                if turn[field] != want[field]:
                    mismatches.append({'n': turn['n'], 'turn': turn['turn'], 'field': field})
            if turn['usd'] != 0:
                mismatches.append({'n': turn['n'], 'turn': turn['turn'], 'field': 'usd_not_zero'})
        replayed.extend(turns)
    restore()
    if tripwire.tripped:
        mismatches.append({'field': 'network_attempt_during_replay', 'detail': tripwire.tripped})
    out = {'turns_replayed': len(replayed), 'turns_live': len(live['turns']), 'replay_usd': sum(t['usd'] for t in replayed),
           'network_calls': 1 if tripwire.tripped else 0, 'fields_compared': list(COMPARE), 'mismatches': mismatches}
    save_json(REPLAY_RESULTS, out)
    print(json.dumps(out, ensure_ascii=False))
    return out


# ---------------------------------------------------------------------------- report

def percentile(values, q):
    values = sorted(values)
    return values[max(0, math.ceil(q * len(values)) - 1)] if values else None


def rate(numerator, denominator):
    return f'{numerator}/{denominator} ({100 * numerator / denominator:.0f}%)' if denominator else '0/0'


def clip(text, size=70):
    text = ' '.join(str(text).split())
    return (text[:size] + '…') if len(text) > size else text


def model_ttfts(turns):
    """TTFT of the first model call of every turn, from the recordings (no search or embedding wait)."""
    result = {}
    for n in sorted({t['n'] for t in turns}):
        path = RECORDINGS / f'sa55-{n:02d}.json'
        if not path.exists():
            continue
        sessions = json.loads(path.read_text(encoding='utf-8'))['sessions']
        for index, session in enumerate(sessions):
            done = [e for e in session['calls'][0]['events'] if e['type'] == 'done']
            result[(n, index + 1)] = done[-1].get('ttft_ms') if done else None
    return result


def write_report(plan, *, status='dang chay'):
    live = json.loads(RESULTS.read_text(encoding='utf-8')) if RESULTS.exists() else None
    replay = json.loads(REPLAY_RESULTS.read_text(encoding='utf-8')) if REPLAY_RESULTS.exists() else None
    dry = json.loads(DRYRUN.read_text(encoding='utf-8')) if DRYRUN.exists() else None
    lines = [f'# SA-55 — Lượt thật trợ lý gộp (2026-10-22)', '', f'**Trạng thái:** {status}', '']
    lines += ['## Duyệt tiền', '',
              'Chủ dự án duyệt trước, nguyên văn tin nhắn ngày 2026-10-22: **"tôi duyệt tiền"**. Phạm vi: lượt thật của vé SA-55, '
              'trần cứng 0,50 USD, chỉ `gemini-3.1-flash-lite`.', '']
    if dry:
        lines += ['## Dry-run (không gọi mạng)', '',
                  f"- Lượt hỏi: {dry['turns']} trên {dry['conversations']} hội thoại; số lời gọi mô hình tối đa: {dry['max_llm_calls_no_retry']} "
                  f"(5 vòng mỗi lượt); trần cứng HTTP: {dry['llm_http_attempt_cap']} cho mô hình, {dry['embedding_http_attempt_cap']} cho embedding.",
                  f"- USD tối đa dự toán, bảng giá chung, 5 vòng đầy mỗi lượt không có trần sản phẩm: {dry['usd_max_llm_unbounded_5_rounds']}; "
                  f"có trần sản phẩm {dry['per_turn_product_cap_usd']} USD mỗi lượt: {dry['usd_max_llm_with_product_turn_cap']}; "
                  f"embedding: {dry['usd_max_embedding']}. Tổng dự toán tối đa: **{dry['usd_max_total']} USD** (trần {dry['cap_usd']}).", '']
    if not live:
        REPORT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
        return
    turns = sorted(live['turns'], key=lambda t: (t['n'], t['turn']))
    model_ttft = model_ttfts(turns)
    answered = [t for t in turns if t['status'] in {'answered', 'partial'}]
    lines += ['## Cách chạy', '',
              '- Mỗi hội thoại một `owner` riêng (`sa55-01` … `sa55-31`, theo số dòng của bảng), để trần ngày 0,20 USD mỗi người học không chặn giữa chừng; '
              'không đổi trần trong mã sản phẩm.',
              '- Kho Pha B: doc-6, naive-bayes, nhap-mon-ml mỗi cuốn một kho JSON mới trong `tmp/sa55/stores/`; doc-1 là bản chép của '
              '`artifacts/phase_b/doc-1-rebuild-20261020.json`. Không dùng `live.json`.',
              '- `get_lecture` đọc cache (`cache_only=True`), `make_quiz` và `make_document` trả lỗi `sa55_suppressed` ("chưa có"); không sinh nội dung có tiền. '
              'Số lần mô hình gọi ba công cụ này ghi ở cột công cụ và ở phần tổng hợp.',
              f"- Chặn HTTP: mô hình {plan['llm_http_attempt_cap']} lời gọi (5 vòng x 36 lượt = 180, cộng 36 dự phòng thử lại), "
              f"embedding {plan['embedding_http_attempt_cap']}. Số vòng mô hình đã gọi (mỗi vòng một lời gọi HTTP): {sum(t['rounds'] for t in turns)}; "
              f"số lời gọi embedding ghi nhận bởi cổng ở lần chạy cuối: {live.get('embedding_http_attempts')} (lần đầu bị dừng sớm, xem mục Câu hỏi).",
              '- Mô hình qua Vertex (`DOC2ROADMAP_LLM_TRANSPORT=vertex`). TTFT là số của sản phẩm (từ lúc bắt đầu `ask` tới token hay lời gọi công cụ đầu tiên của mô hình, '
              'kể cả thời gian tìm kiếm trước đó); "tổng giây" là đồng hồ tường của `ask`.', '']
    lines += ['## Chi phí', '',
              f"- Chi thật từ token trả về (trợ lý): **{live.get('assistant_usd_from_tokens')} USD**.",
              f"- Embedding (tìm kiếm, tra khái niệm; ước tính theo giá chung, không lấy từ token): {live.get('embedding_usd_estimated')} USD.",
              f"- Tổng: **{live.get('total_usd')} USD** — dự toán tối đa {dry['usd_max_total'] if dry else '?'} USD, trần cứng {plan['cap_usd']} USD.",
              f"- Trạng thái chạy: {live.get('status')}; bị chặn: {live.get('tripped')}; lượt bỏ qua vì trần: "
              f"{[s['n'] for s in live.get('skipped', [])]}.", '']
    lines += ['## Từng lượt', '',
              '| # | lượt | cuốn | phiên | loại | câu hỏi | trạng thái | USD | TTFT ms | TTFT mô hình ms | giây | vòng | công cụ | lỗi công cụ | nhắc nền | ngoài tài liệu / từ chối |',
              '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for t in turns:
        tools = Counter(t['tools'])
        tool_text = ', '.join(f'{k}x{v}' if v > 1 else k for k, v in tools.items()) or '-'
        errors = ', '.join(f"{e['name']}:{e['code']}" for e in t['tool_errors']) or '-'
        outside = []
        if t['outside_blocks']:
            outside.append(f"{t['outside_blocks']} khối :::outside_document")
        if t['status'] == 'not_in_document':
            outside.append('not_in_document')
        if t['status'] == 'insufficient_context':
            outside.append('KHONG_DU')
        if t['refusal_text']:
            outside.append('câu từ chối chuẩn')
        lines.append(f"| {t['n']} | {t['turn']} | {t['doc_id']} | {t['scope']} | {t['kind']} | {clip(t['question'], 48)} | "
                     f"{t['status']}{' ' + clip(t['error'], 40) if t['error'] else ''} | {t['usd']:.5f} | "
                     f"{t['ttft_ms'] if t['ttft_ms'] is not None else '-'} | {model_ttft.get((t['n'], t['turn']), '-')} | {t['wall_s']:.1f} | {t['rounds']} | {tool_text} | {errors} | "
                     f"{'có (' + str(t['reminders']) + ')' if t['reminders'] else 'không'} | {', '.join(outside) or '-'} |")
    lines.append('')
    ttft = [t['ttft_ms'] for t in turns if t['ttft_ms'] is not None]
    pure = [v for v in model_ttft.values() if v is not None]
    walls = [t['wall_s'] for t in turns if not t['error']]
    lines += ['## Tổng hợp', '',
              f"- Lượt hỏi chạy: {len(turns)}; trả lời (`answered`/`partial`): {len(answered)}; "
              f"từ chối hay ngoài tài liệu (`not_in_document`, `insufficient_context`): "
              f"{sum(t['status'] in {'not_in_document', 'insufficient_context'} for t in turns)}; "
              f"lỗi (`error`, exception, `budget_exhausted`, `daily_limit`): "
              f"{sum(t['status'] in {'error', 'loi', 'budget_exhausted', 'daily_limit'} for t in turns)}; "
              f"phân bố trạng thái: {dict(Counter(t['status'] for t in turns))}.",
              f"- TTFT (ms, nearest-rank): p50 {median(ttft) if ttft else '-'}, p90 {percentile(ttft, .9)} (n={len(ttft)}).",
              f"- TTFT thuần của mô hình (ms, chỉ lời gọi mô hình đầu tiên của lượt, không có phần tìm kiếm và embedding trước đó): "
              f"p50 {median(pure) if pure else '-'}, p90 {percentile(pure, .9)} (n={len(pure)}). Phần chênh với TTFT ở trên là thời gian chờ embedding và tra khái niệm.",
              f"- Tổng giây mỗi lượt: p50 {median(walls) if walls else '-'}, p90 {percentile(walls, .9)} (n={len(walls)}).",
              f"- USD mỗi câu: trung bình {sum(t['usd'] for t in turns) / max(len(turns), 1):.5f}; p50 {median([t['usd'] for t in turns]) if turns else '-'}; "
              f"p90 {percentile([t['usd'] for t in turns], .9)}; lớn nhất {max((t['usd'] for t in turns), default=0):.5f} (trần sản phẩm 0,01 mỗi lượt).",
              f"- Số vòng mô hình: {dict(sorted(Counter(t['rounds'] for t in turns).items()))}.",
              f"- Lượt có khối nhắc nền: {sum(bool(t['reminders']) for t in turns)}.", '']
    calls, wrong, suppressed = Counter(), Counter(), Counter()
    for t in turns:
        for name in t['tools']:
            calls[name] += 1
        for e in t['tool_errors']:
            if e['suppressed']:
                suppressed[e['name']] += 1
            elif e['code'] in MODEL_ERRORS:
                wrong[e['name']] += 1
    lines += ['### Tỉ lệ gọi công cụ sai', '',
              'Sai = kết quả công cụ là lỗi `invalid_tool_call` (tham số sai), `tool_error` (khái niệm không rõ, tham số hỏng) hay `result_limit`. '
              'Lỗi `sa55_suppressed` do bộ chạy chặn việc sinh nội dung nên tính riêng, không là lỗi của mô hình.', '',
              '| công cụ | số lần gọi | gọi sai | tỉ lệ sai | bị bộ chạy chặn |', '|---|---|---|---|---|']
    flagged = []
    for name in sorted(calls):
        share = wrong[name] / calls[name]
        mark = ' **> 10%**' if share > .10 else ''
        if share > .10:
            flagged.append(name)
        lines.append(f'| {name} | {calls[name]} | {wrong[name]} | {rate(wrong[name], calls[name])}{mark} | {suppressed[name] or "-"} |')
    all_calls, all_wrong = sum(calls.values()), sum(wrong.values())
    lines += ['', f'Tổng: {rate(all_wrong, all_calls)}. Công cụ vượt 10%: {", ".join(flagged) if flagged else "không có"}.']
    if flagged:
        lines += ['', f'> **GHI NỔI BẬT:** tỉ lệ gọi sai của {", ".join(flagged)} vượt 10%; báo chủ dự án, không tự đổi mô hình.']
    content = Counter()
    for t in turns:
        content.update(t['content_tool_calls'])
    detail = [f"- dòng {t['n']} lượt {t['turn']}: `{e['name']}` → `{e['code']}`{' (bộ chạy chặn)' if e['suppressed'] else ''}"
              for t in turns for e in t['tool_errors']]
    others = ', '.join(f'{k} {calls[k]}' for k in ('lookup_concept', 'why_here', 'path_to', 'traverse', 'get_module_info'))
    lines += ['', f"Số lần mô hình gọi ba công cụ tạo nội dung: get_lecture {content['get_lecture']}, make_quiz {content['make_quiz']}, "
              f"make_document {content['make_document']}. Các công cụ khác: {others}.",
              f"Mô hình chỉ gọi công cụ ở {sum(bool(t['tools']) for t in turns)}/{len(turns)} lượt ({all_calls} lời gọi); mẫu số mỗi công cụ rất nhỏ, "
              'nên tỉ lệ sai ở trên chưa đủ để kết luận.', '']
    if detail:
        lines += ['Lỗi gọi công cụ, chi tiết:', *detail, '']
    lines += ['## Lượt 28–31 (tiêu điểm `focus_node_id`)', '',
              '| # | tiêu điểm (id) | `linked_node_ids` | liên kết đúng tiêu điểm? | `search_document` | `lookup_concept` | `focus` có ý bài giảng? | nhãn câu định nghĩa | trích nhãn đó? |',
              '|---|---|---|---|---|---|---|---|---|']
    names = {r['n']: r['focus_name'] for r in plan['rows'] if r.get('focus_name')}
    expected_linked = {r['n']: r['expected_linked_id'] for r in plan['rows'] if r.get('expected_linked_id')}
    for t in turns:
        if t['n'] not in names:
            continue
        counts = Counter(t['tools'])
        linked = t['linked_node_ids']
        want = expected_linked.get(t['n'], t['focus_node_id_sent'])
        same = linked == [want]
        note = ('đúng: tiêu điểm' if want == t['focus_node_id_sent'] else 'đúng: đơn ánh, theo vé') if same else (
            'SAI' if linked else 'rỗng')
        lines.append(f"| {t['n']} | {names[t['n']]} (`{t['focus_node_id_sent']}`) | {linked} | {note} | {counts['search_document']} | "
                     f"{counts['lookup_concept']} | {'có' if t['focus_has_lecture_ideas'] else 'không'} | {t['focus_definition_label']} | "
                     f"{'có' if t['answer_cites_definition_label'] else 'không'} |")
    lines += ['', 'Lượt 29 hỏi "Phần này khác đơn ánh thế nào?": câu nêu tên khái niệm khác nên `linked_node_ids` phải là đơn ánh, không phải tiêu điểm Song ánh; '
              'cột liên kết dùng kỳ vọng này (id đơn ánh lấy theo tên trong graph ghim). Id tiêu điểm lấy theo tên trong graph ghim, như bảng.', '']
    if replay:
        lines += ['## Phát lại 0 USD', '',
                  f"- Phát lại {replay['turns_replayed']}/{replay['turns_live']} lượt từ bản ghi, không gọi mạng, chi {replay['replay_usd']} USD.",
                  f"- Trường so khớp với lượt thật: {', '.join(replay['fields_compared'])}.",
                  f"- Số điểm lệch: **{len(replay['mismatches'])}** {replay['mismatches'][:5] if replay['mismatches'] else ''}.", '']
    lines += QUESTIONS
    REPORT.write_text('\n'.join(lines) + '\n', encoding='utf-8')


QUESTIONS = [
    '## Câu hỏi và điều đáng chú ý (không sửa mã sản phẩm)', '',
    "1. **Lỗi sản phẩm làm hỏng lượt module khi chạy thật.** `AssistantUseCase._search` và công cụ `search_document` mặc định `scope='ưu tiên module'`, "
    'còn `SearchDocumentB.execute` chỉ nhận `uu_tien_module`, `ca_tai_lieu` hay `module:<index>`. Với phiên module, lượt chạy thật đầu tiên (dòng 1–3) '
    'dừng ngay bằng `ValueError: scope phải là ...` với 0 USD (lần chạy đầu, lưu ở `failed_attempts` trong `tmp/sa55/results.json`); phiên toàn lộ trình không bị vì dùng `all`. '
    'Bộ chạy đổi riêng chuỗi này (`SCOPE_ALIASES` trong `sa55_assistant_run.py`) rồi chạy lại 1–3; mọi số ở trên là với phép đổi đó. '
    'Cần một vé sửa ở sản phẩm (thống nhất giá trị `scope` giữa `assistant.py` và `retrieval.py`). Test của trợ lý không bắt được vì dùng hàm tìm kiếm giả.',
    '2. **Ghi âm hội thoại nhiều vòng bị hỏng.** `RecordingToolSession.stream` lưu tham chiếu tới `messages`, mà trợ lý nối thêm tin nhắn vào cùng danh sách sau lời gọi; '
    'bản ghi của vòng 1 thành 3 tin nhắn và phát lại báo `tool replay has no unused session matching this request`. Bộ chạy truyền bản sao sâu (`CaptureSession`). '
    'Mã sản phẩm cần sửa ở `src/doc2roadmap/infrastructure/llm/phase_b.py`.',
    '3. **Chờ embedding chiếm gần hết TTFT.** Mỗi lời gọi embedding truy vấn (39 lần) ghi `elapsed_ms` trung vị 13,4 s, từ 3,8 đến 16,7 s (khoảng 13 s ở dòng 1–23, khoảng 4 s ở các dòng sau); '
    'tạo chỉ mục khái niệm doc-1 lần đầu (277 khái niệm) mất 232 s. TTFT p50 của sản phẩm vì vậy là 15,8 s trong khi TTFT thuần của mô hình p50 là 0,95 s. '
    'Chưa tìm nguyên nhân (nghi lấy token Vertex hoặc hạn mức); cần xem riêng trước khi lấy số TTFT này làm số của sản phẩm.',
    '4. **Mô hình rất ít dùng công cụ.** 33 trong 36 lượt trả lời ở vòng 1 với ngữ cảnh nạp sẵn; không có lời gọi `lookup_concept`, `get_lecture`, `make_quiz`, `make_document`. '
    'Tỉ lệ gọi sai theo công cụ vì thế không đủ mẫu; nếu SA-10 cần số này thì cần bộ câu hỏi buộc dùng công cụ (ngoài phạm vi vé này).',
    '5. **Lần chạy đầu bị dừng sau 4 hội thoại** (thấy dòng 1–3 lỗi ở 0 USD), sửa bộ chạy, rồi chạy tiếp (`--resume`) từ dòng 1; dòng 4 giữ kết quả lần đầu. '
    'Chi thật tổng đã gồm cả lần đầu. Số lời gọi embedding ở cổng chỉ phản ánh lần chạy sau.', '',
]


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--dry-run', action='store_true')
    mode.add_argument('--allow-spend', action='store_true')
    mode.add_argument('--replay', action='store_true')
    mode.add_argument('--report', action='store_true')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    check_code_path()
    plan = load_plan()
    if args.allow_spend:
        if not 0 < plan['cap_usd'] <= 0.50:
            raise ValueError('SA-55 hard cap must be in (0, 0.50] USD')
        paid_run(plan, resume=args.resume)
    elif args.replay:
        replay_run(plan)
    elif args.report:
        write_report(plan, status=os.environ.get('SA55_STATUS', 'dang chay'))
    else:
        dry_run(plan)


if __name__ == '__main__':
    sys.exit(main())
