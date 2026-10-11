"""V4-14: strict metrics alongside the unchanged historical metrics."""
import sys
import argparse
import ctypes
import statistics
import subprocess
import time
from collections import Counter
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / '.venv/Lib/site-packages'))
sys.path.insert(0, str(ROOT / 'scripts/thu-a1'))
import doc_nhe
import so_chunk_doc_nhe
import networkx as nx


def heading_score(reference, candidate):
    reference = [n for n in reference if n['node_type'] in {'title', 'section_header'}]
    candidate = [n for n in candidate if n['node_type'] in {'title', 'section_header'}]
    graph = nx.Graph()
    left = [('r', i) for i in range(len(reference))]
    graph.add_nodes_from(left, bipartite=0)
    graph.add_nodes_from([('c', j) for j in range(len(candidate))], bipartite=1)
    for i, a in enumerate(reference):
        x = doc_nhe.words(a['text'])
        for j, b in enumerate(candidate):
            y = doc_nhe.words(b['text'])
            if a.get('page') != b.get('page') or not x or not y:
                continue
            short, long = sorted((x, y), key=len)
            if len(short) / len(long) >= .8 and any(long[k:k+len(short)] == short for k in range(len(long)-len(short)+1)):
                graph.add_edge(('r', i), ('c', j))
    matched = nx.algorithms.bipartite.maximum_matching(graph, top_nodes=left)
    tp = sum(k in matched for k in left)
    p, r = tp / max(len(candidate), 1), tp / max(len(reference), 1)
    return {'tp': tp, 'fp': len(candidate)-tp, 'fn': len(reference)-tp,
            'precision': p, 'recall': r, 'f1': 2*p*r/max(p+r, 1e-12)}


def leaf_score(reference, candidate):
    hits = eligible = 0
    sets = [so_chunk_doc_nhe.words(n.text) for n in candidate]
    for chunk in reference:
        words = so_chunk_doc_nhe.words(chunk.text)
        options = [(len(words & sets[j]) / max(len(words | sets[j]), 1), -j)
                   for j, other in enumerate(candidate) if abs((other.page or 0)-(chunk.page or 0)) <= 2]
        if not options:
            continue
        similarity, negative_index = max(options)
        if similarity < .5:
            continue
        eligible += 1
        other = candidate[-negative_index]
        a = doc_nhe.words(chunk.section_path[-1]) if chunk.section_path else []
        b = doc_nhe.words(other.section_path[-1]) if other.section_path else []
        hits += bool(a and a == b)
    return {'hits': hits, 'eligible': eligible, 'total': len(reference),
            'share': hits/max(len(reference), 1), 'eligible_share': eligible/max(len(reference), 1)}


def peak_rss_mb():
    if sys.platform != 'win32':
        return None
    from ctypes import wintypes
    class Memory(ctypes.Structure):
        _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
            (n, ctypes.c_size_t) for n in ('PeakWorkingSetSize', 'WorkingSetSize', 'QuotaPeakPagedPoolUsage',
            'QuotaPagedPoolUsage', 'QuotaPeakNonPagedPoolUsage', 'QuotaNonPagedPoolUsage', 'PagefileUsage', 'PeakPagefileUsage')]
    memory = Memory()
    memory.cb = ctypes.sizeof(memory)
    kernel, psapi = ctypes.WinDLL('kernel32'), ctypes.WinDLL('psapi')
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Memory), wintypes.DWORD]
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(memory), memory.cb):
        raise ctypes.WinError()
    return memory.PeakWorkingSetSize / 1024**2


def evaluate_book(out, key):
    import joblib
    import numpy as np
    import hoc_tieu_de as learn
    from doc2roadmap.domain.models import DocumentNode, DocumentTree
    from doc2roadmap.infrastructure.text import SentencePieceTokenCounter
    pinned = learn.manifest(out)
    book = next(b for b in pinned['books'] if b['id'] == key)
    data = learn.read(out / 'datasets' / (key + '.json'))
    if data['fingerprint'] != learn.code_fingerprint():
        raise ValueError('Stale dataset')
    tree = learn.read(ROOT / book['tree'])
    settings = {k: v for k, v in book['chunk_config'].items() if k in ('max_tokens', 'max_table_tokens',
                'hard_cap_tokens', 'target_tokens', 'sentence_overlap', 'result_min_count', 'result_max_body_chars', 'heading_scheme')}
    counter = SentencePieceTokenCounter(ROOT / 'vendor/gemma/tokenizer.model', 'google-gemma-sentencepiece-v1')
    reference = so_chunk_doc_nhe.chunks_of(DocumentTree(nodes=[DocumentNode.from_dict(n) for n in tree['nodes']]), key, counter, settings)
    result = {'id': key, 'field': book['field'], 'split': book['split'], 'pages': data['pages'],
              'chunk_config': settings, 'models': {}}
    # Timing never uses the cached rows; scores do, so evaluation cost is separate.
    for kind in ('baseline', *learn.KINDS, 'silver_oracle'):
        start = time.perf_counter()
        record = None
        if kind in learn.KINDS:
            name = key if book['split'] == 'train' else 'full'
            path = out / 'models' / f'{name}-{kind}.json'
            record = learn.read(path)
            if record['fingerprint'] != learn.code_fingerprint() or key in record['train_books'] or key not in record['heldout']:
                raise ValueError('Stale model or in-sample evaluation')
            if learn.digest(path.with_suffix('.joblib')) != record['model_sha256']:
                raise ValueError('Model file changed')
            model = joblib.load(path.with_suffix('.joblib'))
            predicted = np.array(record['predictions'][key]['probability']) >= .5
            def predictor(rows, body):
                return learn.probability(model, learn.feature_matrix(rows, body), kind) >= .5
        elif kind == 'silver_oracle':
            predicted = np.where(np.array(data['y']) >= 0, data['y'], data['baseline']) == 1
        else:
            predicted = None
        load_seconds = time.perf_counter()-start
        nodes, _ = doc_nhe.group_rows(data['rows'], data['figures'], data['pages'], predicted)
        chunks = so_chunk_doc_nhe.chunks_of(so_chunk_doc_nhe.light_tree(nodes), key, counter, settings)
        line_prediction = data['baseline'] if predicted is None else predicted
        values = {'line': learn.metrics(np.array(data['y']), line_prediction),
                  'tree_legacy': doc_nhe.compare(nodes, tree), 'heading_strict': heading_score(tree['nodes'], nodes),
                  'chunk_legacy': so_chunk_doc_nhe.compare(reference, chunks), 'leaf_strict': leaf_score(reference, chunks),
                  'load_seconds': load_seconds, 'node_types': dict(Counter(n['node_type'] for n in nodes))}
        if kind != 'silver_oracle':
            timings = []
            pdf = learn.allowed_path(ROOT / book['pdf'], external=book['split'] == 'external')
            for _ in range(3):
                start = time.perf_counter()
                fresh, _ = doc_nhe.parse(pdf, predictor if kind in learn.KINDS else None)
                timings.append(time.perf_counter()-start)
                if fresh != nodes:
                    raise AssertionError('Fresh inference differs from saved OOF inference')
            values['timing_seconds'] = timings
            values['seconds_per_page'] = statistics.median(timings)/data['pages']
        result['models'][kind] = values
        print(key, kind, 'line F1', round(values['line']['f1'], 4), 'leaf', values['chunk_legacy']['cung_muc_la'], flush=True)
    result['peak_process_rss_mb'] = peak_rss_mb()
    result['fingerprint'] = learn.code_fingerprint()
    result['evaluator_sha256'] = learn.digest(__file__)
    learn.write(out / 'evaluation' / (key + '.json'), result)


def main():
    import hoc_tieu_de as learn
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=ROOT / 'tmp/doc-nhe-v414')
    parser.add_argument('--book')
    args = parser.parse_args()
    if args.book:
        evaluate_book(args.out, args.book)
        return
    for book in learn.manifest(args.out)['books']:
        path = args.out / 'evaluation' / (book['id'] + '.json')
        if path.exists():
            record = learn.read(path)
            if record.get('fingerprint') == learn.code_fingerprint() and record.get('evaluator_sha256') == learn.digest(__file__):
                print('reuse evaluation', book['id'], flush=True)
                continue
        subprocess.run([sys.executable, __file__, '--out', str(args.out), '--book', book['id']], cwd=ROOT, check=True)
    learn.write(args.out / 'e2e.json', [learn.read(args.out / 'evaluation' / (b['id'] + '.json')) for b in learn.manifest(args.out)['books']])


if __name__ == '__main__':
    main()
