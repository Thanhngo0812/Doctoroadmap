"""SA-59: đo thời gian chờ trước lời gọi mô hình đầu tiên của trợ lý. 0 USD, không mạng.

Embedding giả (độ trễ cố định mỗi lời gọi, vector tất định theo văn bản) và mô hình giả (trả lời ngay).
Mỗi lượt của bộ câu SA-55 trên doc-1 v8 và nhap-mon-ml v50 chạy qua PhaseBRuntime thật; chỉ cổng embedding
và mô hình bị thay. Dữ liệu đồ thị và chỉ mục chỉ đọc từ artifacts/ của worktree; kho Pha B là JSON mới trong tmp/.

  python scripts/phase-b/sa59_do_cho.py --label truoc          # ghi tmp/sa59-truoc.json
  python scripts/phase-b/sa59_do_cho.py --label sau
  python scripts/phase-b/sa59_do_cho.py --compare tmp/sa59-truoc.json tmp/sa59-sau.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import shutil
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from statistics import median

import doc2roadmap
from doc2roadmap.application.phase_b import concept_index, retrieval
from doc2roadmap.application.phase_b.sessions import SessionUseCase
from doc2roadmap.application.ports.phase_b import Delta, Done
from doc2roadmap.composition_phase_b import PhaseBRuntime
import doc2roadmap.composition_phase_b as composition
from doc2roadmap.config import Settings
from doc2roadmap.domain.retrieval import HybridRetriever
from doc2roadmap.infrastructure.artifacts.json_store import JsonArtifactStore

ROOT = Path(__file__).resolve().parents[2]
PLAN = Path(__file__).with_name('sa55_plan.json')
DOCS = ('doc-1', 'nhap-mon-ml')
SITES = {('SearchDocumentB', 'execute'): 'tim_kiem',
         ('IndexConcepts', 'lookup'): 'lookup_concept_cau_hoi',
         ('IndexConcepts', 'execute'): 'lookup_concept_chi_muc'}
STAGES = ('nap_do_thi', 'nap_chi_muc', 'kiem_tuong_thich', 'dung_xep_hang', 'embedding', 'xep_hang',
          'bo_nho_khai_niem', 'nap_do_thi_khai_niem', 'xep_hang_khai_niem')

TURN = {'ms': defaultdict(float), 'calls': Counter(), 'embed': [], 'first_model': None}
STATE = {'in_load': False, 'latency': 0.3, 'hits': None}


def reset_turn():
    TURN['ms'].clear()
    TURN['calls'].clear()
    TURN['embed'].clear()
    TURN['first_model'] = None


def timed(name, function):
    def wrapper(*args, **kwargs):
        started = time.perf_counter()
        try:
            return function(*args, **kwargs)
        finally:
            TURN['ms'][name] += (time.perf_counter() - started) * 1000
            TURN['calls'][name] += 1
    wrapper.__wrapped__ = function
    return wrapper


def install_timers():
    original_load = retrieval.load_learning_graph

    def load(*args, **kwargs):
        STATE['in_load'] = True
        try:
            return original_load(*args, **kwargs)
        finally:
            STATE['in_load'] = False
    retrieval.load_learning_graph = timed('nap_do_thi', load)
    retrieval.assert_retrieval_compatible = timed('kiem_tuong_thich', retrieval.assert_retrieval_compatible)
    retrieval.retriever_from_payload = timed('dung_xep_hang', retrieval.retriever_from_payload)
    retrieval.build_module_assignments = timed('dung_xep_hang', retrieval.build_module_assignments)
    HybridRetriever.search = timed('xep_hang', HybridRetriever.search)
    JsonArtifactStore.load_latest_retrieval = timed('nap_chi_muc', JsonArtifactStore.load_latest_retrieval)
    load_graph = JsonArtifactStore.load_graph

    def store_load_graph(self, doc_id, version):          # only the call IndexConcepts.execute makes
        if STATE['in_load']:
            return load_graph(self, doc_id, version)
        return timed('nap_do_thi_khai_niem', load_graph)(self, doc_id, version)
    JsonArtifactStore.load_graph = store_load_graph
    concept_index.lookup_by_description = timed('xep_hang_khai_niem', concept_index.lookup_by_description)


class FakeEmbedding:
    """Fixed latency per call, deterministic vector per text; counts calls with their call site."""

    def __init__(self, *args, model='gemini-embedding-001', output_dimensionality=768, **kwargs):
        self._model, self._dim = model, output_dimensionality

    identifier = 'sa59-fake-embedding'

    @property
    def embedding_model_id(self):
        return f'{self._model}:{self._dim}'

    def embed(self, requests):
        site = 'khac'
        frame = sys._getframe(1)
        while frame is not None:
            owner = type(frame.f_locals.get('self')).__name__
            label = SITES.get((owner, frame.f_code.co_name))
            if label:
                site = label
                break
            frame = frame.f_back
        started = time.perf_counter()
        time.sleep(STATE['latency'])
        vectors = []
        for request in requests:
            seed = int.from_bytes(hashlib.sha256(f'{request.task_type}|{request.text}'.encode()).digest()[:8], 'big')
            rng = random.Random(seed)
            vector = [rng.gauss(0, 1) for _ in range(self._dim)]
            norm = sum(v * v for v in vector) ** 0.5
            vectors.append([v / norm for v in vector])
        elapsed = (time.perf_counter() - started) * 1000
        TURN['ms']['embedding'] += elapsed
        TURN['calls']['embedding'] += 1
        TURN['embed'].append({'site': site, 'texts': len(requests), 'ms': round(elapsed)})
        return vectors


class FakeSession:
    last_usage = {}

    def stream(self, messages, *, mode='AUTO'):
        if TURN['first_model'] is None:
            TURN['first_model'] = time.perf_counter()
        yield Delta('Không đủ nguồn.')
        yield Done({})


class FakeModel:
    model_id = 'gemini-3.1-flash-lite'
    is_replay = False

    def start_session(self, system_prompt, tools=()):
        return FakeSession()


def block_network():
    from doc2roadmap.infrastructure.embedding import gemini as embedding_transport
    from doc2roadmap.infrastructure.llm import phase_b as llm_transport

    def refuse(*args, **kwargs):
        raise RuntimeError('SA-59 là vé 0 USD: cấm gọi mạng')
    embedding_transport.urlopen = llm_transport.urlopen = refuse


def scope_of(graph, name):
    if name == 'roadmap':
        return {'kind': 'roadmap'}
    module = graph.modules[name]
    return {'kind': 'module', 'node_ids': list(module.get('node_ids', [])), 'module_id_at_creation': name,
            'graph_version_at_creation': graph.graph_version}


def focus_id_of(graph, name):
    matches = [m for m in graph.lookup_concept(name)['matches'] if m['name'] == name]
    if len(matches) != 1:
        raise ValueError(f'focus {name!r} không xác định trong {graph.doc_id}')
    return matches[0]['node_id']


def percentile(values, q):
    values = sorted(values)
    return values[min(len(values) - 1, int(q * len(values)))] if values else 0


def run(label, latency, out_dir):
    plan = json.loads(PLAN.read_text(encoding='utf-8'))
    if Path(doc2roadmap.__file__).resolve().parents[1] != ROOT / 'src':
        raise RuntimeError('doc2roadmap không nạp từ worktree này; đặt PYTHONPATH')
    STATE['latency'] = latency
    block_network()
    install_timers()
    composition.GeminiEmbedding = FakeEmbedding
    settings = Settings(_env_file=None, artifact_dir=ROOT / 'artifacts')

    searches = []
    original_search = PhaseBRuntime.search

    def recording_search(self, graph, query, **kwargs):
        result = original_search(self, graph, query, **kwargs)
        searches.append({'doc_id': graph.doc_id, 'query': query, 'scope': kwargs.get('scope'),
                         'k': kwargs.get('k'), 'current_module_id': kwargs.get('current_module_id'),
                         'hits': [[row['chunk_id'], row['score']] for row in result]})
        return result
    PhaseBRuntime.search = recording_search

    work = ROOT / 'tmp' / f'sa59-{label}'
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    runtimes, graphs, turns = {}, {}, []
    for doc_id in DOCS:
        runtimes[doc_id] = PhaseBRuntime(settings=settings, allow_spend=True, mode='gemini',
                                         store_path=work / f'{doc_id}.json')
        runtimes[doc_id].record_dir = None
        runtimes[doc_id]._models['assistant'] = FakeModel()
        graphs[doc_id] = runtimes[doc_id].graph(doc_id, plan['pins'][doc_id]['graph_version'])
    for row in plan['rows']:
        if row['doc_id'] not in DOCS:
            continue
        doc_id = row['doc_id']
        runtime, graph = runtimes[doc_id], graphs[doc_id]
        owner = f"sa59-{row['n']:02d}"
        sessions = SessionUseCase(runtime.store, graph, settings=runtime.b_settings, clock=runtime.clock)
        session = sessions.create_session(owner, doc_id, scope_of(graph, row['scope']))
        focus = focus_id_of(graph, row['focus_name']) if row.get('focus_name') else None
        for index, question in enumerate(row['questions']):
            reset_turn()
            before = len(searches)
            assistant = runtime.assistant(graph)          # như máy chủ xem trước: dựng mới mỗi yêu cầu
            started = time.perf_counter()
            result = assistant.ask(doc_id, graph.graph_version, session['session_id'], question, owner=owner,
                                   client_turn_id=f'{owner}-t{index + 1}', allow_spend=True, focus_node_id=focus)
            first = TURN['first_model']
            wait = ((first if first is not None else time.perf_counter()) - started) * 1000
            stages = {name: round(TURN['ms'].get(name, 0.0), 1) for name in STAGES}
            stages['khac_dung_ngu_canh'] = round(max(0.0, wait - sum(stages.values())), 1)
            turns.append({
                'n': row['n'], 'turn': index + 1, 'doc_id': doc_id,
                'session': 'lo_trinh' if row['scope'] == 'roadmap' else 'module',
                'question': question, 'status': result.get('status'),
                'cho_toi_mo_hinh_ms': round(wait, 1), 'stages_ms': stages,
                'embedding_calls': len(TURN['embed']), 'embedding_sites': list(TURN['embed']),
                'embedding_texts': sum(item['texts'] for item in TURN['embed']),
                'search_hits': searches[before:]})
    out = {'label': label, 'latency_ms': latency * 1000, 'turns': turns}
    out_path = Path(out_dir) / f'sa59-{label}.json'
    out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding='utf-8')
    (Path(out_dir) / f'sa59-{label}-tim-kiem.json').write_text(
        json.dumps([hit for turn in turns for hit in turn['search_hits']], ensure_ascii=False, indent=1),
        encoding='utf-8')
    summarise(out)
    return out


def summarise(out):
    print(f"nhãn={out['label']} trễ embedding giả={out['latency_ms']:.0f} ms, {len(out['turns'])} lượt")
    for kind in ('module', 'lo_trinh', None):
        rows = [t for t in out['turns'] if kind is None or t['session'] == kind]
        waits = [t['cho_toi_mo_hinh_ms'] for t in rows]
        calls = [t['embedding_calls'] for t in rows]
        print(f"  {kind or 'tất cả':9} lượt={len(rows):2} chờ p50={median(waits):8.0f} p90={percentile(waits, .9):8.0f} ms; "
              f"embedding/lượt tb={sum(calls) / len(calls):.2f} tổng={sum(calls)}")


def compare(path_a, path_b):
    a = json.loads(Path(path_a).read_text(encoding='utf-8'))
    b = json.loads(Path(path_b).read_text(encoding='utf-8'))
    key = lambda t: (t['n'], t['turn'])
    if [key(t) for t in a['turns']] != [key(t) for t in b['turns']]:
        print('KHÁC: danh sách lượt không trùng')
        return 1
    bad = 0
    for left, right in zip(a['turns'], b['turns']):
        if left['search_hits'] != right['search_hits']:
            # same chunk_id order is the contract; scores are compared too (same code path)
            bad += 1
            print(f"KHÁC lượt {key(left)}: chunk_id/điểm không trùng")
    print(f"so tìm kiếm: {len(a['turns'])} lượt, {sum(len(t['search_hits']) for t in a['turns'])} lời gọi tìm kiếm, "
          f"khác {bad}")
    return 1 if bad else 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--label')
    parser.add_argument('--latency', type=float, default=0.3)
    parser.add_argument('--out-dir', default=str(ROOT / 'tmp'))
    parser.add_argument('--compare', nargs=2)
    args = parser.parse_args()
    if args.compare:
        sys.exit(compare(*args.compare))
    if not args.label:
        parser.error('cần --label hoặc --compare')
    run(args.label, args.latency, args.out_dir)
