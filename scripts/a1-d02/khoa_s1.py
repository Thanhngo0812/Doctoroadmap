"""Freeze the measured R25 candidate without retraining or opening locked PDFs."""
import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT/'.venv/Lib/site-packages'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def freeze():
    result_path = ROOT/'tmp/a1-v414-r25/results.json'
    result = json.loads(result_path.read_text(encoding='utf-8'))
    assert len(result['books']) == 19
    files = list((ROOT/'scripts/doc-nhe').glob('*.py'))
    files += [ROOT/'scripts/thu-a1/doc_nhe.py', ROOT/'src/doc2roadmap/domain/chunking.py',
              ROOT/'src/doc2roadmap/infrastructure/parsing/docling_parser.py',
              ROOT/'vendor/gemma/tokenizer.model', result_path]
    for folder, pattern in [('tmp/doc-nhe-v414/models', '*-lightgbm.*'),
                            ('tmp/a1-v414-r5/models', '*.*')]:
        files += [p for p in (ROOT/folder).glob(pattern)
                  if p.suffix in {'.joblib', '.json'} and not p.name.startswith('publisher-')]
    files += list((ROOT/'tmp/a1-v414-r25/trees').glob('*.json'))
    assert sum(p.suffix == '.joblib' for p in files) == 34
    hashes = {p.relative_to(ROOT).as_posix(): digest(p) for p in sorted(set(files))}
    config = dict(candidate='R25-default', row_model='M2f', pair_model='B2', threshold=0.5,
                  margins='R8c+R13', corrections=['R18','R20','R21','R22','R24','R25'],
                  hierarchy='default chunker; H3 not combined with R25', production=False)
    scores = {b['id']: b['models']['placement']['leaf_strict']['share'] for b in result['books']}
    return dict(schema='a1-d02-s1-freeze-v1', date='2026-10-08', config=config, files=hashes,
                fingerprint=hashlib.sha256(json.dumps([config, hashes],sort_keys=True).encode()).hexdigest(),
                old_silver_leaf=dict(per_book=scores, median=statistics.median(scores.values()),
                                    worst=min(scores,key=scores.get)),
                packages={p:importlib.metadata.version(p) for p in ('numpy','lightgbm','scikit-learn','joblib','pypdfium2')})


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out',type=Path,required=True)
    args=parser.parse_args(); data=freeze()
    if args.out.exists():
        assert json.loads(args.out.read_text(encoding='utf-8')) == data, 'Frozen inputs changed'
    else:
        args.out.parent.mkdir(parents=True,exist_ok=True)
        args.out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(data['fingerprint'], '19 books; 34 model files')
