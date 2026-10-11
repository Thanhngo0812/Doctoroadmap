"""V4-14 CPU experiment. No production writes, no model API calls, no test books.

Run with tmp/venv-ml/Scripts/python.exe. Reuses already installed PDF/chunker
packages from .venv, appended AFTER the ML environment's own site-packages.
"""
import argparse
import hashlib
import importlib.metadata
import json
import random
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT / '.venv/Lib/site-packages'))
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'scripts/thu-a1'))
import numpy as np
import doc_nhe as light
from doc2roadmap.infrastructure.parsing.docling_parser import DoclingParser

SEED = 42
KINDS = ('logistic', 'lightgbm', 'no_context')
EXTERNAL = {'doc-1': ('doc-1.pdf', 5), 'doc-4': ('doc-4.pdf', 3),
            'xstk-ch3-1': ('xstk-ch3-1.pdf', 3)}
TRAIN_VERSIONS = (2, 2, 1, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 2, 2, 1)
BASE_NAMES = ('size_ratio', 'bold', 'italic', 'uppercase', 'digits', 'chars', 'tokens',
              'left', 'width', 'center', 'vertical', 'gap_before', 'gap_after',
              'numbered', 'enumerator', 'terminal', 'viet_accent', 'math', 'mono',
              'symbols', 'single', 'repeat', 'indent')
CONTEXT_NAMES = tuple(f'{side}_{name}' for side in ('prev', 'next') for name in BASE_NAMES)
FEATURE_NAMES = BASE_NAMES + CONTEXT_NAMES + ('has_prev', 'has_next', 'prev_font_diff', 'next_font_diff')


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    temporary.replace(path)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def code_fingerprint():
    return hashlib.sha256((digest(__file__) + digest(ROOT / 'scripts/thu-a1/doc_nhe.py')).encode()).hexdigest()


def allowed_path(path, *, external=False):
    resolved = Path(path).resolve()
    if external:
        allowed = {(ROOT / value[0]).resolve() for value in EXTERNAL.values()}
    else:
        base = (ROOT / 'document-data/train').resolve()
        allowed = {(ROOT / 'document-data' / b['file']).resolve()
                   for b in read(ROOT / 'document-data/manifest.json')['books'] if b['split'] == 'train'}
        if not resolved.is_relative_to(base):
            raise ValueError('PDF outside training directory')
    if resolved not in allowed:
        raise ValueError('PDF is not allowlisted')
    return resolved


def latest(folder):
    return max((p for p in folder.iterdir() if re.fullmatch(r'v\d+', p.name)), key=lambda p: int(p.name[1:]))


def manifest(out):
    path = out / 'manifest.json'
    if path.exists():
        result = read(path)
        for b in result['books']:
            allowed_path(ROOT / b['pdf'], external=b['split'] == 'external')
            for name in ('pdf', 'tree', 'chunk_manifest'):
                if digest(ROOT / b[name]) != b[name + '_sha256']:
                    raise ValueError(f"Pinned input changed: {b['id']} {name}; choose a new output directory")
        return result
    books = []
    train = [b for b in read(ROOT / 'document-data/manifest.json')['books'] if b['split'] == 'train']
    assert [b['id'] for b in train] == [f'd01-{i:02}' for i in range(1, 17)]
    entries = [(b['id'], 'document-data/' + b['file'], v, b['field'], b['publisher'], 'train')
               for b, v in zip(train, TRAIN_VERSIONS, strict=True)]
    entries += [(key, pdf, version, 'external', 'external', 'external') for key, (pdf, version) in EXTERNAL.items()]
    for key, pdf, version, field, publisher, split in entries:
        allowed_path(ROOT / pdf, external=split == 'external')
        tree = f'artifacts/parse_tree/{key}/v{version}/tree.json'
        parse_manifest = read(ROOT / Path(tree).parent / 'manifest.json')
        chunks = latest(ROOT / 'artifacts/chunks' / key) / 'manifest.json'
        cm = read(chunks)
        if digest(ROOT / pdf) != parse_manifest['source_hash']:
            raise ValueError(f'Source hash mismatch: {key}')
        book = dict(id=key, pdf=pdf, tree=tree, parse_version=version, split=split,
                    field=field, publisher=publisher, parser=parse_manifest.get('config', {}).get('parser'),
                    chunk_manifest=chunks.relative_to(ROOT).as_posix(), chunk_parse_version=cm.get('parse_version'),
                    chunk_config=cm['config']['chunk'])
        for name in ('pdf', 'tree', 'chunk_manifest'):
            book[name + '_sha256'] = digest(ROOT / book[name])
        books.append(book)
    result = {'seed': SEED, 'books': books, 'python': sys.version,
              'packages': {k: importlib.metadata.version(k) for k in ('lightgbm', 'scikit-learn', 'numpy', 'joblib', 'pypdfium2')},
              'code_fingerprint_at_pin': code_fingerprint()}
    write(path, result)
    return result


def tokens(text):
    text, _ = DoclingParser._clean_text(text, collapse_pdf_glyphs=True)
    return light.words(text)


def contains(short, long):
    return bool(short) and any(long[i:i+len(short)] == short for i in range(len(long)-len(short)+1))


def near(row, node):
    box = node.get('bbox')
    if not box:
        return False  # no geometry = unknown, not a text-only pseudo-label
    left, top, right, bottom = box  # stored Docling/PDFium boxes: bottom-left origin
    if top < bottom:
        raise ValueError('Unexpected bbox origin; inspect before labeling')
    x, y = (row['x0']+row['x1'])/2, (row['top']+row['bottom'])/2
    slack = max(row['top']-row['bottom'], 1)/2
    return left-slack <= x <= right+slack and bottom-slack <= y <= top+slack


def silver_labels(rows, tree):
    pages = defaultdict(list)
    for index, node in enumerate(tree['nodes']):
        content = node.get('raw_text') if node['node_type'] == 'formula' else node.get('text', '')
        if node['node_type'] == 'table':
            content = ' '.join(' '.join(r) for r in node.get('table_rows') or []) or content
        pages[node.get('page')].append((index, node, tokens(content or '')))
    labels, alignments, covered = [], [], set()
    for row in rows:
        key = tokens(row['text'])
        hits = []
        mixed = False
        for index, node, value in pages[row['page']]:
            if not key or not value or not near(row, node):
                continue
            exact = key == value
            short, long = sorted((key, value), key=len)
            enough = len(short) >= 2 or sum(c.isalpha() for t in short for c in t) >= 8
            if not exact and not (enough and contains(short, long)):
                continue
            heading = node['node_type'] in {'title', 'section_header'}
            # Heading embedded in a longer prose line cannot label the entire line.
            if heading and len(key) > len(value) and len(value)/len(key) < .8:
                mixed = True
                continue
            hits.append((index, int(heading), 'exact' if exact else 'containment'))
        classes = {h[1] for h in hits}
        label = next(iter(classes)) if len(classes) == 1 and not mixed else -1
        status = ('exact' if any(h[2] == 'exact' for h in hits) else 'containment') if label >= 0 else ('ambiguous' if hits or mixed else 'unmatched')
        if label == 1:
            covered.update(h[0] for h in hits if h[1] == 1)
        labels.append(label)
        alignments.append({'status': status, 'nodes': [h[0] for h in hits]})
    counts = Counter(a['status'] for a in alignments)
    total_headings = sum(n['node_type'] in {'title', 'section_header'} for n in tree['nodes'])
    return np.array(labels, dtype=np.int8), {'counts': dict(counts), 'covered_heading_nodes': len(covered),
        'total_heading_nodes': total_headings, 'heading_coverage': len(covered)/max(total_headings, 1), 'alignments': alignments}


def feature_matrix(rows, body):
    repeats = defaultdict(set)
    margins = defaultdict(list)
    for r in rows:
        repeats[light.norm_repeat(r['text'])].add(r['page'])
        margins[r['page']].append(r['x0'])
    lefts = {p: float(np.percentile(v, 20)) for p, v in margins.items()}
    base = []
    for i, r in enumerate(rows):
        text = r['text']
        letters = [c for c in text if c.isalpha()]
        size, width, height = max(r['size'], 1), max(r.get('width') or 600, 1), max(r['height'], 1)
        prev = rows[i-1] if i and rows[i-1]['page'] == r['page'] else None
        nxt = rows[i+1] if i+1 < len(rows) and rows[i+1]['page'] == r['page'] else None
        base.append([r['size']/max(body, 1), float(r['bold']), r.get('italic', 0),
            sum(c.isupper() for c in letters)/max(len(letters), 1), sum(c.isdigit() for c in text)/max(len(text), 1),
            np.log1p(r['chars']), np.log1p(r['tokens']), r['x0']/width, (r['x1']-r['x0'])/width,
            abs((r['x0']+r['x1'])/2-width/2)/width, r['top']/height,
            np.clip((prev['bottom']-r['top'])/size, -5, 20) if prev else 0,
            np.clip((r['bottom']-nxt['top'])/size, -5, 20) if nxt else 0,
            float(bool(light.HEADING_NUMBER.match(text))), float(bool(light.ENUMERATOR.match(text))),
            float(text.endswith(('.', ',', ';', ':', '?', '!'))), r['viet']/max(r['tokens'], 1), r['math'], r['mono'],
            r['symbol_share'], r['single'], np.log1p(len(repeats[light.norm_repeat(text)])), (r['x0']-lefts[r['page']])/size])
    x = np.asarray(base, dtype=np.float32).reshape((-1, len(BASE_NAMES)))
    previous, following = np.zeros_like(x), np.zeros_like(x)
    flags = np.zeros((len(rows), 4), dtype=np.float32)
    for i, r in enumerate(rows):
        if i and rows[i-1]['page'] == r['page']:
            previous[i] = x[i-1]
            flags[i, 0], flags[i, 2] = 1, r.get('font') != rows[i-1].get('font')
        if i+1 < len(rows) and rows[i+1]['page'] == r['page']:
            following[i] = x[i+1]
            flags[i, 1], flags[i, 3] = 1, r.get('font') != rows[i+1].get('font')
    return np.concatenate((x, previous, following, flags), axis=1)


def metrics(y, predicted):
    mask = y >= 0
    a, b = y[mask], np.asarray(predicted)[mask]
    tp, fp, fn = (int(np.sum(c)) for c in ((a == 1)&(b == 1), (a == 0)&(b == 1), (a == 1)&(b == 0)))
    p, r = tp/max(tp+fp, 1), tp/max(tp+fn, 1)
    return dict(tp=tp, fp=fp, fn=fn, precision=p, recall=r, f1=2*p*r/max(p+r, 1e-12), evaluated=int(mask.sum()), total=len(y))


def training_arrays(data, heldout=()):
    heldout = {heldout} if isinstance(heldout, str) else set(heldout)
    names = sorted(set(data)-heldout)
    return (np.concatenate([data[k]['X'][data[k]['y'] >= 0] for k in names]),
            np.concatenate([data[k]['y'][data[k]['y'] >= 0] for k in names]), names)


def fit_model(x, y, kind):
    if kind == 'logistic':
        from sklearn.pipeline import make_pipeline
        from sklearn.preprocessing import StandardScaler
        from sklearn.linear_model import LogisticRegression
        model = make_pipeline(StandardScaler(), LogisticRegression(C=1, class_weight='balanced', max_iter=1000, random_state=SEED))
    else:
        from lightgbm import LGBMClassifier
        model = LGBMClassifier(n_estimators=300, num_leaves=15, learning_rate=.05, min_child_samples=30,
                              class_weight='balanced', random_state=SEED, n_jobs=2, verbosity=-1,
                              deterministic=True, force_col_wise=True)
    columns = len(BASE_NAMES) if kind == 'no_context' else len(FEATURE_NAMES)
    model.fit(x[:, :columns], y)
    return model


def probability(model, x, kind):
    columns = len(BASE_NAMES) if kind == 'no_context' else len(FEATURE_NAMES)
    return model.predict_proba(x[:, :columns])[:, 1]


def prepare(out):
    pinned = manifest(out)
    stamp = code_fingerprint()
    for book in pinned['books']:
        path = out / 'datasets' / (book['id'] + '.json')
        if path.exists() and read(path).get('fingerprint') == stamp:
            print('reuse dataset', book['id'], flush=True)
            continue
        start = time.perf_counter()
        raw, figures, pages = light.extract_rows(allowed_path(ROOT / book['pdf'], external=book['split'] == 'external'))
        rows, body = light.prepare_rows(raw)
        tree = read(ROOT / book['tree'])
        labels, detail = silver_labels(rows, tree)
        _, raw_detail = silver_labels(raw, tree)
        alignments = detail.pop('alignments')
        raw_detail.pop('alignments')
        baseline = [light.classify_row(r, s, body) == 'section_header' for r, s in zip(rows, light.standalone_flags(rows))]
        value = dict(book=book, rows=rows, figures=figures, pages=pages, raw_count=len(raw), body=body,
                     y=labels.tolist(), alignments=alignments, detail=detail, raw_detail=raw_detail,
                     baseline=baseline, seconds=time.perf_counter()-start, fingerprint=stamp)
        write(path, value)
        print(json.dumps({'dataset': book['id'], 'rows': len(rows), 'unknown': int(sum(labels < 0)),
                          'coverage': detail['heading_coverage'], 'seconds': value['seconds']}), flush=True)
    sample = []
    rng = random.Random(SEED)
    for b in pinned['books']:
        if b['split'] != 'train':
            continue
        d = read(out / 'datasets' / (b['id'] + '.json'))
        used = set()
        for category in ('positive', 'positive', 'negative', 'containment', 'unknown'):
            indexes = [i for i, (y, a) in enumerate(zip(d['y'], d['alignments'])) if i not in used and
                       (y == 1 if category == 'positive' else y == 0 if category == 'negative' else
                        a['status'] == 'containment' if category == 'containment' else y < 0)]
            fallback = not indexes
            if fallback:
                indexes = [i for i in range(len(d['rows'])) if i not in used]
            i = rng.choice(indexes)
            used.add(i)
            sample.append(dict(id=b['id'], row_index=i, requested=category, fallback=fallback,
                               row=d['rows'][i], label=d['y'][i], alignment=d['alignments'][i]))
    write(out / 'alignment-review-80.json', sample)


def load_data(out, pinned):
    data = {}
    for b in pinned['books']:
        d = read(out / 'datasets' / (b['id'] + '.json'))
        if d['fingerprint'] != code_fingerprint():
            raise ValueError('Dataset code fingerprint changed; prepare again')
        d['X'], d['y'] = feature_matrix(d['rows'], d['body']), np.asarray(d['y'])
        data[b['id']] = d
    return data


def train(out):
    import joblib
    from threadpoolctl import threadpool_limits
    if not (out / 'alignment-review-80-reviewed.json').exists():
        raise ValueError('Read and record the 80 alignment reviews before training')
    pinned = manifest(out)
    data = load_data(out, pinned)
    training = {k: v for k, v in data.items() if v['book']['split'] == 'train'}
    fingerprint = code_fingerprint()
    jobs = [(k, (k,), kind) for k in training for kind in KINDS]
    groups = sorted({d['book']['publisher'] for d in training.values()})
    jobs += [(f'publisher-{i:02}', tuple(k for k in training if training[k]['book']['publisher'] == g), 'lightgbm') for i, g in enumerate(groups)]
    jobs += [('full', (), kind) for kind in KINDS]
    for name, heldout, kind in jobs:
        record = out / 'models' / f'{name}-{kind}.json'
        model_path = record.with_suffix('.joblib')
        if record.exists() and model_path.exists() and read(record).get('fingerprint') == fingerprint:
            print('reuse model', name, kind, flush=True)
            continue
        x, y, names = training_arrays(training, heldout)
        start = time.perf_counter()
        with threadpool_limits(limits=2):
            model = fit_model(x, y, kind)
        seconds = time.perf_counter()-start
        record.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(model, model_path)
        tests = heldout if heldout else tuple(k for k in data if k not in training)
        predictions = {}
        for key in tests:
            probs = probability(model, data[key]['X'], kind)
            predictions[key] = dict(probability=probs.tolist(), metrics=metrics(data[key]['y'], probs >= .5))
        importance = (model[-1].coef_[0].tolist() if kind == 'logistic' else model.booster_.feature_importance(importance_type='gain').tolist())
        write(record, dict(name=name, kind=kind, train_books=names, heldout=list(tests), seconds=seconds,
                           fingerprint=fingerprint, threshold=.5, model_sha256=digest(model_path),
                           model_bytes=model_path.stat().st_size, importance=importance,
                           feature_names=list(FEATURE_NAMES[:len(importance)]), predictions=predictions))
        print(json.dumps({'model': name, 'kind': kind, 'seconds': seconds,
                          'f1': {k: v['metrics']['f1'] for k, v in predictions.items()}}), flush=True)


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=('prepare', 'train'))
    parser.add_argument('--out', type=Path, default=ROOT / 'tmp/doc-nhe-v414')
    args = parser.parse_args()
    {'prepare': prepare, 'train': train}[args.stage](args.out)


if __name__ == '__main__':
    main()
